# -*- coding: utf-8 -*-
"""
QC Report - Generate QC reports for selected tests.

Creates text reports with QC data for documentation purposes.

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
"""
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from i18n import _
from views.parent_view import ParentView
from calendarium import Calendarium


class UI(ParentView):
    """
    QC Report generator window.

    Allows user to:
    - Select a date
    - View validated QC results for that date
    - Select which tests to include
    - Preview and print/save a .txt report
    """

    def __init__(self, parent):
        super().__init__(parent, name="qc_report")
        if self._reusing:
            return

        self.resizable(True, True)
        self.minsize(600, 400)

        # Track selected items
        self.selected_items = set()
        self.dict_items = {}
        self.all_rows = []  # Store all loaded rows for filtering

        self._build_ui()
        self.show()

    def _build_ui(self):
        """Build the UI components."""
        padd = {"padx": 5, "pady": 5}

        # Main container
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        # Top frame - Date selector
        frm_top = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_top.pack(fill=tk.X, **padd)

        bg = self.engine.get_rgb(*getattr(self.engine, "BASE_BG_RGB", (240, 240, 237)))
        self.calendarium = Calendarium(frm_top, _("Date:"), base_bg_color=bg)
        self.calendarium.pack(side=tk.LEFT, **padd)

        btn_load = ttk.Button(
            frm_top,
            text=_("Load"),
            command=self._on_load,
        )
        btn_load.pack(side=tk.LEFT, **padd)

        # Westgard filter
        ttk.Label(frm_top, text=_("Filter:"), style="App.TLabel").pack(side=tk.LEFT, **padd)
        self.filter_var = tk.StringVar(value="all")
        self.cmb_filter = ttk.Combobox(
            frm_top,
            textvariable=self.filter_var,
            values=[_("All"), _("OK"), _("Warning"), _("Violation")],
            state="readonly",
            width=12,
        )
        self.cmb_filter.current(0)
        self.cmb_filter.pack(side=tk.LEFT, **padd)
        self.cmb_filter.bind("<<ComboboxSelected>>", self._on_filter_change)

        # Treeview frame
        frm_tree = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_tree.pack(fill=tk.BOTH, expand=True, **padd)

        # Scrollbars
        sb_vert = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL)
        sb_vert.pack(side=tk.RIGHT, fill=tk.Y)
        sb_horiz = ttk.Scrollbar(frm_tree, orient=tk.HORIZONTAL)
        sb_horiz.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        cols = ("selected", "test", "workstation", "result", "target", "westgard")
        self.tree = ttk.Treeview(
            frm_tree,
            columns=cols,
            show="headings",
            yscrollcommand=sb_vert.set,
            xscrollcommand=sb_horiz.set,
            height=12,
        )
        sb_vert.config(command=self.tree.yview)
        sb_horiz.config(command=self.tree.xview)

        # Column configuration
        self.tree.column("selected", width=40, anchor=tk.CENTER, stretch=False)
        self.tree.column("test", width=150, anchor=tk.W, stretch=True)
        self.tree.column("workstation", width=100, anchor=tk.W, stretch=False)
        self.tree.column("result", width=80, anchor=tk.E, stretch=False)
        self.tree.column("target", width=80, anchor=tk.E, stretch=False)
        self.tree.column("westgard", width=80, anchor=tk.CENTER, stretch=False)

        self.tree.heading("selected", text="")
        self.tree.heading("test", text=_("Test"))
        self.tree.heading("workstation", text=_("Workstation"))
        self.tree.heading("result", text=_("Result"))
        self.tree.heading("target", text=_("Target"))
        self.tree.heading("westgard", text=_("Westgard"))

        # Tags for colors
        self.tree.tag_configure("violation", foreground="red")
        self.tree.tag_configure("warning", foreground="orange")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind click to toggle selection
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # Selection buttons frame
        frm_sel = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_sel.pack(fill=tk.X, **padd)

        btn_select_all = ttk.Button(
            frm_sel,
            text=_("Select All"),
            command=self._on_select_all,
        )
        btn_select_all.pack(side=tk.LEFT, **padd)

        btn_deselect_all = ttk.Button(
            frm_sel,
            text=_("Deselect All"),
            command=self._on_deselect_all,
        )
        btn_deselect_all.pack(side=tk.LEFT, **padd)

        # Bottom buttons frame
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.pack(fill=tk.X, **padd)

        btn_preview = ttk.Button(
            frm_buttons,
            text=_("Preview"),
            command=self._on_preview,
        )
        btn_preview.pack(side=tk.LEFT, **padd)

        btn_cancel = ttk.Button(
            frm_buttons,
            text=_("Cancel"),
            command=self.on_cancel,
        )
        btn_cancel.pack(side=tk.RIGHT, **padd)

    def on_open(self):
        """Called when window is opened."""
        self.title(_("QC Report"))
        self.calendarium.set_today()
        # Subscribe to result changes
        self.engine.subscribe("result_changed", self._on_result_changed)
        self._on_load()

    def _on_result_changed(self, *args):
        """Called when results are validated/changed."""
        # Reload data if window is visible
        if self.winfo_viewable():
            self._on_load()

    def _get_selected_date(self):
        """Get the selected date from Calendarium."""
        try:
            value = self.calendarium.get_date()
        except Exception:
            return None
        if value is False or value is None:
            return None
        return value

    def _on_load(self, evt=None):
        """Load QC results for the selected date."""
        selected_date = self._get_selected_date()
        if selected_date is None:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select a valid date."),
                parent=self,
            )
            return

        # Clear current data
        self.engine.clear_treeview(self.tree)
        self.selected_items.clear()
        self.dict_items.clear()

        # Get lab_id from current context
        lab_id = self.engine.current_ids.get("lab_id")
        if not lab_id:
            messagebox.showwarning(
                self.engine.app_title,
                _("No laboratory selected."),
                parent=self,
            )
            return

        self.engine.busy(self)
        try:
            # Query validated results for this date
            sql = """
                SELECT
                    r.result_id,
                    t.description AS test_name,
                    tm.test_method_id,
                    w.description AS workstation,
                    w.workstation_id,
                    b.batch_id,
                    b.lot_number,
                    b.expiration,
                    b.target,
                    b.sd,
                    b.description AS batch_desc,
                    r.result,
                    r.received,
                    r.validated_by,
                    r.validated_at,
                    u.last_name,
                    u.first_name,
                    un.description AS unit
                FROM results r
                INNER JOIN batches b ON r.batch_id = b.batch_id
                INNER JOIN test_methods tm ON b.test_method_id = tm.test_method_id
                INNER JOIN tests t ON tm.test_id = t.test_id
                INNER JOIN workstations w ON r.workstation_id = w.workstation_id
                LEFT JOIN users u ON r.validated_by = u.user_id
                LEFT JOIN units un ON tm.unit_id = un.unit_id
                WHERE DATE(r.received) = ?
                  AND r.validated = 1
                  AND r.status = 1
                  AND r.is_delete = 0
                  AND b.org_id = ?
                  AND t.status = 1
                  AND tm.status = 1
                ORDER BY t.description, w.description
            """
            rows = self.engine.read(True, sql, (selected_date.isoformat(), lab_id))

            if not rows:
                self.all_rows = []
                messagebox.showinfo(
                    self.engine.app_title,
                    _("No validated results found for this date."),
                    parent=self,
                )
                return

            # Store all rows and apply filter
            self.all_rows = list(rows)
            self._apply_filter()
        finally:
            self.engine.not_busy(self)

    def _on_filter_change(self, evt=None):
        """Handle filter combobox change."""
        self._apply_filter()

    def _apply_filter(self):
        """Apply Westgard filter to the treeview."""
        # Clear current display
        self.engine.clear_treeview(self.tree)
        self.selected_items.clear()
        self.dict_items.clear()

        filter_value = self.cmb_filter.get()

        for row in self.all_rows:
            # Calculate Westgard rule
            westgard = self._get_westgard_for_result(row)

            # Determine category
            if westgard in ("1:3S", "2:2S", "R:4S"):
                category = "violation"
            elif westgard in ("1:2S", "4:1S", "10:X"):
                category = "warning"
            else:
                category = "ok"

            # Apply filter
            if filter_value == _("OK") and category != "ok":
                continue
            elif filter_value == _("Warning") and category != "warning":
                continue
            elif filter_value == _("Violation") and category != "violation":
                continue
            # "All" shows everything

            # Determine tag based on category
            tag = ()
            if category == "violation":
                tag = ("violation",)
            elif category == "warning":
                tag = ("warning",)

            # Insert into treeview
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    "☐",
                    row["test_name"],
                    row["workstation"],
                    f"{row['result']:.2f}",
                    f"{row['target']:.2f}",
                    westgard,
                ),
                tags=tag,
            )
            self.dict_items[item_id] = row

    def _get_westgard_for_result(self, row):
        """Calculate Westgard rule for a result."""
        try:
            # Get series for this batch/workstation
            series = self.engine.get_series(
                row["batch_id"],
                row["workstation_id"],
                result_id=row["result_id"],
            )
            if not series or len(series) < 1:
                return "NED"

            return self.engine.get_westgard_violation_rule(
                row["target"],
                row["sd"],
                series,
            )
        except Exception:
            return "NED"

    def _on_tree_click(self, evt):
        """Toggle selection when clicking on a row."""
        region = self.tree.identify_region(evt.x, evt.y)
        if region != "cell":
            return

        item_id = self.tree.identify_row(evt.y)
        if not item_id:
            return

        self._toggle_item_selection(item_id)

    def _on_tree_double_click(self, evt):
        """Toggle selection on double-click."""
        item_id = self.tree.identify_row(evt.y)
        if not item_id:
            return

        self._toggle_item_selection(item_id)

    def _toggle_item_selection(self, item_id):
        """Toggle selection state of an item."""
        if item_id in self.selected_items:
            self.selected_items.discard(item_id)
            values = list(self.tree.item(item_id, "values"))
            values[0] = "☐"
            self.tree.item(item_id, values=values)
        else:
            self.selected_items.add(item_id)
            values = list(self.tree.item(item_id, "values"))
            values[0] = "☑"
            self.tree.item(item_id, values=values)

    def _on_select_all(self, evt=None):
        """Select all items."""
        for item_id in self.tree.get_children():
            self.selected_items.add(item_id)
            values = list(self.tree.item(item_id, "values"))
            values[0] = "☑"
            self.tree.item(item_id, values=values)

    def _on_deselect_all(self, evt=None):
        """Deselect all items."""
        for item_id in self.tree.get_children():
            self.selected_items.discard(item_id)
            values = list(self.tree.item(item_id, "values"))
            values[0] = "☐"
            self.tree.item(item_id, values=values)

    def _on_preview(self, evt=None):
        """Show report preview dialog."""
        if not self.selected_items:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select at least one test."),
                parent=self,
            )
            return

        selected_date = self._get_selected_date()
        if selected_date is None:
            return

        # Build report content
        content = self._build_report_content(selected_date)

        # Show preview dialog
        PreviewDialog(self, content, selected_date)

    def _build_report_content(self, selected_date):
        """Build the report text content."""
        lines = []

        # Header
        lines.append("REPORT QC")
        lines.append("=" * 50)

        # Get lab info from organizations
        lab_id = self.engine.current_ids.get("lab_id")
        lab_name = ""
        if lab_id:
            lab_row = self.engine.read(
                False,
                "SELECT description FROM organizations WHERE org_id = ? AND org_type = 'lab'",
                (lab_id,),
            )
            if lab_row:
                lab_name = lab_row["description"]

        # Get current user
        user_name = ""
        if hasattr(self.engine, "log_user") and self.engine.log_user:
            user_name = f"{self.engine.log_user.get('last_name', '')} {self.engine.log_user.get('first_name', '')}".strip()

        lines.append(f"Data: {selected_date.strftime('%d/%m/%Y')}")
        lines.append(f"Laboratorio: {lab_name}")
        lines.append(f"Generato da: {user_name}")
        lines.append(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lines.append("")

        # Results
        for item_id in self.selected_items:
            row = self.dict_items.get(item_id)
            if not row:
                continue

            lines.append("-" * 50)
            lines.append(f"Test: {row['test_name']}")
            lines.append(f"Workstation: {row['workstation']}")
            lines.append(f"Lotto: {row['lot_number']} ({row['batch_desc']})")

            if row["expiration"]:
                exp_str = row["expiration"].strftime("%d/%m/%Y") if hasattr(row["expiration"], "strftime") else str(row["expiration"])
                lines.append(f"Scadenza: {exp_str}")

            unit = row.get("unit") or ""
            lines.append(f"Risultato: {row['result']:.2f} {unit}")
            lines.append(f"Target: {row['target']:.2f}  SD: {row['sd']:.2f}")

            # CV%
            if row["target"] != 0:
                cv = (row["sd"] / row["target"]) * 100
                lines.append(f"CV%: {cv:.2f}%")

            # Deviation in SD
            if row["sd"] != 0:
                deviation = (row["result"] - row["target"]) / row["sd"]
                sign = "+" if deviation >= 0 else ""
                lines.append(f"Deviazione: {sign}{deviation:.2f} SD")

            # Westgard
            westgard = self._get_westgard_for_result(row)
            if westgard == "Accept":
                westgard_display = "OK"
            elif westgard in ("1:3S", "2:2S", "R:4S"):
                westgard_display = f"{westgard} *** QC NON SUPERATO ***"
            elif westgard in ("1:2S", "4:1S", "10:X"):
                westgard_display = f"{westgard} (warning)"
            else:
                westgard_display = westgard
            lines.append(f"Westgard: {westgard_display}")

            # Validation info
            validator = f"{row.get('last_name') or ''} {row.get('first_name') or ''}".strip()
            if validator:
                lines.append(f"Validato da: {validator}")
            if row.get("validated_at"):
                val_at = row["validated_at"]
                val_str = val_at.strftime("%d/%m/%Y %H:%M") if hasattr(val_at, "strftime") else str(val_at)
                lines.append(f"Validato il: {val_str}")

            lines.append("")

        # Summary statistics
        count_ok = 0
        count_warning = 0
        count_violation = 0

        for item_id in self.selected_items:
            row = self.dict_items.get(item_id)
            if not row:
                continue
            westgard = self._get_westgard_for_result(row)
            if westgard in ("1:3S", "2:2S", "R:4S"):
                count_violation += 1
            elif westgard in ("1:2S", "4:1S", "10:X"):
                count_warning += 1
            else:
                count_ok += 1

        # Footer with summary
        lines.append("=" * 50)
        lines.append("RIEPILOGO")
        lines.append(f"  Test OK: {count_ok}")
        lines.append(f"  Warning (1:2S, 4:1S, 10:X): {count_warning}")
        lines.append(f"  Violazioni (1:3S, 2:2S, R:4S): {count_violation}")
        lines.append("")
        lines.append(f"Report completato - {len(self.selected_items)} test inclusi")

        return "\n".join(lines)

    def on_cancel(self, evt=None):
        """Close the window."""
        # Unsubscribe from events
        self.engine.unsubscribe("result_changed", self._on_result_changed)
        super().on_cancel(evt)


class PreviewDialog(tk.Toplevel):
    """Preview dialog for QC report."""

    def __init__(self, parent, content, selected_date):
        super().__init__(parent)
        self.parent = parent
        self.content = content
        self.selected_date = selected_date
        self.engine = parent.engine

        self.title(_("Report Preview"))
        # Note: transient() removed - breaks resize on Windows
        self.grab_set()

        self.resizable(True, True)
        self.minsize(500, 400)

        self._build_ui()
        self.engine.center_window(self)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", self._on_close)

    def _build_ui(self):
        """Build dialog UI."""
        padd = {"padx": 5, "pady": 5}

        # Main frame
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, expand=True)

        # Text widget with scrollbar
        frm_text = ttk.Frame(frm_main, style="App.TFrame")
        frm_text.pack(fill=tk.BOTH, expand=True, **padd)

        sb = ttk.Scrollbar(frm_text, orient=tk.VERTICAL)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_preview = tk.Text(
            frm_text,
            wrap=tk.NONE,
            font=("Courier", 10),
            yscrollcommand=sb.set,
        )
        self.txt_preview.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.txt_preview.yview)

        # Insert content
        self.txt_preview.insert("1.0", self.content)
        self.txt_preview.config(state=tk.DISABLED)

        # Buttons frame
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.pack(fill=tk.X, **padd)

        btn_print = ttk.Button(
            frm_buttons,
            text=_("Print"),
            command=self._on_print,
        )
        btn_print.pack(side=tk.LEFT, **padd)

        btn_save = ttk.Button(
            frm_buttons,
            text=_("Save"),
            command=self._on_save,
        )
        btn_save.pack(side=tk.LEFT, **padd)

        btn_copy = ttk.Button(
            frm_buttons,
            text=_("Copy"),
            command=self._on_copy,
        )
        btn_copy.pack(side=tk.LEFT, **padd)

        btn_close = ttk.Button(
            frm_buttons,
            text=_("Close"),
            command=self._on_close,
        )
        btn_close.pack(side=tk.RIGHT, **padd)

    def _on_print(self, evt=None):
        """Print the report using system print dialog."""
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8"
            ) as f:
                f.write(self.content)
                temp_path = f.name

            # Use lpr on Linux
            subprocess.run(["lpr", temp_path], check=True)
            messagebox.showinfo(
                self.engine.app_title,
                _("Report sent to printer."),
                parent=self,
            )
        except FileNotFoundError:
            messagebox.showwarning(
                self.engine.app_title,
                _("Printer not available. Use Save to export the file."),
                parent=self,
            )
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                self.engine.app_title,
                f"{_('Print error:')}\n{e}",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                self.engine.app_title,
                f"{_('Print error:')}\n{e}",
                parent=self,
            )

    def _on_save(self, evt=None):
        """Save report to file."""
        default_filename = f"QC_Report_{self.selected_date.strftime('%Y-%m-%d')}.txt"
        filepath = filedialog.asksaveasfilename(
            parent=self,
            title=_("Save Report"),
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename,
        )

        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.content)
            messagebox.showinfo(
                self.engine.app_title,
                _("Report saved successfully."),
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                self.engine.app_title,
                f"{_('Error saving file:')}\n{e}",
                parent=self,
            )

    def _on_copy(self, evt=None):
        """Copy report to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.content)
        messagebox.showinfo(
            self.engine.app_title,
            _("Report copied to clipboard."),
            parent=self,
        )

    def _on_close(self, evt=None):
        """Close the dialog."""
        self.grab_release()
        self.destroy()
