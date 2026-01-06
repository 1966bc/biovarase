# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   ver MMXXV - refactored with tabular format and column headers
#-----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import views.site as ui


SQL = """
    SELECT 
        sites.site_id, 
        (SELECT suppliers.description
           FROM suppliers
          WHERE suppliers.supplier_id = sites.supplier_id) AS company, 
        (SELECT suppliers.description
           FROM suppliers
          WHERE suppliers.supplier_id = sites.comp_id)      AS site, 
        sites.status 
    FROM sites 
    ORDER BY company ASC
"""


class UI(tk.Toplevel):
    """
    Sites Management Window - Master view (Singleton).
    
    Displays all sites in the system with their associated company and site name.
    Uses fixed-width monospaced font to simulate table columns with header.
    
    Columns:
        - Company (supplier_id): Hospital/company name
        - Site (comp_id): Site/location name
        - Status: Active (enabled) or inactive (grayed out)
    
    Architecture:
        - Singleton pattern (only one instance allowed)
        - Uses fixed-width columns with monospaced font (TkFixedFont)
        - Header row at index 0 (non-selectable, styled)
        - Data rows start at index 1
    """

    # ------------------------------------------------------------------
    # Column Layout Constants (Single Source of Truth)
    # ------------------------------------------------------------------
    COL_COMPANY_WIDTH = 40   # Company/supplier name
    COL_SITE_WIDTH = 40      # Site name
    COL_SPACING = 3          # Spaces between columns

    _instance = None

    def __new__(cls, parent):
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                cls._instance = None
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(name="sites")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        

        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        # Window
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Hot keys
        self.bind("<Escape>", self.on_cancel)
        self.bind("<Alt-c>", self.on_cancel)

        # State
        self.table = "sites"
        self.primary_key = "site_id"

        self.child = None
        self.selected_item = None      # hybrid dict from get_selected
        self.dict_items = {}           # idx listbox -> site_id (starts at 1, 0 is header)
        self.items = tk.StringVar()

        # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window(self, on_screen=True)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        # Set reasonable window size for table display
        self.update_idletasks()
        min_width = 700   # Wide enough for both columns + spacing
        min_height = 500  # Show ~20-25 rows comfortably
        self.minsize(min_width, min_height)
        
        # Set initial geometry (can be resized by user)
        self.geometry(f"{min_width}x{min_height}")

    # ----------------------------------------------------------------- UI
    def _build_ui(self):
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left side: list + scrollbar
        frm_left = ttk.Frame(
            frm_main,
            style="App.TFrame",
            relief=tk.GROOVE,
            padding=8,
        )
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=5, expand=True)

        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL)
        self.lstItems = tk.Listbox(
            frm_left,
            yscrollcommand=sb.set,
            exportselection=False,
            font="TkFixedFont",  # Monospaced font for column alignment
        )
        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self._on_item_activated)
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y, expand=0)

        # Right side: buttons
        frm_buttons = ttk.Frame(
            frm_main,
            style="App.TFrame",
            relief=tk.GROOVE,
            padding=8,
        )

        def add_btn(text, cmd, underline=None, shortcut=None):
            btn = ttk.Button(frm_buttons, text=text, command=cmd, underline=underline)
            btn.pack(fill=tk.X, padx=5, pady=5)
            if shortcut:
                self.bind(shortcut, lambda e, c=cmd: c())
            return btn

        add_btn("Add",    self._on_add,            underline=0, shortcut="<Alt-a>")
        add_btn("Update", self._on_item_activated, underline=0, shortcut="<Alt-u>")
        add_btn("Cancel", self.on_cancel,         underline=0, shortcut="<Alt-c>")

        self.bind("<Return>", self._on_item_activated)

        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, expand=0)

    # ----------------------------------------------------------------- Data formatting
    def _format_header(self) -> str:
        """
        Build the header row with column titles.
        
        Returns:
            Formatted header string with fixed-width columns
        """
        spacing = " " * self.COL_SPACING
        header = (
            f"{'Company':<{self.COL_COMPANY_WIDTH}}"
            f"{spacing}"
            f"{'Site':<{self.COL_SITE_WIDTH}}"
        )
        return header

    def _format_row(self, row: dict) -> str:
        """
        Build a fixed-width data row for the Listbox.
        
        Columns:
            1) Company name (from supplier_id)
            2) Site name (from comp_id)
        
        Args:
            row: Dictionary with site data from database
        
        Returns:
            Formatted string with fixed-width columns
        """
        # Extract and sanitize fields
        company = (row.get("company") or "").strip()
        site_name = (row.get("site") or "").strip()

        # Truncate to column widths (prevent overflow)
        company = company[:self.COL_COMPANY_WIDTH]
        site_name = site_name[:self.COL_SITE_WIDTH]

        # Build formatted string with fixed-width columns
        spacing = " " * self.COL_SPACING
        label = (
            f"{company:<{self.COL_COMPANY_WIDTH}}"
            f"{spacing}"
            f"{site_name:<{self.COL_SITE_WIDTH}}"
        )
        return label

    def _parse_listbox_row(self, raw: str) -> dict:
        """
        Parse a formatted Listbox row back into individual fields.
        
        This method is the inverse of _format_row(): it extracts the fields
        from the fixed-width formatted string using the same column widths.
        
        Args:
            raw: Formatted string from Listbox.get()
        
        Returns:
            Dictionary with parsed fields: company, site
        """
        pos = 0

        # Extract company name
        company = raw[pos:pos + self.COL_COMPANY_WIDTH].strip()
        pos += self.COL_COMPANY_WIDTH + self.COL_SPACING

        # Extract site name (rest of string)
        site = raw[pos:].strip()

        return {
            "company": company,
            "site": site
        }

    # ----------------------------------------------------------------- lifecycle
    def on_open(self):
        """Initialize window on open."""
        self.title("Sites Management")
        self.set_values()

    def set_values(self):
        """
        Populate the Listbox with all sites from database.
        
        Behavior:
            - Index 0: Header row (styled, non-selectable)
            - Index 1+: Data rows (site_id mapped in dict_items)
            - Inactive sites (status=0): grayed out background
        """
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()
        self.selected_item = None

        # Insert header row at index 0
        header = self._format_header()
        self.lstItems.insert(tk.END, header)
        self.lstItems.itemconfig(0, bg="lightgray", fg="black")  # Header style

        # Fetch data
        try:
            rows = self.engine.read(True, SQL, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "sites.set_values:read",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        # Populate data rows (index starts at 1)
        for row in rows:
            site_id = row.get("site_id")
            status = row.get("status", 1)

            # Format and insert row
            label = self._format_row(row)
            idx = self.lstItems.size()  # Current index (after header)
            self.lstItems.insert(tk.END, label)

            # Style inactive sites
            if int(status) != 1:
                self.lstItems.itemconfig(idx, {"bg": "light gray"})

            # Map listbox index -> site_id (skip header at index 0)
            if site_id is not None:
                self.dict_items[idx] = int(site_id)

        # Update count label (exclude header from count)
        data_rows = self.lstItems.size() - 1  # Subtract header
        msg = f"Sites: {data_rows}"
        self.items.set(msg)

    def on_item_selected(self, _evt=None):
        """
        Update self.selected_item when the user selects an item.
        
        Note: Skips header row (index 0) - not selectable for editing.
        """
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return

        idx = sel[0]
        
        # Skip header row
        if idx == 0:
            self.selected_item = None
            return

        pk = self.dict_items.get(idx)
        if pk is None:
            self.selected_item = None
            return

        # Fetch full row as hybrid dict from the Engine
        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            pk,
        )

    def _on_item_activated(self, _evt=None):
        """
        Double-click or Enter: open the editor for the selected item.
        
        Note: Skips header row (index 0).
        """
        sel = self.lstItems.curselection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        idx = sel[0]
        
        # Skip header row
        if idx == 0:
            messagebox.showinfo(
                self.engine.app_title,
                "This is the header row. Please select a site to edit.",
                parent=self,
            )
            return

        if 1 <= idx < self.lstItems.size():
            self._open_child(idx)

    def _on_add(self, _evt=None):
        """Add button handler: open editor in INSERT mode."""
        self._open_child(index=None)

    def _open_child(self, index=None):
        """
        Open child editor window for the given site.
        
        Args:
            index: Listbox index (or None for INSERT mode)
        """
        # Destroy previous child, if any
        try:
            if self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass

        # Translate listbox index -> primary key
        if index is None:
            pk = None  # INSERT mode
        else:
            pk = self.dict_items.get(index)
            if pk is None:
                messagebox.showwarning(
                    self.engine.app_title,
                    self.engine.no_selected,
                    parent=self,
                )
                return

        # Create editor with the correct PK (or None for INSERT)
        self.child = ui.UI(self, index=pk)
        self.child.on_open()

    def _reselect_by_pk(self, pk):
        """
        Reselect the item with the given primary key after reload.
        
        Args:
            pk: Primary key (site_id) to reselect
        """
        if pk is None:
            return
        try:
            for idx, value in self.dict_items.items():
                if value == pk:
                    self.lstItems.selection_clear(0, tk.END)
                    self.lstItems.selection_set(idx)
                    self.lstItems.see(idx)
                    break
        except Exception as e:
            pass

    def reload_and_reselect(self, pk_to_select):
        """
        Called by child after save:
        reloads data and reselects the given PK.
        
        Args:
            pk_to_select: Primary key of the site to reselect
        """
        self.set_values()
        self._reselect_by_pk(pk_to_select)

    # ------------------------------------------------------------- close
    def on_cancel(self, _evt=None):
        """Close handler: remove instance from Engine dict and close safely."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
