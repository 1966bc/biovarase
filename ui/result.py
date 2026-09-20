# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One control result: entered, or corrected.

A result belongs to a lot. The lot is chosen in the main window before this
one opens, and here it can be changed: a result entered on the wrong lot is
moved to the right one, which is the answer to a mistake that would
otherwise want deleting.

Nothing is deleted in this program. A result that was measured and came out
badly is excluded - the In use box - which keeps it on the chart in grey and
out of the statistics; a result entered by mistake is moved or excluded with
a note saying why. What happened, happened, and a record that can be made to
say otherwise is not a record.

Correcting a result leaves the value it had in audit_results, written by the
trigger on the table. Nothing is hidden by a correction, and nothing has to
be remembered to keep it that way.
"""

import datetime
import tkinter as tk

from ui.calendarium import Calendarium
from ui.dialog import Dialog
from ui.lookup import Lookup

#: What goes in reagent_lot when nobody says otherwise.
DEFAULT_REAGENT_LOT = "NOT ASSIGNED"


class UI(Dialog):
    NAME = "result"
    TABLE = "results"

    def __init__(self, parent, batch_id, row_id=None):
        #: The lot this result is on, chosen in the main window.
        self.batch_id = batch_id
        super().__init__(parent, row_id)

    def init_fields(self):

        self.result = tk.StringVar()
        self.reagent_lot = tk.StringVar()

        self.received = Calendarium(self.frm_fields, "")

        # The lot this result is on, and the lots it can be moved to: the
        # other lots of the same analyte, on any instrument. A result typed
        # under the wrong lot is a mistake that moves, not one that is
        # deleted.
        cb_batch = self.engine.tools.get_combo(self.frm_fields)
        self.batch = Lookup(self.engine, cb_batch, "batches", caption="lot_number")
        self.set_batches(cb_batch)
        self.add_field("Batch:", cb_batch)

        # Fields as wide as what goes in them, and anchored west: a grid
        # stretches every field to the width of the widest one, and a control
        # value is five figures next to a lot number that is twenty.
        self.add_field("Result:",
                       self.engine.tools.get_entry(self.frm_fields, self.result,
                                                   "float"),
                       tk.W)

        self.add_field("Received:", self.received, tk.W)

        entry = self.engine.tools.get_entry(self.frm_fields, self.reagent_lot)
        entry.configure(width=20)
        self.add_field("Reagent lot:", entry, tk.W)

    def set_batches(self, combo):
        """The lots this result may sit on: the ones of the same analyte.

        Read here rather than by Lookup, which knows how to read a table and
        not which rows of it belong to this window.
        """
        lot = self.engine.db.get_selected("batches", "batch_id", self.batch_id)

        sql = """SELECT b.batch_id, b.lot_number, b.description AS level,
                        w.description AS bench
                   FROM batches b
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE b.test_method_id = ? AND b.status = 1
               ORDER BY b.rank, w.description"""
        rows = self.engine.db.read(True, sql, (lot["test_method_id"],))

        self.batch.ids = {index: row["batch_id"] for index, row in enumerate(rows)}
        self.engine.tools.set_combo(combo,
                                    ["{0} - {1} - {2}".format(row["lot_number"],
                                                              row["level"],
                                                              row["bench"])
                                     for row in rows])
        self.batch.set_id(self.batch_id)

    def set_values(self, row):

        self.result.set(row["result"])
        self.reagent_lot.set(row["reagent_lot"])
        self.received.set_date(row["received"])
        self.batch.set_id(row["batch_id"])

    def get_values(self):
        """The row as the table wants it, with the time kept as it was.

        A result entered today is stamped with the moment it is entered; a
        result corrected keeps the time it was run at, because that is when
        the control was measured and the chart is drawn in that order.
        """
        if self.row_id is None:
            now = datetime.datetime.now()
            received = datetime.datetime.combine(self.received.get_date(), now.time())
            created_by = self.engine.log_user["user_id"]
            created_at = now
        else:
            row = self.get_row()
            received = datetime.datetime.combine(self.received.get_date(),
                                                 row["received"].time())
            created_by = row["created_by"]
            created_at = row["created_at"]

        reagent_lot = self.engine.tools.get_clean_text(self.reagent_lot.get())
        if not reagent_lot:
            reagent_lot = DEFAULT_REAGENT_LOT

        return {"batch_id": self.batch.get_id() or self.batch_id,
                "result": float(self.result.get().replace(",", ".")),
                "received": received,
                "reagent_lot": reagent_lot,
                "created_by": created_by,
                "created_at": created_at}
