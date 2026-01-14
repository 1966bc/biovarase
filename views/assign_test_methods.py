# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   ver MMXXV - extended Listbox columns (test, code, sample, method, unit)
#           refactored with column constants for maintainability (DRY principle)
#-----------------------------------------------------------------------------

import tkinter as tk

from i18n import _
from views.child_view import ChildView
from tkinter import ttk
from tkinter import messagebox


class UI(ChildView):
    """
    Dialog to assign Test Methods to a single workstation.

    The dialog is opened by workstation_test_methods.UI and receives:
        - target workstation record (dict from engine.get_selected)
        - an optional list of already assigned test_method_id.

    Behaviour:
        - Loads all active test_methods belonging to the same SITE of the workstation,
          excluding those already mapped in workstation_test_methods.
        - Shows for each method:
            * test name
            * code
            * sample type
            * method
            * unit of measure
        - On confirmation, inserts one row into workstation_test_methods and refreshes
          the parent window.

    Architecture:
        - Uses fixed-width monospaced font (TkFixedFont) to simulate table columns
        - Column widths defined as class constants (single source of truth)
        - Centralized parsing method to extract fields from formatted rows
    """

    # ------------------------------------------------------------------
    # Column Layout Constants (Single Source of Truth)
    # ------------------------------------------------------------------
    COL_TEST_WIDTH = 40      # Test name (e.g., "Glucose", "Creatinine")
    COL_CODE_WIDTH = 10      # Test code (e.g., "GLU", "CREA")
    COL_SAMPLE_WIDTH = 12    # Sample type (e.g., "Serum", "Plasma")
    COL_METHOD_WIDTH = 25    # Method (e.g., "Enzymatic", "HPLC-MS/MS")
    COL_UNIT_WIDTH = 10      # Unit (e.g., "mg/dL", "ng/mL")
    COL_SPACING = 2          # Spaces between columns

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(self, parent):
        super().__init__(parent, name="assign_test_methods")

        self.resizable(True, True)
        self.bind("<Return>", self._assign_current)
        self.bind("<Alt-a>", self._assign_current)

        # State
        self.workstation = None          # dict: current target workstation
        self.already_assigned = []       # list[int], kept for compatibility / future checks

        # site_context is a COPY of engine.current_ids at open time
        # (site_id, comp_id, lab_id, section_id, ...)
        self.site_context = {}

        # Search
        self.search_var = tk.StringVar()
        self.items_var = tk.StringVar()
        self.all_items = []  # Full list for filtering: [(test_method_id, label), ...]

        self._build_ui()

        # Bind search filtering
        self.search_var.trace_add("write", self._on_search_changed)

        # Subscribe to tests changes (Observer pattern)
        self.engine.subscribe("tests_changed", self._on_tests_changed)

        self.show()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        frame = ttk.Frame(self, style="App.TFrame", padding=8)
        frame.pack(fill=tk.BOTH, expand=1)

        # Top bar: search + items count
        frm_top = ttk.Frame(frame, style="App.TFrame")
        frm_top.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(frm_top, text=_("Search:"), style="App.TLabel").pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(frm_top, textvariable=self.search_var, width=25)
        self.entry_search.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(frm_top, textvariable=self.items_var, style="App.TLabel").pack(side=tk.LEFT)

        # Listbox with scrollbar
        frm_list = ttk.Frame(frame, style="App.TFrame")
        frm_list.pack(fill=tk.BOTH, expand=1)

        sb = ttk.Scrollbar(frm_list, orient=tk.VERTICAL)
        self.lstItems = tk.Listbox(
            frm_list,
            yscrollcommand=sb.set,
            exportselection=False,
            font="TkFixedFont",  # Monospaced font for column alignment
        )
        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self._assign_current)
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y, expand=0)

        # Set reasonable window size for table display
        self.update_idletasks()
        min_width = 900   # Wide enough for all columns (40+10+12+25+10 + spacing)
        min_height = 600  # Show ~20-25 rows comfortably
        self.minsize(min_width, min_height)
        
        # Set initial geometry (can be resized by user)
        self.geometry(f"{min_width}x{min_height}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def on_open(self, target_workstation, already_assigned_ids=None):
        """
        Initialize dialog state and populate the list for the given workstation.

        Args:
            target_workstation: Dictionary containing workstation details
            already_assigned_ids: Optional list of already assigned test_method_id
        """
        # Store state
        self.workstation = target_workstation or {}
        self.already_assigned = list(already_assigned_ids or [])

        # Use global hierarchical context (already loaded by main),
        # but store a COPY to avoid aliasing mutable global state.
        ids = getattr(self.engine, "current_ids", {}) or {}
        self.site_context = dict(ids)

        lab_id = self.site_context.get("lab_id")
        workstation_id = self.workstation.get("workstation_id")

        # If we don't have a valid lab_id or workstation_id → nothing to show
        if not lab_id or not workstation_id:
            self.lstItems.delete(0, tk.END)
            self.title(_("Assign test methods"))
            return

        # Title
        lab_name = self._get_lab_name(lab_id)
        target_name = self.workstation.get("description", _("workstation"))
        self.title(f"{lab_name} — {_('Assign test methods to')} {target_name}")

        # Fill list (lab + workstation_id so NOT EXISTS always filters correctly)
        self.set_values(lab_id, workstation_id)

        self.show()

        try:
            self.entry_search.focus_set()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers (context)
    # ------------------------------------------------------------------
    def _get_lab_name(self, lab_id: int) -> str:
        """
        Get laboratory name from organizations table.

        Args:
            lab_id: Lab org_id

        Returns:
            Lab name or "Lab" if not found
        """
        sql = "SELECT description FROM organizations WHERE org_id = ?"
        row = self.engine.read(False, sql, (lab_id,))
        return row["description"] if row else _("Lab")

    # ------------------------------------------------------------------
    # List population
    # ------------------------------------------------------------------
    def set_values(self, lab_id=None, workstation_id=None):
        """
        Populate the list of assignable test methods for the given lab context
        and target workstation_id.

        The query:
            - restricts to active tests / test_methods
            - limits to test methods in sections under the current lab
            - excludes already mapped methods using NOT EXISTS.

        Args:
            lab_id: Lab org_id (from current_ids["lab_id"]) to filter test methods
            workstation_id: Workstation ID to check existing assignments
        """
        self.lstItems.delete(0, tk.END)
        self.dict_items = {}
        idx = 0

        # Use lab_id from current_ids or parameter
        lab_id = self.engine.current_ids.get("lab_id") or lab_id
        if not lab_id or not workstation_id:
            return

        # Query uses organizations table
        # test_methods.org_id references a section, we filter sections under this lab
        sql = """
            SELECT
                test_methods.test_method_id              AS test_method_id,
                tests.description                        AS test_description,
                test_methods.code                        AS code,
                samples.description                      AS sample_description,
                methods.description                      AS method_description,
                units.description                        AS unit
            FROM tests
            JOIN test_methods
                ON tests.test_id = test_methods.test_id
            JOIN organizations section
                ON test_methods.org_id = section.org_id
            JOIN samples
                ON test_methods.sample_id = samples.sample_id
            JOIN methods
                ON test_methods.method_id = methods.method_id
            JOIN units
                ON test_methods.unit_id = units.unit_id
            WHERE tests.status = 1
              AND test_methods.status = 1
              AND section.parent_id = ?
              AND section.org_type = 'section'
              AND NOT EXISTS (
                    SELECT 1
                    FROM workstation_test_methods
                    WHERE workstation_test_methods.workstation_id = ?
                      AND workstation_test_methods.test_method_id = test_methods.test_method_id
              )
            ORDER BY tests.description ASC
        """
        rs = self.engine.read(True, sql, (lab_id, workstation_id)) or []

        # Store all items for filtering
        self.all_items = []
        for row in rs:
            test_method_id = int(row["test_method_id"])
            label = self._format_label(row)
            self.all_items.append((test_method_id, label))

        # Apply current filter
        self._filter_items()

    def _filter_items(self):
        """Filter items based on search text."""
        self.lstItems.delete(0, tk.END)
        self.dict_items = {}

        search_text = self.search_var.get().lower().strip()

        idx = 0
        for test_method_id, label in self.all_items:
            if not search_text or search_text in label.lower():
                self.lstItems.insert(tk.END, label)
                self.dict_items[idx] = test_method_id
                idx += 1

        total = len(self.all_items)
        shown = self.lstItems.size()
        if search_text:
            self.items_var.set(f"{_('Items')}: {shown}/{total}")
        else:
            self.items_var.set(f"{_('Items')}: {total}")

    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._filter_items()

    def _format_label(self, row: dict) -> str:
        """
        Build a fixed-width label for the Listbox row, using a monospaced font.

        Columns:
            1) Test name
            2) Code
            3) Sample type
            4) Method
            5) Unit

        Args:
            row: Dictionary with test method data from database

        Returns:
            Formatted string with fixed-width columns
        """
        # Extract and sanitize fields
        test_desc   = (row.get("test_description") or "").strip()
        code        = (row.get("code") or "").strip()
        sample_desc = (row.get("sample_description") or "").strip()
        method_desc = (row.get("method_description") or "").strip()
        unit        = (row.get("unit") or "").strip()

        # Truncate to column widths (prevent overflow)
        test_desc   = test_desc[:self.COL_TEST_WIDTH]
        code        = code[:self.COL_CODE_WIDTH]
        sample_desc = sample_desc[:self.COL_SAMPLE_WIDTH]
        method_desc = method_desc[:self.COL_METHOD_WIDTH]
        unit        = unit[:self.COL_UNIT_WIDTH]

        # Build formatted string with fixed-width columns
        spacing = " " * self.COL_SPACING
        label = (
            f"{test_desc:<{self.COL_TEST_WIDTH}}"
            f"{spacing}"
            f"{code:<{self.COL_CODE_WIDTH}}"
            f"{spacing}"
            f"{sample_desc:<{self.COL_SAMPLE_WIDTH}}"
            f"{spacing}"
            f"{method_desc:<{self.COL_METHOD_WIDTH}}"
            f"{spacing}"
            f"{unit:<{self.COL_UNIT_WIDTH}}"
        )
        return label

    def _parse_listbox_row(self, raw: str) -> dict:
        """
        Parse a formatted Listbox row back into individual fields.

        This method is the inverse of _format_label(): it extracts the fields
        from the fixed-width formatted string using the same column widths.

        Args:
            raw: Formatted string from Listbox.get()

        Returns:
            Dictionary with parsed fields: test, code, sample, method, unit
        """
        pos = 0

        # Extract test name
        test = raw[pos:pos + self.COL_TEST_WIDTH].strip()
        pos += self.COL_TEST_WIDTH + self.COL_SPACING

        # Extract code
        code = raw[pos:pos + self.COL_CODE_WIDTH].strip()
        pos += self.COL_CODE_WIDTH + self.COL_SPACING

        # Extract sample type
        sample = raw[pos:pos + self.COL_SAMPLE_WIDTH].strip()
        pos += self.COL_SAMPLE_WIDTH + self.COL_SPACING

        # Extract method
        method = raw[pos:pos + self.COL_METHOD_WIDTH].strip()
        pos += self.COL_METHOD_WIDTH + self.COL_SPACING

        # Extract unit (rest of string)
        unit = raw[pos:].strip()

        return {
            "test": test,
            "code": code,
            "sample": sample,
            "method": method,
            "unit": unit
        }

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------
    def _assign_current(self, _evt=None):
        """
        Assign the currently selected list item to the target workstation.

        Workflow:
            1. Get selected test method from Listbox
            2. Parse formatted row to extract fields
            3. Show confirmation dialog
            4. Insert into workstation_test_methods table
            5. Refresh parent window and this dialog

        Args:
            _evt: Optional Tkinter event (for keyboard/mouse bindings)
        """
        sel = self.lstItems.curselection()
        if not sel:
            return

        index = sel[0]
        test_method_id = self.dict_items.get(index)
        if test_method_id is None:
            return

        # Get workstation name for the message
        target_name = self.workstation.get("description", "workstation")

        # Get formatted row from Listbox
        raw = self.lstItems.get(index)

        # Parse fields using centralized parser
        fields = self._parse_listbox_row(raw)

        # Build compact label for confirmation dialog
        pretty_label = f"{fields['test']} — {fields['sample']} — {fields['method']} ({fields['unit']})"

        msg = (
            f"{_('Assign test method:')}\n\n"
            f"   {pretty_label}\n\n"
            f"{_('to workstation:')}\n\n"
            f"   {target_name}?"
        )

        if not messagebox.askyesno(
            self.engine.app_title,
            msg,
            parent=self,
        ):
            return

        try:
            workstation_id = self.workstation.get("workstation_id")
            if workstation_id is None:
                return

            # Insert assignment into database
            sql = """
                INSERT INTO workstation_test_methods (workstation_id, test_method_id)
                VALUES (?, ?)
            """
            args = (workstation_id, test_method_id)
            last_id = self.engine.write(sql, args)
            if last_id is None:
                err = self.engine.last_write_error
                if err:
                    msg = self.engine.get_user_friendly_db_error(err)
                else:
                    msg = _("Save failed.")
                messagebox.showerror(self.engine.app_title, msg, parent=self)
                return

            # Refresh parent (workstation methods list) if it exposes a loader
            if hasattr(self.parent, "_set_tests_methods"):
                self.parent._set_tests_methods((workstation_id,))

            # Optionally track assigned ids locally
            if test_method_id not in self.already_assigned:
                self.already_assigned.append(test_method_id)

            # Refill this dialog (so the just-assigned method disappears from list)
            lab_id = self.site_context.get("lab_id")
            self.set_values(lab_id, workstation_id)

            # Return focus to search box
            self.entry_search.focus_set()

        except Exception as exc:
            messagebox.showerror(
                self.engine.app_title,
                f"{_('Assign error:')}\n{exc}",
                parent=self,
            )

    def refresh_from_parent(self):
        """
        Called by the parent after external DELETE/UPDATE operations.
        Always refresh the list using current lab + workstation (if any).
        """
        if not self.workstation or not self.site_context:
            return

        workstation_id = self.workstation.get("workstation_id")
        lab_id = self.site_context.get("lab_id")
        self.set_values(lab_id, workstation_id)

    def on_item_selected(self, _evt=None):
        """
        Hook for future functionality when user selects an item.
        Currently unused but kept for potential detail display.

        Args:
            _evt: Optional Tkinter event
        """
        return

    def _on_tests_changed(self, *args):
        """Refresh list when a test is added/updated."""
        lab_id = self.site_context.get("lab_id")
        workstation_id = self.workstation.get("workstation_id") if self.workstation else None
        if lab_id and workstation_id:
            self.set_values(lab_id, workstation_id)

    def on_cancel(self, _evt=None):
        """
        Close the window using Engine's safe_close method.

        Args:
            _evt: Optional Tkinter event (for keyboard binding)
        """
        self.engine.unsubscribe("tests_changed", self._on_tests_changed)
        self.engine.safe_close(self)
