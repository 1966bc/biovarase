# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk

from ui.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox


class UI(ParentView):
    """
    Observations dialog (Singleton Toplevel).

    - Grid-only layout.
    - Loads current observations from engine on open.
    - Validates integer input via engine.tools.get_validate_integer().
    - Hotkeys: Alt+S (Save), Alt+C/Esc (Cancel), Enter (Save).
    """

    _instance = None  # singleton cache

    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            self.on_open()
            return

        super().__init__(parent, name="observations")

        self.transient(parent)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", self._on_close)
        self.bind("<Alt-c>", self._on_close)
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Form state
        self.observations = tk.IntVar()
        self.vcmd = self.engine.tools.get_validate_integer(self)

        # Root columns: form (col 0) + buttons (col 1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self._build_ui()
        self.show(on_screen=True)

        self._is_init = True
        self.on_open()

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 8}

        # Left: form
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.grid(row=0, column=0, sticky="nsew")

        # LabelFrame
        lf = ttk.Labelframe(frm_main, text="Set observations")
        lf.grid(row=0, column=0, sticky="nsew", **pad)
        lf.columnconfigure(0, weight=1)

        self.tx_observations = ttk.Entry(
            lf,
            width=8,
            justify=tk.CENTER,
            textvariable=self.observations,
            validate="key",
            validatecommand=self.vcmd,
        )
        self.tx_observations.grid(row=0, column=0, sticky="ew", **pad)

        # Right: buttons
        frm_btns = ttk.Frame(self, style="App.TFrame")
        frm_btns.grid(row=0, column=1, sticky="ns", **pad)
        frm_btns.columnconfigure(0, weight=1)

        ttk.Button(frm_btns, style="App.TButton", text="Save", underline=0,
                   command=self._on_save).grid(row=0, column=0, sticky="ew", **pad)
        ttk.Button(frm_btns, style="App.TButton", text="Cancel", underline=0,
                   command=self._on_close).grid(row=1, column=0, sticky="ew", **pad)

        # Keep a reference for optional global validation
        self.frm_main = frm_main

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------
    def on_open(self):
        """Populate current value and set focus."""
        self.title("Observations")
        try:
            self.observations.set(self.engine.get_observations())
        except Exception as e:
            # Fallback to zero if engine getter is unavailable
            self.observations.set(0)
        self.tx_observations.focus()

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------
    def _on_save(self, _evt=None):
        """Validate and persist observations, then notify parent and close."""
        # Optional global validation hook
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.tools.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

        if not messagebox.askyesno(self.engine.app_title,
                                   getattr(self.engine, "ask_to_save", "Do you want to save?"),
                                   parent=self):
            return

        try:
            value = int(self.observations.get())
        except (TypeError, ValueError) as e:
            messagebox.showwarning(self.engine.app_title, "Please enter a valid integer.", parent=self)
            self.tx_observations.focus_set()
            return

        try:
            self.engine.set_observations(value)
            if hasattr(self.parent, "set_observations"):
                self.parent.set_observations()
        except Exception as exc:
            messagebox.showerror(self.engine.app_title, f"Save error:\n{exc}", parent=self)
            return

        self._on_close()

    def _on_close(self, _evt=None):
        """Close the window and clear the singleton reference."""
        type(self)._instance = None
        self.destroy()
