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
from ui.calendarium import Calendarium


class UI(ParentView):
    """
    Single-instance dialog (singleton) for exporting counts.

    - __new__ reuses the existing window if still alive.
    - __init__ is guarded to avoid rebuilding the UI on reuse.
    - Uses Calendarium v2.2 (no get_calendarium()).
    """
    _instance = None  # singleton cache

    # --- Singleton allocation ------------------------------------------------

    # --- Init once (guarded) -------------------------------------------------
    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(parent, name="counts")
        self._is_init = True

        self.resizable(False, False)

        self._build_ui()
        self.show()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        
    # --- UI builder ----------------------------------------------------------
    def _build_ui(self):
        padd = {"padx": 5, "pady": 5}

        # Main container
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        # Left side
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **padd)

        # Date selector (Calendarium v2.2: no get_calendarium())
        self.export_date = Calendarium(frm_left, "Export from:")
        self.export_date.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W,
            padx=5,
            pady=5,
        )

        # Right side (buttons)
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky=tk.NS, **padd)

        btn_export = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Export",
            underline=0,
            command=self.on_export,
        )
        btn_export.grid(row=0, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-e>", self.on_export)

        btn_cancel = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        )
        btn_cancel.grid(row=1, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-c>", self.on_cancel)    # --- Lifecycle -----------------------------------------------------------
    def on_open(self):
        """Called by parent to (re)show the dialog."""

        self.title("Export Counts")

        # Prefill: today
        try:
            self.export_date.set_today()
        except Exception as e:
            pass

        self.after_idle(self._focus_calendar)

    def _focus_calendar(self):
        """Give focus to the Calendarium widget (best-effort)."""
        try:
            self.export_date.focus_set()
        except Exception as e:
            pass

    def _get_selected_date(self):
        """
        Return the selected date from Calendarium in a safe, backward-compatible way.

        Supports both historical signatures:
            - get_date(parent)
            - get_date()

        Returns:
            Any | None:
                - A valid date/representation as returned by Calendarium, or
                - None if the date is invalid / not selected.
        """
        try:
            # Legacy API: get_date(parent)
            value = self.export_date.get_date(self)
        except TypeError:
            # Current API: get_date()
            value = self.export_date.get_date()
        except Exception as e:
            return None

        # Historical behaviour: False means "invalid"
        if value is False:
            return None

        return value

    # --- Actions -------------------------------------------------------------
    def on_export(self, evt=None):
        """Validate the date, confirm, and trigger engine export."""
        selected_date = self._get_selected_date()
        if selected_date is None:
            return

        if messagebox.askyesno(self.engine.app_title, "Export data?", parent=self):
            args = (selected_date,)  # tuple(date,)
            self.engine.get_counts(args)
            self.on_cancel()

    def on_cancel(self, evt=None):
        """Close window."""
        super().on_cancel(evt)
