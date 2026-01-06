# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   ver MMXXV (refactor: dict-based, read_dict, PROJECT_RULES)
#-----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from views.child_view import ChildView


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="site")

        self.index = index

        # State
        self.selected_site: dict | None = None

        # Vars
        self.status = tk.BooleanVar(value=True)

        # Dictionaries for combobox mapping
        self.dict_companies: dict[int, int] = {}  # idx -> supplier_id (company)
        self.dict_sites: dict[int, int] = {}      # idx -> supplier_id (site)

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    def _build_ui(self):
        paddings = {"padx": 6, "pady": 6}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=10)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        self.frm_main.columnconfigure(0, weight=0)
        self.frm_main.columnconfigure(1, weight=1)

        r = 0
        ttk.Label(self.frm_main, text="Company:").grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.cbCompanies = ttk.Combobox(self.frm_main, state="readonly")
        self.cbCompanies.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(self.frm_main, text="Site:").grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.cbSites = ttk.Combobox(self.frm_main, state="readonly")
        self.cbSites.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(self.frm_main, text="Status:").grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        ttk.Checkbutton(
            self.frm_main,
            variable=self.status,
            onvalue=1,
            offvalue=0,
        ).grid(row=r, column=1, sticky=tk.W, **paddings)

        # Buttons
        btns = ttk.Frame(self.frm_main, style="App.TFrame")
        btns.grid(row=0, column=2, rowspan=3, sticky="ns", padx=4, pady=4)

        btn_save = ttk.Button(
            btns,
            text="Save",
            command=self._on_save,
            underline=0,
            style="App.TButton",
        )
        btn_save.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        btn_cancel = ttk.Button(
            btns,
            text="Cancel",
            command=self.on_cancel,
            underline=0,
            style="App.TButton",
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

    # ------------------------------------------------------------- open
    def on_open(self):
        """Public entry called by master (INSERT/UPDATE based on self.index)."""
        self._set_companies()
        self._set_sites()

        if self.index is not None:
            # UPDATE: load dict from DB
            try:
                self.selected_site = self.engine.get_selected(
                    self.parent.table,
                    self.parent.primary_key,
                    int(self.index),
                )
            except Exception as exc:
                try:
                    self.engine.on_log(
                        "site.on_open:get_selected",
                        exc,
                        type(exc),
                        sys.modules[__name__],
                    )
                except Exception as e:
                    pass
                self.selected_site = None

            self._set_values()
            title = "Update Site"
        else:
            # INSERT
            self.status.set(True)
            self.selected_site = None
            title = "Insert Site"

        self.title(title)
        try:
            self.cbCompanies.focus_set()
        except Exception as e:
            pass

    def _set_companies(self):
        """Fill companies combobox from suppliers (master)."""
        self.dict_companies.clear()
        values: list[str] = []

        sql = """
            SELECT
                supplier_id,
                description
            FROM suppliers
            WHERE status = 1
            ORDER BY description ASC;
        """
        try:
            rows = self.engine.read(True, sql, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "site._set_companies:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        for idx, row in enumerate(rows):
            supplier_id = row.get("supplier_id")
            desc = row.get("description", "") or ""
            if supplier_id is None:
                continue
            self.dict_companies[idx] = int(supplier_id)
            values.append(desc)

        self.cbCompanies["values"] = values

    def _set_sites(self):
        """Fill sites combobox from suppliers (composition/site name)."""
        self.dict_sites.clear()
        values: list[str] = []

        sql = """
            SELECT
                supplier_id,
                description
            FROM suppliers
            WHERE status = 1
            ORDER BY description ASC;
        """
        try:
            rows = self.engine.read(True, sql, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "site._set_sites:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        for idx, row in enumerate(rows):
            supplier_id = row.get("supplier_id")
            desc = row.get("description", "") or ""
            if supplier_id is None:
                continue
            self.dict_sites[idx] = int(supplier_id)
            values.append(desc)

        self.cbSites["values"] = values

    def _set_values(self):
        """
        Populate widgets from self.selected_site (hybrid dict from Engine).

        Expected keys in sites:
            - supplier_id (company)
            - comp_id     (site)
            - status
        """
        s = self.selected_site
        if not s:
            return

        # Company: sites.supplier_id
        try:
            company_supplier_id = int(s.get("supplier_id"))
            for k, v in self.dict_companies.items():
                if v == company_supplier_id:
                    self.cbCompanies.current(k)
                    break
        except Exception as e:
            pass

        # Site: sites.comp_id
        try:
            site_supplier_id = int(s.get("comp_id"))
            for k, v in self.dict_sites.items():
                if v == site_supplier_id:
                    self.cbSites.current(k)
                    break
        except Exception as e:
            pass

        # Status
        try:
            self.status.set(int(s.get("status", 1)) == 1)
        except Exception as e:
            self.status.set(True)

    def _get_values(self):
        """Collect current values, validating combobox selections."""
        if self.cbCompanies.current() < 0:
            raise ValueError("Select a Company.")
        if self.cbSites.current() < 0:
            raise ValueError("Select a Site.")

        return [
            self.dict_companies[self.cbCompanies.current()],  # supplier_id (company)
            self.dict_sites[self.cbSites.current()],          # comp_id (site)
            int(bool(self.status.get())),
        ]

    def _on_save(self, _evt=None):
        """
        INSERT or UPDATE a record in the `sites` table.

        Behavior:
        - Validates widget fields (via Engine hook)
        - Confirms user intention
        - Performs SQL INSERT or UPDATE
        - Refreshes the parent window (`sites.py`)
        - If the LABS window is open, refreshes its tree as required by PROJECT_RULES
        """

        title = self.engine.app_title

        # 1) Optional global validation hook (Engine API)
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, title) is False:
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

        # 3) Collect field values (may raise ValueError)
        try:
            args = self._get_values()
        except ValueError as ve:
            messagebox.showwarning(title, str(ve), parent=self)
            return

        try:
            # 4) Build SQL and write to database
            if self.index is not None:
                # UPDATE mode
                sql = self.engine.build_sql(self.parent.table, op="update")
                pk = int(self.index)
                args.append(pk)
                self.engine.write(sql, args)
                pk_to_select = pk
            else:
                # INSERT mode
                sql = self.engine.build_sql(self.parent.table, op="insert")
                last_id = self.engine.write(sql, args)
                pk_to_select = int(last_id)

            # 5) Notify parent window (sites master) to refresh and reselect the edited row
            if hasattr(self.parent, "reload_and_reselect"):
                self.parent.reload_and_reselect(pk_to_select)
            elif hasattr(self.parent, "on_open"):
                self.parent.on_open()

            # 6) Cross-window update for LABS window (PROJECT_RULES)
            #    If the LABS window is open, we MUST refresh its tree.
            try:
                win = self.engine.dict_instances.get("labs")
            except Exception as e:
                win = None

            if win is not None:
                try:
                    if win.winfo_exists():
                        # Reload the treeview in LABS (company → hospitals)
                        win._load_tree()
                except Exception as e:
                    # Cross-window updates MUST NOT break the save process
                    pass

            # 7) Close this editor window
            self.on_cancel()

        except Exception as exc:
            # Log errors safely (logging must not break the UI)
            try:
                self.engine.on_log(
                    "site._on_save:write",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass

            messagebox.showerror(title, f"Save error:\n{exc}", parent=self)


    def on_cancel(self, evt=None):
        """Close dialog."""
        super().on_cancel(evt)
