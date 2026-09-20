# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Everything that has been written about the results, over the period.

The notes are the log of non conformities: with no validation step, this is
where somebody said what was seen and what was done about it, and this
window is that log read end to end instead of one result at a time.

It is the page to open when the question is about the year rather than about
this morning: how often a calibration was repeated, on which instrument, on
which analyte. The answers are the reason the actions are a table and not a
free text field.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import ui.note

from ui.window import Window

COLUMNS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Date", tk.W, False, 90, 105),
           ("#2", "Analyte", tk.W, True, 120, 150),
           ("#3", "Bench", tk.W, False, 55, 70),
           ("#4", "Level", tk.W, False, 50, 65),
           ("#5", "Result", tk.E, False, 55, 70),
           ("#6", "Action", tk.W, False, 130, 150),
           ("#7", "Note", tk.W, True, 200, 260),
           ("#8", "By", tk.W, False, 70, 85))


class UI(Window, tk.Toplevel):
    """The notes of the period, newest first."""

    def __init__(self, parent, since=None):
        super().__init__(name="notes")

        self.parent = parent
        self.since = since
        self.dict_notes = {}
        self.summary = tk.StringVar()

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

        self.engine.events.subscribe("notes", self.on_notes_changed)

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        ttk.Label(frm_main, style="App.TLabel",
                  textvariable=self.summary).pack(side=tk.TOP, anchor=tk.W,
                                                  pady=(0, 4))

        frm_list = ttk.Frame(frm_main, style="App.TFrame")
        self.lst_notes = self.engine.tools.get_tree(frm_list, COLUMNS)
        self.lst_notes.configure(height=20)
        self.lst_notes.bind("<Double-Button-1>", self.on_edit)
        frm_list.pack(fill=tk.BOTH, expand=1)

        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("Notes")
        self.set_notes()

    def set_notes(self):
        """Every note of the period, with the result it is about."""
        sql = """SELECT n.note_id, n.description, n.modified, n.result_id,
                        a.description AS action,
                        r.result,
                        t.description AS analyte,
                        b.description AS level,
                        w.description AS bench,
                        u.last_name AS by_whom
                   FROM notes n
                   JOIN actions a ON a.action_id = n.action_id
                   JOIN results r ON r.result_id = n.result_id
                   JOIN batches b ON b.batch_id = r.batch_id
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                   LEFT JOIN users u ON u.user_id = n.created_by
                  WHERE n.status = 1
                    AND (? IS NULL OR r.received >= ?)
               ORDER BY r.received DESC"""
        rows = self.engine.db.read(True, sql, (self.since, self.since))

        self.engine.tools.clear_treeview(self.lst_notes)
        self.dict_notes.clear()
        for row in rows:
            item = self.lst_notes.insert("", tk.END,
                                         values=(self.engine.format_date(row["modified"]),
                                                 row["analyte"], row["bench"],
                                                 row["level"], row["result"],
                                                 row["action"], row["description"],
                                                 row["by_whom"]))
            self.dict_notes[item] = (row["note_id"], row["result_id"])

        self.summary.set("{0} notes in the period.".format(len(rows)))

    def on_edit(self, evt=None):
        """Open the note the list is on: its author may correct it."""
        chosen = self.dict_notes.get(self.lst_notes.focus())

        if chosen is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected, parent=self)
        else:
            note_id, result_id = chosen
            self.engine.windows.replace(
                "note", lambda: ui.note.UI(self, result_id, note_id))

    def on_notes_changed(self, row_id=None):
        self.set_notes()

    def on_cancel(self, evt=None):
        self.engine.events.unsubscribe("notes", self.on_notes_changed)
        self.destroy()
