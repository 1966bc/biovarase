#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idle Monitor Module for Biovarase.

Provides a background thread that monitors user idle time and
triggers automatic logout after a configurable timeout period.

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import threading
from time import sleep
from typing import Optional, Tuple
import tkinter as tk

# Constants
IDLE_MONITOR_POLL_INTERVAL = 1  # seconds


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

            # Check if parent window still exists
            try:
                if not self.parent.winfo_exists():
                    self.check = False
                    break
                coord = self.parent.winfo_pointerxy()
            except tk.TclError:
                # Window was destroyed
                self.check = False
                break

            if self.old_coord != coord:
                self.old_coord = coord
                self.idle = 0
            else:
                self.idle += 1

            # Get timeout in minutes, convert to seconds
            try:
                timeout_minutes = int(
                    self.parent.nametowidget(".").engine.log_user["elapsing_time"]
                )
                timeout_seconds = timeout_minutes * 60

                if self.idle == timeout_seconds:
                    self.check = False
                    self.parent.after(1000, self.parent.on_quit)
                else:
                    sleep(IDLE_MONITOR_POLL_INTERVAL)
            except (tk.TclError, KeyError):
                # Window destroyed or user logged out
                self.check = False
                break
