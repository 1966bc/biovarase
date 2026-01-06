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

class UI(tk.Toplevel):
    def __init__(self, parent, index=None):
        super().__init__(name="batch")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        try:
            self.transient(parent)
        except Exception as e:
            pass

        self.parent = parent
        self.index = index
        self.engine = self.nametowidget(".").engine
       
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Hotkeys
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)
        self.bind("<Alt-s>", self.on_save)
        
        self.lot_number = tk.StringVar()
        self.description = tk.StringVar()

        # Enforce max lengths as you type (delegated to engine)
        self.lot_number.trace(
            "w",
            lambda x, y, z, c=self.engine.get_lot_length(), v=self.lot_number: self.engine.limit_chars(
                c, v, x, y, z
            ),
        )
        self.description.trace(
            "w",
            lambda x, y, z, c=self.engine.get_batch_length(), v=self.description: self.engine.limit_chars(
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

        # Automatic minimum size based on widgets (NO magic numbers)
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

        # Center window
        if hasattr(self.engine, "center_window_on_screen"):
            self.engine.center_window_relative_to_parent(self)

        # Show window (end anti-flash)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        
    def _build_ui(self):
        paddings = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0)

        
        self.engine.cols_configure(self.frm_main)


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
            frm_buttons, style="App.TButton", text="Cancel", underline=0, command=self._on_cancel
        )
        self.bind("<Alt-c>", self._on_cancel)
        #self.bind("<Escape>", self._on_cancel)  # togli se preferisci solo Alt+F
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
            self._on_cancel()
            return

        self.selected_workstation = selected_workstation
        self.workstation_section_id = selected_workstation[5]

        # Compute lab_id (fail-safe: 0 on failure)
        try:
            idd = self.engine.get_idd_by_section_id(self.workstation_section_id)  # (site_id, lab_id, comp_id)
            self.lab_id = int(idd[1]) if idd else 0
        except Exception as e:
            self.lab_id = 0

        # Remember preference
        try:
            self.remember_batch.set(bool(self.engine.get_remeber_batch()))
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
            self._on_cancel()
            return

        self.selected_test_method = selected_test_method

        if self.index is not None:
            # UPDATE mode
            if not selected_batch:
                messagebox.showerror(self.engine.app_title, "Batch not found.", parent=self)
                self._on_cancel()
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

        lab_id = getattr(self, "lab_id", 0)

        return [
            lab_id,                          # lab_id
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
            msg = "The lower result is greater than the upper result.\nImpossible to compute SD."
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
            messagebox.showerror(self.engine.app_title, "Date format error. Please check the expiration date.", parent=self)
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
            messagebox.showerror(self.engine.app_title, "Save failed.", parent=self)
            return

        target_id = self.selected_batch[0] if self.index is not None else last_id

        # Refresh views (child + main). Fail-safe: wrap in try blocks.
        try:
            self.parent.set_batches()
        except Exception as e:
            pass
        
        # Cross-window refresh per Batches → Main, Batches, ecc.
        if hasattr(self.engine, "refresh_windows_for_table"):
            try:
                self.engine.refresh_windows_for_table("batches")
            except Exception as e:
                pass


        # Persist "remember" cache (safe)
        self._update_remember_batch_data()

        # Restore selection (safe)
        self._set_index(target_id)

        # Close
        self._on_cancel()

    def _update_remember_batch_data(self):
        """Store the 'remember' flag and optionally the last entered values in the engine."""
        remember = self.remember_batch.get()
        if remember == 1:
            self.engine.batch_data = self._get_values()
        else:
            self.engine.batch_data = None

    def _set_index(self, target_id):
        """
        Select the saved/updated row in both the child and main Listboxes.
        Fail-safe: return early when maps are missing.
        """

        try:
            tv = self.parent.lstBatches
        except Exception as e:
            return

        item_id = str(target_id)

        try:
            # Se l'item esiste, selezionalo e scorrilo in vista
            if item_id in tv.get_children(""):
                tv.selection_set(item_id)
                tv.focus(item_id)
                tv.see(item_id)
                tv.event_generate("<<TreeviewSelect>>")
        except Exception as e:
            pass
        
        # Main list
        try:
            main_window = self.nametowidget(".main")
            mapping = getattr(main_window, "dict_batchs", None)
            if not mapping:
                return
            idxs = [i for i, bid in mapping.items() if bid == target_id]
            if idxs:
                i = idxs[0]
                main_window.lstBatches.selection_set(i)
                main_window.lstBatches.see(i)
                main_window.lstBatches.event_generate("<<ListboxSelect>>")
        except Exception as e:
            pass

    def _on_cancel(self, evt=None):
        super().destroy()
