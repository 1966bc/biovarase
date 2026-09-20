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


class TestTheCorrelation(QCTestCase):
    """What the two levels of a control did on the same days."""

    def test_two_series_that_rise_together_are_one(self):
        """The same movement on both levels: r = 1."""
        self.assertEqual(self.qc.get_correlation([1.0, 2.0, 3.0, 4.0],
                                                 [10.0, 20.0, 30.0, 40.0]), 1.0)

    def test_one_that_rises_while_the_other_falls_is_minus_one(self):
        self.assertEqual(self.qc.get_correlation([1.0, 2.0, 3.0, 4.0],
                                                 [40.0, 30.0, 20.0, 10.0]), -1.0)

    def test_a_calibration_drifting_on_both_levels_shows_it(self):
        """Both levels walking up together, with a little noise on each."""
        low = [7.9, 8.0, 8.2, 8.3, 8.5, 8.6, 8.8]
        high = [17.8, 18.1, 18.4, 18.6, 19.0, 19.2, 19.5]
        self.assertGreater(self.qc.get_correlation(low, high), 0.975)

    def test_imprecision_does_not_correlate(self):
        """Each level scattered on its own: nothing to see along the diagonal."""
        low = [8.0, 8.4, 7.6, 8.3, 7.7, 8.2, 7.8]
        high = [18.2, 17.7, 18.1, 18.3, 17.6, 17.9, 18.4]
        self.assertLess(abs(self.qc.get_correlation(low, high)), 0.975)

    def test_a_level_that_never_moved_has_no_correlation(self):
        """No spread on one axis: the fraction has a zero under it."""
        self.assertEqual(self.qc.get_correlation([8.0, 8.0, 8.0],
                                                 [18.0, 18.2, 17.9]), 0.0)

    def test_one_pair_is_not_a_correlation(self):
        self.assertEqual(self.qc.get_correlation([8.0], [18.0]), 0.0)

    def test_series_of_different_lengths_are_not_pairs(self):
        with self.assertRaises(ValueError):
            self.qc.get_correlation([8.0, 8.1], [18.0])


class TestTheVerdict(QCTestCase):
    """What the series does, against what the analyte allows."""

    def test_observed_total_error_is_bias_plus_k_times_cv(self):
        """|2| + 1.65 x 4 = 8.6."""
        self.assertEqual(self.qc.get_te(100.0, 102.0, 4.0), 8.6)

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
