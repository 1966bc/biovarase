# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from i18n import _
from views.parent_view import ParentView
import views.control as control_editor


SQL = (
    "SELECT "
    "  c.control_id              AS control_id, "
    "  s.description             AS supplier_description, "
    "  c.description             AS control_description, "
    "  c.reference               AS control_reference, "
    "  c.status                  AS control_status "
    "FROM controls AS c "
    "INNER JOIN suppliers AS s ON s.supplier_id = c.supplier_id "
    "ORDER BY c.description;"
)


class UI(ParentView):

    def __init__(self, parent):
        super().__init__(parent, name="controls")

        if self._reusing:
            return

        self.table = "controls"
        self.primary_key = "control_id"

        self.selected_item = None
        self.child = None

        self.items = tk.StringVar()

        self.bind("<Return>", self._on_item_activated)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left: Treeview
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame")
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=6, pady=6, expand=True)

        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
        ).pack(fill=tk.X, padx=2, pady=2)

        cols_controls = ("description", "reference", "supplier")
        self.lstItems = ttk.Treeview(frm_left, columns=cols_controls, show="headings")

        self.lstItems.column("description", width=260, minwidth=260, anchor=tk.W, stretch=True)
        self.lstItems.heading("description", text=_("Description"), anchor=tk.W)

        self.lstItems.column("reference", width=120, minwidth=120, anchor=tk.W, stretch=True)
        self.lstItems.heading("reference", text=_("Reference:").rstrip(":"), anchor=tk.W)

        self.lstItems.column("supplier", width=180, minwidth=180, anchor=tk.W, stretch=True)
        self.lstItems.heading("supplier", text=_("Supplier:").rstrip(":"), anchor=tk.W)

        sb_controls = ttk.Scrollbar(frm_left, orient=tk.VERTICAL, command=self.lstItems.yview)
        self.lstItems.configure(yscrollcommand=sb_controls.set)
        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_controls.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.tag_configure("is_disabled", background="light gray")
        self.lstItems.bind("<<TreeviewSelect>>", self._on_item_selected)
        self.lstItems.bind("<Double-1>", self._on_item_activated)

        # Right: Buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        self.engine.add_button(frm_buttons, _("Add"), self._on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, _("Update"), self._on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, _("Cancel"), self.on_cancel, "<Alt-c>", self)

       

    def on_open(self) -> None:
        """Configure title, reload data and center the window."""
        self.title(_("Controls"))
        self.set_values()

    def set_values(self) -> None:
        """Load controls from the database and populate the Treeview."""
        rs = self.engine.read(True, SQL, ()) or []

        # Clear current content
        self.engine.clear_treeview(self.lstItems)

        # Repopulate
        for row in rs:
            status = int(row.get("control_status", 1))
            tag = ("is_disabled",) if status != 1 else ()
            values = (
                row.get("control_description", ""),
                row.get("control_reference", ""),
                row.get("supplier_description", ""),
            )
            control_id = row.get("control_id")
            self.lstItems.insert(
                "",
                tk.END,
                iid=control_id,
                text=control_id,
                values=values,
                tags=tag,
            )

        self.items.set(f"{_('Controls')}: {len(self.lstItems.get_children())}")
        self.selected_item = None

    def _on_item_selected(self, _evt=None) -> None:
        sel = self.lstItems.selection()
        if not sel:
            self.selected_item = None
            return

        primary_key_value = int(sel[0])
        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            primary_key_value,
        )

    def _on_item_activated(self, _evt=None) -> None:
        sel = self.lstItems.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        self._on_item_selected()
        self.engine.open_child(self, control_editor.UI, index=sel[0])

    def _on_add(self, _evt=None) -> None:
        self.engine.open_child(self, control_editor.UI, index=None)

    def on_cancel(self, evt=None) -> None:
        """Close window."""
        super().on_cancel(evt)
