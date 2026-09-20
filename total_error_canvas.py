# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""What the method does, against what the analyte allows.

Total error is the two ways a result can be wrong added together: the method
sits a little off the target, and it scatters around where it sits. Neither
alone says whether a patient result can be reported - a method with no bias
and a wide spread is as unusable as a tight one that reads high.

    TE  = |bias| + z x CV        what this series does
    TEa =  bias  + z x CVa       what the analyte allows

The allowable side comes from biological variation where the analyte has
one, and from the state of the art where it has not; documents/
ANALYTICAL_GOALS.md has the formulae. The observed side comes from the
series on the screen.

The picture is one axis, because there is one question: the green part is
inside the goal, the red part is past it, and the dot is where the method
is. A dot near the line is not a method that has failed, it is a method with
nothing in hand: the next reagent lot, the next calibration, and it is over.
"""

import tkinter as tk


class TotalErrorCanvas(tk.Canvas):
    """One axis from zero, the allowable error on it, and where the series sits."""

    LEFT_MARGIN = 80
    RIGHT_MARGIN = 20
    TOP_MARGIN = 32
    BOTTOM_MARGIN = 40

    AXIS_COLOUR = "#000000"
    TEA_COLOUR = "#0000aa"
    TEXT_COLOUR = "#333333"

    #: The dot, by how much of the goal the method is using up.
    INSIDE_COLOUR = "#00aa00"
    CLOSE_COLOUR = "#ffcc00"
    PAST_COLOUR = "#ff0000"
    INSIDE_FILL = "#ddffdd"
    PAST_FILL = "#ffdddd"

    FONT_LABEL = ("TkDefaultFont", 9)
    FONT_TITLE = ("TkDefaultFont", 10, "bold")
    FONT_SUMMARY = ("TkDefaultFont", 8)

    #: Four fifths of the goal is where a method stops being comfortable.
    CLOSE = 0.8

    #: How far the axis runs past the larger of the two, and the least it
    #: ever shows: an axis that ended at the goal would draw every method
    #: that misses it in the same place, against the right edge.
    ROOM = 1.2
    LEAST = 5.0

    #: Half the height of the coloured band, and the radius of the dot.
    BAND_HEIGHT = 8
    DOT = 5

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self.title = ""
        self.unit = ""
        self.te = 0.0
        self.tea = 0.0
        self.bias = 0.0
        self.cv = 0.0
        self.zscore = 0.0
        self.results = 0

        self.bind("<Configure>", self.on_resize)

    def draw_tea(self, title, te, tea, bias, cv, z_score, n_results, unit=""):
        """The observed total error against the allowable one.

        @param name: title, te, tea, bias, cv, z_score, n_results, unit
        """
        self.title = title
        self.unit = unit or ""
        self.te = float(te)
        self.tea = float(tea)
        self.bias = float(bias)
        self.cv = float(cv)
        self.zscore = float(z_score)
        self.results = int(n_results)
        self.redraw()

    def clear(self):
        """Nothing drawn."""
        self.delete("all")

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        if self.tea or self.te:
            self.redraw()

    def redraw(self):
        """What there is room for: the drawing, a word, or nothing."""
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if width < 10 or height < 10:
            pass
        elif self.tea <= 0.0 and self.te <= 0.0:
            self.create_text(width / 2, height / 2, text="No data",
                             font=self.FONT_TITLE, fill="gray")
        else:
            self.draw_all(width, height)

    def draw_all(self, width, height):
        """The two bands, the axis, the goal, the dot, and the numbers."""
        left = self.LEFT_MARGIN
        right = width - self.RIGHT_MARGIN
        axis = height // 2
        end = self.get_end()

        at_tea = max(self.get_x(self.tea, end, left, right), left)

        self.create_rectangle(left, axis - self.BAND_HEIGHT,
                              at_tea, axis + self.BAND_HEIGHT,
                              fill=self.INSIDE_FILL, outline="")
        self.create_rectangle(at_tea, axis - self.BAND_HEIGHT,
                              right, axis + self.BAND_HEIGHT,
                              fill=self.PAST_FILL, outline="")

        self.create_line(left, axis, right, axis, fill=self.AXIS_COLOUR, width=1)

        self.create_line(at_tea, axis - 12, at_tea, axis + 12,
                         fill=self.TEA_COLOUR, width=2)
        self.create_text(at_tea, axis - 16,
                         text="TEa {0:.1f}%".format(self.tea), anchor=tk.S,
                         font=self.FONT_LABEL, fill=self.TEA_COLOUR)

        colour = self.get_colour()
        at_te = self.get_x(self.te, end, left, right)
        self.create_oval(at_te - self.DOT, axis - self.DOT,
                         at_te + self.DOT, axis + self.DOT,
                         fill=colour, outline=self.AXIS_COLOUR, width=1)
        self.create_text(at_te, axis + 18,
                         text="TE {0:.1f}%".format(self.te), anchor=tk.N,
                         font=self.FONT_LABEL, fill=colour)

        for value, label in ((0.0, "0%"),
                             (self.tea, "{0:.1f}%".format(self.tea)),
                             (end, "{0:.1f}%".format(end))):
            x = self.get_x(value, end, left, right)
            self.create_line(x, axis + 8, x, axis + 12,
                             fill=self.AXIS_COLOUR, width=1)
            self.create_text(x, axis + 16, text=label, anchor=tk.N,
                             font=self.FONT_SUMMARY, fill=self.AXIS_COLOUR)

        if self.title:
            self.create_text((left + right) / 2.0, self.TOP_MARGIN / 2.0,
                             text=self.title, anchor=tk.CENTER,
                             font=self.FONT_TITLE, fill=self.AXIS_COLOUR)

        self.create_text((left + right) / 2.0,
                         height - self.BOTTOM_MARGIN / 2.0,
                         text=self.get_summary(), anchor=tk.CENTER,
                         font=self.FONT_SUMMARY, fill=self.TEXT_COLOUR)

    def get_summary(self):
        """The line under the axis: every number the picture was drawn from.

        The coverage factor among them. A total error at z 1.65 and one at
        1.96 are different numbers, and a chart that showed only the second
        would be read as the first by whoever set the first.

        @return: the line
        @rtype: string
        """
        parts = ["Bias {0:.1f}%".format(self.bias),
                 "CV {0:.1f}%".format(self.cv),
                 "TE {0:.1f}%".format(self.te),
                 "TEa {0:.1f}%".format(self.tea),
                 "z = {0:.2f}".format(self.zscore),
                 "n = {0} results".format(self.results)]

        if self.unit:
            parts.append(self.unit)

        return "   -   ".join(parts)

    def get_colour(self):
        """The dot: green with room to spare, yellow close to the goal, red past it.

        @return: colour
        @rtype: string
        """
        used = 0.0
        if self.tea > 0:
            used = self.te / self.tea

        if used < self.CLOSE:
            found = self.INSIDE_COLOUR
        elif used < 1.0:
            found = self.CLOSE_COLOUR
        else:
            found = self.PAST_COLOUR

        return found

    def get_end(self):
        """Where the axis stops: past the larger of the two, and never tiny.

        @return: the end, in per cent
        @rtype: float
        """
        return max(self.tea * self.ROOM, self.te * self.ROOM, self.LEAST)

    def get_x(self, value, end, left, right):
        """Where a percentage falls along the axis, and never outside it."""
        if end == 0:
            where = 0.5
        else:
            where = max(0.0, min(value / end, 1.0))

        return left + where * (right - left)
