# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
# -----------------------------------------------------------------------------
import tkinter as tk

class UI(tk.Toplevel):

    """
    Informational window for 'Analytical Goals Explained'.
    - Implements the Singleton pattern: ensures only one instance exists.
    - Layout: A Frame containing a 3-column table of Labels.
    """
    _instance = None  # cache singleton

    def __new__(cls, parent):
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                # Instance might be dead, but reference not cleared; force recreation
                cls._instance = None                 
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
        # Prevents double initialization if the instance was retrieved from __new__
        if getattr(self, "_is_init", False):
            self.parent = parent
            return
            
        super().__init__(name="analytical")

        self._is_init = True
        self.engine = self.nametowidget(".").engine
        self.parent = parent
        
        # Window configuration
        self.title("Analytical Goals Explained")
        
        self.transient(parent)
        self.resizable(0, 0)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)
        
        self._init_ui()
        self.engine.center_window_on_screen(self)
        
    def _init_ui(self):
    
        """Builds the user interface"""
        w = self.engine.get_init_ui(self)

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
        items_eta = (("Errore Totale (ETa):", None),
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
        
