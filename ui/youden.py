# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The two levels of a control against each other: systematic or random.

A Levey-Jennings chart shows one level at a time, and a point outside the
limits on it does not say what kind of error put it there. The Youden plot
answers that, and it answers it with the material already on the bench: the
low level of the day on one axis, the high level of the same day on the
other, one point per day.

What the picture says is read from where the points fall. Along the diagonal
through the two targets, up and to the right or down and to the left, is
systematic error: both levels moved the same way, which is a calibration.
Scattered around the crossing of the two targets with no direction is random
error: imprecision, and a different morning's work. A point far out on one
axis only is something that happened to one level - a bad pipetting, a
bubble - and not to the method.

The pairs are made by day, like the Bland-Altman ones, and for the same
reason: it is as close to simultaneous as a laboratory gets.
"""

import tkinter as tk
from tkinter import ttk

from ui.window import Window
from youden_canvas import YoudenPlotCanvas

#: Fewer pairs than this and the picture shows a handful of dots that mean
#: nothing: the eye reads a direction into any three points.
MINIMUM = 8


class UI(Window, tk.Toplevel):
    """The low level against the high level of one control, day by day."""

    def __init__(self, parent, batch_id, since=None):
        super().__init__(name="youden")

        self.parent = parent
        self.batch_id = batch_id
        self.since = since
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

        self.chart = YoudenPlotCanvas(frm_main, width=560, height=520)
        self.chart.pack(fill=tk.BOTH, expand=1)

        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        lot = self.engine.db.get_selected("batches", "batch_id", self.batch_id)
        method = self.engine.db.get_selected("test_methods", "test_method_id",
                                             lot["test_method_id"])
        test = self.engine.db.get_selected("tests", "test_id", method["test_id"])

        self.title("Youden - {0}".format(test["description"]))
        self.set_plot(lot, test)

    def set_plot(self, lot, test):
        """Find the other level of the same control, pair the days, draw."""
        other = self.get_other_level(lot)

        if other is None:
            self.summary.set("This control has one level only:"
                             " a Youden plot needs two.")
            self.chart.clear()
        else:
            # The lower level goes on the x axis whichever of the two was
            # chosen in the main window: the plot is read the same way every
            # time, and a picture that swaps its axes is a picture that has
            # to be read twice.
            if lot["rank"] > other["rank"]:
                lot, other = other, lot

            low, high = self.get_pairs(lot, other)
            if len(low) < MINIMUM:
                self.summary.set(
                    "{0} days with both levels: {1} are wanted.".format(len(low),
                                                                        MINIMUM))
                self.chart.clear()
            else:
                self.summary.set(self.get_summary(low, high))
                self.chart.draw_youden(low, high,
                                       lot["target"], other["target"],
                                       lot["sd"], other["sd"],
                                       title="{0} - lots {1} and {2}".format(
                                           test["description"],
                                           lot["lot_number"],
                                           other["lot_number"]),
                                       x_label=lot["description"],
                                       y_label=other["description"])

    def get_summary(self, low, high):
        """The line above the plot: how many days, and what r says about them.

        The picture answers by its shape and this answers by a number, and
        they are the same answer. What the number adds is a threshold: the
        laboratory sets in the settings how much agreement it calls
        agreement, rather than each person reading the cloud their own way.

        @param name: low, high
        @return: the line
        @rtype: string
        """
        r = self.engine.qc.get_correlation(low, high)

        if r >= self.engine.get_correlation_coefficient():
            verdict = "the two levels moved together: systematic"
        else:
            verdict = "the two levels moved apart: random"

        return "{0} days with both levels run.   r = {1} - {2}.".format(
            len(low), r, verdict)

    def get_other_level(self, lot):
        """The other level of the same control, on the same instrument.

        The same analyte, the same bench, the same control material and a
        different level - and not the same lot number, because a bilevel
        control is often sold as two vials with two numbers on them. What
        makes them a pair is the material and the run, not the print on the
        label.

        @param name: lot
        @return: the other lot, or None
        @rtype: dictionary
        """
        sql = """SELECT * FROM batches
                  WHERE test_method_id = ? AND workstation_id = ?
                    AND control_id = ? AND rank <> ?
                    AND batch_id <> ? AND status = 1
               ORDER BY rank, expiration DESC
                  LIMIT 1"""
        row = self.engine.db.read(False, sql, (lot["test_method_id"],
                                                lot["workstation_id"],
                                                lot["control_id"],
                                                lot["rank"],
                                                lot["batch_id"]))

        return self.engine.db.get_dict(row)

    def get_pairs(self, lot, other):
        """The days both levels were run, as two lists in the same order.

        @param name: lot, other
        @return: the low level, the high level
        @rtype: tuple
        """
        sql = """SELECT ROUND(AVG(low.result), 4) AS low,
                        ROUND(AVG(high.result), 4) AS high
                   FROM results low
                   JOIN results high ON DATE(high.received) = DATE(low.received)
                  WHERE low.batch_id = ? AND high.batch_id = ?
                    AND low.status = 1 AND high.status = 1
                    AND (? IS NULL OR low.received >= ?)
               GROUP BY DATE(low.received)
               ORDER BY DATE(low.received)"""
        rows = self.engine.db.read(True, sql, (lot["batch_id"], other["batch_id"],
                                                self.since, self.since))

        return ([row["low"] for row in rows], [row["high"] for row in rows])

    def on_cancel(self, evt=None):
        self.destroy()
