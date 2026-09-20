# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One instrument on the bench: added, or edited."""

import tkinter as tk

from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "workstation"
    TABLE = "workstations"

    def init_fields(self):

        self.description = tk.StringVar()
        self.serial = tk.StringVar()
        self.rank = tk.IntVar()

        combo = self.engine.tools.get_combo(self.frm_fields)
        self.equipment = Lookup(self.engine, combo, "equipments")

        self.add_field("Instrument:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))
        self.add_field("Model:", combo)
        self.add_field("Serial:",
                       self.engine.tools.get_entry(self.frm_fields, self.serial))
        # Anchored west: the grid stretches every field to the width of the
        # widest one, and the order an instrument is listed in is one figure
        # next to the name of a mass spectrometer.
        self.add_field("Rank:",
                       self.engine.tools.get_entry(self.frm_fields, self.rank,
                                                   "integer"),
                       tk.W)

    def set_values(self, row):

        self.description.set(row["description"])
        self.serial.set(row["serial"])
        self.rank.set(row["rank"])
        self.equipment.set_id(row["equipment_id"])

    def get_values(self):

        return {"equipment_id": self.equipment.get_id(),
                "description": self.description.get(),
                "serial": self.serial.get(),
                "rank": self.rank.get()}
