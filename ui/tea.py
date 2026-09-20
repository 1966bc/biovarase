# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
TEA (Total Error Analysis) module of Biovarase.

This version replaces the Matplotlib-based multi-subplot figure with a
pure Tkinter implementation using TotalErrorCanvas, one dashboard per
batch. The goal is to keep the same calculations (TE, TEa, bias, CV,
z-score, limits) while presenting them in a compact, readable layout.
"""

import tkinter as tk

from ui.parent_view import ParentView
from tkinter import ttk

from total_error_canvas import TotalErrorCanvas


class UI(ParentView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="tea")
        if self._reusing:
            return

        self.engine = self.nametowidget(".").engine

        self.cvw = 0.0
        self.cvb = 0.0
        self.um = None
        self.selected_workstation = None
        self.elements = 0

        self._batches = []
        self._header_var = tk.StringVar(value="")

        self._build_ui()

        # Set initial size BEFORE centering
        self.geometry("700x500")
        self.minsize(600, 400)
        self.show()

    # ---------------------------------------------------------------------
    # UI LAYOUT
    # ---------------------------------------------------------------------
    def _build_ui(self):
        self.title("Total Error")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Frame(self, style="App.TFrame", padding=8)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # Header: test + workstation summary
        header = ttk.Frame(main, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self._header_var, style="App.TLabel")\
            .grid(row=0, column=0, sticky="w")

        # Container for per-batch dashboards
        self.frm_batches = ttk.Frame(main, style="App.TFrame")
        self.frm_batches.grid(row=1, column=0, sticky="nsew")
        self.frm_batches.columnconfigure(0, weight=1)

        ttk.Sizegrip(self).grid(row=1, column=0, sticky="se")

    # ---------------------------------------------------------------------
    # OPEN WINDOW AND INITIALIZE STATE
    # ---------------------------------------------------------------------
    def on_open(self, selected, selected_workstation, elements):
        """
        Initialize TEA window.

        Args:
            selected (dict): unified record for test_methods + goals.
            selected_workstation: tuple/list with workstation fields.
            elements (int): number of results to consider.
        """
        self.selected_workstation = selected_workstation
        self.elements = elements

        # Goals
        self.cvw = selected.get("cvw", 0) or 0
        self.cvb = selected.get("cvb", 0) or 0

        # Unit of measure
        unit_id = selected.get("unit_id")
        self.um = self.engine.get_um(unit_id) if unit_id is not None else None

        # Header text
        test_name = self.engine.get_test_name(selected["test_id"])
        ws_name = selected_workstation[3]
        ws_serial = selected_workstation[4]

        self.title(f"{test_name} — Total Error")
        self._header_var.set(
            f"Test: {test_name}   ·   Workstation: {ws_name}   ·   Serial: {ws_serial}"
        )

        # Load batches
        self.get_batches(selected)

    # ---------------------------------------------------------------------
    # LOAD BATCHES
    # ---------------------------------------------------------------------
    def get_batches(self, selected_test_method):
        """Load all active batches for the given test_method and workstation."""

        sql = (
            "SELECT * "
            "FROM batches "
            "WHERE test_method_id = ? "
            "  AND workstation_id = ? "
            "  AND status = 1 "
            "ORDER BY expiration DESC;"
        )

        args = (selected_test_method["test_method_id"], self.selected_workstation[0])

        rs = self.engine.db.read(True, sql, args)

        if not rs:
            return

        self._batches = rs
        self.set_values(rs)

    # ---------------------------------------------------------------------
    # PROCESS BATCHES AND BUILD DASHBOARDS
    # ---------------------------------------------------------------------
    def set_values(self, batches):
        """Build one TEA dashboard for each batch using TotalErrorCanvas."""

        # Clear previous dashboards
        for child in self.frm_batches.winfo_children():
            child.destroy()

        if not batches:
            return

        # SQL to collect recent results for each batch
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
            batch_id = batch["batch_id"]

            args = (batch_id, self.selected_workstation[0], self.elements)
            rs = self.engine.db.read(True, sql, args)

            if not rs:
                continue

            # Batch statistics
            target = batch["target"]
            sd = batch["sd"]

            series = self.engine.get_series(
                batch_id,
                self.selected_workstation[0],
                int(self.engine.get_observations()),
            )

            if not series:
                continue

            mean = self.engine.qc.get_mean(series)
            cv = self.engine.qc.get_cv(series)
            te = self.engine.qc.get_te(target, mean, cv)
            tea = self.engine.qc.get_tea(self.cvw, self.cvb)
            bias = self.engine.qc.get_bias(mean, target)
            z_score = self.engine.qc.get_zscore()

            x_data = self.get_x_data(rs)
            dates = x_data["dates"]
            date_from = dates[0] if dates else None
            date_to = dates[-1] if dates else None

            lower_raw = batch.get("lower", 0)
            upper_raw = batch.get("upper", 0)

            lower_limit = round(lower_raw, 2) if lower_raw is not None else 0
            upper_limit = round(upper_raw, 2) if upper_raw is not None else 0

            # Build batch title
            control_name = None
            control_id = batch.get("control_id")
            if control_id is not None:
                try:
                    control_name = self.engine.get_control_name(control_id)
                except Exception as e:
                    control_name = None

            lot_number = batch.get("lot_number")
            expiration = batch.get("expiration")

            title_parts = []
            if control_name:
                title_parts.append(control_name)
            if lot_number:
                title_parts.append(f"Lot {lot_number}")
            if expiration:
                title_parts.append(f"Exp {expiration}")

            title = "   ·   ".join(title_parts) if title_parts else f"Batch {batch_id}"

            # Unit text
            unit_txt = ""
            if self.um:
                um_desc = self.um.get("description")
                if um_desc:
                    unit_txt = um_desc

            # Dashboard container
            card = ttk.Frame(self.frm_batches, style="App.TFrame", padding=(8, 6))
            card.grid(row=row_index, column=0, sticky="ew", pady=(0, 8))
            card.columnconfigure(0, weight=1)

            # Limits row (textual)
            limits_text = f"Limits: {lower_limit:.2f} – {upper_limit:.2f}"
            ttk.Label(card, text=limits_text, style="App.TLabel")\
                .grid(row=0, column=0, sticky="w", pady=(0, 2))

            # Canvas
            canvas = TotalErrorCanvas(
                card,
                height=120,
                bg="white",
                highlightthickness=1,
                highlightbackground="#cccccc",
            )
            canvas.grid(row=1, column=0, sticky="ew")

            # Draw TEA dashboard
            canvas.draw_tea(
                title=title,
                te=te,
                tea=tea,
                bias=bias,
                cv=cv,
                z_score=z_score,
                n_series=len(series),
                n_results=len(rs),
                unit=unit_txt,
                date_from=date_from,
                date_to=date_to,
            )

            row_index += 1

    # ---------------------------------------------------------------------
    # X-AXIS DATA HELPER (for date range)
    # ---------------------------------------------------------------------
    def get_x_data(self, rs):
        """Build X-axis labels and date range from results list."""

        x_labels = []
        dates = []

        # Filter only active results
        filtered = [row for row in rs if row.get("status", 0) != 0]

        # Reverse to show oldest first
        for row in reversed(filtered):
            label = row["received_label"]
            x_labels.append(label)
            dates.append(label)

        return {"x_labels": x_labels, "dates": dates}

    # ---------------------------------------------------------------------
    # CANCEL / CLOSE
    # ---------------------------------------------------------------------
    def on_cancel(self, evt=None):
        """Close the TEA window."""
        self.destroy()
