# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""What one series says, in full.

The main window has room for eight numbers; this is the rest of the answer,
for the lot and the period already chosen there. A window that answered
about the whole archive while the status bar said "last 3 months" would be a
true number answering a question nobody asked.

Nothing here is computed on its own: the statistics come from engine.qc and
the rules from engine.westgards, the same ones the chart is drawn with. A
second copy of a formula is a second chance to get it wrong, and the two
would disagree in the one place where being sure matters.

What it does not do is repeat the main window. The target, the SD, the mean,
the CV, the bias, the total error and its allowance are already under the
chart there, and a second copy of them here would be two places to read the
same number and one more to keep in step. This window holds what does not
fit there.

The extremes: lowest, highest, the range between them, and sigma - how many
times the imprecision fits into what the analyte allows, once the bias has
taken its share.

The distribution counts how many results fall inside one, two and three
standard deviations, and says beside each count what a normal distribution
would have put there - 68.3, 95.4, 99.7 per cent. When the observed count
sits well above the expected one, the standard deviation of the lot is
wider than the method really is; well below, and it is too narrow, which is
the more dangerous of the two: a chart drawn on a standard deviation that is
too generous shows nothing at all, and a method can drift inside it for
months without ever breaking a rule.

Every count is shown as a count, with the percentage after it. Four per cent
of twenty-five results is one result, and it is the percentage that gets
quoted.
"""

import tkinter as tk
from tkinter import ttk

from frequency_histogram_canvas import FrequencyHistogramCanvas
from ui.window import Window

#: What a normal distribution puts inside one, two and three deviations.
EXPECTED = ((1, 68.3), (2, 95.4), (3, 99.7))


class UI(Window, tk.Toplevel):
    """The statistics of one series, and what they are held against."""

    def __init__(self, parent, batch_id, since=None):
        super().__init__(name="statistics")

        self.parent = parent
        #: The lot the series belongs to, and the day the period starts.
        self.batch_id = batch_id
        self.since = since

        self.transient(parent.winfo_toplevel())
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):
        """Two columns and a histogram, rather than four blocks in a tower.

        The numbers on the left, what they are held against on the right, and
        the shape of the series under them: a window read at a glance has to
        fit on a screen at a glance.
        """
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)

        across = ttk.Frame(self.frm_main, style="App.TFrame")

        left = ttk.Frame(across, style="App.TFrame")
        self.frm_series = ttk.LabelFrame(left, text="Extremes")
        self.frm_series.pack(side=tk.TOP, fill=tk.X)
        self.frm_spread = ttk.LabelFrame(left, text="Distribution")
        self.frm_spread.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))
        left.pack(side=tk.LEFT, fill=tk.Y)

        right = ttk.Frame(across, style="App.TFrame")
        self.frm_performance = ttk.LabelFrame(right, text="Against the goal")
        self.frm_performance.pack(side=tk.TOP, fill=tk.X)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        across.pack(side=tk.TOP, fill=tk.X)

        # The histogram says the same thing the distribution counts say, in
        # the form the eye reads first: where the results fall, and where the
        # target and the mean sit among them.
        frm_shape = ttk.LabelFrame(self.frm_main, text="Shape")
        self.histogram = FrequencyHistogramCanvas(frm_shape, height=150)
        self.histogram.pack(fill=tk.BOTH, expand=1, padx=2, pady=2)
        frm_shape.pack(side=tk.TOP, fill=tk.BOTH, expand=1, pady=(6, 0))

        self.frm_rules = ttk.LabelFrame(self.frm_main, text="Westgard rules")
        self.frm_rules.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))

        # No Close button: nothing is decided here and nothing is saved, so
        # the window closes the way every window closes, from its title bar.
        # A button that repeats what the title bar already does is a button
        # to read and a row of pixels to spend.
        self.frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        lot = self.engine.db.get_selected("batches", "batch_id", self.batch_id)
        series = self.engine.get_series(self.batch_id,
                                        self.engine.get_observations(),
                                        since=self.since)

        self.title("Statistics - {0} lot {1}".format(lot["description"],
                                                     lot["lot_number"]))
        self.set_series(series)
        self.set_performance(lot, series)
        self.set_spread(lot, series)
        self.set_shape(lot, series)
        self.set_rules(lot, series)

    # ----------------------------------------------------------- the blocks

    def set_series(self, series):
        """The extremes, which the main window has no room for."""
        if series:
            lowest, highest = min(series), max(series)
        else:
            lowest, highest = 0, 0

        self.set_rows(self.frm_series,
                      (("Lowest", lowest),
                       ("Highest", highest),
                       ("Range", self.engine.qc.get_range(series))))

    def set_performance(self, lot, series):
        """Sigma, and the imprecision the analyte allows to compare it with.

        Sigma is how many times the method's own imprecision fits into what
        the analyte allows, after the bias has taken its share: six is world
        class, three is the least a method can be run at. It is the one
        number that puts imprecision and bias together into a verdict, and
        the main window has no room for it.
        """
        method = self.engine.db.get_selected("test_methods", "test_method_id",
                                             lot["test_method_id"])
        mean = self.engine.qc.get_mean(series)
        cv = self.engine.qc.get_cv(series)
        bias = self.engine.qc.get_bias(mean, lot["target"])

        if method["cvw"]:
            sigma = self.engine.qc.get_sigma(method["cvw"], method["cvb"],
                                             lot["target"], series)
        else:
            # No biological variation: the goal is a total error, and sigma
            # is read off it the same way.
            sigma = 0.0
            if cv:
                sigma = round((method["teap005"] - abs(bias)) / cv, 2)

        self.set_rows(self.frm_performance,
                      (("Sigma", sigma),
                       ("CV allowed%", method["imp"]),
                       ("Bias allowed%", method["bias"])))

    def set_spread(self, lot, series):
        """How the results fall, against how a normal distribution would."""
        rows = []
        for deviations, expected in EXPECTED:
            inside = self.get_inside(lot, series, deviations)
            if series:
                share = round(100.0 * inside / len(series), 1)
            else:
                share = 0.0
            rows.append(("Within {0} SD".format(deviations),
                         "{0}/{1}  {2}%  (exp. {3}%)".format(
                             inside, len(series), share, expected)))

        self.set_rows(self.frm_spread, rows, width=22)

    def set_shape(self, lot, series):
        """The histogram of the series, with the target and the mean on it."""
        self.histogram.draw_histogram(series,
                                      target=lot["target"],
                                      mean=self.engine.qc.get_mean(series),
                                      x_label="Result",
                                      y_label="N")

    def get_inside(self, lot, series, deviations):
        """How many results fall within so many standard deviations."""
        found = 0
        if lot["sd"]:
            limit = deviations * lot["sd"]
            found = len([value for value in series
                         if abs(value - lot["target"]) <= limit])

        return found

    def set_rules(self, lot, series):
        """Each rule, said one by one instead of only the first that fires.

        get_westgard_violation_rule answers with the rule that stops the run,
        which is what the chart needs. Here every rule is asked separately,
        because when a run is rejected the next question is always which of
        them held and which did not.
        """
        westgards = self.engine.westgards
        limits = westgards._calculate_control_limits(lot["target"], lot["sd"])

        rows = (("1:2S", westgards.get_rule_12S(series, limits)),
                ("1:3S", westgards.get_rule_13S(series, limits)),
                ("2:2S", westgards.get_rule_22S(series, limits)),
                ("R:4S", westgards.get_rule_R4S(series, limits)),
                ("4:1S", westgards.get_rule_41S(series, lot["target"], limits)),
                ("10:X", westgards.get_rule_10X(series, lot["target"])))

        for column, (name, broken) in enumerate(rows):
            cell = ttk.Frame(self.frm_rules, style="App.TFrame")
            ttk.Label(cell, style="App.TLabel", text=name,
                      anchor=tk.CENTER).pack(fill=tk.X)
            label = ttk.Label(cell, style="App.TLabel", width=9, anchor=tk.CENTER,
                              text=self.get_verdict(broken, series))
            label.configure(foreground=self.get_colour(broken, series))
            label.pack(fill=tk.X)
            cell.pack(side=tk.LEFT, padx=4, pady=2)

    def get_verdict(self, broken, series):
        """What a rule says: held, broken, or not enough results to ask."""
        if len(series) < self.engine.get_observations():
            found = "NED"
        elif broken:
            found = "broken"
        else:
            found = "held"

        return found

    def get_colour(self, broken, series):
        """Grey when it cannot be asked, red when it is broken, green when held."""
        if len(series) < self.engine.get_observations():
            found = "#666666"
        elif broken:
            found = "#c0392b"
        else:
            found = "#1e8449"

        return found

    # ------------------------------------------------------------ the rows

    def set_rows(self, container, rows, width=14):
        """A block of label and value, one per line."""
        for number, (label, value) in enumerate(rows):
            ttk.Label(container, style="App.TLabel",
                      text=label).grid(row=number, column=0, sticky=tk.W,
                                       padx=(8, 0))
            ttk.Label(container, style="App.TLabel", width=width, anchor=tk.W,
                      text=value).grid(row=number, column=1, sticky=tk.W,
                                       padx=(12, 8))

    def on_cancel(self, evt=None):
        self.destroy()
