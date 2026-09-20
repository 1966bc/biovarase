# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Generic lookup list UI for simple tables with:
    - primary key (auto-detected via Engine)
    - description field (customizable)
    - status flag (tinyint(1))

Expected table schema:
    pk_field    : primary key (auto-inferred, e.g. unit_id, action_id, ...)
    description : text field
    status      : tinyint(1) active/inactive
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ui.parent_view import ParentView
from ui.editor import Editor


class LookupUI(ParentView):
    """
    Generic list window for simple lookup tables.

    Usage pattern (PROJECT_RULES compliant):

        win = LookupUI(parent, table="units", ui_name="units")
        win.on_open()   # explicit lifecycle entry point

    The class abstracts:
        - loading table rows
        - mapping listbox index → primary key
        - opening child editor windows
        - window lifecycle management
    """

    def __init__(
        self,
        parent,
        table,
        *,
        desc_field="description",
        label_text=None,
        ui_name=None,
    ):
        """
        Initialize the lookup UI.

        NOTE:
        - __init__ must NOT perform data loading
        - __init__ must NOT call on_open()
        - Data loading MUST be invoked via on_open()
        """
        super().__init__(parent, name=ui_name or table)

        # Skip re-initialization on singleton reuse
        if self._reusing:
            return

        # Table metadata
        self.table = table
        self.primary_key = self.engine.get_primary_key(self.table)
        self.desc_field = desc_field
        self.label_text = label_text or self._derive_label_from_table(table)

        # Child editor instance
        self.child = None

        # Index → PK mapping
        self.dict_items = {}
        self.selected_item = None
        self.items = tk.StringVar()

        # Search
        self.search_var = tk.StringVar()
        self.all_items = []  # Full list for filtering: [(pk, description, status), ...]

        # --- Build interface ------------------------------------------------
        self._build_ui()

        # Bind search filtering
        self.search_var.trace_add("write", self._on_search_changed)

        # Set reasonable window size for table display
        min_width = 600
        min_height = 400
        self.minsize(min_width, min_height)
        self.geometry(f"{min_width}x{min_height}")

        self.show()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _derive_label_from_table(self, table_name):
        """
        Generate a singular, human-friendly label from the table name.
        Examples:
            units      -> Unit
            actions    -> Action
            categories -> Category
        """
        name = table_name.strip().lower()
        if name.endswith("ies"):
            return name[:-3].capitalize() + "y"
        if name.endswith("s"):
            return name[:-1].capitalize()
        return name.capitalize()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Build static window layout."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left panel
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame")
        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=5, expand=True)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL)

        self.lstItems = tk.Listbox(
            frm_left,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self.on_item_activated)
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel: search + buttons
        frm_right = ttk.Frame(frm_main, style="App.TFrame")
        frm_right.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Search box
        frm_search = ttk.Frame(frm_right, style="App.TFrame")
        frm_search.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(frm_search, text="Search:", style="App.TLabel").pack(anchor=tk.W)
        self.txSearch = ttk.Entry(frm_search, textvariable=self.search_var, width=15)
        self.txSearch.pack(fill=tk.X)

        # Buttons
        frm_buttons = ttk.Frame(
            frm_right,
            style="App.TFrame",
            relief=tk.GROOVE,
            padding=8,
        )
        frm_buttons.pack(fill=tk.Y, expand=True)

        self.engine.add_button(frm_buttons, "Add", self.on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, "Update", self.on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, "Cancel", self.on_cancel, "<Alt-c>", self)

        self.bind("<Return>", self.on_item_activated)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def on_open(self):
        """
        Called when the window is displayed.

        Loads table rows and updates the title.
        """
        self.title(f"{self.label_text}s Management")
        self._set_values()

    def _set_values(self):
        """
        Populate the listbox with rows from the table.
        """
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()
        self.selected_item = None

        sql = """
            SELECT
                {pk} AS pk,
                {desc}  AS description,
                status
            FROM {table}
            ORDER BY {desc} ASC;
        """.format(
            pk=self.primary_key,
            desc=self.desc_field,
            table=self.table,
        )

        rows = self.engine.read(True, sql, ()) or []

        # Store all items for filtering
        self.all_items = [(row["pk"], row["description"], row.get("status", 1)) for row in rows]

        # Apply current filter
        self._filter_items()

    def _filter_items(self):
        """Filter items based on search text."""
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()

        search_text = self.search_var.get().lower().strip()

        idx = 0
        for pk, description, status in self.all_items:
            if not search_text or search_text in description.lower():
                self.lstItems.insert(tk.END, description)
                if status != 1:
                    self.lstItems.itemconfig(idx, {"bg": "light gray"})
                self.dict_items[idx] = pk
                idx += 1

        total = len(self.all_items)
        shown = self.lstItems.size()
        if search_text:
            self.items.set(f"Items: {shown}/{total}")
        else:
            self.items.set(f"Items: {total}")

    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._filter_items()
        self.selected_item = None

    # ------------------------------------------------------------------
    # Listbox handlers
    # ------------------------------------------------------------------
    def on_item_selected(self, _evt=None):
        """
        Update self.selected_item when listbox selection changes.
        """
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return

        idx = sel[0]
        pk = self.dict_items.get(idx)
        if pk is None:
            self.selected_item = None
            return

        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            pk,
        )

    def on_item_activated(self, _evt=None):
        """
        Double-click or Enter: open the editor window for the selected item.
        """
        sel = self.lstItems.curselection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        idx = sel[0]
        if 0 <= idx < self.lstItems.size():
            self.engine.open_child(
                self, Editor, index=idx,
                table=self.table,
                pk_field=self.primary_key,
                desc_field=self.desc_field,
                label_text=self.label_text,
                ui_name=f"{self.table}_editor",
            )

    def on_add(self, _evt=None):
        """Open the editor window in INSERT mode."""
        self.engine.open_child(
            self, Editor, index=None,
            table=self.table,
            pk_field=self.primary_key,
            desc_field=self.desc_field,
            label_text=self.label_text,
            ui_name=f"{self.table}_editor",
        )

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def on_cancel(self, evt=None):
        """Close the lookup window."""
        super().on_cancel(evt)
