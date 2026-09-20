# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The lots of control material, and the results entered on them.

Three lists across: the analytes as this laboratory measures them, the lots
open on the one chosen, and the results on the lot. This is where the
material is administered - a new lot when the box arrives, a target
recomputed, a result typed in the wrong place taken out again - while the
main window is where the control is read.

Deleting a result is here and nowhere else, and it is meant to be rare: a
result entered on the wrong lot, or entered twice. What is wrong with a
measurement that was made is said by excluding it, which leaves it on the
chart in grey; deleting is for what never happened.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import ui.batch
import ui.result

from ui.lookup import Lookup
from ui.window import Window

METHODS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Analyte", tk.W, True, 140, 180),
           ("#2", "Matrix", tk.W, False, 70, 90),
           ("#3", "Unit", tk.W, False, 50, 60))

BATCHES = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Liv", tk.W, False, 30, 40),
           ("#2", "Lot", tk.W, True, 90, 110),
           ("#3", "Workstation", tk.W, False, 70, 90),
           ("#4", "Target", tk.E, False, 60, 70),
           ("#5", "SD", tk.E, False, 55, 65),
           ("#6", "Expiration", tk.W, False, 80, 90),
           ("#7", "Results", tk.E, False, 55, 65))

RESULTS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Date", tk.W, True, 120, 145),
           ("#2", "Value", tk.CENTER, False, 55, 70),
           ("#3", "In use", tk.CENTER, False, 45, 55))


