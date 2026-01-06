# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   autumn MMXXV
#-----------------------------------------------------------------------------
"""
Generic lookup list UI for simple tables with:
    - primary key (auto-detected via Engine)
    - description field (customizable)
    - status flag (tinyint(1))

Expected table schema:
    pk_field    : primary key (auto-inferred, e.g. unit_id, action_id, ...)
    description : text field
    status      : tinyint(1) active/inactive
"""

import tkinter as tk
from tkinter import ttk, messagebox

from views.editor import Editor


class LookupUI(tk.Toplevel):
    """
    Generic list window for simple lookup tables.

    Usage pattern (PROJECT_RULES compliant):

        win = LookupUI(parent, table="units", ui_name="units")
        win.show()   # explicit lifecycle entry point

    The class abstracts:
        - loading table rows
        - mapping listbox index → primary key
        - opening child editor windows
        - window lifecycle management
    """

    _instance = None

    def __new__(cls, parent, *args, **kwargs):
        """
        Class-level singleton: ensures one instance per lookup window type.

        If the previous instance still exists, reuse it.
        Otherwise, create a new one.

        NOTE:
        - Lifecycle entry point must be explicit via show()
        - __init__ must NOT call on_open() (PROJECT_RULES)
        """
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    return cls._instance
            except Exception as e:
                cls._instance = None

        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(
        self,
        parent,
        table,
        *,
        desc_field="description",
        label_text=None,
        ui_name=None,
    ):
        """
        Initialize the lookup UI.

        NOTE:
        - __init__ must NOT perform data loading
        - __init__ must NOT call on_open()
        - Data loading MUST be invoked via show()
        """

        if getattr(self, "_is_init", False):
            self.parent = parent
            return

        super().__init__(name=ui_name or table)

        self.engine = self.nametowidget(".").engine
        self._is_init = True
        self.parent = parent

        # Table metadata
        self.table = table
        self.primary_key = self.engine.get_primary_key(self.table)
        self.desc_field = desc_field
        self.label_text = label_text or self._derive_label_from_table(table)

        # Child editor instance
        self.child = None

        # Index → PK mapping
        self.dict_items = {}
        self.selected_item = None
        self.items = tk.StringVar()

        # Register instance into Engine
        self.engine.dict_instances[self.winfo_name()] = self

        # Window configuration
       
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        # Stabilize real geometry, then center and show
        self.update_idletasks()
        self.engine.center_window_on_screen(self)
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.lift()
        #self.update_idletasks()
        #self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        # Set reasonable window size for table display
        self.update_idletasks()
        min_width = 600   # Wide enough for all columns (40+10+12+25+10 + spacing)
        min_height = 400  # Show ~20-25 rows comfortably
        self.minsize(min_width, min_height)
        
        # Set initial geometry (can be resized by user)
        self.geometry(f"{min_width}x{min_height}")

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def show(self):
        """
        Explicit lifecycle entry point.

        MUST be called by the caller after instantiating LookupUI.
        Complies with PROJECT_RULES: no automatic on_open() from __init__.
        """
        self.after_idle(self.focus_set)
        self.on_open()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _derive_label_from_table(self, table_name):
        """
        Generate a singular, human-friendly label from the table name.
        Examples:
            units      -> Unit
            actions    -> Action
            categories -> Category
        """
        name = table_name.strip().lower()
        if name.endswith("ies"):
            return name[:-3].capitalize() + "y"
        if name.endswith("s"):
            return name[:-1].capitalize()
        return name.capitalize()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Build static window layout."""
        frm_main = ttk.Frame(self, style="App.TFrame", padding=8)
        frm_main.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Left panel
        frm_left = ttk.Frame(frm_main, style="App.TFrame", relief=tk.GROOVE, padding=8)
        ttk.Label(
            frm_left,
            style="App.TLabel",
            textvariable=self.items,
            relief=tk.GROOVE,
        ).pack(fill=tk.X, expand=0)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8), pady=5, expand=True)

        sb = ttk.Scrollbar(frm_left, orient=tk.VERTICAL)

        self.lstItems = tk.Listbox(
            frm_left,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        self.lstItems.bind("<<ListboxSelect>>", self.on_item_selected)
        self.lstItems.bind("<Double-Button-1>", self.on_item_activated)
        sb.config(command=self.lstItems.yview)

        self.lstItems.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel: buttons
        frm_buttons = ttk.Frame(
            frm_main,
            style="App.TFrame",
            relief=tk.GROOVE,
            padding=8,
        )

        def add_btn(text, cmd, underline=None, shortcut=None):
            btn = ttk.Button(frm_buttons, text=text, command=cmd, underline=underline)
            btn.pack(fill=tk.X, padx=5, pady=5)
            if shortcut:
                self.bind(shortcut, lambda e, c=cmd: c())
            return btn

        add_btn("Add",    self.on_add,            underline=0, shortcut="<Alt-a>")
        add_btn("Update", self.on_item_activated, underline=0, shortcut="<Alt-u>")
        add_btn("Cancel", self._on_cancel,        underline=0, shortcut="<Alt-c>")

        self.bind("<Return>", self.on_item_activated)

        frm_buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def on_open(self):
        """
        Called when the window is displayed.

        Loads table rows and updates the title.
        """
        self.title(f"{self.label_text}s Management")
        self._set_values()

    def _set_values(self):
        """
        Populate the listbox with rows from the table.
        """
        self.lstItems.delete(0, tk.END)
        self.dict_items.clear()
        self.selected_item = None

        sql = """
            SELECT
                {pk} AS pk,
                {desc}  AS description,
                status
            FROM {table}
            ORDER BY {desc} ASC;
        """.format(
            pk=self.primary_key,
            desc=self.desc_field,
            table=self.table,
        )

        rows = self.engine.read(True, sql, ()) or []
        for index, row in enumerate(rows):
            self.lstItems.insert(tk.END, row["description"])
            if row.get("status", 1) != 1:
                self.lstItems.itemconfig(index, {"bg": "light gray"})
            self.dict_items[index] = row["pk"]

        self.items.set("Items: {0}".format(self.lstItems.size()))

    # ------------------------------------------------------------------
    # Listbox handlers
    # ------------------------------------------------------------------
    def on_item_selected(self, _evt=None):
        """
        Update self.selected_item when listbox selection changes.
        """
        sel = self.lstItems.curselection()
        if not sel:
            self.selected_item = None
            return

        idx = sel[0]
        pk = self.dict_items.get(idx)
        if pk is None:
            self.selected_item = None
            return

        self.selected_item = self.engine.get_selected(
            self.table,
            self.primary_key,
            pk,
        )

    def on_item_activated(self, _evt=None):
        """
        Double-click or Enter: open the editor window for the selected item.
        """
        sel = self.lstItems.curselection()
        if not sel:
            messagebox.showwarning(
                self.nametowidget(".").title(),
                self.engine.no_selected,
                parent=self,
            )
            return

        idx = sel[0]
        if 0 <= idx < self.lstItems.size():
            self._open_child(index=idx)

    def on_add(self, _evt=None):
        """Open the editor window in INSERT mode."""
        self._open_child(index=None)

    # ------------------------------------------------------------------
    # Child editor
    # ------------------------------------------------------------------
    def _open_child(self, index=None):
        """
        Create or replace the editor child window (INSERT or UPDATE mode).
        """
        try:
            if self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass

        self.child = Editor(
            self,
            index=index,
            table=self.table,
            pk_field=self.primary_key,
            desc_field=self.desc_field,
            label_text=self.label_text,
            ui_name=self.table,
        )

        self.child.on_open()

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def _on_cancel(self, _evt=None):
        """
        Close the lookup window and remove it from Engine registry.
        """
        self.engine.dict_instances.pop(self.winfo_name(), None)
        self.engine.safe_close(self)
