# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Test suite for QC Statistical Calculations (qc.py).

Tests statistical methods used for quality control metrics:
- Mean, SD, CV%
- Bias
- Total Error
- Measurement Uncertainty

References:
    - ISO 15189:2022 - Medical laboratories quality requirements
    - ISO/TS 20914:2019 - Measurement uncertainty guidance
"""
import pytest
import math
from qc import QC


@pytest.mark.critical
@pytest.mark.qc
@pytest.mark.unit
class TestQCStatistics:
    """Test QC statistical calculation methods."""

    def setup_method(self):
        """Setup before each test method."""
        self.qc = QC()
        # Mock dependencies that QC expects from Engine
        self.qc.get_file = lambda x: x  # Return filename as-is for testing
        self.qc.on_log = lambda *args: None  # Silent logging for testing
        self.qc.get_zscore = lambda: 1.96  # Mock zscore to 1.96 (95% CI)
        self.qc.get_ddof = lambda: 1  # Mock ddof to 1 (sample SD)

    # ========================================================================
    # Test Mean Calculation
    # ========================================================================

    def test_calculate_mean_simple_series(self, stats_simple_series, stats_known_values):
        """Test mean calculation with known values."""
        series = stats_simple_series
        expected_mean = stats_known_values["mean"]

        result = self.qc.get_mean(series)

        # get_mean() rounds to 2 decimals
        assert result == pytest.approx(expected_mean, abs=0.01), \
            f"Expected mean {expected_mean}, got {result}"

    def test_calculate_mean_single_value(self):
        """Test mean with single value."""
        series = [42.0]

        result = self.qc.get_mean(series)

        assert result == 42.0, "Mean of single value should be the value itself"

    def test_calculate_mean_negative_values(self):
        """Test mean with negative values."""
        series = [-10.0, -20.0, -30.0]

        result = self.qc.get_mean(series)

        assert result == pytest.approx(-20.0), "Mean should handle negative values"

    def test_calculate_mean_empty_series_returns_zero(self):
        """Test mean with empty series returns 0.0."""
        series = []

        result = self.qc.get_mean(series)

        assert result == 0.0, "Empty series should return 0.0"

    # ========================================================================
    # Test Standard Deviation Calculation
    # ========================================================================

    def test_calculate_sd_sample_ddof_1(self, stats_simple_series):
        """Test sample SD (ddof=1) with known values."""
        series = stats_simple_series
        # Expected: 15.811388... but get_sd() rounds to 2 decimals

        result = self.qc.get_sd(series, ddof=1)

        assert result == pytest.approx(15.81, abs=0.01), \
            f"Expected SD (ddof=1) ~15.81, got {result}"

    def test_calculate_sd_population_ddof_0(self, stats_simple_series):
        """Test population SD (ddof=0) with known values."""
        series = stats_simple_series
        # Expected: 14.142135... but get_sd() rounds to 2 decimals

        result = self.qc.get_sd(series, ddof=0)

        assert result == pytest.approx(14.14, abs=0.01), \
            f"Expected SD (ddof=0) ~14.14, got {result}"

    def test_calculate_sd_zero_variance(self):
        """Test SD with zero variance (all values identical)."""
        series = [100.0, 100.0, 100.0, 100.0]

        result = self.qc.get_sd(series, ddof=1)

        assert result == 0.0, "SD of constant series should be 0"

    def test_calculate_sd_single_value_ddof_1_returns_zero(self):
        """Test SD with single value and ddof=1 returns 0.0."""
        series = [42.0]

        result = self.qc.get_sd(series, ddof=1)

        # statistics.stdev() raises StatisticsError for single value
        # but QC.get_sd() catches it and returns 0.0
        assert result == 0.0, "Single value with ddof=1 should return 0.0"

    def test_calculate_sd_empty_series_returns_zero(self):
        """Test SD with empty series returns 0.0."""
        series = []

        result = self.qc.get_sd(series, ddof=1)

        assert result == 0.0, "Empty series should return 0.0"

    # ========================================================================
    # Test Coefficient of Variation (CV%) Calculation
    # ========================================================================

    def test_calculate_cv_sample(self, stats_simple_series):
        """Test CV% calculation with sample SD."""
        series = stats_simple_series

        result = self.qc.get_cv(series, ddof=1)

        # CV% = (SD / Mean) * 100
        # For [10, 20, 30, 40, 50]: mean=30, sd_sample~15.81, cv~52.7%
        expected_cv = pytest.approx(52.7, rel=0.01)  # 1% tolerance
        assert result == expected_cv, f"Expected CV ~{expected_cv}, got {result}"

    def test_calculate_cv_zero_mean_returns_zero(self):
        """Test CV% with zero mean returns 0.0 (no division by zero exception)."""
        series = [-10.0, 0.0, 10.0]  # Mean = 0

        result = self.qc.get_cv(series, ddof=1)

        # get_cv() checks for zero mean and returns 0.0
        assert result == 0.0, "CV with zero mean should return 0.0"

    def test_calculate_cv_single_value_returns_zero(self):
        """Test CV% with single value returns 0.0."""
        series = [42.0]

        result = self.qc.get_cv(series, ddof=1)

        # SD is 0 for single value, so CV should be 0
        assert result == 0.0, "CV for single value should return 0.0"

    # ========================================================================
    # Test Bias Calculation
    # ========================================================================

    def test_calculate_bias_above_target(self):
        """Test bias when results are above target."""
        avg = 106.5  # Mean value
        target = 100.0

        result = self.qc.get_bias(avg, target)

        # Bias = ((106.5 - 100) / 100) * 100 = 6.5%
        expected_bias = pytest.approx(6.5, abs=0.01)
        assert result == expected_bias, f"Expected bias {expected_bias}%, got {result}%"

    def test_calculate_bias_below_target(self):
        """Test bias when results are below target."""
        avg = 93.5  # Mean value
        target = 100.0

        result = self.qc.get_bias(avg, target)

        # Bias = ((93.5 - 100) / 100) * 100 = -6.5%
        expected_bias = pytest.approx(-6.5, abs=0.01)
        assert result == expected_bias, f"Expected bias {expected_bias}%, got {result}%"

    def test_calculate_bias_zero_when_equal_target(self):
        """Test bias is zero when mean equals target."""
        avg = 100.0
        target = 100.0

        result = self.qc.get_bias(avg, target)

        assert result == pytest.approx(0.0, abs=0.01), "Bias should be 0 when avg equals target"

    def test_calculate_bias_zero_target_returns_zero(self):
        """Test bias with zero target returns 0.0 (no division by zero exception)."""
        avg = 10.0
        target = 0.0

        result = self.qc.get_bias(avg, target)

        # get_bias() checks for zero target and returns 0.0
        assert result == 0.0, "Bias with zero target should return 0.0"

    def test_calculate_bias_with_list_as_avg_returns_zero(self):
        """Test bias with list as avg (invalid input) returns 0.0."""
        avg = [10.0, 20.0, 30.0]  # Invalid type
        target = 100.0

        result = self.qc.get_bias(avg, target)

        # get_bias() catches TypeError and returns 0.0
        assert result == 0.0, "Invalid input type should return 0.0"

    # ========================================================================
    # Test Total Error Calculation (get_te)
    # ========================================================================

    def test_calculate_total_error(self):
        """Test total error calculation with get_te()."""
        target = 100.0
        avg = 105.0  # 5% bias
        cv = 3.0  # 3% CV

        result = self.qc.get_te(target, avg, cv)

        # TE = |Bias| + (zscore × CV)
        # Bias = 5%, zscore = 1.96 (default), TE = 5 + (1.96 × 3) = 10.88%
        expected_te = pytest.approx(10.88, abs=0.1)
        assert result == expected_te, f"Expected TE ~{expected_te}%, got {result}%"

    def test_calculate_total_error_negative_bias(self):
        """Test total error with negative bias (absolute value taken)."""
        target = 100.0
        avg = 95.0  # -5% bias
        cv = 3.0

        result = self.qc.get_te(target, avg, cv)

        # TE = |-5| + (1.96 × 3) = 10.88%
        expected_te = pytest.approx(10.88, abs=0.1)
        assert result == expected_te, f"Expected TE ~{expected_te}%, got {result}%"

    def test_calculate_total_error_zero_bias(self):
        """Test total error with zero bias."""
        target = 100.0
        avg = 100.0  # 0% bias
        cv = 3.0

        result = self.qc.get_te(target, avg, cv)

        # TE = 0 + (1.96 × 3) = 5.88%
        expected_te = pytest.approx(5.88, abs=0.1)
        assert result == expected_te, f"Expected TE ~{expected_te}%, got {result}%"

    # ========================================================================
    # Test Measurement Uncertainty Calculation (ISO/TS 20914)
    # ========================================================================

    def test_calculate_uncertainty(self):
        """Test measurement uncertainty calculation."""
        cva = 2.0  # Analytical CV 2%
        bias = 1.5  # Bias 1.5%
        k = 1.96  # 95% confidence interval

        result = self.qc.get_uncertainty(cva, bias, k)

        # u_repeatability = CVa = 2.0
        # u_bias = |bias| / √3 = 1.5 / 1.732 ≈ 0.866
        # u_combined = √(2.0² + 0.866²) ≈ 2.179
        # U = k × u_combined = 1.96 × 2.179 ≈ 4.3%
        expected_u = pytest.approx(4.3, abs=0.2)
        assert result == expected_u, f"Expected uncertainty ~{expected_u}%, got {result}%"

    def test_calculate_uncertainty_zero_bias(self):
        """Test uncertainty with zero bias."""
        cva = 2.0
        bias = 0.0
        k = 1.96

        result = self.qc.get_uncertainty(cva, bias, k)

        # u_combined = √(2.0² + 0²) = 2.0
        # U = 1.96 × 2.0 = 3.92% ≈ 3.9% (rounded to 1 decimal)
        expected_u = pytest.approx(3.9, abs=0.1)
        assert result == expected_u, f"Expected uncertainty ~{expected_u}%, got {result}%"

    def test_calculate_uncertainty_none_inputs_returns_none(self):
        """Test uncertainty with None inputs returns None."""
        result = self.qc.get_uncertainty(None, 1.5, 1.96)
        assert result is None, "None cva should return None"

        result = self.qc.get_uncertainty(2.0, None, 1.96)
        assert result is None, "None bias should return None"

    # ========================================================================
    # Test Sigma Metrics
    # ========================================================================

    def test_calculate_sigma_metric(self):
        """Test sigma metric calculation with get_sigma()."""
        cvw = 5.0  # Within-subject CV 5%
        cvb = 10.0  # Between-subject CV 10%
        target = 100.0
        series = [98.0, 99.0, 100.0, 101.0, 102.0]

        result = self.qc.get_sigma(cvw, cvb, target, series)

        # This is a complex calculation involving TEa, bias, CV
        # We just check that it returns a reasonable positive value
        assert result > 0, "Sigma metric should be positive"
        assert result < 20, "Sigma metric should be reasonable (< 20)"

    def test_calculate_sigma_zero_cv_returns_zero(self):
        """Test sigma metric with zero CV returns 0.0."""
        cvw = 5.0
        cvb = 10.0
        target = 100.0
        series = [100.0, 100.0, 100.0]  # Zero variance → CV = 0

        result = self.qc.get_sigma(cvw, cvb, target, series)

        # get_sigma() checks for zero CV and returns 0.0
        assert result == 0.0, "Sigma with zero CV should return 0.0"

    # ========================================================================
    # Test Range Calculation
    # ========================================================================

    def test_calculate_range(self):
        """Test range calculation."""
        series = [10.0, 15.0, 20.0, 25.0, 30.0]

        result = self.qc.get_range(series)

        # Range = max - min = 30 - 10 = 20
        assert result == 20.0, f"Expected range 20.0, got {result}"

    def test_calculate_range_single_value(self):
        """Test range with single value."""
        series = [42.0]

        result = self.qc.get_range(series)

        # Range = 42 - 42 = 0
        assert result == 0.0, "Range of single value should be 0"

    def test_calculate_range_empty_series_returns_zero(self):
        """Test range with empty series returns 0.0."""
        series = []

        result = self.qc.get_range(series)

        assert result == 0.0, "Empty series should return 0.0"


@pytest.mark.qc
@pytest.mark.unit
@pytest.mark.parametrize("avg,target,expected_bias", [
    # Test various bias scenarios
    (100.0, 100.0, 0.0),  # No bias
    (110.0, 100.0, 10.0),  # 10% positive bias
    (90.0, 100.0, -10.0),  # 10% negative bias
    (105.0, 100.0, 5.0),  # 5% positive bias
])
def test_bias_parametrized(avg, target, expected_bias):
    """Parametrized test for bias calculation."""
    qc = QC()
    qc.get_file = lambda x: x
    qc.on_log = lambda *args: None
    qc.get_zscore = lambda: 1.96
    qc.get_ddof = lambda: 1

    result = qc.get_bias(avg, target)
    assert result == pytest.approx(expected_bias, abs=0.01), \
        f"For avg={avg} and target={target}, expected bias {expected_bias}%, got {result}%"


@pytest.mark.qc
@pytest.mark.unit
def test_qc_requires_mocked_dependencies():
    """Test that QC requires get_file() and on_log() from parent."""
    qc = QC()

    # Without mocking, these methods don't exist
    assert not hasattr(qc, 'get_file') or callable(getattr(qc, 'get_file', None)) is False
    assert not hasattr(qc, 'on_log') or callable(getattr(qc, 'on_log', None)) is False

    # After mocking, they should work
    qc.get_file = lambda x: x
    qc.on_log = lambda *args: None

    assert callable(qc.get_file)
    assert callable(qc.on_log)