class UI(Window, tk.Toplevel):
    """The lots of every analyte, and what has been measured on them."""

    #: The name it is registered under, so only one is ever open.
    TABLE = "batches"

    def __init__(self, parent):
        super().__init__(name="batches")

        self.parent = parent
        self.dict_methods = {}
        self.dict_batches = {}
        self.dict_results = {}
        self.method = None
        self.batch = None
        self.panels = None

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

        self.engine.events.subscribe("batches", self.on_batches_changed)
        self.engine.events.subscribe("results", self.on_results_changed)

    def init_ui(self):
        """Three lists across, each one narrowing the next."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)
        across = ttk.PanedWindow(frm_main, orient=tk.HORIZONTAL)

        self.init_methods(across)
        self.init_batches(across)
        self.init_results(across)

        across.pack(fill=tk.BOTH, expand=1)
        frm_main.pack(fill=tk.BOTH, expand=1)

    def init_methods(self, container):
        """The analytes, with the panel they belong to above them."""
        frm = ttk.LabelFrame(container, text="Test methods")

        self.cb_panel = self.engine.tools.get_combo(frm)
        self.cb_panel.bind("<<ComboboxSelected>>", self.on_panel)
        self.cb_panel.pack(fill=tk.X, padx=4, pady=4)

        self.lst_methods = self.engine.tools.get_tree(frm, METHODS)
        self.lst_methods.bind("<<TreeviewSelect>>", self.on_selected_method)

        container.add(frm, weight=2)

    def init_batches(self, container):
        """The lots open on the analyte chosen, and what can be done to one."""
        frm = ttk.LabelFrame(container, text="Batches")

        self.lst_batches = self.engine.tools.get_tree(frm, BATCHES)
        self.lst_batches.tag_configure("expired", foreground="#c0392b")
        self.lst_batches.tag_configure("discarded", foreground="gray")
        self.lst_batches.bind("<<TreeviewSelect>>", self.on_selected_batch)
        self.lst_batches.bind("<Double-Button-1>", self.on_edit_batch)

        buttons = self.engine.tools.get_button_column(frm,
                                                      (("Add", self.on_add_batch),
                                                       ("Edit", self.on_edit_batch)),
                                                      window=self)
        buttons.pack(side=tk.RIGHT, fill=tk.Y)

        container.add(frm, weight=3)

    def init_results(self, container):
        """The results on the lot chosen, with the three things done to them."""
        frm = ttk.LabelFrame(container, text="Results")

        self.lst_results = self.engine.tools.get_tree(frm, RESULTS)
        self.lst_results.tag_configure("excluded", foreground="gray")
        self.lst_results.bind("<Double-Button-1>", self.on_edit_result)

        buttons = self.engine.tools.get_button_column(frm,
                                                      (("Add", self.on_add_result),
                                                       ("Edit", self.on_edit_result),
                                                       ("Delete", self.on_delete_result),
                                                       ("Close", self.on_cancel)),
                                                      window=self)
        buttons.pack(side=tk.RIGHT, fill=tk.Y)

        container.add(frm, weight=2)

    # ------------------------------------------------------------- the data

    def on_open(self):

        self.title("Batches")
        self.set_panels()
        self.set_methods()

    def set_panels(self):
        """The categories, with every one of them first in the list."""
        self.panels = Lookup(self.engine, self.cb_panel, "categories")
        captions = ["All panels"] + list(self.cb_panel.cget("values"))
        self.panels.ids = {index + 1: key for index, key in self.panels.ids.items()}
        self.engine.tools.set_combo(self.cb_panel, captions)
        self.cb_panel.current(0)

    def set_methods(self):
        """The analytes in use, of the panel chosen or of all of them."""
        sql = """SELECT tm.test_method_id, t.description AS analyte,
                        s.description AS matrix, u.description AS unit
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                  WHERE tm.status = 1
                    AND (? IS NULL OR tm.category_id = ?)
               ORDER BY t.description, s.description"""
        panel = self.panels.get_id()
        rows = self.engine.db.read(True, sql, (panel, panel))

        self.engine.tools.clear_treeview(self.lst_methods)
        self.dict_methods.clear()
        for row in rows:
            item = self.lst_methods.insert("", tk.END,
                                           values=(row["analyte"],
                                                   row["matrix"],
                                                   row["unit"]))
            self.dict_methods[item] = row["test_method_id"]

    def set_batches(self):
        """Every lot of the analyte, in use or not, with how many results it has.

        The count is the reason this list is worth looking at: a lot with no
        results is one that was opened and never run, and a lot with three
        hundred is one nobody has closed.
        """
        sql = """SELECT b.batch_id, b.rank, b.lot_number, b.target, b.sd,
                        b.expiration, b.status,
                        w.description AS workstation,
                        (SELECT COUNT(*) FROM results r
                          WHERE r.batch_id = b.batch_id) AS results
                   FROM batches b
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE b.test_method_id = ?
               ORDER BY b.status DESC, b.rank, w.description"""
        rows = self.engine.db.read(True, sql, (self.method,))

        self.engine.tools.clear_treeview(self.lst_batches)
        self.dict_batches.clear()
        today = self.engine.get_today()
        for row in rows:
            tags = []
            if not row["status"]:
                tags.append("discarded")
            elif row["expiration"] is not None and row["expiration"] < today:
                tags.append("expired")

            item = self.lst_batches.insert(
                "", tk.END,
                values=("L{0}".format(row["rank"]),
                        row["lot_number"],
                        row["workstation"],
                        row["target"],
                        row["sd"],
                        self.engine.format_date(row["expiration"]),
                        row["results"]),
                tags=tuple(tags))
            self.dict_batches[item] = row["batch_id"]

    def set_results(self):
        """The results on the lot, newest first, excluded ones in grey."""
        sql = """SELECT r.result_id, r.result, r.received, r.status
                   FROM results r
                  WHERE r.batch_id = ?
               ORDER BY r.received DESC
                  LIMIT ?"""
        rows = self.engine.db.read(True, sql, (self.batch, self.engine.get_records()))

        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_results.clear()
        for row in rows:
            if row["status"]:
                tags = ()
                in_use = "yes"
            else:
                tags = ("excluded",)
                in_use = "no"

            item = self.lst_results.insert(
                "", tk.END,
                values=(self.engine.format_datetime(row["received"]),
                        row["result"],
                        in_use),
                tags=tags)
            self.dict_results[item] = row["result_id"]

    # ------------------------------------------------------------ the doing

    def on_panel(self, evt=None):
        self.set_methods()
        self.on_reset()

    def on_selected_method(self, evt=None):
        """An analyte chosen: its lots."""
        self.method = self.dict_methods.get(self.lst_methods.focus())

        if self.method is not None:
            self.set_batches()
            self.batch = None
            self.engine.tools.clear_treeview(self.lst_results)
            self.dict_results.clear()

    def on_selected_batch(self, evt=None):
        """A lot chosen: the results on it."""
        self.batch = self.dict_batches.get(self.lst_batches.focus())

        if self.batch is not None:
            self.set_results()

    def on_reset(self):
        """Empty the two lists that hang off the analyte."""
        self.method = None
        self.batch = None
        self.engine.tools.clear_treeview(self.lst_batches)
        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_batches.clear()
        self.dict_results.clear()

    def on_batches_changed(self, row_id=None):
        if self.method is not None:
            self.set_batches()

    def on_results_changed(self, row_id=None):
        if self.batch is not None:
            self.set_results()
            self.set_batches()

    def on_add_batch(self, evt=None):
        """Open a lot on the analyte chosen: a new box of control material."""
        if self.method is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a test method first.",
                                   parent=self)
        else:
            self.engine.windows.replace(
                "batch", lambda: ui.batch.UI(self, self.method))

    def on_edit_batch(self, evt=None):
        """Correct a lot: its target, its SD, its expiration."""
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        else:
            self.engine.windows.replace(
                "batch", lambda: ui.batch.UI(self, self.method, self.batch))

    def on_add_result(self, evt=None):
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a batch first.",
                                   parent=self)
        else:
            self.engine.windows.replace("result",
                                        lambda: ui.result.UI(self, self.batch))

    def on_edit_result(self, evt=None):
        result_id = self.dict_results.get(self.lst_results.focus())

        if result_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        else:
            self.engine.windows.replace(
                "result", lambda: ui.result.UI(self, self.batch, result_id))

    def on_delete_result(self, evt=None):
        """Remove a result from the lot it never belonged to.

        Deleting is for what did not happen - a result entered twice, or on
        the wrong lot. A measurement that was made and came out wrong is
        excluded instead, which keeps it on the chart in grey and keeps the
        series honest. Either way the audit trail holds what it was.
        """
        result_id = self.dict_results.get(self.lst_results.focus())

        if result_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        elif messagebox.askyesno(self.engine.app_title,
                                 "{0}\n\nThe result is removed from the lot."
                                 " What it was stays in the audit trail.".format(
                                     self.engine.ask_to_delete),
                                 parent=self):
            self.engine.db.write("DELETE FROM results WHERE result_id = ?",
                                 (result_id,))
            self.engine.events.notify("results", None)

    def on_cancel(self, evt=None):
        """Stop being told about changes, and go."""
        self.engine.events.unsubscribe("batches", self.on_batches_changed)
        self.engine.events.unsubscribe("results", self.on_results_changed)
        self.destroy()
