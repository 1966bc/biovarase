# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk


class UI(tk.Toplevel):
    """
    Informational window for 'Z-Score, P-Value, Probability'.
    - Implements the Singleton pattern: ensures only one instance exists.
    - Layout: A Frame containing a 3-column table of Labels.
    """
    _instance = None  # class-level singleton cache

    def __new__(cls, parent):
        """Return the existing instance if alive; otherwise create a new one."""
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus)
                    return cls._instance
            except Exception as e:
                # If the underlying Tk widget is in an inconsistent state,
                # ignore and recreate a fresh instance.
                cls._instance = None
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
        """
        Guarded initializer: when the instance is reused, skip widget rebuilds.
        """
        # Prevents double initialization if the instance was retrieved from __new__
        if getattr(self, "_is_init", False):
            self.parent = parent
            return
        
        super().__init__(parent, name="zscore")
        
        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        
        self.attributes('-topmost', True)
        self.transient(parent)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)
        
        self._build_ui()
        self.engine.center_window(self, on_screen=True)
        
        self.on_open()

    def _build_ui(self):
        """Builds the user interface table."""

        main_padding = 8
        content_padding = {"padx": 10, "pady": 5} 

        # Main frame container
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=main_padding)
        self.frm_main.grid(row=0, column=0)

        # Frame for the table content
        frm_table = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_table.grid(row=0, column=0, sticky=tk.NSEW)

        # Column Headers
        headers = ("Z-Score", "P Value", "Probability")
        for c, text in enumerate(headers):
            ttk.Label(frm_table, text=text, font=('TkDefaultFont', 10, 'bold')).grid(
                row=0, column=c, sticky=tk.W, **content_padding
            )

        # Table Data
        data = [
            ("2.33", "p<0.01", "99%"),
            ("2.05", "p<0.02", "98%"),
            ("1.88", "p<0.03", "97%"),
            ("1.75", "p<0.04", "96%"),
            ("1.65", "p<0.05", "95%"),
        ]

        # Populate the table rows
        for r, row_data in enumerate(data, start=1):
            for c, text in enumerate(row_data):
                ttk.Label(frm_table, text=text).grid(
                    row=r, column=c, sticky=tk.W, **content_padding
                )

    def on_open(self):
        self.title("Z-Score, P-Value, Probability")
        
    def on_cancel(self, evt=None):
        """Handles closing (Esc, X button, or direct call) and resets the Singleton reference."""
        # Reset the Singleton reference so a new instance can be created next time.
        UI._instance = None
        self.destroy()
