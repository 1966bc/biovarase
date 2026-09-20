# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ui.parent_view import ParentView


class UI(ParentView):
    """Single-instance dialog using ParentView pattern."""

    def __init__(self, parent):
        super().__init__(parent, name="analytical_goals")
        if self._reusing:
            return

        self.title("Analytical Goals")
        self.resizable(False, False)

        self.elements = tk.IntVar(value=0)

        self._build_ui()
        self.show(on_screen=True)

    # --- UI builder ----------------------------------------------------------
    def _build_ui(self):
        padd = {"padx": 5, "pady": 5}

        # Main frame
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        # Left column
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **padd)

        ttk.Label(frm_left, text="Set elements to export:").grid(
            row=0, column=0, sticky=tk.W
        )

        self.txElements = ttk.Spinbox(
            frm_left,
            from_=1,
            to=999,
            textvariable=self.elements,
            width=4,  # ~3 digits + 1 margin
            justify="right",
            wrap=False,
        )
        self.txElements.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        frm_left.columnconfigure(1, weight=1)

        # Right column (buttons)
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
            command=self._on_close,
        )
        btn_cancel.grid(row=1, column=0, sticky=tk.EW, **padd)
        self.bind("<Alt-c>", self._on_close)
        self.bind("<Escape>", self._on_close)

    # --- Lifecycle -----------------------------------------------------------
    def on_open(self):
        """Called by parent to (re)show the dialog."""
        try:
            self.transient(self.parent)
        except Exception as e:
            pass

        # Preload with current engine preference (clamped 1..999)
        raw = self.engine.get_observations()
        val = self._to_int(raw, default=30)
        val = max(1, min(val, 999))
        self.elements.set(val)

        self.title("Analytical Goals")
        self.deiconify()
        self.lift()
        self.after_idle(self._focus_entry)

    def _focus_entry(self):
        """Give focus to the Spinbox and select its content."""
        try:
            self.txElements.focus_set()
            self.txElements.select_range(0, tk.END)
        except Exception as e:
            pass

        # --- Actions -------------------------------------------------------------
    def on_export(self, evt=None):
        """Validate input, run query, dispatch to engine exporter."""
        # Field-level validation (engine-driven)
        if self.engine.on_fields_control(self) is False:
            return

        # Clamp again 1..999 (even if Spinbox is used)
        limit = max(1, min(self._to_int(self.elements.get(), default=30), 999))

        # NOTE: schema updated to test_methods; batches references test_method_id
        sql = """
            SELECT
                b.batch_id          AS batch_id,
                s.sample            AS sample,
                t.description       AS analyte,
                b.lot_number        AS batch,
                b.expiration        AS expiration,
                b.target            AS target,
                g.cvw               AS cvw,
                g.cvb               AS cvb,
                g.imp               AS imp,
                g.bias              AS bias,
                g.teap005           AS teap005,
                g.teap001           AS teap001,
                r.workstation_id    AS workstation_id
            FROM tests AS t
            INNER JOIN test_methods   AS tm ON t.test_id         = tm.test_id
            INNER JOIN goals          AS g  ON tm.test_method_id = g.test_method_id
            INNER JOIN samples        AS s  ON tm.sample_id      = s.sample_id
            INNER JOIN batches        AS b  ON tm.test_method_id = b.test_method_id
            INNER JOIN results        AS r  ON b.batch_id        = r.batch_id
            INNER JOIN organizations  AS section ON tm.org_id = section.org_id
            INNER JOIN workstations   AS w  ON r.workstation_id  = w.workstation_id
            WHERE t.status = 1
              AND section.parent_id = ?
              AND section.org_type = 'section'
              AND g.to_export = 1
              AND b.status = 1
              AND b.expiration IS NOT NULL
              AND r.is_delete = 0
              AND r.status = 1
            GROUP BY b.batch_id, r.workstation_id
            ORDER BY t.description;
        """

        lab_id = self.engine.get_lab_id()

        # MUST use read_dict(): result rows are dictionaries
        rs = self.engine.read(True, sql, (lab_id,))

        if rs:
            # Dispatch to exporter (engine side) with dict-based rows
            self.engine.get_analitical_goals(limit, rs)
            self._on_close()
        else:
            msg = "No record data to compute."
            title = getattr(self.engine, "app_title", "Biovarase")
            messagebox.showwarning(title, msg, parent=self)


    # --- Utils ----------------------------------------------------------------
    def _to_int(self, value, default=1):
        """Coerce value to int safely, else return default."""
        try:
            if value is None:
                return default
            if isinstance(value, str):
                value = value.strip()
            return int(value)
        except Exception as e:
            return default

    def _on_close(self, evt=None):
        """Close window using ParentView pattern."""
        super().on_cancel()
