# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------
import tkinter as tk

from i18n import _
from views.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox


class UI(ParentView):
    """
    Z-score dialog (Singleton Toplevel).

    - Grid-only layout.
    - Loads current z-score from engine on open.
    - Hotkeys: Alt+S (Save), Alt+C/Esc (Cancel), Enter (Save).
    """

    _instance = None  # singleton cache

    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            self.on_open()
            return

        super().__init__(parent, name="zscore")

        self.transient(parent)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", self._on_close)
        self.bind("<Alt-c>", self._on_close)
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Form state
        self.z_score = tk.DoubleVar()
        self.float_vcmd = self.engine.get_float_vcmd(self)

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

        # Left: form container
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.grid(row=0, column=0, sticky="nsew")

        lf = ttk.Labelframe(frm_main, text=_("Set z-score"))
        lf.grid(row=0, column=0, sticky="nsew", **pad)
        lf.columnconfigure(0, weight=1)

        self.tx_value = ttk.Entry(
            lf,
            width=8,
            justify=tk.CENTER,
            textvariable=self.z_score,
            validate="key",
            validatecommand=self.float_vcmd,
        )
        self.tx_value.grid(row=0, column=0, sticky="ew", **pad)

        # Right: buttons
        frm_btns = ttk.Frame(self, style="App.TFrame")
        frm_btns.grid(row=0, column=1, sticky="ns", **pad)
        frm_btns.columnconfigure(0, weight=1)

        ttk.Button(frm_btns, style="App.TButton", text=_("Save"), underline=0,
                   command=self._on_save).grid(row=0, column=0, sticky="ew", **pad)
        ttk.Button(frm_btns, style="App.TButton", text=_("Cancel"), underline=0,
                   command=self._on_close).grid(row=1, column=0, sticky="ew", **pad)

        # Keep a reference for optional global validation
        self.frm_main = frm_main

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------
    def on_open(self):
        """Populate current value and set focus."""
        self.title(_("Set Z-score"))
        try:
            self.z_score.set(self.engine.get_zscore())
        except Exception as e:
            # Fallback: default to 0.0 if engine getter is unavailable
            self.z_score.set(0.0)
        self.tx_value.focus()

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------
    def _on_save(self, _evt=None):
        """Validate and persist z-score, then notify parent and close."""
        # Optional global validation hook
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

        if not messagebox.askyesno(self.engine.app_title,
                                   getattr(self.engine, "ask_to_save", "Do you want to save?"),
                                   parent=self):
            return

        try:
            value = float(self.z_score.get())
        except (TypeError, ValueError) as e:
            messagebox.showwarning(self.engine.app_title, _("Please enter a valid number."), parent=self)
            self.tx_value.focus_set()
            return

        try:
            self.engine.set_zscore(value)
            if hasattr(self.parent, "set_zscore"):
                self.parent.set_zscore()
        except Exception as exc:
            messagebox.showerror(self.engine.app_title, f"{_('Save error:')}\n{exc}", parent=self)
            return

        self._on_close()

    def _on_close(self, _evt=None):
        """Close the window and clear the singleton reference."""
        type(self)._instance = None
        self.destroy()
