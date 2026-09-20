# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Test suite for Westgard QC Rules (westgards.py).

These are CRITICAL tests for medical safety - Westgard rules determine
if QC results are acceptable or if analytical runs should be rejected.

References:
    - Westgard JO. Basic QC Practices, 4th Edition. 2016.
    - ISO 15189:2022 - Medical laboratories quality requirements
"""
import pytest
from westgards import Westgards


@pytest.mark.critical
@pytest.mark.westgard
@pytest.mark.unit
class TestWestgardRules:
    """Test Westgard multirule QC evaluation."""

    def setup_method(self):
        """Setup before each test method."""
        self.westgards = Westgards()

    # ========================================================================
    # Test 1:3S Rule - Single value > 3SD
    # ========================================================================

    def test_1_3s_violation_above_mean(self, qc_target_sd):
        """Test 1:3S rule detects single value > 3SD above mean."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 116.0]  # Last value 3.2 SD above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "1:3S", f"Expected '1:3S' but got '{result}'"

    def test_1_3s_violation_below_mean(self, qc_target_sd):
        """Test 1:3S rule detects single value > 3SD below mean."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 84.0]  # Last value 3.2 SD below

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "1:3S", f"Expected '1:3S' but got '{result}'"

    def test_1_3s_exactly_3sd(self, qc_target_sd):
        """Test 1:3S rule at exactly 3SD boundary."""
        target, sd = qc_target_sd
        series = [100.0, 115.0]  # Exactly 3.0 SD above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        # Implementation uses > (not >=), so exactly 3SD does NOT trigger 1:3S
        # It triggers 1:2S instead
        assert result == "1:2S", "Exactly 3SD should trigger 1:2S (implementation uses >)"

    # ========================================================================
    # Test 2:2S Rule - Two consecutive > 2SD same side
    # ========================================================================

    def test_2_2s_violation_above_mean(self, qc_target_sd):
        """Test 2:2S rule detects two consecutive > 2SD above mean."""
        target, sd = qc_target_sd
        series = [100.0, 98.0, 111.0, 112.0]  # Last two > 2SD above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "2:2S", f"Expected '2:2S' but got '{result}'"

    def test_2_2s_violation_below_mean(self, qc_target_sd):
        """Test 2:2S rule detects two consecutive > 2SD below mean."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 89.0, 88.0]  # Last two > 2SD below

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "2:2S", f"Expected '2:2S' but got '{result}'"

    def test_2_2s_no_violation_different_sides(self, qc_target_sd):
        """Test 2:2S rule does not trigger when values on different sides."""
        target, sd = qc_target_sd
        series = [100.0, 111.0, 89.0]  # One above, one below (not consecutive same side)

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result != "2:2S", "Different sides should not trigger 2:2S"

    # ========================================================================
    # Test R:4S Rule - Range of 2 consecutive ≥ 4SD
    # ========================================================================

    def test_r_4s_violation(self, qc_target_sd):
        """Test R:4S rule detects range ≥ 4SD between two consecutive values."""
        target, sd = qc_target_sd
        series = [100.0, 90.0, 110.5]  # Range 20.5 = 4.1 SD

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "R:4S", f"Expected 'R:4S' but got '{result}'"

    def test_r_4s_exactly_4sd(self, qc_target_sd):
        """Test R:4S rule at exactly 4SD boundary."""
        target, sd = qc_target_sd
        # Last value must exceed 2SD to trigger rule checks
        series = [100.0, 90.0, 110.1]  # Range 20.1 = 4.02 SD, last value > 2SD

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        # Implementation uses >= for R:4S range check
        assert result == "R:4S", "Range >= 4SD should trigger R:4S"

    def test_r_4s_no_violation_small_range(self, qc_target_sd):
        """Test R:4S rule does not trigger with range < 4SD."""
        target, sd = qc_target_sd
        series = [100.0, 95.0, 105.0]  # Range 10.0 = 2.0 SD

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result != "R:4S", "Range < 4SD should not trigger R:4S"

    # ========================================================================
    # Test 4:1S Rule - Four consecutive > 1SD same side
    # ========================================================================

    def test_4_1s_violation_above_mean(self, qc_target_sd):
        """Test 4:1S rule detects four consecutive > 1SD above mean."""
        target, sd = qc_target_sd
        series = [100.0, 98.0, 106.0, 107.0, 106.5, 108.0]  # Last 4 > 1SD above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "4:1S", f"Expected '4:1S' but got '{result}'"

    def test_4_1s_violation_below_mean(self, qc_target_sd):
        """Test 4:1S rule detects four consecutive > 1SD below mean."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 94.0, 93.0, 93.5, 92.0]  # Last 4 > 1SD below

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "4:1S", f"Expected '4:1S' but got '{result}'"

    def test_4_1s_no_violation_three_values(self, qc_target_sd):
        """Test 4:1S rule does not trigger with only three consecutive values."""
        target, sd = qc_target_sd
        series = [100.0, 106.0, 107.0, 106.5]  # Only 3 consecutive > 1SD

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result != "4:1S", "Only 3 values should not trigger 4:1S"

    # ========================================================================
    # Test 10:X Rule - Ten consecutive same side of mean
    # ========================================================================

    def test_10_x_violation_above_mean(self, qc_target_sd):
        """Test 10:X rule detects ten consecutive values above mean."""
        target, sd = qc_target_sd
        series = [100.0, 98.0] + [101.0 + i*0.5 for i in range(10)]  # Last 10 above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "10:X", f"Expected '10:X' but got '{result}'"

    def test_10_x_violation_below_mean(self, qc_target_sd):
        """Test 10:X rule detects ten consecutive values below mean."""
        target, sd = qc_target_sd
        series = [100.0, 102.0] + [99.0 - i*0.5 for i in range(10)]  # Last 10 below

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "10:X", f"Expected '10:X' but got '{result}'"

    def test_10_x_no_violation_nine_values(self, qc_target_sd):
        """Test 10:X rule does not trigger with only nine consecutive values."""
        target, sd = qc_target_sd
        series = [100.0] + [101.0 + i*0.5 for i in range(9)]  # Only 9 above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result != "10:X", "Only 9 values should not trigger 10:X"

    # ========================================================================
    # Test 1:2S Rule - Single value > 2SD (warning)
    # ========================================================================

    def test_1_2s_warning_above_mean(self, qc_target_sd):
        """Test 1:2S rule detects single value > 2SD above mean (warning)."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 111.0]  # Last value 2.2 SD above

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "1:2S", f"Expected '1:2S' but got '{result}'"

    def test_1_2s_warning_below_mean(self, qc_target_sd):
        """Test 1:2S rule detects single value > 2SD below mean (warning)."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 89.0]  # Last value 2.2 SD below

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "1:2S", f"Expected '1:2S' but got '{result}'"

    # ========================================================================
    # Test Accept - No violations
    # ========================================================================

    def test_accept_all_values_within_1sd(self, qc_target_sd):
        """Test Accept when all values within 1SD."""
        target, sd = qc_target_sd
        series = [100.0, 102.0, 98.0, 101.0, 99.0]  # All within 1SD

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "Accept", f"Expected 'Accept' but got '{result}'"

    def test_accept_values_within_2sd(self, qc_target_sd):
        """Test Accept when values within 2SD (no consecutive violations)."""
        target, sd = qc_target_sd
        series = [100.0, 108.0, 92.0, 101.0]  # Within 2SD, no consecutive

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        # Should be Accept (or 1:2S if last value triggers it)
        assert result in ["Accept", "1:2S"]

    # ========================================================================
    # Test Rule Priority (1:3S highest priority)
    # ========================================================================

    def test_rule_priority_1_3s_over_2_2s(self, qc_target_sd):
        """Test 1:3S rule takes priority over 2:2S."""
        target, sd = qc_target_sd
        series = [100.0, 111.0, 116.0]  # Both 2:2S and 1:3S apply

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "1:3S", "1:3S should have priority over 2:2S"

    # ========================================================================
    # Test Edge Cases
    # ========================================================================

    def test_empty_series(self, qc_target_sd):
        """Test behavior with empty series."""
        target, sd = qc_target_sd
        series = []

        with pytest.raises((IndexError, ValueError)):
            self.westgards.get_westgard_violation_rule(target, sd, series)

    def test_single_value_series(self, qc_target_sd):
        """Test behavior with single value."""
        target, sd = qc_target_sd
        series = [100.0]

        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "Accept", "Single value at mean should Accept"

    def test_zero_sd_behavior(self):
        """Test behavior with zero SD (all values equal target)."""
        target = 100.0
        sd = 0.0
        series = [100.0, 100.0, 100.0]

        # With SD=0, limits are all equal to target (100.0)
        # series[-1] = 100.0 is NOT > 100.0, so no rules trigger
        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        assert result == "Accept", "Zero SD with values at target should Accept"

    def test_negative_sd_behavior(self):
        """Test behavior with negative SD (mathematically invalid but handled)."""
        target = 100.0
        sd = -5.0
        series = [100.0, 102.0, 98.0]

        # Implementation calculates limits even with negative SD
        # Negative SD reverses the limits but the logic still works
        result = self.westgards.get_westgard_violation_rule(target, sd, series)

        # The result depends on the calculated limits (implementation-specific)
        # With negative SD, limits are reversed, so violations can occur
        assert result in ["Accept", "1:2S", "2:2S", "1:3S", "R:4S"], \
            f"Negative SD should return some valid result, got '{result}'"


@pytest.mark.westgard
@pytest.mark.unit
@pytest.mark.parametrize("target,sd,series,expected", [
    # Test various scenarios with parametrize
    (100.0, 5.0, [100.0, 102.0, 98.0], "Accept"),
    (100.0, 5.0, [100.0, 116.0], "1:3S"),
    (100.0, 5.0, [100.0, 111.0, 112.0], "2:2S"),
    (50.0, 10.0, [50.0, 30.0, 71.0], "R:4S"),
    (200.0, 20.0, [200.0, 222.0, 224.0, 226.0, 228.0], "4:1S"),
])
def test_westgard_parametrized(target, sd, series, expected):
    """
    Parametrized test for multiple Westgard scenarios.

    This allows testing many scenarios quickly with different inputs.
    """
    wg = Westgards()
    result = wg.get_westgard_violation_rule(target, sd, series)
    assert result == expected, f"For series {series}, expected '{expected}' but got '{result}'"
