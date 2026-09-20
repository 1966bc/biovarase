# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Pick a day and get its controls as a sheet.

The question at the end of a morning, or the morning after: what was run
yesterday, what came out, and was any of it out of control. The sheet is
what gets printed, signed and filed, which is the reason it exists.
"""

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
                                                      (("Export", self.on_export),
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

    def on_export(self, evt=None):
        """Write the sheet, unless there is nothing to write."""
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
                path = self.engine.exporter.get_day(day)
                self.engine.tools.not_busy(self)
                self.engine.log.trace("exported {0}".format(path))
                self.on_cancel()

    def on_cancel(self, evt=None):
        self.destroy()
