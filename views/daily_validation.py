# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   winter MMXXV - hierarchical treeview (workstations → results)
# -----------------------------------------------------------------------------
"""
Daily QC Validation module.

Hierarchical TreeView:
- Parent nodes: Workstations with aggregated counts
- Child nodes: Individual results (loaded on expand)

Features:
    - Role-based validation control (Admin/Superuser can validate)
    - Workstation-level approval with audit trail (daily_approvals table)
    - Color coding: green=approved, yellow=pending, red=problems
    - Expand/collapse to drill down into results
"""

import sys
import tkinter as tk

from views.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
from calendarium import Calendarium


# Role constants
ROLE_ADMIN = 0
ROLE_SUPERUSER = 1
ROLE_TECHNICIAN = 2
ROLE_AUTOLOGIN = 3

# Node type tags
TAG_WORKSTATION = "ws"
TAG_RESULT = "result"


class UI(ParentView):
    """
    Daily QC Validation window with hierarchical TreeView.

    Workstation nodes show:
        - Name, equipment, result counts, approval status

    Result nodes (children) show:
        - Test method, batch, result value, z-score, validation status
    """

    def __init__(self, parent):
        """Initialize the validation window."""
        super().__init__(parent, name="daily_validation")

        if self._reusing:
            return

        self.title("Daily QC Validation")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", self.on_close)
        self.bind("<F5>", lambda e: self._load_data())

        # Internal state
        self.selected_date = None
        self.can_validate = False

        # Data dictionaries
        self.dict_workstations = {}  # item_id -> workstation data
        self.dict_results = {}       # item_id -> result data
        self.loaded_ws = set()       # workstation_ids already loaded

        # Build UI
        self._init_ui()
        self.show(on_screen=True)

    def _init_ui(self):
        """Build the complete UI."""
        paddings = {"padx": 5, "pady": 5}

        # Main frame
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        # Top frame: filters
        frm_top = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_top.pack(side=tk.TOP, fill=tk.X, **paddings)

        # Date selector
        ttk.Label(frm_top, text="Date:").pack(side=tk.LEFT, **paddings)

        bg = self.engine.get_rgb(240, 240, 237)
        self.calendarium = Calendarium(frm_top, "", base_bg_color=bg)
        self.calendarium.pack(side=tk.LEFT, **paddings)
        self.calendarium.set_today()

        # Load button
        ttk.Button(
            frm_top,
            text="Load",
            command=self._load_data
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Role indicator
        self.lbl_role = ttk.Label(frm_top, text="", foreground="blue")
        self.lbl_role.pack(side=tk.RIGHT, **paddings)

        # Middle frame: TreeView
        frm_tree = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, **paddings)

        # Scrollbars
        sb_vert = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL)
        sb_horiz = ttk.Scrollbar(frm_tree, orient=tk.HORIZONTAL)

        # TreeView with hierarchical structure
        cols = ("equipment_batch", "counts_result", "problems_sd", "status")
        self.tree = ttk.Treeview(
            frm_tree,
            columns=cols,
            yscrollcommand=sb_vert.set,
            xscrollcommand=sb_horiz.set,
            height=18
        )
        sb_vert.config(command=self.tree.yview)
        sb_horiz.config(command=self.tree.xview)

        # Column headers
        self.tree.heading("#0", text="Workstation / Test", anchor=tk.W)
        self.tree.heading("equipment_batch", text="Equipment / Batch", anchor=tk.W)
        self.tree.heading("counts_result", text="Counts / Result", anchor=tk.CENTER)
        self.tree.heading("problems_sd", text="Problems / Z-Score", anchor=tk.CENTER)
        self.tree.heading("status", text="Status", anchor=tk.CENTER)

        # Column widths
        self.tree.column("#0", width=220, anchor=tk.W)
        self.tree.column("equipment_batch", width=160, anchor=tk.W)
        self.tree.column("counts_result", width=120, anchor=tk.CENTER)
        self.tree.column("problems_sd", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=120, anchor=tk.CENTER)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        sb_vert.grid(row=0, column=1, sticky=tk.NS)
        sb_horiz.grid(row=1, column=0, sticky=tk.EW)

        frm_tree.rowconfigure(0, weight=1)
        frm_tree.columnconfigure(0, weight=1)

        # Bindings
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        self.tree.bind("<Double-Button-1>", self._on_double_click)

        # Statistics frame
        frm_stats = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_stats.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.lbl_stats = ttk.Label(frm_stats, text="")
        self.lbl_stats.pack(side=tk.LEFT)

        # Buttons frame
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.btn_approve = ttk.Button(
            frm_buttons,
            text="Approve Workstation",
            command=self._on_approve_workstation
        )
        self.btn_approve.pack(side=tk.LEFT, **paddings)

        self.btn_validate = ttk.Button(
            frm_buttons,
            text="Validate Result",
            command=self._on_validate_result
        )
        self.btn_validate.pack(side=tk.LEFT, **paddings)

        self.btn_invalidate = ttk.Button(
            frm_buttons,
            text="Invalidate",
            command=self._on_invalidate
        )
        self.btn_invalidate.pack(side=tk.LEFT, **paddings)

        ttk.Button(
            frm_buttons,
            text="Close",
            command=self.on_close
        ).pack(side=tk.RIGHT, **paddings)

    def on_open(self):
        """Entry point when opening the window."""
        self._check_user_permissions()
        self.calendarium.set_today()
        self._load_data()
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

            self._update_button_states()

        except Exception as e:
            self.can_validate = False
            self.lbl_role.config(text="⚠ View-only mode", foreground="red")
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

    # =========================================================================
    # DATA LOADING
    # =========================================================================

    def _get_expanded_ws_ids(self):
        """Get list of currently expanded workstation IDs."""
        expanded = []
        for item_id in self.tree.get_children():
            if self.tree.item(item_id, "open"):
                row = self.dict_workstations.get(item_id)
                if row:
                    expanded.append(row["workstation_id"])
        return expanded

    def _expand_ws_ids(self, ws_ids):
        """Expand workstation nodes by their IDs."""
        for item_id, row in self.dict_workstations.items():
            if row["workstation_id"] in ws_ids:
                self.tree.item(item_id, open=True)
                # Trigger load of children
                self._on_expand(None, item_id)

    def _on_expand(self, evt, item_id=None):
        """Handle expand event - load results for workstation."""
        if item_id is None:
            item_id = self.tree.focus()
        if not item_id:
            return

        # Check if this is a workstation node
        tags = self.tree.item(item_id, "tags")
        if TAG_WORKSTATION not in tags:
            return

        row = self.dict_workstations.get(item_id)
        if not row:
            return

        ws_id = row["workstation_id"]

        # Already loaded?
        if ws_id in self.loaded_ws:
            return

        # Remove dummy child
        for child in self.tree.get_children(item_id):
            self.tree.delete(child)

        # Load results
        self._load_results_for_workstation(item_id, ws_id)
        self.loaded_ws.add(ws_id)

    def _load_data(self, preserve_expansion=False):
        """Load workstation summary for selected date."""
        selected_date = self._get_selected_date()
        if selected_date is None:
            messagebox.showwarning("Validation", "Please select a valid date.")
            return

        # Save expanded state if requested
        expanded_ws_ids = self._get_expanded_ws_ids() if preserve_expansion else []

        self.selected_date = selected_date
        self.tree.delete(*self.tree.get_children())
        self.dict_workstations.clear()
        self.dict_results.clear()
        self.loaded_ws.clear()

        try:
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
                self._insert_workstation_node(row)
                if row["approval_id"]:
                    approved_ws += 1

            self.lbl_stats.config(
                text=f"Workstations: {total_ws}  |  Approved: {approved_ws}  |  Pending: {total_ws - approved_ws}"
            )

            # Restore expanded state
            if expanded_ws_ids:
                self._expand_ws_ids(expanded_ws_ids)

        except Exception as e:
            self.engine.on_log(
                "_load_data",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to load data:\n{e}")

    def _insert_workstation_node(self, row):
        """Insert a workstation as parent node."""
        ws_id = row["workstation_id"]
        ws_name = row["workstation_name"]
        eq_name = row["equipment_name"]
        total = row["total_results"] or 0
        validated = row["validated_count"] or 0
        pending = row["pending_count"] or 0
        problems = row["problem_count"] or 0
        approval_id = row["approval_id"]

        # Status text and color
        if approval_id:
            approved_by = f"{row['first_name'] or ''} {row['last_name'] or ''}".strip()
            status_text = f"✓ {approved_by}"
            color = self.engine.get_rgb(200, 255, 200)  # Green
        elif problems > 0:
            status_text = "⚠ Problems"
            color = self.engine.get_rgb(255, 160, 160)  # Red
        elif pending > 0:
            status_text = "Pending"
            color = self.engine.get_rgb(255, 255, 180)  # Yellow
        else:
            status_text = "All validated"
            color = self.engine.get_rgb(200, 255, 200)  # Green

        counts_text = f"{total} tot / {pending} pend"
        problems_text = f"{problems} prob" if problems > 0 else ""

        values = (eq_name, counts_text, problems_text, status_text)
        tags = (TAG_WORKSTATION, color)

        # Insert with dummy child so it's expandable
        item_id = self.tree.insert(
            "", tk.END,
            text=ws_name,
            values=values,
            tags=tags,
            open=False
        )

        # Add dummy child for expand arrow
        self.tree.insert(item_id, tk.END, text="Loading...")

        # Configure color
        self.tree.tag_configure(color, background=color)

        # Store data
        self.dict_workstations[item_id] = row

    def _load_results_for_workstation(self, parent_id, ws_id):
        """Load individual results as children of workstation node."""
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
                    b.target,
                    b.sd,
                    b.lot_number,
                    b.description AS level,
                    t.description AS test_description,
                    s.sample,
                    u.first_name AS validated_first_name,
                    u.last_name AS validated_last_name
                FROM results r
                INNER JOIN batches b ON r.batch_id = b.batch_id
                INNER JOIN test_methods tm ON b.test_method_id = tm.test_method_id
                INNER JOIN tests t ON tm.test_id = t.test_id
                INNER JOIN samples s ON tm.sample_id = s.sample_id
                LEFT JOIN users u ON r.validated_by = u.user_id
                WHERE r.workstation_id = ?
                  AND DATE(r.received) = ?
                  AND r.status = 1
                  AND r.is_delete = 0
                  AND b.lab_id = ?
                ORDER BY t.description, r.received
            """

            lab_id = self.engine.current_ids.get("lab_id")
            args = (ws_id, self.selected_date.isoformat(), lab_id)
            rows = self.engine.read(True, sql, args)

            if rows is None:
                rows = []

            for row in rows:
                self._insert_result_node(parent_id, row)

        except Exception as e:
            self.engine.on_log(
                "_load_results_for_workstation",
                e, type(e), sys.modules[__name__]
            )

    def _insert_result_node(self, parent_id, row):
        """Insert a result as child node under workstation."""
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

        # Status
        if validated == 1:
            validated_by = f"{row.get('validated_first_name') or ''} {row.get('validated_last_name') or ''}".strip()
            status_text = f"✓ {validated_by}" if validated_by else "✓"
            color = self.engine.get_rgb(200, 255, 200)  # Green
        elif abs(zscore) >= 3:
            status_text = "⚠ >3SD"
            color = self.engine.get_rgb(255, 160, 160)  # Red
        elif abs(zscore) >= 2:
            status_text = "Pending"
            color = self.engine.get_rgb(255, 255, 180)  # Yellow
        else:
            status_text = "Pending"
            color = None

        test_name = f"{test_desc}-{sample}"
        batch_info = f"{lot_number} {level}".strip()
        result_str = f"{result_val:.2f} @ {time_str}"

        values = (batch_info, result_str, zscore_str, status_text)
        tags = [TAG_RESULT]
        if color:
            tags.append(color)

        item_id = self.tree.insert(
            parent_id, tk.END,
            text=f"  {test_name}",
            values=values,
            tags=tuple(tags)
        )

        if color:
            self.tree.tag_configure(color, background=color)

        # Store data
        self.dict_results[item_id] = row

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _get_selected_item(self):
        """Get selected item and its type."""
        selection = self.tree.selection()
        if not selection:
            return None, None, None

        item_id = selection[0]
        tags = self.tree.item(item_id, "tags")

        if TAG_WORKSTATION in tags:
            return item_id, TAG_WORKSTATION, self.dict_workstations.get(item_id)
        elif TAG_RESULT in tags:
            return item_id, TAG_RESULT, self.dict_results.get(item_id)

        return None, None, None

    def _on_double_click(self, evt):
        """Handle double-click - validate single result."""
        if not self.can_validate:
            return

        item_id = self.tree.identify_row(evt.y)
        if not item_id:
            return

        tags = self.tree.item(item_id, "tags")
        if TAG_RESULT not in tags:
            return

        row = self.dict_results.get(item_id)
        if not row:
            return

        if row["validated"] == 1:
            messagebox.showinfo("Validation", "This result is already validated.")
            return

        self._validate_result(row["result_id"], item_id)

    def _on_approve_workstation(self):
        """Approve selected workstation."""
        if not self.can_validate:
            messagebox.showinfo("Validation", "You don't have permission to approve.")
            return

        item_id, item_type, row = self._get_selected_item()

        if item_type != TAG_WORKSTATION:
            messagebox.showinfo("Approve", "Please select a workstation.")
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
            lab_id = self.engine.current_ids.get("lab_id")

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
                self.engine.write(sql_validate, (user_id, ws_id, self.selected_date.isoformat(), lab_id))

            # 2. Insert approval record
            sql_approve = """
                INSERT INTO daily_approvals (approval_date, workstation_id, approved_by)
                VALUES (?, ?, ?)
            """
            self.engine.write(sql_approve, (self.selected_date.isoformat(), ws_id, user_id))

            messagebox.showinfo("Success", f"Workstation '{ws_name}' approved.")
            self._load_data(preserve_expansion=True)

        except Exception as e:
            self.engine.on_log(
                "_on_approve_workstation",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to approve:\n{e}")

    def _on_validate_result(self):
        """Validate selected result."""
        if not self.can_validate:
            messagebox.showinfo("Validation", "You don't have permission to validate.")
            return

        item_id, item_type, row = self._get_selected_item()

        if item_type != TAG_RESULT:
            messagebox.showinfo("Validate", "Please select a result.")
            return

        if row["validated"] == 1:
            messagebox.showinfo("Validation", "This result is already validated.")
            return

        self._validate_result(row["result_id"], item_id)

    def _validate_result(self, result_id, item_id):
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
            self.engine.write(sql, (user_id, result_id))

            # Update tree display
            row = self.dict_results[item_id]
            row["validated"] = 1

            color = self.engine.get_rgb(200, 255, 200)
            values = list(self.tree.item(item_id, "values"))
            values[3] = "✓"
            self.tree.item(item_id, values=values, tags=(TAG_RESULT, color))
            self.tree.tag_configure(color, background=color)

            # Refresh parent workstation counts (preserve expansion)
            self._load_data(preserve_expansion=True)

        except Exception as e:
            self.engine.on_log(
                "_validate_result",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to validate:\n{e}")

    def _on_invalidate(self):
        """Invalidate a validated result."""
        if not self.can_validate:
            messagebox.showinfo("Validation", "You don't have permission to invalidate.")
            return

        item_id, item_type, row = self._get_selected_item()

        if item_type != TAG_RESULT:
            messagebox.showinfo("Invalidate", "Please select a result.")
            return

        if row["validated"] == 0:
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

            messagebox.showinfo("Success", "Result invalidated.")
            self._load_data(preserve_expansion=True)

        except Exception as e:
            self.engine.on_log(
                "_on_invalidate",
                e, type(e), sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to invalidate:\n{e}")

    def on_close(self, evt=None):
        """Close the window."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.destroy()
