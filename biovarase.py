#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Biovarase - Laboratory Quality Control Management System.

Entry point for the Biovarase application. Initializes the database
engine, loads configuration, and manages the application lifecycle.

Features:
- Encrypted database credentials (config.enc)
- Automatic login for read-only generic users
- Idle time monitoring with automatic logout
- Log rotation and cleanup

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL Version 3, 29 June 2007
Version: 4.2 (Professional Edition)
"""
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Dict, Any, Optional

from engine import Engine
from monitor import Monitor
from i18n import _
from app_config import (
    CONFIG_FILENAME,
    THREAD_JOIN_TIMEOUT,
    log_to_file,
    rotate_log_if_needed,
    ensure_config_exists,
    load_and_decrypt_config,
    validate_ip_restriction,
    show_fatal_error,
)
import views.main as ui
import views.login as login_view
from __version__ import (
    __version__,
    __release_date__,
    __author__,
    __email__,
    __license__,
    __copyright__,
    __status__,
)


class App(tk.Tk):
    """
    Main application window and initialization.

    Entry point for the Biovarase application. Initializes the database
    engine, loads configuration, and either shows the login screen or
    performs automatic authentication for generic users.

    Attributes:
        engine: Database engine instance
        info: Application information string
        _exit_in_progress: Flag to prevent concurrent exit dialogs

    Autologin Behavior:
        If autologin flag is enabled and generic user exists:
        - Automatically authenticates as generic read-only user
        - Skips login screen
        - Opens main window directly

        Otherwise:
        - Shows normal login screen
        - Requires manual authentication
    """

    def __init__(self, *args: Any, **kwargs: Dict[str, str]) -> None:
        """
        Initialize application and database engine.

        Args:
            *args: Positional arguments (unused)
            **kwargs: Database credentials from config file
                      Expected keys: user, password, database, host
        """
        super().__init__()

        self.resizable(0, 0)

        self.engine: Engine = Engine(
            user=kwargs['user'],
            password=kwargs['password'],
            database=kwargs['database'],
            host=kwargs['host']
        )

        # Context is initialized at login via init_current_ids_from_user()
        self.set_style()
        msg = "Biovarase"
        self.title(msg)
        self.set_info()
        self.set_icon()

        self._exit_in_progress: bool = False

        # Create Login frame
        obj = login_view.Login(self)

        # Try autologin, fallback to manual login on failure
        if self._try_autologin(obj):
            log_to_file("Autologin successful")
        else:
            obj.on_open()

    def _try_autologin(self, login_frame: 'login_view.Login') -> bool:
        """
        Attempt automatic login with generic viewer user.

        Args:
            login_frame: Login frame instance for UI control

        Returns:
            True if autologin succeeded, False if not available or failed

        Note:
            Autologin requires:
            1. Engine.get_autologin_flag() returns True
            2. Engine.autologin_generic_user() successfully authenticates
        """
        try:
            if not hasattr(self.engine, 'get_autologin_flag'):
                return False

            if not hasattr(self.engine, 'autologin_generic_user'):
                return False

            if not self.engine.get_autologin_flag():
                return False

            log_to_file("Attempting autologin with generic viewer user...")
            if not self.engine.autologin_generic_user():
                log_to_file("Autologin failed: generic user authentication failed", "WARNING")
                return False

            # Initialize context from autologin user's org_id
            user_org_id = self.engine.log_user.get("org_id")
            if user_org_id:
                self.engine.init_current_ids_from_user(user_org_id)
            else:
                log_to_file("Autologin user has no org_id assigned", "WARNING")

            # Autologin successful - simulate successful login
            login_frame.hide()

            # Start idle monitor if enabled for this user
            if self.engine.log_user.get("enable_time") is True:
                self.engine.thread = Monitor(login_frame)
                self.engine.thread.start()

            # Open main window
            ui.Main(login_frame).on_open()
            return True

        except (AttributeError, KeyError, TypeError) as e:
            log_to_file(f"Autologin failed with exception: {e}", "ERROR")
            return False

    def set_style(self) -> None:
        """Initialize and configure TTK style themes."""
        self.style = ttk.Style()
        self.engine.set_style(self.style)

    def set_info(self) -> None:
        """Build application information string for About dialog."""
        self.info = (
            f"{self.title()}\n"
            f"Version: {__version__}\n"
            f"Release: {__release_date__}\n"
            f"Author: {__author__}\n"
            f"Email: {__email__}\n"
            f"License: {__license__}\n"
            f"Status: {__status__}"
        )

    def set_icon(self) -> None:
        """Load and set application icon from engine."""
        icon = tk.PhotoImage(data=self.engine.get_icon())
        self.call("wm", "iconphoto", self._w, "-default", icon)

    def on_exit(self, evt: Optional[tk.Event] = None) -> None:
        """
        Handle application exit request.

        This method ensures:
        - Messagebox always appears on top
        - Dialog is not opened multiple times (concurrent protection)
        - Database connection and monitor thread are safely closed
        - Engine registry is properly cleaned up

        Args:
            evt: Tkinter event (optional)

        Behavior:
            - Shows confirmation dialog
            - On confirm: closes DB, stops monitor, quits
            - On cancel: resets exit flag, returns to application
        """
        root = self.nametowidget(".")

        # Prevent multiple concurrent exit dialogs
        if getattr(self, "_exit_in_progress", False):
            return
        self._exit_in_progress = True

        # Ensure the root window is focused and visible
        try:
            root.lift()
            root.focus_force()
        except (tk.TclError, AttributeError):
            pass

        # Confirmation dialog
        msg = _("Do you want to quit {app_name}?").format(app_name=root.title())
        answer = messagebox.askokcancel(root.title(), msg, parent=root)

        if answer:
            # Safe shutdown of database connection and monitor thread
            try:
                # Stop idle monitor thread gracefully
                if getattr(self.engine, "thread", None):
                    self.engine.thread.stop()
                    self.engine.thread.join(timeout=THREAD_JOIN_TIMEOUT)
                    if self.engine.thread.is_alive():
                        log_to_file("Idle monitor thread did not stop cleanly", "WARNING")

                # Close database connection
                if self.engine.con:
                    self.engine.con.close()
            except (AttributeError, OSError) as e:
                log_to_file(f"Error during shutdown: {e}", "ERROR")

            # Cleanup engine registry
            self.engine.batch_data = None
            self.engine.dict_instances.pop(self.winfo_name(), None)

            # Quit application
            root.quit()

        else:
            # User cancelled → allow exit dialog to be triggered again
            self._exit_in_progress = False


def main() -> None:
    """
    Application entry point.

    Workflow:
        0. Rotate log if needed (prevent disk full)
        1. Ensure config.enc exists (run setup wizard if needed)
        2. Decrypt credentials from config.enc
        3. Validate IP restriction (if configured)
        4. Launch application with credentials
    """
    # Rotate log file if it's too large (before writing anything)
    rotate_log_if_needed()

    log_to_file("=" * 60)
    log_to_file("Biovarase starting...")
    log_to_file("=" * 60)

    # Determine config.enc path (in biovarase root directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, CONFIG_FILENAME)

    # Step 1: Ensure configuration exists
    if not ensure_config_exists(config_path):
        log_to_file("Configuration setup failed. Exiting.", "ERROR")
        return

    # Step 2: Load and decrypt credentials
    creds = load_and_decrypt_config(config_path)
    if not creds:
        log_to_file("Failed to load credentials. Exiting.", "ERROR")
        return

    # Step 3: Validate IP restriction (optional)
    if not validate_ip_restriction():
        log_to_file("IP validation failed. Exiting.", "ERROR")
        return

    # Step 4: Launch application
    log_to_file("Launching Biovarase application...")
    try:
        app = App(**creds)
        app.mainloop()
    except Exception as e:
        log_to_file(f"Fatal error during application startup: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        show_fatal_error(
            f"Errore critico durante l'avvio:\n\n{e}\n\n"
            "Controlla il file log.txt per maggiori dettagli."
        )
    finally:
        log_to_file("Biovarase terminated.")
        log_to_file("=" * 60)


if __name__ == "__main__":
    main()
