# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The Levey-Jennings chart: the one picture this program is for.

A lot of control material on one analyte and one instrument, run day after
day. The target comes printed on the box, the standard deviation with it,
and the results are drawn against them: inside one deviation is where most
of them belong, past two is worth a look, past three is a run that does not
go out.

Three things here are decisions rather than drawing, and each of them is a
way of not lying to the person reading.

**The scale is fixed at four standard deviations either side of the target,
whatever the results do.** A chart that fits itself to its data redraws the
same laboratory as a disaster or as perfection depending on the morning: the
bands move, the points stay where they are, and the eye reads the bands. At
a fixed scale two charts of two analytes can be put side by side and mean
the same thing. A result past four deviations is drawn as a triangle at the
edge, pointing the way it went - it is off the chart, and saying so is more
honest than moving the chart.

**The bottom is dated, not numbered.** A control chart is read to answer
when something started, and a series numbered 1 to 30 cannot answer that.

**An excluded result is still drawn**, in grey, with the line broken either
side of it. It was measured, it happened, and it is out of the statistics
and not out of the record. Double clicking it is also the only way back to
it.
"""

import datetime
import tkinter as tk


class LeveyJenningsCanvas(tk.Canvas):
    """A control series against its target, with the bands it is judged by."""

    LEFT_MARGIN = 70
    RIGHT_MARGIN = 20
    TOP_MARGIN = 40
    BOTTOM_MARGIN = 60

    GRID_COLOUR = "#d0d0d0"
    AXIS_COLOUR = "#000000"
    LINE_COLOUR = "#444444"
    TEXT_COLOUR = "#333333"
    BOTTOM_COLOUR = "#444444"

    TARGET_COLOUR = "#00008b"
    SD1_COLOUR = "#006400"
    SD2_COLOUR = "#ff9800"
    SD3_COLOUR = "#e74c3c"

    #: The two bands behind the points: within one deviation, within two.
    BAND_1_FILL = "#e6f4e6"
    BAND_2_FILL = "#fff6cc"

    #: A point, by how far from the target it sits, and grey when excluded.
    INSIDE_COLOUR = "#00aa00"
    WARNING_COLOUR = "#ffcc00"
    VIOLATION_COLOUR = "#ff0000"
    EXCLUDED_COLOUR = "#999999"

    POINT_RADIUS = 4

    FONT_LABEL = ("TkDefaultFont", 6)
    FONT_TITLE = ("TkDefaultFont", 10, "bold")

    #: Where the chart ends, in standard deviations, and the room left over
    #: so the outermost line is not drawn on the frame.
    EDGE = 4
    SPARE = 0.05

    #: Lines of the grid, each way.
    GRID_STEPS = 6

    #: Past this many points the values stop being written on them: thirty
    #: numbers over a chart is a chart with numbers on it, sixty is a wall.
    MOST_VALUES = 30

    #: How many dates fit along the bottom before they run into each other.
    MOST_DATES = 8

    #: How a date is written on the axis. Short on purpose: the year is the
    #: same for every point of a series, and would be read once and
    #: thirty times.
    DATE_FORMAT = "%d-%m"

    #: How close a double click has to land to count as being on a point.
    REACH = 3

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self.series = []
        self.target = 0.0
        self.sd = 0.0
        self.title = ""
        self.status = []
        #: The dates as they are written under the points, already formatted.
        self.labels = []
        self.x_caption = "Observation"
        self.y_caption = "Value"
        self.bottom_text = ""

        #: Every point drawn, for the double click to find again.
        self.points = []
        self.on_point_click = None

        self.bind("<Configure>", self.on_resize)
        self.bind("<Double-Button-1>", self.on_double_click)

    def draw_chart(self, series, target, sd, title="", dates=None, status=None,
                   y_axis_caption="Value", bottom_text=""):
        """Draw a series against its target.

        @param name: series, target, sd, title, dates, status,
                     y_axis_caption, bottom_text
        """
        self.series = [float(value) for value in series]
        self.target = float(target)
        self.sd = float(sd)
        self.title = title or ""
        self.y_caption = y_axis_caption or "Value"
        self.bottom_text = bottom_text or ""

        if status is None:
            self.status = [1] * len(self.series)
        else:
            self.status = [int(value) for value in status]

        if dates is None:
            self.labels = []
            self.x_caption = "Observation"
        else:
            self.labels = [self.get_label(day) for day in dates]
            self.x_caption = "Date"

        self.redraw()

    def clear(self):
        """Nothing drawn but the empty grid, and nothing remembered."""
        self.delete("all")
        self.series = []
        self.target = 0.0
        self.sd = 0.0
        self.title = ""
        self.status = []
        self.labels = []
        self.points = []
        self.x_caption = "Observation"
        self.y_caption = "Value"
        self.redraw()

    def set_point_click_callback(self, callback):
        """Who to tell when a point is double clicked.

        The callback is handed the point: its index in the series, its
        value, where it was drawn and the date written under it. The index
        is what the main window uses to find the result behind it.

        @param name: callback
        """
        self.on_point_click = callback

    def on_resize(self, evt=None):
        """The drawing follows the window: it is redrawn, not stretched."""
        self.redraw()

    def on_double_click(self, evt):
        """A double click near a point opens whatever the callback opens.

        Near, and not on: a dot of four pixels is not something a hand
        lands on exactly, so the whole circle plus a little counts.
        """
        if self.on_point_click is not None:
            reach = self.POINT_RADIUS + self.REACH
            for point in self.points:
                across = evt.x - point["x"]
                up = evt.y - point["y"]
                if across * across + up * up <= reach * reach:
                    self.on_point_click(point)
                    break

    def redraw(self):
        """What there is room for: the chart, the empty grid, or nothing.

        A standard deviation of zero is not a lot that is perfect, it is a
        lot whose limits were never entered: there is nothing to draw the
        bands against, and the grid says so without pretending.
        """
        self.delete("all")
        self.points = []
        width = self.winfo_width()
        height = self.winfo_height()

        if width < 10 or height < 10:
            pass
        elif not self.series or self.sd == 0:
            self.draw_grid(self.LEFT_MARGIN, self.TOP_MARGIN,
                           width - self.RIGHT_MARGIN, height - self.BOTTOM_MARGIN)
        else:
            self.draw_all(width, height)

    def draw_all(self, width, height):
        """The bands, the grid over them, the axes, the series, the labels.

        In that order, because each one is drawn over the last: the bands
        are filled rectangles and would bury a grid drawn first.
        """
        left = self.LEFT_MARGIN
        top = self.TOP_MARGIN
        right = width - self.RIGHT_MARGIN
        bottom = height - self.BOTTOM_MARGIN
        low, high = self.get_limits()

        self.draw_bands(left, top, right, bottom, low, high)
        self.draw_grid(left, top, right, bottom)

        self.create_line(left, top, left, bottom, fill=self.AXIS_COLOUR, width=1)
        self.create_line(left, bottom, right, bottom, fill=self.AXIS_COLOUR, width=1)

        self.set_points(left, top, right, bottom, low, high)
        self.draw_line()
        self.draw_points()
        self.draw_values()

        self.draw_y_labels(left, top, bottom, low, high)
        self.draw_x_labels(left, right, bottom)

        if self.title:
            self.create_text(width / 2.0, self.TOP_MARGIN / 2.0, text=self.title,
                             anchor=tk.CENTER, font=self.FONT_TITLE,
                             fill=self.AXIS_COLOUR)

        if self.bottom_text:
            self.create_text(right, bottom + 42, text=self.bottom_text,
                             anchor=tk.E, font=self.FONT_LABEL,
                             fill=self.BOTTOM_COLOUR)

    def draw_bands(self, left, top, right, bottom, low, high):
        """The two shaded bands, and the seven lines across the chart.

        Each line has its own weight and its own dash, so which one a point
        has crossed can be read without counting from the middle.
        """
        for deviations, fill in ((2, self.BAND_2_FILL), (1, self.BAND_1_FILL)):
            top_of_band = self.get_y(self.target + deviations * self.sd,
                                     top, bottom, low, high)
            bottom_of_band = self.get_y(self.target - deviations * self.sd,
                                        top, bottom, low, high)
            self.create_rectangle(left, top_of_band, right, bottom_of_band,
                                  fill=fill, outline="")

        for value, colour, width, dash in self.get_levels():
            y = self.get_y(value, top, bottom, low, high)
            self.create_line(left, y, right, y, fill=colour, width=width, dash=dash)

    def get_levels(self):
        """The lines the chart is read against: the target and six bands.

        @return: value, colour, width and dash of each
        @rtype: list of tuples
        """
        found = [(self.target, self.TARGET_COLOUR, 2, None)]

        for deviations, colour, width, dash in ((1, self.SD1_COLOUR, 2, (2, 4)),
                                                (2, self.SD2_COLOUR, 2, (4, 4)),
                                                (3, self.SD3_COLOUR, 3, (6, 4))):
            for side in (-1, 1):
                found.append((self.target + side * deviations * self.sd,
                              colour, width, dash))

        return found

    def draw_grid(self, left, top, right, bottom):
        """A faint dotted grid, to carry the eye across a wide chart."""
        for step in range(1, self.GRID_STEPS):
            x = left + step * (right - left) / self.GRID_STEPS
            y = top + step * (bottom - top) / self.GRID_STEPS
            self.create_line(x, top, x, bottom, fill=self.GRID_COLOUR, dash=(2, 4))
            self.create_line(left, y, right, y, fill=self.GRID_COLOUR, dash=(2, 4))

    def set_points(self, left, top, right, bottom, low, high):
        """Work out where every result goes, once, before anything is drawn.

        The line, the dots and the values are three passes over the same
        points and have to agree about where they are. A result past the
        edge of the chart is kept at its own value and drawn at the edge:
        what is clipped is the picture, never the number.
        """
        self.points = []
        highest = self.target + self.EDGE * self.sd
        lowest = self.target - self.EDGE * self.sd

        for index, value in enumerate(self.series):
            beyond = 0
            drawn = value
            if value > highest:
                beyond = 1
                drawn = highest
            elif value < lowest:
                beyond = -1
                drawn = lowest

            label = None
            if index < len(self.labels):
                label = self.labels[index]

            status = 1
            if index < len(self.status):
                status = self.status[index]

            self.points.append({"index": index,
                                "value": value,
                                "x": self.get_x(index, left, right),
                                "y": self.get_y(drawn, top, bottom, low, high),
                                "label": label,
                                "status": status,
                                "beyond": beyond})

    def draw_line(self):
        """The line through the points, broken around the excluded ones.

        A line drawn straight through a result that was taken out would say
        the series went that way, and it did not: that run is not part of
        it any more.
        """
        run = []

        for point in self.points:
            if point["status"] == 1:
                run.extend((point["x"], point["y"]))
            else:
                self.draw_run(run)
                run = []

        self.draw_run(run)

    def draw_run(self, run):
        """One unbroken stretch of the series, if it is long enough to be one."""
        if len(run) >= 4:
            self.create_line(*run, fill=self.LINE_COLOUR, width=1)

    def draw_points(self):
        """A dot per result, or a triangle where the chart ran out."""
        radius = self.POINT_RADIUS

        for point in self.points:
            colour = self.get_colour(point)
            x, y = point["x"], point["y"]

            if point["beyond"] > 0:
                self.create_polygon(x, y - radius - 2,
                                    x - radius - 1, y + radius,
                                    x + radius + 1, y + radius,
                                    fill=colour, outline=self.AXIS_COLOUR, width=1)
            elif point["beyond"] < 0:
                self.create_polygon(x, y + radius + 2,
                                    x - radius - 1, y - radius,
                                    x + radius + 1, y - radius,
                                    fill=colour, outline=self.AXIS_COLOUR, width=1)
            else:
                self.create_oval(x - radius, y - radius, x + radius, y + radius,
                                 fill=colour, outline=self.AXIS_COLOUR, width=1)

    def draw_values(self):
        """The number over each point, while there are few enough to read.

        Not over the excluded ones: they are out of the statistics, and a
        number written on the chart is read as one of them.
        """
        if len(self.points) <= self.MOST_VALUES:
            for point in self.points:
                if point["status"] == 1:
                    if point["beyond"] > 0:
                        y, anchor = point["y"] + 12, tk.N
                    elif point["beyond"] < 0:
                        y, anchor = point["y"] - 12, tk.S
                    else:
                        y, anchor = point["y"] - 8, tk.S

                    self.create_text(point["x"], y,
                                     text="{0:.2f}".format(point["value"]),
                                     anchor=anchor, font=self.FONT_LABEL,
                                     fill=self.TEXT_COLOUR)

    def draw_y_labels(self, left, top, bottom, low, high):
        """Five values up the side, and what they are measured in."""
        ticks = 5
        step = (high - low) / (ticks - 1)

        for tick in range(ticks):
            value = low + tick * step
            y = self.get_y(value, top, bottom, low, high)
            self.create_line(left - 4, y, left, y, fill=self.AXIS_COLOUR, width=1)
            self.create_text(left - 6, y, text="{0:.2f}".format(value),
                             anchor=tk.E, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

        if self.y_caption:
            # One letter per line: Tk can rotate text, and rotated text on a
            # canvas redrawn at every resize is measured differently by
            # every font. Stacked letters are the same everywhere.
            self.create_text(left - 40, (top + bottom) / 2.0,
                             text="\n".join(list(self.y_caption)),
                             anchor=tk.CENTER, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

    def draw_x_labels(self, left, right, bottom):
        """The days along the bottom, as many as fit without touching."""
        how_many = len(self.series)
        every = max(1, int(round(how_many / self.MOST_DATES)))

        for index in range(0, how_many, every):
            if index < len(self.labels):
                label = self.labels[index]
            else:
                label = str(index + 1)

            self.create_text(self.get_x(index, left, right), bottom + 10,
                             text=label, anchor=tk.N, font=self.FONT_LABEL,
                             fill=self.AXIS_COLOUR)

        if self.x_caption:
            self.create_text((left + right) / 2.0, bottom + 28,
                             text=self.x_caption, anchor=tk.N,
                             font=self.FONT_LABEL, fill=self.AXIS_COLOUR)

    def get_label(self, day):
        """A date as it is written under a point, or whatever it was.

        @param name: day
        @return: the label
        @rtype: string
        """
        if isinstance(day, (datetime.date, datetime.datetime)):
            found = day.strftime(self.DATE_FORMAT)
        else:
            found = str(day)

        return found

    def get_colour(self, point):
        """A point: green inside two deviations, orange past two, red past three.

        Grey when the result was excluded, whatever it is worth: a point
        that is out of the statistics must not be coloured as though it
        were in them.

        @param name: point
        @return: colour
        @rtype: string
        """
        if point["status"] != 1:
            found = self.EXCLUDED_COLOUR
        else:
            away = abs(point["value"] - self.target) / self.sd
            if away < 2.0:
                found = self.INSIDE_COLOUR
            elif away < 3.0:
                found = self.WARNING_COLOUR
            else:
                found = self.VIOLATION_COLOUR

        return found

    def get_limits(self):
        """The ends of the axis: four standard deviations either side, and room.

        @return: lowest, highest
        @rtype: tuple
        """
        lowest = self.target - self.EDGE * self.sd
        highest = self.target + self.EDGE * self.sd
        spare = (highest - lowest) * self.SPARE

        return (lowest - spare, highest + spare)

    def get_x(self, index, left, right):
        """Where the result at this position falls across the chart."""
        if len(self.series) <= 1:
            found = (left + right) / 2.0
        else:
            found = left + index * (right - left) / (len(self.series) - 1)

        return found

    def get_y(self, value, top, bottom, low, high):
        """Where a value falls up the chart."""
        if high == low:
            found = (top + bottom) / 2.0
        else:
            found = bottom - (value - low) / (high - low) * (bottom - top)

        return found
