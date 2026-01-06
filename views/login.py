#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Login Window for Biovarase Laboratory QC Management System.

This module provides the authentication interface and application entry point
for Biovarase. It handles user login, autologin functionality, and idle
monitoring for automatic logout.

Features:
- Manual login with username/password authentication
- Automatic login for read-only generic users
- Idle time monitoring with automatic logout
- Database credential loading from config file
- Session management and application initialization

Classes:
    Monitor: Background thread for idle time monitoring
    Login: Login form frame with authentication logic
    App: Main application window and initialization

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL Version 3, 29 June 2007
"""
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
# -----------------------------------------------------------------------------
import os
import sys
import socket
import threading
import datetime
from time import sleep
from typing import Dict, Tuple, Optional, Any
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from engine import Engine
import views.main as ui
from security import decrypt_config
from setup_wizard import SetupWizard

__author__ = "1966bc"
__copyright__ = "Copyleft"
__credits__ = ["hal9000", ]
__license__ = "GNU GPL Version 3, 29 June 2007"
__version__ = "42"
__maintainer__ = "1966bc"
__email__ = "giuseppecostanzi@gmail.com"
__date__ = "ver MMXXV"
__status__ = "Testing"

# Configuration constants
CONFIG_FILENAME = "config.enc"
MAX_LOGIN_ATTEMPTS = 3
IDLE_MONITOR_POLL_INTERVAL = 1  # seconds
THREAD_JOIN_TIMEOUT = 2.0  # seconds
DB_CONNECTION_TIMEOUT = 5  # seconds
LOG_MAX_SIZE_MB = 10  # Maximum log file size before rotation
LOG_KEEP_COUNT = 5  # Number of old log files to keep


def log_to_file(message: str, level: str = "INFO") -> None:
    """
    Simple logging to log.txt before Engine is available.

    This is used during startup before Engine.on_log() is accessible.
    Once Engine is created, use engine.on_log() for exception logging.

    Args:
        message: Log message
        level: Log level (INFO, WARNING, ERROR, DEBUG)
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} - login.py - {level} - {message}\n"

        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(log_line)

        # Also print to console for visibility
        print(f"[{level}] {message}")
    except Exception:
        # Fail silently - never let logging crash the app
        pass


def cleanup_old_logs(keep: int = LOG_KEEP_COUNT) -> None:
    """
    Remove old rotated log files, keeping only the most recent ones.

    Args:
        keep: Number of old log files to keep (default: LOG_KEEP_COUNT)

    Note:
        Log files are named: log_YYYYMMDD_HHMMSS.txt
        Files are sorted by name (which corresponds to timestamp)
    """
    try:
        import glob

        # Find all rotated log files (pattern: log_*.txt)
        log_files = glob.glob("log_*.txt")

        if len(log_files) <= keep:
            # Nothing to clean up
            return

        # Sort by filename (timestamp embedded in name)
        # Newest files have later timestamps
        log_files.sort()

        # Calculate how many to delete
        to_delete = log_files[: len(log_files) - keep]

        # Delete old log files
        for old_log in to_delete:
            try:
                os.remove(old_log)
                print(f"[INFO] Deleted old log file: {old_log}")
            except OSError:
                # Fail silently if deletion fails
                pass

    except Exception:
        # Never let cleanup crash the app
        pass


def rotate_log_if_needed() -> None:
    """
    Rotate log.txt if it exceeds LOG_MAX_SIZE_MB.

    Rotation process:
        1. Check if log.txt exists and size > LOG_MAX_SIZE_MB
        2. Rename log.txt to log_YYYYMMDD_HHMMSS.txt
        3. Clean up old rotated logs (keep only LOG_KEEP_COUNT)

    This prevents disk space issues and keeps logs manageable.
    Safe to call on every application start.
    """
    try:
        log_file = "log.txt"

        # Check if log file exists
        if not os.path.exists(log_file):
            return

        # Check file size in MB
        size_bytes = os.path.getsize(log_file)
        size_mb = size_bytes / (1024 * 1024)

        if size_mb <= LOG_MAX_SIZE_MB:
            # Log file is still small enough
            return

        # Rotate: rename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_name = f"log_{timestamp}.txt"

        os.rename(log_file, rotated_name)
        print(f"[INFO] Log rotated: {log_file} -> {rotated_name} ({size_mb:.2f} MB)")

        # Clean up old logs
        cleanup_old_logs(keep=LOG_KEEP_COUNT)

    except Exception as e:
        # Fail silently - never let rotation crash the app
        print(f"[WARNING] Log rotation failed: {e}")
        pass


