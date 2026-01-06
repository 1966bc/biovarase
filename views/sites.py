# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   autumn MMXXV - refactored with Treeview
# -----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import views.site as ui
from views.parent_view import ParentView


SQL = """
    SELECT
        sites.site_id,
        (SELECT suppliers.description
           FROM suppliers
          WHERE suppliers.supplier_id = sites.supplier_id) AS company,
        (SELECT suppliers.description
           FROM suppliers
          WHERE suppliers.supplier_id = sites.comp_id)      AS site,
        sites.status
    FROM sites
    ORDER BY company ASC
"""


class UI(ParentView):
    """
    Sites Management Window.

    Displays all sites in the system with their associated company and site name.
    """

    def __init__(self, parent):
        super().__init__(parent, name="sites")
        if self._reusing:
            return

        self.resizable(True, True)
        self.bind("<Alt-c>", self.on_cancel)

        self.table = "sites"
        self.primary_key = "site_id"

        self.child = None
        self.selected_item = None
        self.dict_items = {}
        self.items = tk.StringVar()

        self._build_ui()

        self.minsize(700, 500)
        self.geometry("700x500")
        self.show(on_screen=True)

    # ----------------------------------------------------------------- UI
    def _build_ui(self):
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
        cols = ("company", "site")
        self.lstItems = ttk.Treeview(frm_left, columns=cols, show="headings")

        # Configure columns
        self.lstItems.column("company", width=300, minwidth=200, anchor=tk.W)
        self.lstItems.heading("company", text="Company", anchor=tk.W)

        self.lstItems.column("site", width=300, minwidth=200, anchor=tk.W)
        self.lstItems.heading("site", text="Site", anchor=tk.W)

        # Tag for inactive sites
        self.lstItems.tag_configure("inactive", background=self.engine.get_rgb(211, 211, 211))

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL, command=self.lstItems.yview)
        self.lstItems.configure(yscrollcommand=sb.set)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.bind("<<TreeviewSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self._on_item_activated)

        # Right side: buttons
        frm_buttons = ttk.Frame(frm_main, style="Panel.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, expand=False)

        self.engine.add_button(frm_buttons, "Add", self._on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, "Update", self._on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, "Cancel", self.on_cancel, "<Alt-c>", self)

        self.bind("<Return>", self._on_item_activated)

    # ----------------------------------------------------------------- lifecycle
    def on_open(self):
        """Initialize window on open."""
        self.title("Sites Management")
        self.set_values()

    def set_values(self):
        """
        Populate the Treeview with all sites from database.

        Behavior:
            - Inactive sites (status=0): grayed out background
        """
        self.engine.clear_treeview(self.lstItems)
        self.dict_items.clear()
        self.selected_item = None

        # Fetch data
        try:
            rows = self.engine.read(True, SQL, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "sites.set_values:read",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception:
                pass
            rows = []

        for row in rows:
            site_id = row.get("site_id")
            status = row.get("status", 1)

            company = (row.get("company") or "").strip()
            site_name = (row.get("site") or "").strip()

            tags = ("inactive",) if int(status) != 1 else ()

            iid = self.lstItems.insert(
                "",
                tk.END,
                iid=str(site_id),
                values=(company, site_name),
                tags=tags,
            )

            self.dict_items[iid] = int(site_id)

        self.items.set(f"Sites: {len(self.dict_items)}")

    def on_item_selected(self, _evt=None):
        """
        Update self.selected_item when the user selects an item.
        """
        sel = self.lstItems.selection()
        if not sel:
            self.selected_item = None
            return

        iid = sel[0]
        pk = self.dict_items.get(iid)
        if pk is None:
            self.selected_item = None
            return

        # Fetch full row as hybrid dict from the Engine
        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            pk,
        )

    def _on_item_activated(self, _evt=None):
        """
        Double-click or Enter: open the editor for the selected item.
        """
        sel = self.lstItems.selection()
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
        """Add button handler: open editor in INSERT mode."""
        self.engine.open_child(self, ui.UI, index=None)

    def _reselect_by_pk(self, pk):
        """
        Reselect the item with the given primary key after reload.

        Args:
            pk: Primary key (site_id) to reselect
        """
        if pk is None:
            return
        try:
            iid = str(pk)
            self.lstItems.selection_set(iid)
            self.lstItems.see(iid)
            self.lstItems.focus(iid)
        except Exception:
            pass

    def reload_and_reselect(self, pk_to_select):
        """
        Called by child after save:
        reloads data and reselects the given PK.

        Args:
            pk_to_select: Primary key of the site to reselect
        """
        self.set_values()
        self._reselect_by_pk(pk_to_select)

    # ------------------------------------------------------------- close
    def on_cancel(self, _evt=None):
        """Close handler."""
        super().on_cancel()
