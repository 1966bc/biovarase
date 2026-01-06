# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   refactor anti-shake, Calendarium v2.2, English UI text, Treeview display
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
from calendarium import Calendarium


class UI(tk.Toplevel):
    """
    Quick Data Analysis dialog with view-only Treeview display.

    - Window is fully built off-screen, then centered and shown.
    - No geometry recalculation in on_open().
    - 'topmost' and 'lift' are applied only when the window is ready.
    - Only one instance is allowed at a time (singleton).
    - Displays the same data as the Excel export in a Treeview widget.
    """
    _instance = None  # singleton holder

    # --- Singleton allocation -------------------------------------------------
    def __new__(cls, parent, index=None):
        """
        Ensure only one instance of this Toplevel exists.

        Reuse the existing one if it is still alive, otherwise create a new one.
        """
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    return cls._instance
            except Exception as e:
                # If anything goes wrong, fall back to a fresh instance.
                pass

        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    # --- One-time initialization (guarded by _is_init) -----------------------
    def __init__(self, parent, index=None):
        """
        Build the dialog UI once. On subsequent calls, only update references.
        """
        if getattr(self, "_is_init", False):
            # Reuse: just refresh parent / index references.
            self.parent = parent
            self.index = index
            return

        super().__init__(name="quick_data_analysis")

        self._is_init = True
        self.parent = parent
        self.index = index

        # Engine is attached to the root window "."
        self.engine = self.nametowidget(".").engine

        # Register this window in the Engine registry
        self.engine.dict_instances[self.winfo_name()] = self

        # Build off-screen to avoid flicker
        self.withdraw()
        self.attributes("-alpha", 0.0)  # anti-flash trick

        try:
            self.transient(parent)
        except Exception as e:
            # In case parent is not a valid toplevel yet, fail silently.
            pass

        self.resizable(True, True)
        self.title("Quick Data Analysis")

        padd = {"padx": 5, "pady": 5}

        # --- Main container -------------------------------------------------------
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.grid(row=0, column=0, sticky=tk.NSEW)
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(1, weight=1)

        # --- Top section: Date selector and buttons ------------------------------
        frm_top = ttk.Frame(frm_main, style="App.TFrame")
        frm_top.grid(row=0, column=0, sticky=tk.EW, **padd)

        frm_left = ttk.Frame(frm_top, style="App.TFrame")
        frm_left.pack(side=tk.LEFT, fill=tk.Y, **padd)

        frm_buttons = ttk.Frame(frm_top, style="App.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, **padd)

        # --- Date selector (Calendarium v2.2 API) ---------------------------------
        self.analysis_date = Calendarium(frm_left, "Set a date:")
        self.analysis_date.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W,
            padx=5,
            pady=5,
        )

        # --- Buttons --------------------------------------------------------------
        btn_show = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Show",
            underline=0,
            command=self.on_show,
        )
        btn_show.grid(row=0, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-s>", self.on_show)

        btn_export = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Export",
            underline=0,
            command=self.on_export,
        )
        btn_export.grid(row=0, column=1, sticky=tk.EW, **padd)
        self.bind("<Alt-e>", self.on_export)

        btn_close = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Close",
            underline=0,
            command=self._on_close,
        )
        btn_close.grid(row=0, column=2, sticky=tk.EW, **padd)
        self.bind("<Alt-c>", self._on_close)
        self.bind("<Escape>", self._on_close)

        # --- Treeview section -----------------------------------------------------
        frm_tree = ttk.Frame(frm_main, style="App.TFrame")
        frm_tree.grid(row=1, column=0, sticky=tk.NSEW, **padd)
        frm_tree.columnconfigure(0, weight=1)
        frm_tree.rowconfigure(0, weight=1)

        # Scrollbars
        sb_vert = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL)
        sb_vert.grid(row=0, column=1, sticky=tk.NS)

        sb_horiz = ttk.Scrollbar(frm_tree, orient=tk.HORIZONTAL)
        sb_horiz.grid(row=1, column=0, sticky=tk.EW)

        # Define columns (matching Excel export)
        cols = (
            "type", "test", "batch", "expiration", "equipment",
            "target", "result", "avg", "bias", "sd_set", "sd_calc", "cv",
            "uncertainty", "westgard", "date", "category", "workstation",
            "control", "supplier"
        )

        self.tree = ttk.Treeview(
            frm_tree,
            columns=cols,
            show="headings",
            yscrollcommand=sb_vert.set,
            xscrollcommand=sb_horiz.set,
            height=20
        )
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)

        sb_vert.config(command=self.tree.yview)
        sb_horiz.config(command=self.tree.xview)

        # Column headers and widths (matching Excel layout)
        headers = [
            ("type", "Type", 60),
            ("test", "Test", 150),
            ("batch", "Batch", 120),
            ("expiration", "Expiration", 100),
            ("equipment", "Equipment", 150),
            ("target", "Target", 80),
            ("result", "Result", 80),
            ("avg", "avg", 80),
            ("bias", "bias", 80),
            ("sd_set", "SD", 80),
            ("sd_calc", "sd", 80),
            ("cv", "cv", 80),
            ("uncertainty", "U", 80),
            ("westgard", "Wstg", 80),
            ("date", "Date", 120),
            ("category", "Category", 100),
            ("workstation", "Workstation", 130),
            ("control", "Control", 130),
            ("supplier", "Supplier", 130),
        ]

        for col_id, col_text, col_width in headers:
            self.tree.heading(col_id, text=col_text, anchor=tk.W)
            self.tree.column(col_id, width=col_width, anchor=tk.W)

        # Center-align numeric columns
        for col_id in ("target", "result", "avg", "bias", "sd_set", "sd_calc", "cv", "uncertainty"):
            self.tree.column(col_id, anchor=tk.E)

        # Configure tags for color coding
        self.tree.tag_configure("green", background="#90EE90")   # Light green
        self.tree.tag_configure("yellow", background="#FFFF99")  # Light yellow
        self.tree.tag_configure("orange", background="#FFD580")  # Light orange
        self.tree.tag_configure("red", background="#FFB6C1")     # Light red
        self.tree.tag_configure("westgard_violation", background="#FFFF99")  # Yellow for Westgard violations

        # --- Status label ---------------------------------------------------------
        self.status_label = ttk.Label(
            frm_main,
            text="Select a date and click 'Show' to view data",
            style="App.TLabel"
        )
        self.status_label.grid(row=2, column=0, sticky=tk.W, **padd)

        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.attributes("-topmost", True)
        self.lift()
        self.after_idle(self._focus_entry)

    # --- Public API ----------------------------------------------------------
    def on_open(self):
        """
        Entry point called by the parent when the dialog must be shown.

        - Re-sync transient parent.
        - Reset date to today.
        - Bring the window to the front.
        """
        try:
            self.transient(self.parent)
        except Exception as e:
            pass

        # Reset date to today, if supported by Calendarium
        try:
            self.analysis_date.set_today()
        except Exception as e:
            pass

        self.deiconify()
        self.lift()
        self.after_idle(self._focus_entry)

    # --- Internal helpers ----------------------------------------------------
    def _focus_entry(self):
        """Set initial focus to the date widget, if possible."""
        try:
            self.analysis_date.focus_set()
        except Exception as e:
            pass

    def _get_selected_date(self):
        """
        Return the selected date from Calendarium in a safe, backward-compatible way.

        Supports both historical signatures:
            - get_date(parent)
            - get_date()

        Returns:
            Any | None:
                - A valid date/representation as returned by Calendarium, or
                - None if the date is invalid / not selected.
        """
        try:
            # Legacy API: get_date(parent)
            value = self.analysis_date.get_date(self)
        except TypeError:
            # Current API: get_date()
            value = self.analysis_date.get_date()
        except Exception as e:
            return None

        # Historical behaviour: False means "invalid"
        if value is False:
            return None

        return value

    def _clear_tree(self):
        """Clear all items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _populate_tree(self, selected_date):
        """
        Populate the Treeview with Quick Data Analysis data.

        Uses the same logic as exporter.quick_data_analysis() but displays
        in Treeview instead of Excel.
        """
        self._clear_tree()

        # 1) Normalize date
        day_obj, day_sql = self.engine._normalize_date(selected_date)

        # 2) Context
        checked_tests = []
        mandatory_tests = self.engine.get_mandatory()

        # 3) Lab id
        lab_id = self.engine.get_lab_id()
        if lab_id is None:
            row = self.engine.get_idd_by_section_id(self.engine.get_section_id())
            if not row:
                self.status_label.config(text="No valid context - cannot load data")
                return 0
            lab_id = row["lab_id"]

        row_count = 0

        # 4) Fetch test methods
        for row in self.engine._fetch_test_methods(lab_id):
            tm_id = row["test_method_id"]
            tm_sample = row["sample"]
            tm_test_desc = row["test_description"]
            tm_category_desc = row["category_description"]

            # 5) Batches per test method
            for batch in self.engine._fetch_batches(tm_id, lab_id):
                b_batch_id = batch["batch_id"]
                b_workstation_id = batch["workstation_id"]
                b_lot_number = batch["lot_number"]
                b_expiration_fmt = batch["expiration_fmt"]
                b_target = batch["target"]
                b_sd = batch["sd"]
                b_ws_serial = batch["workstation_serial"]
                b_equipment_desc = batch["equipment_description"]
                b_control_id = batch["control_id"]
                b_expiration = batch["expiration"]

                # 6) Results of the day
                results = self.engine._fetch_results(b_batch_id, day_sql, b_workstation_id)
                if not results:
                    continue

                # 7) Control info
                control_desc, control_supplier = self.engine._fetch_control(b_control_id)

                for row in results:
                    r_result_id = row["result_id"]
                    r_result_rounded = row["result_value"]
                    r_received_str = row["received_text"]
                    r_ws_serial = row["workstation_serial"]
                    r_workstation_id = row["workstation_id"]
                    r_received_date = row["received_date"]

                    try:
                        # Series and stats
                        series = self.engine.get_series(
                            b_batch_id,
                            r_workstation_id,
                            int(self.engine.get_observations()),
                            r_result_id,
                        )
                        if not series:
                            continue

                        rule = self.engine._westgard_rule_safe(
                            b_target, b_sd, series,
                            batch,
                            (tm_id, tm_sample, tm_test_desc, tm_category_desc),
                        )

                        avg, sd_calc, cv = self.engine._compute_series_metrics(series)

                        target = float(b_target)
                        sd_set = float(b_sd)
                        res = float(r_result_rounded)
                        bias = self.engine.get_bias(avg, target)

                        # Uncertainty
                        uncertainty = self.engine.get_uncertainty(cv, bias)

                        # Determine color tag based on SD bands
                        r_color = self.engine._result_color(res, target, sd_set)

                        # Prepare values
                        values = (
                            tm_sample,                    # Type
                            tm_test_desc,                 # Test
                            b_lot_number,                 # Batch
                            b_expiration_fmt,             # Expiration
                            b_equipment_desc,             # Equipment
                            f"{target:.2f}",              # Target
                            f"{res:.2f}",                 # Result
                            f"{avg:.2f}",                 # avg
                            f"{bias:.2f}",                # bias
                            f"{sd_set:.2f}",              # SD (set)
                            f"{sd_calc:.2f}",             # sd (calculated)
                            f"{cv:.2f}",                  # cv
                            f"{uncertainty:.1f}" if uncertainty else "",  # U
                            rule,                         # Westgard
                            r_received_str,               # Date
                            tm_category_desc,             # Category
                            r_ws_serial,                  # Workstation
                            control_desc,                 # Control
                            control_supplier,             # Supplier
                        )

                        # Determine tags
                        tags = []
                        if r_color:
                            tags.append(r_color)
                        if rule not in ('Accept', 'No data'):
                            tags.append("westgard_violation")

                        # Insert into tree
                        self.tree.insert("", tk.END, values=values, tags=tuple(tags))
                        row_count += 1

                        checked_tests.append(tm_test_desc)

                    except Exception as e:
                        # Log error but continue
                        print(f"Error processing result {r_result_id}: {e}")
                        continue

        return row_count

    # --- Commands ------------------------------------------------------------
    def on_show(self, evt=None):
        """
        Display Quick Data Analysis data in the Treeview.
        """
        selected_date = self._get_selected_date()
        if selected_date is None:
            self.status_label.config(text="Please select a valid date")
            return

        self.config(cursor="watch")
        self.status_label.config(text="Loading data...")
        self.update()

        try:
            row_count = self._populate_tree(selected_date)
            self.status_label.config(text=f"Loaded {row_count} results")
        except Exception as e:
            self.status_label.config(text=f"Error loading data: {e}")
            print(f"Error in on_show: {e}")
        finally:
            self.config(cursor="")
            self.update()

    def on_export(self, evt=None):
        """
        Validate the selected date and trigger Quick Data Analysis export
        through Engine.quick_data_analysis() (Excel export).
        """
        selected_date = self._get_selected_date()
        if selected_date is None:
            self.status_label.config(text="Please select a valid date")
            return

        self.config(cursor="watch")
        self.status_label.config(text="Exporting to Excel...")
        self.update()

        try:
            args = (selected_date,)
            self.engine.quick_data_analysis(args)
            self.status_label.config(text="Export completed")
        except Exception as e:
            self.status_label.config(text=f"Export error: {e}")
            print(f"Error in on_export: {e}")
        finally:
            self.config(cursor="")
            self.update()

    def _on_close(self, evt=None):
        """
        Destroy the dialog and reset the singleton instance.

        Also unregister the window from Engine.dict_instances.
        """
        # Reset singleton
        type(self)._instance = None

        # Unregister from Engine registry
        try:
            self.engine.dict_instances.pop(self.winfo_name(), None)
        except Exception as e:
            pass

        try:
            super().destroy()
        except Exception as e:
            pass
