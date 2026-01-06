# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import views.section as ui


class UI(tk.Toplevel):
    """
    Sections management window (singleton).

    Left pane  : Sites → Labs tree
    Right pane : Sections for the selected Lab

    Double-click on a Lab        → open section editor in INSERT mode
    Double-click on a Section    → open section editor in UPDATE mode
    """

    _instance = None

    def __new__(cls, parent):
        """
        Standard Toplevel singleton logic:
        if an instance exists → bring to front instead of creating a new one.
        """
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

        super().__init__(name="sections")
        self._is_init = True

        # Engine + singleton registry
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self
        self.parent = parent

        # Table info
        self.table = "sections"
        self.primary_key = "section_id"

        # State
        self.child = None
        self.selected_lab = None
        self.selected_section = None

        self.resizable(True, True)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)
        self.bind("<Alt-c>", self.on_cancel)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window(self, on_screen=True)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    # ---------------------------------------------------------------------- UI
    def _build_ui(self):
        """Builds PanedWindow, tree and list UI."""

        self.pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        self.pw.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        # ---------------- LEFT PANE - Sites → Labs ----------------
        pane_left = ttk.Frame(self.pw, style="App.TFrame")
        grp_left = ttk.Frame(pane_left, style="App.TFrame", relief=tk.GROOVE, padding=8)
        grp_left.pack(fill=tk.BOTH, expand=1)

        self.Sites = ttk.Treeview(grp_left, show="tree")
        self.Sites.column("#0", width=280, minwidth=280, stretch=False)

        sb_sites = ttk.Scrollbar(grp_left, orient=tk.VERTICAL, command=self.Sites.yview)
        self.Sites.configure(yscrollcommand=sb_sites.set)
        self.Sites.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2, expand=1)
        sb_sites.pack(side=tk.RIGHT, fill=tk.Y)

        self.Sites.bind("<<TreeviewSelect>>", self.on_branch_selected)
        self.Sites.bind("<Double-1>", self.on_branch_activated)

        # ---------------- RIGHT PANE - Sections list ----------------
        pane_right = ttk.Frame(self.pw, style="App.TFrame")
        grp_right = ttk.Frame(pane_right, style="App.TFrame", relief=tk.GROOVE, padding=8)
        grp_right.pack(fill=tk.BOTH, expand=1)

        self.lblSections = ttk.Labelframe(grp_right, text="Sections")
        self.lblSections.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        cols_sections = ("manager", "description")
        self.lstSections = ttk.Treeview(self.lblSections, columns=cols_sections, show="headings")

        self.lstSections.column("manager", width=220, minwidth=220, anchor=tk.W, stretch=True)
        self.lstSections.heading("manager", text="Manager", anchor=tk.W)

        self.lstSections.column("description", width=240, minwidth=240, anchor=tk.W, stretch=True)
        self.lstSections.heading("description", text="Description", anchor=tk.W)

        sb_sections = ttk.Scrollbar(self.lblSections, orient=tk.VERTICAL, command=self.lstSections.yview)
        self.lstSections.configure(yscrollcommand=sb_sections.set)
        self.lstSections.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_sections.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstSections.tag_configure("inactive", background="light gray")
        self.lstSections.bind("<<TreeviewSelect>>", self.on_section_selected)
        self.lstSections.bind("<Double-1>", self.on_section_activated)

        self.pw.add(pane_left, minsize=260)
        self.pw.add(pane_right, minsize=520)
        self.after_idle(self._place_sash)

    def _place_sash(self):
        """Places sash after initial rendering."""
        try:
            w = self.pw.winfo_width()
            if w <= 1:
                self.after(50, self._place_sash)
                return
            self.pw.sash_place(0, int(w * 0.30), 1)
        except Exception as e:
            self.engine.on_log("_place_sash", e, type(e), sys.modules[__name__])

    # ---------------------------------------------------------------------- OPEN
    def on_open(self):
        """Called when window becomes visible."""
        self.title("Sections Management")
        self._load_tree()

    # ---------------------------------------------------------------------- TREE
    def _load_tree(self):
        """Builds Sites → Labs tree using read_dict."""
        try:
            for iid in self.Sites.get_children():
                self.Sites.delete(iid)

            root = self.Sites.insert("", tk.END, iid="root", text="Sites")

            sql_sites = """
                SELECT 
                    sites.site_id,
                    suppliers.description AS site_name
                FROM sites
                JOIN suppliers ON suppliers.supplier_id = sites.comp_id
                WHERE sites.status = 1
                ORDER BY suppliers.description ASC;
            """

            rows_sites = self.engine.read(True, sql_sites, ()) or []

            for row in rows_sites:
                site_id = row["site_id"]
                site_name = row["site_name"]

                site_iid = f"site_{site_id}"
                self.Sites.insert(
                    root,
                    tk.END,
                    iid=site_iid,
                    text=site_name,
                    values=(site_id, "site"),
                )

                labs = self._load_labs_for_site(site_id)
                for lab in labs:
                    lab_id = lab["lab_id"]
                    lab_name = lab["description"]

                    lab_iid = f"lab_{lab_id}"
                    self.Sites.insert(
                        site_iid,
                        tk.END,
                        iid=lab_iid,
                        text=lab_name,
                        values=(lab_id, "lab"),
                    )

            self.Sites.item(root, open=True)

        except Exception as e:
            self.engine.on_log("_load_tree", e, type(e), sys.modules[__name__])

    def _load_labs_for_site(self, site_id: int):
        """Returns list of labs (dict rows) for a given site."""
        try:
            sql = """
                SELECT 
                    labs.lab_id,
                    labs.description
                FROM labs
                WHERE labs.site_id = ?
                  AND labs.status = 1
                ORDER BY labs.description ASC;
            """
            return self.engine.read(True, sql, (site_id,)) or []

        except Exception as e:
            self.engine.on_log("_load_labs_for_site", e, type(e), sys.modules[__name__])
            return []

    # ---------------------------------------------------------------------- SECTIONS
    def _load_sections_for_lab(self, lab_id: int):
        """Load sections for a given lab into the right list."""
        try:
            for iid in self.lstSections.get_children():
                self.lstSections.delete(iid)

            sql = """
                SELECT
                    sections.section_id,
                    CONCAT(users.last_name, ' ', users.first_name) AS manager,
                    sections.description,
                    sections.status
                FROM sections
                JOIN users ON users.user_id = sections.user_id
                WHERE sections.lab_id = ?
                ORDER BY sections.description ASC;
            """

            rows = self.engine.read(True, sql, (lab_id,)) or []

            for row in rows:
                section_id = row["section_id"]
                manager = row["manager"]
                description = row["description"]
                status = int(row["status"])

                tags = ("inactive",) if status != 1 else ()

                self.lstSections.insert(
                    "",
                    tk.END,
                    iid=str(section_id),
                    text=str(section_id),
                    values=(manager, description),
                    tags=tags,
                )

            self.lblSections["text"] = f"Sections: {len(rows)}"

        except Exception as e:
            self.engine.on_log("_load_sections_for_lab", e, type(e), sys.modules[__name__])

    # ---------------------------------------------------------------------- EVENTS
    def on_branch_selected(self, _evt=None):
        """Triggered when user selects a node in the left tree."""
        try:
            focus = self.Sites.focus()
            item = self.Sites.item(focus)

            vals = item.get("values") or ()
            if len(vals) < 2:
                return

            ref_id, ref_type = vals

            if ref_type == "lab":
                lab_id = int(ref_id)
                self.selected_lab = self.engine.get_selected("labs", "lab_id", lab_id)
                lab_id = self.selected_lab["lab_id"]
                self._load_sections_for_lab(lab_id)

        except Exception as e:
            self.engine.on_log("on_branch_selected", e, type(e), sys.modules[__name__])

    def on_branch_activated(self, _evt=None):
        """Double-click on a Lab → open section editor in INSERT mode."""
        try:
            focus = self.Sites.focus()
            item = self.Sites.item(focus)
            vals = item.get("values") or ()
            if len(vals) < 2:
                return

            ref_id, ref_type = vals
            if ref_type != "lab":
                return

            lab_id = int(ref_id)
            self.selected_lab = self.engine.get_selected("labs", "lab_id", lab_id)

            # 1) Close any existing child editor
            try:
                if self.child is not None and self.child.winfo_exists():
                    self.child.destroy()
            except Exception as e:
                # Ignore invalid widget state
                pass

            # 2) Open a fresh editor in INSERT mode
            self.child = ui.UI(self, index=None)
            self.child.on_open(self.selected_lab)

        except Exception as e:
            self.engine.on_log("on_branch_activated", e, type(e), sys.modules[__name__])

    def on_section_selected(self, _evt=None):
        """Store selected section (hybrid dict)."""
        sel = self.lstSections.selection()
        if not sel:
            self.selected_section = None
            return

        pk = int(sel[0])
        self.selected_section = self.engine.get_selected(self.table, self.primary_key, pk)

    def on_section_activated(self, _evt=None):
        """Double-click on Section → open editor in UPDATE mode."""
        sel = self.lstSections.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        pk = int(sel[0])
        self.selected_section = self.engine.get_selected(self.table, self.primary_key, pk)

        # 1) Close any existing child editor
        try:
            if self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            # Ignore invalid widget state
            pass

        # 2) Open a fresh editor in UPDATE mode
        self.child = ui.UI(self, index=pk)
        self.child.on_open(self.selected_lab, self.selected_section)


    # ---------------------------------------------------------------------- REFRESH
    def refresh_sections_for_current_lab(self):
        """Called after save: reload sections for the current lab."""
        if self.selected_lab:
            lab_id = self.selected_lab["lab_id"]
            self._load_sections_for_lab(lab_id)

    # ---------------------------------------------------------------------- CLOSE
    def on_cancel(self, _evt=None):
        """Proper window close + deregister from Engine."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
