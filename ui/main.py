# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The main window: a category, a test, an instrument, a lot, and the chart.

The left column narrows the question one step at a time - the panel of
analytes, the analyte, the instrument it is measured on, the lot of control
material open on it - and what comes out is a series: the statistics of it in
the three boxes, the results under them, and the chart filling the right.

That is how the work is done at the bench: I am looking at the quality
control of the antiepileptics this morning.
"""

import os
import tempfile
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import ui.about
import ui.actions
import ui.licence
import ui.batches
import ui.bland_altman
import ui.categories
import ui.change_password
import ui.controls
import ui.equipments
import ui.export_day
import ui.methods
import ui.note
import ui.notes
import ui.performance_dashboard
import ui.plots
import ui.result
import ui.samples
import ui.settings
import ui.since
import ui.statistics
import ui.suppliers
import ui.tea
import ui.test_methods
import ui.tests
import ui.units
import ui.users
import ui.workstations
import ui.youden

from bias_canvas import BiasCanvas
from ljcanvas import LeveyJenningsCanvas
from ui.window import Window

#: The biological variation the analytical goals are computed from: the
#: EFLM keeps it, updates it, and says how each estimate was graded. The
#: formulae that use it are in documents/ANALYTICAL_GOALS.md.
BIOLOGICAL_VARIATION = "https://biologicalvariation.eu/"

#: Nordtest TR 569, the Trollbook: how to plan and run internal quality
#: control, from the control material to the chart, written for analysts
#: rather than for statisticians. Free to read, and not ours to ship.
HANDBOOK = ("https://www.nordtest.info/wp/2026/03/18/internal-quality-control"
            "-handbook-for-chemical-laboratories-trollboken-troll-book-nt-tr-569"
            "-english-edition-6/")

#: The columns of each list, as Tools.get_tree wants them:
#: (identifier, heading, anchor, stretch, minwidth, width).
BATCHES = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Liv", tk.W, False, 30, 45),
           ("#2", "Lot", tk.W, True, 80, 100),
           ("#3", "Expiration", tk.W, False, 70, 90))

RESULTS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Date", tk.W, True, 120, 145),
           ("#2", "Value", tk.CENTER, False, 55, 70))


class Main(Window, ttk.Frame):
    """A category, a test, an instrument, a lot: the chart of that series."""

    #: The statistics, in the three boxes they are read in: what the lot says
    #: it is, what this laboratory got, and how the two compare.
    STATISTICS = (("Lot", (("target", "Target"),
                           ("sd", "SD"),
                           ("tea", "TEa%"))),
                  ("Series", (("n", "N"),
                              ("mean", "Mean"),
                              ("cv_sd", "sd"),
                              ("cv", "CV%"))),
                  ("Performance", (("bias", "Bias%"),
                                   ("te", "TE%"),
                                   ("u", "U%"),
                                   ("westgard", "Westgard"))))

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        #: position in a combo or a list -> primary key
        self.dict_categories = {}
        self.dict_tests = {}
        self.dict_workstations = {}
        self.dict_batches = {}
        self.dict_results = {}
        #: what is chosen now
        self.test_method = None
        self.workstation = None
        self.batch = None
        self.analyte = ""
        self.unit = ""
        #: which result each point of the chart stands for, by position
        self.chart_results = []

        self.status = tk.StringVar()
        #: How far back this window looks, from the settings: the menu writes
        #: it back, so the program opens where it was left.
        code, self.since = self.engine.get_period()
        self.period = tk.StringVar(value=code)
        self.values = {name: tk.StringVar()
                       for caption, cells in self.STATISTICS
                       for name, label in cells}

        self.init_menu()
        self.init_ui()
        # A window that is told about changes after it is gone raises from
        # inside the callback of whoever saved. <Destroy> arrives however
        # this window ends - a change of user, the application closing - so
        # the register of listeners cannot be left holding a dead window.
        self.bind("<Destroy>", self.on_destroy, add="+")
        # The master data this window shows can be changed while it is open,
        # from the Edit menu: an analyte disabled, a category renamed, an
        # instrument taken out of service. The lists are read again when it
        # happens, or they keep offering a choice that no longer exists.
        self.engine.events.subscribe("results", self.on_results_changed)
        self.engine.events.subscribe("notes", self.on_results_changed)
        self.engine.events.subscribe("batches", self.on_batches_changed)
        self.engine.events.subscribe("categories", self.on_master_data_changed)
        self.engine.events.subscribe("tests", self.on_master_data_changed)
        self.engine.events.subscribe("test_methods", self.on_master_data_changed)
        self.engine.events.subscribe("workstations", self.on_master_data_changed)

    # ------------------------------------------------------------- the menu

    def init_menu(self):
        """The menu bar: what can be opened, and who may open it."""
        bar = tk.Menu(self.parent)

        m_file = tk.Menu(bar, tearoff=0)

        m_database = tk.Menu(m_file, tearoff=0)
        m_database.add_command(label="Backup", underline=0, command=self.on_backup)
        m_database.add_command(label="Dump as SQL", underline=0, command=self.on_dump)
        m_database.add_separator()
        m_database.add_command(label="Check", underline=0, command=self.on_check)
        m_database.add_command(label="Vacuum", underline=0, command=self.on_vacuum)
        m_file.add_cascade(label="Database", underline=0, menu=m_database)

        m_file.add_separator()
        m_file.add_command(label="Log", underline=0, command=self.engine.open_log)
        m_file.add_separator()
        m_file.add_command(label="Settings", underline=0, command=self.on_settings)
        m_file.add_command(label="Change password", underline=7,
                           command=self.on_change_password)
        m_file.add_command(label="Exit", underline=1, command=self.parent.on_exit)
        bar.add_cascade(label="File", underline=0, menu=m_file)

        m_qc = tk.Menu(bar, tearoff=0)
        m_qc.add_command(label="Levey-Jennings", underline=0, command=self.on_plots)
        m_qc.add_command(label="Statistics", underline=0, command=self.on_statistics)
        m_qc.add_command(label="Total error", underline=0, command=self.on_tea)
        m_qc.add_command(label="Bland-Altman", underline=0, command=self.on_bland_altman)
        m_qc.add_command(label="Youden", underline=0, command=self.on_youden)
        m_qc.add_separator()
        m_qc.add_command(label="Performance", underline=0,
                         command=self.on_performance)
        m_qc.add_command(label="Notes", underline=1, command=self.on_notes)
        m_qc.add_command(label="Batches", underline=0, command=self.on_batches)
        m_qc.add_separator()
        m_qc.add_command(label="Add result", underline=0, command=self.on_add_result)
        m_qc.add_command(label="Edit result", underline=0, command=self.on_edit_result)
        m_qc.add_command(label="Note", underline=0, command=self.on_note)
        bar.add_cascade(label="QC", underline=0, menu=m_qc)

        # The master data: an administrator keeps it, everybody reads it.
        if self.engine.is_admin():
            m_edit = tk.Menu(bar, tearoff=0)
            for label, module in (("Analytes", ui.tests),
                                  ("Categories", ui.categories),
                                  ("Controls", ui.controls),
                                  ("Corrective actions", ui.actions),
                                  ("Instruments", ui.workstations),
                                  ("Methods", ui.methods),
                                  ("Models", ui.equipments),
                                  ("Samples", ui.samples),
                                  ("Test methods", ui.test_methods),
                                  ("Suppliers", ui.suppliers),
                                  ("Units", ui.units),
                                  ("Users", ui.users)):
                m_edit.add_command(label=label,
                                   command=lambda m=module: self.on_master_data(m))
            bar.add_cascade(label="Edit", underline=0, menu=m_edit)

        m_period = tk.Menu(bar, tearoff=0)
        for code, label in self.PERIODS:
            if code is None:
                m_period.add_separator()
            else:
                m_period.add_radiobutton(label=label, value=code,
                                         variable=self.period,
                                         command=self.on_period)
        bar.add_cascade(label="Period", underline=0, menu=m_period)

        m_exports = tk.Menu(bar, tearoff=0)
        m_exports.add_command(label="Controls of a day", underline=0,
                              command=self.on_export_day)
        m_exports.add_separator()
        m_exports.add_command(label="Notes", underline=0, command=self.on_export_notes)
        m_exports.add_command(label="Counts", underline=0, command=self.on_export_counts)
        m_exports.add_command(label="Analytical goals", underline=0,
                              command=self.on_export_goals)
        bar.add_cascade(label="Exports", underline=1, menu=m_exports)

        m_help = tk.Menu(bar, tearoff=0)
        m_help.add_command(label="User manual", underline=0, command=self.on_manual)
        m_help.add_separator()
        m_help.add_command(label="Biological variation database", underline=0,
                           command=self.on_biological_variation)
        m_help.add_command(label="Internal quality control handbook", underline=0,
                           command=self.on_handbook)
        m_help.add_separator()
        m_help.add_command(label="About", underline=0, command=self.on_about)
        m_help.add_command(label="Licence", underline=0, command=self.on_licence)
        bar.add_cascade(label="?", menu=m_help)

        self.parent.config(menu=bar)

    def on_export_day(self, evt=None):
        """The controls of a day, as a sheet: what was run and how it came out."""
        self.engine.windows.replace("export_day",
                                    lambda: ui.export_day.UI(self))

    def on_export_notes(self, evt=None):
        """The log of non conformities over the period, as a sheet."""
        self.on_export(self.engine.exporter.get_notes, self.since)

    def on_export_counts(self, evt=None):
        """How much control was run, per analyte and per bench."""
        self.on_export(self.engine.exporter.get_counts, self.since)

    def on_export_goals(self, evt=None):
        """The analytical goals, as the document that goes with the procedure.

        A PDF and not a sheet: it is read, checked against its sources and
        filed, and never rearranged.
        """
        path = os.path.join(tempfile.gettempdir(), "analytical_goals.pdf")
        self.on_export(self.engine.report.get_goals, path)
        self.engine.open_file(path)

    def on_export(self, write, *args):
        """Write a sheet while the cursor says the program is busy."""
        self.engine.tools.busy(self)
        path = write(*args)
        self.engine.tools.not_busy(self)
        self.engine.log.trace("exported {0}".format(path))

    def on_backup(self, evt=None):
        """A copy of the database file, named after the moment it was taken.

        The cheapest safety there is, and the one that matters most when the
        file lives on a shared folder: SQLite is one file, so a copy of it is
        the whole laboratory. Copied with the connection's own backup, which
        is consistent even if something is writing while it runs.
        """
        path = self.engine.backup()
        messagebox.showinfo(self.engine.app_title,
                            "Database copied to\n\n{0}".format(path),
                            parent=self)

    def on_dump(self, evt=None):
        """The whole database as SQL statements, in a file that can be read.

        A copy of the file is what is restored; a dump is what is read, and
        what survives a version of SQLite that no longer opens the file.
        """
        path = self.engine.db.dump(self.engine.get_file("sql/bks"))
        messagebox.showinfo(self.engine.app_title,
                            "Database written to\n\n{0}".format(path),
                            parent=self)

    def on_settings(self, evt=None):
        """The numbers the program computes with, in one window."""
        self.engine.windows.replace("settings", lambda: ui.settings.UI(self))

    def on_check(self, evt=None):
        """Ask the database whether it is still sound, and say what it answered."""
        self.engine.tools.busy(self)
        answer = self.engine.db.check()
        self.engine.tools.not_busy(self)

        if answer == "ok":
            messagebox.showinfo(self.engine.app_title,
                                "The database is sound.",
                                parent=self)
        else:
            self.engine.log.error("integrity check: {0}".format(answer))
            messagebox.showerror(self.engine.app_title,
                                 "The database reports:\n\n{0}\n\n"
                                 "Restore the most recent backup.".format(answer),
                                 parent=self)

    def on_vacuum(self, evt=None):
        """Rebuild the file, and say how much smaller it came out.

        Asked first: it rewrites the whole database, and on a file over a
        network that is every page across the wire.
        """
        if messagebox.askyesno(self.engine.app_title,
                               "Rebuild the database file, leaving out the space"
                               " that deleted rows left behind?\n\n"
                               "It reads and writes the whole file.",
                               parent=self):
            self.engine.tools.busy(self)
            freed = self.engine.db.vacuum()
            self.engine.tools.not_busy(self)
            messagebox.showinfo(self.engine.app_title,
                                "The file is {0} KB smaller.".format(freed // 1024),
                                parent=self)

    def on_change_password(self, evt=None):
        """Change the password of whoever is logged in."""
        self.engine.windows.replace("change_password",
                                    lambda: ui.change_password.UI(self))

    def on_manual(self, evt=None):
        """The manual, with the program that reads a PDF on this system."""
        self.engine.open_manual()

    def on_biological_variation(self, evt=None):
        """The EFLM database the analytical goals of every method come from.

        Where a method has an allowable total error and nobody remembers on
        what grounds, this is the ground: the within-subject and
        between-subject variation of the analyte, with the studies behind
        each estimate and how they were graded.
        """
        self.engine.open_url(BIOLOGICAL_VARIATION)

    def on_handbook(self, evt=None):
        """Nordtest TR 569, the handbook this kind of work is taught from.

        Written for chemical laboratories rather than clinical ones, and the
        better for it: it starts from what the control material is and ends
        at the chart, with the arithmetic in the open. There is an Italian
        translation of the fourth edition, published by the Istituto
        Superiore di Sanità as Rapporti ISTISAN 12/29.
        """
        self.engine.open_url(HANDBOOK)

    def on_about(self, evt=None):
        """What this is, who wrote it, and what it is running on."""
        self.engine.windows.replace(
            "about", lambda: ui.about.UI(self, self.parent.info))

    def on_licence(self, evt=None):
        """The licence, as the file in the repository says it."""
        self.engine.windows.replace("licence", lambda: ui.licence.UI(self))

    def on_plots(self, evt=None):
        """Every lot of this analyte, one chart under the other."""
        if self.test_method is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a test first.",
                                   parent=self)
        else:
            self.engine.windows.replace(
                "plots", lambda: ui.plots.UI(self, self.test_method, self.since))

    def on_statistics(self, evt=None):
        """Everything this series says, for the lot and the period chosen."""
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a batch first.",
                                   parent=self)
        else:
            self.engine.windows.replace(
                "statistics",
                lambda: ui.statistics.UI(self, self.batch))

    def on_tea(self, evt=None):
        """What this series does against what the analyte allows."""
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a batch first.",
                                   parent=self)
        else:
            self.engine.windows.replace(
                "tea", lambda: ui.tea.UI(self, self.batch))

    def on_bland_altman(self, evt=None):
        """This control on two instruments: how far apart they are."""
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a batch first.",
                                   parent=self)
        else:
            self.engine.windows.replace(
                "bland_altman",
                lambda: ui.bland_altman.UI(self, self.batch, self.since))

    def on_youden(self, evt=None):
        """The two levels of this control against each other."""
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a batch first.",
                                   parent=self)
        else:
            self.engine.windows.replace(
                "youden", lambda: ui.youden.UI(self, self.batch, self.since))

    def on_performance(self, evt=None):
        """Every lot at once: which ones are worth opening."""
        self.engine.windows.show(
            "performance",
            lambda: ui.performance_dashboard.UI(self, self.since))

    def on_notes(self, evt=None):
        """The log of what was written about the results, over the period."""
        self.engine.windows.show("notes",
                                 lambda: ui.notes.UI(self, self.since))

    def on_batches(self, evt=None):
        """The lots and the results on them: where the material is administered."""
        self.engine.windows.show("batches", lambda: ui.batches.UI(self))

    def on_master_data(self, module):
        """Open a master data list, or bring to the front the one open."""
        self.engine.windows.show(module.UI.TABLE, lambda: module.UI(self))

    # --------------------------------------------------------------- the ui

    def init_ui(self):
        """The column that narrows the question, and the chart it answers with."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        across = ttk.PanedWindow(frm_main, orient=tk.HORIZONTAL)

        left = ttk.Frame(across, style="App.TFrame")
        self.init_choices(left)
        self.init_workstations(left)
        self.init_batches(left)
        self.init_results(left)

        right = ttk.Frame(across, style="App.TFrame")
        self.init_charts(right)
        self.init_statistics(right)

        across.add(left, weight=0)
        across.add(right, weight=4)
        across.pack(fill=tk.BOTH, expand=1)

        # The status bar is packed before the frame that expands: pack gives
        # the space away in the order it is asked for, and a frame with
        # expand=1 asked first leaves nothing for what comes after.
        self.init_status_bar()
        frm_main.pack(fill=tk.BOTH, expand=1)

    def init_choices(self, container):
        """The two combo boxes: the panel, and the analyte in it."""
        ttk.Label(container, style="App.TLabel",
                  text="Categories").pack(side=tk.TOP, fill=tk.X)
        self.cb_categories = self.engine.tools.get_combo(container)
        self.cb_categories.bind("<<ComboboxSelected>>", self.on_selected_category)
        self.cb_categories.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        ttk.Label(container, style="App.TLabel",
                  text="Tests").pack(side=tk.TOP, fill=tk.X)
        self.cb_tests = self.engine.tools.get_combo(container)
        self.cb_tests.bind("<<ComboboxSelected>>", self.on_selected_test)
        self.cb_tests.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

    def init_workstations(self, container):
        """The instruments the analyte chosen is measured on.

        A combo like the two above it: the three choices that narrow the
        question read as three lines of the same sentence, and a list among
        them would look like something else.
        """
        ttk.Label(container, style="App.TLabel",
                  text="Workstation Data Source").pack(side=tk.TOP, fill=tk.X)
        self.cb_workstations = self.engine.tools.get_combo(container)
        self.cb_workstations.bind("<<ComboboxSelected>>", self.on_selected_workstation)
        self.cb_workstations.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

    def init_batches(self, container):
        """The lots of control material open on that analyte and instrument."""
        frm = ttk.LabelFrame(container, text="Batches")

        self.lst_batches = self.engine.tools.get_tree(frm, BATCHES)
        self.lst_batches.configure(height=4)
        self.lst_batches.tag_configure("expired", foreground="#c0392b")
        self.lst_batches.bind("<<TreeviewSelect>>", self.on_selected_batch)
        # Double clicking a lot enters a result on it: the gesture is on the
        # thing it is about, which is why there are no buttons here.
        self.lst_batches.bind("<Double-Button-1>", self.on_add_result)

        frm.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

    def init_statistics(self, container):
        """Three boxes side by side, as they are read.

        The target and the SD come printed on the box the control material
        came in; the average and the CV are what this laboratory got out of
        it; the bias, the uncertainty and the rule are the two put against
        each other. Eight numbers in a row, with nothing saying which is
        which, is how a target ends up compared with a target.
        """
        frm = ttk.Frame(container, style="App.TFrame")

        for caption, cells in self.STATISTICS:
            group = ttk.LabelFrame(frm, text=caption, labelanchor="n")
            for name, label in cells:
                cell = ttk.Frame(group, style="App.TFrame")
                ttk.Label(cell, style="App.TLabel", text=label,
                          anchor=tk.CENTER).pack(fill=tk.X)
                value = ttk.Label(cell, style="App.TLabel", width=9,
                                  anchor=tk.CENTER, textvariable=self.values[name])
                value.pack(fill=tk.X)
                cell.pack(side=tk.LEFT, padx=3, pady=2)
                if name == "westgard":
                    self.lbl_westgard = value
            group.pack(side=tk.LEFT, padx=(0, 6))

        frm.pack(side=tk.TOP, fill=tk.X, pady=(4, 0))

    def init_results(self, container):
        """The results of the lot, newest first, and what can be done to one."""
        frm = ttk.LabelFrame(container, text="Results")

        self.lst_results = self.engine.tools.get_tree(frm, RESULTS)
        self.lst_results.tag_configure("warning", foreground="#e67e22")
        self.lst_results.tag_configure("violation", foreground="#c0392b")
        self.lst_results.tag_configure("excluded", foreground="gray")
        self.lst_results.tag_configure("noted", background="#fff2cc")
        # Double clicking a result opens its note: what is usually wanted of
        # a result already entered is to say what was done about it. The
        # result itself is opened from the chart, by double clicking its point.
        self.lst_results.bind("<Double-Button-1>", self.on_note)
        # The right button reaches what the chart cannot: a result older than
        # the points drawn, and above all an excluded one, which has to be
        # opened again to be put back.
        self.lst_results.bind("<Button-3>", self.on_result_menu)

        self.menu_results = tk.Menu(self, tearoff=0)
        self.menu_results.add_command(label="Edit result", command=self.on_edit_result)
        self.menu_results.add_command(label="Note", command=self.on_note)

        frm.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def init_charts(self, container):
        """The Levey-Jennings chart, and the bias under it like a footer.

        Two canvases drawn by hand, with no plotting library behind them:
        the chart answers whether the method is in control, the bar answers
        how far from the target it sits and in which direction.
        """
        self.chart = LeveyJenningsCanvas(container)
        self.chart.set_point_click_callback(self.on_point)
        self.chart.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.bias_chart = BiasCanvas(container, height=70)
        self.bias_chart.pack(side=tk.TOP, fill=tk.X, pady=(4, 0))

    #: The periods the menu offers, in order: the code, the label, and a
    #: separator where None stands.
    PERIODS = (("last_month", "Last month"),
               ("last_3_months", "Last 3 months"),
               ("last_6_months", "Last 6 months"),
               ("last_12_months", "Last 12 months"),
               ("all", "All"),
               (None, None),
               ("custom", "Since..."))

    #: How often the database is asked whether it is still there, in
    #: milliseconds. Half a minute: often enough to notice before a result is
    #: typed into a window that can no longer save it, rare enough to cost
    #: nothing on a file over the network.
    HEARTBEAT = 30000

    def set_status(self):
        """Who is working, how many points the chart holds, and the period.

        Both numbers, because they answer different questions and the window
        uses them for different things: the chart and the statistics take the
        last so many results, the list and the comparisons take the period.
        """
        label = dict((code, label) for code, label in self.PERIODS if code)
        self.status.set("{0}   |   last {1} results   |   {2}".format(
            self.get_who(),
            self.engine.get_elements(),
            label.get(self.period.get(), self.period.get())))

    def init_status_bar(self):
        """Who is working, on which laboratory, with which numbers.

        The numbers on the right matter more than they look: a mean read with
        ddof 0 and one read with ddof 1 are different numbers, and so is a
        total error computed at z 1.65 or at 1.96. They are shown where they
        are read, rather than kept in a settings file nobody opens.
        """
        bar = ttk.Frame(self, style="StatusBar.TFrame")

        self.lamp = tk.Label(bar, text="\u25cf", font=("TkDefaultFont", 12),
                             bg=self.engine.tools.get_rgb(240, 240, 237))
        self.lamp.pack(side=tk.LEFT, padx=(4, 0))

        self.status.set(self.get_who())
        ttk.Label(bar, style="StatusBar.TLabel", anchor=tk.W,
                  textvariable=self.status).pack(side=tk.LEFT)

        # Packed from the right, so they read left to right as they are added
        # in reverse: laboratory, observations, z, ddof.
        site, lab, section = self.engine.get_laboratory()
        for caption, value in (("Section:", section),
                               ("Observations:", self.engine.get_observations()),
                               ("Z score:", self.engine.qc.get_zscore()),
                               ("ddof:", self.engine.qc.get_ddof())):
            ttk.Label(bar, style="StatusBarValue.TLabel",
                      text=value).pack(side=tk.RIGHT, padx=(0, 8))
            ttk.Label(bar, style="StatusBar.TLabel",
                      text=caption).pack(side=tk.RIGHT)

        bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.on_heartbeat()

    def on_heartbeat(self):
        """Ask the database whether it is still there, and colour the lamp.

        The file can live on a shared folder, and a network folder goes away
        without telling anybody: the window would look exactly the same and
        the first save of the morning would be the one to find out. Green
        means a statement was answered a moment ago.

        The question is the cheapest one there is, and it is asked on the
        connection the program already holds, so it tests what the program
        will actually use - not whether the file exists, which an unmounted
        path can answer wrongly either way.
        """
        try:
            self.engine.db.read(False, "SELECT 1")
            reachable = True
        except Exception:
            reachable = False

        if reachable:
            self.lamp.configure(fg="#1e8449")
            self.set_status()
        else:
            self.lamp.configure(fg="#c0392b")
            self.status.set("{0} - database unreachable".format(self.get_who()))

        self.after(self.HEARTBEAT, self.on_heartbeat)

    def get_who(self):
        """The person at the keyboard, as the status bar names them.

        Ready Player: the line an arcade cabinet showed before the game
        began, and the one this status bar has always opened with.
        """
        return "Ready Player {0} {1}".format(
            self.engine.log_user["last_name"],
            self.engine.log_user["first_name"] or "").strip()

    # ------------------------------------------------------------- the data

    def on_open(self):
        """The categories: everything else follows from the choice."""
        self.set_categories()

    def set_categories(self):
        """The panels that have an analyte in use under them."""
        sql = """SELECT DISTINCT c.category_id, c.description
                   FROM categories c
                   JOIN test_methods tm ON tm.category_id = c.category_id
                  WHERE c.status = 1 AND tm.status = 1
               ORDER BY c.description"""
        rows = self.engine.db.read(True, sql, ())

        self.dict_categories = {index: row["category_id"]
                                for index, row in enumerate(rows)}
        self.engine.tools.set_combo(self.cb_categories,
                                    [row["description"] for row in rows])

    def set_tests(self):
        """The analytes of the panel chosen, with the matrix each is measured in.

        The matrix is part of the name here: cocaine in urine and cocaine in
        keratin are one analyte and two methods, and a list that showed
        "Cocaine" twice would be asking to pick the wrong one.
        """
        category = self.dict_categories.get(self.cb_categories.current())

        sql = """SELECT tm.test_method_id, t.description AS analyte,
                        s.description AS matrix, u.description AS unit
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                  WHERE tm.status = 1 AND t.status = 1 AND tm.category_id = ?
               ORDER BY t.description, s.description"""
        rows = self.engine.db.read(True, sql, (category,))

        self.dict_tests = {index: row["test_method_id"]
                           for index, row in enumerate(rows)}
        self.tests = rows
        self.engine.tools.set_combo(self.cb_tests,
                                    ["{0} ({1})".format(row["analyte"], row["matrix"])
                                     for row in rows])

    def set_workstations(self):
        """The instruments that have a lot open on the analyte chosen."""
        sql = """SELECT DISTINCT w.workstation_id, w.description, w.serial
                   FROM workstations w
                   JOIN batches b ON b.workstation_id = w.workstation_id
                  WHERE w.status = 1 AND b.status = 1 AND b.test_method_id = ?
               ORDER BY w.rank, w.description"""
        rows = self.engine.db.read(True, sql, (self.test_method,))

        self.dict_workstations = {index: row["workstation_id"]
                                  for index, row in enumerate(rows)}
        self.workstations = rows
        self.engine.tools.set_combo(self.cb_workstations,
                                    ["{0} - {1}".format(row["description"],
                                                        row["serial"])
                                     for row in rows])
        self.cb_workstations.set("")

    def set_batches(self):
        """The lots open on that analyte and that instrument."""
        sql = """SELECT b.batch_id, b.rank, b.lot_number, b.expiration
                   FROM batches b
                  WHERE b.status = 1 AND b.test_method_id = ?
                    AND b.workstation_id = ?
               ORDER BY b.rank"""
        rows = self.engine.db.read(True, sql, (self.test_method, self.workstation))

        self.engine.tools.clear_treeview(self.lst_batches)
        self.dict_batches.clear()
        today = self.engine.get_today()
        for row in rows:
            if row["expiration"] is not None and row["expiration"] < today:
                tags = ("expired",)
            else:
                tags = ()
            item = self.lst_batches.insert(
                "", tk.END,
                values=("L{0}".format(row["rank"]),
                        row["lot_number"],
                        self.engine.format_date(row["expiration"])),
                tags=tags)
            self.dict_batches[item] = row["batch_id"]

    def set_results(self):
        """The results of the lot: the list, the charts and the statistics."""
        lot = self.engine.db.get_selected("batches", "batch_id", self.batch)

        sql = """SELECT r.result_id, r.result, r.received, r.status,
                        (SELECT COUNT(*) FROM notes n
                          WHERE n.result_id = r.result_id AND n.status = 1) AS notes
                   FROM results r
                  WHERE r.batch_id = ?
                    AND (? IS NULL OR r.received >= ?)
               ORDER BY r.received DESC
                  LIMIT ?"""
        rows = self.engine.db.read(True, sql, (self.batch, self.since, self.since,
                                                self.engine.get_records()))

        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_results.clear()
        for row in rows:
            item = self.lst_results.insert(
                "", tk.END,
                values=(self.engine.format_datetime(row["received"]), row["result"]),
                tags=self.get_tags(row, lot))
            self.dict_results[item] = row["result_id"]

        self.set_charts(lot)
        self.set_statistics(lot)

    def get_z(self, result, lot):
        """How many standard deviations this result sits from the target."""
        found = 0.0
        if lot["sd"] != 0:
            found = round((result - lot["target"]) / lot["sd"], 2)

        return found

    def get_tags(self, row, lot):
        """How a result is shown: excluded, beyond 2 SD, beyond 3 SD, noted."""
        z = abs(self.get_z(row["result"], lot))

        if row["status"] == 0:
            tags = ["excluded"]
        elif z >= 3:
            tags = ["violation"]
        elif z >= 2:
            tags = ["warning"]
        else:
            tags = []

        if row["notes"]:
            tags.append("noted")

        return tuple(tags)

    def set_charts(self, lot):
        """Draw the series, with the day each result was run on along the bottom.

        A control chart is read to answer when something started going wrong,
        and a series numbered 1 to 30 cannot answer that.
        """
        # Excluded results are drawn too, in grey and without a line through
        # them: a point taken out of the statistics is still a run that was
        # made, and it is the only way back to it - double clicking it is how
        # a result is opened again.
        # The chart is the last N results and not the results of a period.
        # Westgard rules are read on a number of observations; whether those
        # thirty took three weeks or three months does not change the rule,
        # and cutting them by a period chosen for the history would make a
        # series say NED while its thirty points sit just behind the cut.
        sql = """SELECT r.result_id, ROUND(r.result, 2) AS result, r.received,
                        r.status
                   FROM results r
                  WHERE r.batch_id = ?
               ORDER BY r.received DESC
                  LIMIT ?"""
        rows = list(reversed(self.engine.db.read(True, sql,
                                                 (self.batch,
                                                  self.engine.get_elements()))))
        self.chart_results = [row["result_id"] for row in rows]
        series = [row["result"] for row in rows]

        title = "{0} - {1} - Lot {2}".format(self.analyte,
                                             self.cb_workstations.get(),
                                             lot["lot_number"])

        self.chart.draw_chart(series,
                              lot["target"],
                              lot["sd"],
                              title=title,
                              dates=[row["received"] for row in rows],
                              status=[row["status"] for row in rows],
                              y_axis_caption=self.unit,
                              bottom_text=self.get_bottom_text(rows))

        # The bias bar is about the statistics, so it sees what they see.
        series = [row["result"] for row in rows if row["status"] == 1]

        self.bias_chart.draw_bias(series, lot["target"], unit=self.unit)

    def get_bottom_text(self, rows):
        """How many results the statistics were computed on, of those drawn.

        A series of thirty points where two were excluded is not a series of
        thirty, and whoever reads the mean has a right to know first.
        """
        counted = len([row for row in rows if row["status"] == 1])

        if counted == len(rows):
            found = "Computed on {0} results".format(counted)
        else:
            found = "Computed on {0} of {1} results, {2} excluded".format(
                counted, len(rows), len(rows) - counted)

        return found

    def set_statistics(self, lot):
        """The three boxes: the lot, the series, and the two compared."""
        series = self.engine.get_series(self.batch, self.engine.get_observations())
        method = self.engine.db.get_selected("test_methods", "test_method_id",
                                             self.test_method)

        mean = self.engine.qc.get_mean(series)
        cv = self.engine.qc.get_cv(series)
        bias = self.engine.qc.get_bias(mean, lot["target"])

        self.values["target"].set(lot["target"])
        self.values["sd"].set(lot["sd"])
        self.values["tea"].set(method["teap005"])
        self.values["n"].set(len(series))
        self.values["mean"].set(mean)
        self.values["cv_sd"].set(self.engine.qc.get_sd(series))
        self.values["cv"].set(cv)
        self.values["bias"].set(bias)
        self.values["te"].set(self.engine.qc.get_te(lot["target"], mean, cv))
        self.values["u"].set(self.engine.qc.get_uncertainty(cv, bias))

        # A series shorter than the observations asked for is not judged:
        # the rules that need more points simply do not fire, and what comes
        # out is an Accept with nothing behind it. A lot opened last week has
        # not been in control yet - it has not been anything yet.
        if len(series) < self.engine.get_observations():
            rule = "NED"
        else:
            rule = self.engine.westgards.get_rule(lot["target"], lot["sd"],
                                                  series)
        self.values["westgard"].set(rule)
        self.set_westgard_alarm(rule)

    def set_westgard_alarm(self, rule):
        """Colour the rule: it is the one cell that asks for something to be done.

        Accept is green and everything else red - a warning rule and a
        rejection rule both mean the run is looked at before results go out,
        and a colour that said "maybe" would be read as "carry on".
        """
        if rule == "NED":
            # Not enough data: neither good news nor bad, and it should not
            # be read as either.
            colour = "#666666"
        elif rule in ("Accept", ""):
            colour = "#1e8449"
        else:
            colour = "#c0392b"

        self.lbl_westgard.configure(foreground=colour)

    # ------------------------------------------------------------ the doing

    def on_period(self, evt=None):
        """Look back as far as the menu says, and read everything again.

        "Since..." asks for a day; anything else is a number of months from
        today. A mean of the last thirty results and a mean of the last
        thirty within three months are different numbers, so the series, the
        chart and the list all follow the same cut.
        """
        code = self.period.get()

        if code == "custom":
            code = self.get_since()

        if code is None:
            # The question was cancelled: put the menu back where it was.
            self.period.set(self.engine.get_period()[0])
        else:
            self.engine.set_period(code)
            self.period.set(code)
            code, self.since = self.engine.get_period()
            self.set_status()
            if self.batch is not None:
                self.set_results()

    def get_since(self):
        """Ask for the day to start from, with the widget that knows days.

        A text box would take 31 February and 2026-13-01; the calendarium
        takes three numbers and gives back a date or nothing.

        @return: the date, written, or None
        @rtype: string
        """
        window = self.engine.windows.replace(
            "since", lambda: ui.since.UI(self, self.engine.get_period()[1]))
        self.wait_window(window)

        found = None
        if window.chosen is not None:
            found = window.chosen.isoformat()

        return found

    def on_selected_category(self, evt=None):
        """A panel chosen: its analytes, and nothing below that yet."""
        self.set_tests()
        self.cb_tests.set("")
        self.cb_workstations.set("")
        self.engine.tools.set_combo(self.cb_workstations, ())
        self.test_method = None
        self.workstation = None
        self.on_reset()

    def on_selected_test(self, evt=None):
        """An analyte chosen: the instruments it is measured on."""
        index = self.cb_tests.current()
        self.test_method = self.dict_tests.get(index)

        if self.test_method is not None:
            self.analyte = self.tests[index]["analyte"]
            self.unit = self.tests[index]["unit"]
            self.workstation = None
            self.on_reset()
            self.set_workstations()

    def on_selected_workstation(self, evt=None):
        """An instrument chosen: the lots open on it."""
        self.workstation = self.dict_workstations.get(self.cb_workstations.current())

        if self.workstation is not None:
            self.on_reset()
            self.set_batches()

    def on_selected_batch(self, evt=None):
        """A lot chosen: the results, the charts and the statistics."""
        self.batch = self.dict_batches.get(self.lst_batches.focus())

        if self.batch is not None:
            self.set_results()

    def on_reset(self):
        """Empty everything that hangs off the choice just abandoned.

        The lots belong to an analyte and an instrument: leaving them on the
        screen after either has changed offers lots of something else, and
        they look exactly like the right ones.
        """
        self.batch = None
        self.engine.tools.clear_treeview(self.lst_batches)
        self.dict_batches.clear()
        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_results.clear()
        self.chart_results = []
        self.chart.clear()
        self.bias_chart.clear()
        for value in self.values.values():
            value.set("")

    def on_results_changed(self, row_id=None):
        """A result or a note was saved: read the lot again."""
        if self.batch is not None:
            self.set_results()

    def on_batches_changed(self, row_id=None):
        """A lot was saved: read the lots of the instrument again."""
        if self.workstation is not None:
            self.set_batches()

    def on_destroy(self, evt=None):
        """Stop being told about changes when this window goes.

        A Toplevel receives <Destroy> for every widget inside it as well:
        only its own counts.
        """
        if str(evt.widget) == str(self):
            for event, callback in (("results", self.on_results_changed),
                                    ("notes", self.on_results_changed),
                                    ("batches", self.on_batches_changed),
                                    ("categories", self.on_master_data_changed),
                                    ("tests", self.on_master_data_changed),
                                    ("test_methods", self.on_master_data_changed),
                                    ("workstations", self.on_master_data_changed)):
                self.engine.events.unsubscribe(event, callback)

    def on_master_data_changed(self, row_id=None):
        """Master data changed: read the choices again, keeping what still exists.

        An analyte disabled while it is the one being looked at leaves the
        window on a series that is no longer offered anywhere: the charts are
        emptied and the choice is given back, rather than left showing
        numbers that cannot be reached again.
        """
        category = self.cb_categories.get()
        test = self.cb_tests.get()

        self.set_categories()

        if category in self.cb_categories.cget("values"):
            self.cb_categories.set(category)
            self.set_tests()
            if test in self.cb_tests.cget("values"):
                self.cb_tests.set(test)
                self.on_selected_test()
            else:
                self.cb_tests.set("")
                self.test_method = None
                self.on_reset()
        else:
            self.cb_categories.set("")
            self.cb_tests.set("")
            self.engine.tools.set_combo(self.cb_tests, ())
            self.test_method = None
            self.on_reset()

    def on_point(self, info):
        """A point of the chart double clicked: open the result behind it."""
        index = info.get("index")

        if index is not None and 0 <= index < len(self.chart_results):
            result_id = self.chart_results[index]
            self.engine.windows.replace(
                "result", lambda: ui.result.UI(self, self.batch, result_id))

    def on_result_menu(self, evt):
        """The menu of a result, on the row the pointer is over.

        The row is selected first: a menu that acted on the row selected
        before, while the pointer is over another one, would act on the
        wrong result and say nothing about it.
        """
        item = self.lst_results.identify_row(evt.y)

        if item:
            self.lst_results.selection_set(item)
            self.lst_results.focus(item)
            self.menu_results.tk_popup(evt.x_root, evt.y_root)

    def on_add_result(self, evt=None):
        """Enter a result on the lot chosen."""
        if self.batch is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a batch first.",
                                   parent=self)
        else:
            self.engine.windows.replace("result",
                                        lambda: ui.result.UI(self, self.batch))

    def on_edit_result(self, evt=None):
        """Correct the result chosen; what it was stays in the audit trail."""
        result_id = self.dict_results.get(self.lst_results.focus())

        if result_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        else:
            self.engine.windows.replace(
                "result", lambda: ui.result.UI(self, self.batch, result_id))

    def on_note(self, evt=None):
        """Write down what was seen on a result and what was done about it."""
        result_id = self.dict_results.get(self.lst_results.focus())

        if result_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        else:
            self.engine.windows.replace("note",
                                        lambda: ui.note.UI(self, result_id))
