# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   winter MMXXVI
# -----------------------------------------------------------------------------
"""
Organization Editor Dialog.

CRUD dialog for creating/editing organizations in the hierarchy.

Features:
    - Parent selection (determines allowed child types)
    - Type selection based on parent type
    - Code and description fields
    - Status toggle
"""

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from i18n import _
from views.child_view import ChildView

# Organization type constants
ORG_TYPE_COUNTRY = "country"
ORG_TYPE_REGION = "region"
ORG_TYPE_SITE = "site"
ORG_TYPE_LAB = "lab"
ORG_TYPE_SECTION = "section"

# Display names for org types
ORG_TYPE_LABELS = {
    ORG_TYPE_COUNTRY: "Country",
    ORG_TYPE_REGION: "Region",
    ORG_TYPE_SITE: "Site",
    ORG_TYPE_LAB: "Lab",
    ORG_TYPE_SECTION: "Section",
}

# Allowed child types for each parent type
# Hierarchy: Country → Region → Site (hospital) → Lab → Section
ORG_CHILD_TYPES = {
    None: [ORG_TYPE_COUNTRY],  # Root can have countries
    ORG_TYPE_COUNTRY: [ORG_TYPE_REGION],
    ORG_TYPE_REGION: [ORG_TYPE_SITE],  # Region can have sites (hospitals)
    ORG_TYPE_SITE: [ORG_TYPE_LAB],  # Site can have labs
    ORG_TYPE_LAB: [ORG_TYPE_SECTION],
    ORG_TYPE_SECTION: [],  # Sections cannot have children
}


