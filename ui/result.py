# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One control result: entered, or corrected.

A result belongs to a lot, and the lot is chosen in the main window before
this one opens: what is asked here is the value, the day it was run and the
reagent lot in use.

Correcting a result leaves the value it had in audit_results, written by the
trigger on the table. Nothing is hidden by a correction, and nothing has to
be remembered to keep it that way.
"""

import datetime
import tkinter as tk

from ui.calendarium import Calendarium
from ui.dialog import Dialog

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

        self.add_field("Result:",
                       self.engine.tools.get_entry(self.frm_fields, self.result, "float"))
        self.add_field("Received:", self.received)
        self.add_field("Reagent lot:",
                       self.engine.tools.get_entry(self.frm_fields, self.reagent_lot))

    def set_values(self, row):

        self.result.set(row["result"])
        self.reagent_lot.set(row["reagent_lot"])
        self.received.set_date(row["received"])

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

        return {"batch_id": self.batch_id,
                "result": float(self.result.get().replace(",", ".")),
                "received": received,
                "reagent_lot": reagent_lot,
                "created_by": created_by,
                "created_at": created_at}
