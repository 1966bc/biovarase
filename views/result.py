# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
# -----------------------------------------------------------------------------
"""
QC Result Editor Window.

This module provides an editor dialog for creating and updating quality control
test results. Results include test measurements, received timestamps, and status.
"""
import sys
import inspect
from datetime import datetime
from typing import Optional, Any, List
import tkinter as tk

from views.child_view import ChildView
from tkinter import ttk
from tkinter import messagebox
from calendarium import Calendarium

# Constants
FOCUS_DELAY_MS = 50  # Delay for event queue to settle before focusing
DEFAULT_REAGENT_LOT = "NOT ASSIGNED"  # Default value for optional reagent_lot field


class UI(ChildView):
    """
    Editor window for QC test results.

    This is a non-singleton editor window (per PROJECT_RULES.md section 7.1).
    Opens via engine.on_open() for creating new results or editing existing ones.
    """

    def __init__(self, parent: tk.Widget, index: Optional[int] = None) -> None:
        """
        Initialize the result editor window.

        Args:
            parent: Parent widget (typically the main results window)
            index: Index of existing result to edit, or None for new result
        """
        super().__init__(name="result")

        self.engine = self.nametowidget(".").engine
        self.parent = parent
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

        self.float_vcmd = self.engine.get_float_vcmd(self)

        # Layout root columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # Build interface
        self._build_ui()

        # Register window in engine (per PROJECT_RULES.md section 7.1)
        self.engine.dict_instances[self.winfo_name()] = self
        self.show()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def _build_ui(self) -> None:
        """Build the user interface layout."""
        paddings = {"padx": 5, "pady": 5}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **paddings)

        r = 0
        c = 1
        ttk.Label(frm_left, text="Test:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_left,
            style="Data.TLabel",
            textvariable=self.test,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Batch:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_left,
            style="Data.TLabel",
            textvariable=self.batch,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Level:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_left,
            style="Data.TLabel",
            textvariable=self.level,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Workstation:").grid(row=r, sticky=tk.W)
        ttk.Label(
            frm_left,
            style="Data.TLabel",
            textvariable=self.workstation,
        ).grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Reagent Lot:").grid(row=r, sticky=tk.W)
        self.txtReagentLot = ttk.Entry(
            frm_left,
            width=20,
            textvariable=self.reagent_lot,
        )
        self.txtReagentLot.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Result:").grid(row=r, sticky=tk.W)
        self.txtResult = ttk.Entry(
            frm_left,
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
        ttk.Label(frm_left, text="Received:").grid(row=r, sticky=tk.W)

        # Two widgets for "Received" field:
        # 1. Calendarium (editable) - shown only when inserting new result
        bg = getattr(self.engine, "BASE_BG_RGB", self.engine.get_rgb(240, 240, 237))
        self.calendarium_received = Calendarium(frm_left, "", base_bg_color=bg)
        self.calendarium_received.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        # 2. Label (read-only) - shown only when editing existing result
        self.lbl_received = ttk.Label(
            frm_left,
            style="Data.TLabel",
            textvariable=self.received_display,
        )
        self.lbl_received.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        # Initially hide Calendarium (will be shown in on_open() if needed)
        self.calendarium_received.grid_remove()

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, sticky=tk.W)
        self.ckStatus = ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        )
        self.ckStatus.grid(row=r, column=c, sticky=tk.W)

        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky=tk.NS, **paddings)

        r = 0
        c = 0
        btn = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self._on_save,
        )
        self.bind("<Alt-s>", self._on_save)
        btn.grid(row=r, column=c, sticky=tk.EW, **paddings)

        # Only admins/superusers can delete (role < 2)
        if self.engine.log_user["role"] < 2 and self.index is not None:
            r += 1
            btn = ttk.Button(
                frm_buttons,
                style="App.TButton",
                text="Delete",
                underline=0,
                command=self._delete,
            )
            self.bind("<Alt-d>", self._delete)
            btn.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        btn = ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        )
        self.bind("<Alt-c>", self.on_cancel)
        btn.grid(row=r, column=c, sticky=tk.EW, **paddings)

    def on_open(self) -> None:
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

    def _focus_entry(self) -> None:
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

    def _set_values(self) -> None:
        """Fill widgets from selected_result for update mode."""
        # Received datetime
        try:
            received = self.selected_result["received"]
            # Store the datetime internally
            self.received_datetime = received
            # Display formatted datetime with time (read-only)
            self.received_display.set(self.engine.format_datetime(received))
        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

        # Result value
        try:
            value = self.selected_result["result"]
            self.result.set(round(value, 3))
        except (ValueError, TypeError, KeyError) as e:
            self.result.set(0.0)
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

        # Status
        try:
            status_val = self.selected_result["status"]
            self.status.set(status_val)
        except (KeyError, TypeError) as e:
            self.status.set(1)
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

        # Reagent lot (optional field, may be NULL or default value)
        try:
            reagent_lot = self.selected_result.get("reagent_lot", DEFAULT_REAGENT_LOT)
            # If NULL in database, use default value
            if reagent_lot is None:
                reagent_lot = DEFAULT_REAGENT_LOT
            self.reagent_lot.set(reagent_lot)
        except (KeyError, TypeError) as e:
            self.reagent_lot.set(DEFAULT_REAGENT_LOT)
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

    def _get_values(self) -> List[Any]:
        """
        Build the argument list for INSERT/UPDATE on 'results'.

        Table structure (without PK result_id):
            batch_id, run_number, workstation_id, reagent_lot,
            result, received, status,
            validated, validated_by, validated_at,
            is_delete, log_time, log_id, log_ip

        Returns:
            List of values matching the table structure
        """
        if self.index is not None:
            # Update mode - preserve existing values
            run_number = self.selected_result["run_number"]
            is_delete = self.selected_result["is_delete"]
            validated = self.selected_result["validated"]
            validated_by = self.selected_result.get("validated_by")
            validated_at = self.selected_result.get("validated_at")
        else:
            # Insert mode - new result defaults
            run_number = 0
            is_delete = 0
            validated = 0
            validated_by = None
            validated_at = None

        # Result → safe float
        try:
            val = float(self.result.get())
        except (ValueError, TypeError) as e:
            val = 0.0
        val = round(val, 3)

        # Received → get from Calendarium if in INSERT mode, else use stored datetime
        if self.index is None:
            # INSERT mode: read from Calendarium widget
            ts = self.calendarium_received.get_timestamp()
            if ts is None:
                # Validation failed - use current datetime as fallback
                ts = datetime.now()
        else:
            # UPDATE mode: preserve existing datetime (not user-editable)
            ts = self.received_datetime
            if ts is None or isinstance(ts, str):
                ts = datetime.now()

        # Status → int
        status = 1 if self.status.get() else 0

        # FK batch_id
        batch_id = self.selected_batch["batch_id"]

        # FK workstation_id
        workstation_id = self.selected_workstation["workstation_id"]

        # Reagent lot (use default if empty to pass validation)
        reagent_lot_value = self.reagent_lot.get().strip()
        if not reagent_lot_value:
            reagent_lot_value = DEFAULT_REAGENT_LOT

        args = [
            batch_id,         # batch_id
            run_number,       # run_number
            workstation_id,   # workstation_id
            reagent_lot_value,  # reagent_lot
            val,              # result
            ts,               # received
            status,           # status
            validated,        # validated
            validated_by,     # validated_by
            validated_at,     # validated_at
            is_delete,        # is_delete
            self.engine.get_log_time(),
            self.engine.get_log_id(),
            self.engine.get_log_ip()
        ]

        return args

    def _on_save(self, evt: Optional[tk.Event] = None) -> None:
        """
        Save the result to the database.

        Validates fields, prompts for confirmation, then performs INSERT or UPDATE.

        Args:
            evt: Optional Tkinter event (from key binding or button click)
        """
        if not self.engine.on_fields_control(self.frm_main, self.engine.app_title):
            return

        # Validate Calendarium date if in INSERT mode (editable date field)
        if self.index is None:
            if not self.calendarium_received.is_valid:
                messagebox.showerror(
                    self.engine.app_title,
                    "Please enter a valid date for 'Received'.",
                    parent=self,
                )
                return

        if not messagebox.askyesno(
            self.engine.app_title,
            self.engine.ask_to_save,
            parent=self,
        ):
            return

        args = self._get_values()

        if self.index is not None:
            sql = self.engine.build_sql(self.table, op="update")
            # WHERE result_id = ?
            pk = self.selected_result["result_id"]
            args.append(pk)
        else:
            sql = self.engine.build_sql(self.table, op="insert")

        last_id = self.engine.write(sql, tuple(args))

        self._update_main_results_lists()
        self._set_index(last_id)
        self.on_cancel()

    def _update_main_results_lists(self) -> None:
        """
        Ask main window to refresh results list.

        Uses Engine registry pattern (per PROJECT_RULES.md section 16.4)
        instead of hardcoded window names.
        """
        try:
            win = self.engine.dict_instances.get("main")
            if win and win.winfo_exists():
                win.set_results()
        except Exception as e:
            self.engine.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

    def _set_index(self, last_id: int) -> None:
        """
        Ensure the saved/inserted row is selected in parent.lstResults.

        Args:
            last_id: The result_id of the saved record
        """
        if self.index is not None:
            idx = self.index
        else:
            # Find index of last_id in parent's mapping
            keys = list(self.parent.dict_results.keys())
            vals = list(self.parent.dict_results.values())
            try:
                idx = keys[vals.index(last_id)]
            except ValueError:
                # last_id not found: nothing to select
                return

        self.parent.lstResults.selection_set(idx)
        self.parent.lstResults.see(idx)

    def _delete(self, evt: Optional[tk.Event] = None) -> None:
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
        self.engine.write(sql, args)

        self._update_main_results_lists()
        self.on_cancel()

    def on_cancel(self, _evt: Optional[tk.Event] = None) -> None:
        """
        Close the window without saving.

        Unregisters from engine before destroying (per PROJECT_RULES.md section 7.1).

        Args:
            _evt: Optional Tkinter event (from key binding or button click)
        """
        # Unregister from engine (per PROJECT_RULES.md section 7.1)
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.destroy()
