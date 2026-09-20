# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk

from ui.parent_view import ParentView


class UI(ParentView):
    """Informational window for 'Z-Score, P-Value, Probability'."""

    def __init__(self, parent):
        super().__init__(parent, name="zscore")
        if self._reusing:
            return

        self.title("Z-Score, P-Value, Probability")
        self.resizable(False, False)

        self._build_ui()
        self.show(on_screen=True)

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

