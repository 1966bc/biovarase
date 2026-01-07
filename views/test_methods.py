# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   giuseppecostanzi@gmail.com
# modify:   ver MMXXV
#-----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from i18n import _
import views.test_method as test_method_editor
import views.goal as goal_editor
from views.parent_view import ParentView


SQL_LAB_DESCRIPTION = "SELECT description FROM labs WHERE lab_id = ? LIMIT 1;"

SQL_TEST_METHODS = """
                    SELECT
                      test_methods.test_method_id,
                      test_methods.code,
                      samples.description  AS sample_description,
                      methods.description  AS method_description,
                      units.description    AS unit_description,
                      sections.description    AS section_description,
                      test_methods.status  AS status
                    FROM tests
                    INNER JOIN test_methods ON tests.test_id = test_methods.test_id
                    INNER JOIN samples ON test_methods.sample_id = samples.sample_id
                    INNER JOIN methods ON test_methods.method_id = methods.method_id
                    INNER JOIN units   ON test_methods.unit_id   = units.unit_id
                    INNER JOIN sections ON test_methods.section_id = sections.section_id
                    INNER JOIN labs ON sections.lab_id = labs.lab_id
                    WHERE tests.test_id = ?
                      AND labs.lab_id = ?
                      AND tests.status = 1
                    ORDER BY tests.description ASC;
                    """

SQL_TESTS = "SELECT test_id, description, status FROM tests WHERE status = 1 ORDER BY description ASC;"


