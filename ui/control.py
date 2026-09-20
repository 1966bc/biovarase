# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One control material: added, or edited."""

import tkinter as tk

from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "control"
    TABLE = "controls"

    def init_fields(self):

        self.description = tk.StringVar()
        self.reference = tk.StringVar()

        combo = self.engine.tools.get_combo(self.frm_fields)
        self.supplier = Lookup(self.engine, combo, "suppliers")

        self.add_field("Control:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))
        self.add_field("Supplier:", combo)
        self.add_field("Reference:",
                       self.engine.tools.get_entry(self.frm_fields, self.reference))

    def set_values(self, row):

        self.description.set(row["description"])
        self.reference.set(row["reference"])
        self.supplier.set_id(row["supplier_id"])

    def get_values(self):

        return {"supplier_id": self.supplier.get_id(),
                "description": self.description.get(),
                "reference": self.reference.get()}
