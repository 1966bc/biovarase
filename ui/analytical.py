# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk

from i18n import _
from ui.parent_view import ParentView

class UI(ParentView):

    """
    Informational window for 'Analytical Goals Explained'.
    - Implements the Singleton pattern: ensures only one instance exists.
    - Layout: A Frame containing a 3-column table of Labels.
    """
    _instance = None  # cache singleton

    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(parent, name="analytical")
        self._is_init = True

        self.title(_("Analytical Goals Explained"))
        self.transient(parent)
        self.resizable(0, 0)

        self._build_ui()
        self.show(on_screen=True)
        
    def _build_ui(self):
        """Builds the user interface"""
        w = ttk.Frame(self, style="App.TFrame")
        w.columnconfigure(0, weight=1)
        w.columnconfigure(1, weight=2)
        w.columnconfigure(2, weight=1)
        w.grid(row=0, column=0, sticky=tk.N + tk.W + tk.S + tk.E)

        # Colonna 1: k CV
        items_cv = (("k CV:", None), ("0.25", "green"), ("0.50", "yellow"), ("0.75", "red"),)
        r = 0
        c = 0
        for text, color in items_cv:
            tk.Label(w, bg=color, text=text, anchor=tk.W).grid(row=r, column=c, sticky=tk.W, padx=10, pady=5)
            r += 1

        # Colonna 2: k Bias
        items_bias = (("k Bias:", None), ("0.125<= k <= 0.25", "green"),
                      ("0.25<= k <= 0.375", "yellow"), ("k > 0.375", "red"),)
        r = 0
        c = 1
        for text, color in items_bias:
            tk.Label(w, bg=color, text=text, anchor=tk.W).grid(row=r, column=c, sticky=tk.W, padx=10, pady=5)
            r += 1

        # Colonna 3: Eta (Errore Totale)
        items_eta = ((_("Total Error (TEa):"), None),
                     ("ETa < 1.65 (0.25 CVi) + 0.125 (CVi² + CVg²) ½ ", "green"),
                     ("ETa < 1.65 (0.50 CVi) + 0.25 (CVi² + CVg²) ½", "yellow"),
                     ("ETa < 1.65 (0.75 CVi) + 0.375 (CVi² + CVg²) ½", "red"),)
        r = 0
        c = 2
        for text, color in items_eta:
            tk.Label(w, bg=color, text=text, anchor=tk.W).grid(row=r, column=c, sticky=tk.W, padx=10, pady=5)
            r += 1


    def on_open(self):
        """Ensures the window is visible, in front, and focused, useful when reusing a Singleton."""
        try:
            self.transient(self.parent)
        except Exception as e:
            pass
            
        self.deiconify()  # Ensure it's not minimized
        self.lift()       # Bring to the top
        self.after_idle(self.focus_set)

    def on_cancel(self, evt=None):
        """Handles closing (Esc, X button, or direct call) and resets the Singleton reference."""
        # Reset the Singleton reference so a new instance can be created next time.
        UI._instance = None
        self.destroy()
        
