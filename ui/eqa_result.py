# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One analyte of one round: what was reported, and what it should have been.

Three numbers are typed and the fourth is computed, which is why the z score
is not a field here and not a column in the database: it is
(result - assigned) / sd, and a stored copy could disagree with them.

**Result** is what this laboratory sent in. **Assigned** is the value the
scheme assigned - a consensus of the participants, a reference method, or the
way the material was made; the report says which. **SD** is the standard
deviation the scheme judges by, sigma-pt in ISO 13528. When a report gives a
target CV instead, the SD is the assigned value times that CV over a hundred.
"""

import datetime
import tkinter as tk
from tkinter import messagebox

from ui.dialog import Dialog


class UI(Dialog):
    NAME = "eqa_result"
    TABLE = "eqa_results"

    def __init__(self, parent, round_id, row_id=None):
        #: The round this belongs to, chosen before this opens.
        self.round_id = round_id
        super().__init__(parent, row_id)

    def init_fields(self):

        self.result = tk.DoubleVar()
        self.assigned = tk.DoubleVar()
        self.sd = tk.DoubleVar()
        #: position in the box -> test_method_id
        self.methods = {}

        self.cb_method = self.engine.tools.get_combo(self.frm_fields)
        self.set_methods()

        self.add_field("Analyte:", self.cb_method)
        self.add_field("Result:", self.get_entry(self.result), tk.W)
        self.add_field("Assigned:", self.get_entry(self.assigned), tk.W)
        self.add_field("SD:", self.get_entry(self.sd), tk.W)

    def get_entry(self, variable):
        """A number, as wide as a concentration and no wider."""
        entry = self.engine.tools.get_entry(self.frm_fields, variable, "float")
        entry.configure(width=12)

        return entry

    def set_methods(self):
        """The analytes this laboratory measures, with the matrix in brackets.

        The matrix belongs in the name here for the same reason it does in
        the main window: cocaine in urine and cocaine in keratin are one
        analyte and two methods, and a scheme reports them separately.
        """
        sql = """SELECT tm.test_method_id,
                        t.description AS analyte,
                        s.description AS matrix,
                        u.description AS unit
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                  WHERE tm.status = 1 AND t.status = 1
               ORDER BY t.description, s.description"""
        rows = self.engine.db.read(True, sql, ())

        self.methods = {index: row["test_method_id"]
                        for index, row in enumerate(rows)}
        self.engine.tools.set_combo(
            self.cb_method,
            ["{0} ({1}) - {2}".format(row["analyte"], row["matrix"], row["unit"])
             for row in rows])

    def set_values(self, row):

        self.result.set(row["result"])
        self.assigned.set(row["assigned"])
        self.sd.set(row["sd"])
        for index, test_method_id in self.methods.items():
            if test_method_id == row["test_method_id"]:
                self.cb_method.current(index)

    def on_save(self, evt=None):
        """Refuse what the round already has, and what cannot be judged.

        A standard deviation of zero is not a scheme that is certain, it is a
        number missing from the report, and every z computed against it would
        be a division by nothing.
        """
        if self.sd.get() <= 0:
            messagebox.showwarning(self.engine.app_title,
                                   "The SD the scheme judges by has to be"
                                   " greater than zero.", parent=self)
        elif self.is_taken():
            messagebox.showwarning(self.engine.app_title,
                                   "This round already has that analyte.",
                                   parent=self)
        else:
            super().on_save()

    def is_taken(self):
        """True when this round already holds another line for that analyte.

        @return: taken
        @rtype: boolean
        """
        sql = """SELECT eqa_id FROM eqa_results
                  WHERE round_id = ? AND test_method_id = ?
                    AND (? IS NULL OR eqa_id <> ?)"""
        row = self.engine.db.read(True, sql, (self.round_id,
                                              self.get_test_method_id(),
                                              self.row_id, self.row_id))

        return bool(row)

    def get_test_method_id(self):
        """The analyte chosen, by its key."""
        return self.methods.get(self.cb_method.current())

    def get_values(self):

        return {"round_id": self.round_id,
                "test_method_id": self.get_test_method_id(),
                "result": self.result.get(),
                "assigned": self.assigned.get(),
                "sd": self.sd.get(),
                "created_by": self.get_created_by(),
                "created_at": self.get_created_at()}

    def get_created_by(self):
        """Whoever typed it in; a correction does not take it over."""
        if self.row_id is None:
            found = self.engine.log_user["user_id"]
        else:
            found = self.get_row()["created_by"]

        return found

    def get_created_at(self):
        """When it was typed in, kept through every later correction."""
        if self.row_id is None:
            found = datetime.datetime.now()
        else:
            found = self.get_row()["created_at"]

        return found
