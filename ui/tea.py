# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Total error: what this series does against what the analyte allows.

The Levey-Jennings chart answers whether the method is in control. This one
answers whether being in control is good enough, which is a different
question and one a control chart cannot ask: a method can sit inside its own
limits for a year and still be wider than the analyte tolerates.

What is drawn is the observed total error - the bias plus the imprecision
multiplied by the coverage factor - against the allowable one, with the two
parts shown separately underneath, because a method that misses its goal
misses it through one of them and the answer is different each time.
"""

import tkinter as tk
from tkinter import ttk

from total_error_canvas import TotalErrorCanvas
from ui.window import Window


class UI(Window, tk.Toplevel):
    """The total error of one series, against the goal of its analyte."""

    def __init__(self, parent, batch_id, since=None):
        super().__init__(name="tea")

        self.parent = parent
        self.batch_id = batch_id
        self.since = since

        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        self.chart = TotalErrorCanvas(frm_main, width=700, height=230)
        self.chart.pack(fill=tk.BOTH, expand=1)

        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        lot = self.engine.db.get_selected("batches", "batch_id", self.batch_id)
        method = self.engine.db.get_selected("test_methods", "test_method_id",
                                             lot["test_method_id"])
        test = self.engine.db.get_selected("tests", "test_id", method["test_id"])
        unit = self.engine.db.get_selected("units", "unit_id", method["unit_id"])

        series = self.engine.get_series(self.batch_id,
                                        self.engine.get_observations(),
                                        since=self.since)
        mean = self.engine.qc.get_mean(series)
        cv = self.engine.qc.get_cv(series)
        bias = self.engine.qc.get_bias(mean, lot["target"])

        self.title("Total error - {0} - lot {1}".format(test["description"],
                                                        lot["lot_number"]))
        self.chart.draw_tea(title="{0} - {1}".format(test["description"],
                                                     lot["description"]),
                            te=self.engine.qc.get_te(lot["target"], mean, cv),
                            tea=method["teap005"],
                            bias=bias,
                            cv=cv,
                            z_score=self.engine.qc.get_zscore(),
                            n_series=1,
                            n_results=len(series),
                            unit=unit["description"])

    def on_cancel(self, evt=None):
        self.destroy()
