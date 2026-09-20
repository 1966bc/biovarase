# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The two levels of a control against each other, one point per day.

A Levey-Jennings chart shows one level at a time, and a point outside the
limits on it does not say what kind of error put it there. This does: the
low level of the day on one axis, the high level of the same day on the
other, and the shape of the cloud is the answer.

Points strung out along the diagonal - both levels high on the same days,
both low on the same days - is systematic error, and the thing that moved
both is a calibration, a reagent lot, the instrument. A round cloud with no
direction is imprecision. A point far out on one axis only happened to one
level and not to the method: a bubble, a pipetting.

What is drawn: the two targets as a blue crosshair, dashed lines at one and
two standard deviations on each axis, and a point per day, red when either
level was beyond two standard deviations that day.

The eye reads the shape; ui/youden.py puts Pearson's r over the picture, so
that what the shape says can also be written down.
"""

import tkinter as tk


class YoudenPlotCanvas(tk.Canvas):
    """Level 1 across, level 2 up, and the crosshair of the two targets."""

    LEFT_MARGIN = 80
    RIGHT_MARGIN = 20
    TOP_MARGIN = 40
    BOTTOM_MARGIN = 50

    AXIS_COLOUR = "#000000"
    GRID_COLOUR = "#dddddd"
    TARGET_COLOUR = "#0000aa"
    SD1_COLOUR = "#88bbff"
    SD2_COLOUR = "#ffcc66"
    BOTTOM_COLOUR = "#444444"

    POINT_COLOUR = "#008800"
    POINT_OUT_COLOUR = "#ff0000"
    POINT_RADIUS = 4

    FONT_LABEL = ("TkDefaultFont", 9)
    FONT_TITLE = ("TkDefaultFont", 10, "bold")

    #: Room left around the points, as a share of what they span: a day
    #: sitting on the frame is a day that cannot be seen.
    SPARE = 0.10

    #: Lines of the grid behind the points, each way.
    GRID_STEPS = 4

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        #: The pairs, day by day, and what they are judged against.
        self.points = []
        self.target_x = 0.0
        self.target_y = 0.0
        self.sd_x = 0.0
        self.sd_y = 0.0

        self.title = ""
        self.x_label = "Level 1"
        self.y_label = "Level 2"

        self.bind("<Configure>", self.on_resize)

    def draw_youden(self, level1, level2, target_x, target_y, sd_x, sd_y,
                    title="", x_label="Level 1", y_label="Level 2"):
        """The days both levels were run, as points on the two axes.

        The two lists are paired by position and the shorter one decides how
        many pairs there are: a day with only one level run is not a point.

        @param name: level1, level2, target_x, target_y, sd_x, sd_y, title,
                     x_label, y_label
        """
        across = [float(value) for value in level1]
        up = [float(value) for value in level2]
        pairs = min(len(across), len(up))

        self.points = list(zip(across[:pairs], up[:pairs]))
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.sd_x = float(sd_x)
        self.sd_y = float(sd_y)
        self.title = title or ""
        self.x_label = x_label
        self.y_label = y_label
        self.redraw()

    def clear(self):
        """Nothing drawn, and nothing remembered."""
        self.delete("all")
        self.points = []

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        if self.points:
            self.redraw()

    def redraw(self):
        """What there is room for: the drawing, a word, or nothing.

        A standard deviation of zero is not a lot that is perfect, it is a
        lot whose limits were never entered, and there is nothing to draw
        the bands against.
        """
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if not self.points or self.sd_x == 0 or self.sd_y == 0:
            self.create_text(width / 2, height / 2, text="No data",
                             font=self.FONT_TITLE, fill="gray")
        elif width < 10 or height < 10:
            pass
        else:
            self.draw_all(width, height)

    def draw_all(self, width, height):
        """The frame, the grid, the limits, the days, and what they are called."""
        left = self.LEFT_MARGIN
        top = self.TOP_MARGIN
        right = width - self.RIGHT_MARGIN
        bottom = height - self.BOTTOM_MARGIN
        limits = self.get_limits()

        self.create_line(left, top, left, bottom, fill=self.AXIS_COLOUR, width=1)
        self.create_line(left, bottom, right, bottom, fill=self.AXIS_COLOUR, width=1)

        self.draw_grid(left, top, right, bottom)
        self.draw_limits(left, top, right, bottom, limits)
        self.draw_points(left, top, right, bottom, limits)
        self.draw_labels(left, top, right, bottom, limits)

        if self.title:
            self.create_text(width / 2.0, self.TOP_MARGIN / 2.0, text=self.title,
                             anchor=tk.CENTER, font=self.FONT_TITLE,
                             fill=self.AXIS_COLOUR)

    def draw_grid(self, left, top, right, bottom):
        """Lines behind the points, evenly spaced: something for the eye to hold."""
        for step in range(1, self.GRID_STEPS + 1):
            share = step / (self.GRID_STEPS + 1)
            x = left + share * (right - left)
            y = bottom - share * (bottom - top)
            self.create_line(x, top, x, bottom, fill=self.GRID_COLOUR, width=1)
            self.create_line(left, y, right, y, fill=self.GRID_COLOUR, width=1)

    def draw_limits(self, left, top, right, bottom, limits):
        """The crosshair of the two targets, and the bands on either side.

        Both axes carry the same lines, because both levels are judged the
        same way: the crossing of the two solid lines is where a day with
        nothing wrong with it would fall.
        """
        x = self.get_x(self.target_x, left, right, limits)
        y = self.get_y(self.target_y, top, bottom, limits)
        self.create_line(left, y, right, y, fill=self.TARGET_COLOUR, width=2)
        self.create_line(x, top, x, bottom, fill=self.TARGET_COLOUR, width=2)

        for deviations, colour, dash in ((1, self.SD1_COLOUR, (2, 4)),
                                         (2, self.SD2_COLOUR, (4, 4))):
            for side in (-1, 1):
                x = self.get_x(self.target_x + side * deviations * self.sd_x,
                               left, right, limits)
                self.create_line(x, top, x, bottom, fill=colour, width=1, dash=dash)

                y = self.get_y(self.target_y + side * deviations * self.sd_y,
                               top, bottom, limits)
                self.create_line(left, y, right, y, fill=colour, width=1, dash=dash)

    def draw_points(self, left, top, right, bottom, limits):
        """One dot per day, red when either level was out that day."""
        radius = self.POINT_RADIUS

        for across, up in self.points:
            x = self.get_x(across, left, right, limits)
            y = self.get_y(up, top, bottom, limits)

            if self.is_out(across, up):
                colour = self.POINT_OUT_COLOUR
            else:
                colour = self.POINT_COLOUR

            self.create_oval(x - radius, y - radius, x + radius, y + radius,
                             fill=colour, outline=self.AXIS_COLOUR, width=1)

    def draw_labels(self, left, top, right, bottom, limits):
        """The ends of each axis, its target, and what the axis is."""
        low_x, high_x, low_y, high_y = limits

        for value in (low_x, self.target_x, high_x):
            x = self.get_x(value, left, right, limits)
            self.create_line(x, bottom, x, bottom + 4, fill=self.AXIS_COLOUR, width=1)
            self.create_text(x, bottom + 10, text="{0:.2f}".format(value),
                             anchor=tk.N, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

        for value in (low_y, self.target_y, high_y):
            y = self.get_y(value, top, bottom, limits)
            self.create_line(left - 4, y, left, y, fill=self.AXIS_COLOUR, width=1)
            self.create_text(left - 6, y, text="{0:.2f}".format(value),
                             anchor=tk.E, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

        if self.x_label:
            self.create_text((left + right) / 2.0, bottom + 28, text=self.x_label,
                             anchor=tk.N, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

        if self.y_label:
            # One letter per line: Tk can rotate text, and rotated text on a
            # canvas that is redrawn at every resize is measured differently
            # by every font. Stacked letters are the same everywhere.
            self.create_text(left - 62, (top + bottom) / 2.0,
                             text="\n".join(list(self.y_label)),
                             anchor=tk.CENTER, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

    def is_out(self, across, up):
        """True when either level was beyond two standard deviations that day.

        @param name: across, up
        @return: out
        @rtype: boolean
        """
        return (abs(across - self.target_x) > 2 * self.sd_x
                or abs(up - self.target_y) > 2 * self.sd_y)

    def get_limits(self):
        """The ends of the two axes: the days drawn, the two SD bands, and room.

        The bands are taken in even when no day reached them, so that a
        series sitting neatly around its targets is still drawn against the
        limits it is judged by rather than filling the frame by itself.

        @return: low x, high x, low y, high y
        @rtype: tuple
        """
        across = [point[0] for point in self.points]
        up = [point[1] for point in self.points]

        low_x = min(across + [self.target_x - 2 * self.sd_x])
        high_x = max(across + [self.target_x + 2 * self.sd_x])
        low_y = min(up + [self.target_y - 2 * self.sd_y])
        high_y = max(up + [self.target_y + 2 * self.sd_y])

        spare_x = self.get_spare(low_x, high_x)
        spare_y = self.get_spare(low_y, high_y)

        return (low_x - spare_x, high_x + spare_x,
                low_y - spare_y, high_y + spare_y)

    def get_spare(self, lowest, highest):
        """The room left at each end, and something even when there is no span."""
        if highest == lowest:
            span = 1.0
        else:
            span = highest - lowest

        return span * self.SPARE

    def get_x(self, value, left, right, limits):
        """Where a level 1 result falls across the drawing."""
        low, high = limits[0], limits[1]

        if high == low:
            found = (left + right) / 2.0
        else:
            found = left + (value - low) / (high - low) * (right - left)

        return found

    def get_y(self, value, top, bottom, limits):
        """Where a level 2 result falls up the drawing."""
        low, high = limits[2], limits[3]

        if high == low:
            found = (top + bottom) / 2.0
        else:
            found = bottom - (value - low) / (high - low) * (bottom - top)

        return found
