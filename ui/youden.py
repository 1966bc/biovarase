# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV  (rewritten to use YoudenPlotCanvas)
#-----------------------------------------------------------------------------

"""Youden module of Biovarase — rewritten to use pure Tkinter Canvas."""

import tkinter as tk

from ui.parent_view import ParentView
from tkinter import ttk

from youden_canvas import YoudenPlotCanvas


class UI(ParentView):
    """
    Youden plot window.
    Uses YoudenPlotCanvas instead of Matplotlib.
    """

    def __init__(self, parent):
        super().__init__(parent, name="youden")
        if self._reusing:
            return

        self.engine = self.nametowidget(".").engine

        self.title("Youden Plot")
        
        self.batches = []
        self.um = None
        self._cached_args = None

        self.test_name_var = tk.StringVar(value="")
        self.ws_name_var   = tk.StringVar(value="")
        self.ws_serial_var = tk.StringVar(value="")

        self.show_labels_var = tk.BooleanVar(value=False)

        self._build_ui()
        # Set initial size BEFORE centering
        self.geometry("700x500")
        self.minsize(600, 400)
        self.show()
        
    # ----------------------------------------------------------------------
    # UI builder
    # ----------------------------------------------------------------------
    def _build_ui(self):
        

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # ---------------- HEADER ----------------
        hdr = ttk.Frame(self, style="App.TFrame", padding=(8, 6))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ttk.Label(hdr, text="Test:", style="App.TLabel")\
            .grid(row=0, column=0, sticky="w")
        ttk.Label(hdr, textvariable=self.test_name_var)\
            .grid(row=0, column=1, sticky="w")

        ttk.Label(hdr, text="Workstation:", style="App.TLabel")\
            .grid(row=0, column=2, sticky="w", padx=(16, 6))
        ttk.Label(hdr, textvariable=self.ws_name_var)\
            .grid(row=0, column=3, sticky="w")

        ttk.Label(hdr, text="Serial:", style="App.TLabel")\
            .grid(row=0, column=4, sticky="w", padx=(16, 6))
        ttk.Label(hdr, textvariable=self.ws_serial_var)\
            .grid(row=0, column=5, sticky="w")

        # ---------------- CONTENT ----------------
        content = ttk.Frame(self, style="App.TFrame", padding=8)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # >>> This replaces FigureCanvasTkAgg
        self.canvas = YoudenPlotCanvas(content, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Sizegrip
        ttk.Sizegrip(self).grid(row=2, column=0, sticky="se")

        # Redraw on resize
        self.bind("<Configure>", lambda e: self._refresh_plot())

        
    # ----------------------------------------------------------------------
    def on_open(self, selected_test_method, selected_workstation, batches, data):
        """
        Entry point from main window.
        """
        self._cached_args = (selected_test_method, selected_workstation, batches, data)

        test_name = self.engine.get_test_name(selected_test_method[1])
        self.test_name_var.set(test_name)
        self.ws_name_var.set(selected_workstation[3])
        self.ws_serial_var.set(selected_workstation[4])

        # Units
        self.um = self.engine.get_um(selected_test_method[5])

        self.batches = list(batches) if batches else []
        self.title(f"{test_name} — Youden Plot")

        self._draw_youden(data)

    # ----------------------------------------------------------------------
    def _refresh_plot(self):
        if not self._cached_args:
            return
        st, ws, batches, data = self._cached_args
        self._draw_youden(data)

    # ----------------------------------------------------------------------
    def _draw_youden(self, data):
        self.canvas.clear()

        if not self.batches or len(self.batches) < 2:
            return

        if not data or len(data) < 2:
            return

        # Batches (target, sd)
        b1, b2 = self.batches[0], self.batches[1]
        target_x = float(b1[7])
        sd_x     = float(b1[8])
        target_y = float(b2[7])
        sd_y     = float(b2[8])

        # Paired results
        x_vals, y_vals = data
        n = min(len(x_vals), len(y_vals))
        x_vals, y_vals = x_vals[:n], y_vals[:n]

        test_name = self.test_name_var.get()
        ws_name   = self.ws_name_var.get()

        title = f"{test_name} — {ws_name}"
        bottom_text = f"Computed {n} paired results"

        # Units on axes
        um_txt = self.um.get("description") if self.um else ""
        x_label = f"L1 ({um_txt})" if um_txt else "Level 1"
        y_label = f"L2 ({um_txt})" if um_txt else "Level 2"

        self.canvas.draw_youden(
            level1=x_vals,
            level2=y_vals,
            target_x=target_x,
            target_y=target_y,
            sd_x=sd_x,
            sd_y=sd_y,
            title=title,
            x_label=x_label,
            y_label=y_label,
            bottom_text=bottom_text,
            show_indices=self.show_labels_var.get(),
        )

    # ----------------------------------------------------------------------
    def _on_close(self, evt=None):
        type(self)._instance = None
        try:
            super().destroy()
        except Exception as e:
            pass
