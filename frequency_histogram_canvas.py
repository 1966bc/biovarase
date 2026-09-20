#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk


class FrequencyHistogramCanvas(tk.Canvas):
    """
    Simple frequency histogram using pure Tkinter Canvas.

    It is designed as a companion to LeveyJenningsCanvas and is focused
    on QC-style distributions:

        - X axis: result values (binned)
        - Y axis: frequency (count) per bin
        - Vertical lines: target and mean

    This widget is intentionally minimalistic and not a general plotting library.
    """

    LEFT_MARGIN   = 60
    RIGHT_MARGIN  = 20
    TOP_MARGIN    = 30
    BOTTOM_MARGIN = 40

    AXIS_COLOR   = "#000000"
    GRID_COLOR   = "#dddddd"
    BAR_COLOR    = "#cccccc"
    TARGET_COLOR = "#ff8800"   # orange
    MEAN_COLOR   = "#0000cc"   # blue

    FONT_LABEL = ("TkDefaultFont", 9)
    FONT_TITLE = ("TkDefaultFont", 8, "bold")

    def __init__(self, parent, **kwargs):
        """
        Create a frequency histogram canvas.

        kwargs are passed directly to tk.Canvas.
        """
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self._values = []
        self._target = None
        self._mean = None
        self._title = None
        self._x_label = "Result"
        self._y_label = "Frequency"
        self._bottom_text = ""

        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def draw_histogram(
        self,
        values,
        target=None,
        mean=None,
        *,
        title=None,
        x_label = "Result",
        y_label = "Frequency",
        bottom_text=None,
        max_bins=10,
    ):
        """
        Draw histogram for the given values.

        Args:
            values: numeric results used to compute the histogram.
            target: target value (will be drawn as vertical orange line).
            mean:   computed mean (will be drawn as vertical blue line).
            title:  optional title.
            x_label: X axis label.
            y_label: Y axis label.
            bottom_text: optional small string shown below the chart
                         (e.g. "Computed 28 on 30 results").
            max_bins: maximum number of bins to use.
        """
        self._values = [float(v) for v in values]
        self._target = float(target) if target is not None else None
        self._mean = float(mean) if mean is not None else None
        self._title = ""
        self._x_label = x_label
        self._y_label = y_label
        self._bottom_text = bottom_text or ""

        self._max_bins = max_bins
        self._redraw()

    def clear(self):
        """Clear the canvas content."""
        self.delete("all")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _on_resize(self, event):
        if self._values:
            self._redraw()

    def _redraw(self):
        self.delete("all")

        if not self._values:
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

        # Compute histogram bins
        bins, counts = self._compute_histogram(self._values, self._max_bins)
        if not bins or not counts:
            self._draw_no_data()
            return

        # Determine Y max (counts)
        max_count = max(counts) if counts else 1

        # Draw axes, grid, bars, lines
        self._draw_axes(x0, y0, x1, y1)
        self._draw_grid_y(x0, y0, x1, y1, max_count)
        self._draw_bars(x0, y0, x1, y1, bins, counts, max_count)
        self._draw_vertical_lines(x0, y0, x1, y1, bins)

        # Labels and title
        self._draw_y_labels(x0, y0, y1, max_count)
        self._draw_x_labels(x0, y0, x1, y1, bins)
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

    # ---------------------------- Histogram ---------------------------- #

    @staticmethod
    def _compute_histogram(values, max_bins):
        """
        Compute simple histogram bins and counts.

        Returns:
            bins: list of (start, end) for each bin
            counts: list of counts per bin
        """
        if not values:
            return [], []

        v_min = min(values)
        v_max = max(values)

        if v_max == v_min:
            # All values identical: single bin
            return [(v_min - 0.5, v_max + 0.5)], [len(values)]

        # Number of bins: approx sqrt(N), limited to [3..max_bins]
        import math

        n = len(values)
        nb = int(round(math.sqrt(n)))
        nb = max(3, min(nb, max_bins))

        bin_width = (v_max - v_min) / nb

        bins = []
        start = v_min
        for _ in range(nb):
            end = start + bin_width
            bins.append((start, end))
            start = end

        counts = [0 for _ in range(nb)]
        for v in values:
            # Last bin is inclusive on the right
            if v >= bins[-1][1]:
                counts[-1] += 1
            else:
                for i, (b_start, b_end) in enumerate(bins):
                    if b_start <= v < b_end:
                        counts[i] += 1
                        break

        return bins, counts

    # ------------------------------ Axes ------------------------------- #

    def _draw_axes(self, x0, y0, x1, y1):
        # Y axis
        self.create_line(x0, y0, x0, y1, fill=self.AXIS_COLOR, width=1)
        # X axis
        self.create_line(x0, y1, x1, y1, fill=self.AXIS_COLOR, width=1)

    def _draw_grid_y(self, x0, y0, x1, y1, max_count):
        # Simple grid: 4 horizontal lines
        steps = 4
        for i in range(1, steps + 1):
            t = i / steps
            y = y1 - t * (y1 - y0)
            self.create_line(x0, y, x1, y, fill=self.GRID_COLOR, width=1)

    # ------------------------------ Bars ------------------------------- #

    def _draw_bars(
        self,
        x0,
        y0,
        x1,
        y1,
        bins,
        counts,
        max_count,
    ):
        n_bins = len(bins)
        if n_bins == 0 or max_count <= 0:
            return

        # Map bin index to X coordinate
        total_width = x1 - x0
        bin_pixel_width = total_width / n_bins

        for i, ((b_start, b_end), cnt) in enumerate(zip(bins, counts)):
            if cnt == 0:
                continue

            # Bin rectangle coordinates
            x_left = x0 + i * bin_pixel_width
            x_right = x_left + bin_pixel_width * 0.9  # small gap between bars

            height_ratio = cnt / max_count
            y_top = y1 - height_ratio * (y1 - y0)

            self.create_rectangle(
                x_left,
                y_top,
                x_right,
                y1,
                fill=self.BAR_COLOR,
                outline=self.AXIS_COLOR,
                width=1,
            )

    # -------------------------- Target / Mean -------------------------- #

    def _draw_vertical_lines(
        self,
        x0,
        y0,
        x1,
        y1,
        bins,
    ):
        if not bins:
            return

        v_min = bins[0][0]
        v_max = bins[-1][1]
        span = v_max - v_min if v_max != v_min else 1.0

        def value_to_x(value):
            t = (value - v_min) / span
            return x0 + t * (x1 - x0)

        # Target
        if self._target is not None:
            x = value_to_x(self._target)
            self.create_line(
                x, y0, x, y1,
                fill=self.TARGET_COLOR,
                width=2,
            )
            self.create_text(
                x,
                y0 - 5,
                text="Target",
                anchor="s",
                font=self.FONT_LABEL,
                fill=self.TARGET_COLOR,
            )

        # Mean
        if self._mean is not None:
            x = value_to_x(self._mean)
            self.create_line(
                x, y0, x, y1,
                fill=self.MEAN_COLOR,
                width=2,
            )
            self.create_text(
                x,
                y0 - 5,
                text="Mean",
                anchor="s",
                font=self.FONT_LABEL,
                fill=self.MEAN_COLOR,
            )

    # --------------------------- Labels / title ------------------------ #

    def _draw_y_labels(self, x0, y0, y1, max_count):
        steps = 4
        for i in range(0, steps + 1):
            value = int(round(max_count * i / steps))
            t = i / steps
            y = y1 - t * (y1 - y0)

            self.create_line(
                x0 - 4,
                y,
                x0,
                y,
                fill=self.AXIS_COLOR,
                width=1,
            )

            self.create_text(
                x0 - 6,
                y,
                text=str(value),
                anchor="e",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        # Y axis label (simple vertical text using newlines)
        if self._y_label:
            vertical = "\n".join(list(self._y_label))
            self.create_text(
                x0 - 35,
                (y0 + y1) / 2.0,
                text=vertical,
                anchor="center",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

    def _draw_x_labels(self, x0, y0, x1, y1, bins):
        n_bins = len(bins)
        if n_bins == 0:
            return

        total_width = x1 - x0
        bin_pixel_width = total_width / n_bins

        # Label each bin with its center value (rounded)
        for i, (b_start, b_end) in enumerate(bins):
            center = (b_start + b_end) / 2.0
            x = x0 + (i + 0.5) * bin_pixel_width
            self.create_text(
                x,
                y1 + 10,
                text=f"{center:.2f}",
                anchor="n",
                font=self.FONT_LABEL,
                fill=self.AXIS_COLOR,
            )

        # X axis caption
        if self._x_label:
            self.create_text(
                (x0 + x1) / 2.0,
                y1 + 26,
                text=self._x_label,
                anchor="n",
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
            y1 + 42,
            text=self._bottom_text,
            anchor="e",
            font=self.FONT_LABEL,
            fill="#444444",
        )
