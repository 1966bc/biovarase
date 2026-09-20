# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ui.child_view import ChildView


class UI(ChildView):

    def __init__(self, parent, index=None):
        super().__init__(parent, name="equipment")

        self.index = index  # None → INSERT, pk → UPDATE

        # Selected equipment row (hybrid dict from engine.get_selected)
        self.selected_item = None

        # Tk variables
        self.description = tk.StringVar()
        self.status = tk.BooleanVar(value=True)

        # Combobox index → supplier_id mapping
        self.dict_suppliers = {}

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Root grid config (two columns: form + buttons)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # Build UI
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    def _build_ui(self):

        paddings = {"padx": 5, "pady": 5}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Left form (labels/entries)
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky="nswe", **paddings)

        r, c = 0, 1

        ttk.Label(frm_left, text="Suppliers:").grid(row=r, column=0, sticky=tk.W)
        self.cbSuppliers = ttk.Combobox(frm_left, state="readonly")
        self.cbSuppliers.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Description:").grid(row=r, column=0, sticky=tk.W)
        self.txtDescription = ttk.Entry(frm_left, textvariable=self.description)
        self.txtDescription.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, column=0, sticky=tk.W)
        chk = ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        )
        chk.grid(row=r, column=1, sticky=tk.W, **paddings)

        # Make entry column expand inside frm_left
        frm_left.columnconfigure(0, weight=0)
        frm_left.columnconfigure(1, weight=1)

        # Right: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        btn_save = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self._on_save,
        )
        btn_save.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        btn_cancel = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Keep buttons the same width
        frm_buttons.columnconfigure(0, weight=1)

    def on_open(self):

        self._set_suppliers()

        if self.index is not None:
            self.title("Update Equipment")
            try:
                self.selected_item = self.engine.get_selected(
                    self.parent.table,
                    self.parent.primary_key,
                    int(self.index),
                )
            except Exception as exc:
                try:
                    self.engine.on_log(
                        "equipment.on_open:get_selected",
                        exc,
                        type(exc),
                        sys.modules[__name__],
                    )
                except Exception as e:
                    pass
                self.selected_item = None

            if self.selected_item:
                self._set_values()
        else:
            self.title("Add Equipment")
            self.status.set(True)
            # Default to "Not Assigned" supplier if present
            try:
                for idx, sid in self.dict_suppliers.items():
                    if int(sid) == 0:
                        self.cbSuppliers.current(idx)
                        break
            except Exception as e:
                pass

        # Focus description field by default
        try:
            self.txtDescription.focus_set()
            self.txtDescription.selection_range(0, "end")
        except Exception as e:
            pass

    def _set_suppliers(self):
        """Fill suppliers combobox with all active suppliers plus a 'Not Assigned' row.

        dict_suppliers: combobox index → supplier_id
        """
        self.dict_suppliers.clear()
        values = []

        sql = """
            SELECT supplier_id, description
            FROM suppliers
            WHERE status = 1
            ORDER BY description ASC;
        """

        try:
            rows = self.engine.read(True, sql, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "equipment._set_suppliers:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        # Append virtual "Not Assigned" supplier (id = 0)
        rows.append({"supplier_id": 0, "description": "Not Assigned"})

        for idx, row in enumerate(rows):
            supplier_id = int(row["supplier_id"])
            description = row["description"]
            self.dict_suppliers[idx] = supplier_id
            values.append(description)

        self.cbSuppliers["values"] = values

    def _set_values(self):

        s = self.selected_item
        if not s:
            return

        # Supplier
        try:
            supplier_id = int(s.get("supplier_id", 0))
            for idx, sid in self.dict_suppliers.items():
                if sid == supplier_id:
                    self.cbSuppliers.current(idx)
                    break
        except Exception as e:
            # Non blocking: supplier may simply not be found
            pass

        # Description
        try:
            self.description.set(s.get("description", "") or "")
        except Exception as e:
            self.description.set("")

        # Status
        try:
            self.status.set(int(s.get("status", 1)) == 1)
        except Exception as e:
            self.status.set(True)

    def _get_values(self):
        """Collect current form values as a list suitable for SQL arguments.

        Returns:
            [supplier_id, description, status_int]
        """
        # Supplier: if nothing selected use "Not Assigned" (id = 0)
        try:
            idx = self.cbSuppliers.current()
            if idx < 0:
                supplier_id = 0
            else:
                supplier_id = self.dict_suppliers.get(idx, 0)
        except Exception as e:
            supplier_id = 0

        description = self.description.get().strip()
        status_int = int(bool(self.status.get()))

        return [supplier_id, description, status_int]

    def _on_save(self, _evt=None):

        title = self.engine.app_title

        # 1) Optional global validation hook
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, title) is False:
                return

        # 1b) Description validation (required + duplicates)
        if self._check_description() == 0:
            return

        # 2) Confirmation dialog
        if not messagebox.askyesno(
            title,
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            messagebox.showinfo(
                title,
                getattr(self.engine, "abort", "Abort."),
                parent=self,
            )
            return

        # 3) Collect values
        args = self._get_values()

        # 4) Build SQL
        if self.index is not None:
            # UPDATE path → append primary key (equipment_id) at the end
            sql = self.engine.build_sql(self.parent.table, op="update")
            pk = int(self.index)
            args.append(pk)
            target_pk = pk
        else:
            # INSERT path
            sql = self.engine.build_sql(self.parent.table, op="insert")
            target_pk = None

        # 5) Execute write
        last_id = self.engine.write(sql, tuple(args))
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(title, msg, parent=self)
            return

        # 6) Reload parent list
        self.parent.set_values()

        # Determine which PK we need to reselect
        if target_pk is None and last_id is not None:
            target_pk = int(last_id)

        self._reselect_in_parent(target_pk)

        # 7) Cross-window refresh: equipments → workstations
        try:
            self.engine.refresh_windows_for_table(self.parent.table)
        except Exception:
            pass

        self.on_cancel()

    def _reselect_in_parent(self, target_pk):
        """Reselect item in parent using dict_items (index → pk) after save."""
        if target_pk is None:
            return

        try:
            lst_index = next(
                (k for k, v in self.parent.dict_items.items() if v == target_pk),
                None,
            )
            if lst_index is None:
                return

            self.parent.lstItems.see(lst_index)
            self.parent.lstItems.selection_set(lst_index)
            self.parent.on_item_selected()
        except Exception as exc:
            try:
                self.engine.on_log(
                    "equipment._reselect_in_parent",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass

    def _check_description(self):
        """Validate and normalize the description field.

        Returns:
            1 if valid, 0 otherwise.

        Checks:
            - Non-empty description
            - No duplicates (case-insensitive, whitespace-normalized)
            - Updates field with normalized value on success
        """
        # Field metadata (explicitly from parent to show external origin)
        label_text = "Description:".rstrip(":")
        desc_field = "description"
        table = self.parent.table
        pk_field = self.parent.primary_key

        raw = self.description.get()
        norm = self.engine.get_clean_text(raw, compress=True)

        # Empty check
        if not norm:
            messagebox.showwarning(
                self.engine.app_title,
                "Description is required.",
                parent=self,
            )
            return 0

        # UPDATE mode: skip DB duplicate check if description has not changed
        if self.index is not None and self.selected_item:
            current = self.selected_item.get(desc_field, "")
            current_norm = self.engine.get_clean_text(current, compress=True)

            if norm.casefold() == current_norm.casefold():
                # Same logical value, just apply normalization
                self.description.set(norm)
                return 1

        # Duplicate check in database
        sql = (
            f"SELECT {pk_field} "
            f"FROM {table} "
            f"WHERE {desc_field} = ? "
            "LIMIT 1;"
        )

        try:
            row = self.engine.read(False, sql, (norm,))
        except Exception as exc:
            try:
                self.engine.on_log(
                    "equipment._check_description:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass

            messagebox.showerror(
                self.engine.app_title,
                f"Database error:\n{exc}",
                parent=self,
            )
            return 0

        # If duplicate found, ensure it is not the current record
        if row:
            found_id = row[pk_field]
            current_id = (
                self.selected_item.get(pk_field)
                if self.index is not None and self.selected_item
                else None
            )

            if self.index is None or found_id != current_id:
                messagebox.showwarning(
                    self.engine.app_title,
                    f"{label_text} '{norm}' already exists!",
                    parent=self,
                )
                return 0

        # All checks passed → update field with normalized value
        self.description.set(norm)
        return 1

    def on_cancel(self, evt=None):
        """Close the editor window."""
        super().on_cancel(evt)
