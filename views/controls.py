# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import views.control as control_editor


SQL = (
    "SELECT "
    "  c.control_id              AS control_id, "
    "  s.description             AS supplier_description, "
    "  c.description             AS control_description, "
    "  c.reference               AS control_reference, "
    "  c.status                  AS control_status "
    "FROM controls AS c "
    "INNER JOIN suppliers AS s ON s.supplier_id = c.supplier_id "
    "ORDER BY c.description;"
)


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
        # Singleton guard
        if getattr(self, "_is_init", False):
            return

        super().__init__(name="controls")

        # Anti-flash (build off-screen)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        
        self._is_init = True
        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self.engine.dict_instances[self.winfo_name()] = self

        self.table = "controls"
        self.primary_key = "control_id"

        self.selected_item = None
        self.child = None

        self.items = tk.StringVar()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Hotkeys
        self.bind("<Escape>", self._on_cancel)
        self.bind("<Return>", self._on_item_activated)

      
        # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        #self.transient(self.parent)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left: Treeview
        frm_left = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=6, pady=6, expand=True)

        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
        ).pack(fill=tk.X, padx=2, pady=2)

        cols = (
            ["#0", "id",          "w", False,  60,  60],
            ["#1", "Description", "w", True,  260, 260],
            ["#2", "Reference",   "w", True,  120, 120],
            ["#3", "Supplier",    "w", True,  180, 180],
        )

        self.lstItems = self.engine.get_tree(frm_left, cols)
        self.lstItems.tag_configure("is_disabled", background="light gray")
        self.lstItems.bind("<<TreeviewSelect>>", self._on_item_selected)
        self.lstItems.bind("<Double-1>", self._on_item_activated)
        self.lstItems.pack(fill=tk.BOTH, expand=True)

        # Right: Buttons
        frm_buttons = ttk.Frame(frm_main, style="App.TFrame")
        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        def add_btn(text, cmd, hotkey=None):
            btn = ttk.Button(frm_buttons, style="App.TButton", text=text, command=cmd)
            btn.pack(fill=tk.X, pady=4)
            if hotkey:
                self.bind(hotkey, cmd)

        add_btn("Add",    self._on_add,            "<Alt-a>")
        add_btn("Update", self._on_item_activated, "<Alt-u>")
        add_btn("Cancel", self._on_cancel,         "<Alt-c>")

       

    def on_open(self) -> None:
        """Configure title, reload data and center the window."""
        self.title(f"{self.winfo_name().capitalize()} Management")
        self.set_values()

    def set_values(self) -> None:
        """Load controls from the database and populate the Treeview."""
        rs = self.engine.read(True, SQL, ()) or []

        # Clear current content
        for iid in self.lstItems.get_children():
            self.lstItems.delete(iid)

        # Repopulate
        for row in rs:
            status = int(row.get("control_status", 1))
            tag = ("is_disabled",) if status != 1 else ()
            values = (
                row.get("control_description", ""),
                row.get("control_reference", ""),
                row.get("supplier_description", ""),
            )
            control_id = row.get("control_id")
            self.lstItems.insert(
                "",
                tk.END,
                iid=control_id,
                text=control_id,
                values=values,
                tags=tag,
            )

        self.items.set(f"Items: {len(self.lstItems.get_children())}")
        self.selected_item = None

    def _on_item_selected(self, _evt=None) -> None:
        sel = self.lstItems.selection()
        if not sel:
            self.selected_item = None
            return

        primary_key_value = int(sel[0])
        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            primary_key_value,
        )

    def _on_item_activated(self, _evt=None) -> None:
        sel = self.lstItems.selection()
        if not sel:
            messagebox.showwarning(
                self.engine.app_title,
                self.engine.no_selected,
                parent=self,
            )
            return

        self._on_item_selected()
        self._open_child(index=sel[0])

    def _on_add(self, _evt=None) -> None:
        self._open_child(index=None)

    def _open_child(self, index=None) -> None:
        try:
            if hasattr(self, "child") and self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass

        self.child = control_editor.UI(self, index=index)
        self.child.on_open()

    def _on_cancel(self, _evt=None) -> None:
        """Close window safely and unregister from Engine."""
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