class UI(ChildView):
    """Organization editor dialog."""

    def __init__(self, parent, index=None, parent_org_id=None):
        """
        Initialize the organization editor.

        Args:
            parent: Parent widget (organizations master window)
            index: org_id for UPDATE, None for INSERT
            parent_org_id: parent org_id for new child organizations
        """
        super().__init__(parent, name="organization")

        self.index = index
        self.parent_org_id = parent_org_id

        # State
        self.selected_org = None
        self.parent_org = None

        # Vars
        self.org_type = tk.StringVar()
        self.code = tk.StringVar()
        self.description = tk.StringVar()
        self.status = tk.BooleanVar(value=True)

        # Dictionaries for combobox mapping
        self.dict_types = {}  # idx -> org_type value
        self.dict_parents = {}  # idx -> org_id

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Build interface
        self._build_ui()
        self.resizable(True, False)
        self.minsize(400, 200)
        self.show()

    def _build_ui(self):
        """Build the user interface."""
        paddings = {"padx": 6, "pady": 6}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=10)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.frm_main.columnconfigure(1, weight=1)

        r = 0
        # Parent (read-only display)
        ttk.Label(self.frm_main, text=_("Parent:")).grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.lbl_parent = ttk.Label(self.frm_main, text="", relief=tk.SUNKEN, width=40)
        self.lbl_parent.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        # Type
        ttk.Label(self.frm_main, text=_("Type:")).grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.cbType = ttk.Combobox(self.frm_main, state="readonly", textvariable=self.org_type)
        self.cbType.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        # Code
        ttk.Label(self.frm_main, text=_("Code:")).grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.txtCode = ttk.Entry(self.frm_main, textvariable=self.code, width=20)
        self.txtCode.grid(row=r, column=1, sticky=tk.W, **paddings)

        r += 1
        # Description
        ttk.Label(self.frm_main, text=_("Description:")).grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        self.txtDescription = ttk.Entry(self.frm_main, textvariable=self.description)
        self.txtDescription.grid(row=r, column=1, sticky=tk.EW, **paddings)

        r += 1
        # Status
        ttk.Label(self.frm_main, text=_("Status:")).grid(
            row=r, column=0, sticky=tk.W, **paddings
        )
        ttk.Checkbutton(
            self.frm_main,
            variable=self.status,
            onvalue=True,
            offvalue=False,
        ).grid(row=r, column=1, sticky=tk.W, **paddings)

        # Buttons
        btns = ttk.Frame(self.frm_main, style="App.TFrame")
        btns.grid(row=0, column=2, rowspan=5, sticky="ns", padx=4, pady=4)

        btn_save = ttk.Button(
            btns,
            text=_("Save"),
            command=self._on_save,
            underline=0,
            style="App.TButton",
        )
        btn_save.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        btn_cancel = ttk.Button(
            btns,
            text=_("Cancel"),
            command=self.on_cancel,
            underline=0,
            style="App.TButton",
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

    def on_open(self):
        """Public entry called by master."""
        if self.index is not None:
            # UPDATE mode: load existing organization
            try:
                self.selected_org = self.engine.get_selected(
                    self.parent.table,
                    self.parent.primary_key,
                    int(self.index),
                )
            except Exception as exc:
                self.engine.on_log("organization.on_open", exc, type(exc), sys.modules[__name__])
                self.selected_org = None

            if self.selected_org:
                # Get parent org for context
                parent_id = self.selected_org.get("parent_id")
                if parent_id:
                    self.parent_org = self.engine.get_selected(
                        self.parent.table,
                        self.parent.primary_key,
                        parent_id,
                    )
                else:
                    self.parent_org = None

            self._set_type_options()
            self._set_values()
            title = _("Update Organization")
            # Disable type change in edit mode
            self.cbType.config(state="disabled")

        else:
            # INSERT mode
            self.selected_org = None

            # Get parent org for context (if adding child)
            if self.parent_org_id:
                self.parent_org = self.engine.get_selected(
                    self.parent.table,
                    self.parent.primary_key,
                    self.parent_org_id,
                )
            else:
                self.parent_org = None

            self._set_type_options()
            self.status.set(True)
            title = _("Add Organization")

        # Set parent label
        if self.parent_org:
            parent_desc = self.parent_org.get("description", "")
            parent_type = self.parent_org.get("org_type", "")
            self.lbl_parent.config(text=f"{parent_desc} ({_(ORG_TYPE_LABELS.get(parent_type, parent_type))})")
        else:
            self.lbl_parent.config(text=_("(Root)"))

        self.title(title)
        self.txtDescription.focus_set()

    def _set_type_options(self):
        """Set available organization types based on parent."""
        self.dict_types.clear()

        if self.parent_org:
            parent_type = self.parent_org.get("org_type")
        else:
            parent_type = None

        allowed_types = ORG_CHILD_TYPES.get(parent_type, [])

        values = []
        for idx, org_type in enumerate(allowed_types):
            self.dict_types[idx] = org_type
            values.append(_(ORG_TYPE_LABELS.get(org_type, org_type)))

        self.cbType["values"] = values

        # Select first option by default
        if values:
            self.cbType.current(0)

    def _set_values(self):
        """Populate widgets from selected_org."""
        s = self.selected_org
        if not s:
            return

        # Type
        org_type = s.get("org_type")
        for idx, t in self.dict_types.items():
            if t == org_type:
                self.cbType.current(idx)
                break

        # Code
        self.code.set(s.get("code") or "")

        # Description
        self.description.set(s.get("description") or "")

        # Status
        self.status.set(int(s.get("status", 1)) == 1)

    def _get_values(self):
        """Collect and validate field values."""
        # Type
        if self.cbType.current() < 0:
            raise ValueError(_("Select a type."))
        org_type = self.dict_types[self.cbType.current()]

        # Description is mandatory
        desc = self.description.get().strip()
        if not desc:
            raise ValueError(_("Description is mandatory."))

        # Code is optional
        code = self.code.get().strip() or None

        # Parent ID
        if self.index is not None:
            # UPDATE: keep existing parent_id
            parent_id = self.selected_org.get("parent_id") if self.selected_org else None
        else:
            # INSERT: use parent_org_id
            parent_id = self.parent_org_id

        return {
            "parent_id": parent_id,
            "org_type": org_type,
            "code": code,
            "description": desc,
            "status": 1 if self.status.get() else 0,
        }

    def _on_save(self, _evt=None):
        """Save the organization."""
        title = self.engine.app_title

        # Confirmation
        if not messagebox.askyesno(
            title,
            self.engine.ask_to_save,
            parent=self,
        ):
            messagebox.showinfo(title, self.engine.abort, parent=self)
            return

        # Collect values
        try:
            values = self._get_values()
        except ValueError as ve:
            messagebox.showwarning(title, str(ve), parent=self)
            return

        if self.index is not None:
            # UPDATE
            sql = """
                UPDATE organizations
                SET parent_id = ?, org_type = ?, code = ?, description = ?, status = ?
                WHERE org_id = ?
            """
            args = (
                values["parent_id"],
                values["org_type"],
                values["code"],
                values["description"],
                values["status"],
                int(self.index),
            )
            pk_to_select = int(self.index)
        else:
            # INSERT
            sql = """
                INSERT INTO organizations (parent_id, org_type, code, description, status)
                VALUES (?, ?, ?, ?, ?)
            """
            args = (
                values["parent_id"],
                values["org_type"],
                values["code"],
                values["description"],
                values["status"],
            )
            pk_to_select = None

        try:
            result = self.engine.write(sql, args)
            if result is None:
                err = self.engine.last_write_error
                msg = self.engine.get_user_friendly_db_error(err) if err else _("Save failed.")
                messagebox.showerror(title, msg, parent=self)
                return

            if self.index is None:
                pk_to_select = result  # lastrowid for INSERT

        except Exception as exc:
            self.engine.on_log("organization._on_save", exc, type(exc), sys.modules[__name__])
            messagebox.showerror(title, str(exc), parent=self)
            return

        # Notify parent to refresh
        if hasattr(self.parent, "reload_and_reselect"):
            self.parent.reload_and_reselect(pk_to_select)
        elif hasattr(self.parent, "on_open"):
            self.parent.on_open()

        self.on_cancel()

    def on_cancel(self, evt=None):
        """Close dialog."""
        super().on_cancel(evt)
