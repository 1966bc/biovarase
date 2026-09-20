# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One lot of control material, on one analyte and one instrument.

This is where the limits are set, and everything else is measured against
them: the target and the standard deviation the chart is drawn on.

They can be typed, from the insert that came in the box, or computed from
the results already entered on the lot. Both are legitimate and they answer
different questions - the manufacturer's values say what the material is,
the computed ones say what this instrument does with it - so the window
offers the second and writes neither by itself.
"""

import tkinter as tk
from tkinter import messagebox

from app_config import BATCH_DESCRIPTION_MAX_LENGTH, LOT_NUMBER_MAX_LENGTH
from ui.calendarium import Calendarium
from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "batch"
    TABLE = "batches"

    def __init__(self, parent, test_method_id, row_id=None):
        #: The analyte this lot is a control for, chosen before this opens.
        self.test_method_id = test_method_id
        super().__init__(parent, row_id)

    def init_fields(self):

        self.lot_number = tk.StringVar()
        self.description = tk.StringVar()
        self.target = tk.DoubleVar()
        self.sd = tk.DoubleVar()
        self.lower = tk.DoubleVar()
        self.upper = tk.DoubleVar()
        self.rank = tk.IntVar()

        # What does not fit the column is cut as it is typed, rather than
        # refused by the database on saving.
        self.lot_number.trace_add(
            "write",
            lambda *args: self.engine.tools.limit_chars(self.lot_number,
                                                        LOT_NUMBER_MAX_LENGTH))
        self.description.trace_add(
            "write",
            lambda *args: self.engine.tools.limit_chars(self.description,
                                                        BATCH_DESCRIPTION_MAX_LENGTH))

        cb_control = self.engine.tools.get_combo(self.frm_fields)
        self.control = Lookup(self.engine, cb_control, "controls")

        cb_workstation = self.engine.tools.get_combo(self.frm_fields)
        self.workstation = Lookup(self.engine, cb_workstation, "workstations")

        self.expiration = Calendarium(self.frm_fields, "")

        self.add_field("Control:", cb_control)
        self.add_field("Workstation:", cb_workstation)
        self.add_field("Lot number:",
                       self.engine.tools.get_entry(self.frm_fields, self.lot_number))
        self.add_field("Level:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))
        self.add_field("Rank:",
                       self.engine.tools.get_entry(self.frm_fields, self.rank, "integer"))
        self.add_field("Expiration:", self.expiration)
        self.add_field("Target:",
                       self.engine.tools.get_entry(self.frm_fields, self.target, "float"))
        self.add_field("SD:",
                       self.engine.tools.get_entry(self.frm_fields, self.sd, "float"))
        self.add_field("Lower:",
                       self.engine.tools.get_entry(self.frm_fields, self.lower, "float"))
        self.add_field("Upper:",
                       self.engine.tools.get_entry(self.frm_fields, self.upper, "float"))

    def get_buttons(self):
        """Save and Cancel, and Compute for a lot that has results on it."""
        buttons = [("Save", self.on_save), ("Cancel", self.on_cancel)]

        if self.row_id is not None:
            buttons.insert(1, ("Compute", self.on_compute))

        return tuple(buttons)

    def on_compute(self, evt=None):
        """Put the mean and the SD of the results into target and SD.

        What the instrument does with this material, in place of what the box
        says it should: the values a laboratory sets for itself once a lot
        has been run long enough to know. It asks first, and it fills the
        fields rather than saving, so the numbers are seen before they become
        the limits everything is judged against.
        """
        series = self.engine.get_series(self.row_id, self.engine.get_observations())

        if len(series) < self.engine.get_observations():
            messagebox.showwarning(
                self.engine.app_title,
                "{0} results on this lot, {1} are wanted before computing"
                " target and SD.".format(len(series), self.engine.get_observations()),
                parent=self)
        else:
            mean = self.engine.qc.get_mean(series)
            sd = self.engine.qc.get_sd(series)
            msg = ("Set target and SD from the last {0} results?\n\n"
                   "Target {1} -> {2}\nSD {3} -> {4}").format(len(series),
                                                              self.target.get(),
                                                              mean,
                                                              self.sd.get(),
                                                              sd)
            if messagebox.askyesno(self.engine.app_title, msg, parent=self):
                self.target.set(mean)
                self.sd.set(sd)
                self.lower.set(round(mean - 3 * sd, 4))
                self.upper.set(round(mean + 3 * sd, 4))

    def set_values(self, row):

        self.lot_number.set(row["lot_number"])
        self.description.set(row["description"])
        self.target.set(row["target"])
        self.sd.set(row["sd"])
        self.lower.set(row["lower"])
        self.upper.set(row["upper"])
        self.rank.set(row["rank"])
        self.control.set_id(row["control_id"])
        self.workstation.set_id(row["workstation_id"])
        if row["expiration"] is not None:
            self.expiration.set_date(row["expiration"])

    def get_values(self):

        return {"control_id": self.control.get_id(),
                "test_method_id": self.test_method_id,
                "workstation_id": self.workstation.get_id(),
                "lot_number": self.engine.tools.get_clean_text(self.lot_number.get()),
                "description": self.engine.tools.get_clean_text(self.description.get()),
                "expiration": self.expiration.get_date(),
                "target": self.target.get(),
                "sd": self.sd.get(),
                "lower": self.lower.get(),
                "upper": self.upper.get(),
                "rank": self.rank.get()}
