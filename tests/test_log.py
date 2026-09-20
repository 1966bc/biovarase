# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for log.py, on files in a temporary folder.

Run them from the project directory:

    python3 -m unittest discover -s tests -v
"""

import os
import tempfile
import unittest

from log import Log


class LogTestCase(unittest.TestCase):
    """A Log writing into a folder that goes away with the test."""

    def setUp(self):
        """A temporary folder, and a log inside it."""
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "biovarase.log")
        self.log = Log(self.path)

    def tearDown(self):
        """The folder goes, with everything written in it."""
        self.folder.cleanup()

    def read(self, path=None):
        """What a log file holds."""
        with open(path or self.path, encoding="utf-8") as f:
            return f.read()


class TestWriting(LogTestCase):
    """What an entry says, and when the file is born."""

    def test_nothing_is_written_until_something_happens(self):
        """The file is born with the first entry, not with the Log."""
        self.assertTrue(self.log.is_empty())
        self.assertFalse(os.path.exists(self.path))

    def test_an_error_says_when_where_and_what(self):
        """The entry carries the level, the caller, and the message."""
        self.log.error("read failed: SELECT * FROM tabula_rasa")
        entry = self.read()
        self.assertIn("ERROR", entry)
        self.assertIn("test_an_error_says_when_where_and_what", entry)
        self.assertIn("tabula_rasa", entry)

    def test_entries_are_appended(self):
        """A second error does not overwrite the first."""
        self.log.error("first")
        self.log.error("second")
        entry = self.read()
        self.assertIn("first", entry)
        self.assertIn("second", entry)

    def test_an_exception_brings_its_traceback(self):
        """Called from inside an except block, it writes what was raised."""
        try:
            raise ValueError("no such lot")
        except ValueError as exc:
            self.log.exception("save failed: {0}".format(exc))
        entry = self.read()
        self.assertIn("no such lot", entry)
        self.assertIn("Traceback", entry)


class TestRotation(LogTestCase):
    """The file moved aside when it is full, and the copies kept."""

    def fill(self):
        """Write past MAX_SIZE, so the next entry rotates the file."""
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("x" * (Log.MAX_SIZE + 1))

    def test_a_full_file_is_moved_aside(self):
        """The old file becomes .1 and the new entry starts a new file."""
        self.fill()
        self.log.error("after the rotation")
        self.assertTrue(os.path.exists(self.path + ".1"))
        self.assertIn("after the rotation", self.read())
        self.assertNotIn("after the rotation", self.read(self.path + ".1"))

    def test_only_so_many_copies_are_kept(self):
        """BACKUPS of them: the oldest is overwritten, not piled up."""
        for _ in range(Log.BACKUPS + 2):
            self.fill()
            self.log.error("entry")
        kept = [name for name in os.listdir(self.folder.name) if ".log." in name]
        self.assertEqual(len(kept), Log.BACKUPS)


class TestTrace(LogTestCase):
    """The trace: on the terminal, and only when asked for."""

    def test_silent_unless_started_with_trace(self):
        """Without --trace the trace writes nothing anywhere."""
        self.log.trace("a row")
        self.assertFalse(os.path.exists(self.path))

    def test_the_trace_never_touches_the_file(self):
        """It prints; the file is for errors."""
        log = Log(self.path, tracing=True)
        log.trace("a row")
        self.assertTrue(log.is_empty())


if __name__ == "__main__":
    unittest.main()
