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

Role-based access control (three-tier filtering):
    - Admin (role=0):       See all sites (multi-site system administration)
    - Superuser (role=1):   See all sections in their lab (QC validation)
    - Technician (role=2):  See only their section (data entry)
    - Autologin (role=3):   See only their section (read-only)

Key features:
    - Hierarchical tree navigation (left panel)
    - Test methods list for selected workstation (right panel)
    - Double-click workstation: assign new test methods
    - Double-click test method: remove mapping

Singleton window (per PROJECT_RULES.md section 7.1).
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import views.assign_test_methods as assign

# User role constants (must match engine.py)
ROLE_ADMIN = 0       # System administrator - multi-site configuration
ROLE_SUPERUSER = 1   # Lab manager - QC validation + lab-wide access
ROLE_TECHNICIAN = 2  # Section worker - data entry + section-only access
ROLE_AUTOLOGIN = 3   # Guest user - read-only access

# Tree node labels
TREE_ROOT_LABEL = "Sites"


class UI(tk.Toplevel):

    _instance = None  

    def __new__(cls, parent):
        """Return the existing instance if alive; otherwise create a new one."""
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus)
                    return cls._instance
            except Exception as e:
                cls._instance = None
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
        """
        Guarded initializer: when the instance is reused, skip widget rebuilds.
        """
        if getattr(self, "_is_init", False):
            self.parent = parent
            return
        super().__init__(name="workstation_test_methods")

         # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       

        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self
        
        self.resizable(True, True)
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        # Hotkeys
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)

        self.child = None  
        self.selected_workstation = None
        self.test_methods_assigned = []
                
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


    def _build_ui(self):

        pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        pw.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        pane_left  = ttk.Frame(pw, style="App.TFrame")
        pane_right = ttk.Frame(pw, style="App.TFrame")

        pw.add(pane_left,  minsize=160)
        pw.add(pane_right, minsize=300)

        # Left: tree        
        cols_left = (["#0", "",  "w", False, 240, 300],
                     ["#1", "",  "w", False,   0,   0])
        self.Sites = self.engine.get_tree(pane_left, cols_left, show="tree")
        self.Sites["displaycolumns"] = ()
        self.Sites.bind("<<TreeviewSelect>>", self.on_branch_selected)
        self.Sites.bind("<Double-1>", self.on_branch_activated)

        # Right: list of mapped methods
        frm_right = ttk.Frame(pane_right, style="App.TFrame", relief=tk.GROOVE, padding=8)
        frm_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        cols_right = (["#0", "id",     "w", False,   0,   0],
                      ["#1", "Test",   "w", True,  220, 220],
                      ["#2", "Code",   "w", True,   90,  90],
                      ["#3", "Sample", "w", True,  120, 120],
                      ["#4", "Method", "w", True,  140, 140],
                      ["#5", "Unit",   "w", True,   90,  90])
        self.lstTestsMethods = self.engine.get_tree(frm_right, cols_right)
        self.lstTestsMethods.tag_configure("inactive", background="light gray")
        self.lstTestsMethods.bind("<Double-1>", self.on_test_method_activated)
        self.lstTestsMethods.pack(fill=tk.BOTH, expand=1)

    def on_open(self):
        self.title("Workstations — Test Methods Mapping")
        self._load_tree()
        

    def _load_tree(self):
        """
        Build the hierarchy tree: Sites → Labs → Sections → Workstations.

        Implements three-tier role-based filtering:
            - Admin (role=0):       See all active sites (multi-site view)
            - Superuser (role=1):   See all sections in their lab (lab-wide)
            - Technician/Autologin: See only their section (section-only)

        The filtering is done at the SQL level for optimal performance.
        """

        # 1) Clear any existing nodes
        for iid in self.Sites.get_children():
            self.Sites.delete(iid)

        # 2) Create the root node for the hierarchy
        root_iid = "sites_root"
        root = self.Sites.insert("", tk.END, iid=root_iid, text=TREE_ROOT_LABEL)

        # 3) Get user role with fail-safe default
        try:
            role = int(self.engine.log_user.get("role", ROLE_TECHNICIAN))
        except (ValueError, TypeError, KeyError) as e:
            role = ROLE_TECHNICIAN  # Fail safe: restrict to section level

        # 4) Fetch sites based on role (three-tier filtering)
        if role == ROLE_ADMIN:
            # Admin: See all sites (multi-site system administration)
            sql = """
                SELECT
                    sites.site_id          AS site_id,
                    suppliers.description  AS site_name
                FROM sites
                JOIN suppliers
                    ON suppliers.supplier_id = sites.comp_id
                WHERE sites.status = 1
                ORDER BY suppliers.description ASC;
            """
            args = ()

        elif role == ROLE_SUPERUSER:
            # Superuser: See all sections in their laboratory (QC validation)
            sql = """
                SELECT
                    sites.site_id          AS site_id,
                    suppliers.description  AS site_name
                FROM labs
                JOIN sites
                    ON sites.site_id = labs.site_id
                JOIN suppliers
                    ON suppliers.supplier_id = sites.comp_id
                WHERE labs.lab_id = ?
                  AND sites.status = 1
                ORDER BY suppliers.description ASC;
            """
            lab_id = self.engine.current_ids.get("lab_id")
            args = (lab_id,)

        else:  # TECHNICIAN (role=2) or AUTOLOGIN (role=3)
            # Technician/Autologin: See only their section
            sql = """
                SELECT
                    sites.site_id          AS site_id,
                    suppliers.description  AS site_name
                FROM sections
                JOIN labs
                    ON labs.lab_id = sections.lab_id
                JOIN sites
                    ON sites.site_id = labs.site_id
                JOIN suppliers
                    ON suppliers.supplier_id = sites.comp_id
                WHERE sections.section_id = ?
                  AND sites.status = 1
                ORDER BY suppliers.description ASC;
            """
            section_id = int(self.engine.get_section_id())
            args = (section_id,)

        rs_sites = self.engine.read(True, sql, args)

        # Guard: no sites found → just open the root and exit
        if not rs_sites:
            self.Sites.item(root_iid, open=True)
            return

        # 5) Build the tree: Sites → Labs → Sections → Workstations
        for row_site in rs_sites:
            site_id   = row_site["site_id"]
            site_name = row_site["site_name"]

            site_iid = f"site_{site_id}"
            self.Sites.insert(
                root,
                tk.END,
                iid=site_iid,
                text=site_name,
                values=(site_id, "sites")
            )

            rs_labs = self._load_labs(site_id, role)
            if not rs_labs:
                continue  # No labs for this site

            for row_lab in rs_labs:
                lab_id   = row_lab["lab_id"]
                lab_name = row_lab["lab_name"]

                lab_iid = f"lab_{lab_id}"
                self.Sites.insert(
                    site_iid,
                    tk.END,
                    iid=lab_iid,
                    text=lab_name,
                    values=(lab_id, "labs")
                )

                rs_sections = self._load_sections(lab_id, role)
                if not rs_sections:
                    continue  # No sections for this lab

                for row_sec in rs_sections:
                    section_id   = row_sec["section_id"]
                    section_name = row_sec["section_name"]

                    sec_iid = f"sec_{section_id}"
                    self.Sites.insert(
                        lab_iid,
                        tk.END,
                        iid=sec_iid,
                        text=section_name,
                        values=(section_id, "sections")
                    )

                    rs_workstations = self._load_workstations(section_id)
                    if not rs_workstations:
                        continue  # No workstations for this section

                    for row_ws in rs_workstations:
                        workstation_id   = row_ws["workstation_id"]
                        workstation_name = row_ws["workstation_name"]

                        ws_iid = f"ws_{workstation_id}"
                        self.Sites.insert(
                            sec_iid,
                            tk.END,
                            iid=ws_iid,
                            text=workstation_name,
                            values=(workstation_id, "workstations")
                        )

        # 6) Expand the root node by default
        self.Sites.item(root_iid, open=True)


    def _load_labs(self, site_id, role):
        """
        Load labs for a given site, filtered by user role.

        Args:
            site_id: The site ID to filter labs
            role: User role (ADMIN, SUPERUSER, TECHNICIAN, AUTOLOGIN)

        Returns:
            List of lab dictionaries or None
        """
        if role == ROLE_ADMIN:
            # Admin: See all labs in this site
            sql = """
                SELECT
                    labs.lab_id        AS lab_id,
                    labs.description   AS lab_name
                FROM labs
                WHERE labs.site_id = ?
                  AND labs.status = 1
                ORDER BY labs.description ASC;
            """
            args = (site_id,)

        elif role == ROLE_SUPERUSER:
            # Superuser: See only their own lab (if it belongs to this site)
            sql = """
                SELECT
                    labs.lab_id        AS lab_id,
                    labs.description   AS lab_name
                FROM labs
                WHERE labs.site_id = ?
                  AND labs.lab_id = ?
                  AND labs.status = 1
                ORDER BY labs.description ASC;
            """
            lab_id = self.engine.current_ids.get("lab_id")
            args = (site_id, lab_id)

        else:  # TECHNICIAN or AUTOLOGIN
            # Technician/Autologin: See only the lab containing their section
            sql = """
                SELECT
                    labs.lab_id        AS lab_id,
                    labs.description   AS lab_name
                FROM sections
                JOIN labs
                    ON labs.lab_id = sections.lab_id
                WHERE labs.site_id = ?
                  AND sections.section_id = ?
                  AND labs.status = 1
                ORDER BY labs.description ASC;
            """
            section_id = int(self.engine.get_section_id())
            args = (site_id, section_id)

        return self.engine.read(True, sql, args)


    def _load_sections(self, lab_id, role):
        """
        Load sections for a given lab, filtered by user role.

        Args:
            lab_id: The lab ID to filter sections
            role: User role (ADMIN, SUPERUSER, TECHNICIAN, AUTOLOGIN)

        Returns:
            List of section dictionaries or None
        """
        if role == ROLE_ADMIN or role == ROLE_SUPERUSER:
            # Admin/Superuser: See all sections in this lab
            sql = """
                SELECT
                    sections.section_id      AS section_id,
                    sections.description     AS section_name
                FROM sections
                WHERE sections.lab_id = ?
                  AND sections.status = 1
                ORDER BY sections.description ASC;
            """
            args = (lab_id,)

        else:  # TECHNICIAN or AUTOLOGIN
            # Technician/Autologin: See only their own section
            sql = """
                SELECT
                    sections.section_id      AS section_id,
                    sections.description     AS section_name
                FROM sections
                WHERE sections.lab_id = ?
                  AND sections.section_id = ?
                  AND sections.status = 1
                ORDER BY sections.description ASC;
            """
            section_id = int(self.engine.get_section_id())
            args = (lab_id, section_id)

        return self.engine.read(True, sql, args)


    def _load_workstations(self, section_id):
        sql = """
            SELECT 
                workstations.workstation_id    AS workstation_id,
                workstations.description       AS workstation_name
            FROM workstations
            WHERE workstations.section_id = ?
              AND workstations.status = 1
            ORDER BY workstations.description ASC;
        """
        return self.engine.read(True, sql, (section_id,))

    def _clear_tests_methods(self):
        """Clear the right-hand list and reset assigned methods."""
        self.test_methods_assigned = []
        for iid in self.lstTestsMethods.get_children():
            self.lstTestsMethods.delete(iid)

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
        if ref_type != "workstations":
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
        if ref_type != "workstations":
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
                IFNULL(samples.description, 'NA')  AS sample_descr,
                IFNULL(methods.description, 'NA')  AS method_descr,
                IFNULL(units.description,   'NA')  AS unit_descr,
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
            WHERE workstation_test_methods.workstation_id = ?
            ORDER BY tests.description ASC;
        """

        rows = self.engine.read(True, sql, args)
        if not rows:
            return

        for row in rows:
            test_method_id = row["test_method_id"]
            test_descr     = row["test_descr"]
            code           = row["code"]
            sample_descr   = row["sample_descr"]
            method_descr   = row["method_descr"]
            unit_descr     = row["unit_descr"]
            status         = int(row["status"])

            self.test_methods_assigned.append(test_method_id)

            tags = ("inactive",) if status != 1 else ()

            self.lstTestsMethods.insert(
                "",
                tk.END,
                iid=str(test_method_id),
                text=str(test_method_id),
                values=(test_descr, code, sample_descr, method_descr, unit_descr),
                tags=tags
            )

    def on_test_method_activated(self, _evt=None):
        """
        Double-click on a test method: ask confirmation and remove
        the mapping from the selected workstation.

        Permission required: Admin/Superuser only (QC configuration).
        """

        # 1) Check permission (Admin/Superuser only can remove test methods)
        if not self.engine.can_validate_qc():
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.user_not_enable,
                parent=self
            )
            return

        # 2) Get selected method in the right-side Treeview
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
        msg = f"Remove '{test_descr}' from workstation '{ws_name}'?"
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

        self.engine.write(sql, args)

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


    def _on_cancel(self, _evt=None):
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
