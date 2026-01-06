# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   ver MMXXV (refactor: child logic, handlers, layout)
#-----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class UI(tk.Toplevel):
    def __init__(self, parent, index=None):
        super().__init__(name="lab")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       
        # References
        self.parent = parent
        self.index = index  # None → INSERT, pk → UPDATE
        self.engine = self.nametowidget(".").engine

        # State
        self.selected_hospital = None   # sites.* row
        self.selected_lab = None        # labs.* row

        # Window configuration
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Hotkeys
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Vars
        self.description = tk.StringVar()
        self.status = tk.BooleanVar(value=True)

        # Combos mapping: index -> id
        self.dict_sites: dict[int, int] = {}   # combobox index -> site_id
        self.dict_users: dict[int, int] = {}   # combobox index -> user_id

        # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        paddings = {"padx": 6, "pady": 6}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        self.frm_main.columnconfigure(0, weight=0)
        self.frm_main.columnconfigure(1, weight=1)

        # Left form (labels/entries)
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky="nswe", **paddings)

        r, c = 0, 1

        ttk.Label(frm_left, text="Hospital:").grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.cbSites = ttk.Combobox(frm_left, state="readonly")
        self.cbSites.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Manager:").grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.cbUsers = ttk.Combobox(frm_left, state="readonly")
        self.cbUsers.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Laboratory:").grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.txtLab = ttk.Entry(frm_left, textvariable=self.description)
        self.txtLab.grid(row=r, column=1, sticky=tk.EW, **paddings)

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
            command=self._on_cancel,
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Keep buttons the same width
        frm_buttons.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ Lifecycle
    def on_open(self):
       
        # Context from parent
        self.selected_hospital = getattr(self.parent, "selected_hospital", None)
        self.selected_lab = getattr(self.parent, "selected_lab", None)

        # Load combos
        self._set_sites()
        self._set_managers()

        if self.index is not None:
            # ------------------------- UPDATE MODE -------------------------
            # Ensure we have a fresh labs.* row from DB
            try:
                self.selected_lab = self.engine.get_selected(
                    self.parent.table,
                    self.parent.primary_key,
                    int(self.index),
                )
            except Exception as e:
                self.selected_lab = None

            title = "Update Lab"
            self._set_values()
            try:
                self.txtLab.focus_set()
            except Exception as e:
                pass

        else:
            # ------------------------- INSERT MODE -------------------------
            title = "Insert Lab"
            # Preselect current hospital in combo using 'site_id'
            try:
                if isinstance(self.selected_hospital, dict):
                    current_site_id = int(self.selected_hospital.get("site_id"))
                    for idx, site_id in self.dict_sites.items():
                        if site_id == current_site_id:
                            self.cbSites.current(idx)
                            break
            except Exception as e:
                pass
            self.status.set(True)
            try:
                self.txtLab.focus_set()
            except Exception as e:
                pass

        self.title(title)

    # Helpers ------------------------------------------------------------------ 
    def _set_sites(self) -> None:
        """
        Fill hospitals combobox with active sites that belong to
        the same domain (supplier_id) as the current hospital.

        dict_sites: combobox index → site_id
        """
        self.dict_sites.clear()
        values: list[str] = []

        # Determine domain (supplier_id) from selected_hospital
        supplier_id = None
        if isinstance(self.selected_hospital, dict):
            supplier_id = self.selected_hospital.get("supplier_id")

        if supplier_id is None:
            # No context → do not populate the combo (safer than 'all sites')
            self.cbSites["values"] = ()
            return

        sql = """
            SELECT
                sites.site_id,
                suppliers.description
            FROM sites
            JOIN suppliers
                ON suppliers.supplier_id = sites.comp_id
            WHERE sites.status = 1
              AND sites.supplier_id = ?
            ORDER BY suppliers.description ASC;
        """

        try:
            rows = self.engine.read(True, sql, (supplier_id,)) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "lab._set_sites:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        for idx, row in enumerate(rows):
            site_id = row.get("site_id")
            desc = row.get("description", "")
            if site_id is None:
                continue
            self.dict_sites[idx] = int(site_id)
            values.append(desc)

        self.cbSites["values"] = values


    def _set_managers(self):
        """Fill managers combobox from users table (active only)."""
        self.dict_users.clear()
        values: list[str] = []

        sql = """
            SELECT 
                users.user_id,
                CONCAT(users.last_name, ' ', users.first_name) AS fullname
            FROM users
            WHERE users.status = 1
            ORDER BY users.last_name ASC;
        """
        try:
            rows = self.engine.read(True, sql, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "lab._set_managers:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        for idx, row in enumerate(rows):
            user_id = row.get("user_id")
            fullname = row.get("fullname", "")
            if user_id is None:
                continue
            self.dict_users[idx] = int(user_id)
            values.append(fullname)

        self.cbUsers["values"] = values

    def _set_values(self):
        """Populate widgets from selected_lab (labs.* dict)."""
        s = self.selected_lab
        if not s:
            return

        # Hospital
        try:
            site_id = int(s.get("site_id"))
            for idx, sid in self.dict_sites.items():
                if sid == site_id:
                    self.cbSites.current(idx)
                    break
        except Exception as e:
            pass

        # Manager
        try:
            user_id = int(s.get("user_id"))
            for idx, uid in self.dict_users.items():
                if uid == user_id:
                    self.cbUsers.current(idx)
                    break
        except Exception as e:
            pass

        # Lab description
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
        """Collect current widget values, validating combobox selections.

        Raises:
            ValueError: if required combobox selections are missing.
        """
        if self.cbSites.current() < 0:
            raise ValueError("Select a Hospital.")
        if self.cbUsers.current() < 0:
            raise ValueError("Select a Manager.")

        site_id = self.dict_sites[self.cbSites.current()]
        user_id = self.dict_users[self.cbUsers.current()]
        lab_name = self.description.get().strip()
        status = int(bool(self.status.get()))

        return [site_id, user_id, lab_name, status]

    # ------------------------------------------------------------------ Actions
    def _on_save(self, _evt=None):
        """INSERT or UPDATE labs row."""
        title = self.engine.app_title

        # Optional global validation on fields
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, title) is False:
                return

        # Confirmation
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

        try:
            args = self._get_values()
        except ValueError as ve:
            # User-friendly feedback for missing combo selections
            messagebox.showwarning(
                title,
                str(ve),
                parent=self,
            )
            return

        # Build SQL
        if self.index is not None:
            # UPDATE
            sql = self.engine.build_sql(self.parent.table, op="update")
            lab_id = int(self.index)
            args.append(lab_id)
        else:
            # INSERT
            sql = self.engine.build_sql(self.parent.table, op="insert")

        try:
            self.engine.write(sql, tuple(args))

            # Refresh master
            if hasattr(self.parent, "refresh_labs_and_restore_branch"):
                self.parent.refresh_labs_and_restore_branch()
            elif hasattr(self.parent, "_load_labs_for_hospital") and self.selected_hospital:
                site_id = self.selected_hospital.get("site_id")
                if site_id is not None:
                    self.parent._load_labs_for_hospital(site_id)

            # Cross-window refresh via Controller / Engine dispatcher
            # labs → sections, workstation_test_methods, ecc. (vedi mapping)
            if hasattr(self.engine, "refresh_windows_for_table"):
                try:
                    # parent.table should be “labs”
                    self.engine.refresh_windows_for_table(self.parent.table)
                except Exception as e:
                    # Never block saving due to a GUI issue
                    pass
          
            self._on_cancel()

        except Exception as exc:
            messagebox.showerror(
                title,
                f"Save error:\n{exc}",
                parent=self,
            )

    def _on_cancel(self, _evt=None):
        try:
            self.destroy()
        except Exception as e:
            pass
