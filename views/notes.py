# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
#-----------------------------------------------------------------------------
"""
Notes master window.

This Toplevel shows all notes linked to the currently selected result
and opens the editor mask imported as `ui.UI`.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
import views.note as ui
from views.parent_view import ParentView

STATUS_ACTIVE = 1


class UI(ParentView):
    """Master window for managing notes of a selected result."""

    def __init__(self, parent):
        super().__init__(parent, name="notes")
        if self._reusing:
            return

        self.table = "notes"
        self.primary_key = "note_id"

        self.selected_item = None
        self.selected_test = None
        self.selected_batch = None
        self.selected_result = None
        self.child = None

        self.items = tk.StringVar(value="Items: 0")
        self.batch = tk.StringVar()
        self.description = tk.StringVar()
        self.result = tk.StringVar()
        self.received = tk.StringVar()

        self.bind("<Return>", self._on_item_activated)

        self._build_ui()
        self.show(on_screen=True)

    # --------------------------------------------------------------------- UI
    def _build_ui(self):
        """Build the complete master layout."""

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left: context info (test, batch, result, etc.)
        frm_left = ttk.Frame(
            frm_main,
            style="App.TFrame",
            relief=tk.GROOVE,
            padding=8,
        )
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=6, pady=6, expand=True)

        ttk.Label(frm_left, text=_("Batch:")).pack(side=tk.TOP, anchor=tk.W)
        ttk.Label(frm_left, textvariable=self.batch).pack(side=tk.TOP, anchor=tk.W)

        ttk.Label(frm_left, text=_("Description:")).pack(side=tk.TOP, anchor=tk.W)
        ttk.Label(frm_left, textvariable=self.description).pack(side=tk.TOP, anchor=tk.W)

        ttk.Label(frm_left, text=_("Result:")).pack(side=tk.TOP, anchor=tk.W)
        ttk.Label(frm_left, textvariable=self.result).pack(side=tk.TOP, anchor=tk.W)

        ttk.Label(frm_left, text=_("Received:")).pack(side=tk.TOP, anchor=tk.W)
        ttk.Label(frm_left, textvariable=self.received).pack(side=tk.TOP, anchor=tk.W)

        # Middle: Treeview with notes
        frm_middle = ttk.Frame(
            frm_main,
            style="App.TFrame",
            relief=tk.GROOVE,
            padding=8,
        )
        frm_middle.pack(side=tk.LEFT, fill=tk.BOTH, padx=6, pady=6, expand=True)

        ttk.Label(
            frm_middle,
            style="App.TLabel",
            textvariable=self.items,
        ).pack(fill=tk.X, padx=2, pady=2)

        cols_notes = ("description", "modified")
        self.lstItems = ttk.Treeview(frm_middle, columns=cols_notes, show="headings")

        self.lstItems.column("description", width=180, minwidth=180, anchor=tk.W, stretch=True)
        self.lstItems.heading("description", text=_("Description"), anchor=tk.W)

        self.lstItems.column("modified", width=140, minwidth=140, anchor=tk.W, stretch=True)
        self.lstItems.heading("modified", text=_("Modified"), anchor=tk.W)

        sb_notes = ttk.Scrollbar(frm_middle, orient=tk.VERTICAL, command=self.lstItems.yview)
        self.lstItems.configure(yscrollcommand=sb_notes.set)
        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_notes.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.tag_configure("status", background=self.engine.get_rgb(211, 211, 211))

        self.lstItems.bind("<<TreeviewSelect>>", self._on_item_selected)
        self.lstItems.bind("<Double-1>", self._on_item_activated)

        # Right: Buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        self.engine.add_button(frm_buttons, _("Add"), self._on_add, "<Alt-a>", self)
        self.engine.add_button(frm_buttons, _("Update"), self._on_item_activated, "<Alt-u>", self)
        self.engine.add_button(frm_buttons, _("Close"), self.on_cancel, "<Alt-c>", self)

    # ----------------------------------------------------------------- Public
    def on_open(self):
        """
        Configure title, load parent context, reload data and center the window.
        This method MUST always be called after construction.
        """
        # Parent MUST provide dicts (PROJECT_RULES: use read_dict).
        self.selected_test = getattr(self.parent, "selected_test", None)
        self.selected_batch = getattr(self.parent, "selected_batch", None)
        self.selected_result = getattr(self.parent, "selected_result", None)

        # Test description in title
        test_name = ""
        if isinstance(self.selected_test, dict):
            test_name = self.selected_test.get("description", "")
        self.title(f"Notes - {test_name}" if test_name else "Notes management")

        # Batch: lot_number + description
        if isinstance(self.selected_batch, dict):
            self.batch.set(self.selected_batch.get("lot_number", ""))
            self.description.set(self.selected_batch.get("description", ""))
        else:
            self.batch.set("")
            self.description.set("")

        # Result: numeric value + received datetime
        if isinstance(self.selected_result, dict):
            value = self.selected_result.get("result")
            received = self.selected_result.get("received")

            if value is not None:
                try:
                    self.result.set(round(float(value), 3))
                except (TypeError, ValueError):
                    self.result.set("")
            else:
                self.result.set("")

            try:
                if hasattr(received, "strftime"):
                    self.received.set(received.strftime("%d-%m-%Y"))
                else:
                    self.received.set("")
            except Exception:
                self.received.set("")
        else:
            self.result.set("")
            self.received.set("")

        self._set_values()

    def _set_values(self):
        """
        Reload Treeview data for the current result.

        PROJECT_RULES:
        - result_id MUST be obtained from a dict (read_dict).
        - No positional indexing on database rows.
        """
        if not isinstance(self.selected_result, dict):
            # No valid result bound → clear list
            self.engine.clear_treeview(self.lstItems)
            self.items.set("Items: 0")
            self.selected_item = None
            return

        result_id = self.selected_result.get("result_id")
        if result_id is None:
            self.engine.clear_treeview(self.lstItems)
            self.items.set("Items: 0")
            self.selected_item = None
            return

        sql = """
            SELECT
                notes.note_id,
                actions.description AS description,
                notes.modified      AS modified,
                notes.status        AS status
            FROM notes
            INNER JOIN actions
                ON notes.action_id = actions.action_id
            WHERE notes.result_id = ?;
        """

        rs = self.engine.read(True, sql, (result_id,)) or []

        # Clear current content
        self.engine.clear_treeview(self.lstItems)

        count = 0
        for row in rs:
            status = int(row["status"])
            tags = ("status",) if status != STATUS_ACTIVE else ()
            self.lstItems.insert(
                "",
                tk.END,
                iid=str(row["note_id"]),
                text=str(row["note_id"]),
                values=(
                    row["description"],
                    row["modified"],
                ),
                tags=tags,
            )
            count += 1

    
        self.items.set(f"Items: {count}")

        self.selected_item = None

    # --------------------------------------------------------- Tree callbacks
    def _on_item_selected(self, _evt=None):
        """Update self.selected_item with the current note (dict)."""
        sel = self.lstItems.selection()
        if not sel:
            self.selected_item = None
            return

        # Treeview iid is NOT a DB row; PROJECT_RULES are about SQL rows.
        note_id = sel[0]

        # get_selected returns a hybrid dict; we only use named keys.
        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            note_id,
        )

    def _on_item_activated(self, _evt=None):
        """
        Activate current selection:
        - if a note is selected, open the editor on that note
        - otherwise, show warning.
        """
        sel = self.lstItems.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        self._on_item_selected()
        self.engine.open_child(self, ui.UI, index=sel[0])

    def _on_add(self, _evt=None):
        """Open the editor for a new note."""
        self.engine.open_child(self, ui.UI, index=None)

    # -------------------------------------------------------------- Lifecycle
    def on_cancel(self, _evt=None):
        """Close window safely."""
        super().on_cancel()
