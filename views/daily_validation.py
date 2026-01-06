# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   winter MMXXV - two-level view (workstations + results)
# -----------------------------------------------------------------------------
"""
Daily QC Validation module.

Two-level view:
1. Workstation summary (default) - shows approval status per workstation
2. Results detail - drill down to see individual results for a workstation

Features:
    - Role-based validation control (Admin/Superuser can validate)
    - Workstation-level approval with audit trail (daily_approvals table)
    - Color coding: green=approved, yellow=pending, red=problems
    - Excel export of displayed data
"""

import sys
import tkinter as tk

from views.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox
from datetime import date, datetime
from calendarium import Calendarium


# Role constants
ROLE_ADMIN = 0
ROLE_SUPERUSER = 1
ROLE_TECHNICIAN = 2
ROLE_AUTOLOGIN = 3

# View modes
VIEW_WORKSTATIONS = "workstations"
VIEW_RESULTS = "results"


class UI(ParentView):
    """
    Daily QC Validation window with two-level view.

    Level 1: Workstation summary (default)
        - Shows all workstations with pending/problem counts
        - Quick approve for workstations without issues
        - Drill down to see details

    Level 2: Results detail
        - Shows individual results for selected workstation
        - Validate/invalidate individual results
    """

    def __init__(self, parent):
        """Initialize the validation window."""
        super().__init__(parent, name="daily_validation")

        if self._reusing:
            return

        self.title("Daily QC Validation")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)
        self.bind("<F5>", lambda e: self._refresh_current_view())

        # Internal state
        self.view_mode = VIEW_WORKSTATIONS
        self.selected_date = None
        self.selected_workstation_id = None
        self.selected_workstation_name = None
        self.can_validate = False

        # Data dictionaries
        self.dict_workstations = {}  # TreeView index -> workstation data
        self.dict_results = {}       # TreeView index -> result data

        # Build UI
        self._init_ui()
        self.show(on_screen=True)

    def _init_ui(self):
        """Build the complete UI."""
        paddings = {"padx": 5, "pady": 5}

        # Main frame
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        # Top frame: navigation and filters
        frm_top = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_top.pack(side=tk.TOP, fill=tk.X, **paddings)

        # Back button (hidden initially)
        self.btn_back = ttk.Button(
            frm_top,
            text="← Workstations",
            command=self._show_workstations_view
        )
        # Don't pack yet - will be shown when in results view

        # Date selector
        self.lbl_date = ttk.Label(frm_top, text="Date:")
        self.lbl_date.pack(side=tk.LEFT, **paddings)

        bg = self.engine.get_rgb(240, 240, 237)
        self.calendarium = Calendarium(frm_top, "", base_bg_color=bg)
        self.calendarium.pack(side=tk.LEFT, **paddings)
        self.calendarium.set_today()

        # Load button
        ttk.Button(
            frm_top,
            text="Load",
            command=self._refresh_current_view
        ).pack(side=tk.LEFT, padx=(10, 0))

        # View title label (shows current view context)
        self.lbl_view_title = ttk.Label(
            frm_top,
            text="",
            font=("TkDefaultFont", 10, "bold")
        )
        self.lbl_view_title.pack(side=tk.LEFT, padx=(20, 0))

        # Role indicator
        self.lbl_role = ttk.Label(frm_top, text="", foreground="blue")
        self.lbl_role.pack(side=tk.RIGHT, **paddings)

        # Middle frame: TreeView (will be reconfigured based on view mode)
        self.frm_tree = ttk.Frame(self.frm_main, style="App.TFrame")
        self.frm_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, **paddings)

        # Scrollbars
        self.sb_vert = ttk.Scrollbar(self.frm_tree, orient=tk.VERTICAL)
        self.sb_horiz = ttk.Scrollbar(self.frm_tree, orient=tk.HORIZONTAL)

        # TreeView - will be configured per view mode
        self.tree = ttk.Treeview(
            self.frm_tree,
            yscrollcommand=self.sb_vert.set,
            xscrollcommand=self.sb_horiz.set,
            height=15
        )
        self.sb_vert.config(command=self.tree.yview)
        self.sb_horiz.config(command=self.tree.xview)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.sb_vert.grid(row=0, column=1, sticky=tk.NS)
        self.sb_horiz.grid(row=1, column=0, sticky=tk.EW)

        self.frm_tree.rowconfigure(0, weight=1)
        self.frm_tree.columnconfigure(0, weight=1)

        # Statistics frame
        frm_stats = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_stats.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.lbl_stats = ttk.Label(frm_stats, text="")
        self.lbl_stats.pack(side=tk.LEFT)

        # Buttons frame
        self.frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        self.frm_buttons.pack(side=tk.TOP, fill=tk.X, **paddings)

        # Buttons will be created dynamically based on view mode
        self._create_workstation_buttons()

        # Close button (always visible)
        ttk.Button(
            self.frm_buttons,
            text="Close",
            command=self.on_close
        ).pack(side=tk.RIGHT, **paddings)

    def _create_workstation_buttons(self):
        """Create buttons for workstation view."""
        # Clear existing buttons (except Close)
        for widget in self.frm_buttons.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget("text") != "Close":
                widget.destroy()

        paddings = {"padx": 5, "pady": 5}

        self.btn_approve_ws = ttk.Button(
            self.frm_buttons,
            text="Approve Selected WS",
            command=self._on_approve_workstation
        )
        self.btn_approve_ws.pack(side=tk.LEFT, **paddings)

        self.btn_review = ttk.Button(
            self.frm_buttons,
            text="Review Details →",
            command=self._on_review_workstation
        )
        self.btn_review.pack(side=tk.LEFT, **paddings)

        ttk.Button(
            self.frm_buttons,
            text="Export",
            command=self._on_export
        ).pack(side=tk.LEFT, **paddings)

    def _create_results_buttons(self):
        """Create buttons for results view."""
        # Clear existing buttons (except Close)
        for widget in self.frm_buttons.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget("text") != "Close":
                widget.destroy()

        paddings = {"padx": 5, "pady": 5}

        self.btn_select_all = ttk.Button(
            self.frm_buttons,
            text="☑ Select All",
            command=self._on_select_all
        )
        self.btn_select_all.pack(side=tk.LEFT, **paddings)

        self.btn_validate = ttk.Button(
            self.frm_buttons,
            text="Validate Selected",
            command=self._on_validate_selected
        )
        self.btn_validate.pack(side=tk.LEFT, **paddings)

        self.btn_invalidate = ttk.Button(
            self.frm_buttons,
            text="Invalidate",
            command=self._on_invalidate
        )
        self.btn_invalidate.pack(side=tk.LEFT, **paddings)

        ttk.Button(
            self.frm_buttons,
            text="Export",
            command=self._on_export
        ).pack(side=tk.LEFT, **paddings)

    def _configure_tree_for_workstations(self):
        """Configure TreeView columns for workstation summary view."""
        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Remove old columns
        self.tree["columns"] = ()

        # Set new columns
        cols = ("workstation", "equipment", "total", "validated", "pending", "problems", "approved")
        self.tree["columns"] = cols
        self.tree["show"] = "headings"

        # Column headers
        self.tree.heading("workstation", text="Workstation", anchor=tk.W)
        self.tree.heading("equipment", text="Equipment", anchor=tk.W)
        self.tree.heading("total", text="Total", anchor=tk.CENTER)
        self.tree.heading("validated", text="Valid", anchor=tk.CENTER)
        self.tree.heading("pending", text="Pending", anchor=tk.CENTER)
        self.tree.heading("problems", text="Problems", anchor=tk.CENTER)
        self.tree.heading("approved", text="WS Approved", anchor=tk.CENTER)

        # Column widths
        self.tree.column("workstation", width=150, anchor=tk.W)
        self.tree.column("equipment", width=180, anchor=tk.W)
        self.tree.column("total", width=60, anchor=tk.CENTER)
        self.tree.column("validated", width=60, anchor=tk.CENTER)
        self.tree.column("pending", width=60, anchor=tk.CENTER)
        self.tree.column("problems", width=70, anchor=tk.CENTER)
        self.tree.column("approved", width=100, anchor=tk.CENTER)

        # Bindings
        self.tree.bind("<Double-Button-1>", self._on_workstation_double_click)
        self.tree.bind("<Button-1>", lambda e: None)  # Disable checkbox behavior

    def _configure_tree_for_results(self):
        """Configure TreeView columns for results detail view."""
        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Remove old columns
        self.tree["columns"] = ()

        # Set new columns
        cols = ("test_method", "batch", "level", "time", "result", "target", "sd", "zscore", "validated")
        self.tree["columns"] = cols
        self.tree["show"] = "tree headings"

        # Column headers
        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("test_method", text="Test Method", anchor=tk.W)
        self.tree.heading("batch", text="Batch", anchor=tk.W)
        self.tree.heading("level", text="Level", anchor=tk.CENTER)
        self.tree.heading("time", text="Time", anchor=tk.CENTER)
        self.tree.heading("result", text="Result", anchor=tk.E)
        self.tree.heading("target", text="Target", anchor=tk.E)
        self.tree.heading("sd", text="SD", anchor=tk.E)
        self.tree.heading("zscore", text="Z-Score", anchor=tk.CENTER)
        self.tree.heading("validated", text="Val", anchor=tk.CENTER)

        # Column widths
        self.tree.column("#0", width=40, stretch=False)
        self.tree.column("test_method", width=180, anchor=tk.W)
        self.tree.column("batch", width=90, anchor=tk.W)
        self.tree.column("level", width=60, anchor=tk.CENTER)
        self.tree.column("time", width=60, anchor=tk.CENTER)
        self.tree.column("result", width=80, anchor=tk.E)
        self.tree.column("target", width=80, anchor=tk.E)
        self.tree.column("sd", width=60, anchor=tk.E)
        self.tree.column("zscore", width=70, anchor=tk.CENTER)
        self.tree.column("validated", width=40, anchor=tk.CENTER)

        # Bindings
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-Button-1>", self._on_result_double_click)

    def on_open(self):
        """Entry point when opening the window."""
        self._check_user_permissions()
        self.calendarium.set_today()
        self._show_workstations_view()
        self.deiconify()
        self.lift()

    def _check_user_permissions(self):
        """Check user role and enable/disable validation controls."""
        try:
            user_role = self.engine.get_user_role()
            self.can_validate = user_role in (ROLE_ADMIN, ROLE_SUPERUSER)

            if self.can_validate:
                self.lbl_role.config(text="✓ Validation enabled", foreground="green")
            else:
                self.lbl_role.config(text="👁 View-only mode", foreground="orange")

        except Exception as e:
            self.can_validate = False
            self.lbl_role.config(text="⚠ View-only mode", foreground="red")
            self.engine.on_log(
                "_check_user_permissions",
                e, type(e), sys.modules[__name__]
            )

    def _get_selected_date(self):
        """Get selected date from Calendarium."""
        try:
            value = self.calendarium.get_date()
            if value is False or value is None:
                return None
            return value
        except Exception:
            return None

    def _refresh_current_view(self):
        """Refresh the current view."""
        if self.view_mode == VIEW_WORKSTATIONS:
            self._load_workstations()
        else:
            self._load_results()

    # =========================================================================
    # WORKSTATION VIEW
    # =========================================================================

    def _show_workstations_view(self):
        """Switch to workstation summary view."""
        self.view_mode = VIEW_WORKSTATIONS
        self.selected_workstation_id = None
        self.selected_workstation_name = None

        # Update UI
        self.btn_back.pack_forget()
        self.lbl_view_title.config(text="Workstation Summary")

        self._configure_tree_for_workstations()
        self._create_workstation_buttons()
        self._update_button_states()
        self._load_workstations()

    def _load_workstations(self):
        """Load workstation summary for selected date."""
        selected_date = self._get_selected_date()
        if selected_date is None:
            messagebox.showwarning("Validation", "Please select a valid date.")
            return

        self.selected_date = selected_date
        self.tree.delete(*self.tree.get_children())
        self.dict_workstations.clear()

        try:
            # Query to get workstation summary with result counts
            sql = """
                SELECT
                    w.workstation_id,
                    w.description AS workstation_name,
                    e.description AS equipment_name,
                    COUNT(r.result_id) AS total_results,
                    SUM(CASE WHEN r.validated = 1 THEN 1 ELSE 0 END) AS validated_count,
                    SUM(CASE WHEN r.validated = 0 THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE
                        WHEN r.validated = 0 AND b.sd > 0
                             AND ABS(r.result - b.target) > (b.sd * 3)
                        THEN 1 ELSE 0
                    END) AS problem_count,
                    da.approval_id,
                    da.approved_by,
                    da.approved_at,
                    u.first_name,
                    u.last_name
                FROM workstations w
                INNER JOIN equipments e ON w.equipment_id = e.equipment_id
                INNER JOIN sections s ON w.section_id = s.section_id
                LEFT JOIN results r ON r.workstation_id = w.workstation_id
                    AND DATE(r.received) = ?
                    AND r.status = 1
                    AND r.is_delete = 0
                LEFT JOIN batches b ON r.batch_id = b.batch_id
                    AND b.lab_id = ?
                LEFT JOIN daily_approvals da ON da.workstation_id = w.workstation_id
                    AND da.approval_date = ?
                LEFT JOIN users u ON da.approved_by = u.user_id
                WHERE w.status = 1
                    AND s.lab_id = ?
                GROUP BY w.workstation_id, w.description, e.description,
                         da.approval_id, da.approved_by, da.approved_at,
                         u.first_name, u.last_name
                HAVING total_results > 0
                ORDER BY w.description
            """

            lab_id = self.engine.current_ids.get("lab_id")
            args = (selected_date.isoformat(), lab_id, selected_date.isoformat(), lab_id)
            rows = self.engine.read(True, sql, args)

            if rows is None:
                rows = []

            total_ws = 0
            approved_ws = 0

            for row in rows:
                total_ws += 1
                item_id = self._insert_workstation_row(row)
                if row["approval_id"]:
                    approved_ws += 1

            self.lbl_stats.config(
                text=f"Workstations: {total_ws}  |  Approved: {approved_ws}  |  Pending: {total_ws - approved_ws}"
            )

        except Exception as e:
            self.engine.on_log(
                "_load_workstations",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to load workstations:\n{e}")

    def _insert_workstation_row(self, row):
        """Insert a workstation row with color coding."""
        ws_id = row["workstation_id"]
        ws_name = row["workstation_name"]
        eq_name = row["equipment_name"]
        total = row["total_results"] or 0
        validated = row["validated_count"] or 0
        pending = row["pending_count"] or 0
        problems = row["problem_count"] or 0
        approval_id = row["approval_id"]

        # Approval status
        if approval_id:
            approved_by = f"{row['first_name'] or ''} {row['last_name'] or ''}".strip()
            approved_text = f"✓ {approved_by}"
            color = self.engine.get_rgb(200, 255, 200)  # Green
        elif problems > 0:
            approved_text = "⚠ Problems"
            color = self.engine.get_rgb(255, 160, 160)  # Red
        elif pending > 0:
            approved_text = "Pending"
            color = self.engine.get_rgb(255, 255, 180)  # Yellow
        else:
            approved_text = "No data"
            color = None

        values = (ws_name, eq_name, total, validated, pending, problems, approved_text)

        tags = (color,) if color else ()
        item_id = self.tree.insert("", tk.END, values=values, tags=tags)

        if color:
            self.tree.tag_configure(color, background=color)

        # Store data
        self.dict_workstations[item_id] = row

        return item_id

    def _on_workstation_double_click(self, evt):
        """Handle double-click on workstation row - drill down to results."""
        item_id = self.tree.identify_row(evt.y)
        if not item_id or item_id not in self.dict_workstations:
            return

        row = self.dict_workstations[item_id]
        self._show_results_view(row["workstation_id"], row["workstation_name"])

    def _on_review_workstation(self):
        """Review button - drill down to selected workstation."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Review", "Please select a workstation.")
            return

        item_id = selection[0]
        row = self.dict_workstations.get(item_id)
        if row:
            self._show_results_view(row["workstation_id"], row["workstation_name"])

    def _on_approve_workstation(self):
        """Approve selected workstation."""
        if not self.can_validate:
            messagebox.showinfo("Validation", "You don't have permission to approve.")
            return

        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Approve", "Please select a workstation.")
            return

        item_id = selection[0]
        row = self.dict_workstations.get(item_id)
        if not row:
            return

        # Check if already approved
        if row["approval_id"]:
            messagebox.showinfo("Approve", "This workstation is already approved for today.")
            return

        # Check for problems
        if (row["problem_count"] or 0) > 0:
            if not messagebox.askyesno(
                "Warning",
                f"This workstation has {row['problem_count']} result(s) beyond ±3SD.\n\n"
                "Are you sure you want to approve it anyway?"
            ):
                return

        ws_name = row["workstation_name"]
        pending = row["pending_count"] or 0

        msg = f"Approve workstation '{ws_name}'?"
        if pending > 0:
            msg += f"\n\nThis will also validate {pending} pending result(s)."

        if not messagebox.askyesno("Confirm Approval", msg):
            return

        try:
            user_id = self.engine.log_user.get("user_id")
            ws_id = row["workstation_id"]

            # 1. Validate all pending results for this workstation
            if pending > 0:
                sql_validate = """
                    UPDATE results r
                    INNER JOIN batches b ON r.batch_id = b.batch_id
                    SET r.validated = 1,
                        r.validated_by = ?,
                        r.validated_at = NOW()
                    WHERE r.workstation_id = ?
                      AND DATE(r.received) = ?
                      AND r.validated = 0
                      AND r.status = 1
                      AND r.is_delete = 0
                      AND b.lab_id = ?
                """
                lab_id = self.engine.current_ids.get("lab_id")
                self.engine.write(sql_validate, (user_id, ws_id, self.selected_date.isoformat(), lab_id))

            # 2. Insert approval record
            sql_approve = """
                INSERT INTO daily_approvals (approval_date, workstation_id, approved_by)
                VALUES (?, ?, ?)
            """
            self.engine.write(sql_approve, (self.selected_date.isoformat(), ws_id, user_id))

            messagebox.showinfo("Success", f"Workstation '{ws_name}' approved.")
            self._load_workstations()

        except Exception as e:
            self.engine.on_log(
                "_on_approve_workstation",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to approve:\n{e}")

    # =========================================================================
    # RESULTS VIEW
    # =========================================================================

    def _show_results_view(self, workstation_id, workstation_name):
        """Switch to results detail view for specific workstation."""
        self.view_mode = VIEW_RESULTS
        self.selected_workstation_id = workstation_id
        self.selected_workstation_name = workstation_name

        # Update UI
        self.btn_back.pack(side=tk.LEFT, padx=5, pady=5, before=self.lbl_date)
        self.lbl_view_title.config(text=f"Results: {workstation_name}")

        self._configure_tree_for_results()
        self._create_results_buttons()
        self._update_button_states()
        self._load_results()

    def _load_results(self):
        """Load results for selected workstation and date."""
        if not self.selected_workstation_id:
            return

        self.tree.delete(*self.tree.get_children())
        self.dict_results.clear()

        try:
            sql = """
                SELECT
                    r.result_id,
                    r.batch_id,
                    r.workstation_id,
                    r.result,
                    r.received,
                    r.validated,
                    r.validated_by,
                    r.validated_at,
                    b.target,
                    b.sd,
                    b.lot_number,
                    b.description AS level,
                    t.description AS test_description,
                    s.sample
                FROM results r
                INNER JOIN batches b ON r.batch_id = b.batch_id
                INNER JOIN test_methods tm ON b.test_method_id = tm.test_method_id
                INNER JOIN tests t ON tm.test_id = t.test_id
                INNER JOIN samples s ON tm.sample_id = s.sample_id
                WHERE r.workstation_id = ?
                  AND DATE(r.received) = ?
                  AND r.status = 1
                  AND r.is_delete = 0
                  AND b.lab_id = ?
                ORDER BY t.description, r.received
            """

            lab_id = self.engine.current_ids.get("lab_id")
            args = (self.selected_workstation_id, self.selected_date.isoformat(), lab_id)
            rows = self.engine.read(True, sql, args)

            if rows is None:
                rows = []

            total = 0
            validated = 0

            for row in rows:
                total += 1
                if row["validated"] == 1:
                    validated += 1
                self._insert_result_row(row)

            self.lbl_stats.config(
                text=f"Total: {total}  |  Validated: {validated}  |  Pending: {total - validated}"
            )

        except Exception as e:
            self.engine.on_log(
                "_load_results",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to load results:\n{e}")

    def _insert_result_row(self, row):
        """Insert a result row with color coding."""
        result_id = row["result_id"]
        test_desc = row["test_description"]
        sample = row["sample"]
        result_val = float(row["result"])
        target = float(row["target"])
        sd = float(row["sd"])
        validated = row["validated"]
        lot_number = row.get("lot_number", "")
        level = row.get("level", "")

        # Format time
        received = row["received"]
        if isinstance(received, datetime):
            time_str = received.strftime("%H:%M")
        else:
            time_str = str(received)[:5]

        # Calculate Z-score
        if sd > 0:
            zscore = (result_val - target) / sd
            zscore_str = f"{zscore:.2f}"
        else:
            zscore = 0
            zscore_str = "-"

        # Validated indicator
        val_mark = "✓" if validated == 1 else ""

        # Color based on status
        color = self._compute_color(result_val, target, sd, validated)

        test_method_display = f"{test_desc}-{sample}"

        values = (
            test_method_display,
            lot_number,
            level,
            time_str,
            f"{result_val:.2f}",
            f"{target:.2f}",
            f"{sd:.2f}",
            zscore_str,
            val_mark
        )

        tags = ["unchecked"]
        if validated == 1:
            tags.append("validated")
        if color:
            tags.append(color)

        item_id = self.tree.insert(
            "", tk.END,
            text="☐",
            values=values,
            tags=tuple(tags)
        )

        self.dict_results[item_id] = row

        if color:
            self.tree.tag_configure(color, background=color)

        return item_id

    def _compute_color(self, result, target, sd, validated):
        """Compute color based on validation status and SD distance."""
        if validated == 1:
            return self.engine.get_rgb(200, 255, 200)  # Green

        if target == 0 or sd == 0:
            return None

        zscore = abs(result - target) / sd

        if zscore >= 3:
            return self.engine.get_rgb(255, 160, 160)  # Red
        elif zscore >= 2:
            return self.engine.get_rgb(255, 255, 180)  # Yellow

        return None

    def _on_tree_click(self, evt):
        """Handle click on checkbox column in results view."""
        if not self.can_validate:
            return

        region = self.tree.identify("region", evt.x, evt.y)
        if region != "tree":
            return

        item_id = self.tree.identify_row(evt.y)
        if not item_id:
            return

        tags = self.tree.item(item_id, "tags")
        if "validated" in tags:
            return

        # Toggle checkbox
        if "checked" in tags:
            new_tags = [t for t in tags if t != "checked"] + ["unchecked"]
            self.tree.item(item_id, text="☐", tags=new_tags)
        else:
            new_tags = [t for t in tags if t != "unchecked"] + ["checked"]
            self.tree.item(item_id, text="☑", tags=new_tags)

    def _on_result_double_click(self, evt):
        """Handle double-click on result - validate single result."""
        if not self.can_validate:
            messagebox.showinfo("Validation", "You don't have permission to validate.")
            return

        item_id = self.tree.identify_row(evt.y)
        if not item_id or item_id not in self.dict_results:
            return

        row = self.dict_results[item_id]
        if row["validated"] == 1:
            messagebox.showinfo("Validation", "This result is already validated.")
            return

        self._validate_results([row["result_id"]])

    def _on_select_all(self):
        """Toggle select all checkboxes."""
        if not self.can_validate:
            return

        pending_items = []
        checked_count = 0

        for item_id in self.tree.get_children():
            tags = self.tree.item(item_id, "tags")
            if "validated" not in tags:
                pending_items.append(item_id)
                if "checked" in tags:
                    checked_count += 1

        if not pending_items:
            messagebox.showinfo("Select All", "All results are already validated.")
            return

        # Toggle
        if checked_count == len(pending_items):
            for item_id in pending_items:
                tags = self.tree.item(item_id, "tags")
                new_tags = [t for t in tags if t not in ("checked", "unchecked")] + ["unchecked"]
                self.tree.item(item_id, text="☐", tags=new_tags)
        else:
            for item_id in pending_items:
                tags = self.tree.item(item_id, "tags")
                new_tags = [t for t in tags if t not in ("checked", "unchecked")] + ["checked"]
                self.tree.item(item_id, text="☑", tags=new_tags)

    def _on_validate_selected(self):
        """Validate all checked results."""
        if not self.can_validate:
            return

        result_ids = []
        for item_id in self.tree.get_children():
            tags = self.tree.item(item_id, "tags")
            if "checked" in tags:
                row = self.dict_results.get(item_id)
                if row and row["validated"] == 0:
                    result_ids.append(row["result_id"])

        if not result_ids:
            messagebox.showinfo("Validation", "No pending results selected.")
            return

        if messagebox.askyesno("Confirm", f"Validate {len(result_ids)} result(s)?"):
            self._validate_results(result_ids)

    def _validate_results(self, result_ids):
        """Validate the given result_ids."""
        try:
            user_id = self.engine.log_user.get("user_id")

            placeholders = ",".join("?" * len(result_ids))
            sql = f"""
                UPDATE results
                SET validated = 1,
                    validated_by = ?,
                    validated_at = NOW()
                WHERE result_id IN ({placeholders})
            """

            args = [user_id] + result_ids
            self.engine.write(sql, tuple(args))

            self._load_results()
            messagebox.showinfo("Success", f"{len(result_ids)} result(s) validated.")

        except Exception as e:
            self.engine.on_log(
                "_validate_results",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to validate:\n{e}")

    def _on_invalidate(self):
        """Invalidate a validated result."""
        if not self.can_validate:
            return

        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Invalidate", "Please select a result.")
            return

        item_id = selection[0]
        row = self.dict_results.get(item_id)

        if not row or row["validated"] == 0:
            messagebox.showinfo("Invalidate", "This result is not validated.")
            return

        if not messagebox.askyesno("Confirm", f"Invalidate result {row['result_id']}?"):
            return

        try:
            sql = """
                UPDATE results
                SET validated = 0,
                    validated_by = NULL,
                    validated_at = NULL
                WHERE result_id = ?
            """
            self.engine.write(sql, (row["result_id"],))

            self._load_results()
            messagebox.showinfo("Success", "Result invalidated.")

        except Exception as e:
            self.engine.on_log(
                "_on_invalidate",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to invalidate:\n{e}")

    # =========================================================================
    # COMMON
    # =========================================================================

    def _update_button_states(self):
        """Enable/disable buttons based on user role."""
        state = tk.NORMAL if self.can_validate else tk.DISABLED

        if self.view_mode == VIEW_WORKSTATIONS:
            if hasattr(self, 'btn_approve_ws'):
                self.btn_approve_ws.config(state=state)
        else:
            if hasattr(self, 'btn_select_all'):
                self.btn_select_all.config(state=state)
            if hasattr(self, 'btn_validate'):
                self.btn_validate.config(state=state)
            if hasattr(self, 'btn_invalidate'):
                self.btn_invalidate.config(state=state)

    def _on_export(self):
        """Export displayed data to Excel."""
        if not self.selected_date:
            messagebox.showinfo("Export", "Please load data first.")
            return

        try:
            self.engine.quick_data_analysis(self.selected_date, None)
            messagebox.showinfo("Export", f"Data exported for {self.selected_date}")

        except Exception as e:
            self.engine.on_log(
                "_on_export",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def on_close(self, evt=None):
        """Close the window."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.destroy()
