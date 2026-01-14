# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   winter MMXXV - simplified workstation-based validation
# -----------------------------------------------------------------------------
"""
Daily QC Validation module.

Simplified approach:
- Combobox to select workstation (shows pending count)
- Flat TreeView showing results for selected workstation
- Multiple selection for batch validation

Features:
    - Role-based validation control (Admin/Superuser can validate)
    - Workstation-level approval with audit trail (daily_approvals table)
    - Color coding: green=validated, yellow=pending, red=problems
"""

import sys
import tkinter as tk

from i18n import _
from views.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
from calendarium import Calendarium
import views.plots
import views.notes
import views.note


# User roles - imported from engine for consistency
from engine import (
    ROLE_APP_ADMIN, ROLE_COUNTRY_ADMIN, ROLE_REGIONAL_ADMIN,
    ROLE_LAB_ADMIN, ROLE_SUPERUSER, ROLE_TECHNICIAN, ROLE_VIEWER
)
# Legacy aliases
ROLE_ADMIN = ROLE_APP_ADMIN
ROLE_AUTOLOGIN = ROLE_VIEWER


class UI(ParentView):
    """
    Daily QC Validation window with workstation selector.

    User selects:
        1. Date
        2. Workstation from combobox
        3. Clicks Load to see results

    Results are shown in a flat TreeView for easy multi-selection.
    """

    def __init__(self, parent):
        """Initialize the validation window."""
        super().__init__(parent, name="daily_validation")

        if self._reusing:
            return

        self.title(_("Daily QC Validation"))
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)
        self.bind("<F5>", lambda e: self._on_load_click())

        # Internal state
        self.selected_date = None
        self.selected_ws_id = None
        self.can_validate = False

        # Data dictionaries
        self.dict_workstations = {}  # combobox index -> workstation data
        self.dict_results = {}       # item_id -> result data
        self.dict_actions = {}       # combobox index -> action data

        # Build UI
        self._build_ui()

        # Subscribe to result and note changes
        self.engine.subscribe("result_changed", self._on_result_changed)
        self.engine.subscribe("note_changed", self._on_note_changed)

        self.show(on_screen=True)

    def _build_ui(self):
        """Build the complete UI."""
        paddings = {"padx": 5, "pady": 5}

        # Main frame
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        # Top frame row 1: Date and Workstation selector
        frm_row1 = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_row1.pack(side=tk.TOP, fill=tk.X, **paddings)

        # Date selector
        ttk.Label(frm_row1, text=_("Date:")).pack(side=tk.LEFT, **paddings)

        bg = self.engine.get_rgb(240, 240, 237)
        self.calendarium = Calendarium(frm_row1, "", base_bg_color=bg)
        self.calendarium.pack(side=tk.LEFT, **paddings)
        self.calendarium.set_today()

        # Bind date change to reload workstations
        self.calendarium.day.trace_add("write", self._on_date_changed)
        self.calendarium.month.trace_add("write", self._on_date_changed)
        self.calendarium.year.trace_add("write", self._on_date_changed)

        # Workstation selector
        ttk.Label(frm_row1, text=_("Workstation:")).pack(side=tk.LEFT, padx=(15, 5))

        self.cbx_workstation = ttk.Combobox(
            frm_row1,
            state="readonly",
            width=20
        )
        self.cbx_workstation.pack(side=tk.LEFT, **paddings)
        self.cbx_workstation.bind("<<ComboboxSelected>>", self._on_workstation_selected)

        # Top frame row 2: Info, Filter, Load button, Role
        frm_row2 = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_row2.pack(side=tk.TOP, fill=tk.X, **paddings)

        # Workstation info label (shows totals when selected)
        self.lbl_ws_info = ttk.Label(frm_row2, text="", foreground="blue")
        self.lbl_ws_info.pack(side=tk.LEFT, **paddings)

        # Filter checkbox - show only problems
        self.var_only_problems = tk.BooleanVar(value=True)  # Default: show only problems
        self.chk_only_problems = ttk.Checkbutton(
            frm_row2,
            text=_("Only problems"),
            variable=self.var_only_problems
        )
        self.chk_only_problems.pack(side=tk.LEFT, padx=(15, 0))

        # Load button (Alt-L)
        self.btn_load = ttk.Button(
            frm_row2,
            text=_("Load"),
            command=self._on_load_click,
            underline=0
        )
        self.btn_load.pack(side=tk.LEFT, padx=(10, 0))
        self.bind("<Alt-l>", lambda e: self._on_load_click())

        # Role indicator
        self.lbl_role = ttk.Label(frm_row2, text="", foreground="blue")
        self.lbl_role.pack(side=tk.RIGHT, **paddings)

        # Middle frame: TreeView
        frm_tree = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, **paddings)

        # Scrollbars
        sb_vert = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL)
        sb_horiz = ttk.Scrollbar(frm_tree, orient=tk.HORIZONTAL)

        # TreeView - flat results list with multiple selection
        cols = ("batch", "time", "result", "zscore", "operator", "status")
        self.tree = ttk.Treeview(
            frm_tree,
            columns=cols,
            selectmode="extended",  # Allow Ctrl+Click / Shift+Click
            yscrollcommand=sb_vert.set,
            xscrollcommand=sb_horiz.set,
            height=18
        )
        sb_vert.config(command=self.tree.yview)
        sb_horiz.config(command=self.tree.xview)

        # Column headers
        self.tree.heading("#0", text=_("Test"), anchor=tk.W)
        self.tree.heading("batch", text=_("Batch"), anchor=tk.W)
        self.tree.heading("time", text=_("Time"), anchor=tk.CENTER)
        self.tree.heading("result", text=_("Result"), anchor=tk.CENTER)
        self.tree.heading("zscore", text=_("Z-Score"), anchor=tk.CENTER)
        self.tree.heading("operator", text=_("Operator"), anchor=tk.CENTER)
        self.tree.heading("status", text=_("Status"), anchor=tk.CENTER)

        # Column widths
        self.tree.column("#0", width=180, anchor=tk.W)
        self.tree.column("batch", width=120, anchor=tk.W)
        self.tree.column("time", width=60, anchor=tk.CENTER)
        self.tree.column("result", width=80, anchor=tk.CENTER)
        self.tree.column("zscore", width=80, anchor=tk.CENTER)
        self.tree.column("operator", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=120, anchor=tk.CENTER)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        sb_vert.grid(row=0, column=1, sticky=tk.NS)
        sb_horiz.grid(row=1, column=0, sticky=tk.EW)

        frm_tree.rowconfigure(0, weight=1)
        frm_tree.columnconfigure(0, weight=1)

        # Bindings
        self.tree.bind("<Double-Button-1>", self._on_double_click)

        # Statistics frame
        frm_stats = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_stats.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.lbl_stats = ttk.Label(frm_stats, text=_("Select a workstation and click Load"))
        self.lbl_stats.pack(side=tk.LEFT)

        # Buttons frame
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.btn_approve = ttk.Button(
            frm_buttons,
            text=_("Approve WS"),
            command=self._on_approve_workstation
        )
        self.btn_approve.pack(side=tk.LEFT, **paddings)

        self.btn_validate = ttk.Button(
            frm_buttons,
            text=_("Validate"),
            command=self._on_validate_result
        )
        self.btn_validate.pack(side=tk.LEFT, **paddings)

        self.btn_invalidate = ttk.Button(
            frm_buttons,
            text=_("Invalidate"),
            command=self._on_invalidate
        )
        self.btn_invalidate.pack(side=tk.LEFT, **paddings)

        # Separator
        ttk.Separator(frm_buttons, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Notes section
        ttk.Button(
            frm_buttons,
            text=_("Notes"),
            command=self._on_open_notes
        ).pack(side=tk.LEFT, **paddings)

        ttk.Button(
            frm_buttons,
            text=_("+ Note"),
            command=self._on_add_note
        ).pack(side=tk.LEFT, padx=2)

        # Quick action combobox
        ttk.Label(frm_buttons, text=_("Quick:")).pack(side=tk.LEFT, padx=(10, 2))
        self.cbx_quick_action = ttk.Combobox(
            frm_buttons,
            state="readonly",
            width=18
        )
        self.cbx_quick_action.pack(side=tk.LEFT, padx=2)

        ttk.Button(
            frm_buttons,
            text="+",
            width=2,
            command=self._on_quick_action
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            frm_buttons,
            text=_("Export"),
            command=self._on_export
        ).pack(side=tk.LEFT, **paddings)

        ttk.Button(
            frm_buttons,
            text=_("Close"),
            command=self.on_close
        ).pack(side=tk.RIGHT, **paddings)

    def on_open(self):
        """Entry point when opening the window."""
        self._check_user_permissions()
        self._load_actions()
        self.calendarium.set_today()
        self._load_workstations()
        self.deiconify()
        self.lift()

    def _load_actions(self):
        """Load available actions into quick action combobox."""
        try:
            sql = """
                SELECT action_id, code, description
                FROM actions
                WHERE status = 1
                ORDER BY description
            """
            rows = self.engine.read(True, sql, ())

            self.dict_actions.clear()
            display_values = []

            for idx, row in enumerate(rows or []):
                self.dict_actions[idx] = row
                display_values.append(_(row["description"]))

            self.cbx_quick_action["values"] = display_values
            if display_values:
                self.cbx_quick_action.current(0)

        except Exception as e:
            self.engine.on_log(
                "_load_actions",
                e, type(e), sys.modules[__name__]
            )

    def _check_user_permissions(self):
        """Check user role and enable/disable validation controls."""
        try:
            self.can_validate = self.engine.can_validate_qc()

            if self.can_validate:
                self.lbl_role.config(text=_("Validation enabled"), foreground="green")
            else:
                self.lbl_role.config(text=_("View-only mode"), foreground="orange")

            self._update_button_states()

        except Exception as e:
            self.can_validate = False
            self.lbl_role.config(text=_("View-only mode"), foreground="red")
            self.engine.on_log(
                "_check_user_permissions",
                e, type(e), sys.modules[__name__]
            )

    def _update_button_states(self):
        """Enable/disable buttons based on user role."""
        state = tk.NORMAL if self.can_validate else tk.DISABLED
        self.btn_approve.config(state=state)
        self.btn_validate.config(state=state)
        self.btn_invalidate.config(state=state)

    def _get_selected_date(self):
        """Get selected date from Calendarium."""
        try:
            value = self.calendarium.get_date()
            if value is False or value is None:
                return None
            return value
        except Exception:
            return None

    def _on_date_changed(self, *args):
        """Handle date change - reload workstations."""
        # Only reload if date is valid
        if self._get_selected_date() is not None:
            self._load_workstations()

    # =========================================================================
    # WORKSTATION LOADING
    # =========================================================================

    def _load_workstations(self):
        """Load workstations into combobox with pending counts."""
        selected_date = self._get_selected_date()
        if selected_date is None:
            return

        self.selected_date = selected_date
        self.dict_workstations.clear()
        self.cbx_workstation.set("")
        self.cbx_workstation["values"] = []

        try:
            sql = """
                SELECT
                    w.workstation_id,
                    w.description AS workstation_name,
                    e.description AS equipment_name,
                    COUNT(r.result_id) AS total_results,
                    SUM(CASE WHEN r.validated = 0 THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE
                        WHEN b.sd > 0 AND ABS(r.result - b.target) > (b.sd * 3)
                        THEN 1 ELSE 0
                    END) AS count_3sd,
                    SUM(CASE
                        WHEN b.sd > 0 AND ABS(r.result - b.target) > (b.sd * 2)
                             AND ABS(r.result - b.target) <= (b.sd * 3)
                        THEN 1 ELSE 0
                    END) AS count_2sd,
                    da.approval_id
                FROM workstations w
                INNER JOIN equipments e ON w.equipment_id = e.equipment_id
                INNER JOIN organizations section ON section.org_id = w.org_id
                LEFT JOIN results r ON r.workstation_id = w.workstation_id
                    AND DATE(r.received) = ?
                    AND r.status = 1
                    AND r.is_delete = 0
                LEFT JOIN batches b ON r.batch_id = b.batch_id
                LEFT JOIN daily_approvals da ON da.workstation_id = w.workstation_id
                    AND da.approval_date = ?
                WHERE w.status = 1
                    AND section.parent_id = ?
                    AND section.org_type = 'section'
                GROUP BY w.workstation_id, w.description, e.description, da.approval_id
                HAVING total_results > 0
                ORDER BY w.description
            """

            lab_id = self.engine.current_ids.get("lab_id")
            args = (selected_date.isoformat(), selected_date.isoformat(), lab_id)
            rows = self.engine.read(True, sql, args)

            if not rows:
                self.lbl_stats.config(text=_("No results for this date"))
                self.lbl_ws_info.config(text="")
                return

            display_values = []
            for idx, row in enumerate(rows):
                display_values.append(row["workstation_name"])
                self.dict_workstations[idx] = row

            self.cbx_workstation["values"] = display_values

            # Auto-select first workstation with pending results
            selected_idx = 0
            for idx, row in self.dict_workstations.items():
                if (row["pending_count"] or 0) > 0:
                    selected_idx = idx
                    break

            if display_values:
                self.cbx_workstation.current(selected_idx)
                self._update_ws_info(selected_idx)

            self.lbl_stats.config(
                text=_("Select a workstation and click Load")
            )

        except Exception as e:
            self.engine.on_log(
                "_load_workstations",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to load workstations:')}\n{e}")

    def _on_workstation_selected(self, evt=None):
        """Handle workstation selection from combobox."""
        idx = self.cbx_workstation.current()
        if idx >= 0:
            self._update_ws_info(idx)

    def _update_ws_info(self, idx):
        """Update workstation info label with totals, pending and QC problems."""
        row = self.dict_workstations.get(idx)
        if not row:
            self.lbl_ws_info.config(text="")
            return

        total = row["total_results"] or 0
        pending = row["pending_count"] or 0
        count_3sd = row["count_3sd"] or 0
        count_2sd = row["count_2sd"] or 0
        approved = row["approval_id"] is not None

        if approved:
            self.lbl_ws_info.config(
                text=f"✓ {_('Approved')} ({total} tot)",
                foreground="green"
            )
        elif count_3sd > 0:
            # Critical: has >3SD violations
            parts = [f"{total} tot"]
            if pending > 0:
                parts.append(f"{pending} pend")
            parts.append(f"⚠ {count_3sd} >3SD")
            if count_2sd > 0:
                parts.append(f"{count_2sd} >2SD")
            self.lbl_ws_info.config(
                text=", ".join(parts),
                foreground="red"
            )
        elif count_2sd > 0:
            # Warning: has >2SD
            parts = [f"{total} tot"]
            if pending > 0:
                parts.append(f"{pending} pend")
            parts.append(f"⚠ {count_2sd} >2SD")
            self.lbl_ws_info.config(
                text=", ".join(parts),
                foreground="orange"
            )
        elif pending > 0:
            self.lbl_ws_info.config(
                text=f"{total} tot, {pending} pending",
                foreground="orange"
            )
        else:
            self.lbl_ws_info.config(
                text=f"✓ {total} tot, {_('all validated')}",
                foreground="green"
            )

    def _on_load_click(self):
        """Handle Load button click - load results for selected workstation."""
        # First refresh workstations list
        self._load_workstations()

        # Then load results
        idx = self.cbx_workstation.current()
        if idx < 0:
            messagebox.showwarning(_("Validation"), _("Please select a workstation."), parent=self)
            return

        row = self.dict_workstations.get(idx)
        if not row:
            return

        self.selected_ws_id = row["workstation_id"]
        self._load_results()

    # =========================================================================
    # RESULTS LOADING
    # =========================================================================

    def _load_results(self):
        """Load results for selected workstation."""
        if not self.selected_ws_id or not self.selected_date:
            return

        self.tree.delete(*self.tree.get_children())
        self.dict_results.clear()

        try:
            # Build SQL with optional filter for problems only (|Z-score| >= 2)
            only_problems = self.var_only_problems.get()

            if only_problems:
                # Filter: show only results with |Z-score| >= 2
                sql = """
                    SELECT
                        r.result_id,
                        r.batch_id,
                        r.workstation_id,
                        r.result,
                        r.received,
                        r.validated,
                        r.validated_by,
                        r.tech_validated,
                        r.tech_validated_by,
                        r.operator_code,
                        b.target,
                        b.sd,
                        b.lot_number,
                        b.description AS level,
                        b.test_method_id,
                        t.description AS test_description,
                        t.test_id,
                        s.sample,
                        u.first_name AS validated_first_name,
                        u.last_name AS validated_last_name,
                        tu.first_name AS tech_first_name,
                        tu.last_name AS tech_last_name,
                        (SELECT COUNT(*) FROM notes n WHERE n.result_id = r.result_id AND n.status = 1) AS note_count
                    FROM results r
                    INNER JOIN batches b ON r.batch_id = b.batch_id
                    INNER JOIN test_methods tm ON b.test_method_id = tm.test_method_id
                    INNER JOIN tests t ON tm.test_id = t.test_id
                    INNER JOIN samples s ON tm.sample_id = s.sample_id
                    LEFT JOIN users u ON r.validated_by = u.user_id
                    LEFT JOIN users tu ON r.tech_validated_by = tu.user_id
                    WHERE r.workstation_id = ?
                      AND DATE(r.received) = ?
                      AND r.status = 1
                      AND r.is_delete = 0
                      AND b.sd > 0
                      AND ABS(r.result - b.target) >= (b.sd * 2)
                    ORDER BY ABS(r.result - b.target) / b.sd DESC, t.description
                """
            else:
                # Show all results
                sql = """
                    SELECT
                        r.result_id,
                        r.batch_id,
                        r.workstation_id,
                        r.result,
                        r.received,
                        r.validated,
                        r.validated_by,
                        r.tech_validated,
                        r.tech_validated_by,
                        r.operator_code,
                        b.target,
                        b.sd,
                        b.lot_number,
                        b.description AS level,
                        b.test_method_id,
                        t.description AS test_description,
                        t.test_id,
                        s.sample,
                        u.first_name AS validated_first_name,
                        u.last_name AS validated_last_name,
                        tu.first_name AS tech_first_name,
                        tu.last_name AS tech_last_name,
                        (SELECT COUNT(*) FROM notes n WHERE n.result_id = r.result_id AND n.status = 1) AS note_count
                    FROM results r
                    INNER JOIN batches b ON r.batch_id = b.batch_id
                    INNER JOIN test_methods tm ON b.test_method_id = tm.test_method_id
                    INNER JOIN tests t ON tm.test_id = t.test_id
                    INNER JOIN samples s ON tm.sample_id = s.sample_id
                    LEFT JOIN users u ON r.validated_by = u.user_id
                    LEFT JOIN users tu ON r.tech_validated_by = tu.user_id
                    WHERE r.workstation_id = ?
                      AND DATE(r.received) = ?
                      AND r.status = 1
                      AND r.is_delete = 0
                    ORDER BY t.description, r.received
                """

            args = (self.selected_ws_id, self.selected_date.isoformat())
            rows = self.engine.read(True, sql, args)

            if not rows:
                rows = []

            total = 0
            validated = 0
            pending = 0

            for row in rows:
                total += 1
                if row["validated"] == 1:
                    validated += 1
                else:
                    pending += 1
                self._insert_result_row(row)

            # Show filter status in stats
            filter_text = f" ({_('problems only')})" if only_problems else ""
            self.lbl_stats.config(
                text=f"{_('Results:')} {total}{filter_text}  |  {_('Validated:')} {validated}  |  {_('Pending:')} {pending}"
            )

        except Exception as e:
            self.engine.on_log(
                "_load_results",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to load results:')}\n{e}")

    def _insert_result_row(self, row):
        """Insert a result row into the TreeView."""
        result_val = float(row["result"])
        target = float(row["target"])
        sd = float(row["sd"])
        validated = row["validated"]
        lot_number = row.get("lot_number", "")
        level = row.get("level", "")
        test_desc = row["test_description"]
        sample = row["sample"]

        # Format time
        received = row["received"]
        if isinstance(received, datetime):
            time_str = received.strftime("%H:%M")
        else:
            time_str = str(received)[:5] if received else ""

        # Calculate Z-score
        if sd > 0:
            zscore = (result_val - target) / sd
            zscore_str = f"{zscore:+.2f} SD"
        else:
            zscore = 0
            zscore_str = "-"

        # Operator info
        operator_code = row.get("operator_code")
        if operator_code:
            operator_str = operator_code
        else:
            tech_name = f"{row.get('tech_first_name') or ''} {row.get('tech_last_name') or ''}".strip()
            operator_str = tech_name if tech_name else "-"

        # Note indicator (using text instead of emoji for Tcl compatibility)
        note_count = row.get("note_count", 0) or 0
        note_indicator = "[N] " if note_count > 0 else ""

        # Status and color
        if validated == 1:
            validated_by = f"{row.get('validated_first_name') or ''} {row.get('validated_last_name') or ''}".strip()
            status_text = f"{note_indicator}✓ {validated_by}" if validated_by else f"{note_indicator}✓"
            color = self.engine.get_rgb(200, 255, 200)  # Green
        elif abs(zscore) >= 3:
            status_text = f"{note_indicator}⚠ >3SD"
            color = self.engine.get_rgb(255, 160, 160)  # Red
        elif abs(zscore) >= 2:
            status_text = f"{note_indicator}{_('Pending')}"
            color = self.engine.get_rgb(255, 255, 180)  # Yellow
        else:
            status_text = f"{note_indicator}{_('Pending')}"
            color = None

        test_name = f"{test_desc}-{sample}"
        batch_info = f"{lot_number} {level}".strip()
        result_str = f"{result_val:.2f}"

        values = (batch_info, time_str, result_str, zscore_str, operator_str, status_text)
        tags = []
        if color:
            tags.append(color)

        item_id = self.tree.insert(
            "", tk.END,
            text=test_name,
            values=values,
            tags=tuple(tags) if tags else ()
        )

        if color:
            self.tree.tag_configure(color, background=color)

        # Store data
        self.dict_results[item_id] = row

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _select_result_or_next(self, result_id):
        """
        After validation, try to select:
        1. The same result if still visible
        2. Otherwise, the first pending result
        3. Otherwise, the first result in the list
        """
        # Try to find the validated result
        for item_id, row in self.dict_results.items():
            if row["result_id"] == result_id:
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
                self.tree.see(item_id)
                return

        # Not found (filtered out) - select first pending result
        for item_id, row in self.dict_results.items():
            if row["validated"] == 0:
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
                self.tree.see(item_id)
                return

        # No pending - select first result if any
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])
            self.tree.see(children[0])

    def _on_double_click(self, evt):
        """Handle double-click on result."""
        item_id = self.tree.identify_row(evt.y)
        if not item_id:
            return

        row = self.dict_results.get(item_id)
        if not row:
            return

        # Calculate z-score
        result_val = float(row["result"])
        target = float(row["target"])
        sd = float(row["sd"])
        zscore = abs((result_val - target) / sd) if sd > 0 else 0

        # If problem (|z| >= 2): show LJ chart
        if zscore >= 2:
            self._show_lj_chart(row)
            return

        # If OK and can validate: validate directly
        if not self.can_validate:
            messagebox.showinfo(_("Validation"), _("You don't have permission to validate."))
            return

        if row["validated"] == 1:
            messagebox.showinfo(_("Validation"), _("This result is already validated."))
            return

        self._validate_single_result(row["result_id"])

    def _show_lj_chart(self, row):
        """Open Levey-Jennings chart for the result's test method."""
        try:
            batch_id = row["batch_id"]
            workstation_id = row["workstation_id"]

            # Get test_method_id from batch
            sql_batch = "SELECT test_method_id FROM batches WHERE batch_id = ?"
            batch_row = self.engine.read(False, sql_batch, (batch_id,))
            if not batch_row:
                return

            test_method_id = batch_row["test_method_id"]

            selected_test_method = self.engine.get_selected(
                "test_methods", "test_method_id", test_method_id
            )
            if not selected_test_method:
                return

            # Get workstation details
            sql_ws = """
                SELECT workstation_id, description, status, description, serial
                FROM workstations WHERE workstation_id = ?
            """
            ws_row = self.engine.read(False, sql_ws, (workstation_id,))
            if not ws_row:
                return

            selected_workstation = (
                ws_row["workstation_id"],
                ws_row["description"],
                ws_row["status"],
                ws_row["description"],
                ws_row["serial"]
            )

            observations = self.engine.get_observations() or 30

            plots_window = views.plots.UI(self)
            plots_window.on_open(
                selected_test_method,
                selected_workstation,
                int(observations)
            )

        except Exception as e:
            self.engine.on_log(
                "_show_lj_chart",
                e, type(e), sys.modules[__name__]
            )

    def _on_approve_workstation(self):
        """Approve selected workstation."""
        if not self.can_validate:
            messagebox.showinfo(_("Validation"), _("You don't have permission to approve."))
            return

        if not self.selected_ws_id:
            messagebox.showinfo(_("Approve"), _("Please load a workstation first."), parent=self)
            return

        idx = self.cbx_workstation.current()
        row = self.dict_workstations.get(idx)
        if not row:
            return

        # Check if already approved
        if row["approval_id"]:
            messagebox.showinfo(_("Approve"), _("This workstation is already approved for today."))
            return

        ws_name = row["workstation_name"]
        pending = row["pending_count"] or 0

        msg = _("Approve workstation '{0}'?").format(ws_name)
        if pending > 0:
            msg += _("\n\nThis will also validate {0} pending result(s).").format(pending)

        if not messagebox.askyesno(_("Confirm Approval"), msg, parent=self):
            return

        try:
            user_id = self.engine.log_user.get("user_id")
            ws_id = row["workstation_id"]

            # 1. Validate all pending results
            if pending > 0:
                sql_validate = """
                    UPDATE results r
                    SET r.validated = 1,
                        r.validated_by = ?,
                        r.validated_at = NOW()
                    WHERE r.workstation_id = ?
                      AND DATE(r.received) = ?
                      AND r.validated = 0
                      AND r.status = 1
                      AND r.is_delete = 0
                """
                result = self.engine.write(sql_validate, (user_id, ws_id, self.selected_date.isoformat()))
                if result is None:
                    err = self.engine.last_write_error
                    msg = self.engine.get_user_friendly_db_error(err) if err else _("Save failed.")
                    messagebox.showerror(_("Error"), msg)
                    return

            # 2. Insert approval record
            sql_approve = """
                INSERT INTO daily_approvals (approval_date, workstation_id, approved_by)
                VALUES (?, ?, ?)
            """
            result = self.engine.write(sql_approve, (self.selected_date.isoformat(), ws_id, user_id))
            if result is None:
                err = self.engine.last_write_error
                msg = self.engine.get_user_friendly_db_error(err) if err else _("Save failed.")
                messagebox.showerror(_("Error"), msg)
                return

            messagebox.showinfo(_("Success"), _("Workstation '{0}' approved.").format(ws_name), parent=self)

            # Reload
            self._load_workstations()
            self._load_results()

        except Exception as e:
            self.engine.on_log(
                "_on_approve_workstation",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to approve:')}\n{e}")

    def _on_validate_result(self):
        """Validate selected result(s)."""
        if not self.can_validate:
            messagebox.showinfo(_("Validation"), _("You don't have permission to validate."))
            return

        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(_("Validate"), _("Please select one or more results."), parent=self)
            return

        # Collect pending results
        results_to_validate = []
        for item_id in selection:
            row = self.dict_results.get(item_id)
            if row and row["validated"] == 0:
                results_to_validate.append(row["result_id"])

        if not results_to_validate:
            messagebox.showinfo(_("Validation"), _("No pending results selected."), parent=self)
            return

        # Single result
        if len(results_to_validate) == 1:
            self._validate_single_result(results_to_validate[0])
            return

        # Multiple results - ask confirmation
        if not messagebox.askyesno(
            _("Confirm"),
            _("Validate {0} selected results?").format(len(results_to_validate)),
            parent=self
        ):
            return

        self._validate_batch(results_to_validate)

    def _validate_single_result(self, result_id):
        """Validate a single result."""
        try:
            user_id = self.engine.log_user.get("user_id")

            sql = """
                UPDATE results
                SET validated = 1,
                    validated_by = ?,
                    validated_at = NOW()
                WHERE result_id = ?
            """
            result = self.engine.write(sql, (user_id, result_id))
            if result is None:
                err = self.engine.last_write_error
                msg = self.engine.get_user_friendly_db_error(err) if err else _("Save failed.")
                messagebox.showerror(_("Error"), msg)
                return

            # Reload and reposition
            self._load_workstations()
            self._load_results()
            self._select_result_or_next(result_id)

        except Exception as e:
            self.engine.on_log(
                "_validate_single_result",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to validate:')}\n{e}")

    def _validate_batch(self, result_ids):
        """Validate multiple results with single UPDATE."""
        try:
            user_id = self.engine.log_user.get("user_id")
            count = len(result_ids)

            # Single UPDATE with IN clause - no loop
            placeholders = ",".join(["?"] * count)
            sql = f"""
                UPDATE results
                SET validated = 1,
                    validated_by = ?,
                    validated_at = NOW()
                WHERE result_id IN ({placeholders})
            """

            args = [user_id] + list(result_ids)
            result = self.engine.write(sql, tuple(args))

            if result is None:
                err = self.engine.last_write_error
                msg = self.engine.get_user_friendly_db_error(err) if err else _("Save failed.")
                messagebox.showerror(_("Error"), msg, parent=self)
                return

            messagebox.showinfo(
                _("Success"),
                _("{0} results validated.").format(count),
                parent=self
            )

            # Reload and reposition to first validated or next pending
            self._load_workstations()
            self._load_results()
            self._select_result_or_next(result_ids[0])

        except Exception as e:
            self.engine.on_log(
                "_validate_batch",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to validate:')}\n{e}")

    def _on_invalidate(self):
        """Invalidate a validated result."""
        if not self.can_validate:
            messagebox.showinfo(_("Validation"), _("You don't have permission to invalidate."))
            return

        selection = self.tree.selection()
        if not selection or len(selection) != 1:
            messagebox.showinfo(_("Invalidate"), _("Please select a single result."))
            return

        item_id = selection[0]
        row = self.dict_results.get(item_id)
        if not row:
            return

        if row["validated"] == 0:
            messagebox.showinfo(_("Invalidate"), _("This result is not validated."))
            return

        # Check permissions
        current_user_id = self.engine.log_user.get("user_id")
        current_user_role = self.engine.log_user.get("role")
        validated_by = row.get("validated_by")

        if current_user_role != 0 and validated_by != current_user_id:
            messagebox.showwarning(
                _("Invalidate"),
                _("You can only invalidate results you validated yourself."),
                parent=self
            )
            return

        if not messagebox.askyesno(_("Confirm"), _("Invalidate this result?"), parent=self):
            return

        try:
            sql = """
                UPDATE results
                SET validated = 0,
                    validated_by = NULL,
                    validated_at = NULL
                WHERE result_id = ?
            """
            result = self.engine.write(sql, (row["result_id"],))
            if result is None:
                err = self.engine.last_write_error
                msg = self.engine.get_user_friendly_db_error(err) if err else _("Save failed.")
                messagebox.showerror(_("Error"), msg, parent=self)
                return

            messagebox.showinfo(_("Success"), _("Result invalidated."), parent=self)

            # Reload and reposition
            result_id = row["result_id"]
            self._load_workstations()
            self._load_results()
            self._select_result_or_next(result_id)

        except Exception as e:
            self.engine.on_log(
                "_on_invalidate",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to invalidate:')}\n{e}")

    def _on_export(self):
        """Export daily validation data to Excel."""
        if not self.selected_date:
            messagebox.showinfo(_("Export"), _("Please load data first."))
            return

        try:
            self.engine.quick_data_analysis(self.selected_date, None)
        except Exception as e:
            self.engine.on_log(
                "_on_export",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to export:')}\n{e}")

    # =========================================================================
    # NOTES
    # =========================================================================

    def _on_open_notes(self):
        """Open notes view for selected result."""
        selection = self.tree.selection()
        if not selection or len(selection) != 1:
            messagebox.showinfo(_("Notes"), _("Please select a single result."), parent=self)
            return

        item_id = selection[0]
        row = self.dict_results.get(item_id)
        if not row:
            return

        # Prepare context for notes view (it expects selected_test, selected_batch, selected_result)
        self.selected_test = {"description": row["test_description"], "test_id": row.get("test_id")}
        self.selected_batch = {
            "lot_number": row.get("lot_number", ""),
            "description": row.get("level", ""),
            "batch_id": row["batch_id"],
            "test_method_id": row.get("test_method_id")
        }
        self.selected_result = row

        # Open notes view
        try:
            notes_window = views.notes.UI(self)
            notes_window.on_open()
        except Exception as e:
            self.engine.on_log(
                "_on_open_notes",
                e, type(e), sys.modules[__name__]
            )

    def _on_add_note(self):
        """Open note editor to add a new note to selected result."""
        selection = self.tree.selection()
        if not selection or len(selection) != 1:
            messagebox.showinfo(_("Notes"), _("Please select a single result."), parent=self)
            return

        item_id = selection[0]
        row = self.dict_results.get(item_id)
        if not row:
            return

        # Prepare context for note editor
        self.selected_test = {"description": row["test_description"], "test_id": row.get("test_id")}
        self.selected_batch = {
            "lot_number": row.get("lot_number", ""),
            "description": row.get("level", ""),
            "batch_id": row["batch_id"],
            "test_method_id": row.get("test_method_id")
        }
        self.selected_result = row
        self.selected_item = None  # None = INSERT mode

        # Open note editor directly
        try:
            note_window = views.note.UI(self, index=None)
            note_window.on_open()
        except Exception as e:
            self.engine.on_log(
                "_on_add_note",
                e, type(e), sys.modules[__name__]
            )

    def _on_quick_action(self):
        """Add a quick note with selected action to selected result(s)."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(_("Notes"), _("Please select one or more results."), parent=self)
            return

        action_idx = self.cbx_quick_action.current()
        if action_idx < 0:
            messagebox.showinfo(_("Notes"), _("Please select an action."), parent=self)
            return

        action = self.dict_actions.get(action_idx)
        if not action:
            return

        action_id = action["action_id"]
        action_desc = _(action["description"])

        # Confirm
        count = len(selection)
        if count == 1:
            msg = _("Add note '{0}' to selected result?").format(action_desc)
        else:
            msg = _("Add note '{0}' to {1} selected results?").format(action_desc, count)

        if not messagebox.askyesno(_("Confirm"), msg, parent=self):
            return

        # Insert notes
        try:
            import datetime
            today = datetime.date.today()
            user_id = self.engine.log_user.get("user_id")

            for item_id in selection:
                row = self.dict_results.get(item_id)
                if not row:
                    continue

                result_id = row["result_id"]

                sql = """
                    INSERT INTO notes (result_id, action_id, description, modified, status, created_by, created_at)
                    VALUES (?, ?, '', ?, 1, ?, NOW())
                """
                self.engine.write(sql, (result_id, action_id, today, user_id))

            messagebox.showinfo(
                _("Success"),
                _("Note added to {0} result(s).").format(count),
                parent=self
            )

            # Reload to show note indicators
            self._load_results()

            # Reselect first item
            if selection:
                first_row = self.dict_results.get(selection[0])
                if first_row:
                    self._select_result_or_next(first_row["result_id"])

        except Exception as e:
            self.engine.on_log(
                "_on_quick_action",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror(_("Error"), f"{_('Failed to add note:')}\n{e}", parent=self)

    def on_close(self, evt=None):
        """Close the window."""
        self.engine.unsubscribe("result_changed", self._on_result_changed)
        self.engine.unsubscribe("note_changed", self._on_note_changed)
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.destroy()

    def _on_result_changed(self, result_id):
        """Handle result_changed event - reload if visible."""
        if self.winfo_exists() and self.winfo_viewable() and self.selected_ws_id:
            self._load_workstations()
            self._load_results()

    def _on_note_changed(self, note_id=None):
        """Handle note_changed event - reload to update note indicators."""
        if self.winfo_exists() and self.winfo_viewable() and self.selected_ws_id:
            self._load_results()
