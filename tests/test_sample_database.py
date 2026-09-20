# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for the database that ships with the program.

It is not a fixture. sql/biovarase.sl3 is downloaded with the repository and
opened by whoever tries the program for the first time, so what is wrong with
it is wrong in public.

The first test here exists because of a real one. A round of a proficiency
scheme was written with a bare date in a column declared TIMESTAMP: SQLite
stores what it is given, the row went in without a word, and every later read
of that table died inside sqlite3's own converter, four frames below anything
this program wrote. Reading every row of every table would have caught it in
a second, so now it does.

The rest check the claims the README and the manual make about this file. A
sample database is an argument, and an argument has to be true.

    python3 -m unittest discover -s tests -v
"""

import os
import sqlite3
import unittest

from eqa import Eqa

DATABASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "sql", "biovarase.sl3")


class SampleTestCase(unittest.TestCase):
    """The shipped database, opened the way the program opens it."""

    def setUp(self):
        self.con = sqlite3.connect(
            DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()

    def get_tables(self):
        """Every table in the file, in the order it was created."""
        rows = self.con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name NOT LIKE 'sqlite_%' ORDER BY rootpage").fetchall()

        return [row["name"] for row in rows]

    def count(self, sql, args=()):
        """The one number a counting statement gives back."""
        return self.con.execute(sql, args).fetchone()[0]


class TestItCanBeRead(SampleTestCase):
    """Every row of every table, which is where the converters run."""

    def test_every_row_of_every_table_comes_back(self):
        """A value of the wrong shape in a typed column dies on the way out.

        Not on the way in: SQLite stores what it is handed. So the only place
        this can be found is here, reading it.
        """
        for table in self.get_tables():
            rows = self.con.execute("SELECT * FROM {0}".format(table)).fetchall()
            for row in rows:
                # Touching every value is the test: the converters run on
                # access, and a row nobody reads is a row nobody has checked.
                self.assertEqual(len(tuple(row)), len(row.keys()), table)

    def test_the_foreign_keys_all_point_at_something(self):
        """Nothing in the file refers to a row that is not there."""
        self.con.execute("PRAGMA foreign_keys = ON")
        self.assertEqual(self.con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_the_file_is_sound(self):
        """What File > Database > Check asks, asked of what is published."""
        self.assertEqual(self.con.execute("PRAGMA integrity_check").fetchone()[0],
                         "ok")


class TestWhatTheReadmeSays(SampleTestCase):
    """The numbers the README quotes about this file."""

    def test_the_analytes_and_the_methods(self):
        self.assertEqual(self.count("SELECT COUNT(*) FROM tests"), 44)
        self.assertEqual(self.count("SELECT COUNT(*) FROM test_methods"), 56)

    def test_six_matrices(self):
        """Serum, urine, keratin, blood, whole blood, plasma."""
        self.assertEqual(
            self.count("SELECT COUNT(DISTINCT sample_id) FROM test_methods"), 6)

    def test_the_lots_and_the_results(self):
        self.assertEqual(self.count("SELECT COUNT(*) FROM batches"), 133)
        self.assertEqual(self.count("SELECT COUNT(*) FROM results"), 8348)

    def test_the_proficiency_rounds(self):
        self.assertEqual(self.count("SELECT COUNT(*) FROM eqa_schemes"), 4)
        self.assertEqual(self.count("SELECT COUNT(*) FROM eqa_rounds"), 8)

    def test_the_audit_trail_has_a_story_and_not_only_insertions(self):
        """Three corrections and one withdrawal: what the History window shows."""
        self.assertEqual(
            self.count("SELECT COUNT(*) FROM audit_results"
                       " WHERE operation = 'UPDATE'"), 4)
        self.assertEqual(
            self.count("SELECT COUNT(*) FROM results WHERE status = 0"), 1)


class TestTheRoundThatMakesThePoint(SampleTestCase):
    """The case the README and the manual send the reader to look at.

    Nineteen analytes, every one of them satisfactory, and a round that is
    not. If the sample data stops showing this, the claim has to go with it.
    """

    def setUp(self):
        super().setUp()
        self.eqa = Eqa()
        rows = self.con.execute(
            """SELECT e.result, e.assigned, e.sd
                 FROM eqa_results e
                 JOIN eqa_rounds r ON r.round_id = e.round_id
                 JOIN eqa_schemes s ON s.scheme_id = r.scheme_id
                WHERE s.description = 'Drugs of abuse in urine'
                  AND r.description = '2026-1'""").fetchall()
        self.scores = [self.eqa.get_z(row["result"], row["assigned"], row["sd"])
                       for row in rows]

    def test_every_analyte_on_its_own_is_satisfactory(self):
        for score in self.scores:
            self.assertEqual(self.eqa.get_verdict(score), "Satisfactory")

    def test_and_the_round_is_not(self):
        self.assertEqual(self.eqa.get_verdict(self.eqa.get_rsz(self.scores)),
                         "Unsatisfactory")

    def test_while_the_other_score_sees_nothing(self):
        """SZ2 cancels nothing and still says the misses were small."""
        self.assertEqual(self.eqa.get_verdict(self.eqa.get_sz2(self.scores)),
                         "Satisfactory")


if __name__ == "__main__":
    unittest.main()
