# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Dates between Python and SQLite, converted here rather than by default.

SQLite has no type for a date. A date is text in a column that says DATE, and
sqlite3 turned that text into a datetime.date on the way out and back into
text on the way in. Both default conversions are deprecated as of Python 3.12
and will be removed.

This program reads twenty-two such columns and hands what comes out to every
chart, every comparison of a period and every line of a signed record. The
day the defaults go, a date comes back a string - and that does not fail
where it is read, because a string compares with a string and answers
something. It fails in a question about a period, quietly, on a machine in a
laboratory.

So the conversions are written down, and they are the same ones. The database
holds ISO throughout - 2027-07-12 for a day, 2026-03-24 07:05:00 for a moment
- which is what isoformat() writes and fromisoformat() reads back.

They are static because what they are registered with is not an object but a
module: sqlite3 keeps one table of adapters and one of converters for the
whole process, and a conversion that belonged to an instance would leave
those tables pointing at whichever instance was built last.
"""

import datetime
import sqlite3 as lite


class Dates:
    """The four conversions, and the registration of them."""

    def __init__(self):
        self.set_types()

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    def set_types(self):
        """Register the conversions with sqlite3.

        For the module and not for one connection: doing it again does no
        harm, and every connection opened afterwards has them.
        """
        lite.register_adapter(datetime.date, self.adapt_date)
        lite.register_adapter(datetime.datetime, self.adapt_datetime)
        lite.register_converter("DATE", self.convert_date)
        lite.register_converter("TIMESTAMP", self.convert_timestamp)

    @staticmethod
    def adapt_date(value):
        """A day on its way into the database: 2027-07-12."""
        return value.isoformat()

    @staticmethod
    def adapt_datetime(value):
        """A moment on its way in: 2026-03-24 07:05:00.

        A space between the day and the hour, which is what SQLite's own
        CURRENT_TIMESTAMP writes in the columns that have a default, and so
        what the rest of the table already looks like.
        """
        return value.isoformat(" ")

    @staticmethod
    def convert_date(value):
        """A DATE column on its way out, as a datetime.date."""
        return datetime.date.fromisoformat(value.decode())

    @staticmethod
    def convert_timestamp(value):
        """A TIMESTAMP column on its way out, as a datetime.datetime."""
        return datetime.datetime.fromisoformat(value.decode())
