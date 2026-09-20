# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The shape of a series: how often each value came up.

The Levey-Jennings chart draws the results in the order they were run, which
is what a control chart is for. This drops the order and stacks them, which
answers a different question: what does this method's spread actually look
like.

The arithmetic assumes one hump, roughly symmetrical, centred near the
target. When the picture shows something else it is saying so before any
rule does. Two humps is a series that shifted in the middle - two methods,
really, one before the calibration and one after, and a mean computed across
both describes neither. A long tail on one side is a series being pulled by
something that happens occasionally. A block of bars all the same height is
not a distribution at all.

The target is drawn in orange and the mean in blue: the gap between the two
lines is the bias, seen rather than computed.

How many bars: the square root of the number of results, between three and
ten. Too few hides the shape, too many turns thirty results into thirty bars
of height one.
"""

import math
import tkinter as tk


class FrequencyHistogramCanvas(tk.Canvas):
    """The results of a series in bars, with the target and the mean on them."""

    LEFT_MARGIN = 60
    RIGHT_MARGIN = 20
    TOP_MARGIN = 30
    BOTTOM_MARGIN = 40

    AXIS_COLOUR = "#000000"
    GRID_COLOUR = "#dddddd"
    BAR_COLOUR = "#cccccc"
    TARGET_COLOUR = "#ff8800"
    MEAN_COLOUR = "#0000cc"

    FONT_LABEL = ("TkDefaultFont", 9)
    FONT_TITLE = ("TkDefaultFont", 8, "bold")

    #: How many bars the square root is allowed to ask for.
    LEAST_BINS = 3
    MOST_BINS = 10

    #: The share of its slot a bar fills: the rest is the gap that makes two
    #: bars read as two.
    BAR_SHARE = 0.9

    #: Lines across the drawing, and the same number of counts up the side.
    GRID_STEPS = 4

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self.values = []
        self.target = None
        self.mean = None
        self.x_label = "Result"
        self.y_label = "Frequency"

        self.bind("<Configure>", self.on_resize)

    def draw_histogram(self, values, target=None, mean=None,
                       x_label="Result", y_label="Frequency"):
        """The series as bars, with the target and the mean drawn on it.

        @param name: values, target, mean, x_label, y_label
        """
        self.values = [float(value) for value in values]
        self.target = None
        self.mean = None

        if target is not None:
            self.target = float(target)
        if mean is not None:
            self.mean = float(mean)

        self.x_label = x_label
        self.y_label = y_label
        self.redraw()

    def clear(self):
        """Nothing drawn, and nothing remembered."""
        self.delete("all")
        self.values = []

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        if self.values:
            self.redraw()

    def redraw(self):
        """What there is room for: the drawing, a word, or nothing."""
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if not self.values:
            self.create_text(width / 2, height / 2, text="No data",
                             font=self.FONT_TITLE, fill="gray")
        elif width < 10 or height < 10:
            pass
        else:
            self.draw_all(width, height)

    def draw_all(self, width, height):
        """The axes, the grid, the bars, the two lines and the labels."""
        left = self.LEFT_MARGIN
        top = self.TOP_MARGIN
        right = width - self.RIGHT_MARGIN
        bottom = height - self.BOTTOM_MARGIN

        bins, counts = self.get_bins()
        tallest = max(counts)

        self.create_line(left, top, left, bottom, fill=self.AXIS_COLOUR, width=1)
        self.create_line(left, bottom, right, bottom, fill=self.AXIS_COLOUR, width=1)

        for step in range(1, self.GRID_STEPS + 1):
            y = bottom - step / self.GRID_STEPS * (bottom - top)
            self.create_line(left, y, right, y, fill=self.GRID_COLOUR, width=1)

        self.draw_bars(left, top, right, bottom, counts, tallest)
        self.draw_lines(left, top, right, bottom, bins)
        self.draw_counts(left, top, bottom, tallest)
        self.draw_values(left, right, bottom, bins)

    def draw_bars(self, left, top, right, bottom, counts, tallest):
        """One bar per bin, as tall as the count in it."""
        slot = (right - left) / len(counts)

        for index, count in enumerate(counts):
            if count:
                start = left + index * slot
                top_of_bar = bottom - count / tallest * (bottom - top)
                self.create_rectangle(start, top_of_bar,
                                      start + slot * self.BAR_SHARE, bottom,
                                      fill=self.BAR_COLOUR,
                                      outline=self.AXIS_COLOUR, width=1)

    def draw_lines(self, left, top, right, bottom, bins):
        """The target and the mean, standing on the bars they fall among."""
        low = bins[0][0]
        high = bins[-1][1]

        for value, colour, caption in ((self.target, self.TARGET_COLOUR, "Target"),
                                       (self.mean, self.MEAN_COLOUR, "Mean")):
            if value is not None:
                x = self.get_x(value, low, high, left, right)
                self.create_line(x, top, x, bottom, fill=colour, width=2)
                self.create_text(x, top - 5, text=caption, anchor=tk.S,
                                 font=self.FONT_LABEL, fill=colour)

    def draw_counts(self, left, top, bottom, tallest):
        """How many results each height stands for, up the side."""
        for step in range(self.GRID_STEPS + 1):
            y = bottom - step / self.GRID_STEPS * (bottom - top)
            count = int(round(tallest * step / self.GRID_STEPS))
            self.create_line(left - 4, y, left, y, fill=self.AXIS_COLOUR, width=1)
            self.create_text(left - 6, y, text=str(count), anchor=tk.E,
                             font=self.FONT_LABEL, fill=self.AXIS_COLOUR)

        if self.y_label:
            # One letter per line: see the note in youden_canvas.py.
            self.create_text(left - 35, (top + bottom) / 2.0,
                             text="\n".join(list(self.y_label)),
                             anchor=tk.CENTER, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

    def draw_values(self, left, right, bottom, bins):
        """What each bar covers, written at its middle."""
        slot = (right - left) / len(bins)

        for index, (start, end) in enumerate(bins):
            x = left + (index + 0.5) * slot
            self.create_text(x, bottom + 10,
                             text="{0:.2f}".format((start + end) / 2.0),
                             anchor=tk.N, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

        if self.x_label:
            self.create_text((left + right) / 2.0, bottom + 26, text=self.x_label,
                             anchor=tk.N, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

    def get_bins(self):
        """The bars and what fell in each: equal widths across the series.

        A series where every result is the same number has no width to
        divide, and is one bar.

        @return: the bins as (start, end), and the count in each
        @rtype: tuple of two lists
        """
        lowest = min(self.values)
        highest = max(self.values)

        if highest == lowest:
            found = ([(lowest - 0.5, highest + 0.5)], [len(self.values)])
        else:
            how_many = self.get_how_many()
            width = (highest - lowest) / how_many
            bins = [(lowest + step * width, lowest + (step + 1) * width)
                    for step in range(how_many)]
            found = (bins, self.get_counts(bins))

        return found

    def get_counts(self, bins):
        """How many results fall in each bin.

        The last bin takes its right edge as well, which is where the
        highest result sits: without that it would fall outside every bin
        and the tallest value of the series would not be drawn at all.

        @param name: bins
        @return: the count in each bin
        @rtype: list
        """
        counts = [0] * len(bins)

        for value in self.values:
            if value >= bins[-1][1]:
                counts[-1] += 1
            else:
                for index, (start, end) in enumerate(bins):
                    if start <= value < end:
                        counts[index] += 1

        return counts

    def get_how_many(self):
        """How many bars: the square root of the results, within bounds.

        @return: the number of bins
        @rtype: integer
        """
        wanted = int(round(math.sqrt(len(self.values))))

        return max(self.LEAST_BINS, min(wanted, self.MOST_BINS))

    def get_x(self, value, low, high, left, right):
        """Where a value falls across the drawing."""
        if high == low:
            span = 1.0
        else:
            span = high - low

        return left + (value - low) / span * (right - left)
