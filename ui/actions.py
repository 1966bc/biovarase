# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Actions management view.

Actions are global master data used for peer lab comparison.
They have:
- code: English identifier (UPPERCASE, unique) - used for peer lab matching
- description: English readable text - translated via i18n for display
- status: active/inactive flag
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ui.parent_view import ParentView
from ui.child_view import ChildView


class UI(ParentView):
    """Master window for managing QC actions."""

    def __init__(self, parent):
        super().__init__(parent, name="actions")
        if self._reusing:
            return

        self.table = "actions"
        self.primary_key = "action_id"
        self.child = None
        self.dict_items = {}
        self.selected_item = None
        self.items = tk.StringVar()

        self._build_ui()
        self.minsize(700, 400)
        self.show()

    def _build_ui(self):
        """Build the UI layout."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left panel with treeview
        frm_left = ttk.Frame(frm_main, style="Panel.TFrame")
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=5, expand=True)

        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)

        # Treeview with columns
        cols = ("code", "description", "status")
        self.lstItems = ttk.Treeview(frm_left, columns=cols, show="headings")

        self.lstItems.column("code", width=150, minwidth=100, anchor=tk.W)
        self.lstItems.heading("code", text="Code", anchor=tk.W)

        self.lstItems.column("description", width=250, minwidth=150, anchor=tk.W)
        self.lstItems.heading("description", text="Description", anchor=tk.W)

        self.lstItems.column("status", width=80, minwidth=60, anchor=tk.CENTER)
        self.lstItems.heading("status", text="Status", anchor=tk.CENTER)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL, command=self.lstItems.yview)
        self.lstItems.configure(yscrollcommand=sb.set)
        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.tag_configure("disabled", foreground="gray")
        self.lstItems.bind("<<TreeviewSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-1>", self.on_item_activated)

        # Right panel: buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        self.engine.add_button(frm_buttons, "Add", self.on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, "Update", self.on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, "Cancel", self.on_cancel, "<Alt-c>", self)

        self.bind("<Return>", self.on_item_activated)

    def on_open(self):
        """Initialize view."""
        self.title("Actions" + " - " + "Global Master Data")
        self._set_values()

    def _set_values(self):
        """Load actions into treeview."""
        self.lstItems.delete(*self.lstItems.get_children())
        self.dict_items.clear()
        self.selected_item = None

        sql = """
            SELECT action_id, code, description, status
            FROM actions
            ORDER BY code ASC;
        """
        rows = self.engine.db.read(True, sql, ()) or []

        for row in rows:
            status_text = "Enabled" if row["status"] == 1 else "Disabled"
            tags = () if row["status"] == 1 else ("disabled",)

            # Translate description for display
            display_desc = _(row["description"]) if row["description"] else ""

            iid = self.lstItems.insert(
                "", tk.END,
                values=(row["code"], display_desc, status_text),
                tags=tags
            )
            self.dict_items[iid] = row["action_id"]

        self.items.set(f"Items: {len(rows)}")

    def on_item_selected(self, _evt=None):
        """Update selected_item when selection changes."""
        sel = self.lstItems.selection()
        if not sel:
            self.selected_item = None
            return

        pk = self.dict_items.get(sel[0])
        if pk is None:
            self.selected_item = None
            return

        self.selected_item = self.engine.db.get_selected(
            self.table, self.primary_key, pk
        )

    def on_item_activated(self, _evt=None):
        """Open editor for selected item."""
        sel = self.lstItems.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        self.on_item_selected()
        self.engine.open_child(self, ActionEditor, index=sel[0])

    def on_add(self, _evt=None):
        """Open editor in INSERT mode."""
        self.engine.open_child(self, ActionEditor, index=None)


class ActionEditor(ChildView):
    """Editor window for a single action (insert/update)."""

    def __init__(self, parent, index=None):
        super().__init__(parent, name="action_editor")

        self.index = index
        self.selected_item = None

        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Form variables
        self.code = tk.StringVar()
        self.description = tk.StringVar()
        self.status = tk.BooleanVar()

        self._build_ui()
        self.show()

    def _build_ui(self):
        """Build the editor layout."""
        pad = {"padx": 8, "pady": 8}

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.grid(row=0, column=0, sticky="nsew")

        # Left: form fields
        frm_left = ttk.Frame(frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky="ns", **pad)
        frm_left.columnconfigure(1, weight=1)

        r = 0
        # Code field (English, uppercase)
        ttk.Label(frm_left, text="Code:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=5)
        self.txCode = ttk.Entry(frm_left, textvariable=self.code, width=30)
        self.txCode.grid(row=r, column=1, sticky="ew", padx=5, pady=5)

        r += 1
        # Description field (English readable)
        ttk.Label(frm_left, text="Description:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=5)
        self.txDescription = ttk.Entry(frm_left, textvariable=self.description, width=40)
        self.txDescription.grid(row=r, column=1, sticky="ew", padx=5, pady=5)

        r += 1
        # Help text
        help_text = "Code: English uppercase (e.g., CALIBRATION)"
        ttk.Label(frm_left, text=help_text, foreground="gray").grid(
            row=r, column=0, columnspan=2, sticky=tk.W, padx=5
        )

        r += 1
        help_text2 = "Description: English text (translated via i18n)"
        ttk.Label(frm_left, text=help_text2, foreground="gray").grid(
            row=r, column=0, columnspan=2, sticky=tk.W, padx=5
        )

        r += 1
        # Status
        ttk.Label(frm_left, text="Status:").grid(row=r, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Checkbutton(
            frm_left, onvalue=1, offvalue=0, variable=self.status
        ).grid(row=r, column=1, sticky="w", padx=5, pady=5)

        # Right: buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **pad)

        ttk.Button(
            frm_buttons, style="App.TButton", text="Save",
            underline=0, command=self._on_save
        ).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(
            frm_buttons, style="App.TButton", text="Cancel",
            underline=0, command=self.on_cancel
        ).grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    def on_open(self):
        """Initialize editor."""
        if self.index is not None:
            self.title("Update" + " " + "Action")
            self.selected_item = getattr(self.parent, "selected_item", None)
            if self.selected_item:
                self._set_values()
        else:
            self.title("Add" + " " + "Action")
            self.status.set(True)

        self.txCode.focus_set()

    def _set_values(self):
        """Populate fields from selected_item."""
        if not self.selected_item:
            return

        self.code.set(self.selected_item.get("code", ""))
        self.description.set(self.selected_item.get("description", ""))
        self.status.set(bool(self.selected_item.get("status", 1)))

    def _get_values(self):
        """Return form values for SQL."""
        return [
            self.code.get().strip().upper(),  # Force uppercase
            self.description.get().strip(),
            int(self.status.get()),
        ]

    def _on_save(self, _evt=None):
        """Validate and save."""
        # Validate code
        code_val = self.code.get().strip().upper()
        if not code_val:
            messagebox.showwarning(
                self.engine.app_title,
                "Code is required.",
                parent=self,
            )
            return

        # Validate description
        desc_val = self.description.get().strip()
        if not desc_val:
            messagebox.showwarning(
                self.engine.app_title,
                "Description is required.",
                parent=self,
            )
            return

        # Check for duplicate code
        sql = "SELECT action_id FROM actions WHERE code = ? LIMIT 1;"
        existing = self.engine.db.read(False, sql, (code_val,))
        if existing:
            current_id = self.selected_item.get("action_id") if self.selected_item else None
            if existing["action_id"] != current_id:
                messagebox.showwarning(
                    self.engine.app_title,
                    f"Code '{code_val}' already exists!",
                    parent=self,
                )
                return

        # Confirm save
        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.ask_to_save,
            parent=self,
        ):
            return

        # Build SQL
        args = self._get_values()

        if self.index is not None:
            # UPDATE
            sql = """
                UPDATE actions
                SET code = ?, description = ?, status = ?
                WHERE action_id = ?;
            """
            args.append(self.selected_item["action_id"])
        else:
            # INSERT
            sql = """
                INSERT INTO actions (code, description, status)
                VALUES (?, ?, ?);
            """

        last_id = self.engine.db.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            msg = self.engine.tools.get_database_error(err) if err else "Save failed."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        # Refresh parent
        self.parent._set_values()
        self.engine.events.notify("actions")
        self.on_cancel()

    def on_cancel(self, evt=None):
        """Close editor."""
        self.parent.focus_set()
        super().on_cancel(evt)
