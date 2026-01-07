# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV - refactored with Treeview
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from i18n import _
from views.parent_view import ParentView
import views.user as ui


SQL = """
    SELECT
        user_id,
        last_name,
        first_name,
        nickname,
        status
    FROM users
    ORDER BY last_name ASC, first_name ASC
"""


class UI(ParentView):
    """
    Users Management Window - Master view (Singleton).

    Displays all users in the system with their full name and nickname.
    """

    def __init__(self, parent):
        super().__init__(parent, name="users")

        if self._reusing:
            return

        self.table = "users"
        self.primary_key = "user_id"

        self.child = None            # child editor (views.user.UI)
        self.dict_items = {}         # treeview iid -> user_id
        self.selected_item = None    # hybrid dict from engine.get_selected()
        self.items = tk.StringVar()  # status text (items count)

        self.bind("<Return>", self.on_item_activated)

        # --- Build interface ------------------------------------------------
        self._build_ui()

        min_width = 750
        min_height = 500
        self.minsize(min_width, min_height)
        self.geometry(f"{min_width}x{min_height}")

        self.show()

    # ------------------------------------------------------------------ UI BUILD
    def _build_ui(self):
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left: treeview + scrollbar
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame")
        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), expand=True)

        # Define columns
        cols = ("last_name", "first_name", "nickname")
        self.lstItems = ttk.Treeview(frm_left, columns=cols, show="headings")

        # Configure columns
        self.lstItems.column("last_name", width=200, minwidth=150, anchor=tk.W)
        self.lstItems.heading("last_name", text=_("Surname:").rstrip(":"), anchor=tk.W)

        self.lstItems.column("first_name", width=200, minwidth=150, anchor=tk.W)
        self.lstItems.heading("first_name", text=_("First Name:").rstrip(":"), anchor=tk.W)

        self.lstItems.column("nickname", width=150, minwidth=100, anchor=tk.W)
        self.lstItems.heading("nickname", text=_("Nick:").rstrip(":"), anchor=tk.W)

        # Tag for inactive users
        self.lstItems.tag_configure("inactive", background=self.engine.get_rgb(211, 211, 211))

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL, command=self.lstItems.yview)
        self.lstItems.configure(yscrollcommand=sb.set)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.bind("<<TreeviewSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self.on_item_activated)

        # Right: buttons
        frm_buttons = ttk.Frame(frm_main, style="Panel.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, expand=False)

        self.engine.add_button(frm_buttons, _("Add"), self.on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, _("Update"), self.on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, _("Cancel"), self.on_cancel, "<Alt-c>", self)

    # ------------------------------------------------------------------ OPEN
    def on_open(self):
        """Called once the window is ready: set title and load users."""
        self.title(_("Users"))
        self._load_items()

    # ------------------------------------------------------------------ LOAD DATA
    def _load_items(self):
        """
        Load all users into the treeview.

        Behavior:
            - Inactive users (status=0): grayed out background
        """
        self.engine.clear_treeview(self.lstItems)
        self.dict_items.clear()
        self.selected_item = None

        rows = self.engine.read(True, SQL, ()) or []

        for row in rows:
            user_id = int(row["user_id"])
            status = int(row.get("status", 1))

            last_name = (row.get("last_name") or "").strip()
            first_name = (row.get("first_name") or "").strip()
            nickname = (row.get("nickname") or "").strip()

            tags = ("inactive",) if status != 1 else ()

            iid = self.lstItems.insert(
                "",
                tk.END,
                iid=str(user_id),
                values=(last_name, first_name, nickname),
                tags=tags,
            )

            self.dict_items[iid] = user_id

        self.items.set(f"{_('Users')}: {len(self.dict_items)}")

    # ------------------------------------------------------------------ SELECTION
    def on_item_selected(self, _evt=None):
        """
        Track current selection and fetch full record for later operations.
        selected_item is a hybrid dict (index + column names).
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

        self.selected_item = self.engine.get_selected(self.table, self.primary_key, pk)

    def on_item_activated(self, _evt=None):
        """
        Double-click or Enter on a selected item -> open editor in UPDATE mode.
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

    # ------------------------------------------------------------------ ADD / EDIT
    def on_add(self, _evt=None):
        """Open editor in INSERT mode."""
        self.engine.open_child(self, ui.UI, index=None)

    # ------------------------------------------------------------------ CLOSE
    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
