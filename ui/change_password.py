# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Change the password of whoever is logged in.

Only their own: a window that sets somebody else's password shows it to the
person filling the form. An administrator who has to let someone back in
gives them a new user or resets theirs to the one everybody starts with, and
the audit trail says who did it.

The old password is asked for as well. Without it, a terminal left unlocked
for two minutes is a password changed by whoever walked past.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.window import Window

#: Shorter than this is not a password.
MINIMUM = 8


class UI(Window, tk.Toplevel):
    """Three fields: the one in use, the new one, and the new one again."""

    def __init__(self, parent):
        super().__init__(name="change_password")

        self.parent = parent
        self.current = tk.StringVar()
        self.fresh = tk.StringVar()
        self.again = tk.StringVar()

        self.transient(parent.winfo_toplevel())
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=12)
        frm_fields = ttk.Frame(frm_main, style="App.TFrame")

        for row, (label, variable) in enumerate((("Current password:", self.current),
                                                 ("New password:", self.fresh),
                                                 ("New password again:", self.again))):
            ttk.Label(frm_fields, style="App.TLabel",
                      text=label).grid(row=row, column=0, sticky=tk.W)
            entry = self.engine.tools.get_entry(frm_fields, variable)
            entry.configure(show="*", width=self.engine.tools.FIELD_CODE)
            entry.grid(row=row, column=1, padx=6, pady=4)
            if row == 0:
                self.first = entry

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Save", self.on_save),
                                                       ("Cancel", self.on_cancel)),
                                                      window=self)

        frm_fields.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.title("Change password")
        self.first.focus()

    def on_save(self, evt=None):
        """Check the three fields against each other, then write the hash."""
        nickname = self.engine.log_user["nickname"]
        message = self.get_error(nickname)

        if message is not None:
            messagebox.showwarning(self.engine.app_title, message, parent=self)
        else:
            self.engine.db.write(
                "UPDATE users SET pswrd = ? WHERE user_id = ?",
                (self.engine.get_hash(self.fresh.get().encode("utf-8")),
                 self.engine.log_user["user_id"]))
            messagebox.showinfo(self.engine.app_title,
                                "Password changed.",
                                parent=self)
            self.on_cancel()

    def get_error(self, nickname):
        """What is wrong with what was typed, or None when nothing is."""
        found = None

        if self.engine.on_login(nickname, self.current.get().encode("utf-8")) is None:
            found = "The current password is not that one."
        elif len(self.fresh.get()) < MINIMUM:
            found = "A password is at least {0} characters.".format(MINIMUM)
        elif self.fresh.get() != self.again.get():
            found = "The two new passwords are not the same."
        elif self.fresh.get() == self.current.get():
            found = "The new password is the one already in use."

        return found

    def on_cancel(self, evt=None):
        self.destroy()
