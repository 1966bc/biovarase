# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One corrective action: added, or edited."""

import tkinter as tk

from ui.dialog import Dialog


class UI(Dialog):
    NAME = "action"
    TABLE = "actions"

    def init_fields(self):

        self.code = tk.StringVar()
        self.description = tk.StringVar()

        self.add_field("Code:",
                       self.engine.tools.get_entry(self.frm_fields, self.code))
        self.add_field("Action:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))

    def set_values(self, row):

        self.code.set(row["code"])
        self.description.set(row["description"])

    def get_values(self):

        return {"code": self.code.get(),
                "description": self.description.get()}
