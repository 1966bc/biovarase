# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import tkinter as tk

from ui.child_view import ChildView
from tkinter import ttk
from tkinter import messagebox


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="sample")
        self.index = index  # None → INSERT, pk → UPDATE

        self.selected_item: dict | None = None
        
        self.resizable(False, False)        # Hotkeys
        self.bind("<Escape>", self.on_cancel) #Alt+F4
        self.bind("<Alt-c>", self.on_cancel)
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)
        
    
        self.symbol = tk.StringVar()
        self.symbol.trace("w", lambda x, y, z, c=1, v=self.symbol: self.engine.tools.limit_chars(c, v, x, y, z))
        
        self.description = tk.StringVar()
        self.status = tk.BooleanVar()
        
        # Root grid config (two columns: form + buttons)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

         # --- Build interface ------------------------------------------------
        self._build_ui()
        self.show()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
       
    def _build_ui(self):
        
        paddings = {"padx": 8, "pady": 8}

        # Main frame
        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        self.frm_main.grid(row=0, column=0, sticky="nsew")
        
        # Left: fields
        frm_left = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_left.grid(row=0, column=0, sticky="ns", **paddings)

        r = 0
        ttk.Label(frm_left, text="Symbol:").grid(row=r, sticky=tk.W)
        self.ent_Symbol = ttk.Entry(frm_left, textvariable=self.symbol)
        self.ent_Symbol.grid(row=r, column=1, sticky="ew", **paddings)

        r += 1
        ttk.Label(frm_left, text="Description:").grid(row=r, sticky=tk.W)
        self.txtDescription = ttk.Entry(frm_left, textvariable=self.description)
        self.txtDescription.grid(row=r, column=1, sticky="ew", **paddings)

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, sticky=tk.W)
        chk_status = ttk.Checkbutton(frm_left, onvalue=1, offvalue=0, variable=self.status,)
        chk_status.grid(row=r, column=1, sticky="ew", **paddings)

        # Right: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        btn_save = ttk.Button(
            frm_buttons, style="App.TButton", text="Save", underline=0, command=self._on_save
        )
        btn_save.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        btn_cancel = ttk.Button(
            frm_buttons, style="App.TButton", text="Cancel", underline=0, command=self.on_cancel
        )
        btn_cancel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    
        # Keep buttons the same width
        frm_buttons.columnconfigure(0, weight=1)

    def on_open(self):

        if self.index is not None:
            # UPDATE mode
            self.title("Update Sample")
            # Expect parent.selected_item to be set (tuple row)
            self.selected_item = getattr(self.parent, "selected_item", None)
            self._set_values()
        else:
            # INSERT mode
            self.title("Add Sample")
            self.status.set(True)

        self._focus_entry()
        
    def _focus_entry(self):
        try:
            self.ent_Symbol.focus_set()
            self.ent_Symbol.selection_range(0, 'end')
        except Exception as e:
            pass
        
    def _set_values(self,):
        """Populate fields from the selected record (UPDATE mode)."""
        if not self.selected_item:
            return
        
        self.symbol.set(self.selected_item[1])
        self.description.set(self.selected_item[2])
        self.status.set(bool(self.selected_item[2]))


    def _get_values(self):
        """Return current form values as a list suitable for SQL arguments."""
        return [self.symbol.get().strip(),
                self.description.get().strip(),
                int(self.status.get())]

    def _on_save(self, _evt=None):
        """
        Validate → confirm → write (INSERT/UPDATE) → refresh parent list (_set_values)
        → reselect item using parent.lst_items only (no dict mapping).
        """
        # Optional global validation hook
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.tools.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

         # Uniqueness check for symbol
        if self.check_symbol() == 0:
            return

        # Uniqueness check for description
        if self._check_description() == 0:
             return

        if not messagebox.askyesno(
            self.engine.app_title,
            getattr(self.engine, "ask_to_save", "Do you want to save?"),
            parent=self,
        ):
            messagebox.showinfo(
                self.engine.app_title,
                getattr(self.engine, "abort", "Abort."),
                parent=self,
            )
            return

        args = self._get_values()

        # Build SQL with the application helper (insert/update)
        if self.index is not None:
            # UPDATE path → append primary key at the end
            sql = self.engine.build_sql(self.parent.table, op="update")
            args.append(self.selected_item[0])
        else:
            # INSERT path
            sql = self.engine.build_sql(self.parent.table, op="insert")

        last_id = self.engine.db.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.tools.get_database_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        self.parent.set_values()
        self._reselect_in_parent(last_id if self.index is None else None)
        self.on_cancel()


    def check_symbol(self) -> int:
        """
        Enforce symbol (sample) uniqueness on 'samples'.

        - If another row already has the same symbol, warn and block.
        - Allow same row on UPDATE (same primary key).
        Returns: 0 on duplicate found, 1 on OK.
        """
        symbol = self.symbol.get().strip()

        sql = """
            SELECT sample_id, sample
            FROM samples
            WHERE sample = ?;
        """

        # read_dict con fetch=True → lista di dict
        rs = self.engine.db.read(True, sql, (symbol,)) or []

        if not rs:
            return 1  # nessun duplicato

        row = rs[0]                      # primo (e unico) record
        existing_id = row.get("sample_id")

        # UPDATE: stesso record → ok
        if self.index is not None and isinstance(self.selected_item, dict):
            current_id = self.selected_item.get("sample_id")
            if existing_id == current_id:
                return 1

        messagebox.showwarning(
            self.engine.app_title,
            f"Symbol {symbol} has already been assigned!",
            parent=self,
        )
        return 0




    def _check_description(self) -> int:
        """
        Enforce description uniqueness on 'samples'.

        - Normalize description (trim + compress spaces).
        - Require non-empty.
        - On UPDATE: if normalized value is identical to the current one, allow.
        - Otherwise, block if another row already has the same description.

        Returns:
            1 = OK
            0 = duplicate or invalid
        """

        raw = self.description.get()
        norm = self._get_clean_text(raw, compress=True)

        # Must contain something
        if not norm:
            messagebox.showwarning(
                self.engine.app_title,
                "Description is required.",
                parent=self,
            )
            return 0

        # If UPDATE → allow same record with same normalized description
        if self.index is not None and isinstance(self.selected_item, dict):
            current = self.selected_item.get("description") or ""
            current_norm = self._get_clean_text(current, compress=True)

            if norm.casefold() == current_norm.casefold():
                self.description.set(norm)
                return 1

        # Check duplicates using read_dict (PROJECT_RULES)
        sql = """
            SELECT sample_id, description
            FROM samples
            WHERE description = ?
            LIMIT 1;
        """

        rs = self.engine.db.read(False, sql, (norm,)) or []

        if rs:
            row = rs[0]
            existing_id = row.get("sample_id")

            duplicate = False

            if self.index is None:
                # INSERT → any existing record is a duplicate
                duplicate = True
            else:
                # UPDATE → duplicate only if found record is not this record
                current_id = (
                    self.selected_item.get("sample_id")
                    if isinstance(self.selected_item, dict)
                    else None
                )
                if existing_id is not None and existing_id != current_id:
                    duplicate = True

            if duplicate:
                messagebox.showwarning(
                    self.engine.app_title,
                    f"Description '{norm}' has already been assigned!",
                    parent=self,
                )
                return 0

        # All ok → write back normalized description
        self.description.set(norm)
        return 1


    def _get_clean_text(self, s, *, compress = False):
        s = (s or "").strip()
        return " ".join(s.split()) if compress else s

    def _reselect_in_parent(self, last_id=None):
        """
        Reselect item in parent using only its Listbox (lstItems):
        - UPDATE: use the original index (self.index).
        - INSERT: select the last row (last_id).
        """
        # Decide the target PK
        target_pk = self.selected_item[0] if self.index is not None else last_id
        if target_pk is None:
            return

        # Find listbox index matching the PK
        lst_index = next((k for k, v in self.parent.dict_items.items() if v == target_pk), None)
        if lst_index is None:
            return

        lb = self.parent.lstItems
        lb.focus_set()
        lb.see(lst_index)
        lb.selection_clear(0, "end")
        lb.selection_set(lst_index)
        lb.activate(lst_index)
        # Direct callback
        self.parent.on_item_selected()
        # Alternative: lb.event_generate("<<ListboxSelect>>")
  
    def on_cancel(self, _evt=None):
        """Close the window and clear the Singleton reference."""
        type(self)._instance = None
        self.destroy()
