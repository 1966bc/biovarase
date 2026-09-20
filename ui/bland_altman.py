# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Two instruments on the same control: how far apart are they.

The question of the morning an instrument arrives, and of every morning
after one is repaired: can a result be reported from either bench and mean
the same thing. The lot chosen in the main window says which analyte and
which level; the combo here says which other instrument to compare it with.

Pairs are made by day. The same lot of control material, run on both
instruments on the same date, is one pair - which is as close to
simultaneous as a laboratory gets, and closer than the difference being
looked for.
"""

import tkinter as tk
from tkinter import ttk

from bland_altman_canvas import BlandAltmanCanvas
from ui.window import Window

#: Fewer pairs than this and the limits of agreement mean nothing: they are
#: a standard deviation, and a standard deviation of six numbers is a guess.
MINIMUM = 10


class UI(Window, tk.Toplevel):
    """The Bland-Altman plot of one control across two instruments."""

    def __init__(self, parent, batch_id, since=None):
        super().__init__(name="bland_altman")

        self.parent = parent
        self.batch_id = batch_id
        self.since = since
        self.dict_benches = {}
        self.summary = tk.StringVar()

        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        frm_top = ttk.Frame(frm_main, style="App.TFrame")
        ttk.Label(frm_top, style="App.TLabel",
                  text="Compare with:").pack(side=tk.LEFT, padx=(0, 6))
        self.cb_bench = self.engine.tools.get_combo(frm_top)
        self.cb_bench.bind("<<ComboboxSelected>>", self.on_bench)
        self.cb_bench.pack(side=tk.LEFT)
        ttk.Label(frm_top, style="App.TLabel",
                  textvariable=self.summary).pack(side=tk.LEFT, padx=(12, 0))
        frm_top.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.chart = BlandAltmanCanvas(frm_main, width=680, height=420)
        self.chart.pack(fill=tk.BOTH, expand=1)

        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.lot = self.engine.db.get_selected("batches", "batch_id", self.batch_id)
        method = self.engine.db.get_selected("test_methods", "test_method_id",
                                             self.lot["test_method_id"])
        self.test = self.engine.db.get_selected("tests", "test_id", method["test_id"])
        self.unit = self.engine.db.get_selected("units", "unit_id",
                                                method["unit_id"])["description"]

        self.title("Bland-Altman - {0} {1}".format(self.test["description"],
                                                   self.lot["description"]))
        self.set_benches()

    def set_benches(self):
        """The other instruments that run this analyte at this level."""
        sql = """SELECT DISTINCT w.workstation_id, w.description
                   FROM batches b
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE b.test_method_id = ? AND b.description = ?
                    AND b.workstation_id <> ?
               ORDER BY w.description"""
        rows = self.engine.db.read(True, sql, (self.lot["test_method_id"],
                                                self.lot["description"],
                                                self.lot["workstation_id"]))

        self.dict_benches = {index: row["workstation_id"]
                             for index, row in enumerate(rows)}
        self.engine.tools.set_combo(self.cb_bench,
                                    [row["description"] for row in rows])

        if not rows:
            self.summary.set("This analyte runs on one instrument only.")
        else:
            self.cb_bench.current(0)
            self.on_bench()

    def on_bench(self, evt=None):
        """Another instrument chosen: pair the days and draw them."""
        bench = self.dict_benches.get(self.cb_bench.current())

        if bench is not None:
            pairs = self.get_pairs(bench)
            if len(pairs) < MINIMUM:
                self.chart.clear()
                self.summary.set(
                    "{0} pairs: too few to draw limits of agreement,"
                    " {1} are wanted.".format(len(pairs), MINIMUM))
            else:
                self.set_plot(pairs)

    def get_pairs(self, bench):
        """The days both instruments ran this control, as (mean, difference).

        Paired on the date and not on the hour: the two runs are minutes or
        hours apart on the same material, and what is being looked for is
        larger than that.

        @param name: bench
        @return: the pairs
        @rtype: list
        """
        sql = """SELECT ROUND(AVG(mine.result), 4) AS mine,
                        ROUND(AVG(other.result), 4) AS other
                   FROM results mine
                   JOIN batches b1 ON b1.batch_id = mine.batch_id
                   JOIN results other ON DATE(other.received) = DATE(mine.received)
                   JOIN batches b2 ON b2.batch_id = other.batch_id
                  WHERE mine.batch_id = ?
                    AND mine.status = 1 AND other.status = 1
                    AND b2.test_method_id = b1.test_method_id
                    AND b2.description = b1.description
                    AND b2.workstation_id = ?
                    AND (? IS NULL OR mine.received >= ?)
               GROUP BY DATE(mine.received)
               ORDER BY DATE(mine.received)"""
        rows = self.engine.db.read(True, sql, (self.batch_id, bench,
                                                self.since, self.since))

        return [((row["mine"] + row["other"]) / 2.0, row["mine"] - row["other"])
                for row in rows]

    def set_plot(self, pairs):
        """Draw the pairs, and say in one line what they come to."""
        differences = [difference for mean, difference in pairs]
        bias = sum(differences) / len(differences)
        means = sum(mean for mean, difference in pairs) / len(pairs)

        self.chart.draw_plot(pairs,
                             title="{0} {1}: {2} against {3}".format(
                                 self.test["description"],
                                 self.lot["description"],
                                 self.engine.db.get_selected(
                                     "workstations", "workstation_id",
                                     self.lot["workstation_id"])["description"],
                                 self.cb_bench.get()),
                             unit=self.unit)

        if means:
            share = round(100.0 * bias / means, 2)
        else:
            share = 0.0

        self.summary.set("{0} pairs, mean difference {1:.4g} {2} ({3}%)".format(
            len(pairs), bias, self.unit, share))

    def on_cancel(self, evt=None):
        self.destroy()
