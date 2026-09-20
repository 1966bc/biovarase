# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   January 2026
# -----------------------------------------------------------------------------
"""
Category editor - categories are always created in the current lab context.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
from ui.child_view import ChildView


class UI(ChildView):
    """
    Editor for categories table.

    Categories are automatically assigned to the current laboratory
    (from engine.get_lab_id()).

    Fields:
        - description: category name
        - status: active/inactive
    """

    def __init__(self, parent, index=None):
        super().__init__(parent, name="category_editor")

        self.index = index
        self.selected_item = None

        # Form variables
        self.description = tk.StringVar()
        self.status = tk.BooleanVar()

        self._build_ui()
        self.show()

    def _build_ui(self):
        """Build the editor form."""
        paddings = {"padx": 8, "pady": 8}

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.grid(row=0, column=0, sticky="nsew")
        self.frm_main = frm_main

        # Left form
        frm_left = ttk.Frame(frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky="ns", **paddings)

        r = 0

        # Description
        ttk.Label(frm_left, text=_("Category:")).grid(
            row=r, column=0, sticky="w", padx=5, pady=5
        )
        self.txDescription = ttk.Entry(
            frm_left,
            textvariable=self.description,
            width=30
        )
        self.txDescription.grid(row=r, column=1, sticky="ew", padx=5, pady=5)

        r += 1

        # Status
        ttk.Label(frm_left, text=_("Status:")).grid(
            row=r, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        ).grid(row=r, column=1, sticky="w", padx=5, pady=5)

        frm_left.columnconfigure(1, weight=1)

        # Buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        ttk.Button(
            frm_buttons,
            text=_("Save"),
            command=self._on_save,
        ).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(
            frm_buttons,
            text=_("Cancel"),
            command=self.on_cancel,
        ).grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

    def on_open(self):
        """Load data and set form values."""
        if self.index is not None:
            # UPDATE mode
            self.title(_("Update Category"))
            self.selected_item = getattr(self.parent, "selected_item", None)
            if self.selected_item is None:
                self.on_cancel()
                return
            self._set_values()
        else:
            # INSERT mode
            self.title(_("Add Category"))
            self.status.set(True)

        self.txDescription.focus_set()

    def _set_values(self):
        """Populate form from selected record."""
        if not self.selected_item:
            return

        self.description.set(self.selected_item.get("description", ""))
        self.status.set(bool(self.selected_item.get("status", 1)))

    def _on_save(self, _evt=None):
        """Save category."""
        desc = self.description.get().strip()
        if not desc:
            messagebox.showwarning(
                self.engine.app_title,
                _("Category is required."),
                parent=self
            )
            return

        # Get current lab org_id
        org_id = self.engine.get_lab_id()
        if not org_id:
            messagebox.showerror(
                self.engine.app_title,
                _("No laboratory selected."),
                parent=self
            )
            return

        # Check duplicate
        sql = """
            SELECT category_id FROM categories
            WHERE description = ? AND org_id = ?
            LIMIT 1
        """
        row = self.engine.read(False, sql, (desc, org_id))
        if row:
            current_id = self.selected_item.get("category_id") if self.selected_item else None
            if current_id is None or row["category_id"] != current_id:
                messagebox.showwarning(
                    self.engine.app_title,
                    _("Category already exists in this laboratory!"),
                    parent=self
                )
                return

        # Confirm
        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.ask_to_save,
            parent=self
        ):
            return

        # Build args: org_id, description, status
        args = [
            org_id,
            desc,
            int(self.status.get())
        ]

        if self.index is not None:
            # UPDATE
            sql = """
                UPDATE categories
                SET org_id = ?, description = ?, status = ?
                WHERE category_id = ?
            """
            args.append(self.selected_item["category_id"])
        else:
            # INSERT
            sql = """
                INSERT INTO categories (org_id, description, status)
                VALUES (?, ?, ?)
            """

        last_id = self.engine.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = _("Save failed.")
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        self.parent._set_values()
        self.engine.notify("categories_changed")
        self.on_cancel()
