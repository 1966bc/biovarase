#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Westgard Quality Control Rules Module for Biovarase.

Implements Westgard multirule algorithms for statistical QC monitoring
per ISO 15189 requirements. Detects random errors, systematic errors,
and trending in laboratory quality control data.

References:
    - Westgard JO. Basic QC Practices, 4th Edition. 2016.
    - ISO 15189:2022 - Medical laboratories - Requirements for quality and competence
"""
from typing import Dict, List, Optional, Tuple


# Westgard rule window sizes (number of consecutive measurements)
WESTGARD_2_2S_WINDOW = 2   # 2:2s rule - 2 consecutive values
WESTGARD_R_4S_WINDOW = 2   # R:4s rule - range of 2 values
WESTGARD_4_1S_WINDOW = 4   # 4:1s rule - 4 consecutive values
WESTGARD_10_X_WINDOW = 10  # 10:x rule - 10 consecutive values


class Westgards:
    """
    Westgard multirule QC evaluation mixin.

    Evaluates QC results against standard Westgard rules to determine
    if analytical runs are in control or should be rejected.

    **Architecture Note** (✅ Refactored 2025-11-30):
        This mixin now implements pure functions per PROJECT_RULES §7.4 and §10.1.

        **Implementation**: Stateless - all rule methods accept parameters
        - get_westgard_violation_rule() uses local variables only
        - _calculate_control_limits() returns dict without setting instance state
        - All get_rule_XXX() methods accept (series, limits) or (series, target, limits)

        **Benefits**:
        - ✅ Pure functions - no hidden state
        - ✅ Testable independently
        - ✅ Thread-safe
        - ✅ Complies with PROJECT_RULES mixin architecture guidelines
    """

    def __str__(self) -> str:
        return "class: {0}\nMRO: {1}".format(
            self.__class__.__name__,
            [x.__name__ for x in Westgards.__mro__],
        )

    def get_westgard_violation_rule(
        self,
        target: float,
        sd: float,
        series: List[float],
        selected_batch: Optional[int] = None,
        selected_test: Optional[int] = None,
    ) -> str:
        """
        Evaluate QC series against Westgard multirule algorithm.

        Args:
            target: Mean/target value for the QC batch
            sd: Standard deviation for the QC batch
            series: List of QC results (most recent last: [..., oldest, newest])
            selected_batch: Optional batch_id for logging (reserved for future use)
            selected_test: Optional test_id for logging (reserved for future use)

        Returns:
            String indicating violated rule or control status:
            - "1:3S" - Single value > 3SD (reject immediately)
            - "2:2S" - Two consecutive > 2SD same side (systematic error)
            - "R:4S" - Range of 2 values ≥ 4SD (random error)
            - "4:1S" - Four consecutive > 1SD same side (trending)
            - "10:X" - Ten consecutive on same side of mean (persistent bias)
            - "1:2S" - Single value > 2SD (warning, continue testing)
            - "Accept" - All rules passed (in control)

        Raises:
            ValueError: If series is empty or has insufficient data for evaluation

        Example:
            >>> wg = Westgards()
            >>> target = 100.0
            >>> sd = 5.0
            >>> series = [95, 98, 101, 103, 116]  # Last value > 3SD
            >>> wg.get_westgard_violation_rule(target, sd, series)
            '1:3S'
        """
        # Validate input
        if not series:
            raise ValueError("Series cannot be empty")

        if len(series) < 1:
            raise ValueError("Series must contain at least 1 measurement")

        # Calculate control limits (local variable - stateless approach)
        limits = self._calculate_control_limits(target, sd)

        # Apply Westgard multirule algorithm (pass parameters - pure functions)
        if self.get_rule_12S(series, limits):
            # Value exceeds ±2SD → Check rejection rules in priority order
            if self.get_rule_13S(series, limits):
                return "1:3S"  # Most severe - immediate rejection
            elif self.get_rule_22S(series, limits):
                return "2:2S"  # Systematic error
            elif self.get_rule_R4S(series, limits):
                return "R:4S"  # Random error
            elif self.get_rule_41S(series, target, limits):
                return "4:1S"  # Trending
            elif self.get_rule_10X(series, target):
                return "10:X"  # Persistent bias
            else:
                return "1:2S"  # Warning only
        else:
            # Value within ±2SD → Check long-term trends
            if self.get_rule_41S(series, target, limits):
                return "4:1S"  # Trending
            elif self.get_rule_10X(series, target):
                return "10:X"  # Persistent bias
            else:
                return "Accept"  # In control

    def _calculate_control_limits(self, target: float, sd: float) -> Dict[str, float]:
        """
        Calculate control limit boundaries for Westgard rules.

        Args:
            target: Mean/target value
            sd: Standard deviation

        Returns:
            Dictionary containing control limits:
                - sd1, sd2, sd3: Upper control limits (+1SD, +2SD, +3SD)
                - sd_1, sd_2, sd_3: Lower control limits (-1SD, -2SD, -3SD)
                - sd4: Range limit (4SD for R:4s rule)

        Note:
            Pure function - does not modify instance state.
            All rule methods now accept limits as parameters.
        """
        return {
            'sd1': target + sd,
            'sd2': target + (2 * sd),
            'sd3': target + (3 * sd),
            'sd_1': target - sd,
            'sd_2': target - (2 * sd),
            'sd_3': target - (3 * sd),
            'sd4': 4 * sd
        }

    # ========================================================================
    # Individual Westgard Rules
    # ========================================================================

    def get_rule_12S(self, series: List[float], limits: Dict[str, float]) -> bool:
        """
        1:2s Warning Rule (Screening).

        Check if the most recent control measurement exceeds ±2SD.
        This is the screening rule - if violated, additional rules are checked.

        Args:
            series: List of QC measurements (most recent last)
            limits: Dictionary of control limits from _calculate_control_limits()

        Returns:
            True if measurement exceeds ±2SD, False otherwise

        Statistical characteristics:
            - False rejection rate: ~5% (normal distribution)
            - Purpose: Trigger evaluation of additional rules
            - Action: If True, check 1:3s, 2:2s, R:4s, 4:1s, 10:x
        """
        return series[-1] > limits['sd2'] or series[-1] < limits['sd_2']

    def get_rule_13S(self, series: List[float], limits: Dict[str, float]) -> bool:
        """
        1:3s Rejection Rule.

        One control measurement exceeds ±3SD.
        Indicates unacceptable random error.

        Args:
            series: List of QC measurements (most recent last)
            limits: Dictionary of control limits from _calculate_control_limits()

        Returns:
            True if measurement exceeds ±3SD, False otherwise

        Statistical characteristics:
            - False rejection rate: 0.3%
            - Detects: Random error, outliers
            - Action: Reject run, investigate immediately
        """
        return series[-1] > limits['sd3'] or series[-1] < limits['sd_3']

    def get_rule_22S(self, series: List[float], limits: Dict[str, float]) -> bool:
        """
        2:2s Rejection Rule (Systematic Error).

        Two consecutive measurements exceed the same ±2SD limit
        (both high or both low).

        Args:
            series: List of QC measurements (most recent last)
            limits: Dictionary of control limits from _calculate_control_limits()

        Returns:
            True if rule violated, False otherwise

        Statistical characteristics:
            - False rejection rate: ~1%
            - Detects: Systematic error, accuracy shift, calibration drift
            - Action: Reject run, recalibrate

        Requires:
            At least 2 measurements in series
        """
        if len(series) < WESTGARD_2_2S_WINDOW:
            return False

        last_two_values = series[-WESTGARD_2_2S_WINDOW:]
        both_high = all(i >= limits['sd2'] for i in last_two_values)
        both_low = all(i <= limits['sd_2'] for i in last_two_values)
        return both_high or both_low

    def get_rule_R4S(self, series: List[float], limits: Dict[str, float]) -> bool:
        """
        R:4s Rejection Rule (Random Error).

        Range of two consecutive measurements ≥ 4SD.
        One measurement exceeds +2SD and another exceeds -2SD.

        Args:
            series: List of QC measurements (most recent last)
            limits: Dictionary of control limits from _calculate_control_limits()

        Returns:
            True if rule violated, False otherwise

        Statistical characteristics:
            - False rejection rate: ~1%
            - Detects: Excessive random error, poor precision
            - Action: Reject run, check instrument precision

        Important:
            This rule should only be interpreted within-run, not between-run.

        Requires:
            At least 2 measurements in series
        """
        if len(series) < WESTGARD_R_4S_WINDOW:
            return False

        last_two_values = series[-WESTGARD_R_4S_WINDOW:]
        value_range = max(last_two_values) - min(last_two_values)
        return value_range >= limits['sd4']

    def get_rule_41S(self, series: List[float], target: float, limits: Dict[str, float]) -> bool:
        """
        4:1s Rejection Rule (Trending).

        Four consecutive measurements exceed the same ±1SD limit
        (all high or all low).

        Args:
            series: List of QC measurements (most recent last)
            target: Mean/target value
            limits: Dictionary of control limits from _calculate_control_limits()

        Returns:
            True if rule violated, False otherwise

        Statistical characteristics:
            - False rejection rate: ~1%
            - Detects: Systematic trend, reagent degradation
            - Action: Reject run, investigate trend cause

        Requires:
            At least 4 measurements in series
        """
        if len(series) < WESTGARD_4_1S_WINDOW:
            return False

        last_four_values = series[-WESTGARD_4_1S_WINDOW:]
        all_high = all(i > limits['sd1'] for i in last_four_values)
        all_low = all(i < limits['sd_1'] for i in last_four_values)
        return all_high or all_low

    def get_rule_10X(self, series: List[float], target: float) -> bool:
        """
        10:x Rejection Rule (Persistent Bias).

        Ten consecutive measurements fall on the same side of the mean
        (all above or all below target).

        Args:
            series: List of QC measurements (most recent last)
            target: Mean/target value

        Returns:
            True if rule violated, False otherwise

        Statistical characteristics:
            - False rejection rate: 0.1%
            - Detects: Persistent systematic error, calibration offset
            - Action: Reject run, recalibrate immediately

        Requires:
            At least 10 measurements in series
        """
        if len(series) < WESTGARD_10_X_WINDOW:
            return False

        last_ten_values = series[-WESTGARD_10_X_WINDOW:]
        all_high = all(i > target for i in last_ten_values)
        all_low = all(i < target for i in last_ten_values)
        return all_high or all_low


def main():
    """Test cases for Westgard rules implementation."""
    wg = Westgards()
    print(wg)
    print()

    target = 100.0
    sd = 10.0

    # Test 1: 1:2S warning (last value = 121, which is > mean + 2SD)
    print("Test 1: 1:2S Warning Rule")
    series = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 121]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: 1:2S (121 > 120 = mean + 2SD)")
    print()

    # Test 2: 10:X persistent bias (10 consecutive values > mean, but not triggering 4:1S)
    print("Test 2: 10:X Persistent Bias")
    series = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 109]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: 10:X (last 10 values all > 100, but < 110 to avoid 4:1S)")
    print()

    # Test 3: 1:3S rejection (last value = 131, which is > mean + 3SD)
    print("Test 3: 1:3S Rejection Rule")
    series = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 131]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: 1:3S (131 > 130 = mean + 3SD)")
    print()

    # Test 4: 2:2S systematic error (last 2 values both > mean + 2SD)
    print("Test 4: 2:2S Systematic Error")
    series = [100, 100, 100, 100, 100, 100, 100, 100, 121, 122]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: 2:2S (121 and 122 both > 120)")
    print()

    # Test 5: R:4S random error (range ≥ 4SD)
    print("Test 5: R:4S Random Error")
    series = [100, 100, 100, 100, 100, 100, 100, 100, 79, 121]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: R:4S (range = 121 - 79 = 42 ≥ 40)")
    print()

    # Test 6: 4:1S trending (4 consecutive values > mean + 1SD)
    print("Test 6: 4:1S Trending")
    series = [100, 100, 100, 100, 100, 100, 111, 112, 113, 114]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: 4:1S (last 4 values all > 110)")
    print()

    # Test 7: Accept (in control)
    print("Test 7: Accept (In Control)")
    series = [100, 98, 102, 99, 101, 100, 103, 97, 102, 99]
    rule = wg.get_westgard_violation_rule(target, sd, series)
    print(f"  Series: {series}")
    print(f"  Result: {rule}")
    print(f"  Expected: Accept (all values within ±2SD)")
    print()

    input('Press Enter to exit...')


if __name__ == "__main__":
    main()
