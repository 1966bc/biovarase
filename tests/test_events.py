# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for events.py: no window is needed to try the Observer.

Run them from the project directory:

    python3 -m unittest discover -s tests -v
"""

import unittest

from events import Events


class SilentLog:
    """A stand-in for Log: Events only calls trace(), and here it says nothing."""

    def trace(self, message):
        """Keep quiet."""
        pass


class Listener:
    """Something that asks to be told, and remembers what it was told."""

    def __init__(self):
        self.heard = []

    def on_result_changed(self, row_id):
        """Write down the row that changed."""
        self.heard.append(row_id)


class TestEvents(unittest.TestCase):
    """Who is told what, and when they stop being told."""

    def setUp(self):
        """One Events and one listener."""
        self.events = Events(SilentLog())
        self.listener = Listener()

    def test_a_subscriber_is_told(self):
        """With the row that changed, so a list can land on it."""
        self.events.subscribe("result_changed", self.listener.on_result_changed)
        self.events.notify("result_changed", 42)
        self.assertEqual(self.listener.heard, [42])

    def test_nobody_listening_is_not_an_error(self):
        """A window that saves does not care whether anything is open."""
        self.events.notify("result_changed", 42)
        self.assertEqual(self.listener.heard, [])

    def test_subscribing_twice_is_told_once(self):
        """A window that opens twice does not redraw itself twice."""
        self.events.subscribe("result_changed", self.listener.on_result_changed)
        self.events.subscribe("result_changed", self.listener.on_result_changed)
        self.events.notify("result_changed", 42)
        self.assertEqual(self.listener.heard, [42])

    def test_unsubscribing_stops_it(self):
        """A window that closes is not told any more."""
        self.events.subscribe("result_changed", self.listener.on_result_changed)
        self.events.unsubscribe("result_changed", self.listener.on_result_changed)
        self.events.notify("result_changed", 42)
        self.assertEqual(self.listener.heard, [])

    def test_a_callback_may_unsubscribe_while_it_is_told(self):
        """The callbacks are called on a copy, so the list may change meanwhile."""
        def leave(row_id):
            self.events.unsubscribe("result_changed", leave)
            self.listener.heard.append(row_id)

        self.events.subscribe("result_changed", leave)
        self.events.subscribe("result_changed", self.listener.on_result_changed)
        self.events.notify("result_changed", 42)
        self.assertEqual(self.listener.heard, [42, 42])

    def test_an_event_nobody_ever_hears_is_refused(self):
        """A typo in the name is an error where it is written."""
        with self.assertRaises(ValueError):
            self.events.notify("results_changed", 42)

    def test_subscribing_to_a_typo_is_refused_too(self):
        """So a window cannot wait for something that will never arrive."""
        with self.assertRaises(ValueError):
            self.events.subscribe("batches_changed", self.listener.on_result_changed)


if __name__ == "__main__":
    unittest.main()
