#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Control Module for Biovarase.

Implements statistical calculations and analytical performance metrics
for laboratory quality control per ISO 15189 requirements.

References:
    - ISO 15189:2022 - Medical laboratories - Requirements for quality and competence
    - ISO/TS 20914:2019 - Medical laboratories - Practical guidance for the estimation of measurement uncertainty
    - Westgard JO. Basic QC Practices, 4th Edition. 2016.
    - Fraser CG. Biological Variation: From Principles to Practice. AACC Press, 2001.
"""
import statistics
import math
import sys
import inspect
from typing import List, Optional, Tuple


class QC:
    """
    Quality Control statistical calculations mixin.

    Provides methods for calculating QC metrics including:
    - Descriptive statistics (mean, SD, CV, range)
    - Analytical performance (bias, total error, sigma metrics)
    - Measurement uncertainty (ISO/TS 20914 approach)
    - Biological variation-based quality goals

    **Required Parent Attributes** (provided by Engine):
        - get_file(filename: str) -> str:
            Returns absolute path to configuration file.
            Used to read 'ddof' and 'zscore' configuration files.

        - on_log(function, exc_value, exc_type, module, caller=None) -> None:
            Logs errors and exceptions to log file.
            Used for error handling and debugging.

    **Architecture Note**:
        This is a mixin class designed to be combined with Engine.
        It cannot function standalone due to dependencies on Engine methods.
        See PROJECT_RULES §7.4 for mixin architecture guidelines.

    **ISO/IEC Standards**:
        - ISO 15189:2022 - Medical laboratories quality requirements
        - ISO/TS 20914:2019 - Measurement uncertainty guidance
    """

    def __str__(self) -> str:
        return "class: {0}\nMRO: {1}".format(
            self.__class__.__name__, [x.__name__ for x in QC.__mro__]
        )

    def get_ddof(self) -> int:
        """
        Read Delta Degrees of Freedom from configuration.

        Returns:
            int: 1 for sample SD (n-1), 0 for population SD (n)

        Note:
            Defaults to 1 (sample standard deviation) if file cannot be read.
            Most QC applications use ddof=1 for unbiased estimation.
        """
        try:
            with open(self.get_file("ddof"), "r") as f:
                v = f.readline().strip()
                return int(v)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 1  # default: sample standard deviation

    def get_zscore(self) -> float:
        """
        Read z-score (coverage factor) from configuration.

        Returns:
            float: Z-score for confidence interval

        Common values:
            - 1.65 for 90% confidence interval (CLIA recommendation)
            - 1.96 for 95% confidence interval (common default)
            - 2.00 for ~95.4% confidence interval

        Note:
            Defaults to 1.96 (95% CI) if file cannot be read.
        """
        try:
            with open(self.get_file("zscore"), "r") as f:
                v = f.readline().strip()
                return float(v)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 1.96  # default: 95% confidence interval

    def get_sd(self, values: List[float], ddof: Optional[int] = None) -> float:
        """
        Calculate standard deviation.

        Args:
            values: List of numeric measurements
            ddof: Delta degrees of freedom (0=population, 1=sample)
                  If None, reads from configuration file

        Returns:
            Standard deviation rounded to 2 decimals, or 0.0 on error

        Formula:
            ddof=1: sqrt(Σ(x - x̄)² / (n-1))  [sample SD]
            ddof=0: sqrt(Σ(x - x̄)² / n)      [population SD]
        """
        try:
            if not values:
                return 0.0

            effective_ddof = self.get_ddof() if ddof is None else ddof

            if effective_ddof == 1:
                # Sample standard deviation (n-1)
                return round(statistics.stdev(values), 2)
            else:
                # Population standard deviation (n)
                return round(statistics.pstdev(values), 2)

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_cv(self, values: List[float], ddof: Optional[int] = None) -> float:
        """
        Calculate Coefficient of Variation (CV).

        Args:
            values: List of numeric measurements
            ddof: Delta degrees of freedom for SD calculation

        Returns:
            CV as percentage, rounded to 2 decimals, or 0.0 on error

        Formula:
            CV(%) = (SD / mean) × 100

        Note:
            Returns 0.0 if mean is zero to avoid division by zero.
        """
        sd = self.get_sd(values, ddof)
        mean = self.get_mean(values)

        if mean == 0:
            return 0.0
        return round((sd / mean) * 100, 2)

    def get_mean(self, values: List[float]) -> float:
        """
        Calculate arithmetic mean.

        Args:
            values: List of numeric measurements

        Returns:
            Mean rounded to 2 decimals, or 0.0 on error

        Formula:
            mean = Σx / n
        """
        try:
            if not values:
                return 0.0
            return round(statistics.mean(values), 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_range(self, values: List[float]) -> float:
        """
        Calculate range (peak-to-peak).

        Args:
            values: List of numeric measurements

        Returns:
            Range rounded to 2 decimals, or 0.0 on error

        Formula:
            Range = max(values) - min(values)
        """
        try:
            if not values:
                return 0.0
            return round(max(values) - min(values), 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_bias(self, avg: float, target: float) -> float:
        """
        Calculate relative bias (systematic error).

        Args:
            avg: Observed mean value
            target: Reference/target value

        Returns:
            Bias as percentage (SIGNED), rounded to 2 decimals, or 0.0 on error

        Formula:
            Bias(%) = [(avg - target) / target] × 100

        Note:
            Preserves sign: positive = high bias, negative = low bias.
            Returns 0.0 if target is zero (division by zero).

        Important:
            This method returns SIGNED bias. Previous version used abs()
            which lost information about direction of systematic error.
        """
        try:
            a = float(avg)
            t = float(target)
        except (TypeError, ValueError) as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

        if t == 0.0:
            # No meaningful relative bias can be computed.
            return 0.0

        try:
            return round(((a - t) / t) * 100.0, 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_cvt(self, cvw: float, cva: float) -> float:
        """
        Calculate total CV combining within-subject and analytical variation.

        Args:
            cvw: Within-subject biological variation (%)
            cva: Analytical variation (%)

        Returns:
            Total CV rounded to 2 decimals, or 0.0 on error

        Formula:
            CVt = √(CVa² + CVw²)
        """
        try:
            return round(math.sqrt(cva**2 + cvw**2), 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_allowable_bias(self, cvw: float, cvb: float) -> float:
        """
        Calculate allowable bias from biological variation.

        Args:
            cvw: Within-subject biological variation (%)
            cvb: Between-subject biological variation (%)

        Returns:
            Allowable bias (%) rounded to 2 decimals, or 0.0 on error

        Formula:
            Allowable Bias = 0.25 × √(CVw² + CVb²)

        Reference:
            Fraser CG. Biological Variation: From Principles to Practice.
            Desirable specification: Bias < 0.25 × √(CVw² + CVb²)
        """
        try:
            return abs(
                round(math.sqrt((math.pow(cvw, 2) + math.pow(cvb, 2))) * 0.25, 2)
            )
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_te(self, target: float, avg: float, cv: float) -> float:
        """
        Calculate observed Total Error.

        Args:
            target: Reference/target value
            avg: Observed mean value
            cv: Coefficient of variation (%)

        Returns:
            Total error (%) rounded to 2 decimals, or 0.0 on error

        Formula:
            TE = |Bias| + (z × CV)

        Note:
            Uses absolute value of bias because total error is unsigned.
            Z-score is read from configuration (typically 1.65 or 1.96).
        """
        bias = self.get_bias(avg, target)
        try:
            return round(abs(bias) + (self.get_zscore() * float(cv)), 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_tea(self, cvw: float, cvb: float) -> float:
        """
        Calculate Total Error Allowable from biological variation.

        Args:
            cvw: Within-subject biological variation (%)
            cvb: Between-subject biological variation (%)

        Returns:
            Allowable total error (%) rounded to 2 decimals, or 0.0 on error

        Formula:
            TEa = (z × Imprecision_allowable) + Bias_allowable
            where:
                Imprecision_allowable = 0.5 × CVw
                Bias_allowable = 0.25 × √(CVw² + CVb²)

        Reference:
            Fraser CG. Desirable specifications for total error.
        """
        try:
            return round(
                (self.get_zscore() * self.get_imp(cvw))
                + self.get_allowable_bias(cvw, cvb),
                2,
            )
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_sigma(self, cvw: float, cvb: float, target: float, series: List[float]) -> float:
        """
        Calculate Six Sigma quality metric.

        Args:
            cvw: Within-subject biological variation (%)
            cvb: Between-subject biological variation (%)
            target: Reference/target value
            series: QC measurements

        Returns:
            Sigma metric rounded to 2 decimals, or 0.0 on error

        Formula:
            σ = (TEa - |Bias|) / CV

        Interpretation:
            σ ≥ 6.0: World class quality
            σ ≥ 5.0: Excellent
            σ ≥ 4.0: Good
            σ ≥ 3.0: Acceptable
            σ < 3.0: Poor (unacceptable)

        Note:
            Returns 0.0 if CV is zero to avoid division by zero.
        """
        try:
            avg = self.get_mean(series)
            tea = self.get_tea(cvw, cvb)
            bias = self.get_bias(avg, target)
            cv = self.get_cv(series)

            if cv == 0:
                return 0.0

            sigma = (tea - abs(bias)) / cv
            return round(sigma, 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_tea_tes_comparison(
        self,
        avg: float,
        target: float,
        cvw: float,
        cvb: float,
        sd: float,
        cva: float
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Compare allowable vs observed total error.

        Args:
            avg: Observed mean value
            target: Reference/target value
            cvw: Within-subject biological variation (%)
            cvb: Between-subject biological variation (%)
            sd: Standard deviation
            cva: Analytical CV (%)

        Returns:
            Tuple of (TEobs, color):
                TEobs: Observed total error (%)
                color: "green" (acceptable), "yellow" (marginal), "red" (unacceptable)
            or (None, None) on error

        Decision rules:
            TEobs < TEa  → "green"  (method meets quality goals)
            TEobs = TEa  → "yellow" (method at limit)
            TEobs > TEa  → "red"    (method fails quality goals)
        """
        try:
            tea = round(
                self.get_allowable_bias(cvw, cvb)
                + (self.get_zscore() * self.get_imp(cvw)),
                2,
            )
            teobs = self.get_te(target, avg, cva)

            if teobs < tea:
                color = "green"
            elif teobs == tea:
                color = "yellow"
            else:
                color = "red"

            return teobs, color
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return None, None

    def get_imp(self, cvw: float) -> float:
        """
        Calculate maximum allowable imprecision from biological variation.

        Args:
            cvw: Within-subject biological variation (%)

        Returns:
            Allowable analytical CV (%) rounded to 2 decimals, or 0.0 on error

        Formula:
            CVa_allowable = 0.5 × CVw

        Reference:
            Fraser CG. Desirable specifications (minimum performance).
            CVa should be ≤ 0.5 × CVw
        """
        try:
            return round(cvw * 0.5, 2)
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def percentage(self, percent: float, whole: float) -> float:
        """
        Calculate percentage of a whole.

        Args:
            percent: Percentage value
            whole: Whole amount

        Returns:
            Result rounded to default precision, or 0.0 on error

        Formula:
            result = (percent × whole) / 100
        """
        try:
            return (percent * whole) / 100.0
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )
            return 0.0

    def get_uncertainty(
        self,
        cva: Optional[float],
        bias: Optional[float],
        k: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate expanded measurement uncertainty (relative).

        Args:
            cva: Analytical CV (%)
            bias: Relative bias (%)
            k: Coverage factor (default: uses get_zscore())

        Returns:
            Expanded relative uncertainty (%) rounded to 1 decimal,
            or None on error

        Formula:
            u_repeatability = CVa
            u_bias = |bias| / √3
            u_combined = √(u_repeatability² + u_bias²)
            U(%) = k × u_combined

        Reference:
            ISO/TS 20914:2019 - Medical laboratories - Practical guidance
            for the estimation of measurement uncertainty.

        Note:
            The bias component is divided by √3 assuming rectangular
            distribution of the systematic error.
        """
        try:
            if cva is None or bias is None:
                return None

            if k is None:
                # Use the same coverage factor used for TE computations
                k = self.get_zscore()

            cva_f  = float(cva)
            bias_f = abs(float(bias))

            # Relative components (already in %)
            u_rep_rel  = cva_f
            u_bias_rel = bias_f / math.sqrt(3.0)

            # Combined and expanded relative uncertainty
            u_c_rel = math.sqrt((u_rep_rel ** 2) + (u_bias_rel ** 2))
            u_rel   = k * u_c_rel

            return round(u_rel, 1)

        except (ZeroDivisionError, ValueError, RuntimeWarning) as e:
            self.on_log(inspect.stack()[0][3],
                        sys.exc_info()[1],
                        sys.exc_info()[0],
                        sys.modules[__name__])
            return None


def main():
    """Test cases for QC module."""
    foo = QC()

    # Mock dependencies that QC expects
    foo.get_file = lambda x: x  # Return filename as-is for testing
    foo.on_log = lambda *args: None  # Silent logging for testing

    print(foo)
    print()

    # Test data from QCWorkbook2008_Jun08.pdf
    series = [4.0, 4.1, 4.0, 4.2, 4.1, 4.1, 4.2]

    print("Test Series:", series)
    print()

    mean = foo.get_mean(series)
    print(f"Mean: {mean}")

    sd = foo.get_sd(series, ddof=0)
    print(f"SD (population): {sd}")

    sd_sample = foo.get_sd(series, ddof=1)
    print(f"SD (sample): {sd_sample}")

    cv = foo.get_cv(series, ddof=0)
    print(f"CV: {cv}%")

    range_val = foo.get_range(series)
    print(f"Range: {range_val}")

    print()

    # Test bias calculation (now preserves sign)
    target = 4.0
    avg = 4.2
    bias = foo.get_bias(avg, target)
    print(f"Bias (avg={avg}, target={target}): {bias}%")

    avg_low = 3.8
    bias_low = foo.get_bias(avg_low, target)
    print(f"Bias (avg={avg_low}, target={target}): {bias_low}%")

    print()
    print("NumPy has been successfully removed!")
    print("All calculations now use Python's built-in statistics module.")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
