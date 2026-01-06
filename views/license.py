#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXIII
#-----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from views.parent_view import ParentView


class UI(ParentView):
    
    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(parent, name="license")
        self._is_init = True

        self.attributes("-topmost", True)

        self._build_ui()
        self.show(on_screen=True)

    def _build_ui(self):

        main = ttk.Frame(self, style="App.TFrame", padding=8)
        main.pack(fill=tk.BOTH, expand=True)
        self.txLicense = ScrolledText(main, wrap=tk.WORD, bg='light yellow',
                                       relief=tk.GROOVE, font='TkFixedFont')
        self.txLicense.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

    def on_open(self):

        msg = self.engine.get_license()

        if msg:
            self.txLicense.insert("1.0", msg)

        self.title(self.nametowidget(".").title())

    def on_cancel(self, _evt=None):
        type(self)._instance = None
        self.destroy()

