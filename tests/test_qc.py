# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Tests for qc.py: the statistics, and the goals they are held to.

Worked by hand or taken from the sources, not from the program: a test that
computes the expected value the way the code does proves that the code
agrees with itself.

    python3 -m unittest discover -s tests -v
"""

import unittest

from qc import QC


class Settings:
    """A stand-in for Config holding the two settings QC reads."""

    def __init__(self, ddof=1, zscore=1.65):
        self.values = {("statistics", "ddof"): ddof,
                       ("statistics", "zscore"): zscore}

    def get_int(self, section, key):
        return int(self.values[(section, key)])

    def get_float(self, section, key):
        return float(self.values[(section, key)])


class QCTestCase(unittest.TestCase):
    """A QC reading its settings from the stand-in."""

    def setUp(self):
        self.qc = QC(Settings())


class TestTheSeries(QCTestCase):
    """Mean, standard deviation, coefficient of variation, range."""

    #: Five results whose mean is 10 and whose sample SD is 1.5811...
    SERIES = [8.0, 9.0, 10.0, 11.0, 12.0]

    def test_the_mean(self):
        """50 over 5."""
        self.assertEqual(self.qc.get_mean(self.SERIES), 10.0)

    def test_the_sample_standard_deviation(self):
        """Squares 4+1+0+1+4 = 10, over n-1 = 4, square root: 1.58."""
        self.assertEqual(self.qc.get_sd(self.SERIES), 1.58)

    def test_the_population_standard_deviation(self):
        """The same 10, over n = 5: 1.41."""
        self.assertEqual(self.qc.get_sd(self.SERIES, ddof=0), 1.41)

    def test_the_coefficient_of_variation(self):
        """1.5811 over 10, as a percentage, rounded once at the end."""
        self.assertEqual(self.qc.get_cv(self.SERIES), 15.81)

    def test_the_range(self):
        """Highest minus lowest."""
        self.assertEqual(self.qc.get_range(self.SERIES), 4.0)

    def test_an_empty_series_has_no_mean(self):
        """And says 0 rather than raising: there is nothing to average."""
        self.assertEqual(self.qc.get_mean([]), 0.0)

    def test_one_result_has_no_spread(self):
        """A sample of one has no standard deviation to speak of."""
        self.assertEqual(self.qc.get_sd([7.0]), 0.0)

    def test_a_series_around_zero_has_no_cv(self):
        """The spread as a percentage of nothing is not a number."""
        self.assertEqual(self.qc.get_cv([-1.0, 0.0, 1.0]), 0.0)


class TestTheBias(QCTestCase):
    """How far the series sits from the target, and which way."""

    def test_reading_high_is_positive(self):
        self.assertEqual(self.qc.get_bias(105.0, 100.0), 5.0)

    def test_reading_low_is_negative(self):
        """The sign is the difference between two problems."""
        self.assertEqual(self.qc.get_bias(95.0, 100.0), -5.0)

    def test_no_target_is_no_bias(self):
        """A percentage of zero is not a number."""
        self.assertEqual(self.qc.get_bias(5.0, 0.0), 0.0)


class TestTheGoals(QCTestCase):
    """The desirable specifications, as the EFLM task group writes them."""

    #: Cortisol, the figures used in the sample database.
    CVI, CVG = 20.9, 45.6

    def test_allowable_imprecision_is_half_the_within_subject_variation(self):
        """CVa = 0.5 x CVi."""
        self.assertEqual(self.qc.get_imp(self.CVI), 10.45)

    def test_allowable_bias_is_a_quarter_of_the_total_variation(self):
        """bias = 0.25 x sqrt(CVi^2 + CVg^2): sqrt(436.81 + 2079.36) = 50.16."""
        self.assertEqual(self.qc.get_allowable_bias(self.CVI, self.CVG), 12.54)

    def test_allowable_total_error_is_the_two_together(self):
        """TEa = 1.65 x CVa + bias = 17.24 + 12.54."""
        self.assertEqual(self.qc.get_tea(self.CVI, self.CVG), 29.78)

    def test_the_coverage_factor_is_the_setting(self):
        """At k = 2 the same analyte allows more: 20.90 + 12.54."""
        qc = QC(Settings(zscore=2.0))
        self.assertEqual(qc.get_tea(self.CVI, self.CVG), 33.44)

    def test_total_variation_is_the_two_in_quadrature(self):
        """CVt = sqrt(CVa^2 + CVi^2): sqrt(16 + 9) = 5."""
        self.assertEqual(self.qc.get_cvt(3.0, 4.0), 5.0)


class TestTheVerdict(QCTestCase):
    """What the series does, against what the analyte allows."""

    def test_observed_total_error_is_bias_plus_k_times_cv(self):
        """|2| + 1.65 x 4 = 8.6."""
        self.assertEqual(self.qc.get_te(100.0, 102.0, 4.0), 8.6)

    def test_a_method_inside_its_goal_is_green(self):
        observed, colour = self.qc.get_tea_tes_comparison(101.0, 100.0,
                                                          20.9, 45.6, 1.0, 3.0)
        self.assertEqual(colour, "green")

    def test_a_method_past_its_goal_is_red(self):
        observed, colour = self.qc.get_tea_tes_comparison(120.0, 100.0,
                                                          20.9, 45.6, 1.0, 9.0)
        self.assertEqual(colour, "red")

    def test_sigma_counts_how_many_cvs_fit_in_what_is_left(self):
        """(TEa - |bias|) / CV, with the bias taken out first."""
        series = [100.0, 102.0, 98.0, 101.0, 99.0]
        sigma = self.qc.get_sigma(20.9, 45.6, 100.0, series)
        self.assertEqual(sigma, 18.85)

    def test_a_series_with_no_spread_has_no_sigma(self):
        """Dividing by a CV of zero is not a verdict."""
        self.assertEqual(self.qc.get_sigma(20.9, 45.6, 100.0, [100.0]), 0.0)


class TestTheUncertainty(QCTestCase):
    """ISO/TS 20914: imprecision and bias, combined and expanded."""

    def test_the_bias_goes_in_divided_by_root_three(self):
        """sqrt(4^2 + (3/sqrt 3)^2) = sqrt(16 + 3) = 4.36, times 1.65."""
        self.assertEqual(self.qc.get_uncertainty(4.0, 3.0), 7.2)

    def test_the_sign_of_the_bias_does_not_matter(self):
        """It is a distance either way."""
        self.assertEqual(self.qc.get_uncertainty(4.0, -3.0),
                         self.qc.get_uncertainty(4.0, 3.0))

    def test_the_coverage_factor_can_be_given(self):
        """k = 2 rather than the setting."""
        self.assertEqual(self.qc.get_uncertainty(4.0, 3.0, k=2.0), 8.7)


if __name__ == "__main__":
    unittest.main()
