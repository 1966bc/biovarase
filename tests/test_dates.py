# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for dates.py: the conversions on their own, with no database at all.

They are written down because sqlite3 is taking its own away, and the
defaults still work on the Python of today - so a test that only reads a date
back out of a table would pass just as well with all of this deleted. What is
watched here is the conversion itself, and that sqlite3 is holding ours.

Run them from the project directory:

    python3 -m unittest discover -s tests -v
"""

import datetime
import sqlite3
import unittest

from dates import Dates


class TestAdapting(unittest.TestCase):
    """Python to the database: what is written in the column."""

    def test_a_day_is_written_iso(self):
        """2027-07-12, which is what SQLite can compare and what DATE holds."""
        self.assertEqual(Dates.adapt_date(datetime.date(2027, 7, 12)),
                         "2027-07-12")

    def test_a_moment_keeps_its_hour(self):
        """With a space between, as CURRENT_TIMESTAMP writes it."""
        self.assertEqual(Dates.adapt_datetime(datetime.datetime(2026, 3, 24, 7, 5)),
                         "2026-03-24 07:05:00")

    def test_a_moment_keeps_what_it_was_given(self):
        """Microseconds and all: the same text the default adapter wrote."""
        moment = datetime.datetime(2026, 3, 24, 7, 5, 0, 123456)
        self.assertEqual(Dates.adapt_datetime(moment),
                         "2026-03-24 07:05:00.123456")


class TestConverting(unittest.TestCase):
    """The database to Python: sqlite3 hands over bytes."""

    def test_a_day_comes_back_a_date(self):
        self.assertEqual(Dates.convert_date(b"2027-07-12"),
                         datetime.date(2027, 7, 12))

    def test_a_moment_comes_back_a_datetime(self):
        self.assertEqual(Dates.convert_timestamp(b"2026-03-24 07:05:00"),
                         datetime.datetime(2026, 3, 24, 7, 5))

    def test_a_moment_with_microseconds(self):
        """Written by the adapter above, and read back by this."""
        self.assertEqual(Dates.convert_timestamp(b"2026-03-24 07:05:00.123456"),
                         datetime.datetime(2026, 3, 24, 7, 5, 0, 123456))

    def test_a_round_trip_is_the_same_moment(self):
        """Out and back: what goes through the two is what it was."""
        moment = datetime.datetime(2026, 3, 24, 7, 5, 0)
        text = Dates.adapt_datetime(moment)
        self.assertEqual(Dates.convert_timestamp(text.encode()), moment)

    def test_text_that_is_not_a_date_is_refused(self):
        """Loudly. A column of dates holding something else is worth a stop."""
        with self.assertRaises(ValueError):
            Dates.convert_date(b"the fourth of July")


class TestRegistering(unittest.TestCase):
    """sqlite3 holds ours, and not the ones it is giving up."""

    def setUp(self):
        """Building it is registering it."""
        self.dates = Dates()

    def test_the_converters_are_ours(self):
        self.assertIs(sqlite3.converters["DATE"], Dates.convert_date)
        self.assertIs(sqlite3.converters["TIMESTAMP"], Dates.convert_timestamp)

    def test_the_adapters_are_ours(self):
        adapters = sqlite3.adapters
        self.assertIs(adapters[(datetime.date, sqlite3.PrepareProtocol)],
                      Dates.adapt_date)
        self.assertIs(adapters[(datetime.datetime, sqlite3.PrepareProtocol)],
                      Dates.adapt_datetime)

    def test_a_second_registration_changes_nothing(self):
        """Every DBMS built registers them again, tests included."""
        Dates()
        self.assertIs(sqlite3.converters["DATE"], Dates.convert_date)


if __name__ == "__main__":
    unittest.main()
