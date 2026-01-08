# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   January 2026
# -----------------------------------------------------------------------------

"""
Youden Selector Dialog - Select two batches for Youden plot.

Provides a user-friendly dialog to select workstation, test, and two batch
levels for generating a Youden plot, without requiring pre-selection.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
from views.child_view import ChildView


class UI(ChildView):
    """
    Dialog for selecting two batches for Youden plot.

    Flow:
    1. Select workstation from dropdown
    2. Select test (filtered by workstation)
    3. Select Level 1 batch (filtered by workstation + test)
    4. Select Level 2 batch (filtered, excludes Level 1)
    5. Click Plot to generate Youden chart
    """

    def __init__(self, parent, callback, preselect_workstation_id=None, preselect_test_method_id=None):
        """
        Initialize the selector dialog.

        Args:
            parent: Parent window
            callback: Function to call with selected data when Plot is clicked.
                      Signature: callback(test_method, workstation, batches, data)
            preselect_workstation_id: Optional workstation_id to pre-select
            preselect_test_method_id: Optional test_method_id to pre-select
        """
        super().__init__(parent, name="youden_selector")

        self.callback = callback
        self._preselect_workstation_id = preselect_workstation_id
        self._preselect_test_method_id = preselect_test_method_id

        # Data storage
        self.workstations = []      # List of workstation dicts
        self.test_methods = []      # List of test_method dicts
        self.batches_level1 = []    # List of batch dicts for level 1
        self.batches_level2 = []    # List of batch dicts for level 2

        # Selection variables
        self.workstation_var = tk.StringVar()
        self.test_var = tk.StringVar()
        self.level1_var = tk.StringVar()
        self.level2_var = tk.StringVar()

        self.title(_("Select Batches for Youden Plot"))

        self._build_ui()
        self._load_workstations()
        self.show()

    def _build_ui(self):
        """Build the dialog UI."""
        # Main frame with padding
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill=tk.BOTH, expand=True)

        # Grid configuration
        frm.columnconfigure(1, weight=1)

        row = 0

        # Workstation
        ttk.Label(frm, text=_("Workstation:")).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        self.cb_workstation = ttk.Combobox(
            frm, textvariable=self.workstation_var,
            state="readonly", width=40
        )
        self.cb_workstation.grid(row=row, column=1, sticky="ew", pady=(0, 8))
        self.cb_workstation.bind("<<ComboboxSelected>>", self._on_workstation_selected)

        row += 1

        # Test
        ttk.Label(frm, text=_("Test:")).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        self.cb_test = ttk.Combobox(
            frm, textvariable=self.test_var,
            state="readonly", width=40
        )
        self.cb_test.grid(row=row, column=1, sticky="ew", pady=(0, 8))
        self.cb_test.bind("<<ComboboxSelected>>", self._on_test_selected)

        row += 1

        # Separator
        ttk.Separator(frm, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=12
        )

        row += 1

        # Level 1
        ttk.Label(frm, text=_("Level 1:")).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        self.cb_level1 = ttk.Combobox(
            frm, textvariable=self.level1_var,
            state="readonly", width=40
        )
        self.cb_level1.grid(row=row, column=1, sticky="ew", pady=(0, 8))
        self.cb_level1.bind("<<ComboboxSelected>>", self._on_level1_selected)

        row += 1

        # Level 2
        ttk.Label(frm, text=_("Level 2:")).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        self.cb_level2 = ttk.Combobox(
            frm, textvariable=self.level2_var,
            state="readonly", width=40
        )
        self.cb_level2.grid(row=row, column=1, sticky="ew", pady=(0, 8))

        row += 1

        # Buttons frame
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(16, 0))

        ttk.Button(
            btn_frame, text=_("Plot"), command=self._on_plot
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame, text=_("Cancel"), command=self.on_cancel
        ).pack(side=tk.LEFT)

    def _load_workstations(self):
        """Load workstations for the current section and apply pre-selection."""
        section_id = self.engine.get_section_id()
        if not section_id:
            return

        sql = """
            SELECT workstation_id, description, serial
            FROM workstations
            WHERE section_id = ? AND status = 1
            ORDER BY description
        """

        rows = self.engine.read(True, sql, (section_id,))
        self.workstations = list(rows) if rows else []

        values = [f"{ws['description']} ({ws['serial']})" for ws in self.workstations]
        self.cb_workstation["values"] = values

        # Clear dependent comboboxes
        self._clear_tests()

        # Apply pre-selection if provided
        if self._preselect_workstation_id:
            for idx, ws in enumerate(self.workstations):
                if ws["workstation_id"] == self._preselect_workstation_id:
                    self.cb_workstation.current(idx)
                    self._on_workstation_selected()
                    break

    def _on_workstation_selected(self, evt=None):
        """Handle workstation selection - load tests for this workstation."""
        self._clear_tests()

        idx = self.cb_workstation.current()
        if idx < 0:
            return

        workstation = self.workstations[idx]
        workstation_id = workstation["workstation_id"]

        # Get test methods assigned to this workstation that have batches
        sql = """
            SELECT DISTINCT
                tm.test_method_id,
                t.description AS test_name,
                s.description AS sample_name
            FROM test_methods tm
            JOIN tests t ON tm.test_id = t.test_id
            JOIN samples s ON tm.sample_id = s.sample_id
            JOIN workstation_test_methods wtm ON wtm.test_method_id = tm.test_method_id
            JOIN batches b ON b.test_method_id = tm.test_method_id
                          AND b.workstation_id = wtm.workstation_id
            WHERE wtm.workstation_id = ?
              AND tm.status = 1
              AND b.status = 1
            ORDER BY t.description, s.description
        """

        rows = self.engine.read(True, sql, (workstation_id,))
        self.test_methods = list(rows) if rows else []

        values = [f"{tm['test_name']} - {tm['sample_name']}" for tm in self.test_methods]
        self.cb_test["values"] = values

        # Apply pre-selection if provided
        if self._preselect_test_method_id:
            for idx, tm in enumerate(self.test_methods):
                if tm["test_method_id"] == self._preselect_test_method_id:
                    self.cb_test.current(idx)
                    self._on_test_selected()
                    # Clear pre-selection to avoid re-applying on manual change
                    self._preselect_test_method_id = None
                    break

    def _on_test_selected(self, evt=None):
        """Handle test selection - load batches for this workstation + test."""
        self._clear_batches()

        ws_idx = self.cb_workstation.current()
        test_idx = self.cb_test.current()

        if ws_idx < 0 or test_idx < 0:
            return

        workstation = self.workstations[ws_idx]
        test_method = self.test_methods[test_idx]

        sql = """
            SELECT batch_id, description, lot_number,
                   DATE_FORMAT(expiration, '%d-%m-%Y') AS expiration_str,
                   target, sd
            FROM batches
            WHERE test_method_id = ?
              AND workstation_id = ?
              AND status = 1
            ORDER BY rank, description
        """

        rows = self.engine.read(True, sql, (
            test_method["test_method_id"],
            workstation["workstation_id"]
        ))

        self.batches_level1 = list(rows) if rows else []

        values = [f"{b['description']} ({b['lot_number']})" for b in self.batches_level1]
        self.cb_level1["values"] = values

    def _on_level1_selected(self, evt=None):
        """Handle Level 1 selection - update Level 2 excluding Level 1."""
        self.level2_var.set("")
        self.cb_level2["values"] = []
        self.batches_level2 = []

        idx = self.cb_level1.current()
        if idx < 0:
            return

        selected_batch_id = self.batches_level1[idx]["batch_id"]

        # Level 2 options = all batches except the one selected in Level 1
        self.batches_level2 = [
            b for b in self.batches_level1
            if b["batch_id"] != selected_batch_id
        ]

        values = [f"{b['description']} ({b['lot_number']})" for b in self.batches_level2]
        self.cb_level2["values"] = values

    def _clear_tests(self):
        """Clear test combobox and dependent fields."""
        self.test_var.set("")
        self.cb_test["values"] = []
        self.test_methods = []
        self._clear_batches()

    def _clear_batches(self):
        """Clear batch comboboxes."""
        self.level1_var.set("")
        self.level2_var.set("")
        self.cb_level1["values"] = []
        self.cb_level2["values"] = []
        self.batches_level1 = []
        self.batches_level2 = []

    def _on_plot(self):
        """Validate selection and call the callback to generate plot."""
        # Validate all selections
        ws_idx = self.cb_workstation.current()
        test_idx = self.cb_test.current()
        level1_idx = self.cb_level1.current()
        level2_idx = self.cb_level2.current()

        if ws_idx < 0:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select a workstation."),
                parent=self
            )
            return

        if test_idx < 0:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select a test."),
                parent=self
            )
            return

        if level1_idx < 0 or level2_idx < 0:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select both Level 1 and Level 2 batches."),
                parent=self
            )
            return

        # Get selected objects
        workstation = self.workstations[ws_idx]
        test_method_partial = self.test_methods[test_idx]
        batch1 = self.batches_level1[level1_idx]
        batch2 = self.batches_level2[level2_idx]

        # Get full test_method record
        test_method = self.engine.get_selected(
            "test_methods",
            "test_method_id",
            test_method_partial["test_method_id"]
        )

        # Get full workstation record
        workstation_full = self.engine.get_selected(
            "workstations",
            "workstation_id",
            workstation["workstation_id"]
        )

        # Get full batch records
        batch1_full = self.engine.get_selected("batches", "batch_id", batch1["batch_id"])
        batch2_full = self.engine.get_selected("batches", "batch_id", batch2["batch_id"])

        # Get series data for each batch
        observations = int(self.engine.get_observations())

        series1 = self.engine.get_series(
            batch1["batch_id"],
            workstation["workstation_id"],
            observations
        )
        series2 = self.engine.get_series(
            batch2["batch_id"],
            workstation["workstation_id"],
            observations
        )

        # Validate data
        if not series1 or not series2:
            messagebox.showwarning(
                self.engine.app_title,
                _("Not enough data to plot a Youden chart.\n"
                  "Both selected batches must have at least one result."),
                parent=self
            )
            return

        # Close dialog
        self.on_cancel()

        # Call callback with the data
        self.callback(
            test_method,
            workstation_full,
            [batch1_full, batch2_full],
            [series1, series2]
        )
