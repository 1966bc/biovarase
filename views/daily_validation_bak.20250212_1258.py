# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   winter MMXXV - added role-based validation control & Excel export
# -----------------------------------------------------------------------------
"""
Daily QC Validation module.

Allows supervisors/admins to review and validate daily QC results.
Results are displayed with color coding based on SD distance from target.
Supports both single and batch validation.

Features:
    - Role-based validation control (Admin/Superuser can validate, others view-only)
    - Excel export of displayed data
    - Color coding based on validation status and SD distance
"""

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import date, datetime
from calendarium import Calendarium


# Role constants (from SESSION_CONTEXT.md)
ROLE_ADMIN = 0
ROLE_SUPERUSER = 1
ROLE_TECHNICIAN = 2
ROLE_AUTOLOGIN = 3


class UI(tk.Toplevel):
    """
    Daily QC Validation window (singleton).

    Displays all QC results for a selected date, grouped by category.
    Color-codes results based on validation status and SD distance:
        - GREEN: Validated
        - RED: Pending, beyond ±3SD (out of control)
        - YELLOW: Pending, between ±2SD and ±3SD (warning)
        - WHITE: Pending, within ±2SD (OK)

    Features:
        - Role-based validation control
        - Date selection via Calendarium (defaults to today)
        - Category filter (defaults to "All Categories")
        - Checkbox-based multi-selection
        - Batch validation (selected items) - Admin/Superuser only
        - Single validation (double-click) - Admin/Superuser only
        - Invalidate single result (for corrections) - Admin/Superuser only
        - Excel export of displayed data
    """

    _instance = None

    def __new__(cls, parent):
        """Singleton: only one instance allowed."""
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                cls._instance = None

        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
        """Initialize the validation window."""
        if getattr(self, "_initialized", False):
            return

        super().__init__(name="daily_validation")
        self._initialized = True

        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)

        try:
            self.transient(parent)
        except Exception as e:
            pass

        self.title("Daily QC Validation")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Hotkeys
        self.bind("<Escape>", self.on_close)
        self.bind("<F5>", lambda e: self._load_results())

        # Internal state
        self.dict_categories = {}
        self.dict_results = {}  # TreeView index -> result data dict
        self.selected_date = None
        self.can_validate = False  # Will be set based on user role

        # Build UI
        self._init_ui()

        # Center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)

    def _init_ui(self):
        """Build the complete UI."""
        paddings = {"padx": 5, "pady": 5}

        # Main frame
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, expand=True)

        # Top frame: filters
        frm_top = ttk.Frame(frm_main, style="App.TFrame")
        frm_top.pack(side=tk.TOP, fill=tk.X, **paddings)

        # Date selector
        ttk.Label(frm_top, text="Date:").pack(side=tk.LEFT, **paddings)
        bg = getattr(self.engine, "BASE_BG_RGB", self.engine.get_rgb(240, 240, 237))
        self.calendarium = Calendarium(frm_top, "", base_bg_color=bg)
        self.calendarium.pack(side=tk.LEFT, **paddings)
        self.calendarium.set_today()

        # Category filter
        ttk.Label(frm_top, text="Category:").pack(side=tk.LEFT, padx=(20, 5))
        self.cbCategories = ttk.Combobox(
            frm_top,
            state="readonly",
            width=25
        )
        self.cbCategories.pack(side=tk.LEFT, **paddings)
        self.cbCategories.bind("<<ComboboxSelected>>", lambda e: self._load_results())

        # Load button
        ttk.Button(
            frm_top,
            text="Load",
            command=self._load_results
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Middle frame: TreeView
        frm_tree = ttk.Frame(frm_main, style="App.TFrame")
        frm_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, **paddings)

        # Scrollbars
        sb_vert = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL)
        sb_horiz = ttk.Scrollbar(frm_tree, orient=tk.HORIZONTAL)

        # TreeView columns
        cols = (
            "test_method",
            "workstation",
            "time",
            "result",
            "target",
            "sd",
            "westgard",
            "validated"
        )

        self.tree = ttk.Treeview(
            frm_tree,
            columns=cols,
            show="tree headings",
            yscrollcommand=sb_vert.set,
            xscrollcommand=sb_horiz.set,
            height=15
        )

        sb_vert.config(command=self.tree.yview)
        sb_horiz.config(command=self.tree.xview)

        # Column headers
        self.tree.heading("#0", text="☐", anchor=tk.W)
        self.tree.heading("test_method", text="Test Method", anchor=tk.W)
        self.tree.heading("workstation", text="WS", anchor=tk.CENTER)
        self.tree.heading("time", text="Time", anchor=tk.CENTER)
        self.tree.heading("result", text="Result", anchor=tk.E)
        self.tree.heading("target", text="Target", anchor=tk.E)
        self.tree.heading("sd", text="SD", anchor=tk.E)
        self.tree.heading("westgard", text="Rule", anchor=tk.CENTER)
        self.tree.heading("validated", text="Val", anchor=tk.CENTER)

        # Column widths
        self.tree.column("#0", width=30, stretch=False)
        self.tree.column("test_method", width=200, anchor=tk.W)
        self.tree.column("workstation", width=50, anchor=tk.CENTER)
        self.tree.column("time", width=60, anchor=tk.CENTER)
        self.tree.column("result", width=70, anchor=tk.E)
        self.tree.column("target", width=70, anchor=tk.E)
        self.tree.column("sd", width=50, anchor=tk.E)
        self.tree.column("westgard", width=60, anchor=tk.CENTER)
        self.tree.column("validated", width=40, anchor=tk.CENTER)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        sb_vert.grid(row=0, column=1, sticky=tk.NS)
        sb_horiz.grid(row=1, column=0, sticky=tk.EW)

        frm_tree.rowconfigure(0, weight=1)
        frm_tree.columnconfigure(0, weight=1)

        # Bindings (will be enabled/disabled based on role)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-Button-1>", self._on_double_click)

        # Statistics frame
        frm_stats = ttk.Frame(frm_main, style="App.TFrame")
        frm_stats.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.lbl_stats = ttk.Label(
            frm_stats,
            text="Statistics: Total: 0  Validated: 0  Pending: 0"
        )
        self.lbl_stats.pack(side=tk.LEFT)

        # Role indicator label
        self.lbl_role = ttk.Label(frm_stats, text="", foreground="blue")
        self.lbl_role.pack(side=tk.RIGHT, **paddings)

        # Buttons frame
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.pack(side=tk.TOP, fill=tk.X, **paddings)

        self.btn_select_all = ttk.Button(
            frm_buttons,
            text="☑ Select All",
            command=self._on_select_all
        )
        self.btn_select_all.pack(side=tk.LEFT, **paddings)

        self.btn_validate = ttk.Button(
            frm_buttons,
            text="Validate Selected",
            command=self._on_validate_selected
        )
        self.btn_validate.pack(side=tk.LEFT, **paddings)

        self.btn_invalidate = ttk.Button(
            frm_buttons,
            text="Invalidate",
            command=self._on_invalidate
        )
        self.btn_invalidate.pack(side=tk.LEFT, **paddings)

        # Export button (always enabled)
        ttk.Button(
            frm_buttons,
            text="Export to Excel",
            command=self._on_export
        ).pack(side=tk.LEFT, **paddings)

        ttk.Button(
            frm_buttons,
            text="Close",
            command=self.on_close
        ).pack(side=tk.RIGHT, **paddings)

    def on_open(self):
        """
        Entry point when opening the window.

        - Check user role and enable/disable validation controls
        - Load categories
        - Set today's date
        - Load results
        """
        self._check_user_permissions()
        self._load_categories()
        self.calendarium.set_today()
        self._load_results()
        self.deiconify()
        self.lift()

    def _check_user_permissions(self):
        """
        Check user role and enable/disable validation controls.

        Only Admin (0) and Superuser (1) can validate.
        Technician (2) and Autologin (3) can only view.
        """
        try:
            user_role = self.engine.get_user_role()

            # Admin and Superuser can validate
            self.can_validate = user_role in (ROLE_ADMIN, ROLE_SUPERUSER)

            if self.can_validate:
                # Enable validation controls
                self.btn_select_all.config(state=tk.NORMAL)
                self.btn_validate.config(state=tk.NORMAL)
                self.btn_invalidate.config(state=tk.NORMAL)
                self.lbl_role.config(text="✓ Validation enabled", foreground="green")
            else:
                # Disable validation controls (view-only mode)
                self.btn_select_all.config(state=tk.DISABLED)
                self.btn_validate.config(state=tk.DISABLED)
                self.btn_invalidate.config(state=tk.DISABLED)
                self.lbl_role.config(text="👁 View-only mode", foreground="orange")

        except Exception as e:
            # Fail-safe: disable validation if role cannot be determined
            self.can_validate = False
            self.btn_select_all.config(state=tk.DISABLED)
            self.btn_validate.config(state=tk.DISABLED)
            self.btn_invalidate.config(state=tk.DISABLED)
            self.lbl_role.config(text="⚠ View-only mode", foreground="red")

            self.engine.on_log(
                "daily_validation._check_user_permissions",
                e,
                type(e),
                sys.modules[__name__]
            )

    def _load_categories(self):
        """Load categories into combobox."""
        try:
            sql = """
                SELECT category_id, description
                FROM categories
                WHERE status = 1
                ORDER BY description
            """
            rows = self.engine.read(True, sql, ())

            self.dict_categories.clear()
            self.dict_categories[0] = "All Categories"

            items = ["All Categories"]
            for row in rows:
                cat_id = row["category_id"]
                desc = row["description"]
                self.dict_categories[cat_id] = desc
                items.append(desc)

            self.cbCategories["values"] = items
            self.cbCategories.current(0)

        except Exception as e:
            self.engine.on_log(
                "daily_validation._load_categories",
                e,
                type(e),
                sys.modules[__name__]
            )

    def _get_selected_date(self):
        """Get selected date from Calendarium."""
        try:
            value = self.calendarium.get_date()
            if value is False or value is None:
                return None
            return value
        except Exception as e:
            return None

    def _get_selected_category_id(self):
        """Get selected category_id (0 = All)."""
        idx = self.cbCategories.current()
        if idx < 0:
            return 0

        # Map combo index to category_id
        selected_text = self.cbCategories.get()
        for cat_id, desc in self.dict_categories.items():
            if desc == selected_text:
                return cat_id
        return 0

    def _load_results(self, evt=None):
        """Load results for selected date and category."""
        selected_date = self._get_selected_date()

        if selected_date is None:
            messagebox.showwarning("Validation", "Please select a valid date.")
            return

        self.selected_date = selected_date
        category_id = self._get_selected_category_id()

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.dict_results.clear()

        try:
            # Build SQL with optional category filter
            sql = """
                SELECT
                    results.result_id,
                    results.batch_id,
                    results.run_number,
                    results.workstation_id,
                    results.result,
                    results.received,
                    results.status,
                    results.validated,
                    results.validated_by,
                    results.validated_at,
                    batches.target,
                    batches.sd,
                    batches.lot_number,
                    test_methods.test_method_id,
                    tests.description AS test_description,
                    categories.description AS category_description,
                    workstations.description AS workstation_description,
                    samples.sample
                FROM results
                INNER JOIN batches ON results.batch_id = batches.batch_id
                INNER JOIN test_methods ON batches.test_method_id = test_methods.test_method_id
                INNER JOIN tests ON test_methods.test_id = tests.test_id
                INNER JOIN categories ON test_methods.category_id = categories.category_id
                INNER JOIN workstations ON results.workstation_id = workstations.workstation_id
                INNER JOIN samples ON test_methods.sample_id = samples.sample_id
                WHERE DATE(results.received) = ?
                  AND results.status = 1
                  AND results.is_delete = 0
                  AND batches.lab_id = ?
            """

            args = [selected_date.isoformat(), self.engine.current_ids.get("lab_id")]

            if category_id > 0:
                sql += " AND test_methods.category_id = ?"
                args.append(category_id)

            sql += " ORDER BY results.received, tests.description"

            rows = self.engine.read(True, sql, tuple(args))

            # Fail-safe: handle None or empty results
            if rows is None:
                rows = []

            # Insert into tree
            for row in rows:
                self._insert_result_row(row)

            self._update_statistics()

        except Exception as e:
            self.engine.on_log(
                "daily_validation._load_results",
                e,
                type(e),
                sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to load results:\n{e}")

    def _compute_color(self, result, target, sd, validated):
        """
        Compute color based on validation status and SD distance.

        Priority:
        1. Green if validated (regardless of SD distance)
        2. Red if pending and beyond ±3SD
        3. Yellow if pending and between ±2SD and ±3SD
        4. White/None if pending and within ±2SD (OK)

        Args:
            result: Measured value
            target: Target value
            sd: Standard deviation
            validated: Validation flag (0=pending, 1=validated)

        Returns:
            str: RGB color string or None
        """
        # Green: Already validated (highest priority)
        if validated == 1:
            return self.engine.get_rgb(200, 255, 200)  # Light green

        # For pending results, check SD distance
        if target == 0 or sd == 0:
            return None

        up_2sd = target + (sd * 2)
        up_3sd = target + (sd * 3)
        dn_2sd = target - (sd * 2)
        dn_3sd = target - (sd * 3)

        # Red: Out of control (beyond ±3SD)
        if result >= up_3sd or result <= dn_3sd:
            return self.engine.get_rgb(255, 160, 160)  # Light red

        # Yellow: Warning (between ±2SD and ±3SD)
        if (up_2sd <= result < up_3sd) or (dn_3sd < result <= dn_2sd):
            return self.engine.get_rgb(255, 255, 180)  # Light yellow

        # White/None: OK (within ±2SD)
        return None

    def _insert_result_row(self, row):
        """Insert a single result row into the TreeView with color coding."""
        result_id = row["result_id"]
        test_desc = row["test_description"]
        sample = row["sample"]
        workstation = row["workstation_description"][:4]  # Abbreviate
        received = row["received"]
        result_val = row["result"]
        target = row["target"]
        sd = row["sd"]
        validated = row["validated"]

        # Format time (HH:MM)
        if isinstance(received, datetime):
            time_str = received.strftime("%H:%M")
        else:
            time_str = str(received)[:5]

        # Compute Westgard rule (simplified for display)
        westgard = "OK"  # Placeholder - TODO: Call engine.get_westgard_violation_rule()

        # Validated indicator
        val_mark = "✓" if validated == 1 else ""

        # Color: Green for validated, Yellow/Red for pending problems, None for pending OK
        color = self._compute_color(result_val, target, sd, validated)

        # Test method display (test + sample)
        test_method_display = f"{test_desc}-{sample}"

        # Insert into tree
        values = (
            test_method_display,
            workstation,
            time_str,
            f"{result_val:.2f}",
            f"{target:.2f}",
            f"{sd:.2f}",
            westgard,
            val_mark
        )

        # Build tags list
        tags = ["unchecked"]
        if validated == 1:
            tags.append("validated")
        if color:
            tags.append(color)

        item_id = self.tree.insert(
            "",
            tk.END,
            text="☐",
            values=values,
            tags=tuple(tags)
        )

        # Store result data
        self.dict_results[item_id] = row

        # Apply color tag if needed
        if color:
            self.tree.tag_configure(color, background=color)

    def _on_tree_click(self, evt):
        """
        Handle single click on checkbox column.

        Only allows checkbox toggling if user has validation permissions.
        """
        if not self.can_validate:
            return  # View-only mode: ignore clicks

        region = self.tree.identify("region", evt.x, evt.y)
        if region != "tree":
            return

        item_id = self.tree.identify_row(evt.y)
        if not item_id:
            return

        # Don't allow checking already validated results
        tags = self.tree.item(item_id, "tags")
        if "validated" in tags:
            return

        # Toggle checkbox for pending results
        if "checked" in tags:
            # Uncheck
            self.tree.item(item_id, text="☐", tags=[t for t in tags if t != "checked"] + ["unchecked"])
        else:
            # Check
            self.tree.item(item_id, text="☑", tags=[t for t in tags if t != "unchecked"] + ["checked"])

    def _on_double_click(self, evt):
        """
        Handle double-click: validate single result.

        Only works if user has validation permissions.
        """
        if not self.can_validate:
            messagebox.showinfo(
                "Validation Disabled",
                "You do not have permission to validate results.\n"
                "Only Administrators and Supervisors can validate."
            )
            return

        item_id = self.tree.identify_row(evt.y)
        if not item_id or item_id not in self.dict_results:
            return

        row = self.dict_results[item_id]

        # Check if already validated
        if row["validated"] == 1:
            messagebox.showinfo("Validation", "This result is already validated.")
            return

        # Validate single result
        self._validate_results([row["result_id"]])

    def _on_select_all(self):
        """
        Toggle select all checkboxes (only pending results).

        Only works if user has validation permissions.
        """
        if not self.can_validate:
            messagebox.showinfo(
                "Validation Disabled",
                "You do not have permission to validate results.\n"
                "Only Administrators and Supervisors can validate."
            )
            return

        # Count pending results
        pending_items = []
        checked_pending = 0

        for item_id in self.tree.get_children():
            tags = self.tree.item(item_id, "tags")
            if "validated" not in tags:  # Only pending
                pending_items.append(item_id)
                if "checked" in tags:
                    checked_pending += 1

        if not pending_items:
            messagebox.showinfo(
                "Select All",
                "All results are already validated.\nNothing to select."
            )
            return

        # Toggle: if all pending are checked, uncheck all; otherwise check all
        if checked_pending == len(pending_items):
            # Uncheck all pending
            for item_id in pending_items:
                tags = self.tree.item(item_id, "tags")
                color_tags = [t for t in tags if t not in ("checked", "unchecked")]
                self.tree.item(item_id, text="☐", tags=color_tags + ["unchecked"])
            self.btn_select_all.config(text="☑ Select All")
        else:
            # Check all pending
            for item_id in pending_items:
                tags = self.tree.item(item_id, "tags")
                color_tags = [t for t in tags if t not in ("checked", "unchecked")]
                self.tree.item(item_id, text="☑", tags=color_tags + ["checked"])
            self.btn_select_all.config(text="☐ Deselect All")

    def _on_validate_selected(self):
        """Validate all checked results."""
        if not self.can_validate:
            messagebox.showinfo(
                "Validation Disabled",
                "You do not have permission to validate results.\n"
                "Only Administrators and Supervisors can validate."
            )
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

        # Confirm
        msg = f"Validate {len(result_ids)} result(s)?"
        if messagebox.askyesno("Confirm Validation", msg):
            self._validate_results(result_ids)

    def _validate_results(self, result_ids):
        """Validate the given result_ids."""
        try:
            user_id = self.engine.log_user.get("user_id")

            if user_id is None:
                messagebox.showerror(
                    "Error",
                    "User ID not found. Please log in again."
                )
                return

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

            # Reload
            self._load_results()

            messagebox.showinfo("Success", f"{len(result_ids)} result(s) validated.")

        except Exception as e:
            self.engine.on_log(
                "daily_validation._validate_results",
                e,
                type(e),
                sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to validate:\n{e}")

    def _on_invalidate(self):
        """Invalidate a single validated result (for corrections)."""
        if not self.can_validate:
            messagebox.showinfo(
                "Invalidation Disabled",
                "You do not have permission to invalidate results.\n"
                "Only Administrators and Supervisors can invalidate."
            )
            return

        # Get selected item
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Invalidate", "Please select a result to invalidate.")
            return

        item_id = selection[0]
        row = self.dict_results.get(item_id)

        if not row:
            return

        if row["validated"] == 0:
            messagebox.showinfo("Invalidate", "This result is not validated.")
            return

        # Confirm
        msg = f"Invalidate result {row['result_id']}?\nThis action requires supervisor authorization."
        if not messagebox.askyesno("Confirm Invalidation", msg):
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

            # Reload
            self._load_results()

            messagebox.showinfo("Success", "Result invalidated.")

        except Exception as e:
            self.engine.on_log(
                "daily_validation._on_invalidate",
                e,
                type(e),
                sys.modules[__name__]
            )
            messagebox.showerror("Error", f"Failed to invalidate:\n{e}")

    def _on_export(self):
        """
        Export displayed results to Excel using the Exporter's quick_data_analysis method.

        This reuses existing export functionality instead of duplicating code (DRY principle).
        Respects the category filter selected in the combobox.
        """
        if not self.selected_date:
            messagebox.showinfo("Export", "Please select a date and load results first.")
            return

        try:
            # Get selected category (respects filter selection)
            category_id = self._get_selected_category_id()

            # Use existing quick_data_analysis from Exporter class
            # This generates a comprehensive Excel report for the selected date
            # Pass category_id to respect the filter (None or 0 = all, >0 = specific category)
            self.engine.quick_data_analysis(self.selected_date, category_id)

            # Build message showing what was exported
            category_name = self.cbCategories.get() if hasattr(self, 'cbCategories') else "All Categories"
            messagebox.showinfo(
                "Export Successful",
                f"QC data for {self.selected_date}\n"
                f"Category: {category_name}\n\n"
                f"The file has been saved and opened."
            )

        except Exception as e:
            self.engine.on_log(
                "daily_validation._on_export",
                e,
                type(e),
                sys.modules[__name__]
            )
            messagebox.showerror("Export Error", f"Failed to export:\n{e}")

    def _update_statistics(self):
        """Update statistics label."""
        total = len(self.dict_results)
        validated = sum(1 for row in self.dict_results.values() if row["validated"] == 1)
        pending = total - validated

        self.lbl_stats.config(
            text=f"Statistics: Total: {total}  Validated: {validated}  Pending: {pending}"
        )

    def on_close(self, evt=None):
        """Close the window."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.destroy()
