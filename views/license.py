#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXIII
#-----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk


class UI(tk.Toplevel):
    
    _instance = None

    def __new__(cls, parent, index=None):
        # Reuse a living instance if present, otherwise create a new one.
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                cls._instance = None  # stale reference; recreate
        obj = super().__new__(cls)
        cls._instance = obj
        return obj
    
    def __init__(self, parent):
        # Prevent double initialization when the singleton is reused
        if getattr(self, "_is_init", False):
            self.parent = parent
            return
        
        super().__init__(name="license")

        self.parent = parent
        self.engine = self.nametowidget(".").engine
        #self.resizable(0, 0)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)
        
        self._build_ui()
        self.engine.center_window_on_screen(self)
        self._is_init = True

    def _build_ui(self):

        main = ttk.Frame(self, style="App.TFrame", padding=8)
        main.pack(fill=tk.BOTH, expand=True)
        self.txLicense = self.engine.get_text_box(main,)

    def on_open(self):

        msg = self.engine.get_license()

        if msg:
            self.txLicense.insert("1.0", msg)

        self.title(self.nametowidget(".").title())

    def on_cancel(self, _evt=None):
        type(self)._instance = None
        self.destroy()

