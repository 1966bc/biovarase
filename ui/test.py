# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One analyte: added, or edited."""

import tkinter as tk

from ui.dialog import Dialog


class UI(Dialog):
    NAME = "test"
    TABLE = "tests"

    def init_fields(self):

        self.description = tk.StringVar()
        self.loinc = tk.StringVar()

        self.add_field("Analyte:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))
        self.add_field("LOINC:",
                       self.engine.tools.get_entry(self.frm_fields, self.loinc))

    def set_values(self, row):

        self.description.set(row["description"])
        self.loinc.set(row["loinc"])

    def get_values(self):

        return {"description": self.description.get(),
                "loinc": self.loinc.get()}
