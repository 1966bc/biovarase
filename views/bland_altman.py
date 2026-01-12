# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   January 2026
# -----------------------------------------------------------------------------
"""
Bland-Altman plot for comparing measurements between two workstations.

Implements the Bland-Altman method for assessing agreement between two
measurement methods/instruments on the same samples.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import statistics

from i18n import _
from views.parent_view import ParentView


class UI(ParentView):
    """
    Bland-Altman comparison view.

    Allows selecting a test, level, and two workstations to compare.
    Displays the Bland-Altman plot and statistics.
    """

    def __init__(self, parent):
        super().__init__(parent, name="bland_altman")

        if self._reusing:
            return

        # Data structures
        self.dict_categories = {}
        self.dict_tests = {}
        self.dict_levels = {}
        self.dict_workstations_1 = {}
        self.dict_workstations_2 = {}
        self.pairs = []  # List of (mean, diff) tuples

        # Statistics
        self.bias = 0.0
        self.sd_diff = 0.0
        self.upper_limit = 0.0
        self.lower_limit = 0.0

        self._build_ui()
        self.minsize(900, 600)
        self.show()

    def _build_ui(self):
        """Build the UI layout."""
        # Main container
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: controls
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame", padding=8)
        frm_left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        # Category
        ttk.Label(frm_left, text=_("Category:")).pack(anchor=tk.W, pady=(0, 2))
        self.cbCategory = ttk.Combobox(frm_left, state="readonly", width=25)
        self.cbCategory.bind("<<ComboboxSelected>>", self._on_category_selected)
        self.cbCategory.pack(fill=tk.X, pady=(0, 8))

        # Test
        ttk.Label(frm_left, text=_("Test:")).pack(anchor=tk.W, pady=(0, 2))
        self.cbTest = ttk.Combobox(frm_left, state="readonly", width=25)
        self.cbTest.bind("<<ComboboxSelected>>", self._on_test_selected)
        self.cbTest.pack(fill=tk.X, pady=(0, 8))

        # Level
        ttk.Label(frm_left, text=_("Level:")).pack(anchor=tk.W, pady=(0, 2))
        self.cbLevel = ttk.Combobox(frm_left, state="readonly", width=25)
        self.cbLevel.bind("<<ComboboxSelected>>", self._on_level_selected)
        self.cbLevel.pack(fill=tk.X, pady=(0, 8))

        # Separator
        ttk.Separator(frm_left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Workstation 1
        ttk.Label(frm_left, text=_("Workstation 1:")).pack(anchor=tk.W, pady=(0, 2))
        self.cbWorkstation1 = ttk.Combobox(frm_left, state="readonly", width=25)
        self.cbWorkstation1.bind("<<ComboboxSelected>>", self._on_workstation_changed)
        self.cbWorkstation1.pack(fill=tk.X, pady=(0, 8))

        # Workstation 2
        ttk.Label(frm_left, text=_("Workstation 2:")).pack(anchor=tk.W, pady=(0, 2))
        self.cbWorkstation2 = ttk.Combobox(frm_left, state="readonly", width=25)
        self.cbWorkstation2.bind("<<ComboboxSelected>>", self._on_workstation_changed)
        self.cbWorkstation2.pack(fill=tk.X, pady=(0, 8))

        # Calculate button
        ttk.Button(
            frm_left,
            text=_("Calculate"),
            command=self._on_calculate
        ).pack(fill=tk.X, pady=(8, 4))

        # Clear button
        ttk.Button(
            frm_left,
            text=_("Clear"),
            command=self._on_clear
        ).pack(fill=tk.X, pady=4)

        # Separator
        ttk.Separator(frm_left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Statistics frame
        frm_stats = ttk.LabelFrame(frm_left, text=_("Statistics"), padding=8)
        frm_stats.pack(fill=tk.X, pady=(0, 8))

        # Pairs count
        ttk.Label(frm_stats, text=_("Pairs:")).grid(row=0, column=0, sticky=tk.W)
        self.lblPairs = ttk.Label(frm_stats, text="-")
        self.lblPairs.grid(row=0, column=1, sticky=tk.E, padx=(8, 0))

        # Bias
        ttk.Label(frm_stats, text=_("Bias:")).grid(row=1, column=0, sticky=tk.W)
        self.lblBias = ttk.Label(frm_stats, text="-")
        self.lblBias.grid(row=1, column=1, sticky=tk.E, padx=(8, 0))

        # SD of differences
        ttk.Label(frm_stats, text=_("SD:")).grid(row=2, column=0, sticky=tk.W)
        self.lblSD = ttk.Label(frm_stats, text="-")
        self.lblSD.grid(row=2, column=1, sticky=tk.E, padx=(8, 0))

        # Upper limit
        ttk.Label(frm_stats, text=_("+1.96 SD:")).grid(row=3, column=0, sticky=tk.W)
        self.lblUpper = ttk.Label(frm_stats, text="-")
        self.lblUpper.grid(row=3, column=1, sticky=tk.E, padx=(8, 0))

        # Lower limit
        ttk.Label(frm_stats, text=_("-1.96 SD:")).grid(row=4, column=0, sticky=tk.W)
        self.lblLower = ttk.Label(frm_stats, text="-")
        self.lblLower.grid(row=4, column=1, sticky=tk.E, padx=(8, 0))

        frm_stats.columnconfigure(1, weight=1)

        # Cancel button at bottom
        ttk.Button(
            frm_left,
            text=_("Cancel"),
            command=self.on_cancel
        ).pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

        # Right panel: canvas
        frm_right = ttk.Frame(frm_main, style="App.TFrame")
        frm_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Title label
        self.lblTitle = ttk.Label(
            frm_right,
            text=_("Bland-Altman Plot"),
            font=("TkDefaultFont", 12, "bold")
        )
        self.lblTitle.pack(pady=(0, 8))

        # Canvas for plot
        self.canvas = tk.Canvas(
            frm_right,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def on_open(self, preselect=None):
        """Initialize view data.

        Args:
            preselect: Optional dict with keys:
                - test_id: int
                - level: str
                - ws1_id: int
                - ws2_id: int
        """
        self.title(_("Bland-Altman Comparison"))
        self.attributes("-topmost", True)
        self._load_categories()

        # If preselect data provided, auto-select and calculate
        if preselect:
            self.after(100, lambda: self._apply_preselection(preselect))

    def _apply_preselection(self, preselect):
        """Apply preselection from scanner."""
        test_id = preselect.get("test_id")
        level = preselect.get("level")
        ws1_id = preselect.get("ws1_id")
        ws2_id = preselect.get("ws2_id")

        if not all([test_id, level, ws1_id, ws2_id]):
            return

        # Find category for this test
        sql = """
            SELECT DISTINCT c.category_id
            FROM categories c
            JOIN test_methods tm ON tm.category_id = c.category_id
            WHERE tm.test_id = ?
              AND c.org_id = ?
            LIMIT 1
        """
        row = self.engine.read(False, sql, (test_id, self.engine.get_lab_id()))
        if not row:
            return

        category_id = row["category_id"]

        # Select category
        for idx, cat_id in self.dict_categories.items():
            if cat_id == category_id:
                self.cbCategory.current(idx)
                self._load_tests(category_id)
                break
        else:
            return

        # Select test
        for idx, t_id in self.dict_tests.items():
            if t_id == test_id:
                self.cbTest.current(idx)
                self._load_levels(test_id)
                break
        else:
            return

        # Select level
        for idx, lv in self.dict_levels.items():
            if lv == level:
                self.cbLevel.current(idx)
                self._load_workstations(test_id, level)
                break
        else:
            return

        # Select workstation 1
        for idx, w_id in self.dict_workstations_1.items():
            if w_id == ws1_id:
                self.cbWorkstation1.current(idx)
                break

        # Select workstation 2
        for idx, w_id in self.dict_workstations_2.items():
            if w_id == ws2_id:
                self.cbWorkstation2.current(idx)
                break

        # Auto-calculate after short delay
        self.after(100, self._on_calculate)

    def _load_categories(self):
        """Load categories for current lab."""
        self.dict_categories.clear()
        self.cbCategory.set("")
        self.cbCategory["values"] = []

        lab_org_id = self.engine.get_lab_id()

        sql = """
            SELECT DISTINCT c.category_id, c.description
            FROM categories c
            JOIN test_methods tm ON tm.category_id = c.category_id
            WHERE c.org_id = ?
              AND c.status = 1
              AND tm.status = 1
            ORDER BY c.description
        """
        rows = self.engine.read(True, sql, (lab_org_id,)) or []

        values = []
        for idx, row in enumerate(rows):
            self.dict_categories[idx] = row["category_id"]
            values.append(row["description"])

        self.cbCategory["values"] = values

    def _on_category_selected(self, _evt=None):
        """Handle category selection."""
        self._clear_tests()
        self._clear_levels()
        self._clear_workstations()
        self._clear_plot()

        if self.cbCategory.current() < 0:
            return

        category_id = self.dict_categories.get(self.cbCategory.current())
        if category_id is None:
            return

        self._load_tests(category_id)

    def _load_tests(self, category_id):
        """Load tests for selected category."""
        self.dict_tests.clear()

        sql = """
            SELECT DISTINCT t.test_id, t.description
            FROM tests t
            JOIN test_methods tm ON tm.test_id = t.test_id
            WHERE tm.category_id = ?
              AND t.status = 1
              AND tm.status = 1
            ORDER BY t.description
        """
        rows = self.engine.read(True, sql, (category_id,)) or []

        values = []
        for idx, row in enumerate(rows):
            self.dict_tests[idx] = row["test_id"]
            values.append(row["description"])

        self.cbTest["values"] = values

    def _on_test_selected(self, _evt=None):
        """Handle test selection."""
        self._clear_levels()
        self._clear_workstations()
        self._clear_plot()

        if self.cbTest.current() < 0:
            return

        test_id = self.dict_tests.get(self.cbTest.current())
        if test_id is None:
            return

        self._load_levels(test_id)

    def _load_levels(self, test_id):
        """Load distinct levels (batch descriptions) for selected test."""
        self.dict_levels.clear()

        # Get distinct levels from batches for this test
        sql = """
            SELECT DISTINCT b.description AS level
            FROM batches b
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            WHERE tm.test_id = ?
              AND b.status = 1
              AND b.description IS NOT NULL
              AND b.description != ''
            ORDER BY b.description
        """
        rows = self.engine.read(True, sql, (test_id,)) or []

        values = []
        for idx, row in enumerate(rows):
            self.dict_levels[idx] = row["level"]
            values.append(row["level"])

        self.cbLevel["values"] = values

    def _on_level_selected(self, _evt=None):
        """Handle level selection."""
        self._clear_workstations()
        self._clear_plot()

        if self.cbLevel.current() < 0:
            return

        test_id = self.dict_tests.get(self.cbTest.current())
        level = self.dict_levels.get(self.cbLevel.current())
        if test_id is None or level is None:
            return

        self._load_workstations(test_id, level)

    def _load_workstations(self, test_id, level):
        """Load workstations that have results for this test/level."""
        self.dict_workstations_1.clear()
        self.dict_workstations_2.clear()

        # Get workstations with results for this test and level
        sql = """
            SELECT DISTINCT w.workstation_id, w.description
            FROM workstations w
            JOIN batches b ON b.workstation_id = w.workstation_id
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            JOIN results r ON r.batch_id = b.batch_id
            JOIN equipments e ON e.equipment_id = w.equipment_id
            WHERE tm.test_id = ?
              AND b.description = ?
              AND w.status = 1
              AND e.status = 1
            ORDER BY w.description
        """
        rows = self.engine.read(True, sql, (test_id, level)) or []

        values = []
        for idx, row in enumerate(rows):
            self.dict_workstations_1[idx] = row["workstation_id"]
            self.dict_workstations_2[idx] = row["workstation_id"]
            values.append(row["description"])

        self.cbWorkstation1["values"] = values
        self.cbWorkstation2["values"] = values

    def _on_workstation_changed(self, _evt=None):
        """Handle workstation selection change."""
        self._clear_plot()

    def _clear_tests(self):
        """Clear tests combo."""
        self.dict_tests.clear()
        self.cbTest.set("")
        self.cbTest["values"] = []

    def _clear_levels(self):
        """Clear levels combo."""
        self.dict_levels.clear()
        self.cbLevel.set("")
        self.cbLevel["values"] = []

    def _clear_workstations(self):
        """Clear workstation combos."""
        self.dict_workstations_1.clear()
        self.dict_workstations_2.clear()
        self.cbWorkstation1.set("")
        self.cbWorkstation1["values"] = []
        self.cbWorkstation2.set("")
        self.cbWorkstation2["values"] = []

    def _clear_plot(self):
        """Clear the canvas and statistics."""
        self.canvas.delete("all")
        self.pairs.clear()
        self.lblPairs.config(text="-")
        self.lblBias.config(text="-")
        self.lblSD.config(text="-")
        self.lblUpper.config(text="-")
        self.lblLower.config(text="-")

    def _on_clear(self, _evt=None):
        """Clear all selections."""
        self.cbCategory.set("")
        self._clear_tests()
        self._clear_levels()
        self._clear_workstations()
        self._clear_plot()

    def _on_calculate(self, _evt=None):
        """Calculate and display Bland-Altman plot."""
        # Validate selections
        if self.cbWorkstation1.current() < 0 or self.cbWorkstation2.current() < 0:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select two workstations."),
                parent=self
            )
            return

        ws1_id = self.dict_workstations_1.get(self.cbWorkstation1.current())
        ws2_id = self.dict_workstations_2.get(self.cbWorkstation2.current())

        if ws1_id == ws2_id:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select two different workstations."),
                parent=self
            )
            return

        test_id = self.dict_tests.get(self.cbTest.current())
        level = self.dict_levels.get(self.cbLevel.current())

        if test_id is None or level is None:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select test and level."),
                parent=self
            )
            return

        # Get paired results by date
        self._load_paired_results(test_id, level, ws1_id, ws2_id)

        if len(self.pairs) < 10:
            messagebox.showwarning(
                self.engine.app_title,
                _("Not enough paired data. Minimum 10 pairs required.") +
                f"\n{_('Found')}: {len(self.pairs)}",
                parent=self
            )
            return

        # Calculate statistics
        self._calculate_statistics()

        # Update labels
        self._update_statistics_labels()

        # Draw plot
        self._draw_plot()

    def _load_paired_results(self, test_id, level, ws1_id, ws2_id):
        """Load results paired by date from two workstations."""
        self.pairs.clear()

        # Query to get paired results by date
        sql = """
            SELECT
                DATE(r1.received) AS result_date,
                r1.result AS result1,
                r2.result AS result2
            FROM results r1
            JOIN batches b1 ON b1.batch_id = r1.batch_id
            JOIN test_methods tm1 ON tm1.test_method_id = b1.test_method_id
            JOIN results r2 ON DATE(r2.received) = DATE(r1.received)
            JOIN batches b2 ON b2.batch_id = r2.batch_id
            JOIN test_methods tm2 ON tm2.test_method_id = b2.test_method_id
            WHERE tm1.test_id = ?
              AND tm2.test_id = ?
              AND b1.description = ?
              AND b2.description = ?
              AND r1.workstation_id = ?
              AND r2.workstation_id = ?
            ORDER BY result_date
        """
        rows = self.engine.read(
            True, sql,
            (test_id, test_id, level, level, ws1_id, ws2_id)
        ) or []

        for row in rows:
            r1 = float(row["result1"])
            r2 = float(row["result2"])
            mean = (r1 + r2) / 2.0
            diff = r1 - r2
            self.pairs.append((mean, diff))

    def _calculate_statistics(self):
        """Calculate Bland-Altman statistics."""
        if not self.pairs:
            return

        differences = [p[1] for p in self.pairs]

        self.bias = statistics.mean(differences)

        if len(differences) > 1:
            self.sd_diff = statistics.stdev(differences)
        else:
            self.sd_diff = 0.0

        self.upper_limit = self.bias + 1.96 * self.sd_diff
        self.lower_limit = self.bias - 1.96 * self.sd_diff

    def _update_statistics_labels(self):
        """Update statistics labels."""
        self.lblPairs.config(text=str(len(self.pairs)))
        self.lblBias.config(text=f"{self.bias:.2f}")
        self.lblSD.config(text=f"{self.sd_diff:.2f}")
        self.lblUpper.config(text=f"{self.upper_limit:.2f}")
        self.lblLower.config(text=f"{self.lower_limit:.2f}")

    def _on_canvas_resize(self, _evt=None):
        """Redraw plot on canvas resize."""
        if self.pairs:
            self._draw_plot()

    def _draw_plot(self):
        """Draw the Bland-Altman plot on the canvas."""
        self.canvas.delete("all")

        if not self.pairs:
            return

        # Canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        # Margins
        margin_left = 60
        margin_right = 20
        margin_top = 40
        margin_bottom = 50

        plot_width = width - margin_left - margin_right
        plot_height = height - margin_top - margin_bottom

        if plot_width < 50 or plot_height < 50:
            return

        # Data ranges
        means = [p[0] for p in self.pairs]
        diffs = [p[1] for p in self.pairs]

        min_mean = min(means)
        max_mean = max(means)
        mean_range = max_mean - min_mean
        if mean_range == 0:
            mean_range = 1

        # Expand diff range to include limits
        min_diff = min(min(diffs), self.lower_limit)
        max_diff = max(max(diffs), self.upper_limit)
        diff_range = max_diff - min_diff
        if diff_range == 0:
            diff_range = 1

        # Add padding to ranges
        mean_padding = mean_range * 0.1
        diff_padding = diff_range * 0.1
        min_mean -= mean_padding
        max_mean += mean_padding
        min_diff -= diff_padding
        max_diff += diff_padding
        mean_range = max_mean - min_mean
        diff_range = max_diff - min_diff

        def to_canvas_x(val):
            return margin_left + (val - min_mean) / mean_range * plot_width

        def to_canvas_y(val):
            return margin_top + (max_diff - val) / diff_range * plot_height

        # Draw axes
        # X axis
        self.canvas.create_line(
            margin_left, height - margin_bottom,
            width - margin_right, height - margin_bottom,
            fill="black", width=1
        )
        # Y axis
        self.canvas.create_line(
            margin_left, margin_top,
            margin_left, height - margin_bottom,
            fill="black", width=1
        )

        # X axis label
        self.canvas.create_text(
            width / 2, height - 10,
            text=_("Mean of measurements"),
            font=("TkDefaultFont", 9)
        )

        # Y axis label
        self.canvas.create_text(
            15, height / 2,
            text=_("Difference"),
            font=("TkDefaultFont", 9),
            angle=90
        )

        # Draw horizontal lines for limits
        # Bias line (mean of differences)
        y_bias = to_canvas_y(self.bias)
        self.canvas.create_line(
            margin_left, y_bias,
            width - margin_right, y_bias,
            fill="blue", width=2, dash=(4, 4)
        )
        self.canvas.create_text(
            width - margin_right + 5, y_bias,
            text=f"Bias: {self.bias:.2f}",
            anchor=tk.W, fill="blue", font=("TkDefaultFont", 8)
        )

        # Upper limit (+1.96 SD)
        y_upper = to_canvas_y(self.upper_limit)
        self.canvas.create_line(
            margin_left, y_upper,
            width - margin_right, y_upper,
            fill="red", width=1, dash=(2, 2)
        )
        self.canvas.create_text(
            margin_left - 5, y_upper,
            text=f"+1.96SD: {self.upper_limit:.2f}",
            anchor=tk.E, fill="red", font=("TkDefaultFont", 8)
        )

        # Lower limit (-1.96 SD)
        y_lower = to_canvas_y(self.lower_limit)
        self.canvas.create_line(
            margin_left, y_lower,
            width - margin_right, y_lower,
            fill="red", width=1, dash=(2, 2)
        )
        self.canvas.create_text(
            margin_left - 5, y_lower,
            text=f"-1.96SD: {self.lower_limit:.2f}",
            anchor=tk.E, fill="red", font=("TkDefaultFont", 8)
        )

        # Zero line if visible
        if min_diff <= 0 <= max_diff:
            y_zero = to_canvas_y(0)
            self.canvas.create_line(
                margin_left, y_zero,
                width - margin_right, y_zero,
                fill="gray", width=1
            )

        # Draw data points
        point_radius = 4
        for mean_val, diff_val in self.pairs:
            x = to_canvas_x(mean_val)
            y = to_canvas_y(diff_val)
            self.canvas.create_oval(
                x - point_radius, y - point_radius,
                x + point_radius, y + point_radius,
                fill="darkblue", outline="navy"
            )

        # Title with workstation names
        ws1_name = self.cbWorkstation1.get()
        ws2_name = self.cbWorkstation2.get()
        title = f"{ws1_name} vs {ws2_name}"
        self.canvas.create_text(
            width / 2, 15,
            text=title,
            font=("TkDefaultFont", 11, "bold")
        )

        # Draw tick marks and labels on axes
        # X axis ticks
        num_x_ticks = 5
        for i in range(num_x_ticks + 1):
            val = min_mean + (mean_range * i / num_x_ticks)
            x = to_canvas_x(val)
            self.canvas.create_line(
                x, height - margin_bottom,
                x, height - margin_bottom + 5,
                fill="black"
            )
            self.canvas.create_text(
                x, height - margin_bottom + 15,
                text=f"{val:.1f}",
                font=("TkDefaultFont", 8)
            )

        # Y axis ticks
        num_y_ticks = 5
        for i in range(num_y_ticks + 1):
            val = min_diff + (diff_range * i / num_y_ticks)
            y = to_canvas_y(val)
            self.canvas.create_line(
                margin_left - 5, y,
                margin_left, y,
                fill="black"
            )
            self.canvas.create_text(
                margin_left - 25, y,
                text=f"{val:.1f}",
                font=("TkDefaultFont", 8)
            )

    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
