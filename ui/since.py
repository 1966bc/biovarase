# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The day a period starts, asked with the widget that knows about days.

A text box asking for a date gets 31/02, gets 2026-13-01, gets 20 settembre.
The calendarium asks for three numbers and refuses anything that is not a
day, which is the whole reason it exists.
"""

import tkinter as tk
from tkinter import ttk

from ui.calendarium import Calendarium
from ui.window import Window


class UI(Window, tk.Toplevel):
    """A date, and what the window that opened it does with it."""

    def __init__(self, parent, day=None):
        super().__init__(name="since")

        self.parent = parent
        #: The day to start from, or None when the question was cancelled.
        #: Whoever opened this window reads it after wait_window.
        self.chosen = None
        self.day = day

        self.transient(parent.winfo_toplevel())
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=12)

        frm_fields = ttk.Frame(frm_main, style="App.TFrame")
        ttk.Label(frm_fields, style="App.TLabel",
                  text="Show results from:").pack(side=tk.TOP, anchor=tk.W)
        self.calendarium = Calendarium(frm_fields, "")
        self.calendarium.pack(side=tk.TOP, anchor=tk.W, pady=(4, 0))

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Ok", self.on_save),
                                                       ("Cancel", self.on_cancel)),
                                                      window=self)

        frm_fields.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("Period")
        if self.day is not None:
            self.calendarium.set_date(self.day)

    def on_save(self, evt=None):
        """Take the day, if it is one, and go."""
        self.chosen = self.calendarium.get_date()
        self.destroy()

    def on_cancel(self, evt=None):
        self.destroy()
