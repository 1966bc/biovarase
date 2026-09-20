# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Batches Master Window

Hierarchical batch management interface for laboratory quality control.

This module provides a singleton master window that displays a three-pane
hierarchical view of QC batches organized by:
    - Sites → Labs → Sections → Workstations (left pane)
    - Test Methods assigned to selected workstation (middle pane)
    - Batches for selected test method + workstation (right pane)

The window implements role-based access control:
    - App Admin (role=0): See all organizations - global access
    - Country/Regional/Lab Admin (1-3): See descendants of their org
    - Superuser (role=4): QC validation within their lab
    - Technician (role=5): Data entry within their scope
    - Viewer (role=6): Read-only access

Architecture:
    - Singleton master window (PROJECT_RULES 7.1)
    - Uses pack() layout (PROJECT_RULES 7.2)
    - 100% dictionary-based data access (PROJECT_RULES 5.2)
    - Window registry pattern for Engine communication (PROJECT_RULES 16.3)
    - Three-tier role-based filtering (admin/superuser/technician)
"""

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ui.parent_view import ParentView
import ui.batch as batch

# Module constants
STATUS_ACTIVE = 1

# Pane weight ratios (left, middle, right)
PANE_WEIGHTS = (0.28, 0.36, 0.36)

# Tree node types (now based on organizations.org_type)
NODE_TYPE_COUNTRY = "country"
NODE_TYPE_REGION = "region"
NODE_TYPE_SITE = "site"
NODE_TYPE_LAB = "lab"
NODE_TYPE_SECTION = "section"
NODE_TYPE_WORKSTATION = "workstation"

# Legacy aliases for backward compatibility
NODE_TYPE_SITES = NODE_TYPE_SITE
NODE_TYPE_LABS = NODE_TYPE_LAB
NODE_TYPE_SECTIONS = NODE_TYPE_SECTION
NODE_TYPE_WORKSTATIONS = NODE_TYPE_WORKSTATION

# User roles - imported from engine for consistency
from engine import (
    ROLE_APP_ADMIN, ROLE_COUNTRY_ADMIN, ROLE_REGIONAL_ADMIN,
    ROLE_LAB_ADMIN, ROLE_SUPERUSER, ROLE_TECHNICIAN, ROLE_VIEWER
)
# Legacy aliases
ROLE_ADMIN = ROLE_APP_ADMIN
ROLE_AUTOLOGIN = ROLE_VIEWER


class UI(ParentView):
    """
    Batches master window (singleton).

    Provides hierarchical batch management through a three-pane interface:
        - Left pane: Site/Lab/Section/Workstation tree navigation
        - Middle pane: Test methods assigned to selected workstation
        - Right pane: Batches for selected test method + workstation combination

    Role-Based Access Control:
        - App Admin (role=0): Global view, all organizations
        - Country/Regional/Lab Admin (1-3): Descendants of their org
        - Superuser (role=4): Lab-wide QC management
        - Technician (role=5): Data entry in assigned scope
        - Viewer (role=6): Read-only access

    Data Filtering:
        App Admin → No filtering (global)
        Admin hierarchy → WHERE org_id IN descendants
        Superuser/Technician/Viewer → WHERE lab_id = ?

    Attributes:
        _loaded: Flag for lazy tree loading
        _weights: Pane weight ratios for sash placement
        selected_workstation: Currently selected workstation (dict)
        selected_test_method: Currently selected test method (dict)
        selected_batch: Currently selected batch (dict)
        child: Reference to open batch editor window
    """

    def __init__(self, parent):
        """
        Initialize the batches window.

        Args:
            parent: Parent widget (usually main window)
        """
        super().__init__(parent, name="batches")

        if self._reusing:
            return

        self._loaded = False
        self.resizable(True, True)
        self.geometry("900x600")

        # Selection state
        self.child = None
        self.selected_workstation = None
        self.selected_test_method = None
        self.selected_batch = None

        # Subscribe to events (Observer pattern)
        self.engine.subscribe("batch_changed", self._on_batch_changed)
        self.engine.subscribe("tests_changed", self._on_tests_changed)
        self.engine.subscribe("test_method_changed", self._on_tests_changed)

        # Build interface
        self._build_ui()

        # Set minimum size and show
        self.update_idletasks()
        self.minsize(800, 500)
        self.show()

    # ---------------------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------------------
    def _build_ui(self):
        """
        Build the three-pane interface.

        Creates:
            - Left pane: Hierarchical tree (Sites → Labs → Sections → Workstations)
            - Middle pane: Test methods list
            - Right pane: Batches list

        Uses pack() layout as required for master windows (PROJECT_RULES 7.2).
        Widget creation follows Inventarium pattern (direct ttk.Treeview).
        """
        # PanedWindow must be stored on self (used by _place_sashes)
        self.pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        self.pw.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        # Remember pane weight ratios for sash placement
        self._weights = PANE_WEIGHTS

        pane_left = ttk.Frame(self.pw, style="App.TFrame")
        pane_mid = ttk.Frame(self.pw, style="App.TFrame")
        pane_right = ttk.Frame(self.pw, style="App.TFrame")

        self.pw.add(pane_left, minsize=160)
        self.pw.add(pane_mid, minsize=300)
        self.pw.add(pane_right, minsize=300)

        # ---------------------------------------------------------------------
        # Left pane: Sites → Labs → Sections → Workstations (hierarchical tree)
        # ---------------------------------------------------------------------
        self.Sites = ttk.Treeview(pane_left, show="tree")

        self.Sites.column("#0", width=220, minwidth=180, stretch=True)
        self.Sites.heading("#0", text="Sites", anchor=tk.W)

        sb_sites = ttk.Scrollbar(pane_left, orient=tk.VERTICAL, command=self.Sites.yview)
        self.Sites.configure(yscrollcommand=sb_sites.set)
        self.Sites.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_sites.pack(side=tk.RIGHT, fill=tk.Y)

        self.Sites.bind("<<TreeviewSelect>>", self._on_branch_selected)

        # ---------------------------------------------------------------------
        # Middle pane: Test Methods
        # ---------------------------------------------------------------------
        frm_tests = ttk.Frame(pane_mid)
        self.lblTests = ttk.LabelFrame(frm_tests, style="App.TLabelframe", text="Test Methods")

        cols_tests = ("test", "code", "sample", "method", "unit")
        self.lstTestsMethods = ttk.Treeview(self.lblTests, columns=cols_tests, show="headings")

        self.lstTestsMethods.column("test", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("test", text="Test", anchor=tk.W)

        self.lstTestsMethods.column("code", width=60, minwidth=60, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("code", text="Code", anchor=tk.W)

        self.lstTestsMethods.column("sample", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("sample", text="Sample", anchor=tk.W)

        self.lstTestsMethods.column("method", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("method", text="Method", anchor=tk.W)

        self.lstTestsMethods.column("unit", width=80, minwidth=80, anchor=tk.W, stretch=True)
        self.lstTestsMethods.heading("unit", text="Unit", anchor=tk.W)

        sb_tests = ttk.Scrollbar(self.lblTests, orient=tk.VERTICAL, command=self.lstTestsMethods.yview)
        self.lstTestsMethods.configure(yscrollcommand=sb_tests.set)
        self.lstTestsMethods.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_tests.pack(side=tk.RIGHT, fill=tk.Y)

        # Tags for status (use foreground for better ttk theme compatibility)
        self.lstTestsMethods.tag_configure("status", foreground="gray")

        self.lstTestsMethods.bind("<<TreeviewSelect>>", self._on_test_method_selected)
        self.lstTestsMethods.bind("<Double-1>", self._on_test_method_activated)

        self.lblTests.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        frm_tests.pack(fill=tk.BOTH, expand=1)

        # ---------------------------------------------------------------------
        # Right pane: Batches
        # ---------------------------------------------------------------------
        frm_batches = ttk.Frame(pane_right)
        self.lblBatches = ttk.LabelFrame(frm_batches, style="App.TLabelframe", text="Batches")

        cols_batches = ("control", "lot", "description", "expiration", "target")
        self.lstBatches = ttk.Treeview(self.lblBatches, columns=cols_batches, show="headings")

        self.lstBatches.column("control", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstBatches.heading("control", text="Control", anchor=tk.W)

        self.lstBatches.column("lot", width=80, minwidth=80, anchor=tk.W, stretch=True)
        self.lstBatches.heading("lot", text="Lot", anchor=tk.W)

        self.lstBatches.column("description", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstBatches.heading("description", text="Description", anchor=tk.W)

        self.lstBatches.column("expiration", width=80, minwidth=80, anchor=tk.CENTER, stretch=True)
        self.lstBatches.heading("expiration", text="Expiration", anchor=tk.CENTER)

        self.lstBatches.column("target", width=80, minwidth=80, anchor=tk.CENTER, stretch=True)
        self.lstBatches.heading("target", text="Target", anchor=tk.CENTER)

        sb_batches = ttk.Scrollbar(self.lblBatches, orient=tk.VERTICAL, command=self.lstBatches.yview)
        self.lstBatches.configure(yscrollcommand=sb_batches.set)
        self.lstBatches.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_batches.pack(side=tk.RIGHT, fill=tk.Y)

        # Tags for status and expired/expiring batches
        # Use foreground for status (better ttk theme compatibility)
        self.lstBatches.tag_configure("status", foreground="gray")
        self.lstBatches.tag_configure("expired", background="coral")
        self.lstBatches.tag_configure("expiring", background="khaki")

        self.lstBatches.bind("<<TreeviewSelect>>", self._on_batch_selected)
        self.lstBatches.bind("<Double-1>", self._on_batch_activated)

        self.lblBatches.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        frm_batches.pack(fill=tk.BOTH, expand=1)

        # Place sashes after first draw
        self.after_idle(self._place_sashes)

    def _place_sashes(self):
        """
        Place PanedWindow sashes based on configured weight ratios.

        Uses self._weights to calculate proportional sash positions.
        Retries if window width not yet available.
        Fail-safe: does nothing if placement fails.
        """
        try:
            if not hasattr(self, "pw") or not hasattr(self, "_weights"):
                return

            w = self.pw.winfo_width()
            if w <= 1:
                # Window not yet drawn, retry after 50ms
                self.after(50, self._place_sashes)
                return

            a, b, c = self._weights
            tot = a + b + c
            x0 = int(w * (a / tot))
            x1 = int(w * ((a + b) / tot))

            self.pw.sash_place(0, x0, 1)
            self.pw.sash_place(1, x1, 1)
        except (AttributeError, tk.TclError) as e:
            # Fail safe: do nothing if sash placement fails
            pass

    # ---------------------------------------------------------------------
    # Window Lifecycle
    # ---------------------------------------------------------------------
    def on_open(self):
        """
        Called when window is opened or re-opened.

        Performs lazy loading of the tree on first open.
        Sets window title and loads hierarchical data.
        """
        self.title("Batches — Workstations ↔ Test Methods")

        # Lazy load of the tree
        try:
            if not getattr(self, "_loaded", False):
                self._load_tree()
                self._loaded = True
        except (AttributeError, ValueError, KeyError) as e:
            self.engine.on_log("on_open", e, type(e), sys.modules[__name__])
            # Fail safe: keep window usable even if tree loading fails

    # ---------------------------------------------------------------------
    # Tree Loading
    # ---------------------------------------------------------------------
    def reload(self):
        """
        Force reload of the entire tree.

        Used when data changes externally (e.g., after adding new workstation).
        """
        try:
            self._load_tree()
            self._loaded = True
        except (AttributeError, ValueError, KeyError) as e:
            self.engine.on_log("reload", e, type(e), sys.modules[__name__])

    def _load_tree(self, _evt=None):
        """
        Populate the Organizations hierarchy tree from the organizations table.

        Structure: Country → Region → Site → Lab → Section → Workstation

        Role-based filtering:
            - App Admin (role=0): See all organizations
            - Country Admin (role=1): See their country and descendants
            - Regional Admin (role=2): See their region and descendants
            - Lab Admin+ (role>=3): See ONLY their assigned lab and sections

        Args:
            _evt: Optional Tkinter event (unused, for event binding compatibility)
        """
        self.Sites.delete(*self.Sites.get_children())
        root = self.Sites.insert("", tk.END, iid="root", text="Organizations")

        # Determine user role and org scope
        try:
            role = int(self.engine.log_user.get("role", ROLE_TECHNICIAN))
        except (ValueError, TypeError, KeyError):
            role = ROLE_TECHNICIAN

        user_org_id = self.engine.log_user.get("org_id")

        if role == ROLE_APP_ADMIN:  # App Admin - full tree
            self._build_full_tree(root)
        elif role >= ROLE_LAB_ADMIN:  # Lab Admin, Superuser, Technician, Viewer - only their lab
            self._build_lab_only_tree(root, user_org_id)
        else:  # Country/Regional Admin (role 1-2) - their scope and descendants
            self._build_scoped_tree(root, user_org_id, role)

        self.Sites.item(root, open=True)
        # Auto-expand all nodes for better UX
        self._expand_all(root)

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

        try:
            rows = self.engine.read(True, sql, args) or []
            return [(r["org_id"], r["description"]) for r in rows]
        except Exception as e:
            self.engine.on_log("_load_orgs_by_type", e, type(e), sys.modules[__name__])
            return []

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
        try:
            rows = self.engine.read(True, sql, (section_org_id,)) or []
            return [(r["workstation_id"], r["description"]) for r in rows]
        except Exception as e:
            self.engine.on_log("_load_workstations", e, type(e), sys.modules[__name__])
            return []

    # Legacy methods for backward compatibility (deprecated)
    def _load_labs(self, site_id):
        """Deprecated: Use _load_orgs_by_type instead."""
        return self._load_orgs_by_type(site_id, "lab")

    def _load_sections(self, lab_id):
        """Deprecated: Use _load_orgs_by_type instead."""
        return self._load_orgs_by_type(lab_id, "section")

    # ---------------------------------------------------------------------
    # Selection Handlers
    # ---------------------------------------------------------------------
    def _on_branch_selected(self, _evt=None):
        """
        Handle tree node selection.

        If a workstation is selected, loads its test methods.
        If a non-workstation node is selected, clears test methods and batches.

        Args:
            _evt: Tkinter event (unused, for event binding compatibility)
        """
        iid = self.Sites.focus()
        if not iid:
            return

        item = self.Sites.item(iid)
        vals = item.get("values") or []
        if len(vals) < 2:
            return

        ref_id, ref_type = vals[0], vals[1]
        if ref_type != NODE_TYPE_WORKSTATIONS:
            # Clear middle/right panes when not on a workstation
            self.lstTestsMethods.delete(*self.lstTestsMethods.get_children())
            self.lstBatches.delete(*self.lstBatches.get_children())
            self.lblTests["text"] = f"Test Methods: 0"
            self.lblBatches["text"] = f"Batches 0"
            self.selected_workstation = None
            self.selected_test_method = None
            self.selected_batch = None
            return

        try:
            pk = int(ref_id)
        except (ValueError, TypeError) as e:
            return

        self.selected_workstation = self.engine.get_selected(
            "workstations",
            "workstation_id",
            pk,
        )
        if not self.selected_workstation:
            return

        self._set_tests_methods()

    def _set_tests_methods(self):
        """
        Load test methods assigned to the currently selected workstation.

        Populates the middle pane (test methods list).
        Clears the batches list (right pane).
        """
        # Clear existing lists
        self.lstTestsMethods.delete(*self.lstTestsMethods.get_children())
        self.lstBatches.delete(*self.lstBatches.get_children())
        self.lblBatches["text"] = f"Batches 0"

        if not self.selected_workstation:
            self.lblTests["text"] = f"Test Methods: 0"
            return

        workstation_id = self.selected_workstation["workstation_id"]

        sql = """
            SELECT
                test_methods.test_method_id,
                tests.description AS test_description,
                test_methods.code,
                IFNULL(samples.description, 'NA') AS sample,
                IFNULL(methods.description, 'NA') AS method,
                IFNULL(units.description, 'NA') AS unit,
                test_methods.status
            FROM
                workstation_test_methods
            JOIN
                test_methods ON workstation_test_methods.test_method_id = test_methods.test_method_id
            JOIN
                tests ON tests.test_id = test_methods.test_id
            LEFT JOIN
                samples ON test_methods.sample_id = samples.sample_id
            LEFT JOIN
                methods ON test_methods.method_id = methods.method_id
            LEFT JOIN
                units ON test_methods.unit_id = units.unit_id
            WHERE
                workstation_test_methods.workstation_id = ?
            AND
                test_methods.status = 1
            AND
                tests.status = 1
            ORDER BY
                tests.description ASC;
        """

        rs = self.engine.read(True, sql, (workstation_id,)) or []

        count = 0
        for row in rs:
            status = int(row["status"])
            tags = ("status",) if status != STATUS_ACTIVE else ()
            self.lstTestsMethods.insert(
                "",
                tk.END,
                iid=str(row["test_method_id"]),
                text=str(row["test_method_id"]),
                values=(
                    row["test_description"],
                    row["code"],
                    row["sample"],
                    row["method"],
                    row["unit"],
                ),
                tags=tags,
            )
            count += 1

        self.lblTests["text"] = f"Test Methods: {count}"

    def set_batches(self):
        """
        Load batches for the selected test method and workstation.

        Populates the right pane (batches list).
        Only loads batches that have both lot_number and expiration date.
        """
        self.lstBatches.delete(*self.lstBatches.get_children())
        self.lblBatches["text"] = f"Batches 0"

        if not (self.selected_test_method and self.selected_workstation):
            return

        test_method_id = self.selected_test_method["test_method_id"]
        workstation_id = self.selected_workstation["workstation_id"]

        sql = """
            SELECT
                batches.batch_id,
                controls.description AS control,
                batches.lot_number   AS lot,
                batches.description  AS batch_description,
                DATE_FORMAT(batches.expiration, '%d-%m-%Y') AS expiration,
                ROUND(batches.target, 3) AS target,
                batches.status
            FROM
                batches
            JOIN
                controls ON batches.control_id = controls.control_id
            WHERE
                batches.test_method_id = ?
                AND batches.workstation_id = ?
                AND batches.lot_number IS NOT NULL
                AND batches.expiration IS NOT NULL
            ORDER BY
                batches.expiration DESC,
                batches.rank ASC;
        """

        rs = self.engine.read(True, sql, (test_method_id, workstation_id)) or []

        count = 0
        for row in rs:
            status = int(row["status"])
            tags = ("status",) if status != STATUS_ACTIVE else ()

            self.lstBatches.insert(
                "",
                tk.END,
                iid=str(row["batch_id"]),
                text=str(row["batch_id"]),
                values=(
                    row["control"],
                    row["lot"],
                    row["batch_description"],
                    row["expiration"],
                    row["target"],
                ),
                tags=tags,
            )
            count += 1

        self.lblBatches["text"] = f"Batches {count}"

    # ---------------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------------
    def _on_test_method_selected(self, _evt=None):
        """
        Handle test method selection in the middle pane.

        Loads batches for the selected test method + workstation combination.

        Args:
            _evt: Tkinter event (unused, for event binding compatibility)
        """
        sel = self.lstTestsMethods.selection()
        if not sel:
            self.selected_test_method = None
            self.lstBatches.delete(*self.lstBatches.get_children())
            self.lblBatches["text"] = f"Batches 0"
            return

        try:
            pk = int(sel[0])
        except (ValueError, TypeError) as e:
            return

        self.selected_test_method = self.engine.get_selected(
            "test_methods",
            "test_method_id",
            pk,
        )
        self.set_batches()

    def _on_test_method_activated(self, _evt=None):
        """
        Handle double-click on test method.

        Opens batch editor in INSERT mode to create a new batch
        for the selected test method + workstation combination.

        Args:
            _evt: Tkinter event (unused, for event binding compatibility)
        """
        sel = self.lstTestsMethods.selection()
        if not sel:
            return

        try:
            pk = int(sel[0])
        except (ValueError, TypeError) as e:
            return

        self.selected_test_method = self.engine.get_selected(
            "test_methods",
            "test_method_id",
            pk,
        )
        if not self.selected_test_method or not self.selected_workstation:
            return

        try:
            if hasattr(self, "child") and self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except (AttributeError, tk.TclError) as e:
            pass

        self.child = batch.UI(self)
        self.child.on_open(self.selected_test_method, self.selected_workstation)

    def _on_batch_selected(self, _evt=None):
        """
        Handle batch selection in the right pane.

        Args:
            _evt: Tkinter event (unused, for event binding compatibility)
        """
        sel = self.lstBatches.selection()
        if not sel:
            self.selected_batch = None
            return

        try:
            pk = int(sel[0])
        except (ValueError, TypeError) as e:
            return

        self.selected_batch = self.engine.get_selected("batches", "batch_id", pk)

    def _on_batch_activated(self, _evt=None):
        """
        Handle double-click on batch.

        Opens batch editor in UPDATE mode to edit the selected batch.

        Args:
            _evt: Tkinter event (unused, for event binding compatibility)
        """
        sel_batch = self.lstBatches.selection()
        if not sel_batch:
            return
        try:
            batch_id = int(sel_batch[0])
        except (ValueError, TypeError) as e:
            return

        self.selected_batch = self.engine.get_selected("batches", "batch_id", batch_id)
        if not self.selected_batch:
            return

        sel_test = self.lstTestsMethods.selection()
        if not sel_test:
            return
        try:
            test_method_id = int(sel_test[0])
        except (ValueError, TypeError) as e:
            return

        self.selected_test_method = self.engine.get_selected(
            "test_methods",
            "test_method_id",
            test_method_id,
        )
        if not self.selected_test_method or not self.selected_workstation:
            return

        try:
            if hasattr(self, "child") and self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except (AttributeError, tk.TclError) as e:
            pass

        self.child = batch.UI(self, index=batch_id)
        self.child.on_open(self.selected_test_method, self.selected_workstation, self.selected_batch)

    # ---------------------------------------------------------------------
    # Observer Pattern Callbacks
    # ---------------------------------------------------------------------
    def _on_batch_changed(self, data=None):
        """
        Callback when a batch is modified elsewhere.

        Refreshes the batches list for the current selection.

        Args:
            data: Optional event data (unused)
        """
        self.set_batches()

    def _on_tests_changed(self, data=None):
        """
        Callback when a test is modified (e.g., status changed).

        Refreshes the test methods list for the current workstation.

        Args:
            data: Optional event data (unused)
        """
        if self.selected_workstation:
            self.set_test_methods()

    def on_cancel(self, evt=None):
        """
        Close window safely.

        Unsubscribes from events, closes any open child editor,
        and calls parent cleanup.

        Args:
            evt: Tkinter event (unused, for event binding compatibility)
        """
        # Unsubscribe from events (Observer pattern)
        self.engine.unsubscribe("batch_changed", self._on_batch_changed)
        self.engine.unsubscribe("tests_changed", self._on_tests_changed)
        self.engine.unsubscribe("test_method_changed", self._on_tests_changed)

        if self.child is not None:
            try:
                self.child.destroy()
            except Exception:
                pass
        super().on_cancel(evt)
