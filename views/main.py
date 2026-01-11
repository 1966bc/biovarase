# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
# -----------------------------------------------------------------------------
"""
Main Application Window for Biovarase QC System.

This module provides the primary user interface for the laboratory quality control
management system, including:

- Multi-site test and batch selection (categories, tests, workstations, batches)
- Real-time Levey-Jennings chart visualization with Westgard rules
- QC statistics calculation (mean, SD, CV, bias, uncertainty)
- Result management (add, edit, validate, disable/enable)
- Bias chart for target vs actual performance
- Data import/export and reporting
- Daily validation workflows
- Integration with analytical goals and TEa

This is a singleton master window (per PROJECT_RULES.md section 7.1) that coordinates
all QC operations and maintains the current selection context.
"""
# stdlib
import datetime
import inspect
import operator
import os
import random
import sys
from typing import List, Dict, Optional, Any

# tkinter
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox
from tkinter import font

from ljcanvas import LeveyJenningsCanvas
from bias_canvas import BiasCanvas
from i18n import _, set_language
from westgards import WESTGARD_ACCEPT
from app_config import MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT
from engine import (
    ROLE_APP_ADMIN, ROLE_LAB_ADMIN, ROLE_SUPERUSER,
    ROLE_TECHNICIAN, ROLE_VIEWER
)

# project frames
import views.license
import views.tests
import views.test_methods
import views.workstation_test_methods
import views.batches
import views.units
import views.methods
import views.categories
import views.login  # For Change User feature
import views.equipments
import views.workstations
import views.controls
import views.suppliers
import views.labs
import views.sections
import views.batch
import views.actions
import views.notes
import views.result
import views.export_notes
import views.counts
import views.plots
import views.set_zscore
import views.observations
import views.youden
import views.youden_selector
import views.users
import views.samples
import views.analitycal_goals
import views.tea
import views.analytical
import views.change_password
import views.sites
import views.organizations
import views.importer
import views.zscore
import views.daily_validation
import views.bland_altman
import views.bland_altman_alert
import views.qc_report


NO_DATA = "No data"

