# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   winter MMXXVI
# -----------------------------------------------------------------------------
"""
Organizations Management Window.

Hierarchical tree view of the organization structure:
    Country → Region → Lab → Section

Features:
    - Tree navigation with expand/collapse
    - Add/Edit/Delete organizations at any level
    - Role-based access (App Admin only)
    - Visual indicators for inactive organizations
"""

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from i18n import _
from views.parent_view import ParentView
import views.organization as ui

# Organization type constants
ORG_TYPE_COUNTRY = "country"
ORG_TYPE_REGION = "region"
ORG_TYPE_LAB = "lab"
ORG_TYPE_SECTION = "section"

# Display names for org types
ORG_TYPE_LABELS = {
    ORG_TYPE_COUNTRY: "Country",
    ORG_TYPE_REGION: "Region",
    ORG_TYPE_LAB: "Lab",
    ORG_TYPE_SECTION: "Section",
}

# Allowed child types for each parent type
ORG_CHILD_TYPES = {
    None: [ORG_TYPE_COUNTRY],  # Root can have countries
    ORG_TYPE_COUNTRY: [ORG_TYPE_REGION],
    ORG_TYPE_REGION: [ORG_TYPE_LAB],
    ORG_TYPE_LAB: [ORG_TYPE_SECTION],
    ORG_TYPE_SECTION: [],  # Sections cannot have children
}


