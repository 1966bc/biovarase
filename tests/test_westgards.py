# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for westgards.py: the multirule, one rule at a time.

The series are written by hand around a target of 100 with a standard
deviation of 10, so a value is its own z score: 130 is three standard
deviations, 85 is one and a half below. That way what each test is about can
be read off the list of numbers without computing anything.

The order matters as much as the rules. A run that breaks 1:3S and 1:2S at
once is stopped by 1:3S, because what is reported is the reason to reject
and not the first thing noticed.

    python3 -m unittest discover -s tests -v
"""

import unittest

from westgards import Westgards

TARGET = 100.0
SD = 10.0

#: A series that breaks nothing: twelve results inside one standard
#: deviation, alternating around the target so no run builds up.
IN_CONTROL = [101.0, 99.0, 103.0, 97.0, 102.0, 98.0,
              104.0, 96.0, 101.0, 99.0, 102.0, 98.0]


class WestgardTestCase(unittest.TestCase):
    """The rules, read on series written around 100 +- 10."""

    def setUp(self):
        self.westgards = Westgards()
        self.limits = self.westgards._calculate_control_limits(TARGET, SD)

    def get_rule(self, series):
        """What stops the run, or Accept."""
        return self.westgards.get_westgard_violation_rule(TARGET, SD, series)


class TestTheRules(WestgardTestCase):
    """One at a time, each on the shape it is meant to catch."""

    def test_a_series_in_control_is_accepted(self):
        self.assertEqual(self.get_rule(IN_CONTROL), "Accept")

    def test_one_past_two_deviations_is_a_warning(self):
        """1:2S: a single result out there is a warning, not a rejection."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-1] + [121.0]), "1:2S")

    def test_one_past_three_deviations_stops_the_run(self):
        """1:3S: the rejection everybody knows."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-1] + [131.0]), "1:3S")

    def test_two_running_past_two_on_the_same_side(self):
        """2:2S: two in a row out on one side is systematic, not chance."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-2] + [122.0, 123.0]), "2:2S")

    def test_two_running_past_two_on_opposite_sides_is_the_range_rule(self):
        """R:4S: four deviations between two results is random error."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-2] + [121.0, 79.0]), "R:4S")

    def test_four_running_past_one_on_the_same_side(self):
        """4:1S: a mean that has moved, seen before it goes further."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-4] + [111.0, 112.0,
                                                          113.0, 114.0]), "4:1S")

    def test_ten_running_on_the_same_side_of_the_mean(self):
        """10:X: ten results on one side, none of them out of limits."""
        series = [101.0, 102.0, 103.0, 104.0, 105.0,
                  101.0, 102.0, 103.0, 104.0, 105.0]
        self.assertEqual(self.get_rule(series), "10:X")


class TestTheOrder(WestgardTestCase):
    """Which rule is reported when a run breaks more than one."""

    def test_the_rejection_is_reported_before_the_warning(self):
        """A result past three deviations is also past two: 1:3S wins."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-1] + [135.0]), "1:3S")

    def test_two_at_two_deviations_is_reported_over_the_single_one(self):
        """2:2S says systematic where 1:2S would say look again."""
        self.assertEqual(self.get_rule(IN_CONTROL[:-2] + [121.0, 122.0]), "2:2S")

    def test_a_run_on_one_side_is_found_without_anything_out_of_limits(self):
        """Nothing here is past even one deviation, and it is still a rule."""
        series = [101.0, 102.0, 103.0, 104.0, 105.0,
                  106.0, 107.0, 105.0, 104.0, 103.0]
        self.assertEqual(self.get_rule(series), "10:X")


class TestWhatIsNotEnough(WestgardTestCase):
    """What the rules do with series too short to say anything."""

    def test_a_short_series_breaks_no_run_rule(self):
        """Four results cannot show ten on one side."""
        self.assertEqual(self.get_rule([101.0, 102.0, 103.0, 104.0]), "Accept")

    def test_a_single_result_past_three_is_still_a_rejection(self):
        """1:3S needs one result, and one result is what it has."""
        self.assertEqual(self.get_rule([131.0]), "1:3S")


class TestTheLimits(WestgardTestCase):
    """The limits the rules are read against, computed once."""

    def test_the_limits_are_the_target_plus_so_many_deviations(self):
        self.assertEqual(self.limits["sd1"], 110.0)
        self.assertEqual(self.limits["sd2"], 120.0)
        self.assertEqual(self.limits["sd3"], 130.0)

    def test_and_the_same_below(self):
        self.assertEqual(self.limits["sd_1"], 90.0)
        self.assertEqual(self.limits["sd_2"], 80.0)
        self.assertEqual(self.limits["sd_3"], 70.0)


if __name__ == "__main__":
    unittest.main()
