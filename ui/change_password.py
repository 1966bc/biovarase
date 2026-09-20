# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk

from ui.parent_view import ParentView
from tkinter import ttk
from tkinter import messagebox
import bcrypt


class UI(ParentView):

    def __init__(self, parent):        
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(parent, name="change_password")

         # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
       
        self._is_init = True
        self.parent = parent 
        self.engine = self.nametowidget(".").engine
               
        self.resizable(False, False)
        
        self.old_password = tk.StringVar()
        self.new_password = tk.StringVar()
        self.repeat_password = tk.StringVar()

        self.bind("<Escape>", self.__on_cancel)
        self.protocol("WM_DELETE_WINDOW", self.__on_cancel)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.show()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        
    def _build_ui(self):
        """Constructs the user interface (Labels, Entry fields, and Buttons)."""
        paddings = {"padx": 10, "pady": 5} 

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=15)
        self.frm_main.grid(row=0, column=0, sticky=tk.NSEW)

        frm_input = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_input.columnconfigure(1, weight=1) 
        frm_input.grid(row=0, column=0, sticky=tk.NSEW, **paddings)

        r = 0
        c = 1
        
        # Old Password
        ttk.Label(frm_input, text="Old Password:").grid(row=r, column=0, sticky=tk.W, **paddings)
        self.txtOldPassword = ttk.Entry(frm_input, show="*", textvariable=self.old_password, width=30)
        self.txtOldPassword.grid(row=r, column=c, sticky=tk.EW, **paddings)
        self.txtOldPassword.focus_set()

        r += 1
        # New Password
        ttk.Label(frm_input, text="New Password:").grid(row=r, column=0, sticky=tk.W, **paddings)
        self.txtNewPassword = ttk.Entry(frm_input, show="*", textvariable=self.new_password, width=30)
        self.txtNewPassword.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        # Repeat Password
        ttk.Label(frm_input, text="Confirm Password:").grid(row=r, column=0, sticky=tk.W, **paddings)
        self.txtRepeatPassword = ttk.Entry(frm_input, show="*", textvariable=self.repeat_password, width=30)
        self.txtRepeatPassword.grid(row=r, column=c, sticky=tk.EW, **paddings)

        # Frame for Buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=1, column=0, sticky=tk.E, pady=10) # Positioned below the Entry fields

        r = 0
        c = 0
        
        # Save Button
        btn_save = ttk.Button(frm_buttons, style="App.TButton", text="Save", underline=0, command=self.on_save)
        btn_save.grid(row=r, column=c, sticky=tk.EW, padx=5, pady=5)
        self.bind("<Alt-s>", self.on_save)

        c += 1
        # Cancel Button
        btn_cancel = ttk.Button(frm_buttons, style="App.TButton", text="Cancel", underline=0, command=self.__on_cancel)
        btn_cancel.grid(row=r, column=c, sticky=tk.EW, padx=5, pady=5)
        self.bind("<Alt-c>", self.__on_cancel, add="+") # Use add="+" to avoid overwriting existing bindings

    def on_open(self):
        self.title("Change Password")
        self.after_idle(self.txtOldPassword.focus_set)

    def _fetch_current_hash(self):
        """Retrieves the bcrypt hash (string) of the logged-in user or None."""
        if not (hasattr(self.engine, 'log_user') and self.engine.log_user):
            messagebox.showerror(self.title(), "User not found.", parent=self)
            return None

        user_id = self.engine.log_user["user_id"]
        sql = "SELECT pswrd FROM users WHERE user_id = ?;"
        row = self.engine.db.read(False, sql, (user_id,))
        return row["pswrd"] if row else None

    def _match_old_password(self):
        """Compares the old entered password with the stored hash (using bcrypt)."""
        stored_hash = self._fetch_current_hash()
        if not stored_hash:
            return False
            
        # Tkinter strings must be encoded to bytes for bcrypt.checkpw
        old_pw_bytes = self.old_password.get().strip().encode("utf-8")
        # The stored hash string must also be encoded to bytes
        stored_hash_bytes = stored_hash.encode("utf-8")
        
        try:
            return bcrypt.checkpw(old_pw_bytes, stored_hash_bytes)
        except Exception as e:
            return False

    def _hash_new_password(self, plain_password: str) -> str:
        """Generates a bcrypt hash and returns it as a utf-8 string (ready for DB storage)."""
        pw_bytes = plain_password.strip().encode("utf-8")
        # Using a default work factor (rounds=12)
        hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12)) 
        return hashed.decode("utf-8")

    def on_save(self, evt=None):
        """Handles the save logic, including password validation and DB update."""
        
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.tools.on_fields_control(self.frm_main, self.parent.title()) is False:
                return
            
        if not messagebox.askyesno(self.parent.title(),
                                   getattr(self.engine, "ask_to_save", "Save changes?"),
                                   parent=self):
            messagebox.showinfo(self.parent.title(),
                                getattr(self.engine, "abort", "Abort."),
                                parent=self)
            return

        # 1) Verify old password
        if not self._match_old_password():
            messagebox.showinfo(self.parent.title(),
                                "Current password is incorrect.", parent=self)
            self.txtOldPassword.focus_set()
            return

        # 2) Verify new password meets criteria (length and match)
        new_pw = self.new_password.get().strip()
        rep_pw = self.repeat_password.get().strip()

        if len(new_pw) < 8:
            messagebox.showinfo(self.parent.title(),
                                "Password must be at least 8 characters.", parent=self)
            self.txtNewPassword.focus_set()
            return

        if new_pw != rep_pw:
            messagebox.showinfo(self.parent.title(),
                                "Passwords do not match.", parent=self)
            self.txtRepeatPassword.focus_set()
            return

        # 3) Update DB with new bcrypt hash
        hashed = self._hash_new_password(new_pw)
        user_id = self.engine.log_user["user_id"]
        sql = "UPDATE users SET pswrd = ? WHERE user_id = ?;"
        result = self.engine.db.write(sql, (hashed, user_id))
        if result is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.tools.get_database_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(self.parent.title(), msg, parent=self)
            return

        messagebox.showinfo(self.parent.title(), "Password changed successfully.", parent=self)
        self.on_cancel()

    def __on_cancel(self, evt=None):
        """Destroys the window and resets the Singleton reference."""
        UI._instance = None
        self.destroy()
