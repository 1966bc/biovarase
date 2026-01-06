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

import views.workstation as workstation_ui


class UI(tk.Toplevel):

    _instance = None

    def __new__(cls, parent):
       
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                cls._instance = None

        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
       
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(name="workstations")
        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       

        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self
        
        self.table = "workstations"
        self.primary_key = "workstation_id"

        self.selected_section = None        
        self.selected_workstation = None    
        self.child = None                   

        # Window properties
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.resizable(True, True)

        # Hotkeys
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)

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

        cols_sites = (
            ["#0", "Sites", "w", True, 220, 260],
            ["#1", "",      "w", True,   0,   0],
        )

        # Hierarchical tree:
        #   Sites → Labs → Sections
        self.Sites = self.engine.get_tree(
            self.pane_left, cols_sites, show="tree headings"
        )
        # Only show the tree column
        self.Sites["displaycolumns"] = ()
        self.Sites.pack(fill=tk.BOTH, expand=1)

        self.Sites.bind("<<TreeviewSelect>>", self.on_branch_selected)
        self.Sites.bind("<Double-1>", self.on_branch_activated)

        self.pane_right = ttk.Frame(self.pw, style="App.TFrame", padding=6)
        self.pw.add(self.pane_right, minsize=480)

        lf = ttk.LabelFrame(
            self.pane_right, style="App.TLabelframe", text="Workstations"
        )
        lf.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        cols_ws = (
            ["#0", "id",           "w", False,   0,   0],
            ["#1", "Equipments",   "w",  True, 220, 220],
            ["#2", "Workstations", "w",  True, 260, 260],
            ["#3", "Serial",       "w",  True, 140, 140],
            ["#4", "Device ID",    "w",  True, 200, 200],
        )

        # Workstations list (flat Treeview)
        self.lstWorkstations = self.engine.get_tree(lf, cols_ws)
        self.lstWorkstations.pack(fill=tk.BOTH, expand=1)

        # Tag used to highlight inactive workstations
        self.lstWorkstations.tag_configure(
            "status", background=self.engine.get_rgb(211, 211, 211)
        )

        self.lstWorkstations.bind(
            "<<TreeviewSelect>>", self.on_workstation_selected
        )
        self.lstWorkstations.bind(
            "<Double-1>", self.on_workstation_activated
        )

        
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

        self.title(f"{self.winfo_name().capitalize()} Management")

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
        for iid in self.Sites.get_children():
            self.Sites.delete(iid)

        # Decide which sites are visible:
        # - Admin (role_id == 0 in log_user[5]): all sites.
        # - Non admin: only the site associated with the current section_id.
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
                  FROM sections 
                  INNER JOIN labs      ON labs.lab_id = sections.lab_id 
                  INNER JOIN sites     ON sites.site_id = labs.site_id 
                  INNER JOIN suppliers ON suppliers.supplier_id = sites.comp_id 
                  WHERE sections.section_id = ? 
                  AND sites.status = 1 
                  ORDER BY suppliers.description ASC;
            """
            args = (self.engine.get_section_id(),)

        rs_sites = self.engine.read(True, sql, args)

        root_iid = "sites_root"
        self.Sites.insert("", tk.END, iid=root_iid, text="Sites")

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
        self._open_child(index=None)

  
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
                self.nametowidget(".").title(),
                self.engine.no_selected,
                parent=self,
            )
            return

        pk = int(sel[0])

        self.selected_workstation = self.engine.get_selected(
            self.table, self.primary_key, pk
        )

        self._open_child(index=pk)

    def _open_child(self, index=None) -> None:
        """Open the workstation editor child window."""
        try:
            if getattr(self, "child", None) is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass

        self.child = workstation_ui.UI(self, index=index)
        self.child.on_open()

    def _on_cancel(self, _evt=None) -> None:
        """Close window safely and unregister from Engine."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)

