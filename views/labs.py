# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# modify:   ver MMXXV
#-----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import views.lab as ui


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

        super().__init__(name="labs")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       
        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        # Window
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Hot keys
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)

        # State
        self.table = "labs"
        self.primary_key = "lab_id"
        self.child = None
        self.selected_hospital = None       # sites.*
        self.selected_lab = None            # labs.*
        self.tree_item_iid = None           # currently selected node iid in tree
        self.items = tk.StringVar()

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
        # PanedWindow (tk, not ttk)
        self.pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        self.pw.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        # Left pane: Sites tree
        pane_left = ttk.Frame(self.pw, style="App.TFrame")
        grp_left = ttk.Frame(pane_left, style="App.TFrame", relief=tk.GROOVE, padding=8)
        grp_left.pack(fill=tk.BOTH, expand=1)

        cols_tree = (["#0", "", "w", False, 280, 280],
                     ["#1", "", "w", False,   0,   0])
        self.Sites = self.engine.get_tree(grp_left, cols_tree, show="tree")
        self.Sites.pack(fill=tk.BOTH, padx=2, pady=2, expand=1)
        self.Sites.bind("<<TreeviewSelect>>", self.on_branch_selected)
        self.Sites.bind("<Double-1>", self.on_branch_activated)

        # Right pane: Labs list
        pane_right = ttk.Frame(self.pw, style="App.TFrame")
        grp_right = ttk.Frame(pane_right, style="App.TFrame", relief=tk.GROOVE, padding=8)
        grp_right.pack(fill=tk.BOTH, expand=1)

        self.lblLaboratories = ttk.Labelframe(grp_right, text="Laboratories")
        self.lblLaboratories.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        cols_right = (["#0", "id",      "w", False,   0,   0],
                      ["#1", "Manager", "w", True,  220, 220],
                      ["#2", "Lab",     "w", True,  260, 260])
        self.lstLabs = self.engine.get_tree(self.lblLaboratories, cols_right)
        self.lstLabs.tag_configure("inactive", background="light gray")
        self.lstLabs.bind("<<TreeviewSelect>>", self.on_lab_selected)
        self.lstLabs.bind("<Double-1>", self.on_lab_activated)
        self.lstLabs.pack(fill=tk.BOTH, expand=1)

        # Add panes to PanedWindow
        self.pw.add(pane_left, minsize=260)   # ~30%
        self.pw.add(pane_right, minsize=520)  # ~70%

        # Place sash nicely after first draw
        self.after_idle(self._place_sash)

    def _place_sash(self):
        try:
            w = self.pw.winfo_width()
            if w <= 1:
                self.after(50, self._place_sash)
                return
            self.pw.sash_place(0, int(w * 0.30), 1)
        except Exception as e:
            pass

    # Lifecycle ---------------------------------------------------------------
    def on_open(self):
        self.title("Labs Management")
        self._load_tree()

    # --------------------------------------------------------------- data load
    def _load_tree(self):
        """Build Companies → Hospitals tree."""
        # reset
        for iid in self.Sites.get_children():
            self.Sites.delete(iid)

        root = self.Sites.insert("", tk.END, iid="root", text="Sites")

        # Companies (group by supplier that owns hospitals)
        sql_companies = """
            SELECT DISTINCT 
                sites.supplier_id,
                suppliers.description
            FROM sites
            JOIN suppliers ON suppliers.supplier_id = sites.supplier_id
            WHERE sites.status = 1
            ORDER BY suppliers.description ASC;
        """

        try:
            rows_companies = self.engine.read(True, sql_companies, ()) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "labs._load_tree:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows_companies = []

        if rows_companies:
            for row in rows_companies:
                supplier_id = row["supplier_id"]
                company_name = row["description"]

                comp_iid = f"cmp_{supplier_id}"
                self.Sites.insert(
                    root,
                    tk.END,
                    iid=comp_iid,
                    text=company_name,
                    values=(supplier_id, "companies"),
                )

                # Hospitals for the company
                hospitals = self._load_hospitals_for_company(supplier_id) or []
                for hosp in hospitals:
                    site_id = hosp["site_id"]
                    site_name = hosp["description"]

                    hosp_iid = f"site_{site_id}"
                    self.Sites.insert(
                        comp_iid,
                        tk.END,
                        iid=hosp_iid,
                        text=site_name,
                        values=(site_id, "hospitals"),
                    )

        self.Sites.item(root, open=True)

    def _load_hospitals_for_company(self, supplier_id: int):
        sql = """
            SELECT 
                sites.site_id,
                suppliers.description
            FROM sites
            JOIN suppliers ON suppliers.supplier_id = sites.comp_id
            WHERE sites.supplier_id = ?
              AND sites.status = 1
            ORDER BY suppliers.description ASC;
        """
        try:
            return self.engine.read(True, sql, (supplier_id,)) or []
        except Exception as exc:
            try:
                self.engine.on_log(
                    "labs._load_hospitals_for_company:read_dict",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            return []


    def _load_labs_for_hospital(self, site_id: int):
        """Load labs for the given site_id into the right list."""
        for iid in self.lstLabs.get_children():
            self.lstLabs.delete(iid)

        sql = """
            SELECT 
                labs.lab_id,
                CONCAT(users.last_name, ' ', users.first_name) AS manager,
                labs.description,
                labs.status
            FROM labs
            JOIN users ON labs.user_id = users.user_id
            WHERE labs.site_id = ?
            ORDER BY labs.description ASC;
        """

        rows = self.engine.read(True, sql, (site_id,))

        if rows:
            for row in rows:
                lab_id = row["lab_id"]
                manager = row["manager"]
                lab_name = row["description"]
                status = row["status"]

                tags = ("inactive",) if int(status) != 1 else ()
                self.lstLabs.insert(
                    "",
                    tk.END,
                    iid=str(lab_id),
                    text=str(lab_id),
                    values=(manager, lab_name),
                    tags=tags,
                )

        self.lblLaboratories["text"] = f"Laboratories: {len(self.lstLabs.get_children())}"

    # ------------------------------------------------------------------ events
    def on_branch_selected(self, _evt=None):
        """Selecting a node: if it's a hospital, load labs on the right."""
        focus = self.Sites.focus()
        item = self.Sites.item(focus)
        vals = item.get("values") or ()
        if len(vals) < 2:
            return

        ref_id, ref_type = vals[0], vals[1]
        if ref_type == "hospitals":
            try:
                ref_id = int(ref_id)
            except Exception as e:
                pass

            hospital = self.engine.get_selected("sites", "site_id", ref_id)
            if hospital is None:
                self.selected_hospital = None
                return

            self.selected_hospital = hospital
            self.tree_item_iid = focus

            site_id = self.selected_hospital.get("site_id")
            if site_id is None:
                return

            self._load_labs_for_hospital(site_id)

    def on_branch_activated(self, _evt=None):
        """Double click hospital: open Lab editor in INSERT mode (for that hospital)."""
        focus = self.Sites.focus()
        item = self.Sites.item(focus)
        vals = item.get("values") or ()
        if len(vals) < 2:
            return

        ref_id, ref_type = vals[0], vals[1]
        if ref_type != "hospitals":
            return

        try:
            ref_id = int(ref_id)
        except Exception as e:
            pass

        if (
            self.selected_hospital is None
            or self.selected_hospital.get("site_id") != ref_id
        ):
            hospital = self.engine.get_selected("sites", "site_id", ref_id)
            if hospital is None:
                self.selected_hospital = None
                return

            self.selected_hospital = hospital
            self.tree_item_iid = focus

            site_id = self.selected_hospital.get("site_id")
            if site_id is None:
                return

            self._load_labs_for_hospital(site_id)

        # INSERT mode: index=None, context (selected_hospital) letto dalla child
        self.child = ui.UI(self, index=None)
        self.child.on_open()

    def on_lab_selected(self, _evt=None):
        """Store selected lab row from DB."""
        sel = self.lstLabs.selection()
        if not sel:
            self.selected_lab = None
            return

        pk = int(sel[0])
        lab = self.engine.get_selected(self.table, self.primary_key, pk)
        if lab is None:
            self.selected_lab = None
            return

        self.selected_lab = lab

    def on_lab_activated(self, _evt=None):
        """Double click lab: open editor in UPDATE mode."""
        sel = self.lstLabs.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        pk = int(sel[0])
        lab = self.engine.get_selected(self.table, self.primary_key, pk)
        if lab is None:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        self.selected_lab = lab

        # UPDATE mode: index=lab_id, selected_lab letto dalla child via parent
        self.child = ui.UI(self, index=pk)
        self.child.on_open()

    def refresh_labs_and_restore_branch(self):
        """Reload labs for current hospital and restore the tree selection."""
        if self.selected_hospital:
            site_id = self.selected_hospital.get("site_id")
            if site_id is not None:
                self._load_labs_for_hospital(site_id)

        try:
            if self.tree_item_iid:
                self.Sites.focus(self.tree_item_iid)
                self.Sites.see(self.tree_item_iid)
                self.Sites.selection_set(self.tree_item_iid)
        except Exception as e:
            pass

    def _on_cancel(self, _evt=None):
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
