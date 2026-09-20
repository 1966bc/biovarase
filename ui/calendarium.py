# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""A date widget: three spinboxes and no dependencies.

Taken from Calendarium (github.com/1966bc/Calendarium), same author, adapted to
this project's conventions in four ways.

It is built from ttk rather than tk, so it follows the application theme
instead of looking like a piece of another program.

get_date returns a date or None, never False. A caller writing 'if not value'
could not otherwise tell an invalid date from one that is merely falsy, which
is the same trap that was removed from the field check in tools.

It opens no dialog of its own. The widget reports whether the date is valid;
what to say about it is the caller's business, because a widget that pops
message boxes has tied validation to presentation and can no longer be used
where a message would be unwelcome.

The three fields refuse anything but digits as they are typed. It is done
here rather than through Tools, so that the widget stays a widget and can be
dropped into another program unchanged - the reason it is worth borrowing at
all.
"""

import calendar
import datetime
import tkinter as tk
from tkinter import ttk

from ui.window import Window


class Calendarium(Window, ttk.Frame):
    """Day, month and year, with no way to leave the field empty."""

    def __init__(self, parent, caption=""):
        super().__init__(parent)

        self.caption = caption
        self.day = tk.IntVar()
        self.month = tk.IntVar()
        self.year = tk.IntVar()

        self.init_ui()
        self.set_today()

    # No __str__ here, and none on any widget class. Tk passes a widget to the
    # interpreter as its string, so a class that overrides __str__ becomes
    # unusable as an argument: transient(window), wait_window(dialog) and the
    # 'in' option all fail with 'bad window path name'. It cost an afternoon
    # once. Diagnostics go in a get_ method, which nothing converts silently.

    def get_state(self):
        """What this field holds, for a log line or a debugging session."""
        return "{0}: {1}".format(self.caption or self.__class__.__name__,
                                 self.get_iso() or "invalid")

    def init_ui(self):
        frame = ttk.LabelFrame(self, style="App.TLabelframe",
                               text=self.caption)

        spins = ((self.day, 1, 31, 3), (self.month, 1, 12, 3),
                 (self.year, 1900, 2999, 5))
        # Digits and nothing else, checked at the keystroke. A spinbox can
        # be typed into and these three are bound to IntVars, so a letter in
        # one makes get() raise TclError - which get_date answers for, but
        # answering afterwards is not the same as never letting it in. No
        # sign here, unlike the number fields elsewhere: no part of a date is
        # negative.
        check = (self.register(self.validate_digits), "%d", "%P")

        #: Kept, so that the field can be closed as a whole. A form that
        #: shows a record nobody may change has to be able to say so with
        #: every one of its widgets, and a date that stays typeable beside
        #: fourteen greyed figures says the opposite of what is meant.
        self.spins = []
        for variable, low, high, width in spins:
            spin = ttk.Spinbox(frame, width=width, from_=low, to=high,
                               justify=tk.CENTER, textvariable=variable,
                               wrap=True, validate="key",
                               validatecommand=check)
            spin.pack(side=tk.LEFT, padx=2)
            self.spins.append(spin)

        frame.pack(fill=tk.X)

    def set_focus(self):
        """The keyboard to the first box, the day."""
        self.spins[0].focus_set()

    @staticmethod
    def validate_digits(action, value_if_allowed):
        """Allow the keystroke only when the field stays digits.

        isdecimal and not isdigit: the superscript two answers yes to isdigit
        and then raises in int(), which is exactly the value this is here to
        keep out.
        """
        return action != "1" or value_if_allowed.isdecimal()

    def set_state(self, state):
        """tk.NORMAL or tk.DISABLED, for all three at once."""
        for spin in self.spins:
            spin.configure(state=state)

    # --- setting ------------------------------------------------------------

    def set_today(self):
        self.set_date(datetime.date.today())

    def set_date(self, value):
        self.day.set(value.day)
        self.month.set(value.month)
        self.year.set(value.year)

    def set_days_ago(self, days):
        self.set_date(datetime.date.today() - datetime.timedelta(days=days))

    def set_days_ahead(self, days):
        """For a date in the future, so no caller has to say 'minus 365 ago'."""
        self.set_date(datetime.date.today() + datetime.timedelta(days=days))

    # --- reading ------------------------------------------------------------

    def get_date(self):
        """The date, or None when the three parts do not make one.

        A spinbox can be typed into, so 31 February is reachable and has to be
        answered for rather than crashed on.
        """
        value = None
        try:
            value = datetime.date(self.year.get(), self.month.get(),
                                  self.day.get())
        except (ValueError, tk.TclError):
            value = None
        return value

    def is_valid(self):
        return self.get_date() is not None

    def get_iso(self):
        """ISO 8601 text, which is how dates are stored, or None."""
        value = self.get_date()
        iso = None
        if value is not None:
            iso = value.isoformat()
        return iso

    def get_day_start(self):
        """First instant of the day, for a range that includes it."""
        value = self.get_date()
        start = None
        if value:
            start = "{0} 00:00:00".format(value.isoformat())
        return start

    def get_day_end(self):
        """Last instant of the day, so a range's upper bound is inclusive."""
        value = self.get_date()
        end = None
        if value:
            end = "{0} 23:59:59".format(value.isoformat())
        return end

    def get_last_day_of_month(self):
        """Useful when a caller wants to snap a range to whole months."""
        value = self.get_date()
        last = None
        if value is not None:
            last = calendar.monthrange(value.year, value.month)[1]
        return last


def main():
    root = tk.Tk()
    root.title("Calendarium")

    frame = ttk.Frame(root, padding=8)
    first = Calendarium(frame, "From")
    second = Calendarium(frame, "To")
    first.set_days_ago(30)
    first.pack(side=tk.LEFT, padx=4)
    second.pack(side=tk.LEFT, padx=4)

    def show():
        print("from {0} to {1}".format(first.get_day_start(),
                                       second.get_day_end()))

    ttk.Button(frame, text="Read", command=show).pack(side=tk.LEFT, padx=8)
    frame.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
