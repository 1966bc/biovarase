# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The analytes as this laboratory measures them.

Not the list of substances - that is Analytes - but the list of methods: the
same substance appears once per matrix it is measured in, because cocaine in
urine and cocaine in keratin are two methods with two units, two
imprecisions and two sets of goals.
"""

import tkinter as tk

import ui.test_method

from ui.list_window import ListWindow

COLUMNS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Analyte", tk.W, True, 140, 180),
           ("#2", "Matrix", tk.W, False, 75, 90),
           ("#3", "Unit", tk.W, False, 55, 70),
           ("#4", "Panel", tk.W, True, 110, 130),
           ("#5", "Code", tk.W, False, 70, 85),
           ("#6", "TEa%", tk.E, False, 50, 60))


class UI(ListWindow):
    """The methods in use, with what each one is held to."""

    TABLE = "test_methods"
    CAPTION = "code"
    DIALOG = ui.test_method.UI

    def init_ui(self):
        """A tree and not a listbox: a method is six things, not a name."""
        import tkinter.ttk as ttk

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)

        frm_list = ttk.Frame(frm_main, style="App.TFrame")
        ttk.Label(frm_list, style="App.TLabel",
                  textvariable=self.items).pack(fill=tk.X)
        self.lst_items = self.engine.tools.get_tree(frm_list, COLUMNS)
        self.lst_items.configure(height=20)
        self.lst_items.bind("<Double-Button-1>", self.on_edit)

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Add", self.on_add),
                                                       ("Edit", self.on_edit),
                                                       ("Close", self.on_cancel)),
                                                      window=self)

        frm_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y)
        frm_main.pack(fill=tk.BOTH, expand=1)

    def set_values(self):
        """Read the list again: every method, disabled ones in grey."""
        sql = """SELECT tm.test_method_id, tm.code, tm.status, tm.teap005,
                        t.description AS analyte,
                        s.description AS matrix,
                        u.description AS unit,
                        c.description AS panel
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                   LEFT JOIN categories c ON c.category_id = tm.category_id
               ORDER BY t.description, s.description"""
        rows = self.engine.db.read(True, sql, ())

        self.engine.tools.clear_treeview(self.lst_items)
        self.dict_items.clear()
        for row in rows:
            item = self.lst_items.insert("", tk.END,
                                         values=(row["analyte"], row["matrix"],
                                                 row["unit"], row["panel"],
                                                 row["code"], row["teap005"]),
                                         tags=self.engine.tools.get_enable_tags(
                                             row["status"]))
            self.dict_items[item] = row["test_method_id"]

        self.engine.tools.set_count(self.items, len(rows))

    def on_changed(self, row_id):
        """A method was saved: read the list again and land on it."""
        self.set_values()
        for item, key in self.dict_items.items():
            if key == row_id:
                self.engine.tools.set_selected(self.lst_items, item)

    def get_selected(self):
        """The method the list is on, or None."""
        return self.dict_items.get(self.lst_items.focus())

    def on_edit(self, evt=None):
        """Open the method the list is on."""
        from tkinter import messagebox

        row_id = self.get_selected()

        if row_id is None:
            messagebox.showwarning(self.nametowidget(".").title(),
                                   self.engine.no_selected, parent=self)
        else:
            self.dialog = self.engine.windows.replace(
                self.DIALOG.NAME, lambda: self.DIALOG(self, row_id))
