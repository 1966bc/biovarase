# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------
"""
Workstation Test Methods Mapping Window.

This master window manages the assignment of test methods to workstations
across the multi-site laboratory hierarchy.

Hierarchy visualization: Sites → Labs → Sections → Workstations

Role-based access control:
    - App Admin (role=0):        See all organizations (global access)
    - Country/Regional/Lab Admin (1-3): See descendants of their org
    - Superuser (role=4):        QC validation within their lab
    - Technician (role=5):       Data entry within their scope
    - Viewer (role=6):           Read-only access

Key features:
    - Hierarchical tree navigation (left panel)
    - Test methods list for selected workstation (right panel)
    - Double-click workstation: assign new test methods
    - Double-click test method: remove mapping

Singleton window (per PROJECT_RULES.md section 7.1).
"""

import tkinter as tk

from i18n import _
from views.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox

import views.assign_test_methods as assign

# User roles - imported from engine for consistency
from engine import (
    ROLE_APP_ADMIN, ROLE_COUNTRY_ADMIN, ROLE_REGIONAL_ADMIN,
    ROLE_LAB_ADMIN, ROLE_SUPERUSER, ROLE_TECHNICIAN, ROLE_VIEWER
)
# Legacy aliases
ROLE_ADMIN = ROLE_APP_ADMIN
ROLE_AUTOLOGIN = ROLE_VIEWER

# Tree node types (based on organizations.org_type)
NODE_TYPE_COUNTRY = "country"
NODE_TYPE_REGION = "region"
NODE_TYPE_SITE = "site"
NODE_TYPE_LAB = "lab"
NODE_TYPE_SECTION = "section"
NODE_TYPE_WORKSTATION = "workstation"

# Tree root label
TREE_ROOT_LABEL = "Organizations"


