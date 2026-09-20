# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import ui.sample as ui
from ui.parent_view import ParentView

SQL = "SELECT * FROM samples ORDER BY description;"


class UI(ParentView):

    def __init__(self, parent):
        super().__init__(parent, name="samples")
        if self._reusing:
            return

        self.table = "samples"
        self.primary_key = "sample_id"

        self.child = None
        self.dict_items = {}
        self.selected_item = None
        self.items = tk.StringVar()

        self.bind("<Alt-c>", self.on_cancel)

        self._build_ui()

        self.minsize(600, 400)
        self.geometry("600x400")
        self.show(on_screen=True)


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
        self.lstItems = tk.Listbox(frm_left, yscrollcommand=sb.set,)
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self._on_item_activated)

        # Right: buttons
        frm_buttons = ttk.Frame(frm_main, style="Panel.TFrame")

        self.engine.add_button(frm_buttons, "Add", self._on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, "Update", self._on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, "Cancel", self.on_cancel, "<Alt-c>", self)

        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    def on_open(self):
        """Initial setup: set title and populate list."""
        self.title("Samples Management")
        self.set_values()
        
    def set_values(self):
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()

        # PROJECT_RULES → read_dict(), niente indici su tuple
        rows = self.engine.read(True, "SELECT * FROM samples ORDER BY description;", ())

        for index, row in enumerate(rows or []):
            sample_id = row.get("sample_id")
            description = row.get("description", "")
            status = int(row.get("status", 1))

            # Inserisci voce nella Listbox
            self.lstItems.insert(tk.END, description)

            # Colora le righe con status != 1
            if status != 1:
                self.lstItems.itemconfig(
                    index,
                    {"bg": self.engine.get_rgb(211, 211, 211)}
                )

            # Mappa index → PK (sample_id)
            self.dict_items[index] = sample_id

        self.items.set(f"Samples: {self.lstItems.size()}")


    def on_item_selected(self, _evt=None):
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return
        idx = sel[0]
        pk = self.dict_items.get(idx)
        self.selected_item = self.engine.get_selected(self.table, self.primary_key, pk)
        
    def _on_item_activated(self, _evt=None):
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
            self.engine.open_child(self, ui.UI, index=idx)

    def _on_add(self, _evt=None):
        self.engine.open_child(self, ui.UI, index=None)

    def on_cancel(self, _evt=None):
        super().on_cancel()

