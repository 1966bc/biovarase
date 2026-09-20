# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ui.child_view import ChildView


SQL_SUPPLIERS = (
    "SELECT supplier_id, description "
    "  FROM suppliers "
    " WHERE status = 1 "
    " ORDER BY description;"
)


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="control")

        self.index = index

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Form state
        self.description = tk.StringVar()
        self.reference = tk.StringVar()
        self.status = tk.BooleanVar()

        self.dict_suppliers = {}
        self.selected_item = None

        # Layout root columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        # Left: fields
        left = ttk.Frame(self.frm_main, style="App.TFrame")
        left.grid(row=0, column=0, sticky=tk.NS, **pad)
        left.columnconfigure(1, weight=1)

        row = 0
        col = 1

        ttk.Label(left, text="Supplier:").grid(row=row, column=0, sticky=tk.W)
        self.cbSuppliers = ttk.Combobox(left, state="readonly")
        self.cbSuppliers.grid(row=row, column=col, sticky="ew", **pad)

        row += 1
        ttk.Label(left, text="Description:").grid(row=row, column=0, sticky=tk.W)
        self.txDescription = ttk.Entry(left, textvariable=self.description)
        self.txDescription.grid(row=row, column=col, sticky="ew", **pad)

        row += 1
        ttk.Label(left, text="Reference:").grid(row=row, column=0, sticky=tk.W)
        self.txReference = ttk.Entry(left, textvariable=self.reference)
        self.txReference.grid(row=row, column=col, sticky="ew", **pad)

        row += 1
        ttk.Label(left, text="Status:").grid(row=row, column=0, sticky=tk.W)
        self.chkStatus = ttk.Checkbutton(
            left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        )
        self.chkStatus.grid(row=row, column=col, sticky="w", **pad)

        # Right: buttons
        right = ttk.Frame(self.frm_main, style="App.TFrame")
        right.grid(row=0, column=1, sticky=tk.NS, **pad)

        btn_save = ttk.Button(right, text="Save", style="App.TButton", command=self._on_save)
        btn_save.grid(row=0, column=0, sticky="ew", pady=4)

        btn_cancel = ttk.Button(right, text="Cancel", style="App.TButton", command=self.on_cancel)
        btn_cancel.grid(row=1, column=0, sticky="ew", pady=4)

    def on_open(self):

        self._set_suppliers()

        if self.index is not None:
            self.title("Update Control")
            self.selected_item = getattr(self.parent, "selected_item", None)
            self._set_values()
        else:
            self.title("Add Control")
            self.status.set(1)
            if self.cbSuppliers["values"]:
                self.cbSuppliers.current(0)
            self.description.set("")
            self.reference.set("")

        self.txDescription.focus()

    def _set_suppliers(self):
        """Fill the suppliers combobox using read_dict()."""
        self.dict_suppliers.clear()
        values = []

        rs = self.engine.read(True, SQL_SUPPLIERS, ()) or []
        for idx, row in enumerate(rs):
            supplier_id = row.get("supplier_id")
            description = row.get("description", "")
            self.dict_suppliers[idx] = supplier_id
            values.append(description)

        self.cbSuppliers["values"] = values

    def _set_values(self):
        """Copy values from selected_item (hybrid dict) into the form."""
        if not self.selected_item:
            return

        # Supplier: find combobox index by supplier_id
        try:
            supplier_id = self.selected_item["supplier_id"]
            key = next(
                k
                for k, v in self.dict_suppliers.items()
                if v == supplier_id
            )
            self.cbSuppliers.current(key)
        except (KeyError, StopIteration) as e:
            self.cbSuppliers.set("")

        # Fields
        self.description.set(self.selected_item.get("description", "") or "")
        self.reference.set(self.selected_item.get("reference", "") or "")
        # Default status to 1 if missing
        self.status.set(bool(self.selected_item.get("status", 1)))

    def _get_values(self):
        """Validate user input and return a list of values for SQL write."""
        idx = self.cbSuppliers.current()
        if idx < 0:
            messagebox.showwarning(
                self.engine.app_title,
                "Please select a supplier.",
                parent=self,
            )
            self.cbSuppliers.focus_set()
            raise ValueError("supplier-not-selected")

        desc = (self.description.get() or "").strip()
        if not desc:
            messagebox.showwarning(
                self.engine.app_title,
                "Description is required.",
                parent=self,
            )
            self.txDescription.focus_set()
            raise ValueError("description-required")

        return [
            self.dict_suppliers[idx],              # supplier_id
            desc,                                  # description
            (self.reference.get() or "").strip(),  # reference
            int(self.status.get()),                # status (0/1)
        ]

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_save(self, _evt=None):
        """Validate, build SQL and write the record."""
        # Global validation hook if present
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

        if not messagebox.askyesno(
            self.engine.app_title,
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            return

        try:
            args = self._get_values()
        except ValueError:
            return

        if self.index is not None:
            sql = self.engine.build_sql(self.parent.table, op="update")
            # Append primary key at the end of the parameter list
            args.append(self.selected_item["control_id"])
        else:
            sql = self.engine.build_sql(self.parent.table, op="insert")

        last_id = self.engine.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        self.parent.set_values()
        self._reselect_in_parent(last_id if self.index is None else None)
        self.on_cancel()

    def _reselect_in_parent(self, last_id=None):
        """
        UPDATE: re-select self.index.
        INSERT: select last_id (iid of the new record).
        """
        tree = self.parent.lstItems
        target = self.index if self.index is not None else last_id
        if target is None:
            return
        try:
            tree.see(target)
            tree.focus(target)
            tree.selection_set(target)
        except Exception as e:
            # Defensive: do not crash if iid is missing
            pass

    def on_cancel(self, evt=None):
        """Close the editor window."""
        super().on_cancel(evt)
