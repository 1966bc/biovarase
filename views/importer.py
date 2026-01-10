#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QC Import window for Biovarase.

Responsibilities:
    - Let the user select 'received' date/time (Calendarium).
    - Let the user select a QC file whose filename is the device_id
      (e.g. 123e4567-e89b-12d3-a456-426614174001.txt).
    - Delegate the full import workflow to:
          engine.import_qc_file_auto(filepath, received_ts)
"""

import os
import sys
import inspect
import tkinter as tk
from tkinter import ttk, filedialog as fd, messagebox

from i18n import _
from calendarium import Calendarium  # adjust import path if needed
from views.child_view import ChildView

# Default value for optional reagent_lot field
DEFAULT_REAGENT_LOT = "NOT ASSIGNED"


class UI(ChildView):
    """QC import editor window."""

    def __init__(self, parent):
        super().__init__(parent, name="import_qc")

        self.received = None  # Calendarium instance
        self.workstation = tk.IntVar()  # Selected workstation_id
        self.reagent_lot = tk.StringVar()  # Reagent lot number
        self.frm_main = None  # main frame container

        # Data stores
        self.dict_workstations = {}  # {index: workstation_id}

        # Layout
        self.columnconfigure(0, weight=1)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()
        

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        """Build widgets and layout."""
        paddings = {"padx": 5, "pady": 5}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky=tk.NSEW)

        # Left side: fields
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **paddings)

        r = 0
        ttk.Label(frm_left, text=_("Received:")).grid(row=r, column=0, sticky=tk.NW)
        self.received = Calendarium(frm_left, _("Date"))
        self.received.grid(row=r, column=1, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text=_("Workstation:")).grid(row=r, column=0, sticky=tk.W)
        self.cbWorkstation = ttk.Combobox(frm_left, state="readonly")
        self.cbWorkstation.grid(row=r, column=1, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text=_("Reagent Lot:")).grid(row=r, column=0, sticky=tk.W)
        self.txtReagentLot = ttk.Entry(
            frm_left,
            width=30,
            textvariable=self.reagent_lot,
        )
        self.txtReagentLot.grid(row=r, column=1, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(
            frm_left,
            text=(
                _("Select workstation and optionally enter reagent lot.") + "\n" +
                _("File can have any name (no renaming required).")
            ),
            justify=tk.LEFT,
        ).grid(row=r, column=0, columnspan=2, sticky=tk.W, **paddings)

        # Right side: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky=tk.NS, **paddings)

        r = 0
        btn_import = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text=_("Import file…"),
            command=self._on_import_file,
        )
        btn_import.grid(row=r, column=0, sticky=tk.EW, **paddings)

        r += 1
        btn_close = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text=_("Close"),
            command=self.on_cancel,
        )
        btn_close.grid(row=r, column=0, sticky=tk.EW, **paddings)

    # ------------------------------------------------------------------ #
    # Lifecycle hooks
    # ------------------------------------------------------------------ #
    def on_open(self) -> None:
        """
        Called by Engine when the window is opened.

        It sets default values and focuses the first widget.
        """
        self.title(_("Import QC"))
        try:
            self.received.set_today()
        except Exception as e:
            # Fail-safe: do not break if Calendarium fails
            pass

        # Load workstations and set default reagent_lot
        self._load_workstations()
        self.reagent_lot.set(DEFAULT_REAGENT_LOT)
        self.received.focus_set()

    def _load_workstations(self) -> None:
        """Load workstations based on user's lab."""
        try:
            lab_id = self.engine.get_lab_id()
            sql = """SELECT w.workstation_id, w.description
                     FROM workstations w
                     JOIN sections s ON s.section_id = w.section_id
                     WHERE s.lab_id = ? AND w.status = 1
                     ORDER BY w.rank, w.description"""
            rows = self.engine.read(True, sql, (lab_id,))

            values = []
            self.dict_workstations = {}
            for index, row in enumerate(rows):
                values.append(row["description"])
                self.dict_workstations[index] = row["workstation_id"]

            self.cbWorkstation["values"] = values
            if values:
                self.cbWorkstation.current(0)

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def _on_import_file(self, _evt=None) -> None:
        """
        Handler for the 'Import file…' button.

        It validates GUI fields, asks for a file, and delegates the import
        to engine.import_qc_file_auto().
        """
        # 1) Validate fields using Engine helper
        try:
            if not self.engine.on_fields_control(self.frm_main, self.engine.title):
                return
        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )
            return

        # 2) Ask user to select file
        filepath = fd.askopenfilename(
            title=_("Select QC file"),
            filetypes=(
                (_("QC files"), "*.txt *.csv *.tsv"),
                (_("All files"), "*"),
            ),
            parent=self,
        )
        if not filepath:
            return

        if not os.path.isfile(filepath):
            msg = (
                _("Houston we have a problem here.") + "\n" +
                _("Something went wrong or you did not select a valid file.")
            )
            messagebox.showwarning(self.engine.title, msg, parent=self)
            return

        # 3) Busy cursor
        self.config(cursor="watch")
        self.update_idletasks()

        try:
            # 4) Get timestamp from Calendarium
            try:
                received_ts = self.received.get_timestamp()
            except Exception as e:
                received_ts = None

            if received_ts is None:
                messagebox.showwarning(
                    self.engine.title,
                    _("Invalid 'Received' date."),
                    parent=self,
                )
                return

            # 5) Get selected workstation
            selected_index = self.cbWorkstation.current()
            if selected_index < 0:
                messagebox.showwarning(
                    self.engine.title,
                    _("Please select a workstation."),
                    parent=self,
                )
                return
            workstation_id = self.dict_workstations[selected_index]

            # 6) Get reagent lot (use default if empty)
            reagent_lot_value = self.reagent_lot.get().strip()
            if not reagent_lot_value:
                reagent_lot_value = DEFAULT_REAGENT_LOT

            # 7) Delegate import to Engine
            imported, matched, not_matched, profile_name = (
                self.engine.import_qc_file_auto(
                    filepath, received_ts, workstation_id, reagent_lot_value
                )
            )

            msg = (
                f"{_('Profile')}: {profile_name or 'N/A'}\n\n"
                f"{_('Imported rows')}: {imported}\n"
                f"{_('Matched batches')}: {matched}\n"
                f"{_('Unmatched rows')}: {not_matched}"
            )
            messagebox.showinfo(self.engine.title, msg, parent=self)

        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )
            messagebox.showerror(
                self.engine.title,
                _("Unexpected error while importing QC file."),
                parent=self,
            )
        finally:
            self.config(cursor="")
            self.update_idletasks()

    def on_cancel(self, evt=None) -> None:
        """Close dialog."""
        super().on_cancel(evt)
