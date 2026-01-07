# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Generic single-field + status editor for simple lookup tables
# (e.g. units, actions, categories, ...)
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import _
from views.child_view import ChildView


class Editor(ChildView):
    """
    Generic editor for tables with the following structure:

        pk_field   : primary key (e.g. unit_id, action_id)
        desc_field : description field (e.g. description)
        status     : tinyint(1) active/inactive

    The parent is expected to provide:
        - .table        : table name (string)
        - .lstItems     : Listbox widget
        - .dict_items   : dict {listbox_index: pk_value}
        - .selected_item: dict with at least {pk_field, desc_field, status}
        - ._set_values(): method to refresh listbox data
        - .on_item_selected(): method to refresh details

    Parameters:
        parent      : parent window (Toplevel or Tk)
        index       : None for INSERT, int for UPDATE
        table       : table name in the database
        pk_field    : primary key column name
        desc_field  : description column name
        label_text  : human-friendly label for UI/messages (e.g. "Unit")
        ui_name     : name for the Toplevel (e.g. "unit", "action")
    """

    def __init__(
        self,
        parent,
        index=None,
        *,
        table: str,
        pk_field: str,
        desc_field: str = "description",
        label_text: str = "Item",
        ui_name: str = "item",
    ):
        super().__init__(parent, name=ui_name)

        self.index = index               # None -> INSERT mode; not-None -> UPDATE
        self.selected_item = None        # will be filled in UPDATE mode

        # Metadata
        self.table = table
        self.pk_field = pk_field
        self.desc_field = desc_field
        self.label_text = label_text     # e.g. "Unit", "Action", "Category"

        # Key bindings
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Form variables
        self.description = tk.StringVar()
        self.status = tk.BooleanVar()

        # Grid configuration
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # Build UI and position window
        self._build_ui()
        self.show()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        paddings = {"padx": 8, "pady": 8}

        # Main frame
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        # Left form (labels/entries)
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky="ns", **paddings)

        # Description field
        r = 0
        ttk.Label(frm_left, text=f"{self.label_text}:").grid(
            row=r,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )
        self.txDescription = ttk.Entry(
            frm_left,
            textvariable=self.description,
        )
        self.txDescription.grid(row=r, column=1, sticky="ew", padx=5, pady=5)

        # Status checkbox
        r += 1
        ttk.Label(frm_left, text=_("Status:")).grid(
            row=r,
            column=0,
            sticky="w",
            padx=5,
            pady=5,
        )
        ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        ).grid(row=r, column=1, sticky="w", padx=5, pady=5)

        # Make entry column expand inside frm_left
        frm_left.columnconfigure(0, weight=0)
        frm_left.columnconfigure(1, weight=1)

        # Right side: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        ttk.Button(
            frm_buttons,
            style="App.TButton",
            text=_("Save"),
            underline=0,
            command=self._on_save,
        ).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(
            frm_buttons,
            style="App.TButton",
            text=_("Cancel"),
            underline=0,
            command=self.on_cancel,
        ).grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        frm_buttons.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # ENTRY POINT
    # ------------------------------------------------------------------
    def on_open(self):
        """
        Entry point called by the parent after instantiation.
        Decides INSERT vs UPDATE mode and populates fields accordingly.
        """
        if self.index is not None:
            # UPDATE mode
            self.title(f"{_('Update')} {self.label_text}")
            self.selected_item = getattr(self.parent, "selected_item", None)
            if self.selected_item is None:
                messagebox.showerror(
                    self.engine.app_title,
                    f"No {self.label_text.lower()} selected for update.",
                    parent=self,
                )
                self.on_cancel()
                return
            self._set_values()
        else:
            # INSERT mode
            self.title(f"{_('Add')} {self.label_text}")
            self.status.set(True)

        self._set_focus()

    def _set_focus(self):
        """Set keyboard focus on the description entry."""
        try:
            self.txDescription.focus_set()
            self.txDescription.selection_range(0, "end")
        except Exception as e:
            pass

    # ------------------------------------------------------------------
    # DATA BINDING
    # ------------------------------------------------------------------
    def _set_values(self):
        """
        Populate fields from the selected record (UPDATE mode only).
        """
        if not self.selected_item:
            return

        self.description.set(self.selected_item.get(self.desc_field, ""))
        self.status.set(bool(self.selected_item.get("status", 1)))

    def _get_values(self):
        """
        Return current form values as a list for SQL parameters.
        Order must match build_sql() expectations.
        """
        return [
            self.description.get().strip(),
            int(self.status.get()),
        ]

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------
    def _on_save(self, _evt=None):
        """
        Save workflow:
        1. Validate fields
        2. Check for duplicates
        3. Confirm with user
        4. Write to database (INSERT or UPDATE)
        5. Refresh parent list
        6. Reselect item in parent
        7. Close window
        """
        # Engine-level field validation (if available)
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(
                self.frm_main,
                self.engine.app_title,
            ) is False:
                return

        # Validate description and check duplicates
        if self._check_description() == 0:
            return

        # Confirm save
        if not messagebox.askyesno(
            self.engine.app_title,
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            messagebox.showinfo(
                self.engine.app_title,
                getattr(self.engine, "abort", "Operation aborted!"),
                parent=self,
            )
            return

        # Prepare SQL arguments
        args = self._get_values()

        # Build SQL with the application helper (insert/update)
        if self.index is not None:
            # UPDATE mode: append primary key at the end
            sql = self.engine.build_sql(self.table, op="update")
            args.append(self.selected_item[self.pk_field])
        else:
            # INSERT mode
            sql = self.engine.build_sql(self.table, op="insert")

        # Execute and refresh
        try:
            last_id = self.engine.write(sql, args)
            self.parent._set_values()  # Refresh parent list

            # Reselect appropriate item
            if self.index is None:
                # INSERT: select newly added item
                self._reselect_in_parent(last_id)
            else:
                # UPDATE: reselect same item
                self._reselect_in_parent()

            # Cross-window refresh via Engine/Controller dispatcher
            if hasattr(self.engine, "refresh_windows_for_table"):
                self.engine.refresh_windows_for_table(self.table)

            self.on_cancel()  # Close window

        except Exception as exc:
            messagebox.showerror(
                self.engine.app_title,
                f"{_('Save error:')}\n{exc}",
                parent=self,
            )

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------
    def _check_description(self):
        """
        Validate and normalize the description field.

        Returns:
            1 if valid, 0 otherwise.

        Checks:
        - Non-empty description
        - No duplicates (case-insensitive, whitespace-normalized)
        - Updates field with normalized value on success
        """
        raw = self.description.get()
        norm = self._normalize_desc(raw, compress=True)

        # Check if empty
        if not norm:
            messagebox.showwarning(
                self.engine.app_title,
                f"{self.label_text} {_('is required.')}",
                parent=self,
            )
            return 0

        # In UPDATE mode: skip duplicate check if description has not changed
        if self.index is not None:
            current = self.selected_item.get(self.desc_field, "")
            current_norm = self._normalize_desc(current, compress=True)
            if norm.casefold() == current_norm.casefold():
                # Same as original, just apply normalization
                self.description.set(norm)
                return 1

        # Check for duplicates in database (PROJECT_RULES: use read_dict)
        sql = (
            f"SELECT {self.pk_field} "
            f"FROM {self.table} "
            f"WHERE {self.desc_field} = ? "
            "LIMIT 1;"
        )
        try:
            row = self.engine.read(False, sql, (norm,))
        except Exception as exc:
            messagebox.showerror(
                self.engine.app_title,
                f"{_('Database error:')}\n{exc}",
                parent=self,
            )
            return 0

        # If duplicate found, check if it is not the current record
        if row:
            found_id = row[self.pk_field]
            current_id = (
                self.selected_item.get(self.pk_field)
                if self.index is not None
                else None
            )

            if self.index is None or found_id != current_id:
                messagebox.showwarning(
                    self.engine.app_title,
                    f"{self.label_text} '{norm}' {_('already exists!')}",
                    parent=self,
                )
                return 0

        # All checks passed: update field with normalized value
        self.description.set(norm)
        return 1

    def _normalize_desc(self, s, *, compress=False):
        """
        Normalize description string.

        Args:
            s: String to normalize
            compress: If True, collapse multiple spaces to a single space

        Returns:
            Normalized string
        """
        s = (s or "").strip()
        return " ".join(s.split()) if compress else s

    # ------------------------------------------------------------------
    # RESELECT IN PARENT
    # ------------------------------------------------------------------
    def _reselect_in_parent(self, last_id=None):
        """
        Reselect the appropriate item in the parent listbox after saving a record.

        Behavior:
        - UPDATE mode: reselects the same record using its primary key.
        - INSERT mode: selects the newly inserted record using last_id.
        - Fallback: if no valid PK exists, selects the last listbox row if available.
        """
        lb = self.parent.lstItems

        # 1) Determine target primary key
        if self.selected_item:
            target_pk = self.selected_item.get(self.pk_field)
        else:
            target_pk = last_id

        # 2) Resolve the corresponding listbox index
        if target_pk is None:
            size = lb.size()
            if size == 0:
                return
            lst_index = size - 1
        else:
            lst_index = next(
                (k for k, v in self.parent.dict_items.items() if v == target_pk),
                None,
            )
            if lst_index is None:
                return

        # 3) Select and activate the row in the listbox
        lb.focus_set()
        lb.see(lst_index)
        lb.selection_clear(0, "end")
        lb.selection_set(lst_index)
        lb.activate(lst_index)

        # Trigger parent handler to refresh detail display
        self.parent.on_item_selected()

    # ------------------------------------------------------------------
    # CLOSE
    # ------------------------------------------------------------------
    def on_cancel(self, evt=None):
        """Return focus to parent and close the editor."""
        self.parent.focus_set()
        super().on_cancel(evt)
