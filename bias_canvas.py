# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The bias, as one line with two arrows on it.

The Levey-Jennings chart above this one answers whether the method is in
control. It does not answer the other question, which is asked just as often
and by eye: how far from the target is it sitting, and on which side.

So: the range of the series drawn as an axis, a blue arrow where the target
is, a green arrow where the mean of the series is, and the gap between them
shaded. The distance is written underneath in per cent and in the unit the
analyte is measured in, because a bias of one per cent means one thing on a
drug at 18 ug/mL and another on a hormone at 231 pg/mL.

One number and a direction. It sits under the chart like a footer, and it is
the first thing looked at when the chart says Accept and something still
feels wrong.
"""

import tkinter as tk


class BiasCanvas(tk.Canvas):
    """The target and the mean of a series, on the same line."""

    LEFT_MARGIN = 60
    RIGHT_MARGIN = 6
    TOP_MARGIN = 30
    BOTTOM_MARGIN = 50

    AXIS_COLOUR = "#000000"
    TARGET_COLOUR = "#0000aa"
    #: The green of the Levey-Jennings chart: the same colour means the same
    #: thing across the window, and here it is what the laboratory obtained.
    MEAN_COLOUR = "#006400"
    BAND_FILL = "#eeeeff"
    GRID_COLOUR = "#d0d0d0"
    TEXT_COLOUR = "#333333"

    FONT_SUMMARY = ("TkDefaultFont", 8)

    #: Half the height of the shaded band, and the arrows above the axis.
    BAND_HEIGHT = 6
    ARROW_WIDTH = 6
    ARROW_HEIGHT = 10
    ARROW_GAP = 14

    #: How much room to leave on either side of the widest and narrowest
    #: value, so a mean sitting at the edge is still drawn as a point and not
    #: as part of the frame.
    SPARE = 0.10

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        #: The series, and what was read off it. Empty until draw_bias.
        self.series = []
        self.unit = ""
        self.target = 0.0
        self.mean = 0.0
        self.bias = 0.0
        self.distance = 0.0

        self.bind("<Configure>", self.on_resize)

    def draw_bias(self, series, target, unit=""):
        """The series against its target, as the axis and two arrows.

        @param name: series, target, unit
        """
        values = [float(value) for value in series]

        if not values:
            self.clear()
        else:
            self.series = values
            self.unit = unit or ""
            self.target = float(target)
            self.mean = sum(values) / len(values)
            self.distance = self.mean - self.target
            self.bias = 0.0
            if self.target != 0:
                self.bias = self.distance / self.target * 100.0
            self.redraw()

    def clear(self):
        """Nothing drawn, and nothing remembered."""
        self.delete("all")
        self.series = []
        self.unit = ""
        self.target = 0.0
        self.mean = 0.0
        self.bias = 0.0
        self.distance = 0.0
        self.redraw()

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        self.redraw()

    def redraw(self):
        """What there is room for: the drawing, the empty grid, or nothing."""
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if width < 10 or height < 10:
            pass
        elif not self.series:
            self.draw_empty(width, height)
        else:
            self.draw_all(width, height)

    def draw_all(self, width, height):
        """The band, the axis, the two arrows, the ends and the sentence."""
        left = self.LEFT_MARGIN
        right = width - self.RIGHT_MARGIN
        axis = (height - self.BOTTOM_MARGIN) // 2 + self.TOP_MARGIN // 2

        low, high = self.get_span()
        at_target = self.get_x(self.target, low, high, left, right)
        at_mean = self.get_x(self.mean, low, high, left, right)

        self.create_rectangle(min(at_target, at_mean), axis - self.BAND_HEIGHT,
                              max(at_target, at_mean), axis + self.BAND_HEIGHT,
                              fill=self.BAND_FILL, outline="")

        self.create_line(left, axis, right, axis, fill=self.AXIS_COLOUR, width=1)

        self.draw_arrow(at_target, axis, self.TARGET_COLOUR)
        self.draw_arrow(at_mean, axis, self.MEAN_COLOUR)

        for value in (low, high):
            x = self.get_x(value, low, high, left, right)
            self.create_line(x, axis + 8, x, axis + 12,
                             fill=self.AXIS_COLOUR, width=1)
            self.create_text(x, axis + 16, text="{0:.2f}".format(value),
                             anchor=tk.N, font=self.FONT_SUMMARY,
                             fill=self.AXIS_COLOUR)

        self.create_text((left + right) / 2.0,
                         height - self.BOTTOM_MARGIN / 2.0,
                         text=self.get_summary(), anchor=tk.CENTER,
                         font=self.FONT_SUMMARY, fill=self.TEXT_COLOUR)

    def draw_arrow(self, x, axis, colour):
        """A triangle pointing down at a value on the axis."""
        tip = axis - self.ARROW_GAP
        top = tip - self.ARROW_HEIGHT

        self.create_polygon(x, tip,
                            x - self.ARROW_WIDTH, top,
                            x + self.ARROW_WIDTH, top,
                            fill=colour, outline=colour)

    def draw_empty(self, width, height):
        """A faint grid where the drawing would be, so the space reads as a chart.

        A widget that is simply blank until a lot is chosen looks like one
        that has failed to draw.
        """
        rows, columns = 5, 5

        for column in range(1, columns):
            x = column * width / columns
            self.create_line(x, 0, x, height, fill=self.GRID_COLOUR)

        for row in range(1, rows):
            y = row * height / rows
            self.create_line(0, y, width, y, fill=self.GRID_COLOUR)

    def get_summary(self):
        """The sentence under the axis: how far off, and in which direction.

        Both ways round, because neither answers on its own: the percentage
        is what a goal is written in, the difference is what is read on the
        instrument.

        @return: the sentence
        @rtype: string
        """
        unit = ""
        if self.unit:
            unit = " {0}".format(self.unit)

        return "Bias {0:+.1f}% ({1:+.2f}{2})".format(self.bias, self.distance, unit)

    def get_span(self):
        """The ends of the axis: the series, the target and the mean, with room.

        @return: lowest, highest
        @rtype: tuple
        """
        values = self.series + [self.target, self.mean]
        lowest = min(values)
        highest = max(values)

        if highest == lowest:
            spare = self.SPARE
        else:
            spare = (highest - lowest) * self.SPARE

        return (lowest - spare, highest + spare)

    def get_x(self, value, low, high, left, right):
        """Where a value falls across the axis, and never outside it."""
        if high == low:
            where = 0.5
        else:
            where = (value - low) / (high - low)

        return left + max(0.0, min(1.0, where)) * (right - left)
