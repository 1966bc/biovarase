# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Every lot at once: which ones are worth opening.

The rest of the program answers about one series. This answers about all of
them, over the period chosen in the main window, and its job is to say where
to look first - not to judge, which needs the chart.

Four numbers per lot. How many results it has, how many of them sat beyond
two and beyond three standard deviations, its coefficient of variation and
its bias against target. A lot with a hundred results and two past three SD
is a lot that had two bad mornings; one with twenty results and four is a
method that is not working, and the percentages say which is which - with
the counts beside them, because four per cent of twenty-five results is one
result.

The colour is a suggestion and it errs towards attention: red when more than
one result in twenty is past three SD or the bias is past what the analyte
allows, yellow when something is worth a look. Green means nothing is
shouting, not that all is well - that is what the chart is for.
"""

import tkinter as tk
from tkinter import ttk

from ui.window import Window

COLUMNS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Analyte", tk.W, True, 120, 150),
           ("#2", "Matrix", tk.W, False, 75, 90),
           ("#3", "Bench", tk.W, False, 55, 70),
           ("#4", "Level", tk.W, False, 45, 60),
           ("#5", "N", tk.E, False, 40, 50),
           ("#6", "2 SD", tk.E, False, 60, 75),
           ("#7", "3 SD", tk.E, False, 60, 75),
           ("#8", "CV%", tk.E, False, 50, 60),
           ("#9", "Bias%", tk.E, False, 50, 60),
           ("#10", "TEa%", tk.E, False, 50, 60),
           ("#11", "Notes", tk.E, False, 45, 55))

#: Past these, a lot is drawn in red: one result in twenty beyond three
#: standard deviations, or a bias larger than the analyte allows.
VIOLATION_SHARE = 5.0

#: And in yellow: one in fifty beyond three SD, or one in ten beyond two.
WARNING_SHARE = 2.0
WARNING_TOTAL = 10.0


class UI(Window, tk.Toplevel):
    """Every lot in use, with what its results have been doing."""

    def __init__(self, parent, since=None):
        super().__init__(name="performance")

        self.parent = parent
        self.since = since
        self.dict_rows = {}
        self.summary = tk.StringVar()

        self.transient(parent.winfo_toplevel())
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
        self.lst_rows = self.engine.tools.get_tree(frm_list, COLUMNS)
        self.lst_rows.configure(height=22)
        self.lst_rows.tag_configure("violation", background="#f5b7b1")
        self.lst_rows.tag_configure("warning", background="#fdebd0")
        frm_list.pack(fill=tk.BOTH, expand=1)

        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("Performance")
        self.set_rows()

    def set_rows(self):
        """Every lot in use, worst first.

        Sorted by what is wrong rather than by name: the point of the window
        is the first three lines, and a laboratory with a hundred and thirty
        lots does not scroll to find them.
        """
        rows = self.get_rows()

        self.engine.tools.clear_treeview(self.lst_rows)
        self.dict_rows.clear()
        for row in rows:
            item = self.lst_rows.insert("", tk.END,
                                        values=(row["analyte"], row["matrix"],
                                                row["bench"], row["level"],
                                                row["n"],
                                                self.get_share(row["warnings"],
                                                               row["n"]),
                                                self.get_share(row["violations"],
                                                               row["n"]),
                                                row["cv"], row["bias"], row["tea"],
                                                row["notes"]),
                                        tags=self.get_tags(row))
            self.dict_rows[item] = row["batch_id"]

        self.summary.set("{0} lots with results in the period,"
                         " worst first.".format(len(rows)))

    def get_rows(self):
        """What every lot has been doing, counted in one pass.

        The counting is SQL because it is counting: how many results, how
        many past two and three standard deviations of the lot's own SD, how
        many carry a note. The CV and the bias come back to the engine, which
        is where every other CV and bias in this program comes from.

        @return: a row per lot
        @rtype: list
        """
        sql = """SELECT b.batch_id, b.target, b.sd, b.description AS level,
                        t.description AS analyte,
                        s.description AS matrix,
                        w.description AS bench,
                        tm.teap005 AS tea,
                        COUNT(r.result_id) AS n,
                        SUM(CASE WHEN ABS(r.result - b.target) >= 2 * b.sd
                                  AND ABS(r.result - b.target) < 3 * b.sd
                                 THEN 1 ELSE 0 END) AS warnings,
                        SUM(CASE WHEN ABS(r.result - b.target) >= 3 * b.sd
                                 THEN 1 ELSE 0 END) AS violations,
                        (SELECT COUNT(*) FROM notes n
                           JOIN results nr ON nr.result_id = n.result_id
                          WHERE nr.batch_id = b.batch_id AND n.status = 1) AS notes
                   FROM batches b
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                   JOIN results r ON r.batch_id = b.batch_id AND r.status = 1
                  WHERE b.status = 1
                    AND (? IS NULL OR r.received >= ?)
               GROUP BY b.batch_id
                 HAVING COUNT(r.result_id) > 0"""
        rows = self.engine.db.read(True, sql, (self.since, self.since))

        found = []
        for row in rows:
            series = self.engine.get_series(row["batch_id"],
                                            self.engine.get_observations())
            mean = self.engine.qc.get_mean(series)
            found.append({"batch_id": row["batch_id"],
                          "analyte": row["analyte"],
                          "matrix": row["matrix"],
                          "bench": row["bench"],
                          "level": row["level"],
                          "n": row["n"],
                          "warnings": row["warnings"],
                          "violations": row["violations"],
                          "notes": row["notes"],
                          "cv": self.engine.qc.get_cv(series),
                          "bias": self.engine.qc.get_bias(mean, row["target"]),
                          "tea": row["tea"]})

        found.sort(key=self.get_rank, reverse=True)

        return found

    def get_rank(self, row):
        """How loudly a lot is asking to be looked at."""
        return (100.0 * row["violations"] / row["n"],
                100.0 * row["warnings"] / row["n"],
                abs(row["bias"]))

    def get_share(self, count, total):
        """A count, with what it comes to as a percentage after it."""
        if total:
            share = round(100.0 * count / total, 1)
        else:
            share = 0.0

        return "{0} ({1}%)".format(count, share)

    def get_tags(self, row):
        """Red when something is wrong, yellow when something is worth a look."""
        violations = 100.0 * row["violations"] / row["n"]
        warnings = 100.0 * row["warnings"] / row["n"]

        if violations >= VIOLATION_SHARE or abs(row["bias"]) > row["tea"]:
            tags = ("violation",)
        elif violations >= WARNING_SHARE or warnings >= WARNING_TOTAL:
            tags = ("warning",)
        else:
            tags = ()

        return tags

    def on_cancel(self, evt=None):
        self.destroy()
