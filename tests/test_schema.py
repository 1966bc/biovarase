# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for schema.sql, on a database in memory: no file is ever touched.

What is tested here is what the schema promises on its own, without the
program: that a result cannot point at a lot that does not exist, that a
status is 0 or 1 and nothing else, that the audit trail keeps what happened
even when a row is deleted.

Run them from the project directory:

    python3 -m unittest discover -s tests -v
"""

import os
import sqlite3
import unittest

from engine import Engine

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "sql", "ddl", "001_schema.sql")

# The smallest laboratory that can hold one result: a supplier, an instrument,
# a control material, an analyte, a lot of control on that analyte.
LABORATORY = """
INSERT INTO users (user_id, last_name, nickname, pswrd, role)
VALUES (1, 'Costanzi', '1966bc', 'not-a-real-hash', 0);
UPDATE session SET user_id = 1 WHERE session_id = 1;
INSERT INTO suppliers (supplier_id, description) VALUES (1, 'Bio-Rad');
INSERT INTO equipments (equipment_id, supplier_id, description) VALUES (1, 1, 'Analyzer 100');
INSERT INTO workstations (workstation_id, equipment_id, description) VALUES (1, 1, 'ANL-1');
INSERT INTO controls (control_id, supplier_id, description) VALUES (1, 1, 'Multiqual');
INSERT INTO units (unit_id, description) VALUES (1, 'mg/dL');
INSERT INTO samples (sample_id, description) VALUES (1, 'Serum');
INSERT INTO methods (method_id, description) VALUES (1, 'Enzymatic');
INSERT INTO tests (test_id, description) VALUES (1, 'Glucose');
INSERT INTO actions (action_id, description) VALUES (1, 'Calibration');
INSERT INTO test_methods (test_method_id, test_id, sample_id, method_id, unit_id, code)
VALUES (1, 1, 1, 1, 1, 'GLU');
INSERT INTO batches (batch_id, control_id, test_method_id, workstation_id,
                     lot_number, description, target, sd)
VALUES (1, 1, 1, 1, 'LOT-1123', 'Level 1', 95.0, 2.5);
"""


class TestSchema(unittest.TestCase):
    """The schema on its own: what it accepts and what it refuses."""

    def setUp(self):
        """Build the database in memory and fill it with one small laboratory."""
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        with open(SCHEMA) as schema:
            self.con.executescript(schema.read())
        # executescript commits, and foreign keys cannot be turned on inside a
        # transaction: the pragma goes on afterwards, as the program does it.
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.executescript(LABORATORY)

    def tearDown(self):
        """Close the connection: the database goes with it."""
        self.con.close()

    def test_the_schema_creates_every_table(self):
        """Every table the laboratory needs, session included, and no leftovers."""
        expected = {"units", "samples", "methods", "tests", "categories",
                    "suppliers", "equipments", "controls", "actions", "users",
                    "session", "workstations", "test_methods", "batches",
                    "results", "notes", "audit_results", "audit_batches"}
        rows = self.con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name NOT LIKE 'sqlite_%'").fetchall()
        self.assertEqual({row["name"] for row in rows}, expected)

    def test_a_result_needs_a_lot_that_exists(self):
        """A result points at a lot: an orphan result is refused."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute(
                "INSERT INTO results (batch_id, result) VALUES (?, ?)", (99, 95.0))

    def test_status_is_zero_or_one(self):
        """status says in or out of the statistics: nothing else goes in it."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute(
                "INSERT INTO results (batch_id, result, status) VALUES (?, ?, ?)",
                (1, 95.0, 7))

    def test_the_session_holds_one_row(self):
        """The current user is one, so the table that holds them has one row."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute(
                "INSERT INTO session (session_id, user_id) VALUES (?, ?)", (2, 1))

    def test_a_note_goes_with_its_result(self):
        """A note is about a result: when the result goes, the note goes."""
        self.con.execute(
            "INSERT INTO results (result_id, batch_id, result) VALUES (?, ?, ?)",
            (1, 1, 95.0))
        self.con.execute(
            "INSERT INTO notes (result_id, action_id, description, modified)"
            " VALUES (?, ?, ?, ?)",
            (1, 1, 'Recalibrated', '2026-09-20'))
        self.con.execute("DELETE FROM results WHERE result_id = ?", (1,))
        left = self.con.execute("SELECT COUNT(*) AS n FROM notes").fetchone()
        self.assertEqual(left["n"], 0)


