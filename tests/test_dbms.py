# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for dbms.py, on the real schema in memory: no file is ever touched.

The database is built from schema.sql, the one the program uses, so a column
renamed there and not here makes these tests fail rather than pass quietly.

Run them from the project directory:

    python3 -m unittest discover -s tests -v
"""

import os
import sqlite3
import tempfile
import unittest

from dbms import DBMS

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "schema.sql")

# The smallest laboratory that can hold one result.
LABORATORY = """
INSERT INTO users (user_id, last_name, nickname, pswrd, role)
VALUES (1, 'Costanzi', '1966bc', 'not-a-real-hash', 0);
INSERT INTO suppliers (supplier_id, description) VALUES (1, 'Bio-Rad');
INSERT INTO equipments (equipment_id, supplier_id, description) VALUES (1, 1, 'Analyzer 100');
INSERT INTO workstations (workstation_id, equipment_id, description) VALUES (1, 1, 'ANL-1');
INSERT INTO controls (control_id, supplier_id, description) VALUES (1, 1, 'Multiqual');
INSERT INTO units (unit_id, description) VALUES (1, 'mg/dL');
INSERT INTO samples (sample_id, description) VALUES (1, 'Serum');
INSERT INTO methods (method_id, description) VALUES (1, 'Enzymatic');
INSERT INTO tests (test_id, description) VALUES (1, 'Glucose');
INSERT INTO test_methods (test_method_id, test_id, sample_id, method_id, unit_id, code)
VALUES (1, 1, 1, 1, 1, 'GLU');
INSERT INTO batches (batch_id, control_id, test_method_id, workstation_id,
                     lot_number, description, target, sd)
