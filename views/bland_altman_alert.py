# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   January 2026
# -----------------------------------------------------------------------------
"""
Bland-Altman Alert - Automatic comparison scanner.

Scans all test/level combinations with results on multiple workstations
and calculates Bland-Altman statistics to detect discrepancies.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import statistics

from i18n import _
from views.parent_view import ParentView
import views.bland_altman


class UI(ParentView):
    """
    Bland-Altman Alert scanner view.

    Automatically scans all test/level combinations and shows
    a summary of comparisons with alert indicators.
    """

    def __init__(self, parent):
        super().__init__(parent, name="bland_altman_alert")

        if self._reusing:
            return

        # Store comparison results
        self.comparisons = []  # List of dicts with comparison data
        self.dict_items = {}   # Map treeview iid to comparison data

        self._build_ui()
        self.minsize(1000, 500)
        self.show()

    def _build_ui(self):
        """Build the UI layout."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Top controls
        frm_top = ttk.Frame(frm_main, style="App.TFrame")
        frm_top.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            frm_top,
            text=_("Scan"),
            command=self._on_scan
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            frm_top,
            text=_("View Plot"),
            command=self._on_view_plot
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Threshold settings
        ttk.Label(frm_top, text=_("Bias threshold:")).pack(side=tk.LEFT, padx=(16, 4))
        self.spnBiasThreshold = ttk.Spinbox(frm_top, from_=1, to=50, width=6)
        self.spnBiasThreshold.set(10)
        self.spnBiasThreshold.pack(side=tk.LEFT)

        ttk.Label(frm_top, text=_("% out threshold:")).pack(side=tk.LEFT, padx=(16, 4))
        self.spnOutThreshold = ttk.Spinbox(frm_top, from_=1, to=50, width=6)
        self.spnOutThreshold.set(5)
        self.spnOutThreshold.pack(side=tk.LEFT)

        # Status label
        self.lblStatus = ttk.Label(frm_top, text="")
        self.lblStatus.pack(side=tk.RIGHT)

        ttk.Button(
            frm_top,
            text=_("Cancel"),
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=(8, 0))

        # Results treeview in LabelFrame (like main.py lstBatches)
        frm_tree = ttk.LabelFrame(frm_main, text=_("Results"))
        frm_tree.pack(fill=tk.BOTH, expand=True)

        cols = ("test", "level", "ws1", "ws2", "pairs", "bias", "sd", "pct_out", "alert")
        self.tree = ttk.Treeview(frm_tree, columns=cols, show="headings")

        self.tree.column("test", width=120, minwidth=100, anchor=tk.W)
        self.tree.heading("test", text=_("Test"), anchor=tk.W)

        self.tree.column("level", width=60, minwidth=50, anchor=tk.W)
        self.tree.heading("level", text=_("Level"), anchor=tk.W)

        self.tree.column("ws1", width=100, minwidth=80, anchor=tk.W)
        self.tree.heading("ws1", text=_("Workstation 1"), anchor=tk.W)

        self.tree.column("ws2", width=100, minwidth=80, anchor=tk.W)
        self.tree.heading("ws2", text=_("Workstation 2"), anchor=tk.W)

        self.tree.column("pairs", width=60, minwidth=50, anchor=tk.CENTER)
        self.tree.heading("pairs", text=_("Pairs"), anchor=tk.CENTER)

        self.tree.column("bias", width=80, minwidth=60, anchor=tk.E)
        self.tree.heading("bias", text=_("Bias"), anchor=tk.E)

        self.tree.column("sd", width=80, minwidth=60, anchor=tk.E)
        self.tree.heading("sd", text=_("SD"), anchor=tk.E)

        self.tree.column("pct_out", width=80, minwidth=60, anchor=tk.E)
        self.tree.heading("pct_out", text=_("% Out"), anchor=tk.E)

        self.tree.column("alert", width=60, minwidth=50, anchor=tk.CENTER)
        self.tree.heading("alert", text=_("Alert"), anchor=tk.CENTER)

        # Scrollbar and layout (pack like main.py)
        sb_y = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Pre-configure tag colors (like main.py)
        self.tree.tag_configure("alert", background="red")
        self.tree.tag_configure("warning", background="yellow")
        self.tree.tag_configure("ok", background="green")
        self.tree.tag_configure("insufficient", background="gray")

        # Bind double-click
        self.tree.bind("<Double-1>", self._on_view_plot)

    def on_open(self):
        """Initialize view."""
        self.title(_("Bland-Altman Alert Scanner"))

    def _on_scan(self, _evt=None):
        """Scan all test/level/workstation combinations."""
        self.tree.delete(*self.tree.get_children())
        self.comparisons.clear()
        self.dict_items.clear()

        self.lblStatus.config(text=_("Scanning..."))
        self.update_idletasks()

        # Get thresholds
        try:
            bias_threshold = float(self.spnBiasThreshold.get())
            out_threshold = float(self.spnOutThreshold.get())
        except ValueError:
            bias_threshold = 10.0
            out_threshold = 5.0

        # Find all test/level combinations with 2+ workstations
        combinations = self._find_combinations()

        count = 0
        alerts = 0

        for combo in combinations:
            test_id = combo["test_id"]
            test_name = combo["test_name"]
            level = combo["level"]
            workstations = combo["workstations"]

            # Compare each pair of workstations
            for i in range(len(workstations)):
                for j in range(i + 1, len(workstations)):
                    ws1 = workstations[i]
                    ws2 = workstations[j]

                    result = self._compare_workstations(
                        test_id, level,
                        ws1["workstation_id"], ws1["description"],
                        ws2["workstation_id"], ws2["description"],
                        bias_threshold, out_threshold
                    )

                    if result:
                        result["test_name"] = test_name
                        result["test_id"] = test_id
                        self.comparisons.append(result)

                        # Add to treeview with pre-configured tag (like main.py)
                        tag = result["tag"]
                        iid = self.tree.insert(
                            "", tk.END,
                            values=(
                                test_name,
                                level,
                                ws1["description"],
                                ws2["description"],
                                result["pairs"],
                                f"{result['bias']:.2f}",
                                f"{result['sd']:.2f}",
                                f"{result['pct_out']:.1f}%",
                                result["alert_text"]
                            ),
                            tags=(tag,)
                        )
                        
                        self.dict_items[iid] = result
                        count += 1

                        if tag == "alert":
                            alerts += 1

        self.lblStatus.config(
            text=f"{_('Comparisons')}: {count} | {_('Alerts')}: {alerts}"
        )

    def _find_combinations(self):
        """Find all test/level combinations with results on 2+ workstations."""
        lab_id = self.engine.get_lab_id()

        sql = """
            SELECT
                t.test_id,
                t.description AS test_name,
                b.description AS level,
                w.workstation_id,
                w.description AS ws_description
            FROM results r
            JOIN batches b ON b.batch_id = r.batch_id
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            JOIN tests t ON t.test_id = tm.test_id
            JOIN workstations w ON w.workstation_id = r.workstation_id
            JOIN sections s ON s.section_id = w.section_id
            JOIN equipments e ON e.equipment_id = w.equipment_id
            WHERE s.lab_id = ?
              AND w.status = 1
              AND e.status = 1
              AND b.description IS NOT NULL
              AND b.description != ''
            GROUP BY t.test_id, b.description, w.workstation_id
            HAVING COUNT(r.result_id) >= 10
            ORDER BY t.description, b.description, w.description
        """

        rows = self.engine.read(True, sql, (lab_id,)) or []

        # Group by test_id + level
        combos = {}
        for row in rows:
            key = (row["test_id"], row["test_name"], row["level"])
            if key not in combos:
                combos[key] = []
            combos[key].append({
                "workstation_id": row["workstation_id"],
                "description": row["ws_description"]
            })

        # Filter only those with 2+ workstations
        result = []
        for (test_id, test_name, level), workstations in combos.items():
            if len(workstations) >= 2:
                result.append({
                    "test_id": test_id,
                    "test_name": test_name,
                    "level": level,
                    "workstations": workstations
                })

        return result

    def _compare_workstations(self, test_id, level, ws1_id, ws1_name, ws2_id, ws2_name,
                               bias_threshold, out_threshold):
        """Compare two workstations and return statistics."""
        # Get paired results by date
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

        if len(rows) < 10:
            return {
                "level": level,
                "ws1_id": ws1_id,
                "ws1_name": ws1_name,
                "ws2_id": ws2_id,
                "ws2_name": ws2_name,
                "pairs": len(rows),
                "bias": 0,
                "sd": 0,
                "pct_out": 0,
                "alert_text": _("Insufficient"),
                "tag": "insufficient"
            }

        # Calculate statistics
        pairs = []
        for row in rows:
            r1 = float(row["result1"])
            r2 = float(row["result2"])
            mean = (r1 + r2) / 2.0
            diff = r1 - r2
            pairs.append((mean, diff))

        differences = [p[1] for p in pairs]
        bias = statistics.mean(differences)
        sd = statistics.stdev(differences) if len(differences) > 1 else 0

        upper = bias + 1.96 * sd
        lower = bias - 1.96 * sd

        # Count points outside limits
        out_count = sum(1 for _, d in pairs if d > upper or d < lower)
        pct_out = (out_count / len(pairs)) * 100 if pairs else 0

        # Determine alert level
        abs_bias = abs(bias)
        if abs_bias > bias_threshold or pct_out > out_threshold:
            alert_text = "ALERT"
            tag = "alert"
        elif abs_bias > bias_threshold * 0.7 or pct_out > out_threshold * 0.7:
            alert_text = "Warning"
            tag = "warning"
        else:
            alert_text = "OK"
            tag = "ok"

        return {
            "level": level,
            "ws1_id": ws1_id,
            "ws1_name": ws1_name,
            "ws2_id": ws2_id,
            "ws2_name": ws2_name,
            "pairs": len(pairs),
            "bias": bias,
            "sd": sd,
            "upper": upper,
            "lower": lower,
            "pct_out": pct_out,
            "alert_text": alert_text,
            "tag": tag
        }

    def _on_view_plot(self, _evt=None):
        """Open detailed Bland-Altman plot for selected comparison."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select a comparison."),
                parent=self
            )
            return

        iid = sel[0]
        data = self.dict_items.get(iid)
        if not data:
            return

        # Prepare preselection data
        preselect = {
            "test_id": data.get("test_id"),
            "level": data.get("level"),
            "ws1_id": data.get("ws1_id"),
            "ws2_id": data.get("ws2_id"),
        }

        # Open Bland-Altman view with pre-selection
        ba_view = views.bland_altman.UI(self.parent)
        ba_view.on_open(preselect=preselect)

    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
