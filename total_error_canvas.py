# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk


class TotalErrorCanvas(tk.Canvas):
    """
    Simple TE / TEa dashboard widget.

    Shows:
        - horizontal axis from 0 to a computed max (%)
        - vertical marker for TEa (Total Allowable Error)
        - colored marker for TE (Total Error) at its position
        - text summary with Bias, CV, TE, TEa, z-score, n, dates.

    This is not a generic plotting library. It is intentionally focused on
    QC Total Error visualization for a *single* batch.
    """

    LEFT_MARGIN   = 80
    RIGHT_MARGIN  = 20
    TOP_MARGIN    = 32
    BOTTOM_MARGIN = 40

    AXIS_COLOR     = "#000000"
    GRID_COLOR     = "#dddddd"
    TEA_COLOR      = "#0000aa"   # blue
    TE_OK_COLOR    = "#00aa00"   # green
    TE_WARN_COLOR  = "#ffcc00"   # yellow
    TE_FAIL_COLOR  = "#ff0000"   # red
    BAR_OK_FILL    = "#ddffdd"
    BAR_FAIL_FILL  = "#ffdddd"

    FONT_LABEL   = ("TkDefaultFont", 9)
    FONT_TITLE   = ("TkDefaultFont", 10, "bold")
    FONT_SUMMARY = ("TkDefaultFont", 8)

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(parent, **kwargs)

        self._title = ""
        self._unit = ""
        self._te = 0.0
        self._tea = 0.0
        self._bias = 0.0
        self._cv = 0.0
        self._z = 0.0
        self._n_series = 0
        self._n_results = 0
        self._date_from = None
        self._date_to = None

        self.bind("<Configure>", self._on_resize)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def draw_tea(
        self,
        *,
        title,
        te,
        tea,
        bias,
        cv,
        z_score,
        n_series,
        n_results,
        unit = "",
        date_from=None,
        date_to=None,
    ):
        """Draw Total Error dashboard for a single batch."""
        self._title = title
        self._unit = unit or ""
        self._te = float(te)
        self._tea = float(tea)
        self._bias = float(bias)
        self._cv = float(cv)
        self._z = float(z_score)
        self._n_series = int(n_series)
        self._n_results = int(n_results)
        self._date_from = date_from
        self._date_to = date_to
        self._redraw()

    def clear(self):
        self.delete("all")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #
    def _on_resize(self, event):
        if self._tea or self._te:
            self._redraw()

    def _redraw(self):
        self.delete("all")

        width = self.winfo_width()
        height = self.winfo_height()

        if width < 10 or height < 10:
            return

        if self._tea <= 0.0 and self._te <= 0.0:
            self._draw_no_data()
            return

        x0 = self.LEFT_MARGIN
        x1 = width - self.RIGHT_MARGIN
        y_axis = height // 2

        # Horizontal scale
        max_val = max(self._tea * 1.2, self._te * 1.2, 5.0)
        if max_val <= 0:
            max_val = 5.0

        def value_to_x(v):
            if max_val == 0:
                return (x0 + x1) / 2.0
            t = max(0.0, min(v / max_val, 1.0))
            return x0 + t * (x1 - x0)

        # Background zones: OK (0..TEa) and FAIL (TEa..max)
        x_tea = value_to_x(self._tea)

        self.create_rectangle(
            x0,
            y_axis - 8,
            max(x_tea, x0),
            y_axis + 8,
            fill=self.BAR_OK_FILL,
            outline="",
        )
        self.create_rectangle(
            max(x_tea, x0),
            y_axis - 8,
            x1,
            y_axis + 8,
            fill=self.BAR_FAIL_FILL,
            outline="",
        )

        # Axis line
        self.create_line(x0, y_axis, x1, y_axis, fill=self.AXIS_COLOR, width=1)

        # TEa marker
        self.create_line(
            x_tea,
            y_axis - 12,
            x_tea,
            y_axis + 12,
            fill=self.TEA_COLOR,
            width=2,
        )
        self.create_text(
            x_tea,
            y_axis - 16,
            text=f"TEa {self._tea:.1f}%",
            anchor="s",
            font=self.FONT_LABEL,
            fill=self.TEA_COLOR,
        )

        # TE marker (color in base al rapporto TE/TEa)
        x_te = value_to_x(self._te)
        ratio = self._te / self._tea if self._tea > 0 else 0.0
        if ratio < 0.8:
            te_color = self.TE_OK_COLOR
        elif ratio < 1.0:
            te_color = self.TE_WARN_COLOR
        else:
            te_color = self.TE_FAIL_COLOR

        r = 5
        self.create_oval(
            x_te - r,
            y_axis - r,
            x_te + r,
            y_axis + r,
            fill=te_color,
            outline="#000000",
            width=1,
        )
        self.create_text(
            x_te,
            y_axis + 18,
            text=f"TE {self._te:.1f}%",
            anchor="n",
            font=self.FONT_LABEL,
            fill=te_color,
        )

        # Axis ticks (0, TEa, max)
        for val, label in (
            (0.0, "0%"),
            (self._tea, f"{self._tea:.1f}%"),
            (max_val, f"{max_val:.1f}%"),
        ):
            xv = value_to_x(val)
            self.create_line(
                xv,
                y_axis + 8,
                xv,
                y_axis + 12,
                fill=self.AXIS_COLOR,
                width=1,
            )
            self.create_text(
                xv,
                y_axis + 16,
                text=label,
                anchor="n",
                font=self.FONT_SUMMARY,
                fill=self.AXIS_COLOR,
            )

        # Title
        if self._title:
            self.create_text(
                (x0 + x1) / 2.0,
                self.TOP_MARGIN / 2.0,
                text=self._title,
                anchor="center",
                font=self.FONT_TITLE,
                fill=self.AXIS_COLOR,
            )

        # Summary line
        summary_parts = [
            f"Bias {self._bias:.1f}%",
            f"CV {self._cv:.1f}%",
            f"TE {self._te:.1f}%",
            f"TEa {self._tea:.1f}%",
            f"z = {self._z:.2f}",
            f"n = {self._n_series}",
        ]

        if self._n_results and self._n_results != self._n_series:
            summary_parts[-1] = f"n = {self._n_series} on {self._n_results} results"

        if self._unit:
            summary_parts.append(self._unit)

        if self._date_from and self._date_to:
            summary_parts.append(f"{self._date_from} \u2192 {self._date_to}")

        summary = "   ·   ".join(summary_parts)

        self.create_text(
            (x0 + x1) / 2.0,
            self.winfo_height() - self.BOTTOM_MARGIN / 2.0,
            text=summary,
            anchor="center",
            font=self.FONT_SUMMARY,
            fill="#333333",
        )

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