VALUES (1, 1, 1, 1, 'LOT-1123', 'Level 1', 95.0, 2.5);
"""


class MemoryLog:
    """A stand-in for Log that keeps its entries in a list instead of a file.

    DBMS only calls log.error(), so this is all a test needs: the entries can
    be read back without opening a file.
    """

    def __init__(self):
        self.entries = []

    def error(self, message):
        """Keep the message, as Log would write it."""
        self.entries.append(message)


class DBMSTestCase(unittest.TestCase):
    """A DBMS on a database in memory, holding one small laboratory."""

    def setUp(self):
        """Build the database from schema.sql and fill it."""
        self.log = MemoryLog()
        self.db = DBMS(":memory:", self.log)
        with open(SCHEMA) as schema:
            self.db.con.executescript(schema.read())
        # executescript commits, and foreign keys cannot be turned on inside a
        # transaction: the pragma goes on again afterwards.
        self.db.con.execute("PRAGMA foreign_keys = ON")
        self.db.con.executescript(LABORATORY)

    def tearDown(self):
        """Close the connection: the database goes with it."""
        self.db.close()


class TestRead(DBMSTestCase):
    """read: rows by name, and failures that stay failures."""

    def test_fetch_true_returns_a_list(self):
        """A list, and it can be counted."""
        rows = self.db.read(True, "SELECT * FROM batches")
        self.assertEqual(len(rows), 1)

    def test_fetch_false_returns_one_row(self):
        """One row, read by column name."""
        row = self.db.read(False, "SELECT * FROM batches WHERE batch_id = ?", (1,))
        self.assertEqual(row["lot_number"], "LOT-1123")

    def test_no_rows_is_an_empty_list(self):
        """Nothing matched is an empty list, not None."""
        rows = self.db.read(True, "SELECT * FROM results")
        self.assertEqual(rows, [])

    def test_no_row_is_none(self):
        """Nothing matched with fetch False is None."""
        row = self.db.read(False, "SELECT * FROM results WHERE result_id = ?", (99,))
        self.assertIsNone(row)

    def test_a_failed_read_is_raised_and_logged(self):
        """A broken query does not come back looking like an empty table."""
        with self.assertRaises(sqlite3.Error):
            self.db.read(True, "SELECT * FROM tabula_rasa")
        self.assertEqual(len(self.log.entries), 1)


class TestWrite(DBMSTestCase):
    """write: what comes back, and what happens when it fails."""

    def test_an_insert_returns_the_new_id(self):
        """The id of the row just written."""
        written = self.db.write(
            "INSERT INTO results (batch_id, result) VALUES (?, ?)", (1, 95.0))
        self.assertEqual(written, 1)

    def test_an_update_returns_the_rows_touched(self):
        """On an update there is no new row: the count is what is useful."""
        self.db.write("INSERT INTO results (batch_id, result) VALUES (?, ?)", (1, 95.0))
        self.db.write("INSERT INTO results (batch_id, result) VALUES (?, ?)", (1, 96.0))
        written = self.db.write("UPDATE results SET status = ? WHERE batch_id = ?",
                                (0, 1))
        self.assertEqual(written, 2)

    def test_a_delete_returns_the_rows_touched(self):
        """Same for a delete."""
        self.db.write("INSERT INTO results (batch_id, result) VALUES (?, ?)", (1, 95.0))
        written = self.db.write("DELETE FROM results WHERE batch_id = ?", (1,))
        self.assertEqual(written, 1)

    def test_a_failed_write_is_raised_and_leaves_nothing_behind(self):
        """A result on a lot that does not exist is refused, and rolled back."""
        with self.assertRaises(sqlite3.Error):
            self.db.write("INSERT INTO results (batch_id, result) VALUES (?, ?)",
                          (99, 95.0))
        self.assertEqual(self.db.read(True, "SELECT * FROM results"), [])
        self.assertEqual(len(self.log.entries), 1)

    def test_foreign_keys_are_on(self):
        """They are off by default in SQLite, and have to be asked for."""
        row = self.db.read(False, "PRAGMA foreign_keys")
        self.assertEqual(row[0], 1)


class TestStatementsFromTheSchema(DBMSTestCase):
    """The statements built by asking the schema, not by counting columns."""

    def test_the_primary_key_comes_from_the_schema(self):
        """PRAGMA table_info says which column is the key."""
        self.assertEqual(self.db.get_primary_key("results"), "result_id")

    def test_the_fields_leave_the_key_out(self):
        """The key is left out because it is the key, not because it is first."""
        fields = self.db.get_fields("batches")
        self.assertNotIn("batch_id", fields)
        self.assertIn("lot_number", fields)

    def test_the_schema_is_asked_once(self):
        """The second question is answered from dict_tables."""
        self.db.get_fields("results")
        self.db.get_fields("results")
        self.assertEqual(list(self.db.dict_tables), ["results"])

    def test_an_unknown_table_is_refused(self):
        """By name, so the message says which one."""
        with self.assertRaises(ValueError):
            self.db.get_table_info("tabula_rasa")

    def test_an_insert_is_built_by_name(self):
        """The values are given by column name and land in their own column."""
        values = {"batch_id": 1, "result": 95.0, "received": "2026-09-20 08:00:00",
                  "reagent_lot": "R-1", "status": 1, "created_by": 1,
                  "created_at": "2026-09-20 08:00:00"}
        sql, args = self.db.get_insert("results", values)
        result_id = self.db.write(sql, args)
        written = self.db.get_selected("results", "result_id", result_id)
        self.assertEqual(written["result"], 95.0)
        self.assertEqual(written["reagent_lot"], "R-1")

    def test_an_update_is_built_by_name(self):
        """And the key goes last, where the statement expects it."""
        values = {"batch_id": 1, "result": 95.0, "received": "2026-09-20 08:00:00",
                  "reagent_lot": "R-1", "status": 1, "created_by": 1,
                  "created_at": "2026-09-20 08:00:00"}
        sql, args = self.db.get_insert("results", values)
        result_id = self.db.write(sql, args)

        values["result"] = 69.4
        sql, args = self.db.get_update("results", result_id, values)
        self.db.write(sql, args)

        written = self.db.get_selected("results", "result_id", result_id)
        self.assertEqual(written["result"], 69.4)

    def test_a_missing_column_is_refused(self):
        """Rather than written as null, or slid into the next column."""
        with self.assertRaises(ValueError):
            self.db.get_insert("results", {"batch_id": 1})

    def test_a_column_that_is_not_one_is_refused(self):
        """A typo in a name is an error, not a value quietly dropped."""
        values = {"batch_id": 1, "result": 95.0, "received": None,
                  "reagent_lot": None, "status": 1, "created_by": 1,
                  "created_at": None, "operator_code": "ALCI-1"}
        with self.assertRaises(ValueError):
            self.db.get_insert("results", values)


class TestSession(DBMSTestCase):
    """The one row the audit triggers read to know who is working."""

    def test_the_login_writes_who_is_working(self):
        """And the audit trail picks it up from there."""
        self.db.set_session_user(1)
        self.db.write("INSERT INTO results (batch_id, result) VALUES (?, ?)", (1, 95.0))
        row = self.db.read(False, "SELECT log_id FROM audit_results")
        self.assertEqual(row["log_id"], 1)

    def test_the_logout_clears_it(self):
        """With nobody logged in the audit says nobody, not the last name known."""
        self.db.set_session_user(1)
        self.db.set_session_user(None)
        self.db.write("INSERT INTO results (batch_id, result) VALUES (?, ?)", (1, 95.0))
        row = self.db.read(False, "SELECT log_id FROM audit_results")
        self.assertIsNone(row["log_id"])


class TestDump(unittest.TestCase):
    """The dump: the whole database as SQL, in a file named after the moment."""

    def setUp(self):
        """A database in memory with one table in it."""
        self.db = DBMS(":memory:", MemoryLog())
        self.db.con.executescript(
            "CREATE TABLE units (unit_id INTEGER PRIMARY KEY, description TEXT);"
            "INSERT INTO units VALUES (1, 'mg/dL');")

    def tearDown(self):
        """Close the connection."""
        self.db.close()

    def test_the_dump_rebuilds_the_database(self):
        """What comes out can be read back in."""
        with tempfile.TemporaryDirectory() as folder:
            path = self.db.dump(folder)
            self.assertTrue(os.path.exists(path))
            again = sqlite3.connect(":memory:")
            with open(path) as written:
                again.executescript(written.read())
            row = again.execute("SELECT description FROM units").fetchone()
            again.close()
        self.assertEqual(row[0], "mg/dL")


if __name__ == "__main__":
    unittest.main()