class UI(ParentView):

    def __init__(self, parent):
        """
        Guarded initializer: when the instance is reused, skip widget rebuilds.
        """
        super().__init__(parent, name="workstation_test_methods")
        if self._reusing:
            return

        self.resizable(True, True)
        self.geometry("1020x600")
        self.bind("<Alt-c>", self.on_cancel)

        self.child = None
        self.selected_workstation = None
        self.test_methods_assigned = []
        self.action_var = tk.StringVar(value="edit")  # "edit" or "remove"

        # Subscribe to events (Observer pattern)
        self.engine.subscribe("test_method_changed", self._on_test_method_changed)
        self.engine.subscribe("tests_changed", self._on_test_method_changed)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.show()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())


    def _build_ui(self):

        pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        pw.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        pane_left  = ttk.Frame(pw, style="App.TFrame")
        pane_right = ttk.Frame(pw, style="App.TFrame")

        pw.add(pane_left,  minsize=160)
        pw.add(pane_right, minsize=300)

        # Left: hierarchical tree (Sites → Labs → Sections → Workstations)
        self.Sites = ttk.Treeview(pane_left, show="tree")
        self.Sites.column("#0", width=300, minwidth=240, stretch=False)

        sb_sites = ttk.Scrollbar(pane_left, orient=tk.VERTICAL, command=self.Sites.yview)
        self.Sites.configure(yscrollcommand=sb_sites.set)
        self.Sites.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_sites.pack(side=tk.RIGHT, fill=tk.Y)

        self.Sites.bind("<<TreeviewSelect>>", self.on_branch_selected)
        self.Sites.bind("<Double-1>", self.on_branch_activated)

        # Right: list of mapped methods
        frm_right = ttk.Frame(pane_right, style="Panel.TFrame")
        frm_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        # Action selector frame (bottom)
        frm_action = ttk.Frame(frm_right, style="App.TFrame")
        frm_action.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        ttk.Label(frm_action, text=_("Double-click action:")).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Radiobutton(
            frm_action,
            text=_("Edit External Code"),
            variable=self.action_var,
            value="edit"
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Radiobutton(
            frm_action,
            text=_("Remove Mapping"),
            variable=self.action_var,
            value="remove"
        ).pack(side=tk.LEFT)

        # Treeview with scrollbar
        cols_methods = ("test", "code", "external_code", "sample", "method", "unit", "category")
        self.lstTestsMethods = ttk.Treeview(frm_right, columns=cols_methods, show="headings")

        self.lstTestsMethods.column("test", width=200, minwidth=180, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("test", text=_("Test"), anchor=tk.W)

        self.lstTestsMethods.column("code", width=80, minwidth=80, anchor=tk.W, stretch=False)
        self.lstTestsMethods.heading("code", text=_("Code"), anchor=tk.W)

        self.lstTestsMethods.column("external_code", width=100, minwidth=80, anchor=tk.W, stretch=False)
        self.lstTestsMethods.heading("external_code", text=_("External Code"), anchor=tk.W)

        self.lstTestsMethods.column("sample", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("sample", text=_("Sample"), anchor=tk.W)

        self.lstTestsMethods.column("method", width=120, minwidth=120, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("method", text=_("Method"), anchor=tk.W)

        self.lstTestsMethods.column("unit", width=80, minwidth=80, anchor=tk.W, stretch=False)
        self.lstTestsMethods.heading("unit", text=_("Unit"), anchor=tk.W)

        self.lstTestsMethods.column("category", width=120, minwidth=100, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("category", text=_("Category"), anchor=tk.W)

        sb_methods = ttk.Scrollbar(frm_right, orient=tk.VERTICAL, command=self.lstTestsMethods.yview)
        self.lstTestsMethods.configure(yscrollcommand=sb_methods.set)
        self.lstTestsMethods.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_methods.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstTestsMethods.tag_configure("inactive", background="light gray")
        self.lstTestsMethods.bind("<Double-1>", self.on_test_method_activated)

    def on_open(self):
        self.title(_("Workstations — Test Methods Mapping"))
        self._load_tree()
        

    def _load_tree(self):
        """
        Build the hierarchy tree from organizations table.

        Structure: Country → Region → Site → Lab → Section → Workstation

        Role-based filtering:
            - App Admin (role=0): See all organizations
            - Country Admin (role=1): See their country and descendants
            - Regional Admin (role=2): See their region and descendants
            - Lab Admin+ (role>=3): See ONLY their assigned lab and sections
        """
        # 1) Clear any existing nodes
        for iid in self.Sites.get_children():
            self.Sites.delete(iid)

        # 2) Create the root node
        root_iid = "org_root"
        root = self.Sites.insert("", tk.END, iid=root_iid, text=TREE_ROOT_LABEL)

        # 3) Get user role with fail-safe default
        try:
            role = int(self.engine.log_user.get("role", ROLE_TECHNICIAN))
        except (ValueError, TypeError, KeyError):
            role = ROLE_TECHNICIAN

        user_org_id = self.engine.log_user.get("org_id")

        # 4) Build tree based on role
        if role == ROLE_APP_ADMIN:  # App Admin - full tree
            self._build_full_tree(root)
        elif role >= ROLE_LAB_ADMIN:  # Lab Admin, Superuser, Technician, Viewer - only their lab
            self._build_lab_only_tree(root, user_org_id)
        else:  # Country/Regional Admin (role 1-2) - their scope and descendants
            self._build_scoped_tree(root, user_org_id, role)

        # 5) Expand all nodes for better UX
        self.Sites.item(root_iid, open=True)
        self._expand_all(root_iid)

    def _expand_all(self, parent_iid):
        """Recursively expand all tree nodes."""
        for child in self.Sites.get_children(parent_iid):
            self.Sites.item(child, open=True)
            self._expand_all(child)

    def _build_full_tree(self, root):
        """Build full organization tree (App Admin only)."""
        countries = self._load_orgs_by_type(None, "country")
        for country_id, country_name in countries:
            country_iid = f"country_{country_id}"
            self.Sites.insert(root, tk.END, iid=country_iid, text=country_name,
                              values=(country_id, NODE_TYPE_COUNTRY))
            self._build_regions(country_iid, country_id)

    def _build_regions(self, parent_iid, country_id):
        """Build regions under a country."""
        regions = self._load_orgs_by_type(country_id, "region")
        for region_id, region_name in regions:
            region_iid = f"region_{region_id}"
            self.Sites.insert(parent_iid, tk.END, iid=region_iid, text=region_name,
                              values=(region_id, NODE_TYPE_REGION))
            self._build_sites(region_iid, region_id)

    def _build_sites(self, parent_iid, region_id):
        """Build sites under a region."""
        sites = self._load_orgs_by_type(region_id, "site")
        for site_id, site_name in sites:
            site_iid = f"site_{site_id}"
            self.Sites.insert(parent_iid, tk.END, iid=site_iid, text=site_name,
                              values=(site_id, NODE_TYPE_SITE))
            self._build_labs(site_iid, site_id)

    def _build_labs(self, parent_iid, site_id):
        """Build labs under a site."""
        labs = self._load_orgs_by_type(site_id, "lab")
        for lab_id, lab_name in labs:
            lab_iid = f"lab_{lab_id}"
            self.Sites.insert(parent_iid, tk.END, iid=lab_iid, text=lab_name,
                              values=(lab_id, NODE_TYPE_LAB))
            self._build_sections(lab_iid, lab_id)

    def _build_sections(self, parent_iid, lab_id):
        """Build sections under a lab, including workstations."""
        sections = self._load_orgs_by_type(lab_id, "section")
        for section_id, section_name in sections:
            sec_iid = f"sec_{section_id}"
            self.Sites.insert(parent_iid, tk.END, iid=sec_iid, text=section_name,
                              values=(section_id, NODE_TYPE_SECTION))
            # Load workstations under this section
            workstations = self._load_workstations(section_id)
            for ws_id, ws_descr in workstations:
                ws_iid = f"ws_{ws_id}"
                self.Sites.insert(sec_iid, tk.END, iid=ws_iid, text=ws_descr,
                                  values=(ws_id, NODE_TYPE_WORKSTATION))

    def _build_lab_only_tree(self, root, user_org_id):
        """Build tree showing only user's assigned lab (role >= 3)."""
        if user_org_id is None:
            return

        # Get user's org info
        sql = "SELECT org_id, org_type, description FROM organizations WHERE org_id = ?"
        org = self.engine.read(False, sql, (user_org_id,))
        if not org:
            return

        org_type = org["org_type"]

        # Find the lab_id based on org_type
        if org_type == "lab":
            lab_id = user_org_id
        elif org_type == "section":
            # Get parent lab
            sql = "SELECT parent_id FROM organizations WHERE org_id = ?"
            parent = self.engine.read(False, sql, (user_org_id,))
            lab_id = parent["parent_id"] if parent else None
        else:
            lab_id = None

        if lab_id is None:
            return

        # Get lab info
        sql = "SELECT org_id, description FROM organizations WHERE org_id = ?"
        lab = self.engine.read(False, sql, (lab_id,))
        if not lab:
            return

        # Insert lab node
        lab_iid = f"lab_{lab_id}"
        self.Sites.insert(root, tk.END, iid=lab_iid, text=lab["description"],
                          values=(lab_id, NODE_TYPE_LAB))

        # Build sections under this lab (with workstations)
        self._build_sections(lab_iid, lab_id)

    def _build_scoped_tree(self, root, user_org_id, role):
        """Build tree for Country/Regional Admin (role 1-2)."""
        if user_org_id is None:
            return

        # Get user's org info
        sql = "SELECT org_id, org_type, description FROM organizations WHERE org_id = ?"
        org = self.engine.read(False, sql, (user_org_id,))
        if not org:
            return

        org_type = org["org_type"]

        if org_type == "country":
            # Country admin - show country and all descendants
            country_iid = f"country_{user_org_id}"
            self.Sites.insert(root, tk.END, iid=country_iid, text=org["description"],
                              values=(user_org_id, NODE_TYPE_COUNTRY))
            self._build_regions(country_iid, user_org_id)
        elif org_type == "region":
            # Regional admin - show region and all descendants
            region_iid = f"region_{user_org_id}"
            self.Sites.insert(root, tk.END, iid=region_iid, text=org["description"],
                              values=(user_org_id, NODE_TYPE_REGION))
            self._build_sites(region_iid, user_org_id)
        else:
            # Fallback to lab-only view
            self._build_lab_only_tree(root, user_org_id)


    def _load_orgs_by_type(self, parent_id, org_type):
        """
        Load organizations of a specific type under a parent.

        Args:
            parent_id: Parent org_id (None for root/countries)
            org_type: Organization type ('country', 'region', 'site', 'lab', 'section')

        Returns:
            List of (org_id, description) tuples
        """
        if parent_id is None:
            sql = """
                SELECT org_id, description
                FROM organizations
                WHERE parent_id IS NULL AND org_type = ? AND status = 1
                ORDER BY description ASC
            """
            args = (org_type,)
        else:
            sql = """
                SELECT org_id, description
                FROM organizations
                WHERE parent_id = ? AND org_type = ? AND status = 1
                ORDER BY description ASC
            """
            args = (parent_id, org_type)

        rows = self.engine.read(True, sql, args) or []
        return [(r["org_id"], r["description"]) for r in rows]

    def _load_workstations(self, section_org_id):
        """
        Load active workstations for a given section (by org_id).

        Args:
            section_org_id: The section's org_id

        Returns:
            List of (workstation_id, description) tuples
        """
        sql = """
            SELECT workstation_id, description
            FROM workstations
            WHERE org_id = ? AND status = 1
            ORDER BY description ASC
        """
        rows = self.engine.read(True, sql, (section_org_id,)) or []
        return [(r["workstation_id"], r["description"]) for r in rows]

    def _clear_tests_methods(self):
        """Clear the right-hand list and reset assigned methods."""
        self.test_methods_assigned = []
        self.engine.clear_treeview(self.lstTestsMethods)

    def on_branch_selected(self, _evt=None):
        """Triggered when a node is selected.
        If it's a workstation, load its mapped methods on the right.
        Otherwise, clear the right panel and reset the current workstation."""
        
        # 1) Get the currently selected Treeview item
        item_iid = self.Sites.focus()
        item = self.Sites.item(item_iid)

        # Guard: no item selected or no usable values
        if not item or not item.get("values"):
            self.selected_workstation = None
            self._clear_tests_methods()
            return

        ref_id, ref_type = item["values"]

        # 2) If it's not a workstation, clear right panel and reset state
        if ref_type != NODE_TYPE_WORKSTATION:
            self.selected_workstation = None
            self._clear_tests_methods()
            return

        # 3) Ensure PK is a valid integer
        try:
            pk = int(ref_id)
        except Exception as e:
            self.selected_workstation = None
            self._clear_tests_methods()
            return

        # 4) Load workstation record
        ws = self.engine.get_selected("workstations", "workstation_id", pk)
        if ws is None:
            self.selected_workstation = None
            self._clear_tests_methods()
            return

        self.selected_workstation = ws

        # 5) Load mapped test methods for this workstation
        self._set_tests_methods((ws["workstation_id"],))

    def on_branch_activated(self, _evt=None):
        """
        Double-click on a workstation: open the assignment dialog.

        Permission required: Admin/Superuser only (QC configuration).
        """

        # 1) Check permission (Admin/Superuser only can assign test methods)
        if not self.engine.can_validate_qc():
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.user_not_enable,
                parent=self
            )
            return

        # 2) Get the selected item from the Treeview
        item_iid = self.Sites.focus()
        item = self.Sites.item(item_iid)

        # Guard: nothing selected or item without usable values
        if not item or not item.get("values"):
            return

        ref_id, ref_type = item["values"]

        # 3) Only react to workstation nodes
        if ref_type != NODE_TYPE_WORKSTATION:
            return

        # 4) Ensure ref_id is a valid integer
        try:
            pk = int(ref_id)
        except Exception as e:
            return

        # 5) Load workstation details only if changed
        ws = self.selected_workstation
        if ws is None or ws.get("workstation_id") != pk:
            ws = self.engine.get_selected("workstations", "workstation_id", pk)
            if ws is None:
                return  # Fail-safe: nothing to show
            self.selected_workstation = ws
            self._set_tests_methods((ws["workstation_id"],))

        # 6) Open the child dialog for assigning/removing methods
        self.child = assign.UI(self)
        self.child.on_open(
            self.selected_workstation,
            self.test_methods_assigned
        )

    def _set_tests_methods(self, args):
        """
        Load Test Methods mapped to the workstation into the right list.
        Also fill self.test_methods_assigned so the child window knows
        which methods are already assigned.
        """
        # Clear current list and state
        self._clear_tests_methods()

        sql = """
            SELECT
                test_methods.test_method_id,
                tests.description AS test_descr,
                test_methods.code,
                IFNULL(workstation_test_methods.external_code, '') AS external_code,
                IFNULL(samples.description, 'NA')  AS sample_descr,
                IFNULL(methods.description, 'NA')  AS method_descr,
                IFNULL(units.description,   'NA')  AS unit_descr,
                IFNULL(categories.description, '') AS category_descr,
                test_methods.status
            FROM workstation_test_methods
            JOIN test_methods
                ON workstation_test_methods.test_method_id = test_methods.test_method_id
            JOIN tests
                ON tests.test_id = test_methods.test_id
            LEFT JOIN samples
                ON test_methods.sample_id = samples.sample_id
            LEFT JOIN methods
                ON test_methods.method_id = methods.method_id
            LEFT JOIN units
                ON test_methods.unit_id = units.unit_id
            LEFT JOIN categories
                ON test_methods.category_id = categories.category_id
            WHERE workstation_test_methods.workstation_id = ?
              AND tests.status = 1
              AND test_methods.status = 1
            ORDER BY tests.description ASC;
        """

        rows = self.engine.read(True, sql, args)
        if not rows:
            return

        for row in rows:
            test_method_id = row["test_method_id"]
            test_descr     = row["test_descr"]
            code           = row["code"]
            external_code  = row["external_code"]
            sample_descr   = row["sample_descr"]
            method_descr   = row["method_descr"]
            unit_descr     = row["unit_descr"]
            category_descr = row["category_descr"]
            status         = int(row["status"])

            self.test_methods_assigned.append(test_method_id)

            tags = ("inactive",) if status != 1 else ()

            self.lstTestsMethods.insert(
                "",
                tk.END,
                iid=str(test_method_id),
                text=str(test_method_id),
                values=(test_descr, code, external_code, sample_descr, method_descr, unit_descr, category_descr),
                tags=tags
            )

    def on_remove_mapping(self, _evt=None):
        """
        Remove the selected test method mapping from the workstation.

        Permission is already checked via button state (disabled if no permission).
        """
        # 1) Get selected method in the right-side Treeview
        sel = self.lstTestsMethods.selection()
        if not sel:
            return  # Nothing selected → fail-fast

        iid = sel[0]
        values = self.lstTestsMethods.item(iid, "values")

        # Guard: inconsistent row structure
        if not values:
            return

        test_descr = values[0]  # First column is the test description

        # 3) Retrieve the workstation name (if available)
        ws_name = ""
        if self.selected_workstation:
            ws_name = self.selected_workstation.get("description", "")

        # 4) Confirmation dialog
        msg = f"{_('Remove')} '{test_descr}' {_('from workstation')} '{ws_name}'?"
        if not messagebox.askyesno(self.engine.app_title, msg, parent=self):
            return  # User cancelled → safe exit

        # 5) Ensure PK is a valid integer
        try:
            pk = int(iid)
        except Exception as e:
            return  # Fail-fast: invalid iid


        if not self.selected_workstation:
            return  # extra fail-safe, just in case

        # 6) Delete mapping from database
        sql = """
            DELETE FROM workstation_test_methods
            WHERE workstation_id = ?
              AND test_method_id = ?;
        """
        args = (
            self.selected_workstation["workstation_id"],
            pk
        )

        result = self.engine.write(sql, args)
        if result is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = _("Delete failed.")
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        # 7) Refresh the right panel
        self._set_tests_methods((self.selected_workstation["workstation_id"],))

        # 8) Notify the child window (if present)
        try:
            if (
                self.child
                and self.child.winfo_exists()
                and self.child.winfo_name() == "assign_test_methods"
            ):
                self.child.refresh_from_parent()
        except Exception as e:
            # Fail-safe: never crash because of child inconsistencies
            pass

        # 9) Refresh other windows (main: set_workstations)
        # Usa il dispatcher centrale dell'Engine
        if hasattr(self.engine, "refresh_windows_for_table"):
            self.engine.refresh_windows_for_table("workstation_test_methods")


    def refresh_from_tests(self):
        """
        Refresh the right-hand list (self.lstTestsMethods) when tests / test_methods
        have been edited elsewhere.

        It keeps the current tree context and, if a workstation is selected,
        reloads only the mapped test methods list.
        """
        # No workstation selected → just clear the list
        if not self.selected_workstation:
            self._clear_tests_methods()
            return

        try:
            ws_id = self.selected_workstation.get("workstation_id")
        except Exception as e:
            return

        if ws_id is None:
            self._clear_tests_methods()
            return

        # Reuse the existing loader (expects a tuple argument)
        self._set_tests_methods((ws_id,))


    def on_test_method_activated(self, evt=None):
        """
        Double-click on test method: dispatch to edit or remove based on radiobox.

        Permission required: Admin/Superuser only.
        """
        if not self.engine.can_validate_qc():
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.user_not_enable,
                parent=self
            )
            return

        sel = self.lstTestsMethods.selection()
        if not sel:
            return

        action = self.action_var.get()
        if action == "edit":
            self.on_edit_external_code()
        elif action == "remove":
            self.on_remove_mapping()

    def on_edit_external_code(self, evt=None):
        """
        Open dialog to edit external_code for the selected test method mapping.
        """
        # 1) Get selected item
        sel = self.lstTestsMethods.selection()
        if not sel:
            return

        iid = sel[0]
        values = self.lstTestsMethods.item(iid, "values")
        if not values:
            return

        test_descr = values[0]
        current_external_code = values[2]  # external_code is third column

        # 2) Ensure workstation is selected
        if not self.selected_workstation:
            return

        try:
            test_method_id = int(iid)
        except ValueError:
            return

        # 3) Simple dialog to edit external code
        from tkinter import simpledialog

        new_code = simpledialog.askstring(
            _("Edit External Code"),
            f"{_('External code for')} '{test_descr}':",
            initialvalue=current_external_code,
            parent=self
        )

        # User cancelled
        if new_code is None:
            return

        # Normalize: empty string → NULL
        new_code = new_code.strip() if new_code else None

        # 4) Update database
        sql = """
            UPDATE workstation_test_methods
            SET external_code = ?
            WHERE workstation_id = ?
              AND test_method_id = ?;
        """
        args = (new_code, self.selected_workstation["workstation_id"], test_method_id)

        result = self.engine.write(sql, args)
        if result is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = _("Save failed.")
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        # 5) Refresh list
        self._set_tests_methods((self.selected_workstation["workstation_id"],))

    def _on_test_method_changed(self, data=None):
        """Observer callback: refresh when test_method data changes."""
        self.refresh_from_tests()

    def on_cancel(self, evt=None):
        """Close window."""
        self.engine.unsubscribe("test_method_changed", self._on_test_method_changed)
        self.engine.unsubscribe("tests_changed", self._on_test_method_changed)
        super().on_cancel(evt)
