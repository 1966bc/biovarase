# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The main window: look for an analyte, see the chart and the results.

Three lists, left to right and top to bottom, each one narrowing the next:
the analytes as they are measured here, the lots of control material open on
the one chosen, and the results on that lot - as a Levey-Jennings chart and
as a table, with the statistics of the series between them.

The search box filters the analytes as it is typed. A laboratory that runs
fifty methods does not scroll to find one.
"""

import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import ui.actions
import ui.categories
import ui.controls
import ui.equipments
import ui.methods
import ui.note
import ui.result
import ui.samples
import ui.suppliers
import ui.tests
import ui.units
import ui.users
import ui.workstations

from ljcanvas import LeveyJenningsCanvas
from ui.window import Window

#: The columns of each list, as Tools.get_tree wants them:
#: (identifier, heading, anchor, stretch, minwidth, width). The first one is
#: always '#0', the implicit column, which carries no data.
METHODS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Analyte", tk.W, True, 140, 190),
           ("#2", "Matrix", tk.W, True, 70, 90),
           ("#3", "Unit", tk.W, False, 50, 60))

LOTS = (("#0", "id", tk.W, False, 0, 0),
        ("#1", "Level", tk.W, False, 50, 60),
        ("#2", "Lot", tk.W, True, 80, 100),
        ("#3", "Bench", tk.W, False, 60, 70),
        ("#4", "Expiration", tk.W, False, 80, 90))

RESULTS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Received", tk.W, False, 130, 150),
           ("#2", "Result", tk.E, False, 70, 80),
           ("#3", "z", tk.E, False, 40, 50),
           ("#4", "Reagent", tk.W, False, 70, 80),
           ("#5", "Entered by", tk.W, False, 80, 90),
           ("#6", "Note", tk.W, True, 120, 200))


class Main(Window, ttk.Frame):
    """Look for an analyte, see the chart and the results, enter one."""

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        #: position in a list -> primary key, filled when the list is read
        self.dict_methods = {}
        self.dict_lots = {}
        self.dict_results = {}
        #: what is chosen now, as the rows the database gave
        self.method = None
        self.lot = None
        self.analyte = ""
        #: the search box, and the statistics under the chart
        self.search = tk.StringVar()
        self.laboratory = tk.StringVar()
        self.values = {name: tk.StringVar() for name in
                       ("n", "target", "sd", "mean", "cv", "bias", "te", "westgard")}

        self.init_menu()
        self.init_ui()
        self.search.trace_add("write", self.on_search)
        self.engine.events.subscribe("results", self.on_results_changed)
        self.engine.events.subscribe("notes", self.on_results_changed)
        self.engine.events.subscribe("batches", self.on_lots_changed)

    # ------------------------------------------------------------- the menu

    def init_menu(self):
        """The menu bar: what can be opened, and who may open it."""
        bar = tk.Menu(self.parent)

        m_file = tk.Menu(bar, tearoff=0)
        m_file.add_command(label="Log", underline=0, command=self.engine.open_log)
        m_file.add_separator()
        m_file.add_command(label="Exit", underline=1, command=self.parent.on_exit)
        bar.add_cascade(label="File", underline=0, menu=m_file)

        m_qc = tk.Menu(bar, tearoff=0)
        m_qc.add_command(label="Add result", underline=0, command=self.on_add_result)
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
                                  ("Suppliers", ui.suppliers),
                                  ("Units", ui.units),
                                  ("Users", ui.users)):
                m_edit.add_command(label=label,
                                   command=lambda m=module: self.on_master_data(m))
            bar.add_cascade(label="Edit", underline=0, menu=m_edit)

        self.parent.config(menu=bar)

    def on_master_data(self, module):
        """Open a master data list, or bring to the front the one open."""
        self.engine.windows.show(module.UI.TABLE, lambda: module.UI(self))

    # --------------------------------------------------------------- the ui

    def init_ui(self):
        """Three lists, a chart and a table, in panes that can be dragged.

        A PanedWindow and not fixed frames: on the bench the chart wants the
        room, on a laptop the lists do, and the person in front of it knows
        which. The weights say what grows when the window does - the chart
        and the results, not the lists of names.
        """
        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        across = ttk.PanedWindow(frm_main, orient=tk.HORIZONTAL)

        left = ttk.PanedWindow(across, orient=tk.VERTICAL)
        self.init_methods(left)
        self.init_lots(left)

        right = ttk.PanedWindow(across, orient=tk.VERTICAL)
        chart = ttk.Frame(right, style="App.TFrame")
        self.init_chart(chart)
        self.init_statistics(chart)
        right.add(chart, weight=3)
        self.init_results(right)

        across.add(left, weight=1)
        across.add(right, weight=3)
        across.pack(fill=tk.BOTH, expand=1)
        frm_main.pack(fill=tk.BOTH, expand=1)

    def init_methods(self, container):
        """The analytes, with the matrix each one is measured in."""
        frm = ttk.LabelFrame(container, text="Analytes")

        ttk.Entry(frm, textvariable=self.search).pack(fill=tk.X, padx=4, pady=4)

        self.lst_methods = self.engine.tools.get_tree(frm, METHODS)
        self.lst_methods.bind("<<TreeviewSelect>>", self.on_selected_method)

        container.add(frm, weight=3)

    def init_lots(self, container):
        """The lots of control material open on the analyte chosen."""
        frm = ttk.LabelFrame(container, text="Lots")

        self.lst_lots = self.engine.tools.get_tree(frm, LOTS)
        self.lst_lots.tag_configure("expired", foreground="#c0392b")
        self.lst_lots.bind("<<TreeviewSelect>>", self.on_selected_lot)

        container.add(frm, weight=1)

    def init_chart(self, container):
        """The Levey-Jennings chart, drawn on a canvas and nothing else."""
        frm = ttk.LabelFrame(container, text="Levey-Jennings")

        self.chart = LeveyJenningsCanvas(frm, height=280)
        self.chart.pack(fill=tk.BOTH, expand=1, padx=2, pady=2)

        frm.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def init_statistics(self, container):
        """What the series says about itself, in one line."""
        frm = ttk.Frame(container, style="App.TFrame")

        for name, caption in (("n", "N"),
                              ("target", "Target"),
                              ("sd", "SD"),
                              ("mean", "Mean"),
                              ("cv", "CV%"),
                              ("bias", "Bias%"),
                              ("te", "TE%"),
                              ("westgard", "Westgard")):
            cell = ttk.Frame(frm, style="App.TFrame")
            ttk.Label(cell, style="App.TLabel", text=caption).pack()
            ttk.Label(cell, style="App.TLabel", width=10, anchor=tk.CENTER,
                      textvariable=self.values[name]).pack()
            cell.pack(side=tk.LEFT, padx=4, pady=4)

        frm.pack(side=tk.TOP, fill=tk.X)

    def init_results(self, container):
        """The results of the lot, newest first, and the buttons."""
        frm = ttk.LabelFrame(container, text="Results")

        self.lst_results = self.engine.tools.get_tree(frm, RESULTS)
        self.lst_results.tag_configure("warning", foreground="#e67e22")
        self.lst_results.tag_configure("violation", foreground="#c0392b")
        self.lst_results.tag_configure("excluded", foreground="gray")
        self.lst_results.bind("<Double-Button-1>", self.on_edit_result)

        buttons = self.engine.tools.get_button_column(frm,
                                                      (("Add", self.on_add_result),
                                                       ("Edit", self.on_edit_result),
                                                       ("Note", self.on_note)))
        buttons.pack(side=tk.RIGHT, fill=tk.Y)

        container.add(frm, weight=2)

    # ------------------------------------------------------------- the data

    def on_open(self):
        """Read the analytes: the rest follows from what is chosen."""
        self.set_methods()

    def set_methods(self):
        """The methods in use, filtered by what is typed in the search box."""
        sql = """SELECT tm.test_method_id, t.description AS analyte,
                        s.description AS matrix, u.description AS unit
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                  WHERE tm.status = 1 AND t.status = 1
                    AND t.description LIKE ?
               ORDER BY t.description, s.description"""
        rows = self.engine.db.read(True, sql, ("%{0}%".format(self.search.get()),))

        self.engine.tools.clear_treeview(self.lst_methods)
        self.dict_methods.clear()
        for row in rows:
            item = self.lst_methods.insert("", tk.END,
                                           values=(row["analyte"],
                                                   row["matrix"],
                                                   row["unit"]))
            self.dict_methods[item] = row["test_method_id"]

        self.engine.log.trace("methods = {0}".format(len(rows)))

    def set_lots(self):
        """The lots of the method chosen, the newest first."""
        sql = """SELECT b.batch_id, b.description AS level, b.lot_number,
                        b.expiration, b.target, b.sd,
                        w.description AS bench
                   FROM batches b
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE b.status = 1 AND b.test_method_id = ?
               ORDER BY b.rank, w.description"""
        rows = self.engine.db.read(True, sql, (self.method,))

        self.engine.tools.clear_treeview(self.lst_lots)
        self.dict_lots.clear()
        # The connection parses declared types, so a DATE column comes back
        # as a date and is compared with one.
        today = datetime.date.today()
        for row in rows:
            if row["expiration"] is not None and row["expiration"] < today:
                tags = ("expired",)
            else:
                tags = ()
            item = self.lst_lots.insert("", tk.END,
                                        values=(row["level"],
                                                row["lot_number"],
                                                row["bench"],
                                                self.engine.format_date(row["expiration"])),
                                        tags=tags)
            self.dict_lots[item] = row["batch_id"]

    def set_results(self):
        """The results of the lot: the table, the chart and the statistics."""
        lot = self.engine.db.get_selected("batches", "batch_id", self.lot)

        sql = """SELECT r.result_id, r.result, r.received, r.reagent_lot, r.status,
                        u.last_name AS entered,
                        (SELECT n.description FROM notes n
                          WHERE n.result_id = r.result_id AND n.status = 1
                       ORDER BY n.note_id DESC LIMIT 1) AS note
                   FROM results r
                   LEFT JOIN users u ON u.user_id = r.created_by
                  WHERE r.batch_id = ?
               ORDER BY r.received DESC
                  LIMIT ?"""
        rows = self.engine.db.read(True, sql, (self.lot, self.engine.get_records()))

        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_results.clear()
        for row in rows:
            item = self.lst_results.insert("", tk.END,
                                           values=(self.engine.format_datetime(row["received"]),
                                                   row["result"],
                                                   self.get_z(row["result"], lot),
                                                   row["reagent_lot"],
                                                   row["entered"],
                                                   row["note"] or ""),
                                           tags=self.get_tags(row, lot))
            self.dict_results[item] = row["result_id"]

        self.set_chart(lot)
        self.set_statistics(lot)

    def get_z(self, result, lot):
        """How many standard deviations this result sits from the target."""
        found = 0.0
        if lot["sd"] != 0:
            found = round((result - lot["target"]) / lot["sd"], 2)

        return found

    def get_tags(self, row, lot):
        """How a result is shown: excluded, beyond 2 SD, beyond 3 SD."""
        z = abs(self.get_z(row["result"], lot))

        if row["status"] == 0:
            tags = ("excluded",)
        elif z >= 3:
            tags = ("violation",)
        elif z >= 2:
            tags = ("warning",)
        else:
            tags = ()

        return tags

    def set_chart(self, lot):
        """Draw the series: the points the chart shows, oldest first."""
        series = self.engine.get_series(self.lot, self.engine.get_elements())

        title = "{0} - {1} - lot {2}".format(self.analyte,
                                             lot["description"],
                                             lot["lot_number"])

        self.chart.draw_chart(series, lot["target"], lot["sd"], title=title)

    def set_statistics(self, lot):
        """The statistics of the series, and the rule read on it."""
        series = self.engine.get_series(self.lot, self.engine.get_observations())

        mean = self.engine.qc.get_mean(series)
        cv = self.engine.qc.get_cv(series)
        bias = self.engine.qc.get_bias(mean, lot["target"])

        self.values["n"].set(len(series))
        self.values["target"].set(lot["target"])
        self.values["sd"].set(lot["sd"])
        self.values["mean"].set(mean)
        self.values["cv"].set(cv)
        self.values["bias"].set(bias)
        self.values["te"].set(self.engine.qc.get_te(lot["target"], mean, cv))
        self.values["westgard"].set(
            self.engine.westgards.get_westgard_violation_rule(lot["target"],
                                                              lot["sd"],
                                                              series))

    # ------------------------------------------------------------ the doing

    def on_search(self, *args):
        """The analytes again, filtered by what has just been typed."""
        self.set_methods()

    def on_selected_method(self, evt=None):
        """An analyte chosen: read its lots, and clear what was shown."""
        item = self.lst_methods.focus()
        self.method = self.dict_methods.get(item)

        if self.method is not None:
            self.analyte = self.lst_methods.item(item)["values"][0]
            self.set_lots()
            self.lot = None
            self.on_reset()

    def on_selected_lot(self, evt=None):
        """A lot chosen: the results, the chart and the statistics."""
        item = self.lst_lots.focus()
        self.lot = self.dict_lots.get(item)

        if self.lot is not None:
            self.set_results()

    def on_reset(self):
        """Empty the chart, the table and the statistics."""
        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_results.clear()
        self.chart.clear()
        for value in self.values.values():
            value.set("")

    def on_results_changed(self, row_id=None):
        """A result or a note was saved: read the lot again."""
        if self.lot is not None:
            self.set_results()

    def on_lots_changed(self, row_id=None):
        """A lot was saved: read the lots of the analyte again."""
        if self.method is not None:
            self.set_lots()

    def on_add_result(self, evt=None):
        """Enter a result on the lot chosen."""
        if self.lot is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a lot first.",
                                   parent=self)
        else:
            self.engine.windows.replace("result",
                                        lambda: ui.result.UI(self, self.lot))

    def on_edit_result(self, evt=None):
        """Correct the result chosen; what it was stays in the audit trail."""
        result_id = self.dict_results.get(self.lst_results.focus())

        if result_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        else:
            self.engine.windows.replace(
                "result", lambda: ui.result.UI(self, self.lot, result_id))

    def on_note(self, evt=None):
        """Write down what was seen and what was done about it."""
        result_id = self.dict_results.get(self.lst_results.focus())

        if result_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   self.engine.no_selected,
                                   parent=self)
        else:
            self.engine.windows.replace("note",
                                        lambda: ui.note.UI(self, result_id))
