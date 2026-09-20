# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""What was seen on a result, and what was done about it.

With no validation step this is where a non conformity is written down: the
corrective action taken, in the words of whoever took it. It is the reason
the actions table exists, and the reason a note carries who wrote it.
"""

import datetime
import tkinter as tk

from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "note"
    TABLE = "notes"

    def __init__(self, parent, result_id, row_id=None):
        #: The result this note is about.
        self.result_id = result_id
        super().__init__(parent, row_id)

    def init_fields(self):

        self.description = tk.StringVar()

        combo = self.engine.tools.get_combo(self.frm_fields)
        self.action = Lookup(self.engine, combo, "actions")

        self.add_field("Action:", combo)
        self.add_field("Note:",
                       self.engine.tools.get_entry(self.frm_fields, self.description))

    def set_values(self, row):

        self.description.set(row["description"])
        self.action.set_id(row["action_id"])

    def get_values(self):

        if self.row_id is None:
            created_by = self.engine.log_user["user_id"]
            created_at = datetime.datetime.now()
        else:
            row = self.get_row()
            created_by = row["created_by"]
            created_at = row["created_at"]

        return {"result_id": self.result_id,
                "action_id": self.action.get_id(),
                "description": self.engine.tools.get_clean_text(self.description.get()),
                "modified": datetime.date.today(),
                "created_by": created_by,
                "created_at": created_at}
