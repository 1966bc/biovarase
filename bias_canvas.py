#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# module:   bias_canvas
# purpose:  Simple bias chart (target vs mean) using Tkinter Canvas
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   ver MMXXV
# -----------------------------------------------------------------------------

import tkinter as tk
from typing import Iterable, Optional, Any


class BiasCanvas(tk.Canvas):
    """
    Simple horizontal chart showing target vs mean.

    X axis: value in analytical units
    - blue line: target
    - colored line: mean
    - colored band between target and mean

    This widget is designed as a lightweight replacement for the
    frequency histogram when the main question is the bias.
    """

    LEFT_MARGIN   = 60
    RIGHT_MARGIN  = 6
    TOP_MARGIN    = 30
    BOTTOM_MARGIN = 50

    AXIS_COLOR      = "#000000"
    TARGET_COLOR    = "#0000aa"   # blue
    MEAN_COLOR      = "#006400"   # dark green (fixed, like LJ chart)
    BAND_FILL       = "#eeeeff"

    FONT_LABEL   = ("TkDefaultFont", 9)
    FONT_TITLE   = ("TkDefaultFont", 10, "bold")
    FONT_SUMMARY = ("TkDefaultFont", 8)

    def __init__(self, parent: tk.Widget, **kwargs: Any) -> None:
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self._title: Optional[str] = None
        self._unit: str = ""
        self._target: float = 0.0
        self._mean: float = 0.0
        self._bias_pct: float = 0.0
        self._bias_abs: float = 0.0

        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def draw_bias(
        self,
        series: Iterable[float],
        target: float,
        *,
        title: Optional[str] = None,
        unit: str = "",
    ) -> None:
        """
        Draw bias chart for the given series and target.

        Args:
            series: iterable of numeric QC results.
            target: target value of the control.
            title:  optional chart title (e.g. "Control L1").
            unit:   unit of measure to show near axis and in summary.
        """
        values = [float(v) for v in series]
        if not values:
            self.clear()
            self._draw_no_data()
            return

        self._target = float(target)
        self._mean = sum(values) / len(values)
        self._title = title
        self._unit = unit or ""

        if self._target != 0:
            self._bias_pct = (self._mean - self._target) / self._target * 100.0
        else:
            self._bias_pct = 0.0
        self._bias_abs = self._mean - self._target

        self._values = values
        self._redraw()

    def clear(self) -> None:
        """Clear the canvas and reset stored data."""
        self.delete("all")
        self._title = None
        self._unit = ""
        self._target = 0.0
        self._mean = 0.0
        self._bias_pct = 0.0
        self._bias_abs = 0.0
        self._values = []

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #
    def _on_resize(self, event: tk.Event) -> None:
        if getattr(self, "_values", None):
            self._redraw()

    def _redraw(self) -> None:
        self.delete("all")

        if not getattr(self, "_values", None):
            self._draw_no_data()
            return

        width = self.winfo_width()
        height = self.winfo_height()
        if width < 10 or height < 10:
            return

        x0 = self.LEFT_MARGIN
        x1 = width - self.RIGHT_MARGIN
        axis_y = (height - self.BOTTOM_MARGIN) // 2 + self.TOP_MARGIN // 2

        # Determine X axis limits (include values, target and mean)
        vals = list(self._values) + [self._target, self._mean]
        v_min = min(vals)
        v_max = max(vals)
        span = v_max - v_min if v_max != v_min else 1.0
        margin = span * 0.10
        v_min -= margin
        v_max += margin

        def value_to_x(v: float) -> float:
            t = (v - v_min) / (v_max - v_min) if v_max != v_min else 0.5
            t = max(0.0, min(1.0, t))
            return x0 + t * (x1 - x0)

        # Background band between target and mean
        xt = value_to_x(self._target)
        xm = value_to_x(self._mean)
        band_left = min(xt, xm)
        band_right = max(xt, xm)
        self.create_rectangle(
            band_left,
            axis_y - 6,
            band_right,
            axis_y + 6,
            fill=self.BAND_FILL,
            outline="",
        )

        # Axis line
        self.create_line(x0, axis_y, x1, axis_y, fill=self.AXIS_COLOR, width=1)

        # Target arrow (triangle pointing down)
        arrow_size = 6
        self.create_polygon(
            xt, axis_y - 14,                    # bottom vertex (pointing down)
            xt - arrow_size, axis_y - 14 - 10,  # top left
            xt + arrow_size, axis_y - 14 - 10,  # top right
            fill=self.TARGET_COLOR,
            outline=self.TARGET_COLOR,
        )

        # Mean arrow (triangle pointing down) - fixed color
        self.create_polygon(
            xm, axis_y - 14,                    # bottom vertex (pointing down)
            xm - arrow_size, axis_y - 14 - 10,  # top left
            xm + arrow_size, axis_y - 14 - 10,  # top right
            fill=self.MEAN_COLOR,
            outline=self.MEAN_COLOR,
        )

        # Axis ticks for min / max
        for v in (v_min, v_max):
            xv = value_to_x(v)
            self.create_line(
                xv,
                axis_y + 8,
                xv,
                axis_y + 12,
                fill=self.AXIS_COLOR,
                width=1,
            )
            self.create_text(
                xv,
                axis_y + 16,
                text=f"{v:.2f}",
                anchor="n",
                font=self.FONT_SUMMARY,
                fill=self.AXIS_COLOR,
            )

       

        # Summary
        unit_part = f" {self._unit}" if self._unit else ""
        summary = (
            f"Bias {self._bias_pct:+.1f}% ({self._bias_abs:+.2f}{unit_part})"
        )

        self.create_text(
            (x0 + x1) / 2.0,
            height - self.BOTTOM_MARGIN / 2.0,
            text=summary,
            anchor="center",
            font=self.FONT_SUMMARY,
            fill="#333333",
        )

    def _draw_no_data(self) -> None:
        """Draw a faint grid placeholder when no data is available."""
        w = self.winfo_width()
        h = self.winfo_height()

        if w < 10 or h < 10:
            return

        # Numero di divisioni della griglia
        rows = 5
        cols = 5

        # Colore griglia molto leggero
        grid_color = "#d0d0d0"

        # Spaziatura
        dx = w / cols
        dy = h / rows

        # Linee verticali
        for i in range(1, cols):
            x = i * dx
            self.create_line(x, 0, x, h, fill=grid_color)

        # Linee orizzontali
        for i in range(1, rows):
            y = i * dy
            self.create_line(0, y, w, y, fill=grid_color)

