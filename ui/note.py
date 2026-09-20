# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
#-----------------------------------------------------------------------------
"""
Note editor window.

This Toplevel is the editor (child window) for a single note
linked to a QC result. It is opened by the master window
`ui.notes.UI`.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
from calendarium import Calendarium
from ui.child_view import ChildView

# Role constants
ROLE_APP_ADMIN = 0


class UI(ChildView):
    """Editor window for a single note (insert / update)."""

    def __init__(self, parent, index=None):
        """
        :param parent: master window (ui.notes.UI or ui.daily_validation.UI)
        :param index:  note_id (Treeview iid) or None for INSERT
        """
        super().__init__(parent, name="note")

        self.index = index            # Treeview iid (note_id) or None
        self.can_edit = True          # Permission flag

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Model variables
        self.description = tk.StringVar()
        self.status = tk.BooleanVar()

        # Mapping Combobox index → action_id
        self.dict_actions = {}

        # References to parent selections
        self.selected_test = None
        self.selected_batch = None
        self.selected_result = None
        self.selected_note = None

        # Layout root columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()


    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        pad = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        # Left: fields
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **pad)
        frm_left.columnconfigure(1, weight=1)

        r = 0
        c = 1

        ttk.Label(frm_left, text=_("Action:")).grid(row=r, column=0, sticky=tk.W)
        self.cbActions = ttk.Combobox(frm_left, state="readonly")
        self.cbActions.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(frm_left, text=_("Description:")).grid(row=r, column=0, sticky=tk.W)
        self.txDescription = ttk.Entry(frm_left, textvariable=self.description)
        self.txDescription.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(frm_left, text=_("Modified:")).grid(row=r, column=0, sticky=tk.W)

        # Safe fallback background for Calendarium
        try:
            if hasattr(self.engine, "get_base_bg_color_hex"):
                bg = self.engine.get_base_bg_color_hex()
            else:
                bg = self.engine.get_rgb(240, 240, 237)
        except Exception as e:
            bg = "#d9d9d9"

        self.modified = Calendarium(frm_left, "", base_bg_color=bg)
        self.modified.grid(row=r, column=c, sticky=tk.W)

        r += 1
        ttk.Label(frm_left, text=_("Status:")).grid(row=r, column=0, sticky=tk.W)
        self.chkStatus = ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        )
        self.chkStatus.grid(row=r, column=c, sticky="w", **pad)

        # Creator info (shown only for existing notes)
        r += 1
        self.lbl_creator = ttk.Label(frm_left, text="", foreground="gray")
        self.lbl_creator.grid(row=r, column=0, columnspan=2, sticky=tk.W, **pad)

        # Right: buttons
        right = ttk.Frame(self.frm_main, style="App.TFrame")
        right.grid(row=0, column=1, sticky=tk.NS, **pad)

        self.btn_save = ttk.Button(
            right,
            text=_("Save"),
            style="App.TButton",
            command=self._on_save,
        )
        self.btn_save.grid(row=0, column=0, sticky="ew", pady=4)

        btn_cancel = ttk.Button(
            right,
            text=_("Cancel"),
            style="App.TButton",
            command=self.on_cancel,
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", pady=4)

    # --------------------------------------------------------------- Public --
    def on_open(self):
        """
        Initialize editor using parent selections.

        The master window (ui.notes.UI or ui.daily_validation.UI) is expected to expose:
            - selected_test
            - selected_batch
            - selected_result
            - selected_item (current note as hybrid dict for UPDATE)
        """
        self.selected_test = getattr(self.parent, "selected_test", None)
        self.selected_batch = getattr(self.parent, "selected_batch", None)
        self.selected_result = getattr(self.parent, "selected_result", None)
        self.selected_note = getattr(self.parent, "selected_item", None)

        self._set_actions()

        if self.index is not None and self.selected_note:
            msg = _("Update Note")
            self._set_values_from_selected_note()
            self._check_edit_permission()
        else:
            msg = _("Add Note")
            self.status.set(1)
            self.modified.set_today()
            self.lbl_creator.config(text="")
            self.can_edit = True

        self.title(msg)
        self.cbActions.focus()

    def _check_edit_permission(self):
        """Check if current user can edit this note."""
        self.can_edit = True
        current_user_id = self.engine.log_user.get("user_id")
        current_role = self.engine.log_user.get("role")

        # Admin can always edit
        if current_role == ROLE_APP_ADMIN:
            self.can_edit = True
            return

        # Get note creator
        created_by = self.selected_note.get("created_by")

        if created_by is None:
            # Old notes without creator - allow editing
            self.can_edit = True
            self.lbl_creator.config(text=_("Created by: Unknown"))
            return

        # Check if current user is the creator
        if created_by == current_user_id:
            self.can_edit = True
        else:
            self.can_edit = False
            # Disable editing controls
            self.cbActions.config(state="disabled")
            self.txDescription.config(state="disabled")
            self.chkStatus.config(state="disabled")
            self.btn_save.config(state="disabled")

        # Show creator name
        try:
            sql = "SELECT first_name, last_name FROM users WHERE user_id = ?"
            user = self.engine.read(False, sql, (created_by,))
            if user:
                creator_name = f"{user['first_name']} {user['last_name']}"
                if not self.can_edit:
                    self.lbl_creator.config(
                        text=_("Created by: {0} (read-only)").format(creator_name),
                        foreground="orange"
                    )
                else:
                    self.lbl_creator.config(
                        text=_("Created by: {0}").format(creator_name),
                        foreground="gray"
                    )
        except Exception:
            pass

    # ------------------------------------------------------ Data loading ----
    def _set_actions(self):
        """
        Load enabled actions into Combobox and build index → action_id map.

        PROJECT_RULES:
        - use read_dict()
        - no positional indexing on SQL rows
        """
        sql = """
            SELECT action_id, description
            FROM actions
            WHERE status = 1
            ORDER BY description ASC;
        """
        rs = self.engine.read(True, sql, ()) or []

        self.dict_actions = {}
        voices = []

        for index, row in enumerate(rs):
            self.dict_actions[index] = row.get("action_id")
            # Translate action description for display
            voices.append(_(row.get("description", "")))

        self.cbActions["values"] = voices
        if voices:
            self.cbActions.current(0)

    def _set_values_from_selected_note(self):
        """Populate fields from parent.selected_note (hybrid dict)."""
        note = self.selected_note
        if not note:
            return

        # action_id → select correct index in Combobox
        action_id = note.get("action_id")
        for idx, aid in self.dict_actions.items():
            if aid == action_id:
                self.cbActions.current(idx)
                break

        # Description
        self.description.set(note.get("description", ""))

        # Modified date
        modified = note.get("modified")
        try:
            if modified is not None:
                self.modified.set_from_datetime(modified)
            else:
                self.modified.set_today()
        except Exception as e:
            self.modified.set_today()

        # Status
        status_val = note.get("status", 1)
        self.status.set(1 if status_val else 0)

    # ------------------------------------------------------ Data helpers ----
    def _get_result_id(self):
        """Return the result_id from selected_result (dict or tuple)."""
        if self.selected_result is None:
            return None

        if isinstance(self.selected_result, dict):
            return self.selected_result.get("result_id")

        # legacy tuple support (until we refactor upstream)
        try:
            return self.selected_result[0]
        except Exception as e:
            return None

    def _get_values(self):
        """
        Collect current form data in the order required by INSERT / UPDATE:

            result_id, action_id, description, modified (date), status
        """
        result_id = self._get_result_id()
        if result_id is None:
            return None

        action_idx = self.cbActions.current()
        if action_idx < 0:
            return None

        action_id = self.dict_actions.get(action_idx)
        if action_id is None:
            return None

        modified_date = self.modified.get_date()
        if modified_date is None:
            return None

        return (
            result_id,
            action_id,
            self.description.get().strip(),
            modified_date,
            int(self.status.get()),
        )

    # ------------------------------------------------------------ Save ------
    def _on_save(self, _evt=None):
        """Validate, confirm and write data to the `notes` table."""
        # Check permission
        if not self.can_edit:
            messagebox.showwarning(
                self.engine.app_title,
                _("You don't have permission to edit this note."),
                parent=self,
            )
            return

        # Generic field validation
        if not self.engine.on_fields_control(self):
            return

        # Calendarium validation
        if not self.modified.is_valid:
            messagebox.showwarning(
                self.engine.app_title,
                _("Invalid date."),
                parent=self,
            )
            return

        values = self._get_values()
        if values is None:
            messagebox.showwarning(
                self.engine.app_title,
                _("Missing or invalid data."),
                parent=self,
            )
            return

        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.ask_to_save,
            parent=self,
        ):
            return

        # --- Custom SQL for INSERT/UPDATE with created_by support ---
        try:
            result_id, action_id, description, modified_date, status = values
            user_id = self.engine.log_user.get("user_id")

            if self.index is not None:
                # UPDATE - don't change created_by
                sql = """
                    UPDATE notes
                    SET action_id = ?,
                        description = ?,
                        modified = ?,
                        status = ?
                    WHERE note_id = ?
                """
                args = (action_id, description, modified_date, status, int(self.index))
            else:
                # INSERT - set created_by and created_at
                sql = """
                    INSERT INTO notes
                    (result_id, action_id, description, modified, status, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, NOW())
                """
                args = (result_id, action_id, description, modified_date, status, user_id)

            last_id = self.engine.write(sql, args)
            if last_id is None:
                err = self.engine.last_write_error
                if err:
                    msg = self.engine.get_user_friendly_db_error(err)
                else:
                    msg = _("Save failed.")
                messagebox.showerror(self.engine.app_title, msg, parent=self)
                return

            # Notify observers (daily_validation, main, etc.)
            note_id = last_id if self.index is None else int(self.index)
            self.engine.notify("note_changed", note_id)

            # Reload master Treeview (if parent has _set_values, e.g. notes.py)
            if hasattr(self.parent, "_set_values"):
                self.parent._set_values()

            # Reseleziona la nota aggiornata
            if self.index is not None:
                try:
                    self.parent.lstItems.selection_set(self.index)
                    self.parent.lstItems.see(self.index)
                except Exception:
                    pass

            self.on_cancel()

        except Exception as e:
            # Log secondo PROJECT_RULES
            self.engine.on_log(
                "_on_save",
                e,
                type(e),
                __import__(__name__),
                caller=type(self).__name__,
            )
            messagebox.showerror(
                self.engine.app_title,
                _("Error while saving data.") + "\n" + _("Please check the log file."),
                parent=self,
            )

    # ---------------------------------------------------------- Lifecycle ---
    def on_cancel(self, evt=None):
        """Close the editor window."""
        super().on_cancel(evt)
