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

from views.child_view import ChildView


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="user")

        self.index = index   # None → INSERT, pk → UPDATE

        # Selected record (hybrid dict) in UPDATE mode
        self.selected_item = None

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)
        self.bind("<Alt-r>", self._on_reset)

        # Variables
        self.last_name = tk.StringVar()
        self.first_name = tk.StringVar()
        self.nickname = tk.StringVar()
        self.role = tk.IntVar(value=0)
        self.elapsing_time = tk.IntVar(value=0)
        self.enable_time = tk.BooleanVar(value=False)
        self.status = tk.IntVar(value=1)  # 1 = enabled

        # Layout: two columns (form + buttons)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        paddings = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame")
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        frm_left = ttk.Frame(self.frm_main, style="App.TFrame", padding=4)
        frm_left.grid(row=0, column=0, sticky="ns", **paddings)

        r, c = 0, 1
        ttk.Label(frm_left, text="Surname:").grid(row=r, column=0, sticky=tk.W)
        self.txLastName = ttk.Entry(frm_left, textvariable=self.last_name)
        self.txLastName.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="First Name:").grid(row=r, column=0, sticky=tk.W)
        ttk.Entry(frm_left, textvariable=self.first_name).grid(
            row=r, column=c, sticky=tk.EW, **paddings
        )

        r += 1
        ttk.Label(frm_left, text="Nick:").grid(row=r, column=0, sticky=tk.W)
        ttk.Entry(frm_left, textvariable=self.nickname).grid(
            row=r, column=c, sticky=tk.EW, **paddings
        )

        r += 1
        ttk.Label(frm_left, text="Level:").grid(row=r, column=0, sticky=tk.W)
        tk.Spinbox(
            frm_left,
            from_=0,
            to=9,
            width=5,
            justify=tk.CENTER,
            wrap=True,
            textvariable=self.role,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Log out time (min):").grid(
            row=r, column=0, sticky=tk.W
        )
        tk.Spinbox(
            frm_left,
            from_=0,
            to=120,
            width=5,
            justify=tk.CENTER,
            wrap=True,
            textvariable=self.elapsing_time,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Activate log out:").grid(
            row=r, column=0, sticky=tk.W
        )
        ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.enable_time,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, column=0, sticky=tk.W)
        ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        # Make entry column expand inside frm_left
        frm_left.columnconfigure(0, weight=0)
        frm_left.columnconfigure(1, weight=1)

        # Right: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self._on_save,
        ).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        if self.index is not None:
            ttk.Button(
                frm_buttons,
                style="App.TButton",
                text="Reset",
                underline=0,
                command=self._on_reset,
            ).grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        ).grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # Keep buttons the same width
        frm_buttons.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ OPEN
    def on_open(self):
        """
        Initialize the form in INSERT or UPDATE mode.

        In UPDATE mode:
            - self.parent.selected_item is expected to be a hybrid dict
              (index + column names) returned by engine.get_selected.
        """
        if self.index is not None:
            # UPDATE mode
            self.title("Update User")
            self.selected_item = self.parent.selected_item
            self._set_values()
        else:
            # INSERT mode
            self.title("Insert User")
            self.status.set(1)

        self._focus_entry()

    def _focus_entry(self):
        """Focus the surname entry and select its content."""
        try:
            self.txLastName.focus_set()
            self.txLastName.selection_range(0, "end")
        except Exception as e:
            pass

    # ------------------------------------------------------------------ VALUES
    def _set_values(self):
        """
        Populate fields from the selected record (UPDATE mode).

        expected keys in self.selected_item:
            user_id, last_name, first_name, nickname, pswrd,
            role, elapsing_time, enable_time, status
        """
        s = self.selected_item
        if not s:
            return

        try:
            self.last_name.set(s.get("last_name", ""))
            self.first_name.set(s.get("first_name", ""))
            self.nickname.set(s.get("nickname", ""))
            self.role.set(int(s.get("role", 0)))
            self.elapsing_time.set(int(s.get("elapsing_time", 0)))
            self.enable_time.set(bool(s.get("enable_time", 0)))
            self.status.set(int(s.get("status", 1)))
        except Exception as e:
            self.engine.on_log("_set_values", e, type(e), sys.modules[__name__])

    def _get_values(self):
        """
        Return current form values as list suitable for SQL arguments.

        Order must match the table definition after the primary key, e.g.:
            last_name, first_name, nickname, pswrd,
            role, elapsing_time, enable_time, status
        """
        if self.index is not None and self.selected_item:
            # Keep existing password on UPDATE
            pswrd = self.selected_item.get("pswrd")
        else:
            # Generate a new password on INSERT
            pswrd = self.engine.get_new_password()

        return [
            self.last_name.get().strip(),
            self.first_name.get().strip(),
            self.nickname.get().strip(),
            pswrd,
            int(self.role.get()),
            int(self.elapsing_time.get()),
            int(bool(self.enable_time.get())),
            int(self.status.get()),
        ]

    # ------------------------------------------------------------------ SAVE
    def _on_save(self, evt=None):
        """
        Save handler (INSERT or UPDATE):

            1. Validate fields.
            2. Check nickname uniqueness.
            3. Confirm with user.
            4. Build SQL.
            5. Execute.
            6. Reload parent list and reselect item.
        """
        title = self.engine.app_title

        # 1) Generic field validation
        if self.engine.on_fields_control(self.frm_main, title) is False:
            return

        # 2) Nickname uniqueness check
        if self._check_nicknam() == 0:
            return

        # 3) Confirmation dialog
        if not messagebox.askyesno(
            title,
            self.engine.ask_to_save,
            parent=self,
        ):
            messagebox.showinfo(
                title,
                self.engine.abort,
                parent=self,
            )
            return

        # 4) Build SQL and arguments
        args = self._get_values()

        if self.index is not None:
            # UPDATE path → append primary key at the end
            sql = self.engine.build_sql(self.parent.table, op="update")
            pk = int(self.selected_item.get("user_id"))
            args.append(pk)
            target_id = pk
        else:
            # INSERT path
            sql = self.engine.build_sql(self.parent.table, op="insert")
            target_id = None  # will be resolved from last_id

        try:
            last_id = self.engine.write(sql, tuple(args))

            # 5) Refresh parent list
            self.parent._load_items()

            # Determine which PK should be reselected
            if self.index is None and last_id is not None:
                target_id = int(last_id)

            # 6) Reselect row in parent (if possible)
            self._reselect_in_parent(target_id)

            # Close editor
            self.on_cancel()

        except Exception as exc:
            messagebox.showerror(title, f"Save error:\n{exc}", parent=self)

    def _reselect_in_parent(self, target_pk=None):
        """
        Reselect item in parent using only its Listbox (lstItems):

            - UPDATE: uses PK of selected_item.
            - INSERT: uses target_pk (last inserted id).
        """
        if target_pk is None:
            # For UPDATE, recompute from selected_item
            if self.index is not None and self.selected_item:
                target_pk = int(self.selected_item.get("user_id"))
            else:
                return

        lst_index = next(
            (k for k, v in self.parent.dict_items.items() if v == target_pk),
            None,
        )
        if lst_index is None:
            return

        self.parent.lstItems.see(lst_index)
        self.parent.lstItems.selection_set(lst_index)
        self.parent.on_item_selected()

    
    def _on_reset(self, _evt=None):
        """Reset password for the current user (UPDATE mode only)."""
        if self.index is None or not self.selected_item:
            messagebox.showwarning(
                self.engine.app_title,
                "No user loaded for password reset.",
                parent=self,
            )
            return

        try:
            pswrd = self.engine.get_new_password()
            sql = "UPDATE users SET pswrd = ? WHERE user_id = ?;"
            args = (
                pswrd,
                int(self.selected_item.get("user_id")),   # <-- FIX: use child copy
            )
            self.engine.write(sql, args)
            msg = "Password reset."
            messagebox.showinfo(self.engine.app_title, msg, parent=self)
        except Exception as e:
            self.engine.on_log("_on_reset", e, type(e), sys.modules[__name__])

    def _check_nicknam(self):
        """
        Check if nickname is already used by another user.

        Returns:
            1  → nickname is valid (unique or same as current user in UPDATE)
            0  → nickname is already taken by another user
        """
        nickname = self.nickname.get().strip()
        if not nickname:
            # Let on_fields_control catch empty fields
            return 1

        sql = "SELECT user_id, nickname FROM users WHERE nickname = ?;"
        try:
            row = self.engine.read(False, sql, (nickname,))
        except Exception as e:
            self.engine.on_log("_check_nickname", e, type(e), sys.modules[__name__])
            return 1

        if not row:
            # No user with this nickname → OK
            return 1

        existing_id = int(row.get("user_id"))

        # If UPDATE and same user, it's fine
        if self.index is not None and self.selected_item:
            current_id = int(self.selected_item.get("user_id"))
            if existing_id == current_id:
                return 1

        # Otherwise nickname is taken
        msg = f"Call sign {nickname} has already been assigned!"
        messagebox.showwarning(self.engine.app_title, msg, parent=self)
        return 0

    def on_cancel(self, evt=None):
        """Close dialog."""
        super().on_cancel(evt)
