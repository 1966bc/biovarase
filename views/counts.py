#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXIII  (refactor 2025-11: Calendarium v2.2, singleton polish)
#-----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from calendarium import Calendarium


class UI(tk.Toplevel):
    """
    Single-instance dialog (singleton) for exporting counts.

    - __new__ reuses the existing window if still alive.
    - __init__ is guarded to avoid rebuilding the UI on reuse.
    - Uses Calendarium v2.2 (no get_calendarium()).
    """
    _instance = None  # singleton cache

    # --- Singleton allocation ------------------------------------------------
    def __new__(cls, parent, index=None):
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    return cls._instance
            except Exception as e:
                pass
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    # --- Init once (guarded) -------------------------------------------------
    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            # Reuse path: only update parent reference
            self.parent = parent
            return

        super().__init__(name="counts")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       
        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        # Basic window config
        self.resizable(False, False)

       # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
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
            command=self._on_cancel,
        )
        btn_cancel.grid(row=1, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-c>", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

    # --- Lifecycle -----------------------------------------------------------
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
            self._on_cancel()

    def _on_cancel(self, _evt=None):
        """Close window safely and unregister from engine."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
