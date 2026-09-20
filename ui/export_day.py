# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Pick a day and get its controls, as a sheet or as a form.

Two formats because they answer two needs. The sheet is for the data -
sorted, filtered, pasted into something else, two sums done on the side. The
form is the record: it does not change after it is made, it says which
laboratory it belongs to, who produced it, with which program and which
statistical settings, and it has a line for the signature of whoever reviews
the run. ISO 15189 asks for the quality control results to be recorded and
reviewed; a spreadsheet is data, a form is a record.
"""

import os
import tempfile
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.calendarium import Calendarium
from ui.window import Window


class UI(Window, tk.Toplevel):
    """A date, and the sheet it produces."""

    def __init__(self, parent):
        super().__init__(name="export_day")

        self.parent = parent
        self.count = tk.StringVar()

        self.transient(parent)
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.init_ui()
        self.engine.tools.center_me(self)

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=12)
        frm_fields = ttk.Frame(frm_main, style="App.TFrame")

        ttk.Label(frm_fields, style="App.TLabel",
                  text="Day:").grid(row=0, column=0, sticky=tk.W)
        self.day = Calendarium(frm_fields, "")
        self.day.grid(row=0, column=1, padx=6, pady=4, sticky=tk.W)

        ttk.Label(frm_fields, style="App.TLabel",
                  textvariable=self.count).grid(row=1, column=0, columnspan=2,
                                                sticky=tk.W, pady=(4, 0))

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Sheet", self.on_sheet),
                                                       ("Form", self.on_form),
                                                       ("Cancel", self.on_cancel)),
                                                      window=self)

        frm_fields.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("Export the controls of a day")
        self.day.set_today()
        self.set_count()

    def set_count(self):
        """How many controls that day holds, before anybody waits for a sheet."""
        row = self.engine.db.read(False,
                                  "SELECT COUNT(*) AS n FROM results"
                                  " WHERE DATE(received) = ? AND status = 1",
                                  (self.day.get_iso(),))
        self.count.set("{0} results on that day.".format(row["n"]))

    def on_sheet(self, evt=None):
        """The controls of the day as a spreadsheet: the data."""
        self.on_export(self.engine.exporter.get_day)

    def on_form(self, evt=None):
        """The controls of the day as a form: the record that is signed."""
        self.on_export(self.get_form)

    def get_form(self, day):
        """The PDF, written where the system keeps temporary files."""
        path = os.path.join(tempfile.gettempdir(),
                            "qc_{0}.pdf".format(day.isoformat()))
        self.engine.report.get_day(day, path)
        self.engine.open_file(path)

        return path

    def on_export(self, write):
        """Check the day, then let the writer make its file and open it."""
        self.set_count()
        day = self.day.get_date()

        if day is None:
            messagebox.showwarning(self.engine.app_title,
                                   "That is not a date.",
                                   parent=self)
        else:
            row = self.engine.db.read(False,
                                      "SELECT COUNT(*) AS n FROM results"
                                      " WHERE DATE(received) = ? AND status = 1",
                                      (day.isoformat(),))
            if not row["n"]:
                messagebox.showinfo(self.engine.app_title,
                                    "No controls were run on that day.",
                                    parent=self)
            else:
                self.engine.tools.busy(self)
                path = write(day)
                self.engine.tools.not_busy(self)
                self.engine.log.trace("exported {0}".format(path))
                self.on_cancel()

    def on_cancel(self, evt=None):
        self.destroy()
