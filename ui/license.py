#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL Version 3, 29 June 2007
Version: 4.2 (Professional Edition)
"""
import tkinter as tk
from tkinter import ttk

from ui.parent_view import ParentView


class UI(ParentView):
    """License display window (singleton)."""

    def __init__(self, parent):
        super().__init__(parent, name="license")

        if self._reusing:
            return

        self._build_ui()
        self.show()

    def _build_ui(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Text widget with scrollbar
        text_frame = ttk.Frame(main)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.txLicense = tk.Text(
            text_frame,
            width=80,
            height=25,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Courier", 9)
        )
        self.txLicense.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.txLicense.yview)

    def on_open(self):
        msg = self.engine.get_license()

        if msg:
            self.txLicense.insert("1.0", msg)
            self.txLicense.config(state=tk.DISABLED)

        self.title("License - GNU GPL v3")

    def on_cancel(self, _evt=None):
        """Close the window."""
        super().on_cancel()

