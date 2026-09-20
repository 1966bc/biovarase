# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from calendarium import Calendarium
from datetime import date, datetime

from ui.child_view import ChildView
from app_config import BATCH_DESCRIPTION_MAX_LENGTH, LOT_NUMBER_MAX_LENGTH


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="batch")

        self.index = index

        # Hotkeys
        self.bind("<Alt-s>", self.on_save)
        
        self.lot_number = tk.StringVar()
        self.description = tk.StringVar()

        # Enforce max lengths as you type (delegated to engine)
        self.lot_number.trace(
            "w",
            lambda x, y, z, c=LOT_NUMBER_MAX_LENGTH, v=self.lot_number: self.engine.limit_chars(
                c, v, x, y, z
            ),
        )
        self.description.trace(
            "w",
            lambda x, y, z, c=BATCH_DESCRIPTION_MAX_LENGTH, v=self.description: self.engine.limit_chars(
                c, v, x, y, z
            ),
        )

        self.target = tk.DoubleVar()
        self.sd = tk.DoubleVar()
        self.lower = tk.DoubleVar()
        self.upper = tk.DoubleVar()
        self.to_compute = tk.IntVar()              # 0 = Manual, 1 = Computed
        self.rank = tk.IntVar()
        self.status = tk.BooleanVar()
        self.remember_batch = tk.BooleanVar()

        # Numeric validators provided by engine
        self.vcmd = self.engine.get_float_vcmd(self)
        self.vcmd_int = self.engine.get_validate_integer(self)

        # Auto-compute SD when lower/upper change (only if 'Computed' selected)
        self.lower.trace("w", lambda *args: self._compute_sd())
        self.upper.trace("w", lambda *args: self._compute_sd())

        # Root grid config (two columns: form + buttons)
        #self.columnconfigure(0, weight=1)
        #self.columnconfigure(1, weight=0)

        # Build UI
        self._build_ui()

        # Show window (centered by ChildView)
        self.show()
        
    def _build_ui(self):
        paddings = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        self.frm_main.columnconfigure(0, weight=1)
        self.frm_main.columnconfigure(1, weight=2)
        self.frm_main.columnconfigure(2, weight=1)

        # Left: fields
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS, **paddings)

        r = 0; c = 1
        ttk.Label(frm_left, text="Control:").grid(row=r, sticky=tk.W)
        self.cbControls = ttk.Combobox(frm_left, state="readonly")
        self.cbControls.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Lot:").grid(row=r, sticky=tk.W)
        self.txLotNumber = ttk.Entry(frm_left, textvariable=self.lot_number)
        self.txLotNumber.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Description:").grid(row=r, sticky=tk.W)
        self.txDescription = ttk.Entry(frm_left, textvariable=self.description)
        self.txDescription.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="Expiration:").grid(row=r, sticky=tk.N + tk.W)
        # Safe fallback: use BASE_BG_RGB if available, otherwise fallback to a known RGB
        bg = getattr(self.engine, "BASE_BG_RGB", self.engine.get_rgb(240, 240, 237))
        self.expiration_date = Calendarium( frm_left, "", base_bg_color=bg)
        self.expiration_date.grid(row=r, column=c, sticky=tk.W)

        r += 1
        ttk.Label(frm_left, text="Target:").grid(row=r, sticky=tk.W)
        self.txtTarget = ttk.Entry(
            frm_left,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.vcmd,
            textvariable=self.target,
        )
        self.txtTarget.grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Lower:").grid(row=r, sticky=tk.W)
        self.txtLower = ttk.Entry(
            frm_left,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.vcmd,
            textvariable=self.lower,
            state=tk.DISABLED,
        )
        self.txtLower.grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Upper:").grid(row=r, sticky=tk.W)
        self.txtUpper = ttk.Entry(
            frm_left,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.vcmd,
            textvariable=self.upper,
            state=tk.DISABLED,
        )
        self.txtUpper.grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="SD:").grid(row=r, sticky=tk.W)
        self.txtSD = ttk.Entry(
            frm_left,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.vcmd,
            textvariable=self.sd,
        )
        self.txtSD.grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Rank:").grid(row=r, sticky=tk.W)
        self.txtRank = ttk.Entry(
            frm_left,
            width=8,
            justify=tk.CENTER,
            validate="key",
            validatecommand=self.vcmd_int,
            textvariable=self.rank,
        )
        self.txtRank.grid(row=r, column=c, sticky=tk.W, padx=5, pady=5)

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, sticky=tk.W)
        ttk.Checkbutton(frm_left, onvalue=1, offvalue=0, variable=self.status).grid(
            row=r, column=c, sticky=tk.W
        )

        # Right: buttons options
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky=tk.NS, **paddings)

        r = 0; c = 0
        btn = ttk.Button(
            frm_buttons, style="App.TButton", text="Save", underline=0, command=self.on_save
        )
        self.bind("<Alt-s>", self.on_save)
        self.bind("<Return>", self.on_save)
        btn.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        btn = ttk.Button(
            frm_buttons, style="App.TButton", text="Cancel", underline=0, command=self.on_cancel
        )
        self.bind("<Alt-c>", self.on_cancel)
        #self.bind("<Escape>", self.on_cancel)  # remove if you prefer Alt+F only
        btn.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Checkbutton(
            frm_buttons,
            text="Remember data",
            variable=self.remember_batch,
            command=lambda: self.engine.set_remember_batch(self.remember_batch.get())
        ).grid(row=r, column=c, sticky=tk.W)

        r += 1
        frm_sd = ttk.LabelFrame(frm_buttons, style="App.TLabelframe", text="SD mode")
        frm_sd.grid(row=r, column=c, rowspan=4, sticky=tk.NW)

        voices = ["Manual", "Computed"]
        for idx, text in enumerate(voices):
            ttk.Radiobutton(
                frm_sd,
                style="App.TRadiobutton",
                text=text,
                variable=self.to_compute,
                command=self._set_compute_mode,
                value=idx,
            ).grid(row=r + idx, column=c, sticky=tk.EW, **paddings)

    
    def on_open(self, selected_test_method, selected_workstation, selected_batch=None):
 
        # Fail fast: mandatory context
        if not selected_test_method or not selected_workstation:
            messagebox.showerror(self.engine.app_title, "Missing context: test method or workstation.", parent=self)
            self.on_cancel()
            return

        self.selected_workstation = selected_workstation
        # Use org_id from workstation (section level org)
        self.workstation_org_id = selected_workstation.get("org_id") or selected_workstation.get(5)

        # Compute lab_id from org hierarchy (fail-safe: 0 on failure)
        try:
            idd = self.engine.get_idd_by_section_id(self.workstation_org_id)
            self.lab_id = int(idd.get("lab_id", 0)) if idd else 0
        except Exception as e:
            self.lab_id = 0

        # Remember preference
        try:
            self.remember_batch.set(bool(self.engine.get_remember_batch()))
        except Exception as e:
            self.remember_batch.set(False)

        # Populate controls (safe even if empty)
        self._set_controls()

        # Load current test (fail-fast on missing record)
        sql = """
            SELECT
                test_id,
                description
            FROM tests
            WHERE test_id = ?;
        """
        args = (selected_test_method["test_id"],)  
        self.selected_test = self.engine.read(False, sql, args)
        
        if not self.selected_test:
            messagebox.showerror(self.engine.app_title, "Test not found.", parent=self)
            self.on_cancel()
            return

        self.selected_test_method = selected_test_method

        if self.index is not None:
            # UPDATE mode
            if not selected_batch:
                messagebox.showerror(self.engine.app_title, "Batch not found.", parent=self)
                self.on_cancel()
                return

            self.selected_batch = selected_batch
            msg = (
                f"Update {self.winfo_name().capitalize()} "
                f"{self.selected_batch['lot_number']} "
                f"for {self.selected_test['description']}"
            )

            self._set_values()
            
        else:
            # INSERT mode
            msg = (
                f"Insert {self.winfo_name().capitalize()} "
                f"for {self.selected_test['description']}"
            )
                        # Remembered data (fail-safe)
            if self.remember_batch.get() and self.engine.batch_data:
                try:
                    # Preselect control if present in cached tuple
                    target_control_id = self.engine.batch_data[1]
                    key = next(k for k, v in self.dict_controls.items() if v == target_control_id)
                    self.cbControls.current(key)
                except Exception as e:
                    pass
                try:
                    self.lot_number.set(self.engine.batch_data[4])
                    self.description.set(self.engine.batch_data[8])
                    exp = self.engine.batch_data[5]
                    self.expiration_date.year.set(int(exp.year))
                    self.expiration_date.month.set(int(exp.month))
                    self.expiration_date.day.set(int(exp.day))
                except Exception as e:
                    self.expiration_date.set_today()
            else:
                self.expiration_date.set_today()

            # Safe defaults
            self.status.set(1)
            self.to_compute.set(1)
            self._set_compute_mode()
            title = "Insert Batch"

        self.title(msg)
        self.after_idle(self._focus_entry)

    def _focus_entry(self):
        try:
            self.cbControls.focus()
        except Exception as e:
            pass

    def _set_controls(self):
        """Load active controls into the Control combobox."""
        index = 0
        self.dict_controls = {}
        values = []

        sql = """
            SELECT control_id, description
            FROM controls
            WHERE status = 1
            ORDER BY description ASC;
        """
        rs = self.engine.read(True, sql, ())

        for row in (rs or []):
            self.dict_controls[index] = row["control_id"]
            values.append(row["description"])
            index += 1

        self.cbControls["values"] = values

    def _set_values(self):
        """Populate widgets with the currently selected batch values (edit mode)."""
        try:
            key = next(key for key, value in self.dict_controls.items()
                       if value == self.selected_batch[2])
            self.cbControls.current(key)
        except Exception as e:
            pass

        # Lot
        self.lot_number.set(self.selected_batch[5])

        # Expiration (YYYY-MM-DD) -> Calendarium
        exp = self.selected_batch[6]
        try:
            if isinstance(exp, (date, datetime)):
                y, m, d = exp.year, exp.month, exp.day
            else:
                s = str(exp)
                y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
            self.expiration_date.year.set(int(y))
            self.expiration_date.month.set(int(m))
            self.expiration_date.day.set(int(d))
        except Exception as e:
            self.expiration_date.set_today()

        # Numerici e resto
        self.target.set(round(float(self.selected_batch[7]), 3))
        self.sd.set(round(float(self.selected_batch[8]), 2))
        self.description.set(self.selected_batch[9])
        self.lower.set(round(float(self.selected_batch[10]), 2))
        self.upper.set(round(float(self.selected_batch[11]), 2))
        self.rank.set(int(self.selected_batch[12]))
        self.status.set(int(self.selected_batch[13]))

    def _get_selected_control_id(self):
        """
        Return the selected control_id from the combobox, or None if not selected.
        Fail-safe: returns None when current() is -1 or mapping is missing.
        """
        try:
            idx = self.cbControls.current()
            if idx is None or idx < 0:
                return None
            return self.dict_controls.get(idx)
        except Exception as e:
            return None

    def _get_values(self):
        """
        Collect values in table order. Fail fast on invalid mandatory inputs.
        """
        # control_id must be selected
        control_id = self._get_selected_control_id()
        if control_id is None:
            raise ValueError("No control selected.")

        # expiration must be valid (Calendarium already checked upstream)
        expiration = self.expiration_date.get_date()
        if expiration is None:
            raise ValueError("Invalid expiration date.")

        # Numeric conversions: raise early if invalid (engine validators help at typing time)
        try:
            target = round(float(self.target.get()), 3)
            sd     = round(float(self.sd.get()), 2)
            lower  = round(float(self.lower.get()), 2)
            upper  = round(float(self.upper.get()), 2)
            rank   = int(self.rank.get())
        except Exception as e:
            raise ValueError(f"Invalid numeric value: {e}")

        org_id = getattr(self, "lab_id", None)  # org_id from lab context

        return [
            org_id,                          # org_id (organizations FK)
            control_id,                      # control_id
            self.selected_test_method[0],    # test_method_id
            self.selected_workstation[0],    # workstation_id
            self.lot_number.get(),           # lot_number
            expiration,                      # expiration (date)
            target,                          # target
            sd,                              # sd
            self.description.get(),          # description
            lower,                           # lower
            upper,                           # upper
            rank,                            # rank
            int(self.status.get()),          # status
            self.engine.get_log_time(),      # log_time
            self.engine.get_log_id(),        # log_id
            self.engine.get_log_ip(),        # log_ip
        ]

    def _set_compute_mode(self):
        if self.to_compute.get() == 0:  # Manual
            self.txtLower.config(state=tk.DISABLED)
            self.txtUpper.config(state=tk.DISABLED)
            self.txtSD.config(state=tk.NORMAL)
        else:  # Computed
            self.txtLower.config(state=tk.NORMAL)
            self.txtUpper.config(state=tk.NORMAL)
            # readonly se supportato, altrimenti DISABLED
            try:
                self.txtSD.config(state="readonly")
            except Exception as e:
                self.txtSD.config(state=tk.DISABLED)
        self._compute_sd()

    def _compute_sd(self):
        """Recompute SD when in 'Computed' mode: SD = (Upper - Lower) / 3 (rounded to 2)."""
        if self.to_compute.get() != 1:
            return
        try:
            upper = float(self.upper.get())
            lower = float(self.lower.get())
            if upper >= lower:
                self.sd.set(round((upper - lower) / 3.0, 2))
        except Exception as e:
            # Ignore partial/invalid inputs while typing
            pass

    def _check_lower_upper(self):
        """Basic semantic check: Lower must not exceed Upper when computing SD."""
        if self.to_compute.get() != 1:
            return True
        try:
            lo = float(self.lower.get())
            up = float(self.upper.get())
        except Exception as e:
            # Allow partial typing; upstream validation will catch on save
            return True
        if lo > up:
            msg = "Lower value exceeds upper value." + "\n" + "Cannot compute SD."
            messagebox.showwarning(self.engine.app_title, msg, parent=self)
            return False
        return True

    def on_save(self, _evt=None):
        # Required fields check (engine)
        if self.engine.on_fields_control(self.frm_main, self.engine.app_title) is False:
            return
        if self._check_lower_upper() is False:
            return

        # Date validity (fail fast)
        if not self.expiration_date.is_valid:
            msg = "Date format error." + " " + "Please check the expiration date."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        # Confirm
        if not messagebox.askyesno(self.engine.app_title, self.engine.ask_to_save, parent=self):
            return

        # Collect (may raise ValueError → show and stop)
        try:
            args = self._get_values()
        except ValueError as e:
            messagebox.showerror(self.engine.app_title, f"Validation error:\n{e}", parent=self)
            return

        # Build SQL
        if self.index is not None:
            sql = self.engine.build_sql("batches", op="update")
            args.append(self.selected_batch[0])
        else:
            sql = self.engine.build_sql("batches", op="insert")

        # Execute
        last_id = self.engine.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        target_id = self.selected_batch[0] if self.index is not None else last_id

        # Persist "remember" cache (safe)
        self._update_remember_batch_data()

        # Notify all subscribers (Observer pattern)
        # This will refresh: batches.py, main.py, and any other listener
        self.engine.notify("batch_changed", {"batch_id": target_id})

        # Close
        self.on_cancel()

    def _update_remember_batch_data(self):
        """Store the 'remember' flag and optionally the last entered values in the engine."""
        remember = self.remember_batch.get()
        if remember == 1:
            self.engine.batch_data = self._get_values()
        else:
            self.engine.batch_data = None

    def on_cancel(self, evt=None):
        super().on_cancel(evt)
