# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for the register of windows and the Observer, with real windows.

A window that is told about a change after it has been destroyed raises from
inside the callback of whoever saved - and the one who saved is left staring
at an error about a window they never opened. It happens when a window
subscribes and forgets to unsubscribe, which is a line nobody misses until
months later.

These tests open the real windows on the sample database, close them, and
look at who is left listening.

They need a display, and are skipped where there is none. On a desktop they
open and close in front of whoever is working; a screen of their own spares
them that, and is also how the machine with no screen runs them at all.

    xvfb-run -a python3 -m unittest discover -s tests -v
"""

import os
import shutil
import tempfile
import unittest

HAS_DISPLAY = bool(os.environ.get("DISPLAY"))

if HAS_DISPLAY:
    import ui.day

    from dbms import DBMS
    from log import Log
    from ui.app import App


@unittest.skipUnless(HAS_DISPLAY, "no display")
class WindowTestCase(unittest.TestCase):
    """The application, logged in, on the sample database."""

    def setUp(self):
        """Start the program and log in as the administrator."""
        self.log = Log(os.devnull)
        self.app = App("Biovarase", self.log)
        self.app.update()

        login = self.get_frame()
        login.nickname.set("admin")
        login.password.set("pass")
        login.on_login()
        self.app.update()

        self.main = self.get_frame()
        self.engine = self.main.engine

    def tearDown(self):
        """Close everything, whatever the test left open."""
        self.app.destroy()

    def get_frame(self):
        """The frame filling the root window at the moment."""
        return [w for w in self.app.winfo_children()
                if w.winfo_class() == "TFrame"][0]


class TestTheRegister(WindowTestCase):
    """One window per name, and none left behind."""

    def test_the_main_window_is_there(self):
        """Logging in replaces the login with the main window."""
        self.assertEqual(len(self.main.dict_categories), 7)

    def test_a_window_is_opened_once(self):
        """Asking twice brings the one open to the front, it does not build a second."""
        self.main.on_batches()
        first = self.engine.windows.get("batches")
        self.main.on_batches()
        self.assertIs(self.engine.windows.get("batches"), first)

    def test_a_closed_window_leaves_the_register(self):
        """<Destroy> takes it out, however it was closed."""
        self.main.on_batches()
        self.engine.windows.get("batches").on_cancel()
        self.app.update()
        self.assertIsNone(self.engine.windows.get("batches"))

    def test_master_data_windows_open(self):
        """Every list in the Edit menu builds and reads its table."""
        import ui.tests
        import ui.units

        for module in (ui.units, ui.tests):
            self.main.on_master_data(module)
            window = self.engine.windows.get(module.UI.TABLE)
            self.assertIsNotNone(window, module.UI.TABLE)
            self.assertTrue(window.dict_items, module.UI.TABLE)
            window.on_cancel()
            self.app.update()


class TestTheObserver(WindowTestCase):
    """Nobody is left listening after their window is gone."""

    def get_listeners(self):
        """How many callbacks are registered, per event."""
        return {event: len(callbacks)
                for event, callbacks in self.engine.events.subscribers.items()
                if callbacks}

    def test_the_main_window_listens(self):
        """It has to: the master data can change while it is open."""
        self.assertIn("tests", self.get_listeners())

    def test_the_main_window_stops_when_it_goes(self):
        """Or a change of user would talk to the window of the user before."""
        self.main.destroy()
        self.app.update()
        self.assertEqual(self.get_listeners(), {})

    def test_a_list_window_stops_when_it_is_closed(self):
        """The same for every list: open it, close it, nobody is listening."""
        import ui.units

        before = self.get_listeners()
        self.main.on_master_data(ui.units)
        self.assertIn("units", self.get_listeners())

        self.engine.windows.get("units").on_cancel()
        self.app.update()
        self.assertEqual(self.get_listeners(), before)

    def test_the_batches_window_stops_when_it_is_closed(self):
        """It listens to two events, and has to let go of both."""
        before = self.get_listeners()
        self.main.on_batches()
        self.engine.windows.get("batches").on_cancel()
        self.app.update()
        self.assertEqual(self.get_listeners(), before)

    def test_an_event_reaches_the_window_that_asked(self):
        """The main window reads its lists again when master data is saved."""
        heard = []
        self.engine.events.subscribe("tests", lambda row_id: heard.append(row_id))
        self.engine.events.notify("tests", 42)
        self.assertEqual(heard, [42])


class TestTheDay(WindowTestCase):
    """The form that enters a bench's controls in one pass.

    This one writes, and the database it would write into is the sample
    laboratory that ships with the program: it works on a copy instead, and
    throws it away afterwards. A test that leaves a morning's work behind in
    a file somebody is about to clone is not a test.
    """

    def setUp(self):

        super().setUp()
        handle, self.copy = tempfile.mkstemp(suffix=".sl3")
        os.close(handle)
        shutil.copy(self.engine.get_database(), self.copy)

        self.engine.db.close()
        self.engine.db = DBMS(self.copy, self.engine.log)
        self.engine.db.set_session_user(self.engine.log_user["user_id"])

        self.window = ui.day.UI(self.main)
        self.window.on_open()
        self.app.update()

    def tearDown(self):

        self.window.on_cancel()
        super().tearDown()
        os.remove(self.copy)

    def get_results(self):
        """How many results the copy holds now."""
        return self.engine.db.read(False,
                                   "SELECT COUNT(*) AS n FROM results", ())["n"]

    def test_every_lot_of_the_bench_gets_a_box(self):
        """One box per lot open on the bench chosen, and none without one."""
        self.assertTrue(self.window.boxes)
        self.assertEqual(len(self.window.boxes), len(self.window.get_lots()))

    def test_what_was_typed_is_written_and_nothing_else(self):
        """Two boxes filled, two results: an empty box is a control not run."""
        lots = list(self.window.boxes)
        before = self.get_results()

        self.window.boxes[lots[0]].set("12.5")
        self.window.boxes[lots[1]].set("7.25")
        self.window.on_save()

        self.assertEqual(self.get_results(), before + 2)

    def test_a_comma_is_a_decimal_point(self):
        """It is what the keypad of this country writes."""
        lot = list(self.window.boxes)[0]
        self.window.boxes[lot].set("12,5")
        self.window.on_save()

        row = self.engine.db.read(
            False, "SELECT result FROM results ORDER BY result_id DESC LIMIT 1", ())
        self.assertEqual(row["result"], 12.5)

    def test_the_audit_trail_names_whoever_typed_it(self):
        """The triggers read the session table, which the login wrote."""
        lot = list(self.window.boxes)[0]
        self.window.boxes[lot].set("9.9")
        self.window.on_save()

        row = self.engine.db.read(
            False,
            """SELECT a.operation, a.result, a.log_id
                 FROM audit_results a
             ORDER BY a.audit_id DESC LIMIT 1""", ())
        self.assertEqual(row["operation"], "INSERT")
        self.assertEqual(row["result"], 9.9)
        self.assertEqual(row["log_id"], self.engine.log_user["user_id"])

    def test_the_boxes_are_emptied_after_saving(self):
        """Or the next Save would write the same morning twice."""
        lot = list(self.window.boxes)[0]
        self.window.boxes[lot].set("1.0")
        self.window.on_save()

        self.assertEqual([value.get() for value in self.window.boxes.values()],
                         [""] * len(self.window.boxes))


if __name__ == "__main__":
    unittest.main()
