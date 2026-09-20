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


class UI(ParentView):
    """
    Test Method editor (Singleton Toplevel).

    - INSERT when index is None; UPDATE when index is provided (tree iid).
    - Grid-only layout.
    - Readonly comboboxes; minimal validation for required fields.
    - Hotkeys: Alt+S/Enter (Save), Alt+C/Esc (Cancel).
    """

    _instance = None  # class-level singleton cache

    def __init__(self, parent, index=None):
        if getattr(self, "_is_init", False):
            self.parent = parent
            self.index = index
            return

        super().__init__(parent, name="test_method")
        self.index = index

        self.transient(parent)
        self.resizable(False, False)
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)

        # State vars
        self.code = tk.StringVar()
        # limit code to 10 chars via engine helper
        self.code.trace("w", lambda *args, c=10, v=self.code: self.engine.limit_chars(c, v, *args))
        self.is_mandatory = tk.BooleanVar()
        self.status = tk.BooleanVar()

        # Build UI
        self._build_ui()
        self.show()

        self._is_init = True

    # ---------------------------------------------------------------------
    # UI (grid-only)
    # ---------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        self.frm_main = ttk.Frame(self, style="App.TFrame", padding=10)
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        # Left form
        left = ttk.Frame(self.frm_main, style="App.TFrame")
        left.grid(row=0, column=0, sticky=tk.NS)
        left.columnconfigure(1, weight=1)

        r = 0; c = 1
        ttk.Label(left, text="Category:").grid(row=r, column=0, sticky=tk.W)
        self.cbCategories = ttk.Combobox(left, state="readonly")
        self.cbCategories.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(left, text="Code:").grid(row=r, column=0, sticky=tk.W)
        self.txCode = ttk.Entry(left, textvariable=self.code)
        self.txCode.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(left, text="Sample:").grid(row=r, column=0, sticky=tk.W)
        self.cbSamples = ttk.Combobox(left, state="readonly")
        self.cbSamples.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(left, text="Method:").grid(row=r, column=0, sticky=tk.W)
        self.cbMethods = ttk.Combobox(left, state="readonly")
        self.cbMethods.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(left, text="Unit:").grid(row=r, column=0, sticky=tk.W)
        self.cbUnits = ttk.Combobox(left, state="readonly")
        self.cbUnits.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(left, text="Section:").grid(row=r, column=0, sticky=tk.W)
        self.cbSections = ttk.Combobox(left, state="readonly")
        self.cbSections.grid(row=r, column=c, sticky="ew", **pad)

        r += 1
        ttk.Label(left, text="Mandatory:").grid(row=r, column=0, sticky=tk.W)
        self.chkMandatory = ttk.Checkbutton(left, variable=self.is_mandatory, onvalue=1, offvalue=0)
        self.chkMandatory.grid(row=r, column=c, sticky="w", **pad)

        r += 1
        ttk.Label(left, text="Status:").grid(row=r, column=0, sticky=tk.W)
        self.chkStatus = ttk.Checkbutton(left, variable=self.status, onvalue=1, offvalue=0)
        self.chkStatus.grid(row=r, column=c, sticky="w", **pad)

        # Right buttons
        right = ttk.Frame(self.frm_main, style="App.TFrame")
        right.grid(row=0, column=1, sticky=tk.NS, padx=6)
        ttk.Button(right, style="App.TButton", text="Save", underline=0,
                   command=self._on_save).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(right, style="App.TButton", text="Cancel", underline=0,
                   command=self.on_cancel).grid(row=1, column=0, sticky="ew", padx=4, pady=4)

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------

    def on_open(self, selected_test, selected_item=None):
        """
        Called by parent each time the dialog is requested.
        Decides mode/title, (re)loads values, brings front, sets focus.

        selected_test:
            Hybrid dict returned by engine.get_selected("tests", ...), with:
                - "test_id"
                - "description"
                - numeric keys [0], [1], ... for backward compatibility.
        """
        self.selected_test = selected_test
        self.selected_item = selected_item

        # Resolve test description once 
        test_descr = self.selected_test["description"]

        # Reload combos every open (schema/config may change)
        self._set_categories()
        self._set_samples()
        self._set_units()
        self._set_methods()
        self._set_sections()
        

        if self.index is not None and self.selected_item is not None:
            # UPDATE mode
            title = f"Update method for {test_descr}"
            self._load_selected()
        else:
            # INSERT mode
            title = f"Add method for {test_descr}"
            self._clear_fields()
            # Prefill code with first 5 chars of test description
            self.code.set((test_descr or "")[:5].upper())
            self.is_mandatory.set(0)
            self.status.set(1)

        self.title(title)
        try:
            self.transient(self.parent)
            self.deiconify()
            self.lift()
        except Exception as e:
            pass
        self.after_idle(lambda: self.cbCategories.focus_set())
        
    # ---------------------------------------------------------------------
    # Data helpers
    # ---------------------------------------------------------------------
    def _clear_fields(self):
        """
        Reset all form fields to their default/empty state.
        """
        self.code.set("")
        for cb in (self.cbCategories, self.cbSamples, self.cbMethods, self.cbUnits, self.cbSections):
            try:
                cb.set("")
                cb.current(-1)
            except Exception as e:
                pass
        self.is_mandatory.set(0)
        self.status.set(1)

    def _set_categories(self):
        """Load categories filtered by current lab (org_id)."""
        self.dict_categories = {}
        values = []
        sql = """
            SELECT category_id, description
            FROM categories
            WHERE org_id = ?
            AND status = 1
            ORDER BY description
        """
        lab_id = self.engine.get_lab_id()
        rows = self.engine.read(True, sql, (lab_id,)) or []
        for idx, row in enumerate(rows):
            self.dict_categories[idx] = row["category_id"]
            values.append(row["description"])
        self.cbCategories["values"] = values

    def _set_samples(self):
        self.dict_samples = {}
        values = []
        sql = (
            "SELECT sample_id, description "
            "FROM samples "
            "WHERE status = 1 "
            "ORDER BY description;"
        )
        rows = self.engine.read(True, sql, ()) or []
        for idx, row in enumerate(rows):
            self.dict_samples[idx] = row["sample_id"]
            values.append(row["description"])
        self.cbSamples["values"] = values

    def _set_units(self):
        self.dict_units = {}
        values = []
        sql = (
            "SELECT unit_id, description "
            "FROM units "
            "WHERE status = 1 "
            "ORDER BY description;"
        )
        rows = self.engine.read(True, sql, ()) or []
        for idx, row in enumerate(rows):
            self.dict_units[idx] = row["unit_id"]
            values.append(row["description"])
        self.cbUnits["values"] = values

    def _set_methods(self):
        self.dict_methods = {}
        values = []
        sql = (
            "SELECT method_id, description "
            "FROM methods "
            "WHERE status = 1 "
            "ORDER BY description;"
        )
        rows = self.engine.read(True, sql, ()) or []
        for idx, row in enumerate(rows):
            self.dict_methods[idx] = row["method_id"]
            values.append(row["description"])
        self.cbMethods["values"] = values

    def _set_sections(self):
        """
        Load only sections belonging to the lab of the current context.

        Uses organizations table to get sections (org_type='section')
        that are children of the current lab (org_id).

        Populates:
            self.dict_sections: index -> org_id (section)
            self.cbSections["values"]: list of section descriptions
        """
        self.dict_sections = {}
        values = []

        lab_id = self.engine.current_ids.get("lab_id")
        if lab_id is None:
            # No lab context → no sections to display
            self.cbSections["values"] = []
            return

        sql = """
            SELECT
                org_id AS section_id,
                description
            FROM organizations
            WHERE status = 1
              AND parent_id = ?
              AND org_type = 'section'
            ORDER BY description;
        """
        rs = self.engine.read(True, sql, (lab_id,)) or []

        for idx, row in enumerate(rs):
            self.dict_sections[idx] = row["section_id"]
            values.append(row["description"])

        self.cbSections["values"] = values

    def _load_selected(self):
        """
        Load the selected test_method into the form.

        self.selected_item is the hybrid dict returned by:
            engine.get_selected("test_methods", "test_method_id", pk)

        Expected keys:
            - "test_method_id"
            - "test_id"
            - "category_id"
            - "code"
            - "sample_id"
            - "method_id"
            - "unit_id"
            - "section_id"
            - "is_mandatory"
            - "status"
        """
        item = self.selected_item or {}

        # Category
        cid = item.get("category_id")
        if cid is not None:
            try:
                k = next(k for k, v in self.dict_categories.items() if v == cid)
                self.cbCategories.current(k)
            except StopIteration:
                self.cbCategories.set("")
        else:
            self.cbCategories.set("")

        # Code
        self.code.set(item.get("code") or "")

        # Sample
        sid = item.get("sample_id")
        if sid is not None:
            try:
                k = next(k for k, v in self.dict_samples.items() if v == sid)
                self.cbSamples.current(k)
            except StopIteration:
                self.cbSamples.set("")
        else:
            self.cbSamples.set("")

        # Method
        mid = item.get("method_id")
        if mid is not None:
            try:
                k = next(k for k, v in self.dict_methods.items() if v == mid)
                self.cbMethods.current(k)
            except StopIteration:
                self.cbMethods.set("")
        else:
            self.cbMethods.set("")

        # Unit
        uid = item.get("unit_id")
        if uid is not None:
            try:
                k = next(k for k, v in self.dict_units.items() if v == uid)
                self.cbUnits.current(k)
            except StopIteration:
                self.cbUnits.set("")
        else:
            self.cbUnits.set("")

        # Section (now uses org_id)
        org_id = item.get("org_id") or item.get("section_id")
        try:
            k = next(k for k, v in self.dict_sections.items() if v == org_id)
            self.cbSections.current(k)
        except StopIteration:
            self.cbSections.set("")

        # Flags
        self.is_mandatory.set(int(item.get("is_mandatory", 0)))
        self.status.set(int(item.get("status", 1)))

    def _collect_values(self):
        """
        Collect and validate form values, returning a list suitable for SQL args.

        Uses named keys from:
            - self.selected_test -> "test_id"
        The section is always taken from cbSections.
        """

        # Required: all combos selected
        for label, cb in (("Category", self.cbCategories),
                          ("Sample", self.cbSamples),
                          ("Method", self.cbMethods),
                          ("Unit", self.cbUnits),
                          ("Section", self.cbSections),):
            if cb.current() < 0:
                messagebox.showwarning(self.engine.app_title, f"Select a {label}.", parent=self)
                raise RuntimeError("validation")

        # Required: code (non-empty)
        code = (self.code.get() or "").strip()
        if not code:
            messagebox.showwarning(self.engine.app_title, "Code is required.", parent=self)
            self.txCode.focus_set()
            raise RuntimeError("validation")

        # Test id from selected_test (hybrid dict from engine.get_selected)
        test_id = self.selected_test["test_id"]

        # Section org_id for multi-tenant (org_id references the section in organizations table)
        section_org_id = self.dict_sections[self.cbSections.current()]

        return [
            test_id,                                            # test_id
            self.dict_categories[self.cbCategories.current()],  # category_id
            code,                                               # code
            self.dict_samples[self.cbSamples.current()],        # sample_id
            self.dict_methods[self.cbMethods.current()],        # method_id
            self.dict_units[self.cbUnits.current()],            # unit_id
            section_org_id,                                     # org_id (section's org_id)
            int(self.is_mandatory.get()),                       # is_mandatory
            int(self.status.get()),                             # status
        ]

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------
    def _on_save(self, _evt=None):
        # Optional global validation hook
        if hasattr(self.engine, "on_fields_control"):
            if self.engine.on_fields_control(self.frm_main, self.engine.app_title) is False:
                return

        if not messagebox.askyesno(self.engine.app_title,
                                   getattr(self.engine, "ask_to_save", "Do you want to save?"),
                                   parent=self):
            return

        try:
            args = self._collect_values()
        except RuntimeError:
            return

        if self.index is not None and getattr(self, "selected_item", None):
            # UPDATE
            sql = self.engine.build_sql("test_methods", op="update")
            pk = self.selected_item.get("test_method_id")
            args.append(pk)  # pk at the end
        else:
            # INSERT
            sql = self.engine.build_sql("test_methods", op="insert")

        last_id = self.engine.write(sql, args)
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.get_user_friendly_db_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(self.engine.app_title, msg, parent=self)
            return

        # refresh parent view and reselect
        self.parent._load_methods_for_selected_test()
        self._reselect_in_parent(last_id)

        # Notify observers for cross-window refresh
        self.engine.notify("test_method_changed")

        self.on_cancel()

    def _reselect_in_parent(self, last_id=None):
        """
        Reselect the row in the parent's Treeview after save.

        - UPDATE: reselect by current test_method_id
        - INSERT: reselect by last_id
        """
        if self.index is not None and getattr(self, "selected_item", None):
            target_pk = self.selected_item.get("test_method_id")
        else:
            target_pk = last_id

        if target_pk is None:
            return

        tv = self.parent.lstMethods
        iid = str(target_pk)
        try:
            tv.selection_set(iid)
            tv.see(iid)
            self.parent.on_test_method_selected()  # refresh parent state
        except Exception as e:
            pass
        
    def on_cancel(self, _evt=None):
        self.engine.safe_close(self)
