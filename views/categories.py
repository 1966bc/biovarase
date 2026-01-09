# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   January 2026
# -----------------------------------------------------------------------------
"""
Categories management with lab_id filtering for multi-tenant.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
from views.parent_view import ParentView
import views.category as category


class UI(ParentView):
    """
    Categories list filtered by lab_id based on user role.
    """

    def __init__(self, parent):
        super().__init__(parent, name="categories")

        if self._reusing:
            return

        self.table = "categories"
        self.primary_key = "category_id"

        self.dict_items = {}
        self.selected_item = None
        self.items = tk.StringVar()

        self._build_ui()

        self.minsize(600, 400)
        self.geometry("600x400")
        self.show()

    def _build_ui(self):
        """Build UI."""
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

        # Right panel: buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        self.engine.add_button(frm_buttons, _("Add"), self.on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, _("Update"), self.on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, _("Cancel"), self.on_cancel, "<Alt-c>", self)
        self.bind("<Return>", self.on_item_activated)
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    def on_open(self):
        """Load categories."""
        self.title(_("Categories Management"))
        self._set_values()

    def _set_values(self):
        """Load categories filtered by role."""
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()
        self.selected_item = None

        role = self.engine.log_user["role"]

        if role == 0:
            # Admin: all categories (assigned to site labs + unassigned)
            sql = """
                SELECT c.category_id AS pk,
                       c.description,
                       c.status,
                       c.lab_id,
                       l.description AS lab_name
                FROM categories c
                LEFT JOIN labs l ON l.lab_id = c.lab_id
                WHERE l.site_id = ? OR c.lab_id IS NULL
                ORDER BY CASE WHEN c.lab_id IS NULL THEN 1 ELSE 0 END,
                         l.description, c.description
            """
            args = (self.engine.current_ids.get("site_id"),)
        elif role == 1:
            # Superuser: categories in their lab + unassigned
            sql = """
                SELECT c.category_id AS pk,
                       c.description,
                       c.status,
                       c.lab_id,
                       l.description AS lab_name
                FROM categories c
                LEFT JOIN labs l ON l.lab_id = c.lab_id
                WHERE c.lab_id = ? OR c.lab_id IS NULL
                ORDER BY CASE WHEN c.lab_id IS NULL THEN 1 ELSE 0 END,
                         c.description
            """
            args = (self.engine.get_lab_id(),)
        else:
            # Technician: categories used in their section + unassigned
            sql = """
                SELECT DISTINCT c.category_id AS pk,
                       c.description,
                       c.status,
                       c.lab_id,
                       l.description AS lab_name
                FROM categories c
                LEFT JOIN labs l ON l.lab_id = c.lab_id
                LEFT JOIN test_methods tm ON tm.category_id = c.category_id
                WHERE tm.section_id = ? OR c.lab_id IS NULL
                ORDER BY CASE WHEN c.lab_id IS NULL THEN 1 ELSE 0 END,
                         c.description
            """
            args = (self.engine.get_section_id(),)

        rows = self.engine.read(True, sql, args) or []

        for index, row in enumerate(rows):
            lab_name = row.get("lab_name")
            desc = row["description"]

            if lab_name:
                display = f"{lab_name} — {desc}"
            else:
                display = f"({_('Unassigned')}) — {desc}"

            self.lstItems.insert(tk.END, display)

            # Gray background for inactive OR unassigned
            if row.get("status", 1) != 1:
                self.lstItems.itemconfig(index, {"bg": "light gray"})
            elif row.get("lab_id") is None:
                self.lstItems.itemconfig(index, {"bg": "#fff3cd"})  # light yellow for unassigned

            self.dict_items[index] = row["pk"]

        self.items.set(f"{_('Items')}: {self.lstItems.size()}")

    def on_item_selected(self, _evt=None):
        """Update selected_item."""
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return

        idx = sel[0]
        pk = self.dict_items.get(idx)
        if pk is None:
            self.selected_item = None
            return

        self.selected_item = self.engine.get_selected(self.table, self.primary_key, pk)

    def on_item_activated(self, _evt=None):
        """Open editor for update."""
        sel = self.lstItems.curselection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        idx = sel[0]
        self.engine.open_child(self, category.UI, index=idx)

    def on_add(self, _evt=None):
        """Open editor for insert."""
        self.engine.open_child(self, category.UI, index=None)

    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
