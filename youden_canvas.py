# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk


class YoudenPlotCanvas(tk.Canvas):
    """
    Simple Youden plot using pure Tkinter Canvas.

    Designed for two control levels measured on the same series of runs:

        - X axis  -> Level 1 results
        - Y axis  -> Level 2 results
        - Vertical/horizontal lines: target +/-1SD, +/-2SD
        - Points: paired results (x_i, y_i)

    This widget is intentionally focused on QC / Youden charts and is not
    a general plotting library.
    """

    LEFT_MARGIN   = 80
    RIGHT_MARGIN  = 20
    TOP_MARGIN    = 40
    BOTTOM_MARGIN = 50

    AXIS_COLOR   = "#000000"
    GRID_COLOR   = "#dddddd"
    TARGET_COLOR = "#0000aa"   # blue
    SD1_COLOR    = "#88bbff"   # light blue
    SD2_COLOR    = "#ffcc66"   # light orange

    POINT_COLOR      = "#008800"
    POINT_OUT_COLOR  = "#ff0000"  # for clearly out-of-range points
    POINT_RADIUS     = 4

    FONT_LABEL = ("TkDefaultFont", 9)
    FONT_TITLE = ("TkDefaultFont", 10, "bold")
    FONT_VALUES = ("TkDefaultFont", 8)

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self._points = []
        self._target_x = 0.0
        self._target_y = 0.0
        self._sd_x = 0.0
        self._sd_y = 0.0

        self._title = None
        self._x_label = "Level 1"
        self._y_label = "Level 2"
        self._bottom_text = ""

        self._show_indices = False

        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def draw_youden(
        self,
        level1,
        level2,
        target_x,
        target_y,
        sd_x,
        sd_y,
        *,
        title=None,
        x_label = "Level 1",
        y_label = "Level 2",
        bottom_text=None,
        show_indices=False,
    ):
        """
        Draw a Youden plot.

        Args:
            level1: iterable of numeric results for level 1 (x-axis).
            level2: iterable of numeric results for level 2 (y-axis).
                    Must have the same length as level1.
            target_x: target value for level 1.
            target_y: target value for level 2.
            sd_x: standard deviation for level 1.
            sd_y: standard deviation for level 2.
            title: optional chart title.
            x_label: X axis label (e.g. 'L1 (ug/mL)').
            y_label: Y axis label.
            bottom_text: small string shown under the plot
                         (e.g. 'Computed 30 paired results').
            show_indices: if True, annotate points with their index (1..N).
        """
        level1_list = [float(v) for v in level1]
        level2_list = [float(v) for v in level2]

        n = min(len(level1_list), len(level2_list))
        self._points = list(zip(level1_list[:n], level2_list[:n]))

        self._target_x = float(target_x)
        self._target_y = float(target_y)
        self._sd_x = float(sd_x)
        self._sd_y = float(sd_y)

        self._title = title
        self._x_label = x_label
        self._y_label = y_label
        self._bottom_text = bottom_text or ""
        self._show_indices = show_indices

        self._redraw()

    def clear(self):
        """Clear the canvas."""
        self.delete("all")
        self._points = []

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _on_resize(self, event):
        if self._points:
            self._redraw()

    def _redraw(self):
        self.delete("all")

        if not self._points or self._sd_x == 0 or self._sd_y == 0:
            self._draw_no_data()
            return

        width = self.winfo_width()
        height = self.winfo_height()
        if width < 10 or height < 10:
            return

        x0 = self.LEFT_MARGIN
        y0 = self.TOP_MARGIN
        x1 = width - self.RIGHT_MARGIN
        y1 = height - self.BOTTOM_MARGIN

        # Determine ranges (use target +/-2SD plus data min/max)
        x_min, x_max, y_min, y_max = self._compute_limits()

        # Axes and grid
        self._draw_axes(x0, y0, x1, y1)
        self._draw_grid(x0, y0, x1, y1, x_min, x_max, y_min, y_max)

        # SD bands and target crosshair
        self._draw_sd_lines(x0, y0, x1, y1, x_min, x_max, y_min, y_max)

        # Points
        self._draw_points(x0, y0, x1, y1, x_min, x_max, y_min, y_max)

        # Labels, title, bottom text
        self._draw_labels(x0, y0, x1, y1, x_min, x_max, y_min, y_max)
        self._draw_title(width)
        self._draw_bottom_text(x0, x1, y1)

    def _draw_no_data(self):
        w = self.winfo_width()
        h = self.winfo_height()
        self.create_text(
            w / 2,
            h / 2,
            text="No data",
            font=self.FONT_TITLE,
            fill="gray",
        )

    # ---------------------------- Scaling ------------------------------ #

    def _compute_limits(self):
        xs = [p[0] for p in self._points]
        ys = [p[1] for p in self._points]

        x_min = min(xs + [self._target_x - 2 * self._sd_x])
        x_max = max(xs + [self._target_x + 2 * self._sd_x])
        y_min = min(ys + [self._target_y - 2 * self._sd_y])
        y_max = max(ys + [self._target_y + 2 * self._sd_y])

        # Small margins
        span_x = x_max - x_min if x_max != x_min else 1.0
        span_y = y_max - y_min if y_max != y_min else 1.0

        margin_x = span_x * 0.10
        margin_y = span_y * 0.10

        return x_min - margin_x, x_max + margin_x, y_min - margin_y, y_max + margin_y

    @staticmethod
    def _value_to_x(
        value, x0, x1, x_min, x_max
    ):
        if x_max == x_min:
            return (x0 + x1) / 2.0
        t = (value - x_min) / (x_max - x_min)
        return x0 + t * (x1 - x0)

    @staticmethod
    def _value_to_y(
        value, y0, y1, y_min, y_max
    ):
        if y_max == y_min:
            return (y0 + y1) / 2.0
        t = (value - y_min) / (y_max - y_min)
        return y1 - t * (y1 - y0)

    # ------------------------------ Axes ------------------------------- #

    def _draw_axes(self, x0, y0, x1, y1):
        self.create_line(x0, y0, x0, y1, fill=self.AXIS_COLOR, width=1)
        self.create_line(x0, y1, x1, y1, fill=self.AXIS_COLOR, width=1)

    def _draw_grid(
        self,
        x0,
        y0,
        x1,
        y1,
        x_min,
        x_max,
        y_min,
        y_max,
    ):
        # Simple 4x4 grid
        steps = 4
        for i in range(1, steps + 1):
            t = i / (steps + 1)
            # vertical
            xv = x0 + t * (x1 - x0)
            self.create_line(xv, y0, xv, y1, fill=self.GRID_COLOR, width=1)
            # horizontal
            yh = y1 - t * (y1 - y0)
            self.create_line(x0, yh, x1, yh, fill=self.GRID_COLOR, width=1)

    # --------------------------- SD / target --------------------------- #

    def _draw_sd_lines(
        self,
        x0,
        y0,
        x1,
        y1,
        x_min,
        x_max,
        y_min,
        y_max,
    ):
        # Target crosshair
        tx = self._value_to_x(self._target_x, x0, x1, x_min, x_max)
        ty = self._value_to_y(self._target_y, y0, y1, y_min, y_max)

        self.create_line(x0, ty, x1, ty, fill=self.TARGET_COLOR, width=2)
        self.create_line(tx, y0, tx, y1, fill=self.TARGET_COLOR, width=2)

        # +/-1SD and +/-2SD bands
        x_levels = [
            (self._target_x - self._sd_x, self.SD1_COLOR, (2, 4)),
            (self._target_x + self._sd_x, self.SD1_COLOR, (2, 4)),
            (self._target_x - 2 * self._sd_x, self.SD2_COLOR, (4, 4)),
            (self._target_x + 2 * self._sd_x, self.SD2_COLOR, (4, 4)),
        ]
        y_levels = [
            (self._target_y - self._sd_y, self.SD1_COLOR, (2, 4)),
            (self._target_y + self._sd_y, self.SD1_COLOR, (2, 4)),
            (self._target_y - 2 * self._sd_y, self.SD2_COLOR, (4, 4)),
            (self._target_y + 2 * self._sd_y, self.SD2_COLOR, (4, 4)),
        ]

        for value, color, dash in x_levels:
            x = self._value_to_x(value, x0, x1, x_min, x_max)
            self.create_line(x, y0, x, y1, fill=color, width=1, dash=dash)

        for value, color, dash in y_levels:
            y = self._value_to_y(value, y0, y1, y_min, y_max)
            self.create_line(x0, y, x1, y, fill=color, width=1, dash=dash)

    # ------------------------------ Points ----------------------------- #

    def _draw_points(
        self,
        x0,
        y0,
        x1,
        y1,
        x_min,
        x_max,
        y_min,
        y_max,
    ):
        for idx, (vx, vy) in enumerate(self._points):
            x = self._value_to_x(vx, x0, x1, x_min, x_max)
            y = self._value_to_y(vy, y0, y1, y_min, y_max)

            # Simple rule: if point is beyond +/-2SD in either axis -> red
            out = (
                abs(vx - self._target_x) > 2 * self._sd_x
                or abs(vy - self._target_y) > 2 * self._sd_y
            )
            color = self.POINT_OUT_COLOR if out else self.POINT_COLOR

            r = self.POINT_RADIUS
            self.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill=color,
                outline="#000000",
                width=1,
            )

            if self._show_indices:
                self.create_text(
                    x + r + 2,
                    y - r - 2,
                    text=str(idx + 1),
                    anchor="sw",
                    font=self.FONT_VALUES,
                    fill="#202020",
                )

    # --------------------------- Labels / title ------------------------ #

    def _draw_labels(
        self,
        x0,
        y0,
        x1,
        y1,
        x_min,
        x_max,
        y_min,
        y_max,
    ):
        # X ticks (min, target, max)
        x_ticks = [x_min, self._target_x, x_max]
        for value in x_ticks:
            x = self._value_to_x(value, x0, x1, x_min, x_max)
            self.create_line(x, y1, x, y1 + 4, fill=self.AXIS_COLOR, width=1)
            self.create_text(
                x,
                y1 + 10,
                text=f"{value:.2f}",
                anchor="n",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        # Y ticks (min, target, max)
        y_ticks = [y_min, self._target_y, y_max]
        for value in y_ticks:
            y = self._value_to_y(value, y0, y1, y_min, y_max)
            self.create_line(x0 - 4, y, x0, y, fill=self.AXIS_COLOR, width=1)
            self.create_text(
                x0 - 6,
                y,
                text=f"{value:.2f}",
                anchor="e",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        # Axis labels
        if self._x_label:
            self.create_text(
                (x0 + x1) / 2.0,
                y1 + 28,
                text=self._x_label,
                anchor="n",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        if self._y_label:
            vertical = "\n".join(list(self._y_label))
            self.create_text(
                x0 - 62,
                (y0 + y1) / 2.0,
                text=vertical,
                anchor="center",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

    def _draw_title(self, width):
        if not self._title:
            return
        self.create_text(
            width / 2.0,
            self.TOP_MARGIN / 2.0,
            text=self._title,
            anchor="center",
            font=self.FONT_TITLE,
            fill=self.AXIS_COLOR,
        )

    def _draw_bottom_text(self, x0, x1, y1):
        if not self._bottom_text:
            return
        self.create_text(
            x1,
            y1 + 40,
            text=self._bottom_text,
            anchor="e",
            font=self.FONT_LABEL,
            fill="#444444",
        )
