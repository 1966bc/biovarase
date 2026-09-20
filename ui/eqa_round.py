# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One distribution of a proficiency scheme: added, or edited.

Two dates and they are not the same one. **Received** is the day the sample
was run, which is the day the performance belongs to and the day to read the
internal control of. **Reported** is the day the scheme's report came back,
weeks later, which is when the numbers in it could be entered at all.
"""

import datetime
import tkinter as tk

from ui.calendarium import Calendarium
from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "eqa_round"
    TABLE = "eqa_rounds"

    def init_fields(self):

        self.description = tk.StringVar()

        combo = self.engine.tools.get_combo(self.frm_fields)
        self.scheme = Lookup(self.engine, combo, "eqa_schemes")

        self.received = Calendarium(self.frm_fields, "")
        self.reported = Calendarium(self.frm_fields, "")

        entry = self.engine.tools.get_entry(self.frm_fields, self.description)
        entry.configure(width=20)

        self.add_field("Scheme:", combo)
        self.add_field("Round:", entry, tk.W)
        self.add_field("Run on:", self.received, tk.W)
        self.add_field("Reported:", self.reported, tk.W)

    def set_values(self, row):

        self.description.set(row["description"])
        self.scheme.set_id(row["scheme_id"])
        self.received.set_date(row["received"])
        if row["reported"] is not None:
            self.reported.set_date(row["reported"])

    def get_values(self):

        return {"scheme_id": self.scheme.get_id(),
                "description": self.engine.tools.get_clean_text(
                    self.description.get()),
                "received": self.received.get_date(),
                "reported": self.reported.get_date(),
                "created_by": self.get_created_by(),
                "created_at": self.get_created_at()}

    def get_created_by(self):
        """Whoever opened the round; an edit does not take it over."""
        if self.row_id is None:
            found = self.engine.log_user["user_id"]
        else:
            found = self.get_row()["created_by"]

        return found

    def get_created_at(self):
        """When it was opened, kept through every later correction."""
        if self.row_id is None:
            found = datetime.datetime.now()
        else:
            found = self.get_row()["created_at"]

        return found
