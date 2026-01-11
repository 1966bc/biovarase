#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Configuration Module for Biovarase.

Provides utilities for:
- Logging (before Engine is available)
- Log rotation and cleanup
- Configuration file management (config.enc)
- First-time setup wizard launching
- IP validation

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import os
import datetime
import socket
import glob
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional

from security import decrypt_config
from setup_wizard import SetupWizard

# Configuration constants
CONFIG_FILENAME = "config.enc"
MAX_LOGIN_ATTEMPTS = 3
BATCH_DESCRIPTION_MAX_LENGTH = 15  # Matches DB batches.description VARCHAR(15)
LOT_NUMBER_MAX_LENGTH = 20  # Matches DB batches.lot_number VARCHAR(30)
IDLE_MONITOR_POLL_INTERVAL = 1  # seconds
THREAD_JOIN_TIMEOUT = 2.0  # seconds
DB_CONNECTION_TIMEOUT = 5  # seconds
LOG_MAX_SIZE_MB = 10  # Maximum log file size before rotation
LOG_KEEP_COUNT = 5  # Number of old log files to keep

# Main window minimum dimensions (UI design constraint)
MAIN_WINDOW_MIN_WIDTH = 1200
MAIN_WINDOW_MIN_HEIGHT = 700


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
        log_line = f"{timestamp} - app_config.py - {level} - {message}\n"

        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(log_line)

        print(f"[{level}] {message}")
    except Exception:
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
        log_files = glob.glob("log_*.txt")

        if len(log_files) <= keep:
            return

        log_files.sort()
        to_delete = log_files[: len(log_files) - keep]

        for old_log in to_delete:
            try:
                os.remove(old_log)
                print(f"[INFO] Deleted old log file: {old_log}")
            except OSError:
                pass

    except Exception:
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

        if not os.path.exists(log_file):
            return

        size_bytes = os.path.getsize(log_file)
        size_mb = size_bytes / (1024 * 1024)

        if size_mb <= LOG_MAX_SIZE_MB:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_name = f"log_{timestamp}.txt"

        os.rename(log_file, rotated_name)
        print(f"[INFO] Log rotated: {log_file} -> {rotated_name} ({size_mb:.2f} MB)")

        cleanup_old_logs(keep=LOG_KEEP_COUNT)

    except Exception as e:
        print(f"[WARNING] Log rotation failed: {e}")


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

    root = tk.Tk()
    root.title("Biovarase – Configurazione iniziale")
    root.update_idletasks()
    root.withdraw()

    old_cwd = os.getcwd()
    try:
        os.chdir(parent_dir)

        log_to_file(f"Creating setup wizard in directory: {os.getcwd()}")
        log_to_file(f"Config will be saved to: {config_path}")

        wizard = SetupWizard(root)

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

    result = bool(getattr(wizard, "success", False) and os.path.exists(config_path))
    return result


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
