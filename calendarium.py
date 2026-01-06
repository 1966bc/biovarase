#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calendarium - A primitive calendar date widget for Tkinter projects.

Usage:
    from calendarium import Calendarium

    self.received = Calendarium(frm_left, "Received")
    # Use either grid *or* pack on the same parent, not both:
    # self.received.grid(row=r, column=c, sticky=tk.W)
    # self.received.pack(padx=2, pady=2)
    self.received.set_today()

Features:
    - Set current date.
    - Validate via the read-only property `is_valid` and retrieve selected date.
    - Get a timestamp using the current time of day combined with the selected date.

Author: Giuseppe Costanzi (1966bc)
License: GNU GPL v3
Version: 2.2
"""

import datetime as _dt
import tkinter as tk


class Calendarium(tk.LabelFrame):
    """Composite date widget using three Spinboxes (day, month, year)."""

    def __init__(
        self,
        parent,
        name,
        *,
        base_bg_color=None,
        year_from=_dt.MINYEAR,
        year_to=_dt.MAXYEAR,
        **kwargs
    ) -> None:
        """
        :param parent: parent widget
        :param name:   LabelFrame text
        :param base_bg_color: HEX string (e.g. "#f0f0ed") or RGB tuple (240,240,237); None → system default
        :param year_from: min year for Spinbox range (default: datetime.MINYEAR)
        :param year_to:   max year for Spinbox range (default: datetime.MAXYEAR)
        """
        super().__init__(parent, text=name, **kwargs)

        self._year_from = int(year_from)
        self._year_to = int(year_to)

        # Use StringVar so fields can be temporarily empty while editing.
        today = _dt.date.today()
        self.day = tk.StringVar(value=str(today.day))
        self.month = tk.StringVar(value=str(today.month))
        self.year = tk.StringVar(value=str(today.year))

        # Register a digit-only validator (allows empty string for editing).
        self._vcmd = (self.register(self._digits_only), "%d", "%P", "%S")

        # Background setup (standalone; accepts HEX or RGB tuple).
        self._set_label_frame_background(base_bg_color)

        # Build UI (no traces, no side-effects).
        self._spinboxes = {}
        self._build_ui()

    # UI 
    def _build_ui(self):
        lf_kwargs = {"bg": getattr(self, "_base_bg_color", None)}

        # Day
        day_frame = tk.LabelFrame(self, text="Day", **lf_kwargs)
        day_spin = tk.Spinbox(
            day_frame,
            width=2,
            from_=1,
            to=31,
            fg="blue",
            textvariable=self.day,
            validate="key",
            validatecommand=self._vcmd,
        )
        day_frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
        day_spin.pack(padx=2, pady=2)
        self._spinboxes["day"] = day_spin

        # Month
        month_frame = tk.LabelFrame(self, text="Month", **lf_kwargs)
        month_spin = tk.Spinbox(
            month_frame,
            width=2,
            from_=1,
            to=12,
            fg="blue",
            textvariable=self.month,
            validate="key",
            validatecommand=self._vcmd,
        )
        month_frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
        month_spin.pack(padx=2, pady=2)
        self._spinboxes["month"] = month_spin

        # Year
        year_frame = tk.LabelFrame(self, text="Year", **lf_kwargs)
        year_spin = tk.Spinbox(
            year_frame,
            width=5,
            fg="blue",
            from_=self._year_from,
            to=self._year_to,
            textvariable=self.year,
            validate="key",
            validatecommand=self._vcmd,
        )
        year_frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
        year_spin.pack(padx=2, pady=2)
        self._spinboxes["year"] = year_spin

    # -------------------------- Background --------------------------
    def _set_label_frame_background(self, base_bg_color=None):
        """
        Apply background color.

        Accepts:
          - HEX string (e.g., '#f0f0ed')
          - RGB tuple (e.g., (240, 240, 237))
          - None → fallback to system default
        """
        color = base_bg_color

        # Convert RGB tuple to HEX if necessary
        if isinstance(color, tuple) and len(color) == 3:
            try:
                r, g, b = color
                color = "#%02x%02x%02x" % (r, g, b)
            except Exception as e:
                color = None

        if color is None:
            color = "#d9d9d9" # final safe fallback (light gray)

        self._base_bg_color = color
        try:
            self.configure(background=color)
        except tk.TclError:
            # Some Tk themes may ignore bg configuration
            pass

    # -------------------------- Validation --------------------------
    @staticmethod
    def _digits_only(action, value, text):
        """
        Key-level validator:
        - allow only digits on insert
        - allow empty string (during deletion)
        - always allow deletions/others
        """
        if action == "1":  # insertion
            return text.isdigit() or value == ""
        return True  # deletion/others

    def _parse_int(self, var):
        """Return int(var) or None if empty/invalid."""
        s = var.get()
        if s == "":
            return None
        try:
            return int(s)
        except ValueError:
            return None

    # ---------------------------- API -------------------------------
    def set_today(self):
        """Set today's date."""
        t = _dt.date.today()
        self.set_date(t)

    def set_date(self, date_obj):
        """Set fields from a date object."""
        self.day.set(str(date_obj.day))
        self.month.set(str(date_obj.month))
        self.year.set(str(date_obj.year))

    def set_from_datetime(self, dt_obj):
        """Set fields from a datetime or date object."""
        if isinstance(dt_obj, _dt.datetime):
            dt_obj = dt_obj.date()
        self.set_date(dt_obj)

    @property
    def is_valid(self):
        """
        Compute validity on demand.
        - All three fields must be non-empty and parseable.
        - The combination must form a valid datetime.date.
        - Year must lie within the Spinbox range.
        """
        d = self._parse_int(self.day)
        m = self._parse_int(self.month)
        y = self._parse_int(self.year)
        if d is None or m is None or y is None:
            return False
        if not (self._year_from <= y <= self._year_to):
            return False
        try:
            _dt.date(y, m, d)
            return True
        except ValueError:
            return False

    def get_date(self):
        """Return date if valid, else None."""
        if not self.is_valid:
            return None
        return _dt.date(int(self.year.get()), int(self.month.get()), int(self.day.get()))

    def get_timestamp(self):
        """
        Return datetime combining the selected date with the *current* time.
        If invalid, return None.
        """
        d = self.get_date()
        if not d:
            return None
        now = _dt.datetime.now().time()
        return _dt.datetime.combine(d, now)
