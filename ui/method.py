# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One analytical method: added, or edited."""

import tkinter as tk

from ui.dialog import Dialog


class UI(Dialog):
    NAME = "method"
    TABLE = "methods"

    def init_fields(self):

        self.description = tk.StringVar()

        self.add_field("Method:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))

    def set_values(self, row):

        self.description.set(row["description"])

    def get_values(self):

        return {"description": self.description.get()}
