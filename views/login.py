#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Login Frame for Biovarase Laboratory QC Management System.

Provides the authentication interface for user login.

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL Version 3, 29 June 2007
Version: 4.2 (Professional Edition)
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Tuple, Optional

from monitor import Monitor
from app_config import MAX_LOGIN_ATTEMPTS
from i18n import _, set_language
import views.main as ui
from views.lab_selector import LabSelectorDialog


class Login(ttk.Frame):
    """
    Login form frame for user authentication.

    Provides username/password input fields and handles authentication
    logic including attempt tracking and maximum attempt enforcement.

    Attributes:
        parent: Parent window (App instance)
        nick: StringVar for username input
        password: StringVar for password input
        attempts: Number of failed login attempts
        txtNick: Username entry widget

    Methods:
        on_login: Validate credentials and open main window on success
        hide: Hide login window after successful authentication
        get_values: Retrieve entered username and password
    """

    def __init__(self, parent: tk.Widget) -> None:
        """
        Initialize the login frame.

        Args:
            parent: Parent window (App instance)
        """
        super().__init__()

        # Get engine reference once from root window (App)
        self.engine = self.nametowidget(".").engine

        # Initialize language from configuration
        lang = self.engine.get_language()
        set_language(lang)

        self.engine.dict_instances[self.winfo_name()] = self
        self.parent: tk.Widget = parent
        self.parent.protocol("WM_DELETE_WINDOW",
                             self.nametowidget(".").on_exit)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.nick: tk.StringVar = tk.StringVar()
        self.password: tk.StringVar = tk.StringVar()
        self.attempts: int = 0
        self.engine.thread = None
        self.center_me()
        self._build_ui()

    def center_me(self) -> None:
        """Center window on the screen."""
        x = (self.parent.winfo_screenwidth() - self.parent.winfo_reqwidth()) / 2
        y = (self.parent.winfo_screenheight() - self.parent.winfo_reqheight()) / 2
        self.parent.geometry("+%d+%d" % (x, y))

    def _build_ui(self) -> None:
        """
        Create and layout login form widgets.

        Creates:
        - Username entry field
        - Password entry field (masked)
        - Login button (Alt+L shortcut)
        - Cancel button (Alt+C shortcut)
        """
        paddings = {"padx": 5, "pady": 5}

        self.frm_main = ttk.Frame(self.parent, style="App.TFrame")
        self.frm_main.grid(row=0, column=0)

        w = ttk.Frame(self.frm_main, style="App.TFrame", padding=8)
        w.grid(row=0, column=0, sticky=tk.NS, **paddings)

        r = 0
        c = 1
        ttk.Label(w, text=_("Username:")).grid(row=r, sticky=tk.W, **paddings)
        self.txtNick = ttk.Entry(w, textvariable=self.nick)
        self.txtNick.grid(row=r, column=c, **paddings)

        r += 1
        ttk.Label(w, text=_("Password:")).grid(row=r, sticky=tk.W, **paddings)
        ent_password = ttk.Entry(w, show="*", textvariable=self.password)
        ent_password.grid(row=r, column=c, **paddings)
        ent_password.bind("<Return>", self.on_login)
        ent_password.bind("<KP_Enter>", self.on_login)

        r += 1
        c = 0
        btn_login = ttk.Button(w, style="App.TButton", text=_("Login"), underline=0)
        btn_login.bind("<Return>", self.on_login)
        btn_login.bind("<Button-1>", self.on_login)
        btn_login.bind("<Alt-l>", self.on_login)
        self.parent.bind("<Alt-l>", self.on_login)
        btn_login.grid(row=r, column=c, sticky=tk.W, **paddings)

        c += 1
        btn_exit = ttk.Button(w, style="App.TButton", text=_("Cancel"), underline=0)
        btn_exit.bind("<Button-1>", self.parent.on_exit)
        btn_exit.bind("<Alt-c>", self.parent.on_exit)
        self.parent.bind("<Alt-c>", self.parent.on_exit)
        btn_exit.grid(row=r, column=c, sticky=tk.W, **paddings)

    def on_open(self) -> None:
        """Set focus to username field when login window opens."""
        self.txtNick.focus()

    def hide(self) -> None:
        """Hide login window after successful authentication."""
        self.parent.withdraw()

    def get_values(self) -> Tuple[str, bytes]:
        """
        Retrieve entered credentials.

        Returns:
            Tuple of (username, password_bytes)

        Note:
            Password is encoded to UTF-8 bytes for bcrypt verification
        """
        nick = self.nick.get()
        password = self.password.get().encode('utf-8').strip()
        return (nick, password)

    def on_login(self, event: Optional[tk.Event] = None) -> None:
        """
        Authenticate user and open main window on success.

        Validates input fields, attempts database authentication,
        tracks failed attempts, and enforces maximum attempt limit.

        Args:
            event: Tkinter event (from button click or key press)

        Behavior:
            - Validates non-empty fields
            - Calls engine.on_login() for database verification
            - Sets up idle monitor if enabled for user
            - Opens main window on success
            - Shows warning and increments counter on failure
            - Exits after MAX_LOGIN_ATTEMPTS failed attempts
        """
        if self.engine.on_fields_control(
            self.frm_main,
            self.engine.app_title
        ) == False:
            return

        nick, password = self.get_values()

        rs = self.engine.on_login((nick, password))

        if rs:
            self.engine.set_log_user(rs)

            # Initialize context from user's org_id (lab level in organizations table)
            user_org_id = self.engine.log_user.get("org_id")
            user_role = self.engine.log_user.get("role", 99)

            if user_org_id is None:
                # User without org_id assigned
                if user_role == 0:
                    # Admin can select lab
                    dialog = LabSelectorDialog(self)
                    self.wait_window(dialog)
                    selected_lab_id = dialog.get_selected_lab_id()

                    if selected_lab_id is None:
                        messagebox.showinfo(
                            self.engine.app_title,
                            _("Login cancelled."),
                            parent=self
                        )
                        self.engine.log_user.clear()
                        return

                    self.engine.init_current_ids_from_user(selected_lab_id)
                else:
                    # Non-admin without org_id - configuration error
                    messagebox.showerror(
                        self.engine.app_title,
                        _("No laboratory assigned to this user."),
                        parent=self
                    )
                    self.engine.log_user.clear()
                    return
            elif user_role == 0:
                # Admin with org_id: show selector with default
                dialog = LabSelectorDialog(self, default_lab_id=user_org_id)
                self.wait_window(dialog)
                selected_lab_id = dialog.get_selected_lab_id()

                if selected_lab_id is None:
                    messagebox.showinfo(
                        self.engine.app_title,
                        _("Login cancelled."),
                        parent=self
                    )
                    self.engine.log_user.clear()
                    return

                self.engine.init_current_ids_from_user(selected_lab_id)
            else:
                # Normal user: use assigned org_id (lab level)
                self.engine.init_current_ids_from_user(user_org_id)

            self.hide()

            # Start idle monitor if enabled for this user
            if self.engine.log_user["enable_time"] == True:
                self.engine.thread = Monitor(self)
                self.engine.thread.start()

            ui.Main(self).on_open()

        else:
            msg = _("Login failed.")
            messagebox.showwarning(self.engine.app_title, msg, parent=self)

            self.attempts += 1

            if self.attempts >= MAX_LOGIN_ATTEMPTS:
                msg = _("Maximum login attempts exceeded.")
                messagebox.showwarning(self.engine.app_title, msg, parent=self)
                self.on_quit()
            else:
                self.txtNick.focus()

    def on_about(self) -> None:
        """Display application information dialog."""
        messagebox.showinfo(self.engine.app_title,
                            self.nametowidget(".").info,
                            parent=self)

    def on_quit(self, evt: Optional[tk.Event] = None) -> None:
        """
        Close database connection and quit application.

        Args:
            evt: Tkinter event (optional)
        """
        self.engine.con.close()
        self.quit()
