# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Every lot of one analyte, one chart under the other.

The main window draws the lot that is chosen. This draws all of them: both
levels, on every instrument the analyte runs on, stacked in the order they
are listed. What it is for is the thing a single chart cannot show - whether
what is happening to one level is happening to the other as well, and
whether it is happening on one bench or on all of them.

Two levels moving the same way is a calibration. One level moving is a
concentration, or a vial. Both benches moving together is the reagent lot
everybody is using. The three answers look different on this page and
identical on any one chart.
"""

import tkinter as tk
from tkinter import ttk

from ljcanvas import LeveyJenningsCanvas
from ui.window import Window

#: How tall each chart is. Two fit on a screen, which is the common case.
CHART_HEIGHT = 260


class UI(Window, tk.Toplevel):
    """One Levey-Jennings chart per lot, scrolled."""

    def __init__(self, parent, test_method_id, since=None):
        super().__init__(name="plots")

        self.parent = parent
        self.test_method_id = test_method_id
        self.since = since

        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):
        """A canvas that scrolls, with a frame of charts inside it."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=4)

        self.scroller = tk.Canvas(frm_main, background="white",
                                  highlightthickness=0, width=880, height=560)
        scrollbar = ttk.Scrollbar(frm_main, orient=tk.VERTICAL,
                                  command=self.scroller.yview)
        self.scroller.configure(yscrollcommand=scrollbar.set)

        self.frm_charts = ttk.Frame(self.scroller, style="App.TFrame")
        self.window = self.scroller.create_window((0, 0), window=self.frm_charts,
                                                  anchor=tk.NW)

        # The scrolled frame is told how wide it is by the canvas, and the
        # canvas is told how tall the frame came out: each knows one thing
        # about the other, which is what a scrolling area is.
        self.frm_charts.bind("<Configure>", self.on_inside)
        self.scroller.bind("<Configure>", self.on_outside)
        self.scroller.bind_all("<Button-4>", self.on_wheel)
        self.scroller.bind_all("<Button-5>", self.on_wheel)

        self.scroller.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_inside(self, evt=None):
        """The frame changed size: tell the canvas how far it can scroll."""
        self.scroller.configure(scrollregion=self.scroller.bbox("all"))

    def on_outside(self, evt=None):
        """The canvas changed size: the frame inside it is that wide."""
        self.scroller.itemconfigure(self.window, width=evt.width)

    def on_wheel(self, evt):
        """The wheel scrolls, whichever way the system reports it."""
        if evt.num == 4:
            self.scroller.yview_scroll(-3, "units")
        else:
            self.scroller.yview_scroll(3, "units")

    def on_open(self):

        method = self.engine.db.get_selected("test_methods", "test_method_id",
                                             self.test_method_id)
        test = self.engine.db.get_selected("tests", "test_id", method["test_id"])
        unit = self.engine.db.get_selected("units", "unit_id", method["unit_id"])

        self.title("Levey-Jennings - {0}".format(test["description"]))
        self.set_charts(test, unit["description"])

    def set_charts(self, test, unit):
        """One chart per lot in use, in the order the lists show them."""
        sql = """SELECT b.batch_id, b.lot_number, b.description AS level,
                        b.target, b.sd, w.description AS bench
                   FROM batches b
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE b.test_method_id = ? AND b.status = 1
               ORDER BY w.rank, w.description, b.rank"""
        rows = self.engine.db.read(True, sql, (self.test_method_id,))

        for row in rows:
            frm = ttk.LabelFrame(self.frm_charts,
                                 text="{0} - {1} - lot {2}".format(row["bench"],
                                                                   row["level"],
                                                                   row["lot_number"]))
            chart = LeveyJenningsCanvas(frm, height=CHART_HEIGHT)
            chart.pack(fill=tk.BOTH, expand=1, padx=2, pady=2)
            frm.pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=4, pady=4)

            self.set_chart(chart, row, test, unit)

    def set_chart(self, chart, row, test, unit):
        """Draw one lot, the way the main window draws the one it is on."""
        sql = """SELECT ROUND(r.result, 2) AS result, r.received, r.status
                   FROM results r
                  WHERE r.batch_id = ?
                    AND (? IS NULL OR r.received >= ?)
               ORDER BY r.received DESC
                  LIMIT ?"""
        results = list(reversed(self.engine.db.read(True, sql,
                                                    (row["batch_id"],
                                                     self.since, self.since,
                                                     self.engine.get_elements()))))

        series = [line["result"] for line in results]
        counted = [line["result"] for line in results if line["status"] == 1]

        chart.draw_chart(series,
                         row["target"],
                         row["sd"],
                         title="{0} - {1}".format(test["description"], row["level"]),
                         dates=[line["received"] for line in results],
                         status=[line["status"] for line in results],
                         y_axis_caption=unit,
                         bottom_text="{0} results, mean {1}, CV {2}%".format(
                             len(counted),
                             self.engine.qc.get_mean(counted),
                             self.engine.qc.get_cv(counted)))

    def on_cancel(self, evt=None):
        """Let go of the wheel, which was bound for the whole application."""
        self.scroller.unbind_all("<Button-4>")
        self.scroller.unbind_all("<Button-5>")
        self.destroy()
