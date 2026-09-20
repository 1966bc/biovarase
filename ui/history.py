# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Everything that happened to one result, from the audit trail.

The triggers on the results table have been writing this down since the
first run; until this window there was no way to read it without opening the
database in a shell. An audit trail nobody can consult is half a record.

What the triggers store needs saying, because it decides how this is read.
On an insert they keep the row as it was written. On an update and on a
delete they keep the row **as it was before** - the old values, not the new
ones. So the lines here are the states the result passed through, and the
one it is in now is not in that table at all: it is in results, and this
window puts it at the bottom as the last line.

The times are the database's own, and SQLite writes CURRENT_TIMESTAMP in
UTC. They are shown as they are stored rather than moved to the clock on the
wall: a record that says when something happened must not depend on which
side of a daylight saving change it is read from. The column says so.
"""

import tkinter as tk
from tkinter import ttk

from ui.window import Window

COLUMNS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "When (UTC)", tk.W, False, 120, 135),
           ("#2", "What", tk.W, False, 70, 85),
           ("#3", "Value", tk.E, False, 60, 75),
           ("#4", "Lot", tk.W, False, 90, 110),
           ("#5", "Bench", tk.W, False, 55, 70),
           ("#6", "Received", tk.W, False, 125, 140),
           ("#7", "Reagent lot", tk.W, True, 90, 110),
           ("#8", "In use", tk.CENTER, False, 50, 60),
           ("#9", "By whom", tk.W, True, 90, 115))


class UI(Window, tk.Toplevel):
    """The states one result passed through, oldest first, and what it is now."""

    def __init__(self, parent, result_id):
        super().__init__(name="history")

        self.parent = parent
        self.result_id = result_id
        self.summary = tk.StringVar()

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        ttk.Label(frm_main, style="App.TLabel",
                  textvariable=self.summary).pack(side=tk.TOP, anchor=tk.W,
                                                  pady=(0, 4))

        frm_list = ttk.Frame(frm_main, style="App.TFrame")
        self.lst_history = self.engine.tools.get_tree(frm_list, COLUMNS)
        self.lst_history.configure(height=10)
        # The line that says what the result is today, told apart from the
        # ones that say what it used to be.
        self.lst_history.tag_configure("now", background="#e6f4e6")
        self.lst_history.tag_configure("excluded", foreground="gray")
        frm_list.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        ttk.Label(frm_main, style="App.TLabel", wraplength=780,
                  text="Entered is the value as it was first written down, and"
                       " a change keeps what the result was before it. The last"
                       " line is what it is today, and who made it so is the"
                       " line above.").pack(side=tk.TOP, anchor=tk.W,
                                            pady=(6, 0))

        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("History of a result")
        self.set_history()

    def set_history(self):
        """The audit rows, oldest first, and the result as it stands now."""
        now = self.get_now()
        self.summary.set(self.get_summary(now))

        self.engine.tools.clear_treeview(self.lst_history)

        for row in self.get_rows():
            self.put(row,
                     self.engine.format_datetime(row["log_time"]),
                     self.get_what(row["operation"]),
                     self.get_who(row["by_whom"]),
                     ())

        # The last line has no time of its own and nobody's name on it. Its
        # time would be the moment the row was first written, which is the
        # first line, and its author the last person to change it, which is
        # the line above: two columns that would each say something true
        # about a different line.
        self.put(now, "", "Now", "", ("now",))

    def put(self, row, when, what, who, tags):
        """One line: a state the result was in, and when it was in it."""
        if row["status"] == 0:
            tags = tags + ("excluded",)

        self.lst_history.insert(
            "", tk.END,
            values=(when,
                    what,
                    row["result"],
                    row["lot_number"],
                    row["bench"],
                    self.engine.format_datetime(row["received"]),
                    row["reagent_lot"],
                    self.get_in_use(row["status"]),
                    who),
            tags=tags)

    def get_rows(self):
        """Every line the triggers wrote about this result, oldest first.

        The lot is looked up rather than kept: a result moved from one lot to
        another is one of the three answers this program has to a mistake,
        and without the lot on each line a move would look like nothing
        having happened.

        @return: the audit rows
        @rtype: list of dictionaries
        """
        sql = """SELECT a.operation, a.result, a.received, a.reagent_lot,
                        a.status, a.log_time,
                        b.lot_number, b.description AS level,
                        w.description AS bench,
                        u.last_name AS by_whom
                   FROM audit_results a
                   LEFT JOIN batches b ON b.batch_id = a.batch_id
                   LEFT JOIN workstations w
                          ON w.workstation_id = b.workstation_id
                   LEFT JOIN users u ON u.user_id = a.log_id
                  WHERE a.result_id = ?
               ORDER BY a.audit_id"""

        return self.engine.db.read(True, sql, (self.result_id,))

    def get_now(self):
        """The result as it stands, which the audit table does not hold.

        @return: the result
        @rtype: dictionary
        """
        sql = """SELECT r.result, r.received, r.reagent_lot, r.status,
                        b.lot_number, b.description AS level,
                        w.description AS bench,
                        t.description AS analyte,
                        s.description AS matrix,
                        u.last_name AS by_whom
                   FROM results r
                   JOIN batches b ON b.batch_id = r.batch_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   LEFT JOIN users u ON u.user_id = r.created_by
                  WHERE r.result_id = ?"""

        return self.engine.db.get_dict(self.engine.db.read(False, sql,
                                                           (self.result_id,)))

    def get_summary(self, now):
        """Which result this is: the analyte, the matrix, the level, the bench.

        @param name: now
        @return: the line
        @rtype: string
        """
        return "{0} ({1}) - {2} - {3} - lot {4}".format(now["analyte"],
                                                        now["matrix"],
                                                        now["level"],
                                                        now["bench"],
                                                        now["lot_number"])

    def get_what(self, operation):
        """What the trigger was recording, in the words of the bench.

        @param name: operation
        @return: entered, changed or deleted
        @rtype: string
        """
        return {"INSERT": "Entered",
                "UPDATE": "Changed",
                "DELETE": "Deleted"}.get(operation, operation)

    def get_who(self, name):
        """Whoever was logged in, or nothing at all.

        Nothing rather than None: a result written by a script with no
        session - the sample database was generated by one - has no name
        against it, and an empty cell says that better than a word.

        @param name: name
        @return: the name
        @rtype: string
        """
        found = ""
        if name is not None:
            found = name

        return found

    def get_in_use(self, status):
        """Whether the result counted, at that moment."""
        if status == 1:
            found = "yes"
        else:
            found = "no"

        return found

    def on_cancel(self, evt=None):
        self.destroy()
