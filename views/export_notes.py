# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXIII
# -----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from calendarium import Calendarium


class UI(tk.Toplevel):

    _instance = None

    def __new__(cls, parent):
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                cls._instance = None
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    
    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(name="export_notes")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       
        
        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        # Basic window config
        self.title("Export Notes Data")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)
        self.bind("<Alt-c>", self.on_cancel)


         # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window(self, on_screen=True)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def _build_ui(self):

        padd = {"padx": 5, "pady": 5}

        # Main container
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        # Left side
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **padd)

        # Date selector (Calendarium v2.2 API: no get_calendarium())
        self.start_date = Calendarium(frm_left, "Export from:")
        self.start_date.grid(
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
            command=self._on_export,
        )
        btn_export.grid(row=0, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-e>", self._on_export)

        btn_cancel = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        )
        btn_cancel.grid(row=1, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-c>", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)

        self.after_idle(self._focus_calendar)

    # --- Lifecycle ------------------------------------------------------------
    def on_open(self):
        """
        - Re-sync transient parent.
        - Reset date to today.
        - Bring the window to the front.
        """
        try:
            self.transient(self.parent)
        except Exception as e:
            pass

        # Prefill date with today
        try:
            self.start_date.set_today()
        except Exception as e:
            pass

        self.after_idle(self._focus_calendar)

    def _focus_calendar(self):
        """Give focus to the Calendarium widget, best effort."""
        try:
            self.start_date.focus_set()
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
  
        # Current API: get_date()
        try:
            value = self.start_date.get_date()
        except Exception as e:
            return None
   
        # Historical behaviour: False means "invalid"
        if value is False:
            return None

        return value

    # --- Actions --------------------------------------------------------------
    def _on_export(self, evt=None):
        """
        Validate the date, ask for confirmation, and trigger engine export.
        """
        selected_date = self._get_selected_date()
        if selected_date is None:
            # Invalid or missing date → do nothing.
            return

        if not messagebox.askyesno(
            self.engine.app_title,
            "Export data?",
            parent=self,
        ):
            return

        args = (selected_date, self.engine.get_section_id())

        try:
            # Optional: show busy state if Engine provides it
            if hasattr(self.engine, "busy"):
                self.engine.busy(self)
            self.engine.get_notes(args)
        except Exception as exc:
            try:
                self.engine.on_log(
                    "export_notes._on_export:get_notes",
                    exc,
                    type(exc),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass

            messagebox.showerror(
                self.engine.app_title,
                f"Export error:\n{exc}",
                parent=self,
            )
        finally:
            try:
                if hasattr(self.engine, "not_busy"):
                    self.engine.not_busy(self)
            except Exception as e:
                pass

        self.on_cancel()

    def on_cancel(self, _evt=None):
        """Close window safely and unregister from engine."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
