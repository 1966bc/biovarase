# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The rounds of the proficiency schemes, and how each of them went.

Every chart in this program is drawn against a target the laboratory set for
itself. This window is the one place where the number comes from outside, and
that is the whole reason it exists: a method can be in control for six months
on a mean that moved, and only somebody else running the same sample will
ever say so.

The rounds are on the left, newest first. Choosing one shows what was
reported for each analyte, the value the scheme assigned, and the z score
between them. Underneath are the two scores that read the round as a whole -
RSZ, which is about being out on the same side, and SZ2, which is about being
out at all - and eqa.py says at length what each is for.

Nothing here is computed from anything in the internal control: the two
halves of quality are kept apart on purpose, because the point of the second
is to be independent of the first.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import ui.eqa_result
import ui.eqa_round

from ui.window import Window

ROUNDS = (("#0", "id", tk.W, False, 0, 0),
          ("#1", "Scheme", tk.W, True, 130, 165),
          ("#2", "Round", tk.W, False, 60, 70),
          ("#3", "Run on", tk.W, False, 80, 95),
          ("#4", "n", tk.E, False, 28, 35),
          ("#5", "RSZ", tk.E, False, 45, 55),
          ("#6", "SZ2", tk.E, False, 45, 55))

RESULTS = (("#0", "id", tk.W, False, 0, 0),
           ("#1", "Analyte", tk.W, True, 150, 190),
           ("#2", "Matrix", tk.W, False, 70, 85),
           ("#3", "Unit", tk.W, False, 55, 70),
           ("#4", "Result", tk.E, False, 65, 80),
           ("#5", "Assigned", tk.E, False, 70, 85),
           ("#6", "SD", tk.E, False, 55, 70),
           ("#7", "z", tk.E, False, 45, 55),
           ("#8", "Verdict", tk.W, False, 90, 110))

#: The size it opens at: two lists side by side, and room for a round of
#: twenty analytes without scrolling.
WIDTH = 1380
HEIGHT = 600

#: Where the divider goes. A paned window asks its panes how wide they want
#: to be, and a Treeview does not answer with the sum of its columns: left to
#: itself it hands the rounds a third of what they need and cuts off the two
#: scores, which are the reason the list is there.
DIVIDER = 530


