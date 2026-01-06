# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class UI(tk.Toplevel):
    """
    Section editor.

    - No singleton: the parent window is responsible for closing
      any previous editor instance before opening a new one.
    - INSERT if index is None.
    - UPDATE if index is not None (index == primary key).
    """

    def __init__(self, parent, index=None):
        """
        Standard Toplevel initialization (no singleton guard).
        """
        super().__init__(name="section")
        
        self.engine = self.nametowidget(".").engine
        self.parent = parent
        self.index = index  # None for insert, pk for update

       
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)
        self.bind("<Alt-s>", self.on_save)

        # Tk variables
        self.description = tk.StringVar()
        self.status = tk.BooleanVar(value=True)
        self.set_it = tk.BooleanVar(value=False)

        # Combobox index → primary key mapping
        self.dict_labs = {}
        self.dict_users = {}

        # Root grid config (two columns: form + buttons)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

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

    # ------------------------------------------------------------------ UI BUILD
    def _build_ui(self):
        """Build the form and buttons area."""
        paddings = {"padx": 8, "pady": 8}

        # Main form frame (Column 0 of the Toplevel)
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        self.frm_main.columnconfigure(0, weight=0)
        self.frm_main.columnconfigure(1, weight=1)

        r = 0
        ttk.Label(self.frm_main, text="Labs:").grid(row=r, column=0, sticky=tk.W, **paddings)
        self.cbLabs = ttk.Combobox(self.frm_main, state="readonly")
        self.cbLabs.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(self.frm_main, text="Manager:").grid(row=r, column=0, sticky=tk.W, **paddings)
        self.cbUsers = ttk.Combobox(self.frm_main, state="readonly")
        self.cbUsers.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(self.frm_main, text="Description:").grid(row=r, column=0, sticky=tk.W, **paddings)
        self.txSection = ttk.Entry(self.frm_main, textvariable=self.description)
        self.txSection.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(self.frm_main, text="Status:").grid(row=r, column=0, sticky=tk.W, **paddings)
        ttk.Checkbutton(
            self.frm_main,
            variable=self.status,
            onvalue=1,
            offvalue=0,
        ).grid(row=r, column=1, sticky=tk.W, **paddings)

        # Buttons (Column 1 of the Toplevel)
        frm_buttons = ttk.Frame(self, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        btn_save = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self.on_save,
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

        # "Set It" checkbox: marks this section as the current one
        ttk.Checkbutton(
            frm_buttons,
            text="Set It",
            variable=self.set_it,
            onvalue=1,
            offvalue=0,
        ).grid(row=2, column=0, sticky="w", padx=4, pady=4)

        # Keep buttons the same width
        frm_buttons.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ OPEN
    def on_open(self, selected_lab, selected_section=None):
       
        self.selected_lab = selected_lab
        self.selected_section = selected_section

        self._set_labs()
        self._set_users()
        self._preselect_lab_in_combo(self.selected_lab)

        # Default state for "Set It" in INSERT mode
        self.set_it.set(False)

        if self.index is not None:
            # ------------------------ UPDATE MODE ------------------------
            try:
                # Prefer the in-memory context (engine.current_ids) if available
                current_sid = getattr(self.engine, "current_ids", {}).get("section_id")

                # Fallback to file-based value if the context is not loaded
                if current_sid is None:
                    current_sid = int(self.engine.get_section_id())

                editing_sid = int(self.index)

                # Auto-check "Set It" only if editing the currently active section
                self.set_it.set(editing_sid == int(current_sid))

            except Exception as e:
                # Log any issue but do not interrupt the UI
                self.engine.on_log("on_open:set_it", e, type(e), sys.modules[__name__])

            # Re-read selected_section from DB to ensure fresh values
            try:
                self.selected_section = self.engine.get_selected(
                    "sections",
                    "section_id",
                    int(self.index),
                )
            except Exception as e:
                self.selected_section = None
                self.engine.on_log(
                    "on_open:get_selected(section)",
                    e,
                    type(e),
                    sys.modules[__name__],
                )

            # Apply values to the form only if we have a record
            if self.selected_section:
                self._set_values()

            title = "Update Lab Section"

        else:
            # ------------------------ INSERT MODE ------------------------
            try:
                self.status.set(True)
            except Exception as e:
                self.engine.on_log("on_open:set_status", e, type(e), sys.modules[__name__])
            title = "Insert Lab Section"

        # Set window title
        self.title(title)

        # Defer focus to the labs combobox when idle
        try:
            self.after_idle(self.cbLabs.focus)
        except Exception as e:
            self.engine.on_log("on_open:focus", e, type(e), sys.modules[__name__])

    # ------------------------------------------------------------------ COMBOS
    def _set_labs(self):
        """
        Fill labs combobox filtered by the current site of selected_lab.

        Uses:
            - self.selected_lab["site_id"]  (from hybrid dict)
            - engine.read(True, ...)
        """
        self.dict_labs.clear()
        values = []

        # Try to filter by the site_id of the selected_lab
        site_id = None
        try:
            site_id = int(self.selected_lab.get("site_id"))
        except Exception as e:
            site_id = None

        if site_id is None:
            # Fallback: all active labs
            sql = """
                SELECT
                    labs.lab_id,
                    labs.description AS lab_name
                FROM labs
                WHERE labs.status = 1
                ORDER BY labs.description ASC;
            """
            rows = self.engine.read(True, sql, ())
        else:
            sql = """
                SELECT
                    labs.lab_id,
                    labs.description AS lab_name
                FROM labs
                WHERE labs.site_id = ?
                  AND labs.status = 1
                ORDER BY labs.description ASC;
            """
            rows = self.engine.read(True, sql, (site_id,))

        rows = rows or []
        for idx, row in enumerate(rows):
            lab_id = int(row["lab_id"])
            lab_name = row["lab_name"]
            self.dict_labs[idx] = lab_id
            values.append(lab_name)

        self.cbLabs["values"] = values

    def _preselect_lab_in_combo(self, lab_row):
        """
        Preselect the current lab in the combobox based on lab_id.
        lab_row is a hybrid dict from engine.get_selected("labs", ...).
        """
        try:
            lab_id = int(lab_row.get("lab_id"))
            for idx, pk in self.dict_labs.items():
                if pk == lab_id:
                    self.cbLabs.current(idx)
                    break
        except Exception as e:
            pass

    def _set_users(self):
        """Fill users combobox with all active users (status = 1)."""
        self.dict_users.clear()
        values = []

        sql = """
            SELECT
                users.user_id,
                CONCAT(users.last_name, ' ', users.first_name) AS fullname
            FROM users
            WHERE users.status = 1
            ORDER BY users.last_name ASC;
        """
        rows = self.engine.read(True, sql, ()) or []

        for idx, row in enumerate(rows):
            user_id = int(row["user_id"])
            fullname = row["fullname"]
            self.dict_users[idx] = user_id
            values.append(fullname)

        self.cbUsers["values"] = values

    def _set_values(self):
        """
        Map DB row (selected_section hybrid dict) to widgets in UPDATE mode.

        expected keys:
            section_id, lab_id, user_id, description, status
        """
        s = self.selected_section
        if not s:
            return

        # Preselect lab
        try:
            lab_id = int(s.get("lab_id"))
            for idx, pk in self.dict_labs.items():
                if pk == lab_id:
                    self.cbLabs.current(idx)
                    break
        except Exception as e:
            pass

        # Preselect manager
        try:
            user_id = int(s.get("user_id"))
            for idx, pk in self.dict_users.items():
                if pk == user_id:
                    self.cbUsers.current(idx)
                    break
        except Exception as e:
            pass

        # Description and status
        try:
            self.description.set(s.get("description", ""))
            self.status.set(int(s.get("status", 1)) == 1)
        except Exception as e:
            self.status.set(True)

    def _get_values(self):
       
        if self.cbLabs.current() < 0:
            raise ValueError("Select a Lab.")
        if self.cbUsers.current() < 0:
            raise ValueError("Select a Manager.")

        lab_id = self.dict_labs[self.cbLabs.current()]
        user_id = self.dict_users[self.cbUsers.current()]
        description = self.description.get()
        status = int(bool(self.status.get()))

        return [lab_id, user_id, description, status]

    def on_save(self, _evt=None):
        """
        Save handler for the Section editor (INSERT or UPDATE).

        Steps:
            1. Validate all mandatory fields.
            2. Ask for confirmation.
            3. Collect field values.
            4. Build the SQL (INSERT or UPDATE).
            5. Execute the statement via Engine.write().
            6. Optionally set the section_id as current ("Set It").
            7. Refresh dependent windows via Controller dispatcher.
            8. Refresh parent list and reselect the saved row.
        """
        # 1. Field validation
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(
                self.frm_main,
                self.nametowidget(".").title(),
            ) is False:
                return

        # 2. Confirm save
        if not messagebox.askyesno(
            self.nametowidget(".").title(),
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            messagebox.showinfo(
                self.nametowidget(".").title(),
                getattr(self.engine, "abort", "Operation cancelled."),
                parent=self,
            )
            return

        try:
            # 3. Gather all widget values
            args = self._get_values()

            # 4. Determine operation type
            is_update = self.index is not None
            if is_update:
                pk = int(self.index)
                sql = self.engine.build_sql(self.parent.table, op="update")
                args.append(pk)  # primary key at the end for UPDATE
            else:
                sql = self.engine.build_sql(self.parent.table, op="insert")

            # 5. Execute the SQL and retrieve the result
            last_id = self.engine.write(sql, tuple(args))
            if last_id is None:
                raise RuntimeError("Write failed: Engine returned None.")

            # Determine the actual record ID
            resolved_id = pk if is_update else int(last_id)

            # 6. Handle "Set It" checkbox → store selected section_id + reload context
            if self.set_it.get():
                self._set_current_section(resolved_id)

            # 7. Cross-window refresh via Controller / Engine dispatcher
            #    La tabella del parent è "sections"
            if hasattr(self.engine, "refresh_windows_for_table"):
                try:
                    self.engine.refresh_windows_for_table(self.parent.table)
                except Exception as e:
                    try:
                        self.engine.on_log(
                            "sections.on_save.refresh_windows_for_table",
                            e,
                            type(e),
                            sys.modules[__name__],
                        )
                    except Exception as e:
                        pass

            # 8. Reload and reselect the record in parent list
            self._reselect_in_parent(resolved_id)

            # Finally close the editor
            self._on_cancel()

        except Exception as exc:
            messagebox.showerror(
                self.engine.app_title,
                f"Save error (sections):\n{exc}",
                parent=self,
            )


    
    def _set_current_section(self, section_id: int):
        """
        Save the current section_id, reload the hierarchical context
        (site_id, lab_id, supplier_id, etc.) and update interested windows.
        """
        try:
            # Persist the new current section_id to disk
            self.engine.set_section_id(section_id)

            # Reload in-memory context IDs (site_id, lab_id, supplier_id, ...)
            if hasattr(self.engine, "load_context_ids"):
                self.engine.load_context_ids()

            # Notify the main window (dispatcher for context changes)
            main = self.engine.dict_instances.get("main")
            if main and hasattr(main, "refresh_context_from_section"):
                main.refresh_context_from_section()

        except Exception as e:
            self.engine.on_log(
                "_set_current_section",
                e,
                type(e),
                sys.modules[__name__],
            )

    def _reselect_in_parent(self, section_id: int):
        """
        Ask parent to refresh the list and reselect the just-saved record.
        """
        self.parent.refresh_sections_for_current_lab()
        try:
            tv = self.parent.lstSections
            iid = str(section_id)
            tv.selection_set(iid)
            tv.see(iid)
        except Exception as e:
            self.engine.on_log("_reselect_in_parent", e, type(e), sys.modules[__name__])

    
    def _on_cancel(self, _evt=None):
        try:
            self.destroy()
        except Exception as e:
            pass