class Main(tk.Toplevel):
    _instance: Optional['Main'] = None

    def __new__(cls, parent: tk.Widget) -> 'Main':
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

    def __init__(self, parent: tk.Widget) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__(name="main")
        self._initialized = True
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self
        self.parent = parent

        # Subscribe to changes (Observer pattern)
        self.engine.subscribe("batch_changed", self._on_batch_changed)
        self.engine.subscribe("tests_changed", self._on_tests_changed)
        self.engine.subscribe("categories_changed", self._on_categories_changed)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.status_bar_text = tk.StringVar()
        self.average = tk.DoubleVar()
        self.bias = tk.DoubleVar()
        self.westgard = tk.StringVar()
        self.calculated_sd = tk.DoubleVar()
        self.cva = tk.DoubleVar()
        self.uncertainty = tk.DoubleVar()

        self.observations = tk.IntVar()
        self.target = tk.DoubleVar()
        self.sd = tk.DoubleVar()
        self.zscore = tk.DoubleVar()
        self.expiration = tk.StringVar()
        self.te = tk.DoubleVar()
        self.ddof = tk.IntVar()
        self.show_expired = tk.IntVar()
        self.status_bar_site_description = tk.StringVar()
        
        # selection state (all dictionaries, not tuples)
        self.selected_category = None
        self.selected_test_method = None
        self.selected_test = None
        self.selected_workstation = None
        self.selected_batch = None
        self.selected_result = None

        # mapping index → id
        self.dict_categories = {}
        self.test_methods = {}
        self.workstation_test_methods = {}
        self.dict_batches = {}
        self.dict_results = {}

        # mapping Levey-Jennings point index -> result_id (enabled results only)
        self.lj_index_to_result_id = []

        self._build_ui()
        self.init_menu()
        self.init_status_bar()
        self.center_ui()
        
    def center_ui(self):

        """Set high, width, x, y coords"""
        #get screen width and height
        screen_width  = self.nametowidget(".").winfo_screenwidth()
        screen_height  = self.nametowidget(".").winfo_screenheight()

        #get dimension from dimension file
        d = self.engine.get_dimensions()
        window_width = int(d['w'])
        window_height = int(d['h'])
        
        # calculate position x, y
        position_right = int(screen_width /2 - window_width/2)
        position_top = int(screen_height /2 - window_height/2)
        #we only position the window because otherwise it doesn't resize well on laptop
        self.geometry('+%d+%d'%(position_right, position_top))
        
    def init_menu(self) -> None:
        """
        Build menu bar with role-based visibility.

        Menu visibility by role:
        - App Admin (0): All menus, all items
        - Lab Admin (3): Edit, QC, Exports, Documents, Users management
        - Superuser (4): QC (validation), Batches, view-only access
        - Technician (5): QC (data entry), Imports, limited Edit
        - Viewer (6): QC (view only), Exports, Documents
        """
        role = self.engine.log_user.get("role", ROLE_VIEWER)
        is_admin = role == ROLE_APP_ADMIN
        is_lab_admin = role <= ROLE_LAB_ADMIN  # 0, 1, 2, 3
        can_modify = role <= ROLE_TECHNICIAN   # 0-5
        is_viewer = role == ROLE_VIEWER

        m_main = tk.Menu(self, bd=1)

        m_file = tk.Menu(m_main, tearoff=0, bd=1)
        m_plots = tk.Menu(m_main, tearoff=0, bd=1)
        m_exports = tk.Menu(m_main, tearoff=0, bd=1)
        m_documents = tk.Menu(m_main, tearoff=0, bd=1)
        m_about = tk.Menu(m_main, tearoff=0, bd=1)

        # Conditional menus
        m_edit = tk.Menu(m_main, tearoff=0, bd=1) if can_modify else None
        m_imports = tk.Menu(m_main, tearoff=0, bd=1) if can_modify else None
        m_adm = tk.Menu(m_main, tearoff=0, bd=1) if is_admin else None

        # Build main menu bar
        m_main.add_cascade(label=_("File"), underline=0, menu=m_file)
        m_main.add_cascade(label=_("QC"), underline=0, menu=m_plots)

        if m_edit:
            m_main.add_cascade(label=_("Edit"), underline=0, menu=m_edit)
        if m_imports:
            m_main.add_cascade(label=_("Imports"), underline=1, menu=m_imports)

        m_main.add_cascade(label=_("Exports"), underline=1, menu=m_exports)
        m_main.add_cascade(label=_("Documents"), underline=0, menu=m_documents)

        if m_adm:
            m_main.add_cascade(label=_("Admin"), underline=0, menu=m_adm)

        m_main.add_cascade(label="?", underline=0, menu=m_about)

        # === FILE MENU ===
        items = [(_("Reset"), 0, self.on_reset)]
        if is_admin:
            items.append((_("Insert random results"), 0, self.on_insert_demo_result))
        items.extend([
            (_("Analytica"), 0, self.on_analitical),
            (_("Z Score"), 0, self.on_zscore),
        ])

        for i in items:
            m_file.add_command(label=i[0], underline=i[1], command=i[2])

        m_file.add_separator()

        m_file.add_command(label=_("Change User"),
                           underline=0,
                           accelerator="Ctrl+U",
                           command=self.on_change_user)

        if is_admin:
            m_file.add_command(label=_("Change Laboratory"),
                               underline=7,
                               accelerator="Ctrl+E",
                               command=self.on_change_lab)

        m_file.add_separator()
        m_file.add_command(label=_("Change Password"),
                           underline=0,
                           command=self.on_change_password)
        m_file.add_command(label=_("Log"),
                           underline=0,
                           command=self.on_log)

        if is_admin:
            m_file.add_separator()
            m_lang = tk.Menu(m_file, tearoff=0)
            self.lang_var = tk.StringVar(value=self.engine.get_language())
            m_lang.add_radiobutton(
                label="English",
                value="en",
                variable=self.lang_var,
                command=self._on_language_change
            )
            m_lang.add_radiobutton(
                label="Italiano",
                value="it",
                variable=self.lang_var,
                command=self._on_language_change
            )
            m_file.add_cascade(label=_("Language"), underline=0, menu=m_lang)
            m_lang.config(bg=self.engine.get_rgb(240, 240, 237), fg="black")

        m_file.add_separator()
        m_file.add_command(label=_("Exit"), underline=0, command=self.on_close)

        # === QC MENU ===
        m_plots.add_command(label=_("Daily Validation"), underline=0, command=self.on_daily_validation)
        m_plots.add_separator()

        items = ((_("Levey-Jennings"), 0, self.on_plots),
                 (_("Youden"), 0, self.on_youden),
                 (_("Tea"), 0, self.on_tea),
                 (_("Bland-Altman"), 0, self.on_bland_altman),
                 (_("Bland-Altman Scanner"), 0, self.on_bland_altman_alert),
                 (_("QC Report"), 0, self.on_qc_report),)

        for i in items:
            m_plots.add_command(label=i[0], underline=i[1], command=i[2])

        # === EDIT MENU (if can_modify) ===
        if m_edit:
            items = [
                (_("Batches"), 0, self.on_batches),
                (_("Categories"), 0, self.on_categories),
                (_("Test Methods"), 0, self.on_test_methods),
                (_("Tests Methods Workstations"), 0, self.on_workstation_test_methods),
                (_("Workstations"), 0, self.on_workstations),
            ]
            # Settings only for lab admins+
            if is_lab_admin:
                items.extend([
                    (_("Set Observations"), 0, self.on_observations),
                    (_("Set Z Score"), 0, self.on_set_zscore),
                ])

            for i in sorted(items, key=operator.itemgetter(0)):
                m_edit.add_command(label=i[0], underline=i[1], command=i[2])

        # === IMPORTS MENU (if can_modify) ===
        if m_imports:
            items = ((_("Import"), 0, self.on_import_results),)
            for i in items:
                m_imports.add_command(label=i[0], underline=i[1], command=i[2])

        # === EXPORTS MENU ===
        items = ((_("Notes"), 0, self.on_export_notes),
                 (_("Analytical Goals"), 0, self.on_analitycal_goals),
                 (_("Counts"), 0, self.on_export_counts),)

        for i in items:
            m_exports.add_command(label=i[0], underline=i[1], command=i[2])

        # === DOCUMENTS MENU ===
        items = ((_("User Manual"), 0, self.on_user_manual),
                 (_("QC Technical Manual"), 0, self.on_qc_thecnical_manual),
                 (_("Guidelines"), 0, self.on_get_guidelines),
                 (_("Biological Values"), 0, self.on_bvv),)

        for i in items:
            m_documents.add_command(label=i[0], underline=i[1], command=i[2])

        # === ADMIN MENU (admin only) ===
        # Global master data: controls, tests, units, methods, samples, equipments, suppliers
        # These must be managed centrally for peer lab comparison
        if m_adm:
            items = ((_("Actions"), 0, self.on_actions),
                     (_("Controls"), 0, self.on_controls),
                     (_("Equipments"), 0, self.on_equipments),
                     (_("Labs"), 0, self.on_labs),
                     (_("Methods"), 0, self.on_methods),
                     (_("Organizations"), 0, self.on_organizations),
                     (_("Samples"), 0, self.on_samples),
                     (_("Sections"), 0, self.on_sections),
                     (_("Sites"), 0, self.on_sites),
                     (_("Suppliers"), 0, self.on_suppliers),
                     (_("Tests"), 0, self.on_tests),
                     (_("Units"), 0, self.on_units),
                     (_("Users"), 0, self.on_users),)

            for i in sorted(items, key=operator.itemgetter(0)):
                m_adm.add_command(label=i[0], underline=i[1], command=i[2])

        # === ABOUT MENU ===
        m_about.add_command(label=_("About"), underline=0, command=self.on_about)
        m_about.add_command(label=_("License"), underline=0, command=self.on_license)
        m_about.add_command(label=_("Python"), underline=0, command=self.on_python_version)
        m_about.add_command(label=_("Tkinter"), underline=0, command=self.on_tkinter_version)

        # Apply styling to all menus
        all_menus = [m_main, m_file, m_plots, m_exports, m_documents, m_about]
        if m_edit:
            all_menus.append(m_edit)
        if m_imports:
            all_menus.append(m_imports)
        if m_adm:
            all_menus.append(m_adm)

        for m in all_menus:
            m.config(bg=self.engine.get_rgb(240, 240, 237),)
            m.config(fg="black")

        self.config(menu=m_main)

        # Keyboard shortcuts
        self.bind("<Control-u>", self.on_change_user)
        # Ctrl+E for Change Laboratory (admin only)
        if self.engine.log_user["role"] == 0:
            self.bind("<Control-e>", self.on_change_lab)

    def _rebuild_menu(self) -> None:
        """Rebuild menu after user change (menu items depend on user role)."""
        # Destroy existing menu
        current_menu = self["menu"]
        if current_menu:
            try:
                self.nametowidget(current_menu).destroy()
            except Exception:
                pass
        self.config(menu="")

        # Rebuild menu with new role
        self.init_menu()

    def _build_ui(self) -> None:

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)

        frm_data = ttk.Frame(self.frm_main, style="App.TFrame")

        frm_lists = ttk.Frame(frm_data, style="App.TFrame")

        ttk.Label(frm_lists, text=_('Categories')).pack(side=tk.TOP, fill=tk.X, expand=0)

        self.cbCategories = ttk.Combobox(frm_lists, style="App.TCombobox", state="readonly")
        self.cbCategories.bind("<<ComboboxSelected>>", self.on_selected_category)
        self.cbCategories.pack(side=tk.TOP, fill=tk.X, pady=5, expand=0)

        ttk.Label(frm_lists, text='Tests').pack(side=tk.TOP, fill=tk.X, expand=0)
        self.cbTests = ttk.Combobox(frm_lists, style="App.TCombobox")
        self.cbTests.bind("<<ComboboxSelected>>", self.on_selected_test)
        self.cbTests.pack(side=tk.TOP, fill=tk.X, pady=5, expand=0)

        w = ttk.LabelFrame(frm_lists, text=_('Workstation Data Source'))
        cols_ws = ("description", "serial")
        self.lstWorkstations = ttk.Treeview(w, columns=cols_ws, show="headings", height=4)
        self.lstWorkstations.column("description", width=100, minwidth=80, anchor=tk.W)
        self.lstWorkstations.column("serial", width=80, minwidth=60, anchor=tk.W)
        self.lstWorkstations.heading("description", text=_("Workstation"), anchor=tk.W)
        self.lstWorkstations.heading("serial", text=_("Serial"), anchor=tk.W)
        sb_ws = ttk.Scrollbar(w, orient=tk.VERTICAL, command=self.lstWorkstations.yview)
        self.lstWorkstations.configure(yscrollcommand=sb_ws.set)
        self.lstWorkstations.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_ws.pack(side=tk.RIGHT, fill=tk.Y)
        self.lstWorkstations.bind("<<TreeviewSelect>>", self.on_selected_workstation)
        w.pack(side=tk.TOP, fill=tk.BOTH, expand=0)

        w = ttk.LabelFrame(frm_lists, text=_("Batches"))
        cols_batch = ("level", "lot", "expiration")
        self.lstBatches = ttk.Treeview(w, columns=cols_batch, show="headings", height=4)
        self.lstBatches.column("level", width=30, minwidth=25, anchor=tk.W)
        self.lstBatches.column("lot", width=70, minwidth=60, anchor=tk.W)
        self.lstBatches.column("expiration", width=80, minwidth=70, anchor=tk.W)
        self.lstBatches.heading("level", text=_("Lv"), anchor=tk.W)
        self.lstBatches.heading("lot", text=_("Lot"), anchor=tk.W)
        self.lstBatches.heading("expiration", text=_("Expiration"), anchor=tk.W)
        self.lstBatches.tag_configure("expired", background="red")
        self.lstBatches.tag_configure("expiring", background="yellow")
        sb_batch = ttk.Scrollbar(w, orient=tk.VERTICAL, command=self.lstBatches.yview)
        self.lstBatches.configure(yscrollcommand=sb_batch.set)
        self.lstBatches.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_batch.pack(side=tk.RIGHT, fill=tk.Y)
        self.lstBatches.bind("<<TreeviewSelect>>", self.on_selected_batch)
        self.lstBatches.bind('<Double-Button-1>', self.on_batch_double_button)
        w.pack(side=tk.TOP, fill=tk.BOTH, expand=0)

        frm_stats = ttk.Frame(frm_lists, style="App.TFrame")

        # --- Column 1: Batch data (from lot) ---
        frm_batch = ttk.LabelFrame(frm_stats, text=_("Batch"), labelanchor="n")
        frm_batch.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=(0, 2))

        ttk.Label(frm_batch, text=_("Target"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_batch,
                  style="Target.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.target).pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(frm_batch, text=_("SD"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_batch,
                  style="black_and_white.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.sd).pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(frm_batch, text=_("TE%"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_batch,
                  style="black_and_white.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.te).pack(fill=tk.X, padx=4, pady=1)

        # --- Column 2: Computed statistics ---
        frm_calc = ttk.LabelFrame(frm_stats, text=_("Computed"), labelanchor="n")
        frm_calc.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=2)

        ttk.Label(frm_calc, text=_("Mean"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_calc,
                  style="Average.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.average).pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(frm_calc, text=_("sd"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_calc,
                  style="black_and_white.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.calculated_sd).pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(frm_calc, text=_("CV%"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_calc,
                  style="black_and_white.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.cva).pack(fill=tk.X, padx=4, pady=1)

        # --- Column 3: QC evaluation ---
        frm_qc = ttk.LabelFrame(frm_stats, text=_("QC"), labelanchor="n")
        frm_qc.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=(2, 0))

        ttk.Label(frm_qc, text=_("Bias%"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_qc,
                  style="black_and_white.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.bias).pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(frm_qc, text=_("U"), anchor=tk.CENTER).pack(fill=tk.X)
        ttk.Label(frm_qc,
                  style="black_and_white.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.uncertainty).pack(fill=tk.X, padx=4, pady=1)
        ttk.Label(frm_qc, text=_("Westgard"), anchor=tk.CENTER).pack(fill=tk.X)
        self.lblWestgard = ttk.Label(
            frm_qc,
            style="black_and_white.TLabel",
            anchor=tk.CENTER,
            textvariable=self.westgard,
        )
        self.lblWestgard.pack(fill=tk.X, padx=4, pady=1)

        w = ttk.LabelFrame(frm_lists, text=_("Results"))
        # Treeview for results
        cols = ("date", "result")
        self.lstResults = ttk.Treeview(w, columns=cols, show="headings", height=8)
        self.lstResults.heading("date", text=_("Date"), anchor=tk.W)
        self.lstResults.heading("result", text=_("Result"), anchor=tk.E)
        self.lstResults.column("date", width=90, anchor=tk.W)
        self.lstResults.column("result", width=80, anchor=tk.E)
        # Tags for row colors
        self.lstResults.tag_configure("disabled", foreground="gray")
        self.lstResults.tag_configure("violation_3s", foreground="red")
        self.lstResults.tag_configure("violation_2s", foreground="orange")
        self.lstResults.tag_configure("has_notes", background="#fff2cc")
        sb_results = ttk.Scrollbar(w, orient=tk.VERTICAL, command=self.lstResults.yview)
        self.lstResults.configure(yscrollcommand=sb_results.set)
        self.lstResults.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_results.pack(side=tk.RIGHT, fill=tk.Y)
        self.lstResults.bind("<<TreeviewSelect>>", self.on_selected_result)
        self.lstResults.bind("<Double-Button-1>", self.on_update_result)
        w.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)

        # Create graph!
        frm_graphs = ttk.Frame(frm_data, style="App.TFrame")
        frm_graphs.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1,  padx=5, pady=5)

        # Una sola colonna, due righe:
        # row 0 = Levey–Jennings (si espande)
        # row 1 = Bias chart (basso, tipo "barra di stato")
        frm_graphs.grid_columnconfigure(0, weight=1)
        frm_graphs.grid_rowconfigure(0, weight=1)
        frm_graphs.grid_rowconfigure(1, weight=0)

        # Levey–Jennings (grafico principale)
        self.lj_canvas = LeveyJenningsCanvas(
            frm_graphs,
            bg="white",
        )

        # Double–click on LJ points → show detail
        self.lj_canvas.set_point_click_callback(self.on_lj_point_double_click)
        
        self.lj_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        # Bias chart below, more compact
        self.bias_canvas = BiasCanvas(
            frm_graphs,
            bg="white",
            height=80,   # summary row only
        )
        self.bias_canvas.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

        frm_data.pack(fill=tk.BOTH, expand=1)
        frm_lists.pack(side=tk.LEFT, fill=tk.Y, expand=0)
        frm_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        frm_graphs.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.frm_main.pack(fill=tk.BOTH, expand=1)

        # Set fixed minimum size to prevent resizing based on content
        # (status bar text, combobox values, etc.)
        self.minsize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)

    def init_status_bar(self) -> None:

        user = "{0} {1} on board {2}".format(self.engine.log_user["last_name"],
                                             self.engine.log_user["first_name"],
                                             self.engine.get_log_ip())

        msg = _("Ready Player {0}").format(user)

        self.status_bar_text.set(msg)

        f = font.Font(family="TkDefaultFont", size=10, weight="bold")

        frm_status_bar = ttk.Frame(self.frm_main,  style="StatusBar.TFrame",)

        self.status = ttk.Label(frm_status_bar,
                                style="LoggedUser.TLabel",
                                textvariable=self.status_bar_text,
                                anchor=tk.W)

        ttk.Label(frm_status_bar, font=f,
                  textvariable=self.status_bar_site_description,
                  relief=tk.FLAT,
                  anchor=tk.W).pack(side=tk.RIGHT, fill=tk.X)
        ttk.Label(frm_status_bar, text=_("Lab:")).pack(side=tk.RIGHT, fill=tk.X)

        ttk.Label(frm_status_bar, font=f,
                  textvariable=self.observations,
                  relief=tk.FLAT,
                  anchor=tk.W).pack(side=tk.RIGHT, fill=tk.X)
        ttk.Label(frm_status_bar, text=_("Observations:")).pack(side=tk.RIGHT, fill=tk.X)

        ttk.Label(frm_status_bar, font=f,
                  textvariable=self.zscore,
                  relief=tk.FLAT,
                  anchor=tk.W).pack(side=tk.RIGHT, fill=tk.X)
        ttk.Label(frm_status_bar, text=_("Z Score:")).pack(side=tk.RIGHT, fill=tk.X)

        ttk.Checkbutton(frm_status_bar,
                        text=_("Delta Degree of Freedom"),
                        onvalue=1,
                        offvalue=0,
                        variable=self.ddof,
                        command=self.on_ddof).pack(side=tk.RIGHT, fill=tk.X)

        ttk.Checkbutton(frm_status_bar,
                        text=_("Show Expired"),
                        onvalue=1,
                        offvalue=0,
                        variable=self.show_expired,
                        command=self.on_show_expired).pack(side=tk.RIGHT, fill=tk.X)

        self.status.pack(side=tk.LEFT, fill=tk.X, expand=1)

        frm_status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def on_open(self) -> None:
        #print(self.engine.current_ids)
        company = self.engine.get_company_data()
        if company:
            # Use site name (hospital) - fallback to lab if site not defined
            site_name = company.get('site', company.get('lab', ''))
            self.title(f"Biovarase {site_name}")
        else:
            self.title("Biovarase")

        self.status_bar_site_description.set(self.get_status_bar_site_description(company))
        self.ddof.set(self.engine.get_ddof())
        self.show_expired.set(self.engine.get_show_expired_batches())
        self.observations.set(self.engine.get_observations())
        self.set_categories()
        self.set_zscore()

    def get_status_bar_site_description(self, company: dict) -> str:
        """
        Build a short label for the status bar using lab name.

        Args:
            company (dict): Dictionary returned by get_company_data(), e.g.
                            {
                                "lab_id": 1,
                                "country": "Italia",
                                "region": "Regione Lazio",
                                "lab": "UOC Biochimica Clinica"
                            }

        Returns:
            str: Lab name, max 80 chars
        """
        if not company:
            return ""

        # Show only lab name
        lab = company.get("lab", "")
        return lab[:80]

    def refresh_context_from_section(self):
        """Re-read section-dependent data and update title, status bar and lists."""
        company = self.engine.get_company_data()
        if company:
            # Use site name (hospital) - fallback to lab if site not defined
            site_name = company.get('site', company.get('lab', ''))
            self.title(f"Biovarase {site_name}")
            self.status_bar_site_description.set(
                self.get_status_bar_site_description(company)
            )
        else:
            self.title("Biovarase")
            self.status_bar_site_description.set("")

        # Close all windows except main (clean state for new section)
        self.engine.close_all_windows_except_main()

        # Reset main's own section-dependent lists/filters
        self.on_reset()

    def _create_listbox(self, container, height=None, width=None, color=None):
        """Create a listbox with vertical scrollbar."""
        sb = ttk.Scrollbar(container, orient=tk.VERTICAL)
        w = tk.Listbox(
            container,
            relief=tk.GROOVE,
            selectmode=tk.EXTENDED,
            exportselection=0,
            height=height,
            width=width,
            background=color,
            font='TkFixedFont',
            yscrollcommand=sb.set
        )
        sb.config(command=w.yview)
        w.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(fill=tk.Y, expand=1)
        return w

    def set_observations(self):
        self.observations.set(self.engine.get_observations())

    def set_zscore(self):
        self.zscore.set(self.engine.get_zscore())

    def on_reset(self):

        self.cbCategories.set('')
        self.cbTests.set('')

        self.set_categories()
        self.set_tests()
        self.set_workstations()

        self.set_observations()
        self.reset_batch_data()
        self.reset_cal_data()
        self.reset_graph()

    def reset_graph(self) -> None:
        """Reset Levey–Jennings and histogram charts and clear results list."""

        # Levey–Jennings
        if getattr(self, "lj_canvas", None) is not None:
            try:
                self.lj_canvas.clear()
            except AttributeError:
                # Vecchia versione / fallback
                self.lj_canvas.delete("all")


        if getattr(self, "bias_canvas", None) is not None:
            self.bias_canvas.clear()

        # Histogram
        

        # Lista risultati
        if getattr(self, "lstResults", None) is not None:
            self.engine.clear_treeview(self.lstResults)

    def reset_batch_data(self) -> None:

        self.expiration.set('')
        self.target.set(0)
        self.sd.set(0)
        self.engine.clear_treeview(self.lstBatches)

    def reset_cal_data(self) -> None:

        self.average.set(0)
        self.calculated_sd.set(0)
        self.cva.set(0)
        self.bias.set(0)
        self.uncertainty.set(0)
        self.te.set(0)
        self.westgard.set('')
        self.set_westgard_alarm()

    def set_batch_data(self) -> None:

        self.expiration.set(self.selected_batch["expiration"])
        self.target.set(round(self.selected_batch["target"], 3))
        self.sd.set(round(self.selected_batch["sd"], 4))

    def set_calculated_data(self, mean: float, sd: float, cv: float, bias: float) -> None:
        """
        Update calculated statistics for the selected batch.

        U is shown as a formatted string like "±2.1 ng/mL",
        where the unit is read automatically from the selected test method.
        """

        self.average.set(mean)
        self.calculated_sd.set(sd)
        self.cva.set(cv)
        self.bias.set(bias)

        # --- Compute expanded uncertainty at control level -------------------
        try:
            u = self.engine.get_uncertainty(cv, bias)
        except Exception as e:
            u = 0.0


        if u is not None and u != 0:
           self.uncertainty.set(f"±{u} %")
        else:
            self.uncertainty.set("")

        # --- Total error (percent) as before --------------------------------
        if self.target.get() != 0:
            et = self.engine.get_te(
                self.target.get(),
                self.average.get(),
                self.cva.get(),
            )
            self.te.set(et)
        else:
            self.te.set(0)

    def set_westgard(self, series: List[float]) -> None:
        """Aggiorna regola Westgard e stile etichetta."""
        # Normalizza la serie
        series = series or []                      # None -> []
        has_data = isinstance(series, (list, tuple)) and len(series) >= 10

        if not has_data:
            self.westgard.set("")                  # <<== No data
            self.set_westgard_alarm()
            return

        # Calcolo regola
        try:
            engine = getattr(self, "engine", None) or self.engine
            rule = engine.get_westgard_violation_rule(
                self.selected_batch["target"], self.selected_batch["sd"],
                [float(x) for x in series],
                self.selected_batch, self.selected_test
            ) or ""
        except Exception as e:
            try: engine.on_log(f"westgard error: {e}")
            except Exception: pass
            rule = ""

        self.westgard.set(rule.strip())
        self.set_westgard_alarm()

    def set_westgard_alarm(self):
        val = (self.westgard.get() or "").strip()

        if len(val) == 0:
            self.lblWestgard.configure(style="black_and_white.TLabel")
            self.westgard.set(_("No data"))
            return

        if val == WESTGARD_ACCEPT:
            style = "westgard_ok.TLabel"
        else:
            style = "westgard_violation.TLabel"

        self.lblWestgard.configure(style=style)


    def set_categories(self) -> None:

        self.selected_category = None
        self.dict_categories = {}
        voices = []
        index = 0

        role = self.engine.log_user["role"]

        # Get categories from test_methods in sections under current lab
        lab_id = self.engine.current_ids.get("lab_id")
        if not lab_id:
            self.cbCategories["values"] = []
            return

        # Query uses organizations table
        # test_methods.org_id references a section (child of lab)
        sql = """
            SELECT DISTINCT categories.category_id,
                            categories.description
            FROM test_methods
            INNER JOIN organizations section ON test_methods.org_id = section.org_id
            INNER JOIN categories ON categories.category_id = test_methods.category_id
                                  AND categories.org_id = section.parent_id
            WHERE section.parent_id = ?
              AND section.org_type = 'section'
              AND test_methods.status = 1
              AND categories.status = 1
            ORDER BY categories.description;
        """
        args = (lab_id,)
            
        rs = self.engine.read(True, sql, args)

        if rs:
            for row in rs:
                self.dict_categories[index] = row["category_id"]
                voices.append(row["description"])
                index += 1

        self.cbCategories["values"] = voices
        self.reset_batch_data()

    def set_tests(self) -> None:
        """Fill tests combobox for selected category."""
        if self.cbCategories.current() == -1:
            return

        self.selected_test = None
        self.test_methods = {}
        voices = []
        index = 0

        cat_index = self.cbCategories.current()
        category_id = self.dict_categories.get(cat_index)
        if category_id is None:
            return

        # Get lab_id from current context
        lab_id = self.engine.current_ids.get("lab_id")
        if not lab_id:
            self.cbTests["values"] = []
            return

        # Query using organizations - filter test_methods in sections under this lab
        sql = """
            SELECT test_methods.test_method_id,
                   tests.description
            FROM test_methods
            JOIN tests ON tests.test_id = test_methods.test_id
            JOIN organizations section ON test_methods.org_id = section.org_id
            WHERE test_methods.category_id = ?
              AND section.parent_id = ?
              AND section.org_type = 'section'
              AND tests.status = 1
              AND test_methods.status = 1
            ORDER BY tests.description;
        """
        args = (category_id, lab_id)

        rs = self.engine.read(True, sql, args)
        if rs:
            for row in rs:
                self.test_methods[index] = row["test_method_id"]
                voices.append(row["description"])
                index += 1

        self.cbTests["values"] = voices
        self.reset_batch_data()

    def set_workstations(self) -> None:
        """Fill workstations treeview for selected test method."""
        self.engine.clear_treeview(self.lstWorkstations)
        self.selected_workstation = None
        self.workstation_test_methods = {}

        if self.cbTests.current() == -1:
            return

        if not self.selected_test_method:
            return

        # Get lab_id from current context
        lab_id = self.engine.current_ids.get("lab_id")
        test_method_id = self.selected_test_method["test_method_id"]

        if not lab_id:
            return

        # Query using organizations - workstations.org_id is section, filter by parent lab
        sql = """
            SELECT workstations.workstation_id,
                   workstations.description,
                   workstations.serial
            FROM workstation_test_methods
            JOIN workstations
              ON workstation_test_methods.workstation_id = workstations.workstation_id
            JOIN organizations section
              ON section.org_id = workstations.org_id
            JOIN equipments
              ON equipments.equipment_id = workstations.equipment_id
            WHERE workstation_test_methods.test_method_id = ?
              AND section.parent_id = ?
              AND section.org_type = 'section'
              AND workstations.status = 1
              AND equipments.status = 1
            ORDER BY workstations.rank ASC;
        """
        args = (test_method_id, lab_id)

        rs = self.engine.read(True, sql, args)

        if rs:
            first_item = None
            for row in rs:
                item_id = self.lstWorkstations.insert(
                    "", tk.END, values=(row["description"], row["serial"])
                )
                self.workstation_test_methods[item_id] = row["workstation_id"]
                if first_item is None:
                    first_item = item_id

            self.reset_batch_data()
            if first_item:
                self.lstWorkstations.selection_set(first_item)
                self.lstWorkstations.event_generate("<<TreeviewSelect>>")

    def _on_batch_changed(self, data=None) -> None:
        """Observer callback for batch changes - refresh batch list.

        Bypasses GUI selection checks and preserves current batch selection.
        """
        # Only refresh if we have valid selection context (instance variables)
        if not (self.selected_test_method and self.selected_workstation):
            return

        # Save current batch_id to restore selection
        current_batch_id = (
            self.selected_batch.get("batch_id") if self.selected_batch else None
        )

        # Refresh batch list (reuse core logic)
        self._populate_batches()

        # Restore previous selection if possible
        if current_batch_id:
            for item_id, batch_id in self.dict_batches.items():
                if batch_id == current_batch_id:
                    self.lstBatches.selection_set(item_id)
                    self.lstBatches.see(item_id)
                    self.lstBatches.event_generate("<<TreeviewSelect>>")
                    return

        # If batch not found, select first item
        children = self.lstBatches.get_children()
        if children:
            self.lstBatches.selection_set(children[0])
            self.lstBatches.event_generate("<<TreeviewSelect>>")

    def _on_tests_changed(self, data=None) -> None:
        """Observer callback for test changes - refresh tests combobox."""
        # Save current selection
        current_index = self.cbTests.current()
        current_test_id = (
            self.selected_test.get("test_id") if self.selected_test else None
        )

        # Refresh tests list
        self.set_tests()

        # Try to restore selection by test_id
        if current_test_id:
            for idx, test_id in self.test_methods.items():
                if test_id == current_test_id:
                    self.cbTests.current(idx)
                    return

        # Fallback: restore by index if valid
        if current_index >= 0 and current_index < len(self.cbTests["values"]):
            self.cbTests.current(current_index)

    def _on_categories_changed(self, data=None) -> None:
        """Observer callback for category changes - refresh categories combobox."""
        # Save current selection
        current_index = self.cbCategories.current()
        current_category_id = (
            self.selected_category.get("category_id") if self.selected_category else None
        )

        # Refresh categories list
        self.set_categories()

        # Try to restore selection by category_id
        if current_category_id:
            for idx, cat_id in self.dict_categories.items():
                if cat_id == current_category_id:
                    self.cbCategories.current(idx)
                    self.cbCategories.event_generate("<<ComboboxSelected>>")
                    return

        # Fallback: restore by index if valid
        if current_index >= 0 and current_index < len(self.cbCategories["values"]):
            self.cbCategories.current(current_index)
            self.cbCategories.event_generate("<<ComboboxSelected>>")

    def _populate_batches(self) -> None:
        """Core logic to populate batch treeview (no early-return checks)."""
        self.engine.clear_treeview(self.lstBatches)
        self.dict_batches = {}

        # Base query
        sql = """
            SELECT batches.batch_id,
                   batches.description,
                   DATE_FORMAT(batches.expiration, '%d-%m-%Y') AS expiration_str,
                   batches.target,
                   batches.sd,
                   batches.lot_number,
                   batches.expiration
            FROM batches
            WHERE batches.test_method_id  = ?
              AND batches.workstation_id  = ?
              AND batches.status          = 1
        """

        # Filter expired batches unless show_expired is checked
        if not self.show_expired.get():
            sql += """
              AND (batches.expiration IS NULL OR batches.expiration >= CURDATE())
            """

        sql += """
            ORDER BY batches.rank ASC;
        """

        args = (
            self.selected_test_method["test_method_id"],
            self.selected_workstation["workstation_id"],
        )

        rs = self.engine.read(True, sql, args)

        if rs:
            for row in rs:
                x = self.engine.get_expiration_date(row["expiration_str"])
                tags = ()
                if x <= 0:
                    tags = ("expired",)
                elif x <= 15:
                    tags = ("expiring",)

                item_id = self.lstBatches.insert(
                    "", tk.END,
                    values=(row["description"], row["lot_number"], row["expiration_str"]),
                    tags=tags
                )
                self.dict_batches[item_id] = row["batch_id"]

    def set_batches(self) -> None:
        """Fill batches treeview for selected test method and workstation."""
        if self.cbTests.current() == -1 or not self.lstWorkstations.selection():
            self.engine.clear_treeview(self.lstBatches)
            self.dict_batches = {}
            self.reset_cal_data()
            self.reset_graph()
            return

        if not (self.selected_test_method and self.selected_workstation):
            self.engine.clear_treeview(self.lstBatches)
            self.dict_batches = {}
            self.reset_cal_data()
            self.reset_graph()
            return

        self._populate_batches()

        children = self.lstBatches.get_children()
        if children:
            self.lstBatches.selection_set(children[0])
            self.lstBatches.event_generate("<<TreeviewSelect>>")
        else:
            self.reset_cal_data()
            self.reset_graph()

    def set_results(self) -> None:
        """Fill results treeview for selected batch and workstation."""
        self.engine.clear_treeview(self.lstResults)
        self.dict_results = {}

        if not (self.selected_batch and self.selected_workstation):
            self.reset_cal_data()
            self.reset_graph()
            return

        try:
            target = float(self.selected_batch.get("target", 0.0))
        except Exception:
            target = 0.0
        try:
            sd = float(self.selected_batch.get("sd", 0.0))
        except Exception:
            sd = 0.0

        sql = """
                SELECT results.result_id,
                       ROUND(results.result, 3) AS result_rounded,
                       DATE_FORMAT(results.received,'%d-%m-%Y') AS received_str,
                       results.status,
                       results.received
                FROM results
                WHERE results.batch_id = ?
                  AND results.workstation_id = ?
                  AND results.is_delete = 0
                ORDER BY results.received DESC
                LIMIT ?;
              """

        args = (
            self.selected_batch["batch_id"],
            self.selected_workstation["workstation_id"],
            int(self.observations.get())
        )

        rs = self.engine.read(True, sql, args)

        if not rs:
            self.reset_cal_data()
            self.reset_graph()
            return

        # Build a map: result_id → notes_count (only active notes)
        result_ids = [row["result_id"] for row in rs]
        notes_map = {}

        if result_ids:
            placeholders = ",".join(["?"] * len(result_ids))
            sql_notes = f"""
                SELECT result_id, COUNT(*) AS notes_count
                FROM notes
                WHERE result_id IN ({placeholders})
                  AND status = 1
                GROUP BY result_id;
            """
            notes_rows = self.engine.read(True, sql_notes, tuple(result_ids)) or []
            notes_map = {
                row["result_id"]: row["notes_count"]
                for row in notes_rows
            }

        for row in rs:
            result_val = float(row["result_rounded"])
            is_enabled = row["status"]
            has_notes = notes_map.get(row["result_id"], 0) > 0

            # Build tags list
            tags = []
            if not is_enabled:
                tags.append("disabled")
            elif sd and abs(result_val - target) > 3 * sd:
                tags.append("violation_3s")
            elif sd and abs(result_val - target) > 2 * sd:
                tags.append("violation_2s")

            if has_notes:
                tags.append("has_notes")

            # Add note indicator to date column
            date_text = f"* {row['received_str']}" if has_notes else row["received_str"]

            item_id = self.lstResults.insert(
                "", tk.END,
                values=(date_text, row["result_rounded"]),
                tags=tuple(tags) if tags else ()
            )
            self.dict_results[item_id] = row["result_id"]

        self.get_values(rs)


    def get_values(self, rs: List[Dict[str, Any]]) -> None:
        """
        Compute statistics and update plots.
        `rs` is a list of dict rows from `set_results`.
        """
        if not (self.selected_batch and self.selected_workstation):
            self.reset_cal_data()
            self.reset_graph()
            self.lj_index_to_result_id = []
            return

        try:
            target = float(self.selected_batch.get("target", 0.0))
        except Exception as e:
            target = 0.0
        try:
            sd = float(self.selected_batch.get("sd", 0.0))
        except Exception as e:
            sd = 0.0

        # --- Build numeric series and LJ index → result_id mapping -------------
        # Include ALL results (enabled and disabled) - reversed for chronological order
        all_results_reversed = list(reversed(rs))

        series = []
        status_list = []  # Track enabled (1) vs disabled (0) points
        lj_map = []
        for row in all_results_reversed:
            try:
                value = float(row.get("result_rounded") or row.get("result") or 0.0)
            except (TypeError, ValueError) as e:
                continue

            series.append(value)
            status_list.append(row.get("status", 1))  # 1=enabled, 0=disabled
            lj_map.append(row.get("result_id"))

        self.lj_index_to_result_id = lj_map

        count_rs = len(rs)
        count_series = len(series)

        if not series:
            self.reset_cal_data()
            self.reset_graph()
            return

        # --- Statistiche QC ----------------------------------------------------
        # Compute statistics ONLY on enabled results (status=1)
        enabled_values = [
            series[i] for i in range(len(series)) if status_list[i] == 1
        ]
        count_enabled = len(enabled_values)

        if enabled_values:
            mean = self.engine.get_mean(enabled_values)
            cv = self.engine.get_cv(enabled_values)
            bias = self.engine.get_bias(mean, target)
            computed_sd = self.engine.get_sd(enabled_values)

            self.set_calculated_data(mean, computed_sd, cv, bias)

            # Westgard rules on enabled results only
            self.set_westgard(enabled_values)
        else:
            # No enabled results - reset calculated data
            self.reset_cal_data()

        # X-axis labels (for ALL results, including disabled)
        dates = self.get_x_labels_all(rs)

        # Levey-Jennings chart with status info
        self.set_levey_jennings_ax(
            count_rs,
            target,
            sd,
            series,
            status_list,  # NEW: pass status list
            count_enabled,  # Count of ENABLED results for the message
            mean if enabled_values else 0.0,
            cv if enabled_values else 0.0,
            dates,
            dates,
        )


        # Bias chart: target vs mean (using enabled values only)
        if enabled_values:
            self.set_bias_chart(enabled_values, target, mean)
        else:
            # No enabled values - clear bias chart
            if hasattr(self, "bias_canvas"):
                self.bias_canvas.clear()


    # EVENT HANDLERS (SELECTION)
    def on_selected_category(self, evt: Optional[tk.Event]) -> None:
        """Handle category selection change."""
        if self.cbCategories.current() == -1:
            return

        self.cbTests.set("")
        self.engine.clear_treeview(self.lstWorkstations)

        index = self.cbCategories.current()
        pk = self.dict_categories.get(index)
        if pk is None:
            return

        self.selected_category = self.engine.get_selected("categories", "category_id", pk)
        self.reset_batch_data()
        self.reset_cal_data()
        self.reset_graph()
        self.set_tests()

    def on_selected_test(self, event: Optional[tk.Event]) -> None:
        """Handle test selection change."""
        if self.cbCategories.current() == -1:
            return

        if self.cbTests.current() == -1:
            self.engine.clear_treeview(self.lstWorkstations)
            self.reset_batch_data()
            self.reset_cal_data()
            self.reset_graph()
            return

        index = self.cbTests.current()
        pk = self.test_methods.get(index)
        if pk is None:
            return

        # test_method and test as dictionaries
        self.selected_test_method = self.engine.get_selected(
            "test_methods", "test_method_id", pk
        )
        if self.selected_test_method:
            test_id = self.selected_test_method.get("test_id")
            if test_id is not None:
                self.selected_test = self.engine.get_selected("tests", "test_id", test_id)
            else:
                self.selected_test = None
        else:
            self.selected_test = None

        self.reset_batch_data()
        self.reset_cal_data()
        self.reset_graph()
        self.set_workstations()

    def on_selected_workstation(self, evt: Optional[tk.Event]) -> None:
        """Handle workstation selection change."""
        if not self.lstWorkstations.selection():
            self.selected_workstation = None
            self.reset_batch_data()
            return

        item_id = self.lstWorkstations.selection()[0]
        pk = self.workstation_test_methods.get(item_id)
        if pk is None:
            self.selected_workstation = None
            self.reset_batch_data()
            return

        self.selected_workstation = self.engine.get_selected(
            "workstations", "workstation_id", pk
        )
        self.reset_batch_data()
        self.set_batches()

    def on_selected_batch(self, evt: Optional[tk.Event] = None) -> None:
        """Handle batch selection change."""
        if not self.lstBatches.selection():
            self.selected_batch = None
            self.reset_cal_data()
            self.reset_graph()
            return

        item_id = self.lstBatches.selection()[0]
        pk = self.dict_batches.get(item_id)
        if pk is None:
            self.selected_batch = None
            self.reset_cal_data()
            self.reset_graph()
            return

        self.selected_batch = self.engine.get_selected("batches", "batch_id", pk)
        self.set_batch_data()
        self.set_results()

    def on_selected_result(self, event: Optional[tk.Event]) -> None:
        """Handle result selection change and load selected_result dict."""
        selection = self.lstResults.selection()
        if not selection:
            self.selected_result = None
            return

        item_id = selection[0]
        pk = self.dict_results.get(item_id)
        if pk is None:
            self.selected_result = None
            return

        self.selected_result = self.engine.get_selected("results", "result_id", pk)

    def _open_result_editor_for_item(self, item_id: str) -> None:
        """Open result editor in update mode for the given treeview item_id."""
        try:
            # --- Build dictionaries required by result.py ---------------------
            result_id = self.dict_results.get(item_id)
            if result_id is None:
                messagebox.showerror(
                    self.engine.app_title,
                    _("Result not found. Cannot edit."),
                    parent=self,
                )
                return

            self.selected_result = self.engine.get_selected("results", "result_id", result_id)

            if not self.selected_result:
                messagebox.showerror(
                    self.engine.app_title,
                    _("Result not found. Cannot edit."),
                    parent=self,
                )
                return

            # Get selected batch.
            batch_id = self.selected_result["batch_id"]
            self.selected_batch = self.engine.get_selected("batches", "batch_id", batch_id)

            if not self.selected_batch:
                messagebox.showerror(
                    self.engine.app_title,
                    _("Batch not found. Cannot edit result."),
                    parent=self,
                )
                return

            # Get selected test_method and then test.
            test_method_id = self.selected_batch["test_method_id"]
            self.selected_test_method = self.engine.get_selected(
                "test_methods", "test_method_id", test_method_id
            )

            if not self.selected_test_method:
                messagebox.showerror(
                    self.engine.app_title,
                    _("Test method not found. Cannot edit result."),
                    parent=self,
                )
                return

            test_id = self.selected_test_method["test_id"]
            self.selected_test = self.engine.get_selected("tests", "test_id", test_id)

            # Get selected workstation.
            workstation_id = self.selected_result["workstation_id"]
            self.selected_workstation = self.engine.get_selected(
                "workstations", "workstation_id", workstation_id
            )

            views.result.UI(self, item_id).on_open()

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )

    def on_lj_point_double_click(self, info: dict) -> None:
        """
        Handle double–click on a Levey–Jennings point.

        info keys (see ljcanvas.py):
            - index (0-based)
            - value (float)
            - label (optional X label, e.g., date)
        """
        try:
            idx = info.get("index")
            if idx is None:
                return

            mapping = getattr(self, "lj_index_to_result_id", None) or []
            if not (0 <= idx < len(mapping)):
                # Nothing to do if mapping is missing or out of range
                return

            result_id = mapping[idx]

            # Find corresponding treeview item_id
            item_id = None
            for k, rid in self.dict_results.items():
                if rid == result_id:
                    item_id = k
                    break

            if item_id is None:
                messagebox.showerror(
                    self.engine.app_title,
                    _("Result not found in list. Cannot edit."),
                    parent=self,
                )
                return

            # Sync selection in the treeview
            self.lstResults.selection_set(item_id)
            self.lstResults.see(item_id)

            # Open editor
            self._open_result_editor_for_item(item_id)

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )



    def get_x_labels(self, rs: List[Dict[str, Any]]) -> List[str]:
        """Return list of date labels for enabled results."""
        enabled = [row for row in rs if row.get("status", 0) != 0]
        return [row.get("received_str", "") for row in reversed(enabled)]

    def get_x_labels_all(self, rs: List[Dict[str, Any]]) -> List[str]:
        """Return list of date labels for ALL results (including disabled)."""
        return [row.get("received_str", "") for row in reversed(rs)]

    def set_levey_jennings_ax(
        self,
        count_rs: int,
        target: float,
        sd: float,
        series: List[float],
        status_list: List[int],
        count_series: int,
        compute_average: float,
        compute_cv: float,
        x_labels: List[str],
        dates: List[str],
    ) -> None:
        """
        Draw Levey–Jennings chart using LeveyJenningsCanvas.

        Args:
            status_list: List of status values (1=enabled, 0=disabled) same length as series
        """
        try:
            # --- Short X labels: only day-month (dd-mm) -----------------------
            short_dates = []
            for d in dates or []:
                # Expecting format like "21-09-2025"
                if isinstance(d, str) and len(d) >= 5:
                    short_dates.append(d[:5])  # "21-09-2025" -> "21-09"
                else:
                    short_dates.append(str(d))

            # --- Y axis label: unit of measure --------------------------------
            unit_id = None
            if self.selected_test_method:
                unit_id = self.selected_test_method.get("unit_id")

            um = self.engine.get_um(unit_id) if unit_id is not None else None
            y_axis_caption = um.get("description") if um else ""

            # --- Title: test, workstation, control, lot ------------------------
            test_name = self.selected_test.get("description") if self.selected_test else NO_DATA
            ws_name = self.selected_workstation.get("description") if self.selected_workstation else NO_DATA
            ws_serial = self.selected_workstation.get("serial") if self.selected_workstation else ""
            control_name = ""
            if self.selected_batch:
                control_name = self.engine.get_control_name(self.selected_batch.get("control_id"))
            lot_number = self.selected_batch.get("lot_number") if self.selected_batch else ""

            title = f"{test_name} - {ws_name} {ws_serial} - Lot {lot_number}"

            # --- Bottom-right text: computed / total ---------------------------
            # Example: "Computed 28 on 30 results" or "Computed 30 on 30 results"
            bottom_text = f"Computed {count_series} on {count_rs} results"
            if count_series != count_rs:
                # Some results were disabled / excluded from the series
                bottom_text += " (some results disabled)"

            # --- Draw chart ----------------------------------------------------
            self.lj_canvas.draw_chart(
                series=series,
                target=target,
                sd=sd,
                status=status_list,      # Pass status info to show disabled points
                title=title,
                dates=short_dates,
                x_axis_caption="Date",
                y_axis_caption=y_axis_caption,
                show_values=True,        # show values only on anomalous points
                bottom_text=bottom_text,
            )

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )

    def set_bias_chart(self, series, target, avg):
        """Update bias chart (target vs mean)."""
        if not hasattr(self, "bias_canvas"):
            return

        values = series or []
        if not values:
            self.bias_canvas.clear()
            return

        # Unit label from selected_test_method (same logica del LJ)
        unit = ""
        try:
            unit_id = None
            if self.selected_test_method:
                unit_id = self.selected_test_method.get("unit_id")

            if unit_id is not None:
                um = self.engine.get_um(unit_id)
                if isinstance(um, dict):
                    unit = um.get("description", "") or ""
                elif isinstance(um, (list, tuple)):
                    unit = um[0] if um else ""
                elif um:
                    unit = str(um)
        except Exception as e:
            unit = ""

        # Title: test + (optional) control/lot
        test_name = (
            self.selected_test.get("description")
            if self.selected_test
            else "No data"
        )

        control_name = ""
        lot_number = ""
        if self.selected_batch:
            try:
                control_name = self.engine.get_control_name(
                    self.selected_batch.get("control_id")
                )
            except Exception as e:
                control_name = ""
            lot_number = self.selected_batch.get("lot_number", "")

        if control_name:
            title = f"{test_name} - {control_name}"
        else:
            title = test_name
        if lot_number:
            title = f"{title} (Lot {lot_number})"

        # Disegna il grafico Bias
        self.bias_canvas.draw_bias(
            series=values,
            target=target,
            title=title,
            unit=unit,
        )

    def on_daily_validation(self, evt=None):
        """Open Daily QC Validation window."""
        if not self.engine.can_validate_qc():
            messagebox.showwarning(
                _("Access Denied"),
                self.engine.user_not_enable
            )
            return
        
        views.daily_validation.UI(self).on_open()

    def on_tests(self) -> None:
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return
        
        views.tests.UI(self).on_open()

    def on_test_methods(self) -> None:
        """Open Test Methods window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.test_methods.UI(self).on_open()

    def on_workstation_test_methods(self):
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return
        
        views.workstation_test_methods.UI(self).on_open()

    def on_categories(self):
        # Admin and Superuser can manage categories
        role = self.engine.log_user.get("role", 99)
        if role > 1:
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.categories.UI(self).on_open()

    def on_samples(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return
        
        views.samples.UI(self).on_open()

    def on_units(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.units.UI(self).on_open()

    def on_methods(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.methods.UI(self).on_open()

    def on_controls(self,):
        """Open Controls window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.controls.UI(self).on_open()

    def on_equipments(self):

        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)

        else:
            views.equipments.UI(self).on_open()

    def on_workstations(self,):
        """Open Workstations window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.workstations.UI(self).on_open()

    def on_suppliers(self,):

        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
        else:
            views.suppliers.UI(self).on_open()

    def on_labs(self):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.labs.UI(self).on_open()

    def on_sites(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.sites.UI(self).on_open()

    def on_organizations(self,):
        """Open Organizations management window (App Admin only)."""
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.organizations.UI(self).on_open()

    def on_sections(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return
        
        views.sections.UI(self).on_open()

    def on_observations(self,):
        views.observations.UI(self).on_open()
        
    def on_analitical(self,):
        views.analytical.UI(self).on_open()

    def on_set_zscore(self,):
        views.set_zscore.UI(self).on_open()

    def on_batches(self) -> None:
        """Open Batches window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.batches.UI(self).on_open()

    def on_actions(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return
        
        views.actions.UI(self).on_open()

    def on_users(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return
        
        views.users.UI(self).on_open()

    def on_zscore(self,):
        views.zscore.UI(self,)

    def on_plots(self,):

        if self.cbTests.current() != -1:

            if self.lstBatches.selection():

                index = self.cbTests.current()
                pk = self.test_methods[index]
                selected_test_method = self.engine.get_selected("test_methods", "test_method_id", pk)
                views.plots.UI(self,).on_open(selected_test_method,
                                               self.selected_workstation,
                                               int(self.observations.get()))
            else:
                msg = _("Not enough data to plot.\nSelect an instrument and a batch.")
                messagebox.showwarning(self.engine.app_title, msg, parent=self)
        else:
            msg = _("Not enough data to plot.\nSelect a test.")
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            
    def on_tea(self):
        """
        Open TEA window if:
          - a test is selected
          - a batch is selected
          - the test has goals with to_export = 1
        """

        if self.cbTests.current() == -1:
            messagebox.showwarning(self.engine.app_title,
                                   _("Not enough data to plot.\nSelect a test."),
                                   parent=self)
            return

        if not self.lstBatches.selection():
            messagebox.showwarning(self.engine.app_title,
                                   _("Not enough data to plot.\nSelect a batch."),
                                   parent=self)
            return

        index = self.cbTests.current()
        pk = self.test_methods[index]

        # Get full test_method + goals structure
        selected = self.engine.get_test_method_with_goals(pk)

        if not selected:
            messagebox.showwarning(self.engine.app_title,
                                   _("Test method not found."),
                                   parent=self)
            return

        # Check if TEA is enabled (to_export == 1)
        if selected.get("to_export", 0) != 1:
            messagebox.showwarning(self.engine.app_title,
                                   _("Selected test is not enabled for this plot type."),
                                   parent=self)
            return

        # Everything OK → open TEA
        views.tea.UI(self).on_open(
            selected,                       # unified dict
            self.selected_workstation,
            int(self.observations.get())
        )


    def on_youden(self):
        """Open Youden selector dialog to choose batches for Youden plot."""
        # Pre-select workstation and test if already selected in main window
        preselect_ws_id = None
        preselect_tm_id = None

        if hasattr(self, 'selected_workstation') and self.selected_workstation:
            preselect_ws_id = self.selected_workstation.get("workstation_id")

        if hasattr(self, 'selected_test_method') and self.selected_test_method:
            preselect_tm_id = self.selected_test_method.get("test_method_id")

        views.youden_selector.UI(
            self,
            self._on_youden_plot,
            preselect_workstation_id=preselect_ws_id,
            preselect_test_method_id=preselect_tm_id
        )

    def _on_youden_plot(self, test_method, workstation, batches, data):
        """
        Callback from Youden selector - open the actual Youden plot.

        Args:
            test_method: Selected test method dict
            workstation: Selected workstation dict
            batches: List of two batch dicts [level1, level2]
            data: List of two series [series1, series2]
        """
        views.youden.UI(self).on_open(test_method, workstation, batches, data)

    def on_bland_altman(self):
        """Open Bland-Altman comparison view."""
        views.bland_altman.UI(self).on_open()

    def on_bland_altman_alert(self):
        """Open Bland-Altman alert scanner view."""
        views.bland_altman_alert.UI(self).on_open()

    def on_qc_report(self):
        """Open QC Report generator window."""
        views.qc_report.UI(self).on_open()

    def on_export_notes(self) -> None:
        views.export_notes.UI(self).on_open()

    # Quick Data Analysis removed - functionality integrated into Daily Validation
    # def on_quick_data_analysis(self,):
    #     views.quick_data_analysis.UI(self).on_open()

    def on_analitycal_goals(self,):
        views.analitycal_goals.UI(self).on_open()

    def on_export_counts(self) -> None:
        views.counts.UI(self).on_open()

    def on_ddof(self,):

        if self.ddof.get() == True:
            self.engine.set_ddof(1)
        else:
            self.engine.set_ddof(0)

        self.ddof.set(self.engine.get_ddof())

        try:
            self.set_results()
        except AttributeError:
            msg = _("Attention please.\nNo batch selected.")
            messagebox.showinfo(self.engine.app_title, msg, parent=self)

    def on_show_expired(self):
        """Toggle visibility of expired batches and refresh list."""
        if self.show_expired.get():
            self.engine.set_show_expired_batches(1)
        else:
            self.engine.set_show_expired_batches(0)

        self.show_expired.set(self.engine.get_show_expired_batches())

        # Refresh batch list with new filter
        try:
            self.set_batches()
        except AttributeError:
            pass  # No test method/workstation selected

    def on_insert_demo_result(self, evt: Optional[tk.Event] = None) -> None:

        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        if self.lstBatches.selection():

            msg = _("Insert 30 random results for:\n{0}\nbatch {1} {2}?").format(
                self.selected_test["description"],
                self.selected_batch["lot_number"],
                self.selected_batch["description"]
            )

            if messagebox.askyesno(self.engine.app_title,
                                   msg,
                                   parent=self) == True:


                try:
                    cur = self.engine.con.cursor()
                    # Begin transaction
                    cur.execute("START TRANSACTION")  # Use START TRANSACTION for better MariaDB compatibility

                    sql_delete = "DELETE FROM results WHERE batch_id =? AND workstation_id =?;"
                    args = (self.selected_batch["batch_id"], self.selected_workstation["workstation_id"])
                    cur.execute(sql_delete, args)

                    target = float(self.selected_batch["target"])
                    sd = float(self.selected_batch["sd"])
                    min_val = round(target - sd, 2)
                    max_val = round(target + sd, 2)
                                                                                        
                    sql_insert = "INSERT INTO results(batch_id, lab_id, workstation_id, result, received, log_time, log_id) VALUES(?,?,?,?,?,?,?)"
                    log_time = self.engine.get_log_time()

                    # Convert log_time to datetime if string
                    if isinstance(log_time, str):
                        current_log_time = datetime.datetime.strptime(log_time, '%Y-%m-%d %H:%M:%S')
                    else:
                        current_log_time = log_time

                    # Insert 30 results
                    for _i in range(30):
                        result = round(random.uniform(min_val, max_val), 2)
                        args = (
                            self.selected_batch["batch_id"],
                            self.selected_batch["lab_id"],
                            self.selected_workstation["workstation_id"],
                            result,
                            current_log_time,
                            current_log_time,
                            self.engine.log_user["user_id"]
                        )
                        cur.execute(sql_insert, args)
                        current_log_time += datetime.timedelta(days=1)

                    self.engine.con.commit()  # Commit the transaction
                    self.set_results()
                except Exception as e:  # Catch generic exception for rollback
                    self.engine.con.rollback()  # Rollback on any error
                    self.engine.on_log(inspect.stack()[0][3],
                                                           str(e),
                                                           sys.exc_info()[0],
                                                           sys.modules[__name__])
                finally:
                    if 'cur' in locals() and cur:  # Check if cursor was created before closing
                        cur.close()

        else:
            msg = "Attention please.\nBefore add 30 random results you must select a batch."
            messagebox.showinfo(self.engine.app_title, msg, parent=self)


    def on_batch_double_button(self, evt: Optional[tk.Event] = None) -> None:

        if self.lstBatches.selection():
            self.on_add_result()
        else:
            msg = _("Attention please.\nSelect a batch.")
            messagebox.showinfo(self.engine.app_title, msg, parent=self)


    def on_add_result(self):
        """Open result editor in insert mode for current batch and workstation."""
        # Check read-only mode (block autologin users)
        if self.engine.is_read_only():
            msg = _("Read-only mode.\nCannot add results.")
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        if not self.lstBatches.selection():
            msg = _(
                "Attention please.\nBefore adding a result you must select a batch."
            )
            messagebox.showinfo(self.engine.app_title, msg, parent=self)
            return

        batch_item = self.lstBatches.selection()[0]
        batch_id = self.dict_batches[batch_item]
        self.selected_batch = self.engine.get_selected("batches", "batch_id", batch_id)

        if not self.selected_batch:
            messagebox.showerror(
                self.engine.app_title,
                _("Batch not found. Cannot add result."),
                parent=self,
            )
            return

        # Get selected test_method and then test.
        test_method_id = self.selected_batch["test_method_id"]
        self.selected_test_method = self.engine.get_selected(
            "test_methods", "test_method_id", test_method_id
        )

        if not self.selected_test_method:
            messagebox.showerror(
                self.engine.app_title,
                _("Test method not found. Cannot edit result."),
                parent=self,
            )
            return

        test_id = self.selected_test_method["test_id"]
        self.selected_test = self.engine.get_selected("tests", "test_id", test_id)

        workstation_id = self.selected_batch["workstation_id"]
        self.selected_workstation = self.engine.get_selected("workstations", "workstation_id", workstation_id)

        views.result.UI(self).on_open()


    def on_update_result(self, evt: Optional[tk.Event] = None) -> None:
        """Default double–click on results list: open notes editor."""
        try:
            # Check read-only mode (block autologin users)
            if self.engine.is_read_only():
                msg = _("Read-only mode.\nCannot edit notes.")
                messagebox.showwarning(self.engine.app_title, msg, parent=self)
                return

            selection = self.lstResults.selection()
            if not selection:
                msg = _("Attention please.\nSelect a result.")
                messagebox.showinfo(self.engine.app_title, msg, parent=self)
                return

            # Ensure selected_result is set before opening notes
            item_id = selection[0]
            pk = self.dict_results.get(item_id)
            if pk:
                self.selected_result = self.engine.get_selected("results", "result_id", pk)

            views.notes.UI(self).on_open()

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )

    def _open_document(self, key: str, error_msg: str) -> None:
        """Helper to open documents from documents.json."""
        engine = self.engine
        engine.busy(self)

        try:
            ret = engine.launch_document(key)
        finally:
            engine.not_busy(self)

        if not ret:
            messagebox.showinfo(
                self.engine.app_title,
                error_msg,
                parent=self
            )

    def on_bvv(self) -> None:
        self._open_document(
            "biological_values",
            _("The file Biological Variation Values does not exist or cannot be opened.")
        )

    def on_user_manual(self) -> None:
        self._open_document(
            "user_manual",
            _("The Biovarase User Manual does not exist or cannot be opened.")
        )

    def on_qc_thecnical_manual(self) -> None:
        self._open_document(
            "qc_technical",
            _("The QC Technical Manual does not exist or cannot be opened.")
        )

    def on_get_guidelines(self) -> None:
        self._open_document(
            "guidelines",
            _("The Biovarase Guidelines file does not exist or cannot be opened.")
        )

    def on_license(self) -> None:
        views.license.UI(self).on_open()

    def on_python_version(self) -> None:
        s = self.engine.get_python_version()
        messagebox.showinfo(self.engine.app_title, s, parent=self)

    def on_tkinter_version(self) -> None:
        s = "Tkinter patchlevel\n{0}".format(self.nametowidget(".").tk.call("info", "patchlevel"))
        messagebox.showinfo(self.engine.app_title, s, parent=self)

    def on_about(self) -> None:
        messagebox.showinfo(self.engine.app_title,
                            self.nametowidget(".").info,
                            parent=self)

    def _on_language_change(self) -> None:
        """Handle language change from menu."""
        lang = self.lang_var.get()
        self.engine.set_language(lang)
        set_language(lang)
        messagebox.showinfo(
            self.engine.app_title,
            _("Restart to apply language change."),
            parent=self
        )

    def on_change_password(self) -> None:
        views.change_password.UI(self, ).on_open()

    def on_log(self,):
        self.engine.get_log_file()

    def on_import_results(self) -> None:
        """Open Import Results window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        views.importer.UI(self, ).on_open()
   

    def on_change_user(self, _evt=None):
        """
        Change User - Logout current user and show login screen.
        
        Workflow:
        1. Confirm with user
        2. Close all windows except main
        3. Reset user context
        4. Show login dialog
        5. If login successful: reload main
        6. If login canceled: exit application
        
        Args:
            _evt: Optional Tkinter event (for keyboard shortcut)
        """
        # Confirm action
        msg = _("Logout and switch to different user?\n\nAll open windows will be closed.")
        if not messagebox.askyesno(_("Change User"), msg, parent=self, icon="question"):
            return
        
        try:
            # Close all windows except main
            self.engine.close_all_windows_except_main()
            
            # Reset user context
            self.engine.log_user.clear()
            
            # Show login dialog
            login_window = views.login.Login(self)
            
            # Wait for login to complete
            self.wait_window(login_window)
            
            # Check if login was successful
            if self.engine.log_user.get("user_id"):
                # Login successful - rebuild menu (role-dependent) and reload
                self._rebuild_menu()
                self.on_open()

                # Welcome message
                first = self.engine.log_user.get("first_name", "")
                last = self.engine.log_user.get("last_name", "")
                user_name = f"{first} {last}".strip()
                messagebox.showinfo(
                    _("Welcome"),
                    f"{_('Logged in as:')} {user_name}",
                    parent=self
                )
            else:
                # Login canceled - exit application
                self.on_exit()
                
        except Exception as exc:
            # Log error
            self.engine.on_log(
                "on_change_user",
                str(exc),
                type(exc).__name__,
                sys.modules[__name__],
                inspect.currentframe()
            )
            messagebox.showerror(_("Error"), f"{_('Failed to change user:')} {exc}", parent=self)

    def _fetch_available_sections(self, role):
        """Fetch sections available to user based on role.

        Uses organizations table for section hierarchy.

        Args:
            role: User role (0=Admin, etc.)

        Returns:
            List of section dicts with section_id, description, and lab_name, or None on error.
        """
        if role == 0:
            # Admin: all active sections with lab name
            sql = """
                SELECT
                    section.org_id AS section_id,
                    section.description,
                    lab.description AS lab_name
                FROM organizations section
                JOIN organizations lab ON section.parent_id = lab.org_id
                WHERE section.org_type = 'section'
                  AND section.status = 1
                ORDER BY lab.description, section.description
            """
            args = ()
        else:
            # Other users: only sections in their lab
            lab_id = self.engine.current_ids.get("lab_id")
            sql = """
                SELECT
                    section.org_id AS section_id,
                    section.description,
                    lab.description AS lab_name
                FROM organizations section
                JOIN organizations lab ON section.parent_id = lab.org_id
                WHERE section.parent_id = ?
                  AND section.org_type = 'section'
                  AND section.status = 1
                ORDER BY lab.description, section.description
            """
            args = (lab_id,)

        return self.engine.read(True, sql, args)

    def _show_section_picker_dialog(self, sections, current_section_id):
        """Show modal dialog to pick a section.

        Args:
            sections: List of section dicts
            current_section_id: Currently active section ID

        Returns:
            Selected section_id or None if canceled.
        """
        dialog = tk.Toplevel(self)
        dialog.title(_("Change Section"))
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Label
        tk.Label(
            dialog,
            text=_("Select new section:"),
            font=("TkDefaultFont", 10, "bold")
        ).pack(padx=10, pady=10, anchor=tk.W)

        # Listbox with scrollbar
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            font=("TkFixedFont", 10),
            activestyle="dotbox"
        )
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate listbox with "Lab - Section" format
        dict_sections = {}
        for idx, section in enumerate(sections):
            section_id = section["section_id"]
            dict_sections[idx] = section_id
            lab_name = section.get("lab_name", "")
            section_name = section["description"]
            display_text = f"{lab_name} — {section_name}" if lab_name else section_name
            listbox.insert(tk.END, display_text)

            if section_id == current_section_id:
                listbox.selection_set(idx)
                listbox.see(idx)

        # Result container (mutable for closure)
        selected_section_id = [None]

        def on_select():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning(_("No Selection"), _("Please select a section."), parent=dialog)
                return
            selected_section_id[0] = dict_sections[selection[0]]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text=_("OK"), width=10, command=on_select).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=_("Cancel"), width=10, command=on_cancel).pack(side=tk.LEFT, padx=5)

        listbox.bind("<Double-Button-1>", lambda e: on_select())

        self.wait_window(dialog)
        return selected_section_id[0]

    def _apply_section_change(self, new_section_id, sections):
        """Apply section change: update state, close windows, reload.

        Args:
            new_section_id: The section ID to switch to
            sections: List of section dicts (for name lookup)
        """
        self.engine.set_section_id(new_section_id)

        # Update all hierarchical IDs (site_id, lab_id, section_id, etc.)
        ids = self.engine.get_idd_by_section_id(new_section_id)
        if ids:
            self.engine.current_ids.update(ids)

        self.refresh_context_from_section()

        # Build display name with lab
        section_data = next(
            (s for s in sections if s["section_id"] == new_section_id),
            None
        )
        if section_data:
            lab_name = section_data.get("lab_name", "")
            section_name = section_data["description"]
            display_name = f"{lab_name} — {section_name}" if lab_name else section_name
        else:
            display_name = f"{_('Section')} {new_section_id}"

        messagebox.showinfo(_("Section Changed"), f"{_('Now working in:')} {display_name}", parent=self)

    def on_change_lab(self, _evt=None):
        """Change Laboratory - Admin only. Switch to different laboratory without logout."""
        from views.lab_selector import LabSelectorDialog

        if self.engine.get_user_role() != 0:
            messagebox.showwarning(
                _("Permission Denied"),
                _("Only administrators can change laboratory."),
                parent=self
            )
            return

        try:
            current_lab_id = self.engine.get_lab_id()

            # Show lab selector dialog with current lab pre-selected
            dialog = LabSelectorDialog(self, default_lab_id=current_lab_id)
            self.wait_window(dialog)
            selected_lab_id = dialog.get_selected_lab_id()

            if selected_lab_id is None:
                # User cancelled
                return

            if selected_lab_id == current_lab_id:
                messagebox.showinfo(
                    _("Same Laboratory"),
                    _("Already in this laboratory."),
                    parent=self
                )
                return

            # Apply lab change
            self.engine.init_current_ids_from_user(selected_lab_id)

            # Close all child windows and refresh
            self._close_all_windows()
            self.set_categories()

            # Get lab name for confirmation message
            lab_row = self.engine.read(
                False,
                "SELECT description FROM labs WHERE lab_id = ?",
                (selected_lab_id,)
            )
            lab_name = lab_row["description"] if lab_row else str(selected_lab_id)

            messagebox.showinfo(
                _("Laboratory Changed"),
                f"{_('Now working in:')} {lab_name}",
                parent=self
            )

        except Exception as exc:
            self.engine.on_log(
                "on_change_lab",
                str(exc),
                type(exc).__name__,
                sys.modules[__name__],
                inspect.currentframe()
            )
            messagebox.showerror(
                _("Error"),
                f"{_('Failed to change laboratory:')} {exc}",
                parent=self
            )

    def on_change_section(self, _evt=None):
        """Change Section - Switch to different section without logout. DEPRECATED."""
        role = self.engine.get_user_role()

        if role == 3:
            messagebox.showwarning(_("Permission Denied"), _("Read-only users cannot change section."), parent=self)
            return

        try:
            sections = self._fetch_available_sections(role)

            if not sections:
                messagebox.showwarning(_("No Sections"), _("No sections available for selection."), parent=self)
                return

            current_section_id = self.engine.get_section_id()
            new_section_id = self._show_section_picker_dialog(sections, current_section_id)

            if new_section_id is None:
                return

            if new_section_id == current_section_id:
                messagebox.showinfo(_("Same Section"), _("Already in this section."), parent=self)
                return

            self._apply_section_change(new_section_id, sections)

        except Exception as exc:
            self.engine.on_log(
                "on_change_section",
                str(exc),
                type(exc).__name__,
                sys.modules[__name__],
                inspect.currentframe()
            )
            messagebox.showerror(_("Error"), f"{_('Failed to change section:')} {exc}", parent=self)

    def on_close(self) -> None:
        # Unsubscribe from events (Observer pattern)
        self.engine.unsubscribe("batch_changed", self._on_batch_changed)
        self.engine.unsubscribe("tests_changed", self._on_tests_changed)
        self.engine.unsubscribe("categories_changed", self._on_categories_changed)
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.nametowidget(".").on_exit()