def load_credentials_from_file(file_path: str) -> Dict[str, str]:
    """
    Load database credentials from a text file.

    Args:
        file_path: Path to the credentials file.
                   Expected format: 'key=value' per line.

    Returns:
        Dictionary containing credentials, or empty dict on error.

    Example:
        File contents:
            user=biovarase
            password=secret
            database=biovarase
            host=localhost

    Note:
        - Lines without '=' are ignored
        - Whitespace is stripped from keys and values
        - FileNotFoundError is caught and logged
    """
    credentials: Dict[str, str] = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Error: Credentials file '{file_path}' not found.")
    except IOError as e:
        print(f"Error reading credentials file: {e}")
    except Exception as e:
        print(f"Unexpected error loading credentials: {e}")
    return credentials

def get_current_ip() -> str:
    """
    Return current primary IPv4 address of this machine.
    Used for optional IP-based checks.
    """
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except OSError:
        return "0.0.0.0"


def show_fatal_error(message: str) -> None:
    """
    Show a fatal error messagebox and exit.

    Creates a temporary hidden root just for the dialog,
    then terminates the process.
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Biovarase", message, parent=root)
    root.destroy()


def run_first_time_setup(config_path: str) -> bool:
    """
    Run the SetupWizard to create config.enc.

    Args:
        config_path: Absolute path where config.enc must be created
                     (es. .../biovarase/config.enc)

    Returns:
        True if setup was completed and config.enc exists, False otherwise.
    """
    parent_dir = os.path.dirname(config_path)

    # Temporary root dedicated to the wizard
    root = tk.Tk()
    root.title("Biovarase – Configurazione iniziale")
    root.update_idletasks()      # ensure geometry is initialized
    root.withdraw()              # hide the empty root window

    old_cwd = os.getcwd()
    try:
        # Change working dir so setup_wizard writes config.enc
        # in the expected folder.
        os.chdir(parent_dir)

        log_to_file(f"Creating setup wizard in directory: {os.getcwd()}")
        log_to_file(f"Config will be saved to: {config_path}")

        wizard = SetupWizard(root)

        # Force wizard to show on Linux (withdrawn parent + transient child issue)
        wizard.deiconify()
        wizard.lift()
        wizard.focus_force()

        log_to_file("Waiting for user to complete setup wizard...")
        wizard.wait_window()

        success = getattr(wizard, 'success', False)
        log_to_file(f"Wizard closed. Setup completed: {success}")
    except Exception as e:
        log_to_file(f"Exception during setup wizard: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(old_cwd)
        root.destroy()

    # Success only if wizard.success and the file really exists
    result = bool(getattr(wizard, "success", False) and os.path.exists(config_path))
    return result


class Monitor(threading.Thread):
    """
    Background thread that monitors user idle time.

    Tracks mouse movements to detect user activity. If the user remains
    idle for longer than their configured timeout period, automatically
    triggers logout.

    Attributes:
        check: Flag to control thread execution
        parent: Parent widget to monitor
        idle: Seconds of inactivity
        old_coord: Previous mouse coordinates

    Note:
        - Polls mouse position every second
        - Timeout is read from user's elapsing_time setting
        - Thread stops on logout or manual stop() call
    """

    def __init__(self, parent: tk.Widget) -> None:
        """
        Initialize the idle monitor thread.

        Args:
            parent: Parent widget (typically Login frame)
        """
        threading.Thread.__init__(self)

        self.check: bool = True
        self.parent: tk.Widget = parent
        self.idle: int = 0
        self.old_coord: Optional[Tuple[int, int]] = None

    def stop(self) -> None:
        """Stop the monitoring thread."""
        self.check = False

    def run(self) -> None:
        """
        Main monitoring loop.

        Continuously polls mouse position and compares with previous
        position. Increments idle counter when no movement detected.
        Triggers logout when idle time exceeds user's timeout setting.
        """
        while self.check:

            if not self.check:
                break
            else:
                coord = self.parent.winfo_pointerxy()

                if self.old_coord != coord:
                    self.old_coord = coord
                    self.idle = 0
                else:
                    self.idle += 1

                # Get timeout in minutes, convert to seconds
                timeout_minutes = int(
                    self.parent.nametowidget(".").engine.log_user["elapsing_time"]
                )
                timeout_seconds = timeout_minutes * 60

                if self.idle == timeout_seconds:
                    self.check = False
                    self.parent.after(1000, self.parent.on_quit)
                else:
                    sleep(IDLE_MONITOR_POLL_INTERVAL)


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

        self.nametowidget(".").engine.dict_instances[self.winfo_name()] = self
        self.parent: tk.Widget = parent
        self.parent.protocol("WM_DELETE_WINDOW",
                             self.nametowidget(".").on_exit)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.nick: tk.StringVar = tk.StringVar()
        self.password: tk.StringVar = tk.StringVar()
        self.attempts: int = 0
        self.nametowidget(".").engine.thread = None
        self.center_me()
        self.init_ui()

    def center_me(self) -> None:
        """Center window on the screen."""
        x = (self.parent.winfo_screenwidth() - self.parent.winfo_reqwidth()) / 2
        y = (self.parent.winfo_screenheight() - self.parent.winfo_reqheight()) / 2
        self.parent.geometry("+%d+%d" % (x, y))

    def init_ui(self) -> None:
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
        ttk.Label(w, text="Login:",).grid(row=r, sticky=tk.W, **paddings)
        self.txtNick = ttk.Entry(w, textvariable=self.nick,)
        self.txtNick.grid(row=r, column=c, **paddings)

        r += 1
        ttk.Label(w, text="Password:",).grid(row=r, sticky=tk.W, **paddings)
        ent_password = ttk.Entry(w, show="*", textvariable=self.password)
        ent_password.grid(row=r, column=c, **paddings)
        ent_password.bind("<Return>", self.on_login)
        ent_password.bind("<KP_Enter>", self.on_login)

        r += 1
        c = 0
        btn_login = ttk.Button(w, style="App.TButton", text="Login", underline=0)
        btn_login.bind("<Return>", self.on_login)
        btn_login.bind("<Button-1>", self.on_login)
        btn_login.bind("<Alt-l>", self.on_login)
        self.parent.bind("<Alt-l>", self.on_login)
        btn_login.grid(row=r, column=c, sticky=tk.W, **paddings)

        c += 1
        btn_exit = ttk.Button(w, style="App.TButton", text="Cancel", underline=0)
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
        # Encode to bytes using UTF-8 for bcrypt
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
            - Exits after 3 failed attempts
        """
        if self.nametowidget(".").engine.on_fields_control(
            self.frm_main,
            self.nametowidget(".").title()
        ) == False:
            return

        nick, password = self.get_values()

        rs = self.nametowidget(".").engine.on_login((nick, password))

        if rs:
            self.nametowidget(".").engine.set_log_user(rs)
            self.hide()

            # Start idle monitor if enabled for this user
            if self.nametowidget(".").engine.log_user["enable_time"] == True:
                self.nametowidget(".").engine.thread = Monitor(self)
                self.nametowidget(".").engine.thread.start()

            ui.Main(self).on_open()

        else:
            msg = "Login failed."
            messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)

            self.attempts += 1

            if self.attempts >= MAX_LOGIN_ATTEMPTS:
                msg = f"Maximum login attempts ({MAX_LOGIN_ATTEMPTS}) exceeded.\nContact system administrator."
                messagebox.showwarning(self.nametowidget(".").title(), msg, parent=self)
                self.on_quit()
            else:
                self.txtNick.focus()

    def on_about(self) -> None:
        """Display application information dialog."""
        messagebox.showinfo(self.nametowidget(".").title(),
                            self.nametowidget(".").info,
                            parent=self)

    def on_quit(self, evt: Optional[tk.Event] = None) -> None:
        """
        Close database connection and quit application.

        Args:
            evt: Tkinter event (optional)
        """
        self.nametowidget(".").engine.con.close()
        self.quit()


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

        self.engine.load_context_ids()

        self.set_style()
        msg = "Biovarase"
        self.title(msg)
        self.set_info()
        self.set_icon()

        self._exit_in_progress: bool = False

        # Always create Login frame (keeps current behavior intact)
        obj = Login(self)

        # Try autologin, fallback to manual login on failure
        if self._try_autologin(obj):
            log_to_file("Autologin successful")
        else:
            obj.on_open()

    def _try_autologin(self, login_frame: 'Login') -> bool:
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
            # Check if Engine supports autologin methods
            if not hasattr(self.engine, 'get_autologin_flag'):
                return False

            if not hasattr(self.engine, 'autologin_generic_user'):
                return False

            # Check if autologin is enabled
            if not self.engine.get_autologin_flag():
                return False

            # Attempt autologin
            log_to_file("Attempting autologin with generic viewer user...")
            if not self.engine.autologin_generic_user():
                log_to_file("Autologin failed: generic user authentication failed", "WARNING")
                return False

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
        msg = (
            "{0}\nauthor: {1}\ncopyright: {2}\ncredits: {3}\nlicense: {4}\n"
            "version: {5}\nmaintainer: {6}\nemail: {7}\ndate: {8}\nstatus: {9}"
        )
        self.info = msg.format(
            self.title(),
            __author__,
            __copyright__,
            __credits__,
            __license__,
            __version__,
            __maintainer__,
            __email__,
            __date__,
            __status__
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
            root.lift()           # Bring window to front
            root.focus_force()    # Request keyboard focus
        except (tk.TclError, AttributeError) as e:
            pass  # Focus handling must never raise errors

        # Confirmation dialog
        msg = f"Do you want to quit {root.title()}?"
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
                pass  # Never interrupt shutdown on errors

            # Cleanup engine registry
            self.engine.batch_data = None
            self.engine.dict_instances.pop(self.winfo_name(), None)

            # Quit application
            root.quit()

        else:
            # User cancelled → allow exit dialog to be triggered again
            self._exit_in_progress = False


def ensure_config_exists(config_path: str) -> bool:
    """
    Ensure config.enc exists, running setup wizard if needed.

    Args:
        config_path: Absolute path to config.enc file

    Returns:
        True if config.enc exists (created or already present), False otherwise
    """
    if os.path.exists(config_path):
        log_to_file(f"Configuration file found: {config_path}")
        return True

    log_to_file("Configuration file not found. Starting first-time setup...", "WARNING")
    success = run_first_time_setup(config_path)

    if not success:
        show_fatal_error(
            "Configurazione non completata.\n\n"
            "Il setup iniziale è stato annullato o non è riuscito.\n"
            "Biovarase verrà chiuso.\n\n"
            "Riavvia l'applicazione per riprovare."
        )
        return False

    log_to_file("First-time setup completed successfully")
    return True


def load_and_decrypt_config(config_path: str) -> Optional[Dict[str, str]]:
    """
    Load and decrypt database credentials from config.enc.

    Args:
        config_path: Absolute path to config.enc file

    Returns:
        Dictionary with credentials (user, password, database, host) or None on error
    """
    log_to_file("Decrypting configuration file...")
    creds = decrypt_config(config_path)

    if not creds:
        show_fatal_error(
            "Impossibile leggere config.enc.\n\n"
            "Motivi possibili:\n"
            "- File corrotto\n"
            "- File creato su un'altra macchina (hardware diverso)\n\n"
            "Ricrea la configurazione con il setup wizard."
        )
        return None

    log_to_file("Configuration decrypted successfully")
    return creds


def validate_ip_restriction() -> bool:
    """
    Validate IP restriction if BIOVARASE_SERVER_IP environment variable is set.

    Returns:
        True if no restriction or IP matches, False if IP mismatch
    """
    expected_ip = os.environ.get("BIOVARASE_SERVER_IP")

    if not expected_ip:
        # No IP restriction configured
        return True

    current_ip = get_current_ip()
    log_to_file(f"IP restriction enabled. Expected: {expected_ip}, Current: {current_ip}")

    if current_ip != expected_ip:
        show_fatal_error(
            f"IP corrente ({current_ip}) diverso dall'IP autorizzato ({expected_ip}).\n\n"
            "Controlla la configurazione di rete o aggiorna l'IP autorizzato."
        )
        return False

    log_to_file("IP validation passed")
    return True


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

    # Determine config.enc path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_path = os.path.join(parent_dir, CONFIG_FILENAME)

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
