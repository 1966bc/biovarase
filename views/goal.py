# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV (refactor: unified child logic, no external dicts)
# -----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class UI(tk.Toplevel):
    """
    Analytical Goal Editor (child window, NOT a singleton).

    Behavior:
        - INSERT if no row exists in goals for this test_method.
        - UPDATE if a goals row already exists.

    The master opens this window with:

        self.child = goal_editor.UI(self, index=test_method_id)
        self.child.on_open()

    The child retrieves all data autonomously using engine.get_selected.
    """

    def __init__(self, parent, index=None):
        super().__init__(name="goal")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        try:
            self.transient(parent)
        except Exception as e:
            pass

        # References
        self.parent = parent
        self.index = index          # test_method_id
        self.engine = self.nametowidget(".").engine

        # Tk variables
        self.cvw      = tk.DoubleVar()
        self.cvb      = tk.DoubleVar()
        self.imp      = tk.DoubleVar()
        self.bias     = tk.DoubleVar()
        self.teap005  = tk.DoubleVar()
        self.teap001  = tk.DoubleVar()
        self.to_export = tk.BooleanVar()
        self.status    = tk.BooleanVar()

        # DB dicts
        self.selected_test_method = None
        self.selected_test = None
        self.selected_goal = None

        # Float validation provided by engine
        self.float_vcmd = self.engine.get_float_vcmd(self)

        # Window configuration
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Global key bindings
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # Build UI
        self._build_ui()

        # Autosize
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

        # Center window
        try:
            if hasattr(self.engine, "center_window_relative_to_parent"):
                self.engine.center_window_relative_to_parent(self)
        except Exception as e:
            pass

        # Show (end anti-flash)
        self.deiconify()
        self.attributes("-alpha", 1.0)

    # ---------------------------------------------------------------------
    # UI BUILD
    # ---------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky=tk.NS)
        frm_left.columnconfigure(1, weight=1)

        r, c = 0, 1

        def add_float_row(label_text, var_ref):
            nonlocal r
            ttk.Label(frm_left, text=label_text).grid(row=r, column=0, sticky=tk.W)
            e = ttk.Entry(
                frm_left,
                width=8,
                justify=tk.CENTER,
                validate="key",
                validatecommand=self.float_vcmd,
                textvariable=var_ref,
            )
            e.grid(row=r, column=c, sticky="w", **pad)
            r += 1
            return e

        self.txCvw    = add_float_row("cvw:",            self.cvw)
        self.txCvb    = add_float_row("cvb:",            self.cvb)
        self.txImp    = add_float_row("Imp %:",          self.imp)
        self.txBias   = add_float_row("Bias %:",         self.bias)
        self.txTeaP05 = add_float_row("TEa % p<0.05:",   self.teap005)
        self.txTeaP01 = add_float_row("TEa % p<0.01:",   self.teap001)

        ttk.Label(frm_left, text="To export:").grid(row=r, column=0, sticky=tk.W)
        self.chkExport = ttk.Checkbutton(frm_left, variable=self.to_export, onvalue=1, offvalue=0)
        self.chkExport.grid(row=r, column=c, sticky="w", **pad)
        r += 1

        ttk.Label(frm_left, text="Status:").grid(row=r, column=0, sticky=tk.W)
        self.chkStatus = ttk.Checkbutton(frm_left, variable=self.status, onvalue=1, offvalue=0)
        self.chkStatus.grid(row=r, column=c, sticky="w", **pad)

        # Buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky=tk.NS, padx=6)

        ttk.Button(
            frm_buttons, style="App.TButton", text="Save",
            underline=0, command=self._on_save
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        ttk.Button(
            frm_buttons, style="App.TButton", text="Cancel",
            underline=0, command=self._on_cancel
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=4)

    # ---------------------------------------------------------------------
    # LIFECYCLE
    # ---------------------------------------------------------------------
    def on_open(self):
        """
        Open/update the window:
            - Always retrieve test_method from index.
            - Retrieve test from parent (if available).
            - Retrieve goal row (insert/update mode).
        """
        try:
            self.transient(self.parent)
        except Exception as e:
            pass

        # Retrieve test_method via engine
        try:
            self.selected_test_method = self.engine.get_selected(
                "test_methods", "test_method_id", int(self.index)
            )
        except Exception as e:
            messagebox.showerror(
                self.engine.app_title,
                f"Cannot load Test Method:\n{e}",
                parent=self,
            )
            return

        # Retrieve surrounding test (optional)
        self.selected_test = getattr(self.parent, "selected_test", {})

        # Load goal row
        try:
            sql = "SELECT * FROM goals WHERE test_method_id = ? LIMIT 1;"
            self.selected_goal = self.engine.read(False, sql, (self.index,))
        except Exception as e:
            self.selected_goal = None

        # Determine test description for window title
        test_descr = self.selected_test.get("description", "")
        if not test_descr:
            test_descr = f"Method {self.index}"

        # UPDATE vs INSERT
        if self.selected_goal:
            self.title(f"Update Analytical Goal for {test_descr}")
            self._set_values()
        else:
            self.title(f"Insert Analytical Goal for {test_descr}")
            self._clear_fields()
            self.status.set(1)

        self.after_idle(self.txCvw.focus_set)

    # ---------------------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------------------
    def _clear_fields(self):
        """Reset all fields for INSERT mode."""
        for var in (self.cvw, self.cvb, self.imp, self.bias, self.teap005, self.teap001):
            var.set(0.0)
        self.to_export.set(0)
        self.status.set(1)

    def _set_values(self):
        """Populate widgets from selected_goal (dict)."""
        g = self.selected_goal
        self.cvw.set(round(float(g["cvw"]), 2))
        self.cvb.set(round(float(g["cvb"]), 2))
        self.imp.set(round(float(g["imp"]), 2))
        self.bias.set(round(float(g["bias"]), 2))
        self.teap005.set(round(float(g["teap005"]), 2))
        self.teap001.set(round(float(g["teap001"]), 2))
        self.to_export.set(int(g["to_export"]))
        self.status.set(int(g["status"]))

    def _get_values(self):
        """
        Collect all fields for SQL operations.

        Returns list:
            [
                test_method_id, cvw, cvb, imp, bias,
                teap005, teap001, to_export, status
            ]
        """
        def as_float(v):
            try:
                return float(v.get())
            except Exception as e:
                return 0.0

        return [
            self.selected_test_method["test_method_id"],
            as_float(self.cvw),
            as_float(self.cvb),
            as_float(self.imp),
            as_float(self.bias),
            as_float(self.teap005),
            as_float(self.teap001),
            int(self.to_export.get()),
            int(self.status.get()),
        ]

    # ---------------------------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------------------------
    def _on_save(self, _evt=None):
        """INSERT or UPDATE analytical goal with UNIQUE fallback."""

        # Optional global validation
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

        # Confirmation
        if not messagebox.askyesno(
            self.engine.app_title,
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            return

        args = self._get_values()

        try:
            if self.selected_goal:
                # UPDATE
                sql = self.engine.build_sql("goals", op="update")
                args.append(self.selected_goal["goal_id"])
                self.engine.write(sql, args)

            else:
                # INSERT → fallback to UPDATE on UNIQUE
                try:
                    sql = self.engine.build_sql("goals", op="insert")
                    self.engine.write(sql, args)

                except Exception as e:
                    if "Duplicate entry" in str(e) or "1062" in str(e):
                        row = self.engine.read(
                            False,
                            "SELECT * FROM goals WHERE test_method_id = ? LIMIT 1;",
                            (args[0],),
                        )
                        if row:
                            sql = self.engine.build_sql("goals", op="update")
                            args.append(row["goal_id"])
                            self.engine.write(sql, args)
                        else:
                            raise
                    else:
                        raise

            # Notify parent to refresh
            if hasattr(self.parent, "on_test_method_selected"):
                self.parent.on_test_method_selected()

            self._on_cancel()

        except Exception as exc:
            messagebox.showerror(
                self.engine.app_title,
                f"Save error:\n{exc}",
                parent=self,
            )

    def _on_cancel(self, _evt=None):
        try:
            super().destroy()
        except Exception as e:
            pass
