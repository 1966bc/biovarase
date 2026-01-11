# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   January 2026
# -----------------------------------------------------------------------------
"""
Category editor with lab_id support for multi-tenant.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
from views.child_view import ChildView


class UI(ChildView):
    """
    Editor for categories table with lab_id field.

    Fields:
        - lab_id: combobox to select laboratory
        - description: category name
        - status: active/inactive
    """

    def __init__(self, parent, index=None):
        super().__init__(parent, name="category_editor")

        self.index = index
        self.selected_item = None

        # Form variables
        self.lab_var = tk.StringVar()
        self.description = tk.StringVar()
        self.status = tk.BooleanVar()

        # Lab mapping
        self.labs = []
        self.dict_labs = {}

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

        # Lab combobox
        ttk.Label(frm_left, text=_("Laboratory:")).grid(
            row=r, column=0, sticky="w", padx=5, pady=5
        )
        self.cbLab = ttk.Combobox(
            frm_left,
            textvariable=self.lab_var,
            state="readonly",
            width=30
        )
        self.cbLab.grid(row=r, column=1, sticky="ew", padx=5, pady=5)

        r += 1

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
        self._load_labs()

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
            # Pre-select current lab
            current_lab_id = self.engine.get_lab_id()
            if current_lab_id:
                for idx, lab_id in self.dict_labs.items():
                    if lab_id == current_lab_id:
                        self.cbLab.current(idx)
                        break

        self.txDescription.focus_set()

    def _load_labs(self):
        """Load laboratories for combobox from organizations table."""
        role = self.engine.log_user["role"]

        if role == 0:
            # Admin: all labs
            sql = """
                SELECT org_id AS lab_id, description
                FROM organizations
                WHERE org_type = 'lab' AND status = 1
                ORDER BY description
            """
            args = ()
        else:
            # Others: only their lab
            sql = """
                SELECT org_id AS lab_id, description
                FROM organizations
                WHERE org_id = ? AND org_type = 'lab' AND status = 1
            """
            args = (self.engine.get_lab_id(),)

        rows = self.engine.read(True, sql, args) or []
        self.labs = list(rows)

        values = []
        self.dict_labs = {}
        for idx, lab in enumerate(self.labs):
            values.append(lab["description"])
            self.dict_labs[idx] = lab["lab_id"]

        self.cbLab["values"] = values

    def _set_values(self):
        """Populate form from selected record."""
        if not self.selected_item:
            return

        # Set lab
        lab_id = self.selected_item.get("lab_id")
        if lab_id:
            for idx, lid in self.dict_labs.items():
                if lid == lab_id:
                    self.cbLab.current(idx)
                    break

        self.description.set(self.selected_item.get("description", ""))
        self.status.set(bool(self.selected_item.get("status", 1)))

    def _on_save(self, _evt=None):
        """Save category."""
        # Validate
        if self.cbLab.current() < 0:
            messagebox.showwarning(
                self.engine.app_title,
                _("Please select a laboratory."),
                parent=self
            )
            return

        desc = self.description.get().strip()
        if not desc:
            messagebox.showwarning(
                self.engine.app_title,
                _("Category is required."),
                parent=self
            )
            return

        # Check duplicate
        lab_id = self.dict_labs[self.cbLab.current()]
        sql = """
            SELECT category_id FROM categories
            WHERE description = ? AND lab_id = ?
            LIMIT 1
        """
        row = self.engine.read(False, sql, (desc, lab_id))
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

        # Build args: lab_id, description, status
        args = [
            lab_id,
            desc,
            int(self.status.get())
        ]

        if self.index is not None:
            # UPDATE
            sql = """
                UPDATE categories
                SET lab_id = ?, description = ?, status = ?
                WHERE category_id = ?
            """
            args.append(self.selected_item["category_id"])
        else:
            # INSERT
            sql = """
                INSERT INTO categories (lab_id, description, status)
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
