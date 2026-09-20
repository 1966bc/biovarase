# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import uuid

from ui.child_view import ChildView


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="workstation")

        self.index = index

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Tk variables
        self.device_id = tk.StringVar()
        self.description = tk.StringVar()
        self.serial = tk.StringVar()
        self.rank = tk.IntVar()
        self.status = tk.BooleanVar()

        # Integer validation callback from Engine
        self.vcmd_int = self.engine.tools.get_validate_integer(self)

        # Internal dictionaries used to map combobox index → primary key
        self.dict_instruments = {}
        self.dict_sections = {}

        # Root grid config (two columns: form + buttons)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    
    def _build_ui(self):

        paddings = {"padx": 5, "pady": 5}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        # LEFT: form fields
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **paddings)

        r = 0
        c = 1

        ttk.Label(frm_left, text="Equipment:").grid(row=r, column=0, sticky=tk.W)
        self.cbEquipments = ttk.Combobox(frm_left, state="readonly")
        self.cbEquipments.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Device ID:").grid(row=r, column=0, sticky=tk.W)
        ent_device = ttk.Entry(frm_left, textvariable=self.device_id)
        ent_device.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Description:").grid(row=r, column=0, sticky=tk.W)
        ent_description = ttk.Entry(frm_left, textvariable=self.description)
        ent_description.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Serial:").grid(row=r, column=0, sticky=tk.W)
        ent_serial = ttk.Entry(frm_left, textvariable=self.serial)
        ent_serial.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Section:").grid(row=r, column=0, sticky=tk.W)
        self.cbSections = ttk.Combobox(frm_left, state="readonly")
        self.cbSections.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Rank:").grid(row=r, column=0, sticky=tk.W)
        ent_rank = ttk.Entry(
            frm_left,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.vcmd_int,
            textvariable=self.rank,
        )
        ent_rank.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, column=0, sticky=tk.W)
        chk_status = ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        )
        chk_status.grid(row=r, column=c, sticky=tk.EW, **paddings)

        # RIGHT: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky=tk.NS, **paddings)

        r = 0
        c = 0
        btn_save = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self._on_save,
        )
        btn_save.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        btn_uuid = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="UUID",
            underline=0,
            command=self._generate_uuid,
        )
        btn_uuid.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        btn_cancel = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        )
        btn_cancel.grid(row=r, column=c, sticky=tk.EW, **paddings)

        frm_buttons.columnconfigure(0, weight=1)

    # ----------------------------------------------------------------------
    def on_open(self):
        # Get section org_id from parent (workstations.py now uses org_id)
        self.selected_section_org_id = getattr(self.parent, "selected_section_org_id", None)
        self.selected_workstation = getattr(self.parent, "selected_workstation", None)

        if self.selected_section_org_id is not None:
            self._set_instruments()
            self._set_sections()
            self._set_section(self.selected_section_org_id)

        if self.selected_workstation is not None:
            self._set_values()
            self.title("Update Workstation")
        else:
            self.status.set(1)
            self.title("Add Workstation")

        try:
            self.cbEquipments.focus()
        except Exception as e:
            self.focus_set()

    # ----------------------------------------------------------------------
    def _set_instruments(self):

        self.dict_instruments.clear()
        values = []

        sql = """
            SELECT equipment_id, description
            FROM equipments
            WHERE status = 1
            ORDER BY description ASC;
        """

        rows = self.engine.db.read(True, sql, ())

        for idx, row in enumerate(rows or []):
            equipment_id = row["equipment_id"]
            description = row["description"] or ""
            self.dict_instruments[idx] = equipment_id
            values.append(description)

        self.cbEquipments["values"] = values

    # ----------------------------------------------------------------------
    def _set_sections(self):
        """Load sections from organizations table based on selected section's lab."""
        if self.selected_section_org_id is None:
            self.dict_sections.clear()
            self.cbSections["values"] = ()
            return

        self.dict_sections.clear()
        values = []

        # Get the lab (parent of section) from organizations
        sql_parent = """
            SELECT parent_id FROM organizations
            WHERE org_id = ? AND org_type = 'section'
        """
        row = self.engine.db.read(False, sql_parent, (self.selected_section_org_id,))
        lab_org_id = row["parent_id"] if row else None

        if lab_org_id is None:
            self.cbSections["values"] = ()
            return

        # Load all sections under this lab
        sql = """
            SELECT org_id, description
            FROM organizations
            WHERE parent_id = ? AND org_type = 'section' AND status = 1
            ORDER BY description;
        """

        rows = self.engine.db.read(True, sql, (lab_org_id,))

        for idx, row in enumerate(rows or []):
            org_id = row["org_id"]
            desc = row["description"] or ""
            self.dict_sections[idx] = org_id
            values.append(desc)

        self.cbSections["values"] = values

    # ----------------------------------------------------------------------
    def _set_section(self, section_org_id):
        """Set the section combobox to the given org_id."""
        if section_org_id is None or not self.dict_sections:
            return

        try:
            key = next(k for k, v in self.dict_sections.items() if v == section_org_id)
            self.cbSections.current(key)
        except StopIteration:
            pass

    # ----------------------------------------------------------------------
    def _generate_uuid(self):
        self.device_id.set(str(uuid.uuid4()))

    # ----------------------------------------------------------------------
    def _get_values(self):
        """Get form values for INSERT/UPDATE."""
        equipment_idx = self.cbEquipments.current()
        section_idx = self.cbSections.current()

        equipment_id = self.dict_instruments.get(equipment_idx)
        section_org_id = self.dict_sections.get(section_idx)  # org_id of the section

        return [
            equipment_id,
            self.device_id.get(),
            self.description.get(),
            self.serial.get(),
            section_org_id,  # org_id (organizations FK)
            self.rank.get(),
            self.status.get(),
        ]

    # ----------------------------------------------------------------------
    def _set_values(self):
        """Set form values from selected workstation."""
        if not self.selected_workstation:
            return

        # Equipments combobox
        equipment_id = self.selected_workstation.get("equipment_id")
        try:
            key = next(k for k, v in self.dict_instruments.items() if v == equipment_id)
            self.cbEquipments.current(key)
        except StopIteration:
            pass

        self.device_id.set(self.selected_workstation.get("device_id", ""))
        self.description.set(self.selected_workstation.get("description", ""))
        self.serial.set(self.selected_workstation.get("serial", ""))

        # Sections combobox - now uses org_id
        org_id = self.selected_workstation.get("org_id")
        try:
            key = next(k for k, v in self.dict_sections.items() if v == org_id)
            self.cbSections.current(key)
        except StopIteration:
            pass

        self.rank.set(self.selected_workstation.get("rank", 1))
        self.status.set(self.selected_workstation.get("status", 1))

    # ----------------------------------------------------------------------
    def _on_save(self, _evt=None):

        if hasattr(self.engine, "on_fields_control"):
            if self.engine.tools.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

        if self._check_device_id() == 0:
            return

        if not messagebox.askyesno(
            self.engine.app_title,
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            return

        args = self._get_values()

        if self.index is not None:
            sql = self.engine.build_sql(self.parent.table, op="update")
            args.append(self.selected_workstation.get("workstation_id"))
        else:
            sql = self.engine.build_sql(self.parent.table, op="insert")

        last_id = self.engine.db.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.tools.get_database_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        if self.selected_section_org_id:
            self.parent.set_workstations((self.selected_section_org_id,))

        try:
            if self.index is not None:
                target_pk = self.selected_workstation.get("workstation_id")
            else:
                target_pk = last_id

            if target_pk is not None:
                iid = str(target_pk)
                self.parent.lstWorkstations.focus(iid)
                self.parent.lstWorkstations.selection_set(iid)
        except Exception as e:
            pass

        self.on_cancel()

    # ----------------------------------------------------------------------
    def _check_device_id(self):

        device = self.device_id.get()
        if not device:
            return 1

        sql = """
            SELECT workstation_id, device_id
            FROM workstations
            WHERE device_id = ?;
        """

        row = self.engine.db.read(False, sql, (device,))

        if row:
            existing_id = row.get("workstation_id")

            if self.index is not None:
                current_id = (
                    self.parent.selected_workstation.get("workstation_id")
                    if self.parent.selected_workstation
                    else None
                )
                if existing_id is not None and existing_id != current_id:
                    messagebox.showwarning(
                        self.engine.app_title,
                        "This Device ID is already in use.",
                        parent=self,
                    )
                    return 0
            else:
                messagebox.showwarning(
                    self.engine.app_title,
                    "This Device ID is already in use.",
                    parent=self,
                )
                return 0

        return 1

    # ----------------------------------------------------------------------
    def on_cancel(self, evt=None):
        """Close dialog."""
        super().on_cancel(evt)
