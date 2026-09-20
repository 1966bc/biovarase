# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""An analyte as this laboratory measures it, and what it is held to.

The analyte says what substance; this says how it is measured here - the
matrix, the method, the unit, the panel it is reported in - and what the
result has to be worth: the analytical goals.

The goals come two ways and the window offers both, because they are two
different things. An endogenous analyte is held to its own biological
variation, and the imprecision, the bias and the total error follow from it
by formula. A drug has no biological variation - the concentration is what
the dose made it - and is held to the state of the art, which is a total
error to stay inside. Type the variation and the rest is computed; leave it
at zero and type the total error instead.

documents/ANALYTICAL_GOALS.md has the formulae and where the numbers come
from.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from ui.dialog import Dialog
from ui.lookup import Lookup


class UI(Dialog):
    NAME = "test_method"
    TABLE = "test_methods"

    def init_fields(self):

        self.code = tk.StringVar()
        self.cvw = tk.DoubleVar()
        self.cvb = tk.DoubleVar()
        self.imp = tk.DoubleVar()
        self.bias = tk.DoubleVar()
        self.teap005 = tk.DoubleVar()
        self.teap001 = tk.DoubleVar()
        self.is_mandatory = tk.BooleanVar()

        cb_test = self.engine.tools.get_combo(self.frm_fields)
        self.test = Lookup(self.engine, cb_test, "tests")

        cb_sample = self.engine.tools.get_combo(self.frm_fields)
        self.sample = Lookup(self.engine, cb_sample, "samples")

        cb_method = self.engine.tools.get_combo(self.frm_fields)
        self.method = Lookup(self.engine, cb_method, "methods")

        cb_unit = self.engine.tools.get_combo(self.frm_fields)
        self.unit = Lookup(self.engine, cb_unit, "units")

        cb_category = self.engine.tools.get_combo(self.frm_fields)
        self.category = Lookup(self.engine, cb_category, "categories")

        self.add_field("Analyte:", cb_test)
        self.add_field("Matrix:", cb_sample)
        self.add_field("Method:", cb_method)
        self.add_field("Unit:", cb_unit)
        self.add_field("Panel:", cb_category)
        self.add_field("Code:", self.get_entry(self.code, 12), tk.W)

        chk = ttk.Checkbutton(self.frm_fields, style="App.TCheckbutton",
                              onvalue=1, offvalue=0, variable=self.is_mandatory)
        self.add_field("Every day:", chk, tk.W)

        self.add_field("CVi%:", self.get_entry(self.cvw, kind="float"), tk.W)
        self.add_field("CVg%:", self.get_entry(self.cvb, kind="float"), tk.W)
        self.add_field("Imprecision%:", self.get_entry(self.imp, kind="float"), tk.W)
        self.add_field("Bias%:", self.get_entry(self.bias, kind="float"), tk.W)
        self.add_field("TEa% (95):", self.get_entry(self.teap005, kind="float"), tk.W)
        self.add_field("TEa% (99):", self.get_entry(self.teap001, kind="float"), tk.W)

    def get_entry(self, variable, width=None, kind="text"):
        """A field of the width its column allows, and no wider.

        The code is given a width of its own; a per cent is left the one its
        kind carries.
        """
        entry = self.engine.tools.get_entry(self.frm_fields, variable, kind)
        if width is not None:
            entry.configure(width=width)

        return entry

    def get_buttons(self):
        """Save and Cancel, and Compute for the goals that follow a formula."""
        return (("Save", self.on_save),
                ("Compute", self.on_compute),
                ("Cancel", self.on_cancel))

    def on_compute(self, evt=None):
        """Work the goals out of the biological variation, by the formulae.

        CVa = 0.5 x CVi, bias = 0.25 x sqrt(CVi^2 + CVg^2), TEa = z x CVa +
        bias, with the coverage factor from the settings. Refused when the
        variation is zero, because that is the case the formulae do not
        cover: a drug is held to the state of the art, and its total error is
        typed rather than derived.
        """
        cvw = self.cvw.get()
        cvb = self.cvb.get()

        if not cvw:
            messagebox.showinfo(
                self.engine.app_title,
                "No biological variation: nothing to compute from.\n\n"
                "An analyte with a variation of its own has its goals"
                " computed; a drug is held to the state of the art, and its"
                " allowable total error is typed in.",
                parent=self)
        else:
            imp = self.engine.qc.get_imp(cvw)
            bias = self.engine.qc.get_allowable_bias(cvw, cvb)
            self.imp.set(imp)
            self.bias.set(bias)
            self.teap005.set(round(1.65 * imp + bias, 2))
            self.teap001.set(round(2.58 * imp + bias, 2))

    def set_values(self, row):

        self.code.set(row["code"])
        self.cvw.set(row["cvw"])
        self.cvb.set(row["cvb"])
        self.imp.set(row["imp"])
        self.bias.set(row["bias"])
        self.teap005.set(row["teap005"])
        self.teap001.set(row["teap001"])
        self.is_mandatory.set(row["is_mandatory"])
        self.test.set_id(row["test_id"])
        self.sample.set_id(row["sample_id"])
        self.method.set_id(row["method_id"])
        self.unit.set_id(row["unit_id"])
        self.category.set_id(row["category_id"])

    def get_values(self):

        return {"test_id": self.test.get_id(),
                "category_id": self.category.get_id(),
                "sample_id": self.sample.get_id(),
                "method_id": self.method.get_id(),
                "unit_id": self.unit.get_id(),
                "code": self.engine.tools.get_clean_text(self.code.get()),
                "is_mandatory": int(self.is_mandatory.get()),
                "cvw": self.cvw.get(),
                "cvb": self.cvb.get(),
                "imp": self.imp.get(),
                "bias": self.bias.get(),
                "teap005": self.teap005.get(),
                "teap001": self.teap001.get()}
