# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for eqa.py: one z score, and the two that read a whole round.

The numbers are written so that what is being tested can be read off them.
The pair of rounds in TestTheTwoTogether is the reason both scores exist: the
same five misses, once all on the same side and once not, and only one of the
two scores can tell them apart.

    python3 -m unittest discover -s tests -v
"""

import unittest

from eqa import Eqa


class EqaTestCase(unittest.TestCase):

    def setUp(self):
        self.eqa = Eqa()


class TestTheZScore(EqaTestCase):
    """How far one result fell from the value the scheme assigned."""

    def test_a_result_on_the_assigned_value_is_zero(self):
        self.assertEqual(self.eqa.get_z(10.0, 10.0, 0.5), 0.0)

    def test_one_standard_deviation_high_is_one(self):
        self.assertEqual(self.eqa.get_z(10.5, 10.0, 0.5), 1.0)

    def test_the_sign_says_which_way(self):
        """Reading high and reading low are two different problems."""
        self.assertEqual(self.eqa.get_z(9.0, 10.0, 0.5), -2.0)

    def test_a_standard_deviation_of_zero_judges_nothing(self):
        """It is not a perfect scheme, it is a missing number."""
        with self.assertRaises(ValueError):
            self.eqa.get_z(10.0, 10.0, 0.0)


class TestTheTwoTogether(EqaTestCase):
    """Why a round needs both scores and not one."""

    #: Five analytes, every one of them about one deviation high.
    ALL_HIGH = [0.8, 0.9, 1.1, 0.7, 1.0]

    #: The same five misses, scattered either side instead.
    SCATTERED = [0.8, -0.9, 1.1, -0.7, 1.0]

    def test_a_laboratory_high_on_everything_shows_in_rsz(self):
        """4.5 / sqrt(5) = 2.01: questionable, and nothing was out on its own."""
        self.assertEqual(self.eqa.get_rsz(self.ALL_HIGH), 2.01)

    def test_and_does_not_show_in_sz2(self):
        """Every miss is about one deviation, so the mean square is about one."""
        self.assertEqual(self.eqa.get_sz2(self.ALL_HIGH), 0.83)

    def test_the_same_misses_scattered_cancel_in_rsz(self):
        """1.3 / sqrt(5) = 0.58: no side to be on."""
        self.assertEqual(self.eqa.get_rsz(self.SCATTERED), 0.58)

    def test_and_are_identical_in_sz2(self):
        """Squaring loses the sign, which is what it is for."""
        self.assertEqual(self.eqa.get_sz2(self.SCATTERED),
                         self.eqa.get_sz2(self.ALL_HIGH))

    def test_one_analyte_badly_out_raises_sz2_and_leaves_rsz(self):
        """A single miss of four deviations, with the rest on the value."""
        scores = [0.0, 0.0, 4.0, 0.0, -4.0]
        self.assertEqual(self.eqa.get_rsz(scores), 0.0)
        self.assertEqual(self.eqa.get_sz2(scores), 6.4)

    def test_an_empty_round_has_nothing_to_say(self):
        self.assertEqual(self.eqa.get_rsz([]), 0.0)
        self.assertEqual(self.eqa.get_sz2([]), 0.0)


class TestTheVerdict(EqaTestCase):
    """The thresholds of ISO 13528, read on the size and not on the sign."""

    def test_inside_two_is_satisfactory(self):
        self.assertEqual(self.eqa.get_verdict(1.9), "Satisfactory")

    def test_two_is_already_questionable(self):
        self.assertEqual(self.eqa.get_verdict(2.0), "Questionable")

    def test_three_is_unsatisfactory(self):
        self.assertEqual(self.eqa.get_verdict(3.0), "Unsatisfactory")

    def test_the_sign_does_not_matter(self):
        """Two deviations out is two deviations out, either way."""
        self.assertEqual(self.eqa.get_verdict(-3.4),
                         self.eqa.get_verdict(3.4))


if __name__ == "__main__":
    unittest.main()
