# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The morning's controls, one bench at a time, in one form.

Entering results one at a time is the right shape for a correction and the
wrong shape for the work: a bench passes its controls together, and going
back to the main window to choose the analyte, the instrument and the lot
before each value is most of the time the job takes.

So: a bench and a day, every lot open on it, and a box for each. Tab goes
down the column, and Save writes the ones that were filled in. Nothing else
is touched - a box left empty is a control not run, not a result of zero.

The lots the laboratory has said it controls every working day are marked,
because the question this window is really answering is not "what did I
measure" but "what have I not measured yet".
"""

import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.calendarium import Calendarium
from ui.window import Window

#: The size the window opens at. Wide enough for the columns and tall
#: enough that a bench of twenty lots is scrolled rather than hunted through.
WIDTH = 1160
HEIGHT = 560

#: The columns of a row, and how wide each label is in characters.
ANALYTE_WIDTH = 30
LEVEL_WIDTH = 8
LOT_WIDTH = 13
NUMBER_WIDTH = 8
UNIT_WIDTH = 8
DAILY_WIDTH = 6
ENTRY_WIDTH = 10

#: What goes in reagent_lot when the box at the top is left empty. The same
#: word ui/result.py writes, so the two ways in agree.
DEFAULT_REAGENT_LOT = "NOT ASSIGNED"


class UI(Window, tk.Toplevel):
    """A bench, a day, and a box for every lot open on it."""

    def __init__(self, parent):
        super().__init__(name="day")

        self.parent = parent
        self.summary = tk.StringVar()
        self.reagent_lot = tk.StringVar()
        #: The box of each lot: batch_id -> the variable behind its entry.
        self.boxes = {}
        self.workstations = []

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.geometry("{0}x{1}".format(WIDTH, HEIGHT))
        self.minsize(WIDTH, 300)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Save", self.on_save),
                                                       ("Close", self.on_cancel)))

        frm_body = ttk.Frame(frm_main, style="App.TFrame")
        self.init_choices(frm_body)
        # The summary is packed before the rows, which expand: pack gives the
        # room away in the order it is asked for, and a frame with expand=1
        # asked first leaves nothing for what comes after.
        ttk.Label(frm_body, style="App.TLabel",
                  textvariable=self.summary).pack(side=tk.BOTTOM, anchor=tk.W,
                                                  pady=(4, 0))
        self.init_rows(frm_body)

        frm_body.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        frm_main.pack(fill=tk.BOTH, expand=1)

    def init_choices(self, container):
        """The bench, the day, and the reagent lot they were all run with."""
        frm = ttk.Frame(container, style="App.TFrame")

        ttk.Label(frm, style="App.TLabel", text="Bench:").pack(side=tk.LEFT)
        self.cb_workstations = self.engine.tools.get_combo(frm)
        self.cb_workstations.bind("<<ComboboxSelected>>", self.on_chosen)
        self.cb_workstations.pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(frm, style="App.TLabel", text="Day:").pack(side=tk.LEFT)
        self.day = Calendarium(frm, "")
        self.day.pack(side=tk.LEFT, padx=(4, 12))
        for variable in (self.day.day, self.day.month, self.day.year):
            variable.trace_add("write", self.on_day)

        # One box for the whole pass: a bench that runs its controls together
        # usually runs them on one reagent lot, and typing it once is the
        # difference between recording it and not.
        ttk.Label(frm, style="App.TLabel", text="Reagent lot:").pack(side=tk.LEFT)
        entry = self.engine.tools.get_entry(frm, self.reagent_lot)
        entry.configure(width=16)
        entry.pack(side=tk.LEFT, padx=(4, 12))

        frm.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

    def init_rows(self, container):
        """The scrolling area the lots are listed in.

        A Treeview cannot hold an entry box in a cell, so the rows are
        widgets in a frame, and the frame is scrolled by a canvas - which is
        how Tk has always done this.
        """
        frm = ttk.Frame(container, style="App.TFrame")

        self.sheet = tk.Canvas(frm, highlightthickness=0,
                               background=self.engine.tools.get_rgb(
                                   *self.engine.tools.BACKGROUND))
        scrollbar = ttk.Scrollbar(frm, orient=tk.VERTICAL,
                                  command=self.sheet.yview)
        self.sheet.configure(yscrollcommand=scrollbar.set)

        self.rows = ttk.Frame(self.sheet, style="App.TFrame")
        self.rows_window = self.sheet.create_window((0, 0), window=self.rows,
                                                    anchor=tk.NW)
        self.rows.bind("<Configure>", self.on_rows_resized)
        self.sheet.bind("<Configure>", self.on_sheet_resized)
        # Linux sends wheel events as buttons four and five.
        for sequence in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.sheet.bind_all(sequence, self.on_wheel)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sheet.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        frm.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def on_rows_resized(self, evt=None):
        """The rows grew or shrank: tell the canvas how far it can scroll."""
        self.sheet.configure(scrollregion=self.sheet.bbox(tk.ALL))

    def on_sheet_resized(self, evt):
        """The window was resized: the rows are as wide as the canvas."""
        self.sheet.itemconfigure(self.rows_window, width=evt.width)

    def on_wheel(self, evt):
        """The wheel, however this system reports it."""
        if evt.num == 5 or evt.delta < 0:
            self.sheet.yview_scroll(1, tk.UNITS)
        else:
            self.sheet.yview_scroll(-1, tk.UNITS)

    # ------------------------------------------------------------- the data

    def on_open(self):

        self.title("The controls of a day")
        self.day.set_today()
        self.set_workstations()
        self.set_rows()

    def set_workstations(self):
        """The benches that have a lot open on them."""
        sql = """SELECT DISTINCT w.workstation_id, w.description, w.serial
                   FROM workstations w
                   JOIN batches b ON b.workstation_id = w.workstation_id
                  WHERE w.status = 1 AND b.status = 1
               ORDER BY w.rank, w.description"""
        self.workstations = self.engine.db.read(True, sql, ())

        self.engine.tools.set_combo(self.cb_workstations,
                                    ["{0} - {1}".format(row["description"],
                                                        row["serial"])
                                     for row in self.workstations])
        if self.workstations:
            self.cb_workstations.current(0)

    def set_rows(self):
        """Every lot open on the bench chosen, with a box to type into."""
        for child in self.rows.winfo_children():
            child.destroy()
        self.boxes.clear()

        rows = self.get_lots()
        self.put_headings()

        for line, row in enumerate(rows, start=1):
            self.put_row(line, row)

        self.set_summary(rows)
        self.on_rows_resized()

    def put_headings(self):
        """The names of the columns, once, above the rows."""
        for column, (caption, width) in enumerate(
                (("Analyte", ANALYTE_WIDTH),
                 ("Level", LEVEL_WIDTH),
                 ("Lot", LOT_WIDTH),
                 ("Target", NUMBER_WIDTH),
                 ("SD", NUMBER_WIDTH),
                 ("Unit", UNIT_WIDTH),
                 ("Daily", DAILY_WIDTH),
                 ("Today", DAILY_WIDTH),
                 ("Result", ENTRY_WIDTH))):
            ttk.Label(self.rows, style="App.TLabel", text=caption, width=width,
                      anchor=tk.W).grid(row=0, column=column, padx=2, sticky=tk.W)

    def put_row(self, line, row):
        """One lot: what it is, what it is worth, and a box for today's value."""
        cells = ("{0} ({1})".format(row["analyte"], row["matrix"]),
                 row["level"],
                 row["lot_number"],
                 row["target"],
                 row["sd"],
                 row["unit"],
                 self.get_daily(row["is_mandatory"]),
                 self.get_today(row["today"]))

        for column, (text, width) in enumerate(zip(cells,
                                                   (ANALYTE_WIDTH, LEVEL_WIDTH,
                                                    LOT_WIDTH, NUMBER_WIDTH,
                                                    NUMBER_WIDTH, UNIT_WIDTH,
                                                    DAILY_WIDTH, DAILY_WIDTH))):
            ttk.Label(self.rows, style="App.TLabel", text=text, width=width,
                      anchor=tk.W).grid(row=line, column=column, padx=2,
                                        sticky=tk.W)

        value = tk.StringVar()
        entry = self.engine.tools.get_entry(self.rows, value, "float")
        entry.configure(width=ENTRY_WIDTH)
        entry.grid(row=line, column=8, padx=2, pady=1, sticky=tk.W)
        self.boxes[row["batch_id"]] = value

    def get_lots(self):
        """The lots open on the bench chosen, and how many results today.

        The count is the point of the window: it answers, lot by lot,
        whether this one has been done yet this morning.

        @return: the lots
        @rtype: list of dictionaries
        """
        found = []
        index = self.cb_workstations.current()
        day = self.day.get_date()

        if index >= 0 and day is not None:
            sql = """SELECT b.batch_id, b.lot_number, b.description AS level,
                            b.target, b.sd,
                            t.description AS analyte,
                            s.description AS matrix,
                            u.description AS unit,
                            tm.is_mandatory,
                            (SELECT COUNT(*)
                               FROM results r
                              WHERE r.batch_id = b.batch_id
                                AND r.status = 1
                                AND DATE(r.received) = ?) AS today
                       FROM batches b
                       JOIN test_methods tm
                            ON tm.test_method_id = b.test_method_id
                       JOIN tests t ON t.test_id = tm.test_id
                       JOIN samples s ON s.sample_id = tm.sample_id
                       JOIN units u ON u.unit_id = tm.unit_id
                       JOIN categories c ON c.category_id = tm.category_id
                      WHERE b.status = 1 AND tm.status = 1 AND t.status = 1
                        AND b.workstation_id = ?
                   ORDER BY c.description, t.description, s.description, b.rank"""
            found = self.engine.db.read(
                True, sql, (day.isoformat(),
                            self.workstations[index]["workstation_id"]))

        return found

    def set_summary(self, rows):
        """How much of this bench is still to do, said in one line."""
        waiting = len([row for row in rows if not row["today"]])
        daily = len([row for row in rows
                     if row["is_mandatory"] and not row["today"]])

        self.summary.set("{0} lots on this bench, {1} without a result today,"
                         " {2} of them controlled every day.".format(len(rows),
                                                                     waiting,
                                                                     daily))

    def get_daily(self, is_mandatory):
        """Whether the laboratory controls this one every working day."""
        if is_mandatory:
            found = "yes"
        else:
            found = ""

        return found

    def get_today(self, how_many):
        """How many results this lot already has on the day chosen."""
        if how_many:
            found = str(how_many)
        else:
            found = ""

        return found

    # ------------------------------------------------------------ the doing

    def on_chosen(self, evt=None):
        """Another bench: its lots, and its own empty boxes."""
        self.set_rows()

    def on_day(self, *args):
        """The day changed under the fingers: count that day instead.

        A day half typed is not a date - 31 of a month on its way to
        February - so what is not a date yet is left alone.
        """
        if self.day.get_date() is not None:
            self.set_rows()

    def on_save(self, evt=None):
        """Write every box that was filled in, and leave the rest alone."""
        day = self.day.get_date()

        if day is None:
            messagebox.showwarning(self.engine.app_title,
                                   "That is not a date.", parent=self)
        else:
            typed = self.get_typed()
            if not typed:
                messagebox.showwarning(self.engine.app_title,
                                       "Nothing was entered.", parent=self)
            else:
                self.save(day, typed)

    def get_typed(self):
        """The boxes with something in them, as numbers.

        A comma is read as a decimal point, which is what the keypad of this
        country writes.

        @return: batch_id -> value
        @rtype: dictionary
        """
        found = {}

        for batch_id, value in self.boxes.items():
            written = value.get().strip()
            if written:
                found[batch_id] = float(written.replace(",", "."))

        return found

    def save(self, day, typed):
        """One result per box, all stamped with the same moment.

        The day is the one chosen, the time is now: a control entered this
        morning for yesterday keeps yesterday's date, which is when it was
        run, and the chart is drawn in that order.
        """
        now = datetime.datetime.now()
        received = datetime.datetime.combine(day, now.time())
        reagent_lot = self.engine.tools.get_clean_text(self.reagent_lot.get())

        if not reagent_lot:
            reagent_lot = DEFAULT_REAGENT_LOT

        saved = None
        for batch_id, result in typed.items():
            values = {"batch_id": batch_id,
                      "result": result,
                      "received": received,
                      "reagent_lot": reagent_lot,
                      "status": 1,
                      "created_by": self.engine.log_user["user_id"],
                      "created_at": now}
            sql, args = self.engine.db.get_insert("results", values)
            saved = self.engine.db.write(sql, args)

        self.engine.log.trace("saved {0} results".format(len(typed)))
        self.set_rows()
        # Once, and after the boxes have been read: the callbacks run inside
        # notify, and one of them reads this window's lot again.
        self.engine.events.notify("results", saved)

    def on_cancel(self, evt=None):
        """Let go of the wheel before going: bind_all is not this window's alone."""
        for sequence in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.sheet.unbind_all(sequence)
        self.destroy()
