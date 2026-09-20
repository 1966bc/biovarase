# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One proficiency scheme the laboratory takes part in: added, or edited."""

import tkinter as tk

from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "eqa_scheme"
    TABLE = "eqa_schemes"

    def init_fields(self):

        self.description = tk.StringVar()

        combo = self.engine.tools.get_combo(self.frm_fields)
        self.supplier = Lookup(self.engine, combo, "suppliers")

        self.add_field("Scheme:",
                       self.engine.tools.get_entry(self.frm_fields,
                                                   self.description))
        self.add_field("Organiser:", combo)

    def set_values(self, row):

        self.description.set(row["description"])
        self.supplier.set_id(row["supplier_id"])

    def get_values(self):

        return {"description": self.engine.tools.get_clean_text(
                    self.description.get()),
                "supplier_id": self.supplier.get_id()}
