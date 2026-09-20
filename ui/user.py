# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""One member of the staff: added, or edited.

The password is not a field here. A new user is given one to change, and
changing it is done by whoever owns it, in ui.change_password: a form that
sets somebody else's password shows it to the person filling the form.
"""

import tkinter as tk

from ui.dialog import Dialog

#: What each role can do, as the combo box says it.
ROLES = ("Administrator", "Technician")


class UI(Dialog):
    NAME = "user"
    TABLE = "users"

    def init_fields(self):

        self.last_name = tk.StringVar()
        self.first_name = tk.StringVar()
        self.nickname = tk.StringVar()

        self.cb_role = self.engine.tools.get_combo(self.frm_fields)
        self.engine.tools.set_combo(self.cb_role, ROLES)

        self.add_field("Last name:",
                       self.engine.tools.get_entry(self.frm_fields, self.last_name))
        self.add_field("First name:",
                       self.engine.tools.get_entry(self.frm_fields, self.first_name))
        self.add_field("Nickname:",
                       self.engine.tools.get_entry(self.frm_fields, self.nickname))
        self.add_field("Role:", self.cb_role)

    def set_values(self, row):

        self.last_name.set(row["last_name"])
        self.first_name.set(row["first_name"])
        self.nickname.set(row["nickname"])
        self.cb_role.current(row["role"])

    def get_values(self):

        values = {"last_name": self.last_name.get(),
                  "first_name": self.first_name.get(),
                  "nickname": self.nickname.get(),
                  "role": self.cb_role.current()}

        # A new user starts with a password to change; an existing one keeps
        # the hash that is already stored, which this form never reads.
        if self.row_id is None:
            values["pswrd"] = self.engine.get_new_password()
        else:
            values["pswrd"] = self.get_row()["pswrd"]

        return values
