# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The Bland-Altman plot, drawn by hand on a canvas.

Two instruments measuring the same control on the same day give two numbers.
Plotting one against the other and looking at the correlation answers the
wrong question - two methods that disagree by a constant five per cent
correlate perfectly. Bland and Altman put the difference of each pair
against its mean instead, so what is read off the picture is how far apart
the two instruments are and whether the distance changes with the
concentration.

Three lines matter: the mean difference, which is the bias between the two,
and the limits of agreement at mean +- 1.96 SD of the differences, between
which 95 per cent of future pairs are expected to fall. Whether that
interval is acceptable is not a statistical question: it is the laboratory
looking at those two numbers and deciding whether a patient result moved
from one instrument to the other would still mean the same thing.
"""

import tkinter as tk

#: What is left around the drawing, in pixels: room for the labels.
MARGIN_LEFT = 62
MARGIN_RIGHT = 74
MARGIN_TOP = 34
MARGIN_BOTTOM = 46

#: The colours, the same the rest of the program uses.
POINT = "#2e6da4"
MEAN_LINE = "#1e3a5f"
LIMIT_LINE = "#e67e22"
ZERO_LINE = "#999999"
TEXT = "#333333"


class BlandAltmanCanvas(tk.Canvas):
    """Differences against means, with the mean difference and its limits."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("background", "white")
        kwargs.setdefault("highlightthickness", 1)
        kwargs.setdefault("highlightbackground", "#cccccc")
        super().__init__(parent, **kwargs)

        self.pairs = []
        self.title = ""
        self.unit = ""
        self.bind("<Configure>", self.on_resize)

    def get_state(self):
        """What is drawn at the moment, for the trace: not __str__, which Tk owns."""
        return "pairs: {0}, title: {1}".format(len(self.pairs), self.title)

    def draw_plot(self, pairs, title="", unit=""):
        """Draw the pairs: each one a mean and a difference.

        @param name: pairs, title, unit
        """
        self.pairs = [(float(mean), float(difference)) for mean, difference in pairs]
        self.title = title
        self.unit = unit
        self.redraw()

    def clear(self):
        """Nothing drawn, and nothing remembered."""
        self.pairs = []
        self.delete("all")

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        self.redraw()

    # --------------------------------------------------------- the drawing

    def redraw(self):

        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if width < 80 or height < 60:
            pass
        elif not self.pairs:
            self.create_text(width / 2, height / 2, text="No paired results",
                             fill=TEXT, font=("TkDefaultFont", 10))
        else:
            self.draw_all(width, height)

    def draw_all(self, width, height):
        """The axes, the three lines, the points and what they are called."""
        differences = [difference for mean, difference in self.pairs]
        bias = sum(differences) / len(differences)
        deviation = self.get_deviation(differences, bias)
        upper = bias + 1.96 * deviation
        lower = bias - 1.96 * deviation

        left, right = MARGIN_LEFT, width - MARGIN_RIGHT
        top, bottom = MARGIN_TOP, height - MARGIN_BOTTOM

        means = [mean for mean, difference in self.pairs]
        low_x, high_x = self.get_span(min(means), max(means))
        low_y, high_y = self.get_span(min(differences + [lower]),
                                      max(differences + [upper]))

        self.draw_frame(left, top, right, bottom, low_x, high_x, low_y, high_y)

        for value, colour, caption, dashed in ((0.0, ZERO_LINE, "", True),
                                               (bias, MEAN_LINE,
                                                "mean {0:.3g}".format(bias), False),
                                               (upper, LIMIT_LINE,
                                                "+1.96 SD {0:.3g}".format(upper), True),
                                               (lower, LIMIT_LINE,
                                                "-1.96 SD {0:.3g}".format(lower), True)):
            y = self.get_y(value, low_y, high_y, top, bottom)
            if dashed:
                self.create_line(left, y, right, y, fill=colour, dash=(4, 3))
            else:
                self.create_line(left, y, right, y, fill=colour, width=2)
            if caption:
                self.create_text(right + 4, y, text=caption, anchor=tk.W,
                                 fill=colour, font=("TkDefaultFont", 7))

        for mean, difference in self.pairs:
            x = self.get_x(mean, low_x, high_x, left, right)
            y = self.get_y(difference, low_y, high_y, top, bottom)
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=POINT, outline="white")

        self.create_text(width / 2, 16, text=self.title, fill=TEXT,
                         font=("TkDefaultFont", 10, "bold"))
        self.create_text(width / 2, height - 12,
                         text="Mean of the two instruments{0}".format(
                             " ({0})".format(self.unit) if self.unit else ""),
                         fill=TEXT, font=("TkDefaultFont", 8))
        self.create_text(12, height / 2, text="Difference", angle=90,
                         fill=TEXT, font=("TkDefaultFont", 8))
        self.create_text(left, height - 26,
                         text="{0} pairs".format(len(self.pairs)),
                         anchor=tk.W, fill=TEXT, font=("TkDefaultFont", 7))

    def draw_frame(self, left, top, right, bottom, low_x, high_x, low_y, high_y):
        """The two axes and the values along them."""
        self.create_line(left, bottom, right, bottom, fill=TEXT)
        self.create_line(left, top, left, bottom, fill=TEXT)

        for step in range(5):
            value = low_y + (high_y - low_y) * step / 4.0
            y = self.get_y(value, low_y, high_y, top, bottom)
            self.create_text(left - 6, y, text="{0:.3g}".format(value), anchor=tk.E,
                             fill=TEXT, font=("TkDefaultFont", 7))
            if step:
                self.create_line(left, y, right, y, fill="#eeeeee")

        for step in range(5):
            value = low_x + (high_x - low_x) * step / 4.0
            x = self.get_x(value, low_x, high_x, left, right)
            self.create_text(x, bottom + 8, text="{0:.4g}".format(value),
                             fill=TEXT, font=("TkDefaultFont", 7))

    # ------------------------------------------------------------- the maths

    def get_deviation(self, values, mean):
        """The standard deviation of the differences, as a sample.

        A sample and not the population: these pairs are the ones that
        happened, out of all the pairs the two instruments would produce.
        """
        found = 0.0
        if len(values) > 1:
            total = sum((value - mean) ** 2 for value in values)
            found = (total / (len(values) - 1)) ** 0.5

        return found

    def get_span(self, lowest, highest):
        """A span with something to spare, and never of zero width."""
        if highest == lowest:
            spare = abs(highest) * 0.1 or 1.0
        else:
            spare = (highest - lowest) * 0.12

        return (lowest - spare, highest + spare)

    def get_x(self, value, low, high, left, right):
        """Where a mean falls across the drawing."""
        return left + (value - low) / (high - low) * (right - left)

    def get_y(self, value, low, high, top, bottom):
        """Where a difference falls up the drawing."""
        return bottom - (value - low) / (high - low) * (bottom - top)
