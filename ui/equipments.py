# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ui.parent_view import ParentView
import ui.equipment as ui


SQL = """
    SELECT equipment_id, supplier_id, description, status
    FROM equipments
    ORDER BY description ASC;
"""


class UI(ParentView):

    def __init__(self, parent):
        super().__init__(parent, name="equipments")

        if self._reusing:
            return

        self.table = "equipments"
        self.primary_key = "equipment_id"

        self.child = None
        self.dict_items = {}        # list index → equipment_id
        self.selected_item = None
        self.items = tk.StringVar()

        self.resizable(True, True)

        # --- Build interface ------------------------------------------------
        self._build_ui()

        min_width = 600
        min_height = 400
        self.minsize(min_width, min_height)
        self.geometry(f"{min_width}x{min_height}")

        self.show()

    def _build_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left: list
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame")
        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), expand=True)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL)
        self.lstItems = tk.Listbox(
            frm_left,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self._on_item_activated)
        self.bind("<Return>", self._on_item_activated)

        # Right: buttons
        frm_buttons = ttk.Frame(frm_main, style="Panel.TFrame")

        self.engine.add_button(frm_buttons, "Add", self._on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, "Update", self._on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, "Cancel", self.on_cancel, "<Alt-c>", self)

        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

      
    def on_open(self):

        self.title("Equipments Management")
        self.set_values()

    def set_values(self):
        """Load all equipments."""
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()

        try:
            rows = self.engine.db.read(True, SQL, ()) or []
        except Exception as e:
            try:
                self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))
            except Exception as e:
                pass
            rows = []

        for index, row in enumerate(rows):
            eq_id = row["equipment_id"]
            description = row.get("description", "")
            status = int(row.get("status", 1))

            self.lstItems.insert(tk.END, description)

            if status != 1:  # inactive
                self.lstItems.itemconfig(index, {"bg": "light gray"})

            self.dict_items[index] = eq_id

        self.items.set(f"Equipments: {self.lstItems.size()}")

    def on_item_selected(self, _evt=None):
        """Fetch selected equipment from DB (hybrid dict)."""
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return

        idx = sel[0]
        pk = self.dict_items.get(idx)
        if pk is None:
            self.selected_item = None
            return

        try:
            self.selected_item = self.engine.db.get_selected(
                self.table,
                self.primary_key,
                pk,
            )
        except Exception as e:
            try:
                self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))
            except Exception as e:
                pass
            self.selected_item = None

    def _on_item_activated(self, _evt=None):
        """Open editor in UPDATE mode."""
        sel = self.lstItems.curselection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        idx = sel[0]
        pk = self.dict_items.get(idx)
        if pk is not None:
            self.engine.open_child(self, ui.UI, index=pk)

    def _on_add(self, _evt=None):
        """Open editor in INSERT mode."""
        self.engine.open_child(self, ui.UI, index=None)

    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
