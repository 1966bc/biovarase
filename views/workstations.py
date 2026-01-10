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


class UI(ParentView):

    def __init__(self, parent):
        super().__init__(parent, name="workstations")
        if self._reusing:
            return

        self.table = "workstations"
        self.primary_key = "workstation_id"

        self.selected_section = None
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

        # Hierarchical tree: Sites → Labs → Sections
        self.Sites = ttk.Treeview(self.pane_left, show="tree")
        self.Sites.column("#0", width=260, minwidth=220, stretch=True)
        self.Sites.heading("#0", text=_("Sites"), anchor=tk.W)

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
        Populate the Sites tree with the full hierarchy:

            Sites → Labs → Sections

        Rules:
        - Always use engine.read(True, sql, args) (4.1).
        - Never use positional indexing (no row[0], row[1]) (4.2).
        - Do not use Treeview values indexing (9.1); iid must be parsable
          by engine.parse_iid().
        """
        # Clear current content
        self.engine.clear_treeview(self.Sites)

        # Decide which sites are visible:
        # - Admin (role_id == 0 in log_user[5]): all sites.
        # - Non admin: only the site associated with the current lab_id.
        if self.engine.log_user.get("role") == 0:
            sql = """
                  SELECT sites.site_id, suppliers.description
                  FROM sites
                  INNER JOIN suppliers ON suppliers.supplier_id = sites.comp_id
                  WHERE sites.status = 1
                 ORDER BY suppliers.description ASC;
            """
            args = ()
        else:
            sql = """
                  SELECT sites.site_id, suppliers.description
                  FROM labs
                  INNER JOIN sites     ON sites.site_id = labs.site_id
                  INNER JOIN suppliers ON suppliers.supplier_id = sites.comp_id
                  WHERE labs.lab_id = ?
                  AND sites.status = 1
                  ORDER BY suppliers.description ASC;
            """
            args = (self.engine.get_lab_id(),)

        rs_sites = self.engine.read(True, sql, args)

        root_iid = "sites_root"
        self.Sites.insert("", tk.END, iid=root_iid, text=_("Sites"))

        for site_row in (rs_sites or []):
            site_id = site_row["site_id"]
            site_name = site_row["description"]

            site_iid = f"site_{site_id}"
            self.Sites.insert(root_iid, tk.END, iid=site_iid, text=site_name)

            # Load labs for this site
            rs_labs = self._load_labs(site_id)
            for lab_row in (rs_labs or []):
                lab_id = lab_row["lab_id"]
                lab_name = lab_row["description"]

                lab_iid = f"lab_{lab_id}"
                self.Sites.insert(site_iid, tk.END, iid=lab_iid, text=lab_name)

                # Load sections for this lab
                rs_sections = self._load_sections(lab_id)
                for sec_row in (rs_sections or []):
                    section_id = sec_row["section_id"]
                    section_name = sec_row["description"]

                    sec_iid = f"section_{section_id}"
                    self.Sites.insert(lab_iid, tk.END, iid=sec_iid, text=section_name)

        self.Sites.item(root_iid, open=True)

    def _load_labs(self, site_id):
      
        sql = """
              SELECT labs.lab_id, labs.description 
            FROM labs 
            WHERE labs.site_id = ? AND labs.status = 1 
            ORDER BY labs.description ASC;
        """
        
        return self.engine.read(True, sql, (site_id,)) or []

    def _load_sections(self, lab_id):
     
        sql = """
              SELECT sections.section_id, sections.description 
              FROM sections 
              WHERE sections.lab_id = ? AND sections.status = 1
              ORDER BY sections.description ASC;
        """
        
        return self.engine.read(True, sql, (lab_id,)) or []

    def on_branch_selected(self, evt=None):
        """
        Called when a node is selected in the Sites tree.

        Uses engine.parse_iid() to decode the iid into a structured dict
        (type + id), avoiding any positional indexing on Treeview values.
        """
        focus_iid = self.Sites.focus()
        if not focus_iid:
            self._reset_workstations()
            return

        # parse_iid is expected to return something like:
        #   {"type": "site", "id": 1}
        #   {"type": "lab", "id": 3}
        #   {"type": "section", "id": 7}
        info = self.engine.parse_iid(focus_iid)
        if not info:
            # Unrecognized node → clear the workstations list
            self._reset_workstations()
            return

        kind = info.get("type")
        pk = info.get("id")

        if kind == "section" and pk is not None:
            # Retrieve the selected section as a dict from the DB
            self.selected_section = self.engine.get_selected(
                "sections", "section_id", pk
            )
            # Load workstations for this section
            self.set_workstations((pk,))
        else:
            # Only sections have workstations attached
            self._reset_workstations()

    def on_branch_activated(self, evt=None):
   
        focus_iid = self.Sites.focus()
        if not focus_iid:
            return

        info = self.engine.parse_iid(focus_iid)
        if not info or info.get("type") != "section":
            return

        pk = info.get("id")
        if pk is None:
            return

        self.selected_section = self.engine.get_selected(
            "sections", "section_id", pk
        )
         # INSERT mode
        self.selected_section = self.engine.get_selected("sections", "section_id", pk)
        self.selected_workstation = None
        self.engine.open_child(self, workstation_ui.UI, index=None)

  
    def _reset_workstations(self):
        """
        Clear the workstations Treeview and reset selection state.
        """
        self.lstWorkstations.delete(*self.lstWorkstations.get_children())
        self.selected_workstation = None

    def set_workstations(self, args):
        
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
                INNER JOIN sections
                    ON workstations.section_id = sections.section_id
                WHERE sections.section_id = ?
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
        if not self.selected_section:
            self._reset_workstations()
            return

        section_id = self.selected_section.get("section_id")
        if section_id is None:
            self._reset_workstations()
            return

        # Reuse existing loader with the correct (section_id,) tuple
        self.set_workstations((section_id,))

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

