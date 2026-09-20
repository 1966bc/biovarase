# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The shape of the series, turned on its side and stood beside the chart.

A Levey-Jennings chart draws the results in the order they were run, which is
what a control chart is for and is also what hides the other question: where
does the mass of this series actually sit. Thirty points walking up and down
between the bands look much the same whether they are piled around the
target or split into two camps either side of it.

So: the same results, counted into bins half a standard deviation wide, drawn
as bars growing to the right, on **the same vertical scale as the chart next
to it**. A bar at plus two is level with the chart's plus two, and the eye
reads the two pictures as one - the left saying when, the right saying how
often.

The scale is not this widget's to choose, which is the whole point, so it
takes it from LeveyJenningsCanvas rather than working one out. A profile that
decided its own limits would line up with nothing and would be worse than not
drawing it.

Excluded results are left out, as they are left out of the mean: a bar is a
count of what the statistics were computed on.
"""

import tkinter as tk

from ljcanvas import LeveyJenningsCanvas


class ProfileCanvas(tk.Canvas):
    """How often the series was where, beside the chart that says when."""

    #: The same top and bottom as the chart, so the two grids line up. They
    #: are read off it rather than copied: a margin changed there and not
    #: here would slide the bars against the bands by a few pixels, which is
    #: exactly the kind of wrong that is never noticed and never right.
    TOP_MARGIN = LeveyJenningsCanvas.TOP_MARGIN
    BOTTOM_MARGIN = LeveyJenningsCanvas.BOTTOM_MARGIN
    LEFT_MARGIN = 6
    RIGHT_MARGIN = 26

    #: And the same scale: four standard deviations either side, with the
    #: same room left over.
    EDGE = LeveyJenningsCanvas.EDGE
    SPARE = LeveyJenningsCanvas.SPARE

    GRID_COLOUR = LeveyJenningsCanvas.GRID_COLOUR
    AXIS_COLOUR = LeveyJenningsCanvas.AXIS_COLOUR
    TEXT_COLOUR = LeveyJenningsCanvas.TEXT_COLOUR

    BAND_1_FILL = LeveyJenningsCanvas.BAND_1_FILL
    BAND_2_FILL = LeveyJenningsCanvas.BAND_2_FILL

    #: A bar wears the colour its results would wear as points.
    INSIDE_COLOUR = LeveyJenningsCanvas.INSIDE_COLOUR
    WARNING_COLOUR = LeveyJenningsCanvas.WARNING_COLOUR
    VIOLATION_COLOUR = LeveyJenningsCanvas.VIOLATION_COLOUR

    FONT_LABEL = ("TkDefaultFont", 6)

    #: The deviations written down the right edge. The chart on the left
    #: carries the scale in the unit of the method, and both pictures stand
    #: on it; this is the same height read the other way, which is the one a
    #: control chart is actually judged by. Two scales, one position.
    MARKS = (-3, -2, -1, 0, 1, 2, 3)

    #: Room kept at the end of the longest bar for the count written after
    #: it, so that it never lands on the deviations down the edge.
    COUNT_ROOM = 16

    #: How wide a bin is, in standard deviations. Half of one: whole ones
    #: give eight bars, which for thirty results is a picture of nothing,
    #: and a quarter gives thirty-two bars mostly empty.
    BIN = 0.5

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self.series = []
        self.target = 0.0
        self.sd = 0.0

        self.bind("<Configure>", self.on_resize)

    def draw_profile(self, series, target, sd, status=None):
        """Count the series into bins and draw them lying on their side.

        @param name: series, target, sd, status
        """
        if status is None:
            self.series = [float(value) for value in series]
        else:
            self.series = [float(value)
                           for value, counted in zip(series, status)
                           if counted == 1]

        self.target = float(target)
        self.sd = float(sd)
        self.redraw()

    def clear(self):
        """Nothing drawn, and nothing remembered."""
        self.delete("all")
        self.series = []
        self.target = 0.0
        self.sd = 0.0
        self.redraw()

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        self.redraw()

    def redraw(self):
        """What there is room for: the bars, an empty frame, or nothing."""
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if width < 10 or height < 10:
            pass
        elif not self.series or self.sd == 0:
            self.draw_bands(width, height)
        else:
            self.draw_bands(width, height)
            self.draw_bars(width, height)

    def draw_bands(self, width, height):
        """The two shaded bands of the chart, carried across.

        Without them the bars float: it is the green and the yellow behind
        them that say which of them are the ones to worry about.
        """
        top = self.TOP_MARGIN
        bottom = height - self.BOTTOM_MARGIN
        left = self.LEFT_MARGIN
        right = width - self.RIGHT_MARGIN

        if self.sd:
            for deviations, fill in ((2, self.BAND_2_FILL), (1, self.BAND_1_FILL)):
                self.create_rectangle(left,
                                      self.get_y(deviations, top, bottom),
                                      right,
                                      self.get_y(-deviations, top, bottom),
                                      fill=fill, outline="")

        self.create_line(left, bottom, right, bottom, fill=self.AXIS_COLOUR)

        if self.sd:
            self.draw_marks(width, top, bottom, right)

    def draw_marks(self, width, top, bottom, right):
        """How many standard deviations, down the right edge."""
        for away in self.MARKS:
            y = self.get_y(away, top, bottom)
            self.create_line(right, y, right + 3, y, fill=self.AXIS_COLOUR)
            self.create_text(right + 5, y, text="{0:+d}".format(away).replace("+0", "0"),
                             anchor=tk.W, font=self.FONT_LABEL,
                             fill=self.TEXT_COLOUR)

        self.create_text(width - 4, (top + bottom) / 2.0,
                         text="\n".join("SD"), anchor=tk.CENTER,
                         font=self.FONT_LABEL, fill=self.TEXT_COLOUR)

    def draw_bars(self, width, height):
        """One bar per bin, as long as the count in it."""
        top = self.TOP_MARGIN
        bottom = height - self.BOTTOM_MARGIN
        left = self.LEFT_MARGIN
        right = width - self.RIGHT_MARGIN

        counts = self.get_counts()
        most = max(counts.values())
        right = right - self.COUNT_ROOM

        for step, how_many in counts.items():
            if how_many:
                away = step * self.BIN
                end = left + how_many / most * (right - left)
                self.create_rectangle(left,
                                      self.get_y(away + self.BIN, top, bottom) + 1,
                                      end,
                                      self.get_y(away, top, bottom) - 1,
                                      fill=self.get_colour(away),
                                      outline=self.AXIS_COLOUR)
                self.create_text(end + 3,
                                 self.get_y(away + self.BIN / 2.0, top, bottom),
                                 text=str(how_many), anchor=tk.W,
                                 font=self.FONT_LABEL, fill=self.TEXT_COLOUR)

    def get_counts(self):
        """How many results fell in each half deviation, by the step it starts at.

        A result further out than the chart goes is counted in the last bin
        it can be drawn in, exactly as the chart clips its points: the bar
        would otherwise be missing from a picture whose whole job is to show
        where the results are.

        @return: step -> count
        @rtype: dictionary
        """
        steps = int(self.EDGE / self.BIN)
        counts = {step: 0 for step in range(-steps, steps)}

        for value in self.series:
            away = (value - self.target) / self.sd
            step = int(away // self.BIN)
            counts[max(-steps, min(step, steps - 1))] += 1

        return counts

    def get_colour(self, away):
        """A bar wears what its results would wear as points on the chart."""
        outer = abs(away)
        if away < 0:
            outer = abs(away - self.BIN)

        if outer < 2.0:
            found = self.INSIDE_COLOUR
        elif outer < 3.0:
            found = self.WARNING_COLOUR
        else:
            found = self.VIOLATION_COLOUR

        return found

    def get_y(self, away, top, bottom):
        """Where so many standard deviations from the target fall up the drawing.

        The same arithmetic the chart does, on the same limits, which is why
        a bar at plus two is level with the chart's plus two. The room left
        over is a share of the whole span and not of half of it, which is
        the one place this is easy to get wrong: four standard deviations
        either side is a span of eight, and five per cent of eight is four
        tenths at each end.
        """
        edge = self.EDGE + 2 * self.EDGE * self.SPARE

        return bottom - (away + edge) / (2 * edge) * (bottom - top)
