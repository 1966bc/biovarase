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
import threading
from queue import Queue, Empty

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

        # Pre-configure tag colors (foreground works better on GTK/Debian)
        self.tree.tag_configure("alert", foreground="red")
        self.tree.tag_configure("warning", foreground="orange")
        self.tree.tag_configure("insufficient", foreground="gray")

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

        # Create thread-safe queue for results
        self._result_queue = Queue()
        self._scan_count = 0
        self._scan_alerts = 0
        self._displayed = 0

        # Run scan in background thread to avoid UI freeze
        self._scan_thread = threading.Thread(
            target=self._do_scan,
            args=(bias_threshold, out_threshold, self._result_queue),
            daemon=True
        )
        self._scan_thread.start()

        # Process queue periodically (updates UI progressively)
        self._process_result_queue()

    def _process_result_queue(self):
        """Process results from queue and update UI progressively."""
        try:
            # Process all available results without blocking
            while True:
                try:
                    result = self._result_queue.get_nowait()
                except Empty:
                    break

                # None signals scan complete
                if result is None:
                    self.lblStatus.config(
                        text=f"{_('Scanned')}: {self._scan_count} | "
                             f"{_('Displayed')}: {self._displayed} | "
                             f"{_('Alerts')}: {self._scan_alerts}"
                    )
                    return  # Stop polling

                # Update counters
                self._scan_count += 1
                if result["tag"] == "alert":
                    self._scan_alerts += 1

                # Show only alerts and warnings (skip OK and insufficient)
                if result["tag"] in ("alert", "warning"):
                    iid = self.tree.insert(
                        "", tk.END,
                        values=(
                            result["test_name"],
                            result["level"],
                            result["ws1_desc"],
                            result["ws2_desc"],
                            result["pairs"],
                            f"{result['bias']:.2f}",
                            f"{result['sd']:.2f}",
                            f"{result['pct_out']:.1f}%",
                            result["alert_text"]
                        ),
                        tags=(result["tag"],)
                    )
                    self.dict_items[iid] = result
                    self.comparisons.append(result)
                    self._displayed += 1

                # Update status while scanning
                self.lblStatus.config(
                    text=f"{_('Scanning...')} {self._scan_count} | "
                         f"{_('Alerts')}: {self._scan_alerts}"
                )

        except tk.TclError:
            # Window was closed
            return

        # Continue polling queue
        self.after(50, self._process_result_queue)

    def _do_scan(self, bias_threshold, out_threshold, result_queue):
        """Background scan thread - puts results in queue."""
        try:
            # Find all test/level combinations with 2+ workstations
            combinations = self._find_combinations()

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
                            result["ws1_desc"] = ws1["description"]
                            result["ws2_desc"] = ws2["description"]
                            # Put result in queue (thread-safe)
                            result_queue.put(result)
        finally:
            # Signal completion with sentinel
            result_queue.put(None)

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
            JOIN organizations section ON section.org_id = w.org_id
            JOIN equipments e ON e.equipment_id = w.equipment_id
            WHERE section.parent_id = ?
              AND section.org_type = 'section'
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
        # Get results for each workstation separately (faster than self-join)
        sql = """
            SELECT DATE(r.received) AS result_date, r.result
            FROM results r
            JOIN batches b ON b.batch_id = r.batch_id
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            WHERE tm.test_id = ?
              AND b.description = ?
              AND r.workstation_id = ?
            ORDER BY result_date
        """
        rows1 = self.engine.read(True, sql, (test_id, level, ws1_id)) or []
        rows2 = self.engine.read(True, sql, (test_id, level, ws2_id)) or []

        # Group by date and match pairs in Python (much faster)
        data1 = {}
        for row in rows1:
            dt = row["result_date"]
            if dt not in data1:
                data1[dt] = []
            data1[dt].append(float(row["result"]))

        data2 = {}
        for row in rows2:
            dt = row["result_date"]
            if dt not in data2:
                data2[dt] = []
            data2[dt].append(float(row["result"]))

        # Match pairs by date
        rows = []
        for dt in data1:
            if dt in data2:
                # Take first result from each workstation for that date
                for r1 in data1[dt]:
                    for r2 in data2[dt]:
                        rows.append({"result1": r1, "result2": r2})

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
        """Close window and cleanup thread resources."""
        # Clear queue to unblock any waiting thread
        if hasattr(self, '_result_queue'):
            try:
                while not self._result_queue.empty():
                    self._result_queue.get_nowait()
            except Empty:
                pass

        super().on_cancel(evt)
