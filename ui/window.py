# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""How a window reaches the engine, written once instead of twenty-nine times.

Every window in this application needs the engine, and every one of them had
the same four lines to get it:

    def get_engine(self):
        return self.nametowidget(".").engine

Twenty-nine copies of one expression, and then `self.get_engine()` at a
hundred and seventy-three call sites, or `engine = self.get_engine()` at the
head of a method at eighty-six more. None of it was wrong and all of it was
noise: what a window wants to say is `self.engine.read_all(sql)`.

The lookup itself does not change and is the one described in CLAUDE.md: the
engine lives on the root window, so any widget can find it by name from
anywhere in the tree, and nothing has to be handed down a constructor.

Not a widget class, which is deliberate. A Toplevel and a Frame both need
this and they are not each other; inheriting from a class that is itself a
widget would decide their kind for them, and a mixin that adds one property
decides nothing. It is also why the rule in CONVENTIONS.md about __str__ does
not apply here - this class is never handed to Tk, its subclasses are, and
they are Toplevels and Frames exactly as they were.
"""


class Window:
    """The engine, reached from any widget in the tree."""

    @property
    def engine(self):
        return self.nametowidget(".").engine