class UI(ParentView):

    def __init__(self, parent):
        super().__init__(parent, name="test_methods")
        if self._reusing:
            self.on_open()
            return

        self.resizable(True, True)

        # Hotkeys
        self.bind("<Alt-c>", self.on_cancel)
        self.bind("<Alt-b>", self.on_analytical_goal)
        self.bind("<Return>", self._open_current_selection)

        # State
        self.items = tk.StringVar()
        self.selected_test = None
        self.child = None

        self._build_ui()
        self.show(on_screen=True)
        


    # ---------------------------------------------------------------------
    # UI (pack-based)
    # ---------------------------------------------------------------------
    def _build_ui(self):

        # Window title with current lab context
        self._update_lab_title()

        # PanedWindow root (H)
        self.pw = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6)
        self.pw.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)

        # --- Left pane: Tests 
        pane_left = ttk.Frame(self.pw, style="App.TFrame")
        self.pw.add(pane_left, minsize=220, stretch="always")

        lbl_cnt = ttk.Label(pane_left, style="App.TLabel", textvariable=self.items)
        lbl_cnt.pack(fill=tk.X, padx=2, pady=2)

        frm_tests = ttk.Frame(pane_left, style="Panel.TFrame")
        frm_tests.pack(fill=tk.BOTH, expand=1)

        sb = ttk.Scrollbar(frm_tests, orient=tk.VERTICAL)
        self.lstTests = tk.Listbox(frm_tests, yscrollcommand=sb.set, exportselection=False)
        self.lstTests.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb.config(command=self.lstTests.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstTests.bind("<<ListboxSelect>>", self.on_test_selected)
        self.lstTests.bind("<Double-Button-1>", self.on_test_activated)

        # --- Middle pane: Methods 
        pane_mid = ttk.Frame(self.pw, style="App.TFrame")
        self.pw.add(pane_mid, minsize=360, stretch="always")

        frm_methods = ttk.Frame(pane_mid, style="Panel.TFrame")
        frm_methods.pack(fill=tk.BOTH, expand=1)

        lf_methods = ttk.Labelframe(frm_methods, text=_("Methods"))
        lf_methods.pack(fill=tk.BOTH, expand=1)

        cols_methods = ("code", "sample", "method", "unit", "section")
        self.lstMethods = ttk.Treeview(lf_methods, columns=cols_methods, show="headings")

        self.lstMethods.column("code", width=80, minwidth=80, anchor=tk.W, stretch=True)
        self.lstMethods.heading("code", text=_("Code:").rstrip(":"), anchor=tk.W)

        self.lstMethods.column("sample", width=140, minwidth=140, anchor=tk.W, stretch=True)
        self.lstMethods.heading("sample", text=_("Sample:").rstrip(":"), anchor=tk.W)

        self.lstMethods.column("method", width=180, minwidth=180, anchor=tk.W, stretch=True)
        self.lstMethods.heading("method", text=_("Method:").rstrip(":"), anchor=tk.W)

        self.lstMethods.column("unit", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstMethods.heading("unit", text=_("Unit:").rstrip(":"), anchor=tk.W)

        self.lstMethods.column("section", width=100, minwidth=100, anchor=tk.W, stretch=True)
        self.lstMethods.heading("section", text=_("Section:").rstrip(":"), anchor=tk.W)

        sb_methods = ttk.Scrollbar(lf_methods, orient=tk.VERTICAL, command=self.lstMethods.yview)
        self.lstMethods.configure(yscrollcommand=sb_methods.set)
        self.lstMethods.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        sb_methods.pack(side=tk.RIGHT, fill=tk.Y)

        self.lstMethods.tag_configure("inactive", background="light gray")
        self.lstMethods.bind("<<TreeviewSelect>>", self.on_test_method_selected)
        self.lstMethods.bind("<Double-1>", self.on_test_method_activated)

        # --- Right pane: Actions
        pane_right = ttk.Frame(self.pw, style="App.TFrame")
        self.pw.add(pane_right, minsize=140, stretch="never")

        frm_buttons = ttk.Frame(pane_right, style="Panel.TFrame")
        frm_buttons.pack(side=tk.LEFT, fill=tk.Y, expand=0)

        self.engine.add_button(frm_buttons, _("Goals"), self.on_analytical_goal, "<Alt-g>", self)
        self.engine.add_button(frm_buttons, _("Cancel"), self.on_cancel, "<Alt-c>", self)

        # Place sashes after first layout
        self.after_idle(self._place_sashes)

    def _place_sashes(self, fixed_right=160, left_ratio=0.30):
        """
        Place sashes so that:
          - left pane ≈ left_ratio of total width
          - right pane ≈ fixed_right pixels
          - middle pane takes the remaining space.
        """
        try:
            w = self.pw.winfo_width()
            if w <= fixed_right + 100:
                return

            left = int(w * left_ratio)
            right = w - fixed_right

            self.pw.sash_place(0, left, 1)
            self.pw.sash_place(1, right, 1)
        except Exception as e:
            pass
        
    def on_open(self):

        self._update_lab_title()
        self._load_tests()
        self._clear_methods()

    def _update_lab_title(self):
        """Set window title with current lab description."""
        lab_id = self.engine.current_ids.get("lab_id")
        lab_row = self.engine.read(False, SQL_LAB_DESCRIPTION, (lab_id,))
        lab_name = lab_row["description"] if lab_row else "?"
        self.title(f"{_('Test Methods')} – {_('Lab')}: {lab_name}")

    def _load_tests(self):
        """Load active tests into the listbox."""
        self.lstTests.delete(0, tk.END)
        self.dict_tests = {}

        rs = self.engine.read(True, SQL_TESTS, ()) or []

        for idx, row in enumerate(rs):            
            self.lstTests.insert(tk.END, row["description"])
            self.dict_tests[idx] = row["test_id"]

        self.items.set(f"{_('Tests')}: {self.lstTests.size()}")
        self.selected_test = None

    def _clear_methods(self):
        """Clear the methods tree."""
        self.engine.clear_treeview(self.lstMethods)

    def _load_methods_for_selected_test(self):
        """Populate methods tree for the currently selected test."""
        self._clear_methods()
        if not self.selected_test:
            return

        test_id = self.selected_test["test_id"]
        lab_id = self.engine.current_ids["lab_id"]

        args = (test_id, lab_id)
        rows = self.engine.read(True, SQL_TEST_METHODS, args) or []

        for row in rows:
            tags = ("inactive",) if int(row["status"]) != 1 else ()
            self.lstMethods.insert(
                "",
                tk.END,
                iid=row["test_method_id"],
                text=row["test_method_id"],
                values=(
                    row["code"],
                    row["sample_description"],
                    row["method_description"],
                    row["unit_description"],
                    row["section_description"],      
                ),
                tags=tags,)
   
    def on_test_selected(self, _evt=None):
        """When a test is selected, load its methods."""
        sel = self.lstTests.curselection()
        if not sel:
            self.selected_test = None
            self._clear_methods()
            return

        idx = sel[0]
        pk = self.dict_tests.get(idx)
        self.selected_test = self.engine.get_selected("tests", "test_id", pk)
        self._load_methods_for_selected_test()

    def on_test_activated(self, _evt=None):
        """Double-click on a test: open test editor (anagraphic)."""
        sel = self.lstTests.curselection()
        if not sel or not self.selected_test:
            return
        self.child = test_method_editor.UI(self)
        self.child.on_open(self.selected_test)

    def on_test_method_selected(self, _evt=None):
         """Track the selected test_method record (currently unused)."""
         pass

    def on_test_method_activated(self, _evt=None):
        """Double-click on a method: open test_method editor."""
        sel = self.lstMethods.selection()
        if not sel or not self.selected_test:
            return
        pk = int(sel[0])
        selected_item = self.engine.get_selected("test_methods", "test_method_id", pk)
        self.child = test_method_editor.UI(self, sel[0])
        self.child.on_open(self.selected_test, selected_item)

    def _open_current_selection(self, _evt=None):
        """
        Enter key: open selected method if any; otherwise open test editor.
        """
        if self.lstMethods.selection():
            self.on_test_method_activated()
        elif self.lstTests.curselection():
            self.on_test_activated()

    def on_analytical_goal(self, _evt=None):
        """Open analytical goals dialog for the selected test_method."""

        # Destroy existing child if open
        try:
            if self.child is not None and self.child.winfo_exists():
                self.child.destroy()
        except Exception as e:
            pass
        
        sel = self.lstMethods.selection()
        if not sel:
            messagebox.showwarning(self.engine.app_title, _("Select a Test Method."), parent=self)
            return
        pk = int(sel[0])
        selected_tm = self.engine.get_selected("test_methods", "test_method_id", pk)
        self.child = goal_editor.UI(self, index=pk)
        self.child.on_open()

    def refresh_context_from_section(self):
        """
        Called when the current section/lab changes elsewhere.
        - Rilegge lab_id/lab_name dal contesto.
        - Aggiorna il titolo della finestra.
        - Ricarica la lista dei metodi per il test selezionato.
        """
        try:
            self._update_lab_title()
            self._clear_methods()
            if self.selected_test:
                self._load_methods_for_selected_test()

        except Exception as e:
            self.engine.on_log("test_methods.refresh_context_from_section",
                               e, type(e), __name__)

    def on_cancel(self, _evt=None):
        super().on_cancel()
