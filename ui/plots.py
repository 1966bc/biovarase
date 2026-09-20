# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk

from ui.parent_view import ParentView
from tkinter import ttk

from ljcanvas import LeveyJenningsCanvas


class UI(ParentView):
    """
    Levey–Jennings plots window.

    It shows one LeveyJenningsCanvas per batch (level) for the selected test
    and workstation, stacked vertically (one above the other), inside a
    scrollable area.
    """
    def __init__(self, parent, index=None):
        super().__init__(parent, name="plots")
        if self._reusing:
            return

        # Note: transient() removed - breaks resize on Windows

        self.selected_workstation = None
        self.selected_test_method = None
        self.elements = 0
        self.um = None

        self.bind("<Destroy>", self._on_destroy)

        self._header_var = tk.StringVar(value="")

        self._build_ui()

    # -------------------------------------------------------------------------
    # UI SETUP
    # -------------------------------------------------------------------------
    def _build_ui(self):
        """Create the main frame and scrollable container for stacked charts."""

        self.title("Quality Control Plots")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Frame(self, style="App.TFrame", padding=8)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # Header: test + workstation info
        header = ttk.Frame(main, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self._header_var, style="App.TLabel")\
            .grid(row=0, column=0, sticky="w")

        # ------------------------------------------------------------------
        # Scrollable area: Canvas + internal frame + vertical scrollbar
        # ------------------------------------------------------------------
        scroll_container = ttk.Frame(main, style="App.TFrame")
        scroll_container.grid(row=1, column=0, sticky="nsew")
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            scroll_container,
            highlightthickness=0,
            bg=self.cget("bg"),
        )

        
        self._canvas.bind("<Enter>", self._on_enter_canvas)
        self._canvas.bind("<Leave>", self._on_leave_canvas)

        self._canvas.grid(row=0, column=0, sticky="nsew")

        vbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self._canvas.yview,
        )
        vbar.grid(row=0, column=1, sticky="ns")

        self._canvas.configure(yscrollcommand=vbar.set)

        # Frame inside the Canvas that will hold all batch cards
        self.frm_plots = ttk.Frame(self._canvas, style="App.TFrame")
        self.frm_plots.columnconfigure(0, weight=1) 
        self.frm_plots.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")) if self._canvas else None,
        )

        # Create the window inside the canvas and keep its id
        self._plots_window = self._canvas.create_window(
            (0, 0),
            window=self.frm_plots,
            anchor="nw",
        )

        # Make inner frame width follow the canvas width
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfigure(self._plots_window, width=e.width) if self._canvas else None,
        )



        # Mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)  # Linux

        ttk.Sizegrip(self).grid(row=1, column=0, sticky="se")

        # Set initial size BEFORE centering
        self.geometry("700x500")
        self.minsize(600, 400)
        # Center and show window
        self.show(on_screen=True)

    # -------------------------------------------------------------------------
    # OPEN WINDOW
    # -------------------------------------------------------------------------
    def on_open(self, selected_test_method, selected_workstation, elements):
        """
        Initialize the window and start plotting.

        Args:
            selected_test_method: dict/hybrid from get_selected("test_methods", ...)
                                  Should be accessed via named keys:
                                      ['test_id'], ['unit_id'], ['test_method_id'], ...
            selected_workstation: workstation record (legacy tuple).
            elements (int): max number of results to show per batch.
        """
        self.selected_workstation = selected_workstation
        self.selected_test_method = selected_test_method
        self.elements = int(elements)

        # Test name using the new dict interface.
        test_id = selected_test_method["test_id"]
        test_name = self.engine.get_test_name(test_id)

        # Unit of measurement: unit_id from test_methods.
        unit_id = selected_test_method["unit_id"]
        self.um = self.engine.get_um(unit_id)

        ws_name = selected_workstation[3]
        ws_serial = selected_workstation[4]

        self.title(f"{test_name} – Quality Control Plots")
        self._header_var.set(
            f"Test: {test_name}   ·   Workstation: {ws_name}   ·   Serial: {ws_serial}"
        )

        # Load batches and plot
        self.get_batches()

    # -------------------------------------------------------------------------
    # LOAD BATCHES
    # -------------------------------------------------------------------------
    def get_batches(self):
        """
        Load all active batches for the current test_method and workstation.

        Uses read_dict() so each batch is a dictionary with fields like:
            'batch_id', 'lot_number', 'target', 'sd', 'expiration', ...
        """
        if not self.selected_test_method or not self.selected_workstation:
            return

        sql = (
            "SELECT * "
            "FROM batches "
            "WHERE test_method_id = ? "
            "  AND workstation_id = ? "
            "  AND status = 1 "
            "ORDER BY expiration DESC;"
        )

        args = (
            self.selected_test_method["test_method_id"],
            self.selected_workstation[0],
        )

        batches = self.engine.db.read(True, sql, args) or []
        self.set_values(batches)

    # -------------------------------------------------------------------------
    # BUILD STACKED CHARTS
    # -------------------------------------------------------------------------
    def set_values(self, batches):
        """
        Build one LeveyJenningsCanvas per batch, stacked vertically.

        Args:
            batches: list[dict] from read_dict() on 'batches'.
        """

        # Clear previous charts
        for child in self.frm_plots.winfo_children():
            child.destroy()

        if not batches:
            no_data = ttk.Label(
                self.frm_plots,
                text="No batches available for this test.",
                style="App.TLabel",
            )
            no_data.grid(row=0, column=0, sticky="w")
            return

        # SQL template to collect recent results for each batch
        sql = """
            SELECT
                result_id,
                ROUND(result, 2)                  AS result_value,
                DATE_FORMAT(received, '%d-%m-%Y') AS received_label,
                status,
                received
            FROM results
            WHERE batch_id = ?
              AND workstation_id = ?
              AND is_delete = 0
            ORDER BY received DESC
            LIMIT ?;
        """

        row_index = 0

        for batch in batches:
            args = (
                batch["batch_id"],
                self.selected_workstation[0],
                self.elements,
            )
            rs = self.engine.db.read(True, sql, args)

            # Create card for this batch
            card = ttk.Frame(self.frm_plots, style="App.TFrame", padding=(6, 4))
            card.grid(row=row_index, column=0, sticky="ew", pady=(0, 8))
            card.columnconfigure(0, weight=1)

            # Batch description (lot, target, SD, expiration)
            lot_number = batch.get("lot_number", "N/A")
            expiration = batch.get("expiration", "")
            target = batch.get("target")
            sd = batch.get("sd")

            # Optional control name (if available)
            control_name = None
            control_id = batch.get("control_id")
            if control_id is not None:
                try:
                    control_name = self.engine.get_control_name(control_id)
                except Exception as e:
                    control_name = None

            title_parts = []
            if control_name:
                title_parts.append(control_name)
            title_parts.append(f"Lot {lot_number}")
            if target is not None and sd is not None:
                title_parts.append(f"Target: {target:.2f}")
                title_parts.append(f"SD: {sd:.3f}")
            if expiration:
                title_parts.append(f"Exp: {expiration}")

            title_line = "   ·   ".join(title_parts)

            ttk.Label(card, text=title_line, style="App.TLabel")\
                .grid(row=0, column=0, sticky="w", pady=(0, 2))


            # Canvas for this batch
            lj_canvas = LeveyJenningsCanvas(
                card,
                bg="white",
                height=220,
                highlightthickness=1,
                highlightbackground="#cccccc",
            )
            lj_canvas.grid(row=1, column=0, sticky="nsew")
            card.rowconfigure(1, weight=1)

            # Default text for the summary row
            info_text = "No data available"

            # If there are results, plot; otherwise show "No data"
            if rs:
                series = self.engine.get_series(
                    batch["batch_id"],
                    self.selected_workstation[0],
                    int(self.engine.get_observations()),
                )

                if series:
                    x_data = self.get_x_data(rs)

                    # Y-axis label from unit of measurement, if available
                    if self.um:
                        if isinstance(self.um, dict):
                            y_label = self.um.get("description", "") or "Value"
                        elif isinstance(self.um, (list, tuple)):
                            y_label = self.um[0] if self.um else "Value"
                        else:
                            y_label = str(self.um)
                    else:
                        y_label = "Value"

                    lj_canvas.draw_chart(
                        series=series,
                        target=target,
                        sd=sd,
                        title=None,
                        dates=x_data["dates"],
                        y_axis_caption=y_label,
                    )

                    # Summary string (like main LJ window)
                    count_series = len(series)
                    count_rs = len(rs)
                    info_text = f"Computed {count_series} on {count_rs} results"
                else:
                    lj_canvas.create_text(
                        lj_canvas.winfo_reqwidth() / 2,
                        lj_canvas.winfo_reqheight() / 2,
                        text="No series available",
                        fill="red",
                    )
                    info_text = "No series available"
            else:
                lj_canvas.create_text(
                    lj_canvas.winfo_reqwidth() / 2,
                    lj_canvas.winfo_reqheight() / 2,
                    text="No data available",
                    fill="red",
                )
                info_text = "No data available"

            # Summary label under the chart (right aligned)
            ttk.Label(card, text=info_text, style="App.TLabel")\
                .grid(row=2, column=0, sticky="e", pady=(2, 0))


            row_index += 1

    # -------------------------------------------------------------------------
    # X-AXIS DATA
    # -------------------------------------------------------------------------
    def get_x_data(self, rs):
        """
        Build X-axis labels (dates in dd-mm-YYYY format) and the list of dates.

        Args:
            rs: list[dict] from results query.

        Returns:
            dict: {'x_labels': [...], 'dates': [...]}
        """
        x_labels = []
        dates = []

        if rs:
            # Filter out rows with status == 0 (disabled results)
            filtered = [row for row in rs if row.get("status", 0) != 0]
            # Reverse to show oldest on the left
            for row in reversed(filtered):
                label = row["received_label"]
                x_labels.append(label)
                dates.append(label)

        return {"x_labels": x_labels, "dates": dates}

    # -------------------------------------------------------------------------
    # MOUSE WHEEL HANDLER
    # -------------------------------------------------------------------------
    def _on_mousewheel(self, event):
        """Scroll the canvas with the mouse wheel."""
        # Recupera il canvas in modo sicuro
        canvas = getattr(self, "_canvas", None)
        if canvas is None:
            return

        try:
            # If widget was destroyed, do nothing
            if not canvas.winfo_exists():
                self._canvas = None
                return
        except tk.TclError:
            self._canvas = None
            return

        # Calcolo del delta: Linux (Button-4/5) oppure Windows/macOS (event.delta)
        if getattr(event, "num", None) == 4:       # Linux scroll up
            delta = -1
        elif getattr(event, "num", None) == 5:     # Linux scroll down
            delta = 1
        else:
            # Windows / other: event.delta is a multiple of 120
            delta = -1 * (event.delta // 120) if getattr(event, "delta", 0) != 0 else 0

        if delta == 0:
            return

        try:
            canvas.yview_scroll(delta, "units")
        except tk.TclError:
            # Canvas was destroyed in the meantime
            self._canvas = None
            return

    def _on_destroy(self, event=None):
        """
        Unbind global mousewheel when this window is destroyed.
        """
        try:
            # Se in questa finestra hai usato bind_all
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception as e:
            pass

        # Clear canvas reference
        if hasattr(self, "_canvas"):
            self._canvas = None

    def _on_enter_canvas(self, event=None):
        # Enable global bindings ONLY when mouse is over the canvas
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

    def _on_leave_canvas(self, event=None):
        # Disable bindings when mouse leaves
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception as e:
            pass



    # -------------------------------------------------------------------------
    # CLOSE
    # -------------------------------------------------------------------------
    def on_cancel(self, evt=None):
        """Close the window."""
        self._on_destroy()
        self.destroy()
