#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# module:   ljcanvas
# purpose:  Levey–Jennings chart using pure Tkinter Canvas
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
# -----------------------------------------------------------------------------

import tkinter as tk
import datetime as _dt
from typing import Iterable, List, Optional, Sequence, Tuple, Any


class LeveyJenningsCanvas(tk.Canvas):
    """
    Simple Levey–Jennings chart using pure Tkinter Canvas.

    Features:
        - X axis: observation index or dates
        - Y axis: numeric values
        - Horizontal lines: target, ±1SD, ±2SD, ±3SD
        - Points colored by SD distance:
            green  → |value - target| < 2SD
            yellow → 2SD ≤ |value - target| < 3SD
            red    → |value - target| ≥ 3SD

    This widget is *not* a generic plotting library.
    It is intentionally focused on QC / Levey–Jennings style charts.
    """

    # Layout margins (pixels)
    LEFT_MARGIN   = 70
    RIGHT_MARGIN  = 20
    TOP_MARGIN    = 40
    BOTTOM_MARGIN = 60

    
    # Basic colors
    GRID_COLOR    = "#d0d0d0"
    AXIS_COLOR    = "#000000"

    TARGET_COLOR  = "#00008b"   # deep blue
    SD1_COLOR     = "#006400"   # dark green (±1 SD)
    SD2_COLOR     = "#ff9800"   # saturated orange (±2 SD)
    SD3_COLOR     = "#e74c3c"   # technical red (±3 SD)

    # Shaded bands between SD lines
    BAND_1_FILL   = "#e6f4e6"   # very light green  (Target ±1SD)
    BAND_2_FILL   = "#fff6cc"   # very light yellow (Target ±2SD)



    POINT_RADIUS  = 4

    FONT_LABEL    = ("TkDefaultFont", 6)
    FONT_TITLE    = ("TkDefaultFont", 10, "bold")

    def __init__(self, parent: tk.Widget, **kwargs: Any) -> None:
        """
        Create a Levey–Jennings canvas.

        Typical usage:
            self.chart = LeveyJenningsCanvas(parent, bg="white", height=300)
            self.chart.pack(fill=tk.BOTH, expand=True)
        """
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self._series: List[float] = []
        self._target: float = 0.0
        self._sd: float = 0.0
        self._title: Optional[str] = None
        # Stored as label strings (already formatted)
        self._x_labels: Optional[List[str]] = None
        # Status list: 1 = enabled, 0 = disabled (same length as series)
        self._status: Optional[List[int]] = None

        # Optional axis captions
        self._x_axis_caption: str = "Observation"
        self._y_axis_caption: str = "Value"

        # Hit–test data for points
        self._points_info: List[dict] = []
        self._on_point_click = None  # callback esterna

        # Redraw on resize
        self.bind("<Configure>", self._on_resize)

        # Double–click on point
        self.bind("<Double-Button-1>", self._on_double_click)

        self._show_values = True
        self.FONT_VALUES = ("TkDefaultFont", 8)
        self._bottom_text: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw_chart(
        self,
        series: Iterable[float],
        target: float,
        sd: float,
        *,
        title: Optional[str] = None,
        dates: Optional[Sequence[Any]] = None,
        status: Optional[Sequence[int]] = None,
        x_axis_caption: Optional[str] = None,
        y_axis_caption: Optional[str] = None,
        date_format: str = "%d-%m",
        show_values: bool = True,
        bottom_text: Optional[str] = None,
    ) -> None:
        """
        Draw a Levey–Jennings chart.

        Args:
            series: iterable of numeric QC results (chronological order).
            target: target value of the control.
            sd:     standard deviation used for SD bands.
            title:  optional chart title (e.g. "QC – Control L1").
            dates:  optional sequence (same length as series) used for X labels.
                    Elements can be:
                        - datetime.date / datetime.datetime
                        - any object accepted by str()
            status: optional sequence (same length as series) of status values.
                    1 = enabled (normal display with connecting lines)
                    0 = disabled (gray color, no connecting lines)
            x_axis_caption: optional caption for X axis (default "Observation"
                            or "Date" if dates are provided).
            y_axis_caption: optional caption for Y axis (default "Value").
            date_format:    strftime format if dates are datetime objects.
        """
        # Store numeric data
        self._series = [float(v) for v in series]
        self._target = float(target)
        self._sd = float(sd)
        self._title = title

        # Store status (1=enabled, 0=disabled)
        if status is not None:
            self._status = [int(s) for s in status]
        else:
            # Default: all enabled
            self._status = [1] * len(self._series)

        # Axis captions
        if y_axis_caption is not None:
            self._y_axis_caption = y_axis_caption
        else:
            self._y_axis_caption = "Value"

        # Prepare X labels
        if dates is not None:
            labels: List[str] = []
            for d in dates:
                if isinstance(d, (_dt.date, _dt.datetime)):
                    labels.append(d.strftime(date_format))
                else:
                    labels.append(str(d))
            self._x_labels = labels
            # If no explicit caption is given, use "Date"
            self._x_axis_caption = x_axis_caption or "Date"
        else:
            # No dates → we will show index (1..N)
            self._x_labels = None
            self._x_axis_caption = x_axis_caption or "Observation"

        self._show_values = show_values
        self._bottom_text = bottom_text or ""
        self._redraw()

    def clear(self) -> None:
        """
        Clear the canvas and reset internal data.
        """
        self.delete("all")

        self._series = []
        self._target = 0.0
        self._sd = 0.0
        self._title = None
        self._x_labels = None
        self._status = None
        self._x_axis_caption = "Observation"
        self._y_axis_caption = "Value"

        # Draw placeholder grid
        self._draw_no_data()

    def set_point_click_callback(self, callback) -> None:
        """
        Register a callback called when the user double–clicks on a point.

        callback signature:
            callback(info: dict)

        Where info contains at least:
            - index  (0-based index in series)
            - value  (float)
            - x, y   (canvas coordinates)
            - label  (optional X label, e.g. date)
        """
        self._on_point_click = callback


    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_resize(self, event: tk.Event) -> None:
        """Redraw chart (or placeholder) when the widget is resized."""
        self._redraw()


    def _redraw(self) -> None:
        """Clear the canvas and draw the full chart."""
        self.delete("all")

        self._points_info = []

        if not self._series or self._sd == 0:
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

        # Compute Y-axis limits
        y_min, y_max = self._compute_y_limits()

        # Draw SD bands and axes
        # Draw grid first (background)
        self._draw_grid(x0, y0, x1, y1)


        # SD bands (shading + horizontal lines)
        self._draw_y_bands(x0, y0, x1, y1, y_min, y_max)

        # Grid on top of shading
        self._draw_grid(x0, y0, x1, y1)

        # Axes on top of grid
        self._draw_axes(x0, y0, x1, y1)



        # Draw series
        self._draw_series(x0, y0, x1, y1, y_min, y_max)

        # Labels and title
        self._draw_y_labels(x0, y0, y1, y_min, y_max)
        self._draw_x_labels(x0, y0, x1, y1)
        self._draw_title(width)
        self._draw_bottom_text(x0, x1, y1)


    def _draw_bottom_text(self, x0: int, x1: int, y1: int) -> None:
        """
        Draw a small information string in the bottom-right area
        (e.g. 'Computed 28 on 30 results').
        """
        if not self._bottom_text:
            return

        self.create_text(
            x1,
            y1 + 42,  # under X axis caption
            text=self._bottom_text,
            anchor="e",
            font=self.FONT_LABEL,
            fill="#444444",
        )

    def _draw_no_data(self) -> None:
        """
        Show a faint grid placeholder when no data or invalid SD.
        """
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        x0 = self.LEFT_MARGIN
        y0 = self.TOP_MARGIN
        x1 = w - self.RIGHT_MARGIN
        y1 = h - self.BOTTOM_MARGIN

        self._draw_grid(x0, y0, x1, y1)




    # --------------------------- Y / scaling ---------------------------

    def _compute_y_limits(self) -> Tuple[float, float]:
        """
        Compute Y-axis limits using target ± 4SD (Westgard recommendation).

        Values beyond ±4SD will be clipped to the edge of the chart
        and displayed with a triangle marker to indicate "out of range".
        """
        target = self._target
        sd = self._sd

        # Fixed scale at ±4SD per Westgard best practices
        y_min = target - 4 * sd
        y_max = target + 4 * sd

        # Small margin for visual clarity
        span = y_max - y_min if y_max != y_min else 1.0
        margin = span * 0.05
        return y_min - margin, y_max + margin

    @staticmethod
    def _value_to_y(
        value: float, y0: int, y1: int, y_min: float, y_max: float
    ) -> float:
        """
        Map a data value to canvas Y coordinate (inverted axis).
        """
        if y_max == y_min:
            return (y0 + y1) / 2.0

        t = (value - y_min) / (y_max - y_min)
        return y1 - t * (y1 - y0)

    @staticmethod
    def _index_to_x(idx: int, n: int, x0: int, x1: int) -> float:
        """
        Map series index (0..n-1) to canvas X coordinate.
        """
        if n <= 1:
            return (x0 + x1) / 2.0
        step = (x1 - x0) / max(1, (n - 1))
        return x0 + idx * step

    # ----------------------------- Bands -------------------------------

    def _draw_y_bands(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        y_min: float,
        y_max: float,
    ) -> None:
        """
        Draw shaded bands for ±1SD and ±2SD and the horizontal SD/target lines.
        """
        target = self._target
        sd = self._sd

        if sd <= 0:
            return

        # First compute all Y positions
        levels = {
            "target": target,
            "+1sd": target + sd,
            "-1sd": target - sd,
            "+2sd": target + 2 * sd,
            "-2sd": target - 2 * sd,
            "+3sd": target + 3 * sd,
            "-3sd": target - 3 * sd,
        }

        y_pos = {
            name: self._value_to_y(value, y0, y1, y_min, y_max)
            for name, value in levels.items()
        }

        # ------------------------------------------------------------------
        # Shaded bands (drawn first)
        # ------------------------------------------------------------------
        # Target ±2SD (background band)
        y_top_2 = y_pos["+2sd"]
        y_bot_2 = y_pos["-2sd"]
        if y_top_2 > y_bot_2:
            y_top_2, y_bot_2 = y_bot_2, y_top_2

        self.create_rectangle(
            x0,
            y_top_2,
            x1,
            y_bot_2,
            fill=self.BAND_2_FILL,
            outline="",
        )

        # Target ±1SD (inner band, overrides colour inside)
        y_top_1 = y_pos["+1sd"]
        y_bot_1 = y_pos["-1sd"]
        if y_top_1 > y_bot_1:
            y_top_1, y_bot_1 = y_bot_1, y_top_1

        self.create_rectangle(
            x0,
            y_top_1,
            x1,
            y_bot_1,
            fill=self.BAND_1_FILL,
            outline="",
        )

        # ------------------------------------------------------------------
        # Horizontal lines (target, ±1/2/3 SD)
        # ------------------------------------------------------------------
        level_styles = {
            "target": ("Target", self.TARGET_COLOR),
            "+1sd": ("+1 SD", self.SD1_COLOR),
            "-1sd": ("-1 SD", self.SD1_COLOR),
            "+2sd": ("+2 SD", self.SD2_COLOR),
            "-2sd": ("-2 SD", self.SD2_COLOR),
            "+3sd": ("+3 SD", self.SD3_COLOR),
            "-3sd": ("-3 SD", self.SD3_COLOR),
        }

        for name, (label, color) in level_styles.items():
            y = y_pos[name]
            width = 1
            dash = None

            if name == "target":
                width = 2
            elif "1sd" in name:
                width = 2
                dash = (2, 4)
            elif "2sd" in name:
                width = 2
                dash = (4, 4)
            elif "3sd" in name:
                width = 3
                dash = (6, 4)

            self.create_line(
                x0,
                y,
                x1,
                y,
                fill=color,
                width=width,
                dash=dash,
            )


    # ------------------------------ Axes -------------------------------

    def _draw_axes(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """Draw X and Y axes."""
        # Y axis
        self.create_line(
            x0,
            y0,
            x0,
            y1,
            fill=self.AXIS_COLOR,
            width=1,
        )

        # X axis
        self.create_line(
            x0,
            y1,
            x1,
            y1,
            fill=self.AXIS_COLOR,
            width=1,
        )

           # ----------------------------- Grid -------------------------------

        # ----------------------------- Grid -------------------------------

    def _draw_grid(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """
        Draw a faint dotted grid behind the Levey–Jennings chart.
        """
        grid_color = self.GRID_COLOR
        rows = 6
        cols = 6

        dx = (x1 - x0) / cols
        dy = (y1 - y0) / rows

        # Vertical dotted lines
        for i in range(1, cols):
            x = x0 + i * dx
            self.create_line(
                x,
                y0,
                x,
                y1,
                fill=grid_color,
                dash=(2, 4),
            )

        # Horizontal dotted lines
        for i in range(1, rows):
            y = y0 + i * dy
            self.create_line(
                x0,
                y,
                x1,
                y,
                fill=grid_color,
                dash=(2, 4),
            )


 

    # ---------------------------- Series -------------------------------

    def _draw_series(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        y_min: float,
        y_max: float,
    ) -> None:
        """Draw series as line + colored points (respecting enabled/disabled status).

        Points beyond ±4SD are clipped to the chart edge and displayed
        as triangles pointing in the direction of the actual value.
        """
        n = len(self._series)
        if n == 0:
            return

        target = self._target
        sd = self._sd

        # Clip threshold at ±4SD
        clip_high = target + 4 * sd
        clip_low = target - 4 * sd

        # Build points with status and clipping info
        # (x, y, value, status, is_clipped, clip_direction)
        # clip_direction: 1 = above, -1 = below, 0 = not clipped
        points: List[Tuple[float, float, float, int, bool, int]] = []
        for idx, value in enumerate(self._series):
            v = float(value)
            x = self._index_to_x(idx, n, x0, x1)

            # Check if value needs clipping
            is_clipped = False
            clip_direction = 0
            display_value = v

            if v > clip_high:
                is_clipped = True
                clip_direction = 1  # pointing up (value is above)
                display_value = clip_high
            elif v < clip_low:
                is_clipped = True
                clip_direction = -1  # pointing down (value is below)
                display_value = clip_low

            y = self._value_to_y(display_value, y0, y1, y_min, y_max)

            # Get status (default to enabled if not provided)
            status = 1
            if self._status is not None and idx < len(self._status):
                status = self._status[idx]

            points.append((x, y, v, status, is_clipped, clip_direction))

            # Save info for hit-test
            label = None
            if self._x_labels is not None and idx < len(self._x_labels):
                label = self._x_labels[idx]

            self._points_info.append(
                {
                    "index": idx,
                    "value": v,
                    "x": x,
                    "y": y,
                    "label": label,
                }
            )

        # Connecting lines ONLY between consecutive enabled points
        if n > 1:
            line_coords: List[float] = []
            for idx, (x, y, _, status, _, _) in enumerate(points):
                if status == 1:  # Enabled point
                    line_coords.extend((x, y))
                else:
                    # Disabled point - finish current line segment if any
                    if len(line_coords) >= 4:  # At least 2 points
                        self.create_line(
                            *line_coords,
                            fill="#444444",
                            width=1,
                        )
                    line_coords = []  # Start new segment

            # Draw final segment if any
            if len(line_coords) >= 4:
                self.create_line(
                    *line_coords,
                    fill="#444444",
                    width=1,
                )

        # Points with color based on status
        for x, y, value, status, is_clipped, clip_direction in points:
            if status == 1:
                # Enabled: normal color (green/yellow/red based on SD)
                color = self._get_point_color(value)
            else:
                # Disabled: gray color to indicate it's not active
                color = "#999999"

            r = self.POINT_RADIUS

            if is_clipped:
                # Draw triangle for clipped points
                if clip_direction == 1:
                    # Triangle pointing UP (value is above chart)
                    self.create_polygon(
                        x, y - r - 2,      # top vertex
                        x - r - 1, y + r,  # bottom left
                        x + r + 1, y + r,  # bottom right
                        fill=color,
                        outline="#000000",
                        width=1,
                    )
                else:
                    # Triangle pointing DOWN (value is below chart)
                    self.create_polygon(
                        x, y + r + 2,      # bottom vertex
                        x - r - 1, y - r,  # top left
                        x + r + 1, y - r,  # top right
                        fill=color,
                        outline="#000000",
                        width=1,
                    )
            else:
                # Normal circle for non-clipped points
                self.create_oval(
                    x - r,
                    y - r,
                    x + r,
                    y + r,
                    fill=color,
                    outline="#000000",
                    width=1,
                )

        # Etichette opzionali dei valori (se abilitate altrove)
        if getattr(self, "_show_values", False) and len(points) <= 30:
            for x, y, value, status, is_clipped, clip_direction in points:
                # Only show values for enabled points
                if status == 1:
                    # Position label above or below based on clipping
                    if is_clipped and clip_direction == 1:
                        # Clipped above: put label below the triangle
                        label_y = y + 12
                        anchor = "n"
                    elif is_clipped and clip_direction == -1:
                        # Clipped below: put label above the triangle
                        label_y = y - 12
                        anchor = "s"
                    else:
                        # Normal: label above the point
                        label_y = y - 8
                        anchor = "s"

                    self.create_text(
                        x,
                        label_y,
                        text=f"{value:.2f}",
                        anchor=anchor,
                        font=self.FONT_LABEL,
                        fill="#333333",
                    )



    def _get_point_color(self, value: float) -> str:
        """
        Return color based on SD distance:

            |z| < 2  → green
            2 ≤ |z| < 3 → yellow
            |z| ≥ 3 → red
        """
        if self._sd == 0:
            return "#00aa00"

        z = (value - self._target) / self._sd
        az = abs(z)
        if az < 2.0:
            return "#00aa00"   # green
        elif az < 3.0:
            return "#ffcc00"   # yellow
        else:
            return "#ff0000"   # red

    # --------------------------- Labels / title ------------------------

    def _draw_y_labels(
        self, x0: int, y0: int, y1: int, y_min: float, y_max: float
    ) -> None:
        """
        Draw Y axis tick labels (5 ticks: min..max).
        """
        ticks = 5
        span = y_max - y_min if y_max != y_min else 1.0
        step = span / max(1, (ticks - 1))

        for i in range(ticks):
            value = y_min + i * step
            y = self._value_to_y(value, y0, y1, y_min, y_max)

            # Tick mark
            self.create_line(
                x0 - 4,
                y,
                x0,
                y,
                fill=self.AXIS_COLOR,
                width=1,
            )

            # Label
            text = f"{value:.2f}"
            self.create_text(
                x0 - 6,
                y,
                text=text,
                anchor="e",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        # Y axis caption (rotated)
        caption = self._y_axis_caption
        if caption:
            # Tkinter Canvas has no native text rotation.
            # A simple approach is to place it vertically using newlines.
            vertical = "\n".join(list(caption))
            self.create_text(
                x0 - 40,
                (y0 + y1) / 2.0,
                text=vertical,
                anchor="center",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

    def _draw_x_labels(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """
        Draw X axis tick labels.

        If self._x_labels is defined and has the same length of the series,
        use those (dates or custom labels). Otherwise use 1..N.

        To avoid cluttered labels, only a limited number of them is shown.
        """
        n = len(self._series)
        if n == 0:
            return

        # Decide labels
        if self._x_labels is not None and len(self._x_labels) == n:
            labels: List[str] = list(self._x_labels)
        else:
            labels = [str(i + 1) for i in range(n)]

        # Keep labels compact (defensive: truncate very long strings)
        truncated: List[str] = []
        for text in labels:
            s = str(text)
            if len(s) > 8:
                s = s[:8]
            truncated.append(s)
        labels = truncated

        # Limit the number of visible labels
        max_labels = 8                       # <= circa 8 etichette al massimo
        step = max(1, int(round(n / max_labels)))

        for idx in range(0, n, step):
            x = self._index_to_x(idx, n, x0, x1)
            label = labels[idx]
            self.create_text(
                x,
                y1 + 10,
                text=label,
                anchor="n",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        # X axis caption
        caption = self._x_axis_caption
        if caption:
            self.create_text(
                (x0 + x1) / 2.0,
                y1 + 28,
                text=caption,
                anchor="n",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

    def _draw_title(self, width: int) -> None:
        """Draw chart title, if any."""
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

    def _on_double_click(self, event: tk.Event) -> None:
        """
        Handle double–clicks on the canvas.

        If the click is close to a point, call the registered callback
        with the point info.
        """
        if not self._on_point_click or not self._points_info:
            return

        x_click = event.x
        y_click = event.y
        hit_radius = self.POINT_RADIUS + 3

        for info in self._points_info:
            dx = x_click - info["x"]
            dy = y_click - info["y"]
            if dx * dx + dy * dy <= hit_radius * hit_radius:
                # Punto trovato → chiama callback
                self._on_point_click(info)
                break

