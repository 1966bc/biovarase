# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The numbers the program computes with, in one window.

They were three windows - one for the coverage factor, one for the degrees
of freedom, one for the observations - and they belong together, because
they are read together: a total error at z 1.65 with ddof 0 over thirty
observations is one statement, and changing any of the three changes every
number on the screen.

Written straight into biovarase.ini, where the comments explaining what each
one means are; only the line that changes is rewritten, so those comments
survive being changed from here.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.window import Window

#: The settings this window edits: section, key, caption, and what it is.
FIELDS = (("statistics", "ddof", "Degrees of freedom",
           "0 for the population, 1 for a sample"),
          ("statistics", "zscore", "Coverage factor",
           "1.65 one-sided 95%, 1.96 two-sided, 2 for k = 2"),
          ("statistics", "observations", "Observations",
           "how many results a series needs before the rules are read"),
          ("display", "elements", "Points on the chart",
           "how many results the Levey-Jennings draws"),
          ("display", "records", "Results in the list",
           "how many the main window loads at once"))


class UI(Window, tk.Toplevel):
    """Five numbers, and what each of them does."""

    def __init__(self, parent):
        super().__init__(name="settings")

        self.parent = parent
        self.values = {}

        self.transient(parent.winfo_toplevel())
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=12)
        frm_fields = ttk.Frame(frm_main, style="App.TFrame")

        for row, (section, key, caption, what) in enumerate(FIELDS):
            self.values[key] = tk.StringVar(value=self.engine.config.get(section, key))

            ttk.Label(frm_fields, style="App.TLabel",
                      text="{0}:".format(caption)).grid(row=row, column=0,
                                                        sticky=tk.W, pady=2)
            entry = self.engine.tools.get_entry(frm_fields, self.values[key], "float")
            entry.configure(width=8)
            entry.grid(row=row, column=1, sticky=tk.W, padx=8, pady=2)
            ttk.Label(frm_fields, style="App.TLabel",
                      text=what).grid(row=row, column=2, sticky=tk.W, pady=2)

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Save", self.on_save),
                                                       ("Cancel", self.on_cancel)),
                                                      window=self)

        frm_fields.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("Settings")

    def on_save(self, evt=None):
        """Write them back, and say that the windows already open will not follow.

        A window reads these when it draws: the ones on the screen were drawn
        with the old ones, and telling somebody to reopen them is honest
        where quietly leaving two sets of numbers on one desktop is not.
        """
        for section, key, caption, what in FIELDS:
            self.engine.config.set(section, key, self.values[key].get().strip())

        messagebox.showinfo(self.engine.app_title,
                            "Saved. Windows already open keep the numbers they"
                            " were drawn with: close and open them again.",
                            parent=self)
        self.on_cancel()

    def on_cancel(self, evt=None):
        self.destroy()