class UI(ParentView):
    """
    Organizations master window (singleton).

    Displays a hierarchical tree of all organizations in the system.
    Only App Admin (role=0) can access this window.
    """

    def __init__(self, parent):
        super().__init__(parent, name="organizations")
        if self._reusing:
            return

        self.resizable(True, True)
        self.bind("<Alt-c>", self.on_cancel)

        self.table = "organizations"
        self.primary_key = "org_id"

        self.child = None
        self.selected_item = None
        self.dict_items = {}  # iid -> org_id
        self.items = tk.StringVar()

        self._build_ui()

        self.minsize(600, 500)
        self.geometry("700x550")
        self.show(on_screen=True)

    def _build_ui(self):
        """Build the user interface."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left side: treeview + scrollbar
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame")
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=5, expand=True)

        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)

        # Define columns
        cols = ("type", "code", "description")
        self.tree = ttk.Treeview(frm_left, columns=cols, show="tree headings")

        # Configure tree column (hierarchy)
        self.tree.column("#0", width=250, minwidth=150, anchor=tk.W)
        self.tree.heading("#0", text=_("Organization"), anchor=tk.W)

        # Configure data columns
        self.tree.column("type", width=80, minwidth=60, anchor=tk.W)
        self.tree.heading("type", text=_("Type"), anchor=tk.W)

        self.tree.column("code", width=80, minwidth=50, anchor=tk.W)
        self.tree.heading("code", text=_("Code"), anchor=tk.W)

        self.tree.column("description", width=200, minwidth=100, anchor=tk.W)
        self.tree.heading("description", text=_("Description"), anchor=tk.W)

        # Tags for visual styling
        self.tree.tag_configure("inactive", foreground="gray")
        self.tree.tag_configure("country", foreground="darkblue")
        self.tree.tag_configure("region", foreground="darkgreen")
        self.tree.tag_configure("lab", foreground="darkorange")
        self.tree.tag_configure("section", foreground="purple")

        # Scrollbars
        vsb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(frm_left, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout for tree and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_item_selected)
        self.tree.bind("<Double-Button-1>", self._on_item_activated)

        # Right side: buttons
        frm_buttons = ttk.Frame(frm_main, style="Panel.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, expand=False)

        self.engine.add_button(frm_buttons, _("Add"), self._on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, _("Add Child"), self._on_add_child, "<Alt-h>", self)
        self.engine.add_button(frm_buttons, _("Update"), self._on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, _("Delete"), self._on_delete, "<Alt-d>", self)
        ttk.Separator(frm_buttons, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self.engine.add_button(frm_buttons, _("Expand All"), self._on_expand_all, "<Alt-e>", self)
        self.engine.add_button(frm_buttons, _("Collapse All"), self._on_collapse_all, "<Alt-l>", self)
        ttk.Separator(frm_buttons, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self.engine.add_button(frm_buttons, _("Cancel"), self.on_cancel, "<Alt-c>", self)

        self.bind("<Return>", self._on_item_activated)

    def on_open(self):
        """Initialize window on open."""
        self.title(_("Organizations Management"))
        self._load_tree()

    def _load_tree(self):
        """Load the organization hierarchy into the tree."""
        self.tree.delete(*self.tree.get_children())
        self.dict_items.clear()
        self.selected_item = None

        # Fetch all organizations
        sql = """
            SELECT org_id, parent_id, org_type, code, description, status
            FROM organizations
            ORDER BY org_type, description ASC
        """
        try:
            rows = self.engine.read(True, sql, ()) or []
        except Exception as exc:
            self.engine.on_log("organizations._load_tree", exc, type(exc), sys.modules[__name__])
            rows = []

        # Build a dict for quick parent lookup
        org_dict = {}
        for row in rows:
            org_id = row["org_id"]
            org_dict[org_id] = row

        # Insert nodes recursively starting from roots (parent_id is NULL)
        self._insert_children(org_dict, parent_id=None, tree_parent="")

        self.items.set(f"{_('Organizations')}: {len(self.dict_items)}")

        # Expand root level
        for child in self.tree.get_children(""):
            self.tree.item(child, open=True)

    def _insert_children(self, org_dict, parent_id, tree_parent):
        """
        Recursively insert organization nodes.

        Args:
            org_dict: Dictionary of all organizations {org_id: row}
            parent_id: Parent org_id (None for roots)
            tree_parent: Tree iid of the parent node ("" for root)
        """
        # Find all children of this parent
        children = [row for row in org_dict.values() if row["parent_id"] == parent_id]

        # Sort by type order, then by description
        type_order = {ORG_TYPE_COUNTRY: 0, ORG_TYPE_REGION: 1, ORG_TYPE_LAB: 2, ORG_TYPE_SECTION: 3}
        children.sort(key=lambda r: (type_order.get(r["org_type"], 99), r["description"] or ""))

        for row in children:
            org_id = row["org_id"]
            org_type = row["org_type"]
            code = row["code"] or ""
            description = row["description"] or ""
            status = row["status"]

            # Determine tags
            tags = []
            if status != 1:
                tags.append("inactive")
            tags.append(org_type)

            # Type label for display
            type_label = _(ORG_TYPE_LABELS.get(org_type, org_type))

            # Insert node
            iid = f"org_{org_id}"
            self.tree.insert(
                tree_parent,
                tk.END,
                iid=iid,
                text=description,
                values=(type_label, code, description),
                tags=tuple(tags),
                open=False,
            )
            self.dict_items[iid] = org_id

            # Recursively insert children
            self._insert_children(org_dict, parent_id=org_id, tree_parent=iid)

    def _on_item_selected(self, _evt=None):
        """Handle tree selection."""
        sel = self.tree.selection()
        if not sel:
            self.selected_item = None
            return

        iid = sel[0]
        pk = self.dict_items.get(iid)
        if pk is None:
            self.selected_item = None
            return

        self.selected_item = self.engine.get_selected(self.table, self.primary_key, pk)

    def _on_item_activated(self, _evt=None):
        """Double-click or Enter: open editor for selected item."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        iid = sel[0]
        pk = self.dict_items.get(iid)
        if pk is not None:
            self.engine.open_child(self, ui.UI, index=pk)

    def _on_add(self, _evt=None):
        """Add a new root organization (country)."""
        self.engine.open_child(self, ui.UI, index=None, parent_org_id=None)

    def _on_add_child(self, _evt=None):
        """Add a child organization under the selected item."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                _("Select a parent organization first."),
                parent=self,
            )
            return

        iid = sel[0]
        parent_org_id = self.dict_items.get(iid)
        if parent_org_id is None:
            return

        # Check if this org type can have children
        parent_row = self.engine.get_selected(self.table, self.primary_key, parent_org_id)
        if parent_row:
            parent_type = parent_row.get("org_type")
            allowed_children = ORG_CHILD_TYPES.get(parent_type, [])
            if not allowed_children:
                messagebox.showwarning(
                    self.engine.app_title,
                    _("This organization type cannot have children."),
                    parent=self,
                )
                return

        self.engine.open_child(self, ui.UI, index=None, parent_org_id=parent_org_id)

    def _on_delete(self, _evt=None):
        """Delete the selected organization."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        iid = sel[0]
        pk = self.dict_items.get(iid)
        if pk is None:
            return

        # Check for children
        children = self.tree.get_children(iid)
        if children:
            messagebox.showwarning(
                self.engine.app_title,
                _("Cannot delete: organization has children. Delete children first."),
                parent=self,
            )
            return

        # Confirm deletion
        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.ask_to_delete,
            parent=self,
        ):
            return

        # Delete from database
        sql = "DELETE FROM organizations WHERE org_id = ?"
        try:
            result = self.engine.write(sql, (pk,))
            if result is not None:
                self._load_tree()
            else:
                err = self.engine.last_write_error
                msg = self.engine.get_user_friendly_db_error(err) if err else _("Delete failed.")
                messagebox.showerror(self.engine.app_title, msg, parent=self)
        except Exception as exc:
            self.engine.on_log("organizations._on_delete", exc, type(exc), sys.modules[__name__])
            messagebox.showerror(self.engine.app_title, str(exc), parent=self)

    def _on_expand_all(self, _evt=None):
        """Expand all tree nodes."""
        def expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_recursive(child)

        for item in self.tree.get_children(""):
            expand_recursive(item)

    def _on_collapse_all(self, _evt=None):
        """Collapse all tree nodes."""
        def collapse_recursive(item):
            for child in self.tree.get_children(item):
                collapse_recursive(child)
            self.tree.item(item, open=False)

        for item in self.tree.get_children(""):
            collapse_recursive(item)

    def reload_and_reselect(self, pk_to_select):
        """Reload tree and reselect the given org_id."""
        self._load_tree()
        if pk_to_select:
            iid = f"org_{pk_to_select}"
            try:
                self.tree.selection_set(iid)
                self.tree.see(iid)
                self.tree.focus(iid)
                # Expand parents
                parent_iid = self.tree.parent(iid)
                while parent_iid:
                    self.tree.item(parent_iid, open=True)
                    parent_iid = self.tree.parent(parent_iid)
            except Exception:
                pass

    def on_cancel(self, _evt=None):
        """Close handler."""
        super().on_cancel()
