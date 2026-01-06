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

from ljcanvas import LeveyJenningsCanvas
from bias_canvas import BiasCanvas

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
import views.users
import views.samples
import views.analitycal_goals
import views.tea
import views.analytical
import views.change_password
import views.sites
import views.importer
import views.zscore
import views.daily_validation


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

        # mapping Levey–Jennings point index → result_id (solo risultati abilitati)
        self.lj_index_to_result_id = []

        self.init_ui()
        self.init_menu()
        self.init_status_bar()
        self.center_ui()
        
    def center_ui(self):

        """Set high, width, x, y coords"""
        #get screen width and height
        screen_width  = self.nametowidget(".").winfo_screenwidth()
        screen_height  = self.nametowidget(".").winfo_screenheight()

        #get dimension from dimension file
        d = self.nametowidget(".").engine.get_dimensions()
        window_width = int(d['w'])
        window_height = int(d['h'])
        
        # calculate position x, y
        position_right = int(screen_width /2 - window_width/2)
        position_top = int(screen_height /2 - window_height/2)
        #we only position the window because otherwise it doesn't resize well on laptop
        self.geometry('+%d+%d'%(position_right, position_top))
        
    def init_menu(self) -> None:

        m_main = tk.Menu(self, bd=1)

        m_file = tk.Menu(m_main, tearoff=0, bd=1)
        m_exports = tk.Menu(m_file)
        m_imports = tk.Menu(m_file)
        m_plots = tk.Menu(m_main, tearoff=0, bd=1)
        m_edit = tk.Menu(m_main, tearoff=0, bd=1)
        m_documents = tk.Menu(m_main, tearoff=0, bd=1)
        m_adm = tk.Menu(m_main, tearoff=0, bd=1)
        m_about = tk.Menu(m_main, tearoff=0, bd=1)

        m_main.add_cascade(label="File", underline=0, menu=m_file)
        m_main.add_cascade(label="Plots", underline=0, menu=m_plots)
        m_main.add_cascade(label="Edit", underline=0, menu=m_edit)
        m_main.add_cascade(label='Imports', underline=1, menu=m_imports)
        m_main.add_cascade(label='Exports', underline=1, menu=m_exports)
        m_main.add_cascade(label="Documents", underline=0, menu=m_documents)
        m_main.add_cascade(label="Admin", underline=0, menu=m_adm)
        m_main.add_cascade(label="?", underline=0, menu=m_about)

        if self.nametowidget(".").engine.log_user["role"] != 0:

            items = (("Reset", 0, self.on_reset),
                     ("Analytica", 0, self.on_analitical),
                     ("Z Score", 0, self.on_zscore),)
        else:

            items = (("Reset", 0, self.on_reset),
                     ("Insert random results", 0, self.on_insert_demo_result),
                     ("Analytica", 0, self.on_analitical),
                     ("Z Score", 0, self.on_zscore),)
            

        for i in items:
            m_file.add_command(label=i[0], underline=i[1], command=i[2])

        
        m_file.add_separator()

        m_file.add_command(label="Change User",
                           underline=7,
                           accelerator="Ctrl+U",
                           command=self.on_change_user)
        m_file.add_command(label="Change Section",
                           underline=7,
                           accelerator="Ctrl+E",
                           command=self.on_change_section)
        m_file.add_separator()
        m_file.add_command(label="Change Password",
                           underline=7,
                           command=self.on_change_password)
        m_file.add_command(label="Log",
                           underline=0,
                           command=self.on_log)

        m_file.add_command(label="Exit", underline=0, command=self.on_close)

        items = (("Plots", 0, self.on_plots),
                 ("Youden", 0, self.on_youden),
                 ("Tea", 0, self.on_tea),)

        for i in items:
            m_plots.add_command(label=i[0], underline=i[1], command=i[2])

        items = (("Daily Validation", 0, self.on_daily_validation),
                 ("Batches", 0, self.on_batches),
                 ("Test Methods", 9, self.on_test_methods),
                 ("Tests Methods Workstations", 0, self.on_workstation_test_methods),
                 ("Workstations", 0, self.on_workstations),
                 ("Controls", 0, self.on_controls),
                 ("Set Observations", 4, self.on_observations),
                 ("Set Z Score", 4, self.on_set_zscore),)
        

        for i in sorted(items, key=operator.itemgetter(0)):
            m_edit.add_command(label=i[0], underline=i[1], command=i[2])


        items = (("Notes", 0, self.on_export_notes),
                 ("Analytical Goals", 0, self.on_analitycal_goals),
                 ("Counts", 0, self.on_export_counts),)

        for i in items:
            m_exports.add_command(label=i[0], underline=i[1], command=i[2])


        items = (("Import", 4, self.on_import_results),)

        for i in items:
            m_imports.add_command(label=i[0], underline=i[1], command=i[2])

        items = (("User Manual", 0, self.on_user_manual),
                 ("QC Technical Manual", 0, self.on_qc_thecnical_manual),
                 ("Guidelines", 0, self.on_get_guidelines),
                 ("Biological Values", 0, self.on_bvv),)

        for i in items:
            m_documents.add_command(label=i[0], underline=i[1], command=i[2])

        items = (("Suppliers", 1, self.on_suppliers),
                 ("Sites", 1, self.on_sites),
                 ("Labs", 1, self.on_labs),
                 ("Sections", 1, self.on_sections),
                 ("Users", 0, self.on_users),
                 ("Tests", 0, self.on_tests),
                 ("Equipments", 0, self.on_equipments),
                 ("Categories", 1, self.on_categories),
                 ("Samples", 0, self.on_samples),
                 ("Units", 0, self.on_units),
                 ("Methods", 0, self.on_methods),
                ("Actions", 0, self.on_actions),)

        for i in sorted(items, key=operator.itemgetter(0)):
            m_adm.add_command(label=i[0], underline=i[1], command=i[2])

        m_about.add_command(label="About", underline=0, command=self.on_about)
        m_about.add_command(label="License", underline=0, command=self.on_license)
        m_about.add_command(label="Python", underline=0, command=self.on_python_version)
        m_about.add_command(label="Tkinter", underline=0, command=self.on_tkinter_version)

        for i in (m_main, m_file, ):
            i.config(bg=self.nametowidget(".").engine.get_rgb(240, 240, 237),)
            i.config(fg="black")

        self.config(menu=m_main)

        # Keyboard shortcuts for Change User/Section
        self.bind("<Control-u>", self.on_change_user)
        self.bind("<Control-e>", self.on_change_section)

    def init_ui(self) -> None:

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)

        frm_data = ttk.Frame(self.frm_main, style="App.TFrame")

        frm_lists = ttk.Frame(frm_data, style="App.TFrame")

        ttk.Label(frm_lists, text='Categories').pack(side=tk.TOP, fill=tk.X, expand=0)

        self.cbCategories = ttk.Combobox(frm_lists, style="App.TCombobox", state="readonly")
        self.cbCategories.bind("<<ComboboxSelected>>", self.on_selected_category)
        self.cbCategories.pack(side=tk.TOP, fill=tk.X, pady=5, expand=0)

        ttk.Label(frm_lists, text='Tests').pack(side=tk.TOP, fill=tk.X, expand=0)
        self.cbTests = ttk.Combobox(frm_lists, style="App.TCombobox")
        self.cbTests.bind("<<ComboboxSelected>>", self.on_selected_test)
        self.cbTests.pack(side=tk.TOP, fill=tk.X, pady=5, expand=0)

        w = ttk.LabelFrame(frm_lists, text='Workstation Data Source')
        self.lstWorkstations = self.nametowidget(".").engine.get_listbox(w, height=5, width=2, color="white")
        self.lstWorkstations.bind("<<ListboxSelect>>", self.on_selected_workstation)
        w.pack(side=tk.TOP, fill=tk.BOTH, expand=0)

        w = ttk.LabelFrame(frm_lists, text="Batches")
        self.lstBatches = self.nametowidget(".").engine.get_listbox(w, height=5, color="white")
        self.lstBatches.selectmode = tk.MULTIPLE
        self.lstBatches.bind("<<ListboxSelect>>", self.on_selected_batch)
        self.lstBatches.bind('<Double-Button-1>', self.on_batch_double_button)
        w.pack(side=tk.TOP, fill=tk.BOTH, expand=0)

        frm_stats = ttk.Frame(frm_lists, style="App.TFrame")

        w = tk.LabelFrame(frm_stats, text="Batch data", font="Helvetica 10 bold")

        ttk.Label(w, text="Target").pack()
        ttk.Label(w,
                  style="Target.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.target).pack(fill=tk.X, padx=2, pady=2)
        ttk.Label(w, text="SD").pack()
        ttk.Label(w,
                  style="black_and_withe.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.sd).pack(fill=tk.X, padx=2, pady=2)
        ttk.Label(w, text="TE%").pack()
        ttk.Label(w,
                  style="black_and_withe.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.te).pack(fill=tk.X, padx=2, pady=2)

        w.pack(side=tk.LEFT, fill=tk.X, expand=0)

        w = tk.LabelFrame(frm_stats, text="Cal data", font="Helvetica 10 bold")

        ttk.Label(w, text="Average").pack()
        ttk.Label(w,
                  style="Average.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.average).pack(fill=tk.X, padx=2, pady=2)
        ttk.Label(w, text="sd").pack()
        ttk.Label(w,
                  style="black_and_withe.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.calculated_sd).pack(fill=tk.X, padx=2, pady=2)
        ttk.Label(w, text="CV%").pack()
        ttk.Label(w,
                  style="black_and_withe.TLabel",
                  anchor=tk.CENTER,
                  textvariable=self.cva).pack(fill=tk.X, padx=2, pady=2)

        w.pack(side=tk.LEFT, fill=tk.X, expand=0)

        w = tk.LabelFrame(frm_stats, text="Other data", font="Helvetica 10 bold")

        ttk.Label(w, text="Westgard").pack()

        self.lblWestgard = ttk.Label(
            w,
            style="black_and_withe.TLabel",
            anchor=tk.CENTER,
            textvariable=self.westgard,
        )
        self.lblWestgard.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(w, text="U").pack()
        ttk.Label(
            w,
            style="black_and_withe.TLabel",
            anchor=tk.CENTER,
            textvariable=self.uncertainty,
        ).pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(w, text="Bias%").pack()
        ttk.Label(
            w,
            style="black_and_withe.TLabel",
            anchor=tk.CENTER,
            textvariable=self.bias,
        ).pack(fill=tk.X, padx=2, pady=2)


        w.pack(side=tk.RIGHT, fill=tk.X, expand=0)

        w = ttk.LabelFrame(frm_lists, text="Results")
        self.lstResults = self.nametowidget(".").engine.get_listbox(w, color="white")
        self.lstResults.bind("<<ListboxSelect>>", self.on_selected_result)
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

        # Bias chart sotto, più compatto
        self.bias_canvas = BiasCanvas(
            frm_graphs,
            bg="white",
            height=80,   # solo la riga riassuntiva
        )
        self.bias_canvas.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

        frm_data.pack(fill=tk.BOTH, expand=1)
        frm_lists.pack(side=tk.LEFT, fill=tk.Y, expand=0)
        frm_stats.pack(side=tk.LEFT, fill=tk.Y, expand=0)
        frm_graphs.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.frm_main.pack(fill=tk.BOTH, expand=1)

        d = self.nametowidget(".").engine.get_dimensions()
        window_width = int(d['w'])
        window_height = int(d['h'])

        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def init_status_bar(self) -> None:

        user = "{0} {1} on board {2}".format(self.nametowidget(".").engine.log_user["last_name"],
                                             self.nametowidget(".").engine.log_user["first_name"],
                                             self.nametowidget(".").engine.get_log_ip())

        msg = "Ready Player {0}".format(user)

        self.status_bar_text.set(msg)

        f = self.nametowidget(".").engine.set_font(family="TkDefaultFont", size=10, weight="bold")

        frm_status_bar = ttk.Frame(self.frm_main,  style="StatusBar.TFrame",)

        self.status = ttk.Label(frm_status_bar,
                                style="LoggedUser.TLabel",
                                textvariable=self.status_bar_text,
                                anchor=tk.W)

        ttk.Label(frm_status_bar, font=f,
                  textvariable=self.status_bar_site_description,
                  relief=tk.FLAT,
                  anchor=tk.W).pack(side=tk.RIGHT, fill=tk.X)
        ttk.Label(frm_status_bar, text="Site:").pack(side=tk.RIGHT, fill=tk.X)


        ttk.Label(frm_status_bar, font=f,
                  textvariable=self.observations,
                  relief=tk.FLAT,
                  anchor=tk.W).pack(side=tk.RIGHT, fill=tk.X)
        ttk.Label(frm_status_bar, text="Observations").pack(side=tk.RIGHT, fill=tk.X)


        ttk.Label(frm_status_bar, font=f,
                  textvariable=self.zscore,
                  relief=tk.FLAT,
                  anchor=tk.W).pack(side=tk.RIGHT, fill=tk.X)
        ttk.Label(frm_status_bar, text="Z Score").pack(side=tk.RIGHT, fill=tk.X)

        ttk.Checkbutton(frm_status_bar,
                        text='Delta Degree of Freedom',
                        onvalue=1,
                        offvalue=0,
                        variable=self.ddof,
                        command=self.on_ddof).pack(side=tk.RIGHT, fill=tk.X)


        self.status.pack(side=tk.LEFT, fill=tk.X, expand=1)

        frm_status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def on_open(self) -> None:
        #print(self.nametowidget(".").engine.current_ids)
        company = self.nametowidget(".").engine.get_company_data()
        if company:
            self.title(f"Biovarase {company['site']}")
        else:
            self.title("Biovarase")

        self.status_bar_site_description.set(self.get_status_bar_site_description(company))
        self.ddof.set(self.nametowidget(".").engine.get_ddof())
        self.observations.set(self.nametowidget(".").engine.get_observations())
        self.set_categories()
        self.set_zscore()

    def get_status_bar_site_description(self, company: dict) -> str:
        """
        Build a short label for the status bar using lab and section names.

        Args:
            company (dict): Dictionary returned by get_company_data(), e.g.
                            {
                                "site_id": 1,
                                "company": "Regione Lazio",
                                "site": "Ospedale Santo Preferito",
                                "lab": "Chimica Clinica",
                                "section": "Spettrometria"
                            }

        Returns:
            str: A short formatted string, max 80 chars, like
                 "Chimica Clinica - Ematologia"
        """
        if not company:
            return ""

        # Safely extract lab and section with defaults
        lab = company.get("lab", "")
        section = company.get("section", "")

        s = f"{lab} - {section}"
        return s[:80]

    def refresh_context_from_section(self):
        """Re-read section-dependent data and update title, status bar and lists."""
        company = self.nametowidget(".").engine.get_company_data()
        if company:
            self.title(f"Biovarase {company['site']}")
            self.status_bar_site_description.set(
                self.get_status_bar_site_description(company)
            )
        else:
            self.title("Biovarase")
            self.status_bar_site_description.set("")

        # 1) Close all untracked Toplevels
        self._close_untracked_windows()

        # 2) Notify tracked child windows that depend on section/lab
        tm = self.engine.dict_instances.get("test_methods")
        if tm and hasattr(tm, "refresh_context_from_section"):
            tm.refresh_context_from_section()

        # 3) Reset main's own section-dependent lists/filters
        try:
            self.on_reset()
            self.set_categories()
            # eventually: self.set_tests(), self.set_workstations(), ...
        except Exception as e:
            pass

    def _close_untracked_windows(self):
        """
        Close every Toplevel window that is not registered
        in engine.dict_instances.

        Assumption:
            dict_instances contains only windows that should survive
            context changes (e.g. login, main, test_methods, ...).
        """
        root = self.nametowidget(".")
        tracked = set(self.engine.dict_instances.values())

        for w in root.winfo_children():
            # Skip the root itself
            if not isinstance(w, tk.Toplevel):
                continue

            # If this Toplevel is not tracked, destroy it
            if w not in tracked:
                try:
                    w.destroy()
                except Exception as e:
                    pass


    def set_observations(self):
        self.observations.set(self.nametowidget(".").engine.get_observations())

    def set_zscore(self):
        self.zscore.set(self.nametowidget(".").engine.get_zscore())

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
            self.lstResults.delete(0, tk.END)

    def reset_batch_data(self) -> None:

        self.expiration.set('')
        self.target.set(0)
        self.sd.set(0)
        self.lstBatches.delete(0, tk.END)

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
            et = self.nametowidget(".").engine.get_te(
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
            engine = getattr(self, "engine", None) or self.nametowidget(".").engine
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
            self.lblWestgard.configure(style="black_and_withe.TLabel")
            self.westgard.set("No data")
            return

        if val == "Accept":
            style = "westgard_ok.TLabel"
        else:
            style = "westgard_violation.TLabel"

        self.lblWestgard.configure(style=style)


    def set_categories(self) -> None:

        self.selected_category = None
        self.dict_categories = {}
        voices = []
        index = 0

        # user: per section
        if self.nametowidget(".").engine.log_user["role"] == 2:

            sql = """
                    SELECT DISTINCT categories.category_id, 
                                    categories.description 
                    FROM test_methods 
                    INNER JOIN sections ON sections.section_id = test_methods.section_id 
                    INNER JOIN categories ON categories.category_id = test_methods.category_id
                    WHERE sections.section_id =? 
                    AND test_methods.status =1 
                    AND categories.status =1 
                    ORDER BY categories.description;
                """
            
            args = (self.nametowidget('.').engine.get_section_id(),)
            
        else:
            # admin/superuser: per lab

            sql = """
                    SELECT DISTINCT categories.category_id, 
                                    categories.description 
                    FROM test_methods 
                    INNER JOIN sections ON sections.section_id = test_methods.section_id 
                    INNER JOIN categories ON categories.category_id = test_methods.category_id 
                    WHERE sections.lab_id =? 
                    AND test_methods.status =1 
                    AND categories.status =1 
                    ORDER BY categories.description;
                """
        
            args = (self.nametowidget(".").engine.get_lab_id(),)
            
        rs = self.nametowidget(".").engine.read(True, sql, args)

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
        
        sql = """
              SELECT test_methods.test_method_id,
                     tests.description
              FROM test_methods
              JOIN tests ON tests.test_id = test_methods.test_id
              WHERE test_methods.category_id = ?
              AND test_methods.section_id = ?
              AND tests.status = 1
              AND test_methods.status = 1
              ORDER BY tests.description;
              """

        args = (category_id,
                self.nametowidget(".").engine.get_section_id())

        rs = self.nametowidget(".").engine.read(True, sql, args)
        if rs:
            for row in rs:
                self.test_methods[index] = row["test_method_id"]
                voices.append(row["description"])
                index += 1

        self.cbTests["values"] = voices
        self.reset_batch_data()

    def set_workstations(self) -> None:
        """Fill workstations listbox for selected test method."""
        self.lstWorkstations.delete(0, tk.END)
        self.selected_workstation = None
        self.workstation_test_methods = {}
        index = 0

        if self.cbTests.current() == -1:
            return

        if not self.selected_test_method:
            return
        
        sql = """
                SELECT workstations.workstation_id, 
                       workstations.description, 
                       workstations.serial 
                FROM workstation_test_methods 
                JOIN workstations 
                  ON workstation_test_methods.workstation_id = workstations.workstation_id 
                WHERE workstation_test_methods.test_method_id = ? 
                  AND workstations.section_id = ? 
                  AND workstations.status = 1 
                ORDER BY workstations.rank ASC;
             """

        args = (self.selected_test_method["test_method_id"],
                    self.nametowidget(".").engine.get_section_id())

        rs = self.nametowidget(".").engine.read(True, sql, args)

        if rs:
            for row in rs:
                text = f"{row['description']:<15} {row['serial']:>18}"
                self.lstWorkstations.insert(tk.END, text)
                self.workstation_test_methods[index] = row["workstation_id"]
                index += 1

            self.reset_batch_data()
            self.lstWorkstations.select_set(0)
            self.lstWorkstations.event_generate("<<ListboxSelect>>")

    def set_batches(self) -> None:
        """Fill batches listbox for selected test method and workstation."""
        self.lstBatches.delete(0, tk.END)
        self.dict_batches = {}
        index = 0

        if self.cbTests.current() == -1 or not self.lstWorkstations.curselection():
            self.reset_cal_data()
            self.reset_graph()
            return

        if not (self.selected_test_method and self.selected_workstation):
            self.reset_cal_data()
            self.reset_graph()
            return

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
            ORDER BY batches.rank ASC;
        """

        args = (
            self.selected_test_method["test_method_id"],
            self.selected_workstation["workstation_id"],
        )

        rs = self.nametowidget(".").engine.read(True, sql, args)

        if rs:
            for row in rs:
                x = self.engine.get_expiration_date(row["expiration_str"])
                label = "{0:<2}  {1:<8}  {2:<10}".format(
                    row["description"], row["lot_number"], row["expiration_str"]
                )
                self.lstBatches.insert(tk.END, label[:25])

                if x <= 0:
                    self.lstBatches.itemconfig(index, {"bg": "red"})
                elif x <= 15:
                    self.lstBatches.itemconfig(index, {"bg": "yellow"})

                self.dict_batches[index] = row["batch_id"]
                index += 1

            self.lstBatches.select_set(0)
            self.lstBatches.event_generate("<<ListboxSelect>>")
        else:
            self.reset_cal_data()
            self.reset_graph()

    def set_results(self) -> None:
        """Fill results listbox for selected batch and workstation."""
        self.lstResults.delete(0, tk.END)
        self.dict_results = {}

        if not (self.selected_batch and self.selected_workstation):
            self.reset_cal_data()
            self.reset_graph()
            return

        try:
             target = float(self.selected_batch.get("target", 0.0))
        except Exception as e:
            target = 0.0
        try:
            sd = float(self.selected_batch.get("sd", 0.0))
        except Exception as e:
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

        rs = self.nametowidget(".").engine.read(True, sql, args)

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


        index = 0
        for row in rs:
            base_text = "{0:10}{1:12}".format(row["received_str"], row["result_rounded"])

            has_notes = notes_map.get(row["result_id"], 0) > 0
            # Aggiungo un marcatore visivo nel testo, ad es. un asterisco iniziale
            text = f"* {base_text}" if has_notes else base_text

            self.lstResults.insert(tk.END, text)

            result_val = float(row["result_rounded"])
            is_enabled = row["status"]
            self.set_results_row_color(index, result_val, is_enabled, target, sd)

            # Se ci sono note, evidenzio anche lo sfondo della riga
            if has_notes:
                try:
                    self.lstResults.itemconfig(index, {"background": "#fff2cc"})  # giallino
                except Exception as e:
                    pass

            self.dict_results[index] = row["result_id"]
            index += 1

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
        self.lstWorkstations.delete(0, tk.END)

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
            self.lstWorkstations.delete(0, tk.END)
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
        if not self.lstWorkstations.curselection():
            self.selected_workstation = None
            self.reset_batch_data()
            return

        index = self.lstWorkstations.curselection()[0]
        pk = self.workstation_test_methods.get(index)
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
        if not self.lstBatches.curselection():
            self.selected_batch = None
            self.reset_cal_data()
            self.reset_graph()
            return

        index = self.lstBatches.curselection()[0]
        pk = self.dict_batches.get(index)
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
        if not self.lstResults.curselection():
            self.selected_result = None
            return

        index = self.lstResults.curselection()[0]
        pk = self.dict_results.get(index)
        if pk is None:
            self.selected_result = None
            return

        self.selected_result = self.engine.get_selected("results", "result_id", pk)
        #print(self.selected_result)

    def _open_result_editor_for_list_index(self, index: int) -> None:
        """Open result editor in update mode for the given listbox index."""
        try:
            # --- Build dictionaries required by result.py ---------------------
            result_id = self.dict_results.get(index)
            if result_id is None:
                messagebox.showerror(
                    self.engine.app_title,
                    "Result not found. Cannot edit.",
                    parent=self,
                )
                return

            self.selected_result = self.engine.get_selected("results", "result_id", result_id)

            if not self.selected_result:
                messagebox.showerror(
                    self.engine.app_title,
                    "Result not found. Cannot edit.",
                    parent=self,
                )
                return

            # Get selected batch.
            batch_id = self.selected_result["batch_id"]
            self.selected_batch = self.engine.get_selected("batches", "batch_id", batch_id)

            if not self.selected_batch:
                messagebox.showerror(
                    self.engine.app_title,
                    "Batch not found. Cannot edit result.",
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
                    "Test method not found. Cannot edit result.",
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

            frames.result.UI(self, index).on_open()

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )


    def set_results_row_color(self, index, result, is_enabled, target, sd):
        """Set color of a result row according to Westgard thresholds."""
        try:
            if not is_enabled:
                self.lstResults.itemconfig(index, {"fg": "gray"})
                return

            # 1s, 2s, 3s etc. (simple thresholds)
            if sd and abs(result - target) > 3 * sd:
                color = "red"
            elif sd and abs(result - target) > 2 * sd:
                color = "orange"
            else:
                color = "black"

            self.lstResults.itemconfig(index, {"fg": color})
        except Exception as e:
            pass

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

            # Find corresponding listbox index
            list_index = None
            for k, rid in self.dict_results.items():
                if rid == result_id:
                    list_index = k
                    break

            if list_index is None:
                messagebox.showerror(
                    self.engine.app_title,
                    "Result not found in list. Cannot edit.",
                    parent=self,
                )
                return

            # Sync selection in the listbox
            self.lstResults.selection_clear(0, tk.END)
            self.lstResults.selection_set(list_index)
            self.lstResults.activate(list_index)
            self.lstResults.see(list_index)

            # Open editor
            self._open_result_editor_for_list_index(list_index)

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
                show_values=True,        # valori solo sui punti anomali, come abbiamo settato
                bottom_text=bottom_text,  # 👈 qui passa la stringa
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

        # Title: test + (eventuale) controllo/lotto
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
                "Access Denied",
                self.engine.user_not_enable
            )
            return
        
        frames.daily_validation.UI(self).on_open()

    def on_tests(self) -> None:
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.tests.UI(self).on_open()

    def on_test_methods(self) -> None:
        """Open Test Methods window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.test_methods.UI(self).on_open()

    def on_workstation_test_methods(self):
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.workstation_test_methods.UI(self).on_open()

    def on_categories(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.categories.UI(self).on_open()

    def on_samples(self,):
        if not self.engine.is_admin():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.samples.UI(self).on_open()

    def on_units(self,):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.units.UI(self).on_open()

    def on_methods(self,):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.methods.UI(self).on_open()

    def on_controls(self,):
        """Open Controls window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.controls.UI(self).on_open()

    def on_equipments(self):

        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)

        else:
            frames.equipments.UI(self).on_open()

    def on_workstations(self,):
        """Open Workstations window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.workstations.UI(self).on_open()

    def on_suppliers(self,):

        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
        else:
            frames.suppliers.UI(self).on_open()

    def on_labs(self):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.labs.UI(self).on_open()

    def on_sites(self,):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.sites.UI(self).on_open()

    def on_sections(self,):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.sections.UI(self).on_open()

    def on_observations(self,):
        frames.observations.UI(self).on_open()
        
    def on_analitical(self,):
        frames.analytical.UI(self).on_open()

    def on_set_zscore(self,):
        frames.set_zscore.UI(self).on_open()

    def on_batches(self) -> None:
        """Open Batches window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        frames.batches.UI(self).on_open()

    def on_actions(self,):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.actions.UI(self).on_open()

    def on_users(self,):
        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return
        
        frames.users.UI(self).on_open()

    def on_zscore(self,):
        frames.zscore.UI(self,)

    def on_plots(self,):

        if self.cbTests.current() != -1:

            if self.lstBatches.curselection():

                index = self.cbTests.current()
                pk = self.test_methods[index]
                selected_test_method = self.nametowidget(".").engine.get_selected("test_methods", "test_method_id", pk)
                frames.plots.UI(self,).on_open(selected_test_method,
                                               self.selected_workstation,
                                               int(self.observations.get()))
            else:
                msg = "Not enough data to plot.\nSelect an instrument and a batch."
                messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
        else:
            msg = "Not enough data to plot.\nSelect a test."
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            
    def on_tea(self):
        """
        Open TEA window if:
          - a test is selected
          - a batch is selected
          - the test has goals with to_export = 1
        """

        if self.cbTests.current() == -1:
            messagebox.showwarning(self.nametowidget(".").title(),
                                   "Not enough data to plot.\nSelect a test.",
                                   parent=self)
            return

        if not self.lstBatches.curselection():
            messagebox.showwarning(self.nametowidget(".").title(),
                                   "Not enough data to plot.\nSelect a batch.",
                                   parent=self)
            return

        index = self.cbTests.current()
        pk = self.test_methods[index]

        # Get full test_method + goals structure
        selected = self.nametowidget(".").engine.get_test_method_with_goals(pk)

        if not selected:
            messagebox.showwarning(self.nametowidget(".").title(),
                                   "Test method not found.",
                                   parent=self)
            return

        # Check if TEA is enabled (to_export == 1)
        if selected.get("to_export", 0) != 1:
            messagebox.showwarning(self.nametowidget(".").title(),
                                   "Selected test is not enabled for this plot type.",
                                   parent=self)
            return

        # Everything OK → open TEA
        frames.tea.UI(self).on_open(
            selected,                       # unified dict
            self.selected_workstation,
            int(self.observations.get())
        )


    def on_youden(self,):
        """Open Youden plot window for two selected batches."""

        engine = self.nametowidget(".").engine

        # A test must be selected
        if self.cbTests.current() == -1:
            msg = "Not enough data to plot.\nSelect a test."
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        # Two batches must be selected
        items = self.lstBatches.curselection()
        if not items:
            msg = (
                "Not enough data to plot a Youden chart.\n"
                "You need to select two batches."
            )
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        if len(items) != 2:
            msg = (
                "Youden plot requires exactly two batches.\n"
                "Please select only two batches."
            )
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        # Selected test method
        index = self.cbTests.current()
        pk_test_method = self.test_methods[index]
        selected_test_method = engine.get_selected(
            "test_methods",
            "test_method_id",
            pk_test_method,
        )

        # Resolve selected batches
        pks = []
        batches = []
        for list_index in items:
            batch_pk = self.dict_batches.get(list_index)
            if batch_pk is not None:
                pks.append(batch_pk)

        for batch_pk in pks:
            batch = engine.get_selected("batches", "batch_id", batch_pk)
            batches.append(batch)

        # Get series for each batch
        data = []
        observations = int(engine.get_observations())
        for batch in batches:
            series = engine.get_series(
                batch["batch_id"],
                self.selected_workstation["workstation_id"],
                observations,
            )
            data.append(series)

        # Both batches must have at least one result
        if not data[0] or not data[1]:
            msg = (
                "Not enough data to plot a Youden chart.\n"
                "Both selected batches must have at least one result."
            )
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        # Even if lengths are different, youden.py will use min(len(L1), len(L2))
        frames.youden.UI(self).on_open(
            selected_test_method,
            self.selected_workstation,
            batches,
            data,
        )

    def on_export_notes(self) -> None:
        frames.export_notes.UI(self).on_open()

    # Quick Data Analysis removed - functionality integrated into Daily Validation
    # def on_quick_data_analysis(self,):
    #     frames.quick_data_analysis.UI(self).on_open()

    def on_analitycal_goals(self,):
        frames.analitycal_goals.UI(self).on_open()

    def on_export_counts(self) -> None:
        frames.counts.UI(self).on_open()

    def on_ddof(self,):

        if self.ddof.get() == True:
            self.nametowidget(".").engine.set_ddof(1)
        else:
            self.nametowidget(".").engine.set_ddof(0)

        self.ddof.set(self.nametowidget(".").engine.get_ddof())

        try:
            self.set_results()
        except AttributeError:
            msg = "Attention please.\nNo batch selected."
            messagebox.showinfo(self.nametowidget(".").title(), msg, parent=self)


    def on_insert_demo_result(self, evt: Optional[tk.Event] = None) -> None:

        if not self.nametowidget(".").engine.is_admin():
            msg = self.nametowidget(".").engine.user_not_enable
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
            return

        if self.lstBatches.curselection():

            msg = "Insert 30 random results for:\n{0}\nbatch {1} {2}?".format(
                self.selected_test["description"],
                self.selected_batch["lot_number"],
                self.selected_batch["description"]
            )

            if messagebox.askyesno(self.nametowidget(".").title(),
                                   msg,
                                   parent=self) == True:


                try:
                    cur = self.nametowidget(".").engine.con.cursor()
                    # Begin transaction
                    cur.execute("START TRANSACTION")  # Usare START TRANSACTION per maggiore compatibilità MariaDB

                    sql_delete = "DELETE FROM results WHERE batch_id =? AND workstation_id =?;"
                    args = (self.selected_batch["batch_id"], self.selected_workstation["workstation_id"])
                    cur.execute(sql_delete, args)

                    min_val = round((self.selected_batch["target"] - self.selected_batch["sd"]), 2)
                    max_val = round((self.selected_batch["target"] + self.selected_batch["sd"]), 2)
                                                                                        
                    sql_insert = "INSERT INTO results(batch_id, workstation_id, result, received, log_time, log_id) VALUES(?,?,?,?,?,?)"
                    log_time = self.nametowidget(".").engine.get_log_time()

                    # Prepare data for executemany()
                    data_to_insert = []
                    current_log_time = log_time  # Initialize outside the loop
                    for _ in range(0, 30):
                        result = random.uniform(min_val, max_val)
                        data_to_insert.append((
                            self.selected_batch["batch_id"],
                            self.selected_workstation["workstation_id"],
                            round(result, 2),
                            current_log_time,
                            current_log_time,
                            self.nametowidget(".").engine.log_user["user_id"]
                        ))
                        # Assicurati che current_log_time sia un oggetto datetime per l'incremento
                        if isinstance(current_log_time, str):
                            try:
                                current_log_time = datetime.datetime.strptime(current_log_time, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                # Gestisci l'errore se il formato della stringa non è corretto
                                self.nametowidget(".").engine.on_log(inspect.stack()[0][3],
                                                                       "Errore nel formato della data/ora",
                                                                       ValueError,
                                                                       sys.modules[__name__])
                                cur.rollback()
                                return  # Interrompi l'operazione in caso di errore
                        current_log_time += datetime.timedelta(days=1)

                    cur.executemany(sql_insert, data_to_insert)  # Use executemany()

                    self.nametowidget(".").engine.con.commit()  # Commit the transaction
                    self.set_results()
                except Exception as e:  # Cattura un'eccezione più generica per il rollback
                    self.nametowidget(".").engine.con.rollback()  # Rollback on any error
                    self.nametowidget(".").engine.on_log(inspect.stack()[0][3],
                                                           str(e),
                                                           sys.exc_info()[0],
                                                           sys.modules[__name__])
                finally:
                    if 'cur' in locals() and cur:  # Verifica se il cursore è stato creato prima di chiuderlo
                        cur.close()

        else:
            msg = "Attention please.\nBefore add 30 random results you must select a batch."
            messagebox.showinfo(self.nametowidget(".").title(), msg, parent=self)


    def on_batch_double_button(self, evt: Optional[tk.Event] = None) -> None:

        if self.lstBatches.curselection():
            self.on_add_result()
        else:
            msg = "Attention please.\nSelect a batch."
            messagebox.showinfo(self.nametowidget(".").title(), msg, parent=self)


    def on_add_result(self):
        """Open result editor in insert mode for current batch and workstation."""
        # Check read-only mode (block autologin users)
        if self.engine.is_read_only():
            msg = "Read-only mode.\nCannot add results."
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        if not self.lstBatches.curselection():
            msg = (
                "Attention please.\nBefore adding a result you must select a batch."
            )
            messagebox.showinfo(self.nametowidget(".").title(), msg, parent=self)
            return


        batch_index = self.lstBatches.curselection()[0]
        batch_id = self.dict_batches[batch_index]
        self.selected_batch = self.engine.get_selected("batches", "batch_id", batch_id)

        if not self.selected_batch:
            messagebox.showerror(
                self.engine.app_title,
                "Batch not found. Cannot add result.",
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
                "Test method not found. Cannot edit result.",
                parent=self,
            )
            return

        test_id = self.selected_test_method["test_id"]
        self.selected_test = self.engine.get_selected("tests", "test_id", test_id)

        workstation_id = self.selected_batch["workstation_id"]
        self.selected_workstation = self.engine.get_selected("workstations", "workstation_id", workstation_id)

        frames.result.UI(self).on_open()


    def on_update_result(self, evt: Optional[tk.Event] = None) -> None:
        """Default double–click on results list: open notes editor."""
        try:
            # Check read-only mode (block autologin users)
            if self.engine.is_read_only():
                msg = "Read-only mode.\nCannot edit notes."
                messagebox.showwarning(self.engine.app_title, msg, parent=self)
                return

            if not self.lstResults.curselection():
                msg = "Attention please.\nSelect a result."
                messagebox.showinfo(self.nametowidget(".").title(), msg, parent=self)
                return

            frames.notes.UI(self).on_open()

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )

    def on_bvv(self) -> None:

        engine = self.nametowidget(".").engine
        engine.busy(self)

        try:
            filename = engine.get_bvv()
            path = engine.get_file(os.path.join("documents", filename))
            ret = engine.launch(path)
        finally:
            engine.not_busy(self)

        if not ret:
            messagebox.showinfo(
                self.nametowidget(".").title(),
                "The file Biological Variation Values does not exist or cannot be opened.",
                parent=self
            )

    def on_user_manual(self) -> None:

        engine = self.nametowidget(".").engine
        engine.busy(self)

        try:
            filename = engine.get_user_manual()
            path = engine.get_file(os.path.join("documents", filename))
            ret = engine.launch(path)
        finally:
            engine.not_busy(self)

        if not ret:
            messagebox.showinfo(
                self.nametowidget(".").title(),
                "The Biovarase User Manual does not exist or cannot be opened.",
                parent=self,
            )


    def on_qc_thecnical_manual(self) -> None:

        engine = self.nametowidget(".").engine

        engine.busy(self)

        file = engine.get_qc_thecnical_manual()
        path = engine.get_file(os.path.join("documents", file))

        ret = engine.launch(path)

        engine.not_busy(self)

        if not ret:
            messagebox.showinfo(
                self.nametowidget(".").title(),
                "The QC Technical Manual does not exist or cannot be opened.",
                parent=self,
            )

    def on_get_guidelines(self) -> None:

        engine = self.nametowidget(".").engine

        engine.busy(self)

        file = engine.get_guidelines()
        path = engine.get_file(os.path.join("documents", file))

        ret = engine.launch(path)

        engine.not_busy(self)

        if not ret:
            messagebox.showinfo(
                self.nametowidget(".").title(),
                "The Biovarase Guidelines file does not exist or cannot be opened.",
                parent=self,
            )

    def on_license(self) -> None:
        frames.license.UI(self).on_open()

    def on_python_version(self) -> None:
        s = self.nametowidget(".").engine.get_python_version()
        messagebox.showinfo(self.nametowidget(".").title(), s, parent=self)

    def on_tkinter_version(self) -> None:
        s = "Tkinter patchlevel\n{0}".format(self.nametowidget(".").tk.call("info", "patchlevel"))
        messagebox.showinfo(self.nametowidget(".").title(), s, parent=self)

    def on_about(self) -> None:
        messagebox.showinfo(self.nametowidget(".").title(),
                            self.nametowidget(".").info,
                            parent=self)

    def on_change_password(self) -> None:
        frames.change_password.UI(self, ).on_open()

    def on_log(self,):
        self.nametowidget(".").engine.get_log_file()

    def on_import_results(self) -> None:
        """Open Import Results window (Admin/Superuser only)."""
        if not self.engine.can_validate_qc():
            msg = self.engine.user_not_enable
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return

        frames.importer.UI(self, ).on_open()
   

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
        msg = "Logout and switch to different user?\n\nAll open windows will be closed."
        if not messagebox.askyesno("Change User", msg, parent=self, icon="question"):
            return
        
        try:
            # Close all windows except main
            self.engine.close_all_windows_except_main()
            
            # Reset user context
            self.engine.log_user.clear()
            
            # Show login dialog
            login_window = frames.login.Login(self)
            
            # Wait for login to complete
            self.wait_window(login_window)
            
            # Check if login was successful
            if self.engine.log_user.get("user_id"):
                # Login successful - reload main window
                self.on_open()
                
                # Welcome message
                first = self.engine.log_user.get("first_name", "")
                last = self.engine.log_user.get("last_name", "")
                user_name = f"{first} {last}".strip()
                messagebox.showinfo(
                    "Welcome",
                    f"Logged in as: {user_name}",
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
            messagebox.showerror("Error", f"Failed to change user: {exc}", parent=self)

    def on_change_section(self, _evt=None):
        """
        Change Section - Switch to different section without logout.
        
        Permission:
        - Admin (role=0): Can change to any section
        - Superuser (role=1): Can change to sections in their lab
        - Technician (role=2): Can change to sections in their lab
        - Autologin (role=3): BLOCKED (read-only users)
        
        Workflow:
        1. Check permissions
        2. Fetch available sections based on role
        3. Show selection dialog
        4. Update section_id
        5. Close section-dependent windows
        6. Reload main window
        
        Args:
            _evt: Optional Tkinter event (for keyboard shortcut)
        """
        role = self.engine.get_user_role()
        
        # Permission check - only autologin (role=3) is blocked
        if role == 3:
            messagebox.showwarning(
                "Permission Denied",
                "Read-only users cannot change section.",
                parent=self
            )
            return
        
        try:
            # Fetch available sections based on role
            if role == 0:
                # Admin: all active sections
                sql = """
                    SELECT section_id, description
                    FROM sections
                    WHERE status = 1
                    ORDER BY description
                """
                args = ()
            else:
                # Superuser/Technician: only sections in their lab
                lab_id = self.engine.current_ids.get("lab_id")
                sql = """
                    SELECT section_id, description
                    FROM sections
                    WHERE lab_id = ? AND status = 1
                    ORDER BY description
                """
                args = (lab_id,)
            
            sections = self.engine.read(True, sql, args)
            
            if not sections:
                messagebox.showwarning(
                    "No Sections",
                    "No sections available for selection.",
                    parent=self
                )
                return
            
            # Create selection dialog
            dialog = tk.Toplevel(self)
            dialog.title("Change Section")
            dialog.geometry("400x300")
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            
            # Center dialog
            dialog.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
            y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
            # Label
            tk.Label(
                dialog,
                text="Select new section:",
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
            
            # Populate listbox
            dict_sections = {}
            current_section_id = self.engine.get_section_id()
            
            for idx, section in enumerate(sections):
                section_id = section["section_id"]
                description = section["description"]
                dict_sections[idx] = section_id
                
                display = f"{description}"
                listbox.insert(tk.END, display)
                
                # Highlight current section
                if section_id == current_section_id:
                    listbox.selection_set(idx)
                    listbox.see(idx)
            
            # Result variable
            selected_section_id = [None]
            
            def on_select():
                """Handle selection."""
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a section.", parent=dialog)
                    return
                
                idx = selection[0]
                selected_section_id[0] = dict_sections[idx]
                dialog.destroy()
            
            def on_cancel():
                """Handle cancel."""
                dialog.destroy()
            
            # Buttons
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=10)
            
            tk.Button(
                btn_frame,
                text="OK",
                width=10,
                command=on_select
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                btn_frame,
                text="Cancel",
                width=10,
                command=on_cancel
            ).pack(side=tk.LEFT, padx=5)
            
            # Double-click to select
            listbox.bind("<Double-Button-1>", lambda e: on_select())
            
            # Wait for dialog to close
            self.wait_window(dialog)
            
            # Check if section was selected
            if selected_section_id[0] is None:
                return  # User canceled
            
            new_section_id = selected_section_id[0]
            
            # Check if same section
            if new_section_id == current_section_id:
                messagebox.showinfo("Same Section", "Already in this section.", parent=self)
                return
            
            # Update section_id
            self.engine.set_section_id(new_section_id)
            self.engine.current_ids["section_id"] = new_section_id
            
            # Close section-dependent windows
            self.engine.close_unregistered_toplevels(self)
            
            # Reload main window
            self.on_open()
            
            # Get section name for confirmation
            section_name = next(
                (s["description"] for s in sections if s["section_id"] == new_section_id),
                f"Section {new_section_id}"
            )
            
            # Confirmation message
            messagebox.showinfo(
                "Section Changed",
                f"Now working in: {section_name}",
                parent=self
            )
            
        except Exception as exc:
            # Log error
            self.engine.on_log(
                "on_change_section",
                str(exc),
                type(exc).__name__,
                sys.modules[__name__],
                inspect.currentframe()
            )
            messagebox.showerror("Error", f"Failed to change section: {exc}", parent=self)

    def on_close(self) -> None:
        self.nametowidget(".").engine.dict_instances.pop(self.winfo_name(), None)
        self.nametowidget(".").on_exit()