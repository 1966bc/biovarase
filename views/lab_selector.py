# -*- coding: utf-8 -*-
"""
Lab Selector Dialog - Select laboratory for admin users.

Shows a list of available laboratories for admin users (role=0)
at login. Optionally pre-selects the user's default lab.

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
"""
import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _


class LabSelectorDialog(tk.Toplevel):
    """Dialog for selecting a laboratory."""

    def __init__(self, parent, default_lab_id=None):
        super().__init__(parent)
        self.parent = parent
        self.engine = parent.engine
        self.selected_lab_id = None
        self.default_lab_id = default_lab_id

        self.title(_("Select Laboratory"))
        self.transient(parent)
        self.grab_set()

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

        self._build_ui()
        self._load_labs()
        self.engine.center_window(self)

    def _build_ui(self):
        """Build dialog UI."""
        padd = {"padx": 10, "pady": 5}

        # Main frame
        frm_main = ttk.Frame(self, style="App.TFrame", padding=15)
        frm_main.pack(fill=tk.BOTH, expand=True)

        # Label
        ttk.Label(
            frm_main,
            text=_("Select the laboratory to work with:"),
            style="App.TLabel"
        ).pack(**padd)

        # Listbox with scrollbar
        frm_list = ttk.Frame(frm_main, style="App.TFrame")
        frm_list.pack(fill=tk.BOTH, expand=True, **padd)

        sb = ttk.Scrollbar(frm_list, orient=tk.VERTICAL)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            frm_list,
            height=8,
            width=50,
            yscrollcommand=sb.set,
            font=("TkFixedFont", 10),
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.listbox.yview)

        self.listbox.bind("<Double-1>", self._on_select)

        # Buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.pack(fill=tk.X, **padd)

        btn_select = ttk.Button(
            frm_buttons,
            text=_("Select"),
            command=self._on_select,
        )
        btn_select.pack(side=tk.LEFT, **padd)

        btn_cancel = ttk.Button(
            frm_buttons,
            text=_("Cancel"),
            command=self._on_cancel,
        )
        btn_cancel.pack(side=tk.RIGHT, **padd)

        # Store lab_ids for selection
        self.lab_ids = []

    def _load_labs(self):
        """Load available laboratories with region names from organizations."""
        # Get labs from organizations table (org_type='lab')
        # Join with parent organization (region) for context
        sql = """
            SELECT
                lab.org_id AS lab_id,
                lab.description AS lab_name,
                COALESCE(region.description, 'N/A') AS region_name
            FROM organizations lab
            LEFT JOIN organizations region ON lab.parent_id = region.org_id
            WHERE lab.org_type = 'lab' AND lab.status = 1
            ORDER BY region.description, lab.description
        """
        rows = self.engine.read(True, sql, ()) or []

        self.listbox.delete(0, tk.END)
        self.lab_ids = []

        if rows:
            default_idx = 0
            for idx, row in enumerate(rows):
                display = f"{row['lab_name']} - {row['region_name']}"
                self.listbox.insert(tk.END, display)
                self.lab_ids.append(row["lab_id"])
                if row["lab_id"] == self.default_lab_id:
                    default_idx = idx

            # Select default or first item
            self.listbox.selection_set(default_idx)
            self.listbox.see(default_idx)
            self.listbox.focus_set()

    def _on_select(self, evt=None):
        """Handle lab selection."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select a laboratory."),
                parent=self,
            )
            return

        idx = selection[0]
        self.selected_lab_id = self.lab_ids[idx]
        self.grab_release()
        self.destroy()

    def _on_cancel(self, evt=None):
        """Handle cancel - returns None."""
        self.selected_lab_id = None
        self.grab_release()
        self.destroy()

    def get_selected_lab_id(self):
        """Return the selected lab_id or None if cancelled."""
        return self.selected_lab_id
