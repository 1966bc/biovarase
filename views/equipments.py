#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import views.equipment as ui


SQL = """
    SELECT equipment_id, supplier_id, description, status
    FROM equipments
    ORDER BY description ASC;
"""


class UI(tk.Toplevel):

    _instance = None

    def __new__(cls, parent):
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception as e:
                cls._instance = None
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent):
        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(name="equipments")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        
        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        self.table = "equipments"
        self.primary_key = "equipment_id"

        self.child = None
        self.dict_items = {}        # list index → equipment_id
        self.selected_item = None
        self.items = tk.StringVar()

        self.resizable(True, True)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Alt-c>", self._on_cancel)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        # Set reasonable window size for table display
        self.update_idletasks()
        min_width = 600   # Wide enough for all columns (40+10+12+25+10 + spacing)
        min_height = 400  # Show ~20-25 rows comfortably
        self.minsize(min_width, min_height)
        
        # Set initial geometry (can be resized by user)
        self.geometry(f"{min_width}x{min_height}")

    def _build_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left: list
        frm_left = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), expand=True)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL)
        self.lstItems = tk.Listbox(
            frm_left,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self._on_item_activated)
        self.bind("<Return>", self._on_item_activated)

        # Right: buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)

        def add_btn(text, cmd, *, underline=None, shortcut=None):
            btn = ttk.Button(frm_buttons, text=text, command=cmd, underline=underline)
            btn.pack(fill=tk.X, padx=5, pady=5)
            if shortcut:
                self.bind(shortcut, lambda e, c=cmd: c())
            return btn

        add_btn("Add", self._on_add, underline=0, shortcut="<Alt-a>")
        add_btn("Update", self._on_item_activated, underline=0, shortcut="<Alt-u>")
        add_btn("Cancel", self._on_cancel, underline=0, shortcut="<Alt-c>")

        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

      
    def on_open(self):
     
        self.title(f"{self.winfo_name().capitalize()} Management")
        self.set_values()

    def set_values(self):
        """Load all equipments."""
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()

        try:
            rows = self.engine.read(True, SQL, ()) or []
        except Exception as e:
            try:
                self.engine.on_log(
                    "equipments.set_values:read_dict",
                    e,
                    type(e),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            rows = []

        for index, row in enumerate(rows):
            eq_id = row["equipment_id"]
            description = row.get("description", "")
            status = int(row.get("status", 1))

            self.lstItems.insert(tk.END, description)

            if status != 1:  # inactive
                self.lstItems.itemconfig(index, {"bg": "light gray"})

            self.dict_items[index] = eq_id

        msg = f"Items: {self.lstItems.size()}"
        self.items.set(msg)

    def on_item_selected(self, _evt=None):
        """Fetch selected equipment from DB (hybrid dict)."""
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return

        idx = sel[0]
        pk = self.dict_items.get(idx)
        if pk is None:
            self.selected_item = None
            return

        try:
            self.selected_item = self.engine.get_selected(
                self.table,
                self.primary_key,
                pk,
            )
        except Exception as e:
            try:
                self.engine.on_log(
                    "equipments.on_item_selected:get_selected",
                    e,
                    type(e),
                    sys.modules[__name__],
                )
            except Exception as e:
                pass
            self.selected_item = None

    def _on_item_activated(self, _evt=None):
        """Open editor in UPDATE mode."""
        sel = self.lstItems.curselection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        idx = sel[0]
        self._open_child(idx)

    def _on_add(self, _evt=None):
        """Open editor in INSERT mode."""
        self._open_child(None)

    def _open_child(self, index=None):
        """Destroy previous child and open a new editor window."""

        # Destroy existing child if open
        try:
            if self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass

        # INSERT mode
        if index is None:
            self.child = ui.UI(self, index=None)
            self.child.on_open()
            return

        # UPDATE mode
        pk = self.dict_items.get(index)
        if pk is None:
            return

        self.child = ui.UI(self, index=pk)
        self.child.on_open()


    def _on_cancel(self, _evt=None):
        """Close window safely and unregister from engine."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
