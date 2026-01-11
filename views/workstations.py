# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from i18n import _
import views.workstation as workstation_ui
from views.parent_view import ParentView

# Tree node types (based on organizations.org_type)
NODE_TYPE_COUNTRY = "country"
NODE_TYPE_REGION = "region"
NODE_TYPE_LAB = "lab"
NODE_TYPE_SECTION = "section"


class UI(ParentView):

    def __init__(self, parent):
        super().__init__(parent, name="workstations")
        if self._reusing:
            return

        self.table = "workstations"
        self.primary_key = "workstation_id"

        self.selected_section_org_id = None  # org_id of selected section
        self.selected_workstation = None
        self.child = None

        self.resizable(True, True)
        self.bind("<Alt-c>", self.on_cancel)

        self._build_ui()
        self.show(on_screen=True)

    def _build_ui(self):
        """
        Build the full UI layout.

        Left pane: Sites/Labs/Sections hierarchy.
        Right pane: Workstations list for the selected Section.
        """
        # Paned container
        self.pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        self.pw.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)

        # -------------------------- LEFT PANE ----------------------------- #
        self.pane_left = ttk.Frame(self.pw, style="App.TFrame", padding=6)
        self.pw.add(self.pane_left, minsize=260)

        # Hierarchical tree: Country → Region → Site → Lab → Section
        self.Sites = ttk.Treeview(self.pane_left, show="tree")
        self.Sites.column("#0", width=260, minwidth=220, stretch=True)
        self.Sites.heading("#0", text=_("Organizations"), anchor=tk.W)

        sb_sites = ttk.Scrollbar(self.pane_left, orient=tk.VERTICAL, command=self.Sites.yview)
        self.Sites.configure(yscrollcommand=sb_sites.set)
        self.Sites.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_sites.pack(side=tk.RIGHT, fill=tk.Y)

        self.Sites.bind("<<TreeviewSelect>>", self.on_branch_selected)
        self.Sites.bind("<Double-1>", self.on_branch_activated)

        # -------------------------- RIGHT PANE ----------------------------- #
        self.pane_right = ttk.Frame(self.pw, style="App.TFrame", padding=6)
        self.pw.add(self.pane_right, minsize=480)

        lf = ttk.LabelFrame(self.pane_right, style="App.TLabelframe", text=_("Workstations"))
        lf.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        cols_ws = ("equipment", "workstation", "serial", "device_id")
        self.lstWorkstations = ttk.Treeview(lf, columns=cols_ws, show="headings")

        self.lstWorkstations.column("equipment", width=220, minwidth=220, anchor=tk.W, stretch=True)
        self.lstWorkstations.heading("equipment", text=_("Equipment:").rstrip(":"), anchor=tk.W)

        self.lstWorkstations.column("workstation", width=260, minwidth=260, anchor=tk.W, stretch=True)
        self.lstWorkstations.heading("workstation", text=_("Workstation:").rstrip(":"), anchor=tk.W)

        self.lstWorkstations.column("serial", width=140, minwidth=140, anchor=tk.W, stretch=True)
        self.lstWorkstations.heading("serial", text=_("Serial:").rstrip(":"), anchor=tk.W)

        self.lstWorkstations.column("device_id", width=200, minwidth=200, anchor=tk.W, stretch=True)
        self.lstWorkstations.heading("device_id", text=_("Device ID:").rstrip(":"), anchor=tk.W)

        sb_ws = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self.lstWorkstations.yview)
        self.lstWorkstations.configure(yscrollcommand=sb_ws.set)
        self.lstWorkstations.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_ws.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag used to highlight inactive workstations
        self.lstWorkstations.tag_configure("status", background=self.engine.get_rgb(211, 211, 211))

        self.lstWorkstations.bind("<<TreeviewSelect>>", self.on_workstation_selected)
        self.lstWorkstations.bind("<Double-1>", self.on_workstation_activated)

        
        # Place the sash after the widget has a valid width
        self.after(50, self._place_sashes)

    def _place_sashes(self, left_ratio: float = 0.35):
        """
        Place the sash between left and right panes using a fixed ratio.

        Args:
            left_ratio (float): Portion of the total width assigned
                                to the left pane.
        """
        try:
            width = self.pw.winfo_width()
            if width <= 1:
                # Called too early, try again a bit later
                self.after(60, self._place_sashes)
                return

            x0 = int(width * left_ratio)
            self.pw.sash_place(0, x0, 1)
        except Exception as e:
            # Never raise GUI errors from here
            pass
        
    def on_open(self):

        self.title(_("Workstations"))

        self._populate_sites_tree()
        
    def _populate_sites_tree(self):
        """
        Populate the tree with the full hierarchy from organizations table:

            Country → Region → Site → Lab → Section

        Role-based filtering:
        - App Admin (role=0): See all organizations
        - Other roles: Filtered by user's org_id scope
        """
        # Clear current content
        self.engine.clear_treeview(self.Sites)

        root_iid = "org_root"
        self.Sites.insert("", tk.END, iid=root_iid, text=_("Organizations"))

        # Get user role
        role = self.engine.log_user.get("role", 5)  # Default to technician
        user_org_id = self.engine.log_user.get("org_id")

        # Load countries (root level organizations)
        if role == 0:  # App Admin
            countries = self._load_orgs_by_type(None, "country")
        else:
            # Non-admin: find the country ancestor of user's org
            countries = self._get_user_country_scope(user_org_id)

        # Build the tree: Country → Region → Site → Lab → Section
        for country_id, country_name in countries:
            country_iid = f"country_{country_id}"
            self.Sites.insert(
                root_iid, tk.END, iid=country_iid,
                text=country_name,
            )

            # Load regions under this country
            regions = self._load_orgs_by_type(country_id, "region")
            for region_id, region_name in regions:
                region_iid = f"region_{region_id}"
                self.Sites.insert(
                    country_iid, tk.END, iid=region_iid,
                    text=region_name,
                )

                # Load sites (hospitals) under this region
                sites = self._load_orgs_by_type(region_id, "site")
                for site_id, site_name in sites:
                    site_iid = f"site_{site_id}"
                    self.Sites.insert(
                        region_iid, tk.END, iid=site_iid,
                        text=site_name,
                    )

                    # Load labs under this site
                    labs = self._load_orgs_by_type(site_id, "lab")
                    for lab_id, lab_name in labs:
                        lab_iid = f"lab_{lab_id}"
                        self.Sites.insert(
                            site_iid, tk.END, iid=lab_iid,
                            text=lab_name,
                        )

                        # Load sections under this lab
                        sections = self._load_orgs_by_type(lab_id, "section")
                        for section_id, section_name in sections:
                            sec_iid = f"section_{section_id}"
                            self.Sites.insert(
                                lab_iid, tk.END, iid=sec_iid,
                                text=section_name,
                            )

        self.Sites.item(root_iid, open=True)
        # Auto-expand first level for better UX
        for child in self.Sites.get_children(root_iid):
            self.Sites.item(child, open=True)

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

    def _get_user_country_scope(self, user_org_id):
        """
        Get the country scope for a non-admin user based on their org_id.

        Traverses up the organization hierarchy to find the country.

        Args:
            user_org_id: User's assigned org_id

        Returns:
            List containing the user's country (org_id, description)
        """
        if user_org_id is None:
            return self._load_orgs_by_type(None, "country")

        # Traverse up to find the country using recursive CTE
        sql = """
            WITH RECURSIVE ancestors AS (
                SELECT org_id, parent_id, org_type, description
                FROM organizations WHERE org_id = ?
                UNION ALL
                SELECT o.org_id, o.parent_id, o.org_type, o.description
                FROM organizations o
                JOIN ancestors a ON o.org_id = a.parent_id
            )
            SELECT org_id, description FROM ancestors WHERE org_type = 'country'
        """
        row = self.engine.read(False, sql, (user_org_id,))
        if row:
            return [(row["org_id"], row["description"])]

        return self._load_orgs_by_type(None, "country")

    def on_branch_selected(self, evt=None):
        """
        Called when a node is selected in the tree.

        Uses engine.parse_iid() to decode the iid into a structured dict
        (type + id), avoiding any positional indexing on Treeview values.
        """
        focus_iid = self.Sites.focus()
        if not focus_iid:
            self._reset_workstations()
            return

        # parse_iid returns: {"type": "section", "id": 7} etc.
        info = self.engine.parse_iid(focus_iid)
        if not info:
            self._reset_workstations()
            return

        kind = info.get("type")
        pk = info.get("id")

        if kind == NODE_TYPE_SECTION and pk is not None:
            # Store the section org_id
            self.selected_section_org_id = pk
            # Load workstations for this section (by org_id)
            self.set_workstations((pk,))
        else:
            # Only sections have workstations attached
            self._reset_workstations()

    def on_branch_activated(self, evt=None):
        """
        Double-click on a section: open dialog to add new workstation.
        """
        focus_iid = self.Sites.focus()
        if not focus_iid:
            return

        info = self.engine.parse_iid(focus_iid)
        if not info or info.get("type") != NODE_TYPE_SECTION:
            return

        pk = info.get("id")
        if pk is None:
            return

        # Store section org_id and open INSERT mode
        self.selected_section_org_id = pk
        self.selected_workstation = None
        self.engine.open_child(self, workstation_ui.UI, index=None)

  
    def _reset_workstations(self):
        """
        Clear the workstations Treeview and reset selection state.
        """
        self.lstWorkstations.delete(*self.lstWorkstations.get_children())
        self.selected_workstation = None
        self.selected_section_org_id = None

    def set_workstations(self, args):
        """
        Load workstations for a section (by org_id).

        Args:
            args: Tuple containing (section_org_id,)
        """
        self._reset_workstations()

        sql = """
            SELECT
                workstations.workstation_id,
                equipments.description AS equipment_description,
                workstations.description AS workstation_description,
                workstations.serial,
                workstations.device_id,
                workstations.status
            FROM workstations
            INNER JOIN equipments
                ON workstations.equipment_id = equipments.equipment_id
            WHERE workstations.org_id = ?
              AND equipments.status = 1
            ORDER BY workstations.description;
        """

        rows = self.engine.read(True, sql, args)

        for row in (rows or []):
            workstation_id = row["workstation_id"]
            equipment_desc = row["equipment_description"]
            ws_desc = row["workstation_description"]
            serial = row["serial"]
            device_id = row["device_id"]
            status = row["status"]

            tags = ("status",) if int(status) != 1 else ("",)

            self.lstWorkstations.insert(
                "",
                tk.END,
                iid=str(workstation_id),
                text=str(workstation_id),
                values=(equipment_desc, ws_desc, serial, device_id, status),
                tags=tags,
            )

    def refresh_workstations(self) -> None:
        """
        Refresh the workstations list for the currently selected section.

        This is used by Engine.refresh_windows_for_table() after external
        changes (e.g. Equipments editor).
        """
        if self.selected_section_org_id is None:
            self._reset_workstations()
            return

        # Reuse existing loader with the section org_id
        self.set_workstations((self.selected_section_org_id,))

    def on_workstation_selected(self, evt=None):
        
        sel = self.lstWorkstations.selection()
        if not sel:
            self.selected_workstation = None
            return

        pk = int(sel[0])

        self.selected_workstation = self.engine.get_selected(
            self.table, self.primary_key, pk
        )

    def on_workstation_activated(self, evt=None):
  
        sel = self.lstWorkstations.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        pk = int(sel[0])

        self.selected_workstation = self.engine.get_selected(
            self.table, self.primary_key, pk
        )

        self.engine.open_child(self, workstation_ui.UI, index=pk)

    def on_cancel(self, _evt=None) -> None:
        """Close window safely."""
        super().on_cancel()