class TestAuditTrail(unittest.TestCase):
    """The audit trail: with no validation step, this is the whole record."""

    def setUp(self):
        """Build the database and enter one result on the lot."""
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        with open(SCHEMA) as schema:
            self.con.executescript(schema.read())
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.executescript(LABORATORY)
        self.con.execute(
            "INSERT INTO results (result_id, batch_id, result, created_by)"
            " VALUES (?, ?, ?, ?)", (1, 1, 96.4, 1))

    def tearDown(self):
        """Close the connection: the database goes with it."""
        self.con.close()

    def _audit(self):
        """Return the audit rows for the result, oldest first."""
        return self.con.execute(
            "SELECT operation, result, status, log_id FROM audit_results"
            " WHERE result_id = 1 ORDER BY audit_id").fetchall()

    def test_an_insert_is_written_down(self):
        """Entering a result leaves a row that holds the value entered."""
        rows = self._audit()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["operation"], "INSERT")
        self.assertEqual(rows[0]["result"], 96.4)

    def test_an_update_keeps_the_value_as_it_was(self):
        """A correction keeps the old value: that is what makes it a trail."""
        self.con.execute("UPDATE results SET result = ? WHERE result_id = ?",
                         (69.4, 1))
        rows = self._audit()
        self.assertEqual(rows[1]["operation"], "UPDATE")
        self.assertEqual(rows[1]["result"], 96.4)

    def test_a_deleted_result_survives_in_the_audit(self):
        """The row goes from results and stays in audit_results, as it was."""
        self.con.execute("UPDATE results SET status = 0 WHERE result_id = ?", (1,))
        self.con.execute("DELETE FROM results WHERE result_id = ?", (1,))
        rows = self._audit()
        self.assertEqual([row["operation"] for row in rows],
                         ["INSERT", "UPDATE", "DELETE"])
        self.assertEqual(rows[2]["result"], 96.4)
        self.assertEqual(rows[2]["status"], 0)

    def test_the_audit_says_who(self):
        """SQLite has no CURRENT_USER: the trigger reads it from session."""
        rows = self._audit()
        self.assertEqual(rows[0]["log_id"], 1)

    def test_with_nobody_logged_in_the_audit_says_nobody(self):
        """An empty session leaves log_id null, rather than a wrong name."""
        self.con.execute("UPDATE session SET user_id = NULL WHERE session_id = 1")
        self.con.execute("UPDATE results SET result = ? WHERE result_id = ?",
                         (69.4, 1))
        rows = self._audit()
        self.assertIsNone(rows[1]["log_id"])


class TestTheDatabaseFile(unittest.TestCase):
    """Where the database is: the settings say it, not the code.

    An engine is not built here - building one opens the database - so the
    method is called on a stand-in holding the two things it uses: the
    setting, and where the program is.
    """

    def get_path(self, written):
        """What the engine would use, for this setting."""
        return Engine.get_database(_Stand(written))

    def test_a_bare_name_is_taken_beside_the_program(self):
        """So the program finds its database wherever it is started from."""
        path = self.get_path("biovarase.sl3")
        self.assertTrue(os.path.isabs(path))
        self.assertTrue(path.endswith(os.sep + "biovarase.sl3"))

    def test_an_absolute_path_is_taken_as_it_is(self):
        """A database kept somewhere else: another disk, a shared folder."""
        elsewhere = os.sep + os.path.join("var", "lib", "biovarase.sl3")
        self.assertEqual(self.get_path(elsewhere), elsewhere)


class _Stand:
    """The two things get_database asks of the engine, and nothing else."""

    def __init__(self, written):
        self.written = written
        self.config = self

    def get(self, section, key):
        """The setting, whatever is asked for."""
        return self.written

    def get_file(self, name):
        """Beside the program, as the engine does it."""
        return Engine.get_file(self, name)


if __name__ == "__main__":
    unittest.main()