class UI(Window, tk.Toplevel):
    """The rounds on the left, the analytes of the one chosen on the right."""

    def __init__(self, parent):
        super().__init__(name="eqa")

        self.parent = parent
        self.dict_rounds = {}
        self.dict_results = {}
        self.round_id = None
        self.scores = tk.StringVar()

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.geometry("{0}x{1}".format(WIDTH, HEIGHT))
        self.minsize(900, 400)
        self.engine.tools.hide_me(self)
        self.init_ui()
        self.engine.tools.center_me(self, parent.winfo_toplevel())

        self.engine.events.subscribe("eqa_rounds", self.on_rounds_changed)
        self.engine.events.subscribe("eqa_results", self.on_results_changed)

    def init_ui(self):

        frm_main = ttk.Frame(self, style="App.TFrame", padding=6)

        # Buttons here and gestures everywhere else, on purpose. A lot is
        # opened every morning and the gesture is learnt in two days; a
        # proficiency round is entered four times a year, and the first one
        # has to be made on an empty list - there is nothing on the screen
        # to double click, and a menu that appears on the right button
        # announces itself to nobody.
        buttons = self.engine.tools.get_button_column(frm_main,
                                                      (("New round", self.on_add_round),
                                                       ("Add analyte", self.on_add_result),
                                                       ("Close", self.on_cancel)))

        self.across = ttk.PanedWindow(frm_main, orient=tk.HORIZONTAL)
        self.init_rounds(self.across)
        self.init_results(self.across)

        # The buttons are packed first, though they sit on the right: pack
        # hands the room out in the order it is asked for, and the pane that
        # expands would leave them the width of what is left.
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        self.across.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        frm_main.pack(fill=tk.BOTH, expand=1)

    def init_rounds(self, container):
        """The rounds, and what can be done to one."""
        frm = ttk.LabelFrame(container, text="Rounds")

        self.lst_rounds = self.engine.tools.get_tree(frm, ROUNDS)
        self.lst_rounds.tag_configure("questionable", foreground="#e67e22")
        self.lst_rounds.tag_configure("unsatisfactory", foreground="#c0392b")
        self.lst_rounds.bind("<<TreeviewSelect>>", self.on_selected_round)
        self.lst_rounds.bind("<Double-Button-1>", self.on_edit_round)
        self.lst_rounds.bind("<Button-3>", self.on_round_menu)

        self.menu_rounds = tk.Menu(self, tearoff=0)
        self.menu_rounds.add_command(label="New round", command=self.on_add_round)
        self.menu_rounds.add_command(label="Edit round", command=self.on_edit_round)

        container.add(frm, weight=2)

    def init_results(self, container):
        """The analytes of the round chosen, and the two scores under them."""
        frm = ttk.LabelFrame(container, text="Analytes")

        self.lst_results = self.engine.tools.get_tree(frm, RESULTS)
        self.lst_results.tag_configure("questionable", foreground="#e67e22")
        self.lst_results.tag_configure("unsatisfactory", foreground="#c0392b")
        # Double clicking an analyte edits it; double clicking nothing adds
        # one, which is the gesture the Batches window uses for the same job.
        self.lst_results.bind("<Double-Button-1>", self.on_edit_result)
        self.lst_results.bind("<Button-3>", self.on_result_menu)

        self.menu_results = tk.Menu(self, tearoff=0)
        self.menu_results.add_command(label="Add analyte",
                                      command=self.on_add_result)
        self.menu_results.add_command(label="Edit analyte",
                                      command=self.on_edit_result)

        ttk.Label(frm, style="App.TLabel", wraplength=700,
                  textvariable=self.scores).pack(side=tk.BOTTOM, anchor=tk.W,
                                                 pady=(4, 0))

        container.add(frm, weight=3)

    # ------------------------------------------------------------- the data

    def on_open(self):

        self.title("External quality assessment")
        self.set_rounds()
        # After the window has been laid out: before that the panes have no
        # size and the divider has nothing to be a fraction of.
        self.update_idletasks()
        self.across.sashpos(0, DIVIDER)

    def set_rounds(self):
        """Every round, newest first, with the two scores of each."""
        sql = """SELECT r.round_id, r.description, r.received,
                        s.description AS scheme
                   FROM eqa_rounds r
                   JOIN eqa_schemes s ON s.scheme_id = r.scheme_id
                  WHERE r.status = 1
               ORDER BY r.received DESC, r.round_id DESC"""
        rows = self.engine.db.read(True, sql, ())

        self.engine.tools.clear_treeview(self.lst_rounds)
        self.dict_rounds.clear()

        for row in rows:
            scores = self.get_scores(row["round_id"])
            rsz = self.engine.eqa.get_rsz(scores)
            sz2 = self.engine.eqa.get_sz2(scores)
            item = self.lst_rounds.insert(
                "", tk.END,
                values=(row["scheme"],
                        row["description"],
                        self.engine.format_date(row["received"]),
                        len(scores),
                        rsz,
                        sz2),
                tags=self.get_tags(max(abs(rsz), sz2)))
            self.dict_rounds[item] = row["round_id"]

    def set_results(self):
        """The analytes of the round chosen, and the scores under them."""
        rows = self.get_results()

        self.engine.tools.clear_treeview(self.lst_results)
        self.dict_results.clear()
        scores = []

        for row in rows:
            z = self.engine.eqa.get_z(row["result"], row["assigned"], row["sd"])
            scores.append(z)
            item = self.lst_results.insert(
                "", tk.END,
                values=(row["analyte"],
                        row["matrix"],
                        row["unit"],
                        row["result"],
                        row["assigned"],
                        row["sd"],
                        z,
                        self.engine.eqa.get_verdict(z)),
                tags=self.get_tags(z))
            self.dict_results[item] = row["eqa_id"]

        self.set_scores(scores)

    def set_scores(self, scores):
        """The line under the analytes: the round read as one thing."""
        if not scores:
            self.scores.set("No analytes in this round yet.")
        else:
            rsz = self.engine.eqa.get_rsz(scores)
            sz2 = self.engine.eqa.get_sz2(scores)
            self.scores.set(
                "{0} analytes.   RSZ {1}, {2}.   SZ2 {3}, {4}.".format(
                    len(scores),
                    rsz, self.engine.eqa.get_verdict(rsz).lower(),
                    sz2, self.engine.eqa.get_verdict(sz2).lower()))

    def get_results(self):
        """The analytes of the round chosen, in use, by name.

        @return: the rows
        @rtype: list of dictionaries
        """
        found = []

        if self.round_id is not None:
            sql = """SELECT e.eqa_id, e.result, e.assigned, e.sd,
                            t.description AS analyte,
                            s.description AS matrix,
                            u.description AS unit
                       FROM eqa_results e
                       JOIN test_methods tm
                            ON tm.test_method_id = e.test_method_id
                       JOIN tests t ON t.test_id = tm.test_id
                       JOIN samples s ON s.sample_id = tm.sample_id
                       JOIN units u ON u.unit_id = tm.unit_id
                      WHERE e.round_id = ? AND e.status = 1
                   ORDER BY t.description, s.description"""
            found = self.engine.db.read(True, sql, (self.round_id,))

        return found

    def get_scores(self, round_id):
        """The z scores of a round, for the two that read it as a whole.

        @param name: round_id
        @return: the scores
        @rtype: list
        """
        sql = """SELECT result, assigned, sd FROM eqa_results
                  WHERE round_id = ? AND status = 1"""
        rows = self.engine.db.read(True, sql, (round_id,))

        return [self.engine.eqa.get_z(row["result"], row["assigned"], row["sd"])
                for row in rows]

    def get_tags(self, score):
        """How a line is shown: by how far from zero its score is."""
        verdict = self.engine.eqa.get_verdict(score)

        if verdict == "Unsatisfactory":
            found = ("unsatisfactory",)
        elif verdict == "Questionable":
            found = ("questionable",)
        else:
            found = ()

        return found

    # ------------------------------------------------------------ the doing

    def on_selected_round(self, evt=None):
        """A round chosen: its analytes, and its scores."""
        self.round_id = self.dict_rounds.get(self.lst_rounds.focus())
        self.set_results()

    def on_add_round(self, evt=None):
        self.engine.windows.replace("eqa_round",
                                    lambda: ui.eqa_round.UI(self))

    def on_edit_round(self, evt=None):
        round_id = self.dict_rounds.get(self.lst_rounds.focus())

        if round_id is None:
            self.on_add_round()
        else:
            self.engine.windows.replace(
                "eqa_round", lambda: ui.eqa_round.UI(self, round_id))

    def on_add_result(self, evt=None):
        if self.round_id is None:
            messagebox.showwarning(self.engine.app_title,
                                   "Choose a round first.", parent=self)
        else:
            self.engine.windows.replace(
                "eqa_result", lambda: ui.eqa_result.UI(self, self.round_id))

    def on_edit_result(self, evt=None):
        eqa_id = self.dict_results.get(self.lst_results.focus())

        if eqa_id is None:
            self.on_add_result()
        else:
            self.engine.windows.replace(
                "eqa_result",
                lambda: ui.eqa_result.UI(self, self.round_id, eqa_id))

    def on_round_menu(self, evt):
        """The menu of a round, on the row the pointer is over."""
        self.popup(self.lst_rounds, self.menu_rounds, evt)

    def on_result_menu(self, evt):
        """The menu of an analyte, on the row the pointer is over."""
        self.popup(self.lst_results, self.menu_results, evt)

    def popup(self, tree, menu, evt):
        """Select what the pointer is over, then show its menu.

        A menu that acted on the row selected before, while the pointer is
        over another one, would act on the wrong row and say nothing.
        """
        item = tree.identify_row(evt.y)

        if item:
            tree.selection_set(item)
            tree.focus(item)
            if tree is self.lst_rounds:
                self.on_selected_round()

        menu.tk_popup(evt.x_root, evt.y_root)

    def on_rounds_changed(self, row_id=None):
        """A round was saved: read the list again and land on it."""
        self.set_rounds()

        for item, round_id in self.dict_rounds.items():
            if round_id == row_id:
                self.lst_rounds.selection_set(item)
                self.lst_rounds.focus(item)
                self.on_selected_round()

    def on_results_changed(self, row_id=None):
        """An analyte was saved: the round it belongs to is read again."""
        self.set_results()
        self.set_rounds()

    def on_cancel(self, evt=None):
        self.engine.events.unsubscribe("eqa_rounds", self.on_rounds_changed)
        self.engine.events.unsubscribe("eqa_results", self.on_results_changed)
        self.destroy()
