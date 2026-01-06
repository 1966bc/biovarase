# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc (users & user refactor inspired by methods/method)
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV - refactored with tabular format and column headers
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from views.parent_view import ParentView
import views.user as ui


SQL = """
    SELECT
        user_id,
        last_name,
        first_name,
        nickname,
        status
    FROM users
    ORDER BY last_name ASC, first_name ASC
"""


class UI(ParentView):
    """
    Users Management Window - Master view (Singleton).

    Displays all users in the system with their full name and nickname.
    Uses fixed-width monospaced font to simulate table columns with header.
    """

    # ------------------------------------------------------------------
    # Column Layout Constants (Single Source of Truth)
    # ------------------------------------------------------------------
    COL_LASTNAME_WIDTH = 25    # Last name
    COL_FIRSTNAME_WIDTH = 25   # First name
    COL_NICKNAME_WIDTH = 20    # Nickname (login)
    COL_SPACING = 3            # Spaces between columns

    def __init__(self, parent):
        super().__init__(parent, name="users")

        if self._reusing:
            return

        self.table = "users"
        self.primary_key = "user_id"

        self.child = None            # child editor (views.user.UI)
        self.dict_items = {}         # listbox index -> user_id (starts at 1, 0 is header)
        self.selected_item = None    # hybrid dict from engine.get_selected()
        self.items = tk.StringVar()  # status text (items count)

        self.bind("<Return>", self.on_item_activated)

        # --- Build interface ------------------------------------------------
        self._build_ui()

        min_width = 750
        min_height = 500
        self.minsize(min_width, min_height)
        self.geometry(f"{min_width}x{min_height}")

        self.show()

    # ------------------------------------------------------------------ UI BUILD
    def _build_ui(self):
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        # Left: list + scrollbar
        frm_left = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), expand=True)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL)
        self.lstItems = tk.Listbox(
            frm_left,
            yscrollcommand=sb.set,
            font="TkFixedFont",  # Monospaced font for column alignment
        )
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self.on_item_activated)

        # Right: buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, expand=False)

        self._add_button(frm_buttons, "Add",    self.on_add,            "<Alt-a>")
        self._add_button(frm_buttons, "Update", self.on_item_activated, "<Alt-u>")
        self._add_button(frm_buttons, "Cancel", self.on_cancel,         "<Alt-c>")

    def _add_button(self, parent, text, cmd, hotkey):
        """Helper: create a button and bind an optional keyboard shortcut."""
        btn = ttk.Button(parent, style="App.TButton", text=text, command=cmd)
        btn.pack(fill=tk.X, pady=4)
        if hotkey:
            self.bind(hotkey, cmd)

    def _focus_list(self):
        """Give focus to the listbox safely (only if window still exists)."""
        if self.winfo_exists():
            try:
                self.lstItems.focus_set()
            except Exception as e:
                pass

    # ------------------------------------------------------------------ Data formatting
    def _format_header(self) -> str:
        """
        Build the header row with column titles.
        
        Returns:
            Formatted header string with fixed-width columns
        """
        spacing = " " * self.COL_SPACING
        header = (
            f"{'Last Name':<{self.COL_LASTNAME_WIDTH}}"
            f"{spacing}"
            f"{'First Name':<{self.COL_FIRSTNAME_WIDTH}}"
            f"{spacing}"
            f"{'Nickname':<{self.COL_NICKNAME_WIDTH}}"
        )
        return header

    def _format_row(self, row: dict) -> str:
        """
        Build a fixed-width data row for the Listbox.
        
        Columns:
            1) Last name
            2) First name
            3) Nickname (login)
        
        Args:
            row: Dictionary with user data from database
        
        Returns:
            Formatted string with fixed-width columns
        """
        # Extract and sanitize fields
        last_name = (row.get("last_name") or "").strip()
        first_name = (row.get("first_name") or "").strip()
        nickname = (row.get("nickname") or "").strip()

        # Truncate to column widths (prevent overflow)
        last_name = last_name[:self.COL_LASTNAME_WIDTH]
        first_name = first_name[:self.COL_FIRSTNAME_WIDTH]
        nickname = nickname[:self.COL_NICKNAME_WIDTH]

        # Build formatted string with fixed-width columns
        spacing = " " * self.COL_SPACING
        label = (
            f"{last_name:<{self.COL_LASTNAME_WIDTH}}"
            f"{spacing}"
            f"{first_name:<{self.COL_FIRSTNAME_WIDTH}}"
            f"{spacing}"
            f"{nickname:<{self.COL_NICKNAME_WIDTH}}"
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
            Dictionary with parsed fields: last_name, first_name, nickname
        """
        pos = 0

        # Extract last name
        last_name = raw[pos:pos + self.COL_LASTNAME_WIDTH].strip()
        pos += self.COL_LASTNAME_WIDTH + self.COL_SPACING

        # Extract first name
        first_name = raw[pos:pos + self.COL_FIRSTNAME_WIDTH].strip()
        pos += self.COL_FIRSTNAME_WIDTH + self.COL_SPACING

        # Extract nickname (rest of string)
        nickname = raw[pos:].strip()

        return {
            "last_name": last_name,
            "first_name": first_name,
            "nickname": nickname
        }

    # ------------------------------------------------------------------ OPEN
    def on_open(self):
        """Called once the window is ready: set title and load users."""
        self.title("Users Management")
        self._load_items()
        
    # ------------------------------------------------------------------ LOAD DATA
    def _load_items(self):
        """
        Load all users into the listbox.

        Behavior:
            - Index 0: Header row (styled, non-selectable)
            - Index 1+: Data rows (user_id mapped in dict_items)
            - Inactive users (status=0): grayed out background
        """
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()
        self.selected_item = None

        # Insert header row at index 0
        header = self._format_header()
        self.lstItems.insert(tk.END, header)
        self.lstItems.itemconfig(0, bg="lightgray", fg="black")  # Header style

        rows = self.engine.read(True, SQL, ()) or []

        # Populate data rows (index starts at 1)
        for row in rows:
            user_id = int(row["user_id"])
            status = int(row.get("status", 1))

            # Format and insert row
            label = self._format_row(row)
            idx = self.lstItems.size()  # Current index (after header)
            self.lstItems.insert(tk.END, label)

            # Style inactive users
            if status != 1:
                self.lstItems.itemconfig(idx, {"bg": self.engine.get_rgb(211, 211, 211)})

            # Map listbox index -> user_id (skip header at index 0)
            self.dict_items[idx] = user_id

        # Update count label (exclude header from count)
        data_rows = self.lstItems.size() - 1  # Subtract header
        msg = f"Users: {data_rows}"
        self.items.set(msg)

    # ------------------------------------------------------------------ SELECTION
    def on_item_selected(self, _evt=None):
        """
        Track current selection and fetch full record for later operations.
        selected_item is a hybrid dict (index + column names).
        
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

        self.selected_item = self.engine.get_selected(self.table, self.primary_key, pk)

    def on_item_activated(self, _evt=None):
        """
        Double-click or Enter on a selected item → open editor in UPDATE mode.
        
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
                "This is the header row. Please select a user to edit.",
                parent=self,
            )
            return

        if 1 <= idx < self.lstItems.size():
            self._open_editor(index=idx)

    # ------------------------------------------------------------------ ADD / EDIT
    def on_add(self, _evt=None):
        """Open editor in INSERT mode."""
        self._open_editor(index=None)

    def _open_editor(self, index=None):
        """
        Open the child editor (frames.user.UI).

        Args:
            index:
                None → INSERT
                int  → UPDATE (parent.selected_item already set by on_item_selected)
        """
        # Close any existing child editor
        try:
            if self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass

        # Create a fresh editor instance
        self.child = ui.UI(self, index)
        self.child.on_open()

    # ------------------------------------------------------------------ CLOSE
    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
