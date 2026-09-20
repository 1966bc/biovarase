# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Who is working: a nickname, a password, and three tries.

The password is compared against the hash stored for that user, in the
engine; nothing here ever sees a password that is not the one just typed.
What the login also does is write the user into the session table, so that
the audit trail can say who entered a result.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.window import Window

#: Tries before the program gives up and closes. Three, as a cash machine
#: gives three: enough for a typing mistake, not enough to guess with.
MAX_LOGIN_ATTEMPTS = 3


class Login(Window, ttk.Frame):
    """The form that decides whether the program opens."""

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.nickname = tk.StringVar()
        self.password = tk.StringVar()
        #: Tries used up. Past MAX_LOGIN_ATTEMPTS the program closes.
        self.attempts = 0

        self.init_ui()

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=12)

        frm_fields = ttk.Frame(frm_main, style="App.TFrame")
        ttk.Label(frm_fields, style="App.TLabel", text="Nickname:").grid(row=0, column=0,
                                                                         sticky=tk.W)
        # The short measure: a nickname is not a supplier's name, and a login
        # as wide as a form looks like a form that is missing its fields.
        self.ent_nickname = self.engine.tools.get_entry(frm_fields, self.nickname)
        self.ent_nickname.configure(width=self.engine.tools.FIELD_CODE)
        self.ent_nickname.grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(frm_fields, style="App.TLabel", text="Password:").grid(row=1, column=0,
                                                                         sticky=tk.W)
        ent_password = self.engine.tools.get_entry(frm_fields, self.password)
        ent_password.configure(show="*", width=self.engine.tools.FIELD_CODE)
        ent_password.grid(row=1, column=1, padx=6, pady=4)
        ent_password.bind("<Return>", self.on_login)

        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("Login", self.on_login),
                                                       ("Quit", self.on_quit)))

        frm_fields.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        frm_main.pack(fill=tk.BOTH, expand=1)

    def on_open(self):

        self.pack(fill=tk.BOTH, expand=1)
        self.ent_nickname.focus()

    def on_login(self, evt=None):
        """Let them in, or count the try and say so.

        The message does not say which of the two was wrong: a login that
        answers "no such user" tells whoever is guessing which nicknames
        exist.
        """
        user = self.engine.on_login(self.nickname.get(),
                                    self.password.get().encode("utf-8"))

        if user is None:
            self.attempts += 1
            self.password.set("")
            if self.attempts >= MAX_LOGIN_ATTEMPTS:
                messagebox.showwarning(self.engine.app_title,
                                       "Too many attempts.",
                                       parent=self)
                self.on_quit()
            else:
                messagebox.showwarning(self.engine.app_title,
                                       "Login failed.",
                                       parent=self)
                self.ent_nickname.focus()
        else:
            self.engine.set_log_user(user)
            self.parent.show_main()
            self.destroy()

    def on_quit(self, evt=None):
        """Close the database and go: nobody got in."""
        self.engine.db.close()
        self.parent.destroy()
