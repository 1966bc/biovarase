# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
QC Result Editor Window.

This module provides an editor dialog for creating and updating quality control
test results. Results include test measurements, received timestamps, and status.
"""
import sys
import inspect
from datetime import datetime
import tkinter as tk

from ui.child_view import ChildView
from tkinter import ttk
from tkinter import messagebox
from ui.calendarium import Calendarium

# Constants
FOCUS_DELAY_MS = 50  # Delay for event queue to settle before focusing
DEFAULT_REAGENT_LOT = "NOT ASSIGNED"  # Default value for optional reagent_lot field


class UI(ChildView):
    """
    Editor window for QC test results.

    This is a non-singleton editor window (per PROJECT_RULES.md section 7.1).
    Opens via engine.on_open() for creating new results or editing existing ones.
    """

    def __init__(self, parent, index=None):
        """
        Initialize the result editor window.

        Args:
            parent: Parent widget (typically the main results window)
            index: Treeview item_id of existing result to edit, or None for new result
        """
        super().__init__(parent, name="result")

        self.engine = self.nametowidget(".").engine
        self.index = index
        self.table = "results"        # UI variables
        self.test = tk.StringVar()
        self.batch = tk.StringVar()
        self.level = tk.StringVar()
        self.workstation = tk.StringVar()
        self.reagent_lot = tk.StringVar()
        self.result = tk.DoubleVar()
        self.status = tk.BooleanVar()
        self.received_display = tk.StringVar()

        # Store received datetime internally (not user-editable)
        self.received_datetime = None  # type: Optional[datetime]

        self.float_vcmd = self.engine.tools.get_validate_float(self)

        # Layout root - single column, rows expand
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Build interface
        self._build_ui()

        # Register window in engine (per PROJECT_RULES.md section 7.1)
        self.engine.windows.dict_instances[self.winfo_name()] = self
        self.show()

    def _build_ui(self):
        """Build the user interface layout following GNOME/Windows HIG."""
        paddings = {"padx": 5, "pady": 5}

        # Main container with adequate padding
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=(15, 10, 15, 12))
        self.frm_main.grid(row=0, column=0, sticky=tk.NSEW)
        self.frm_main.columnconfigure(0, weight=1)

        # Content frame (form fields)
        frm_content = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_content.grid(row=0, column=0, sticky=tk.NSEW, **paddings)

        r = 0
        c = 1
        ttk.Label(frm_content, text="Test:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_content,
            style="Data.TLabel",
            textvariable=self.test,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_content, text="Batch:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_content,
            style="Data.TLabel",
            textvariable=self.batch,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_content, text="Level:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_content,
            style="Data.TLabel",
            textvariable=self.level,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_content, text="Workstation:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_content,
            style="Data.TLabel",
            textvariable=self.workstation,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_content, text="Reagent Lot:").grid(row=r, sticky=tk.W)
        self.txtReagentLot = ttk.Entry(
            frm_content,
            width=20,
            textvariable=self.reagent_lot,
        )
        self.txtReagentLot.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_content, text="Result:").grid(row=r, sticky=tk.W)
        self.txtResult = ttk.Entry(
            frm_content,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.float_vcmd,
            textvariable=self.result,
        )
        self.txtResult.bind("<Return>", self._on_save)
        self.txtResult.bind("<KP_Enter>", self._on_save)
        self.txtResult.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_content, text="Received:").grid(row=r, sticky=tk.W)

        # Two widgets for "Received" field:
        # 1. Calendarium (editable) - shown only when inserting new result
        bg = getattr(self.engine, "BASE_BG_RGB", self.engine.tools.get_rgb(240, 240, 237))
        self.calendarium_received = Calendarium(frm_content, "")
        self.calendarium_received.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        # 2. Label (read-only) - shown only when editing existing result
        self.lbl_received = ttk.Label(
            frm_content,
            style="Data.TLabel",
            textvariable=self.received_display,
        )
        self.lbl_received.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        # Initially hide Calendarium (will be shown in on_open() if needed)
        self.calendarium_received.grid_remove()

        r += 1
        ttk.Label(frm_content, text="Status:").grid(row=r, sticky=tk.W)
        self.ckStatus = ttk.Checkbutton(
            frm_content,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        )
        self.ckStatus.grid(row=r, column=c, sticky=tk.W)

        # Separator before buttons
        ttk.Separator(self.frm_main, orient=tk.HORIZONTAL).grid(
            row=1, column=0, sticky=tk.EW, pady=(15, 10)
        )

        # Button bar at bottom (GNOME/Windows HIG: buttons at bottom, right-aligned)
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=2, column=0, sticky=tk.E, pady=(0, 5))

        # Button order: Cancel, Delete (if applicable), Save (primary action on right)
        c = 0
        btn_cancel = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        )
        self.bind("<Alt-c>", self.on_cancel)
        btn_cancel.grid(row=0, column=c, padx=(0, 5))

        # Only admins/superusers can delete (role < 2)
        if self.engine.log_user["role"] < 2 and self.index is not None:
            c += 1
            btn_delete = ttk.Button(
                frm_buttons,
                style="App.TButton",
                text="Delete",
                underline=0,
                command=self._delete,
            )
            self.bind("<Alt-d>", self._delete)
            btn_delete.grid(row=0, column=c, padx=(0, 5))

        c += 1
        btn_save = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self._on_save,
        )
        self.bind("<Alt-s>", self._on_save)
        btn_save.grid(row=0, column=c)

    def on_open(self):
        """
        Entry point called by the parent after creating the dialog.

        Initializes the window with data from parent selections and sets
        appropriate mode (insert or update).
        """
        self.selected_test_method = self.parent.selected_test_method
        self.selected_batch = self.parent.selected_batch
        self.selected_workstation = self.parent.selected_workstation

        # Parent objects are dictionaries (read_dict / get_selected)
        # Use named keys (per PROJECT_RULES.md section 5.2 - no positional indexing)
        self.test.set(self.parent.selected_test["description"])
        self.batch.set(self.selected_batch["lot_number"])
        # Batch 'description' is typically the level label (e.g. L1, L2)
        self.level.set(self.selected_batch["description"])
        self.workstation.set(self.selected_workstation["description"])

        if self.index is not None:
            # UPDATE mode: show read-only Label, hide Calendarium
            self.selected_result = self.parent.selected_result
            msg = f"Update {self.winfo_name().capitalize()} "
            self.lbl_received.grid()
            self.calendarium_received.grid_remove()
            self._set_values()
        else:
            # INSERT mode: show editable Calendarium, hide Label
            msg = f"Add {self.winfo_name().capitalize()} "
            self.calendarium_received.grid()
            self.lbl_received.grid_remove()
            self.status.set(1)
            #self.result.set(0.0)
            self.result.set("")
            self.reagent_lot.set(DEFAULT_REAGENT_LOT)  # Pre-populate to pass validation
            # Set Calendarium to today's date
            self.calendarium_received.set_today()
            # Also store in received_datetime for compatibility
            self.received_datetime = datetime.now()
            self.received_display.set(
                self.engine.format_datetime(self.received_datetime)
            )

        self.title(msg)

        # Make sure the window is visible and on top
        self.deiconify()
        self.lift()

        # Focus on result entry
        self._focus_entry()

        # Second attempt after event queue settles (covers double-click edge cases)
        self.after(FOCUS_DELAY_MS, self._focus_entry)

        # Calculate minimum size AFTER layout is finalized
        # Extra height for Windows compatibility (different font metrics)
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight() + 20)

    def _focus_entry(self):
        """Ensure focus goes to result entry field."""
        try:
            self.lift()
            self.focus_force()
            if self.index is not None:
                self.txtResult.focus_set()
            else:
                self.txtReagentLot.focus_set()
                
            #self.txtResult.selection_range(0, tk.END)
        except Exception as e:
            pass

    def _set_values(self):
        """Fill widgets from selected_result for update mode."""
        # Received datetime
        try:
            received = self.selected_result["received"]
            # Store the datetime internally
            self.received_datetime = received
            # Display formatted datetime with time (read-only)
            self.received_display.set(self.engine.format_datetime(received))
        except Exception as e:
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

        # Result value
        try:
            value = self.selected_result["result"]
            self.result.set(round(value, 3))
        except (ValueError, TypeError, KeyError) as e:
            self.result.set(0.0)
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

        # Status
        try:
            status_val = self.selected_result["status"]
            self.status.set(status_val)
        except (KeyError, TypeError) as e:
            self.status.set(1)
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

        # Reagent lot (optional field, may be NULL or default value)
        try:
            reagent_lot = self.selected_result.get("reagent_lot", DEFAULT_REAGENT_LOT)
            # If NULL in database, use default value
            if reagent_lot is None:
                reagent_lot = DEFAULT_REAGENT_LOT
            self.reagent_lot.set(reagent_lot)
        except (KeyError, TypeError) as e:
            self.reagent_lot.set(DEFAULT_REAGENT_LOT)
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

    def _get_values(self):
        """The row as a dictionary keyed by column name.

        The columns are the ones results has: nothing here knows in which
        order they were declared, and nothing has to be kept in step with
        the table by counting commas.

        @return: values
        @rtype: dictionary
        """
        try:
            val = round(float(self.result.get()), 3)
        except (ValueError, TypeError):
            val = 0.0

        if self.index is None:
            ts = self.calendarium_received.get_timestamp()
            if ts is None:
                ts = datetime.now()
        else:
            ts = self.received_datetime
            if ts is None or isinstance(ts, str):
                ts = datetime.now()

        reagent_lot = self.reagent_lot.get().strip()
        if not reagent_lot:
            reagent_lot = DEFAULT_REAGENT_LOT

        if self.index is None:
            created_by = self.engine.log_user["user_id"]
            created_at = ts
        else:
            created_by = self.selected_result["created_by"]
            created_at = self.selected_result["created_at"]

        if self.status.get():
            status = 1
        else:
            status = 0

        return {"batch_id": self.selected_batch["batch_id"],
                "result": val,
                "received": ts,
                "reagent_lot": reagent_lot,
                "status": status,
                "created_by": created_by,
                "created_at": created_at}

    def _on_save(self, evt=None):
        """
        Save the result to the database.

        Validates fields, prompts for confirmation, then performs INSERT or UPDATE.

        Args:
            evt: Optional Tkinter event (from key binding or button click)
        """
        if not self.engine.tools.on_fields_control(self.frm_main, self.engine.app_title):
            return

        # Validate Calendarium date if in INSERT mode (editable date field)
        if self.index is None:
            if not self.calendarium_received.is_valid:
                messagebox.showerror(
                    self.engine.app_title,
                    "Please enter a valid received date.",
                    parent=self,
                )
                return

        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.ask_to_save,
            parent=self,
        ):
            return

        values = self._get_values()

        if self.index is not None:
            pk = self.selected_result["result_id"]
            sql, args = self.engine.db.get_update(self.table, pk, values)
        else:
            sql, args = self.engine.db.get_insert(self.table, values)

        last_id = self.engine.db.write(sql, args)

        self._update_main_results_lists()
        self._set_index(last_id)

        # Notify observers
        self.engine.events.notify("result_changed", last_id)

        self.on_cancel()

    def _update_main_results_lists(self):
        """
        Ask main window to refresh results list.

        Uses Engine registry pattern (per PROJECT_RULES.md section 16.4)
        instead of hardcoded window names.
        """
        try:
            win = self.engine.windows.dict_instances.get("main")
            if win and win.winfo_exists():
                win.set_results()
        except Exception as e:
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

    def _set_index(self, last_id):
        """
        Ensure the saved/inserted row is selected in parent.lstResults.

        Args:
            last_id: The result_id of the saved record
        """
        # After save, treeview is reloaded and item_ids change.
        # Always search for the result_id in the updated dict_results.
        item_id = None
        for k, rid in self.parent.dict_results.items():
            if rid == last_id:
                item_id = k
                break

        if item_id is None:
            return

        self.parent.lstResults.selection_set(item_id)
        self.parent.lstResults.see(item_id)

    def _delete(self, evt=None):
        """
        Soft-delete current result (set is_delete = 1).

        Preserves audit trail by marking deleted rather than removing the record.

        Args:
            evt: Optional Tkinter event (from key binding or button click)
        """
        if self.index is None:
            return

        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.delete,
            parent=self,
        ):
            messagebox.showinfo(
                self.engine.app_title,
                self.engine.abort,
                parent=self,
            )
            return

        sql = """
              UPDATE results
                 SET is_delete = 1,
                     log_time  = ?,
                     log_id    = ?,
                     log_ip    = ?
               WHERE result_id = ?;
             """
        pk = self.selected_result["result_id"]

        args = (
            self.engine.get_log_time(),
            self.engine.get_log_id(),
            self.engine.get_log_ip(),
            pk,
        )
        self.engine.db.write(sql, args)

        self._update_main_results_lists()

        # Notify observers
        self.engine.events.notify("result_changed", pk)

        self.on_cancel()

    def on_cancel(self, _evt=None):
        """
        Close the window without saving.

        Unregisters from engine before destroying (per PROJECT_RULES.md section 7.1).

        Args:
            _evt: Optional Tkinter event (from key binding or button click)
        """
        # Unregister from engine (per PROJECT_RULES.md section 7.1)
        self.engine.windows.dict_instances.pop(self.winfo_name(), None)
        self.destroy()
