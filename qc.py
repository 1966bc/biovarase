# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The statistics of a control series, and the goals they are held to.

Two kinds of number live here. What the series says about itself - mean,
standard deviation, coefficient of variation, range, bias against the target -
and what the analyte allows, which comes from biological variation and does
not depend on this laboratory at all: allowable imprecision, allowable bias,
total error allowable.

None of these methods swallows an error. A CV of 0.0 returned because
something went wrong is indistinguishable from a method that measures
perfectly, and it would be read as the second. Where a zero denominator is a
real case - an empty series, a target of zero - it is answered explicitly and
said so in the docstring; anything else raises and is written to the log.

References:
    ISO 15189:2022, medical laboratories.
    ISO/TS 20914:2019, practical guidance for the estimation of measurement
    uncertainty.
    Westgard JO. Basic QC Practices, 4th edition, 2016.
    Fraser CG. Biological Variation: From Principles to Practice, 2001.
"""

import math
import statistics


class QC:
    """The numbers read off a series of control results."""

    def __init__(self, config):
        #: Where ddof and the coverage factor come from.
        self.config = config

    def __str__(self):
        return "class: {0}\nddof: {1}, zscore: {2}".format(self.__class__.__name__,
                                                           self.get_ddof(),
                                                           self.get_zscore())

    def get_ddof(self):
        """Delta degrees of freedom: 1 for a sample, 0 for the population.

        @return: ddof
        @rtype: integer
        """
        return self.config.get_int("statistics", "ddof")

    def get_zscore(self):
        """The coverage factor: 1.65, 1.96 or 2, as the settings say.

        @return: zscore
        @rtype: float
        """
        return self.config.get_float("statistics", "zscore")

    def get_mean(self, values):
        """The arithmetic mean of a series; an empty series has none, and is 0.

        @param name: values
        @return: mean
        @rtype: float
        """
        found = 0.0
        if values:
            found = round(statistics.mean(values), 2)

        return found

    def get_sd(self, values, ddof=None):
        """The standard deviation of a series.

        With ddof 1 it is the standard deviation of a sample, divided by n-1,
        which is what a series of control results is: a sample of what the
        method would do if it ran for ever. With ddof 0 it is the population's,
        divided by n. A sample of one has no spread to speak of, and is 0.

        @param name: values, ddof
        @return: standard deviation
        @rtype: float
        """
        if ddof is None:
            ddof = self.get_ddof()

        found = 0.0
        if len(values) > 1:
            if ddof == 1:
                found = round(statistics.stdev(values), 2)
            else:
                found = round(statistics.pstdev(values), 2)
        elif len(values) == 1 and ddof == 0:
            found = 0.0

        return found

    def get_cv(self, values, ddof=None):
        """The coefficient of variation, the spread as a percentage of the mean.

        Computed from the standard deviation and the mean as they are, and
        rounded once at the end. Dividing the rounded SD by the rounded mean
        would carry two roundings into a third: on a series of 8 to 12 it is
        the difference between 15.81 and 15.8, and the same mistake on a
        small CV moves the figure a method is judged by.

        A series whose mean is zero has no coefficient of variation - the
        spread would be a percentage of nothing - and is 0.

        @param name: values, ddof
        @return: cv %
        @rtype: float
        """
        if ddof is None:
            ddof = self.get_ddof()

        found = 0.0
        if values:
            mean = statistics.mean(values)
            if mean != 0 and len(values) > 1:
                if ddof == 1:
                    deviation = statistics.stdev(values)
                else:
                    deviation = statistics.pstdev(values)
                found = round((deviation / mean) * 100, 2)

        return found

    def get_range(self, values):
        """Highest minus lowest, the peak to peak of a series.

        @param name: values
        @return: range
        @rtype: float
        """
        found = 0.0
        if values:
            found = round(max(values) - min(values), 2)

        return found

    def get_bias(self, avg, target):
        """How far the series sits from the target, as a signed percentage.

        The sign is kept: a method reading high and one reading low are two
        different problems, and abs() would lose which is which.

        @param name: avg, target
        @return: bias %
        @rtype: float
        """
        found = 0.0
        if float(target) != 0:
            found = round(((float(avg) - float(target)) / float(target)) * 100.0, 2)

        return found

    def get_imp(self, cvw):
        """The imprecision the analyte allows: half its within-subject variation.

        Fraser's desirable specification, CVa <= 0.5 x CVw.

        @param name: cvw
        @return: allowable cv %
        @rtype: float
        """
        return round(cvw * 0.5, 2)

    def get_allowable_bias(self, cvw, cvb):
        """The bias the analyte allows: 0.25 x sqrt(CVw^2 + CVb^2).

        Fraser again: the desirable specification puts the bias at a quarter
        of the total biological variation, within and between subjects.

        @param name: cvw, cvb
        @return: allowable bias %
        @rtype: float
        """
        return abs(round(math.sqrt(math.pow(cvw, 2) + math.pow(cvb, 2)) * 0.25, 2))

    def get_te(self, target, avg, cv):
        """The total error this series shows: |bias| + k x CV.

        @param name: target, avg, cv
        @return: total error %
        @rtype: float
        """
        bias = self.get_bias(avg, target)

        return round(abs(bias) + (self.get_zscore() * float(cv)), 2)

    def get_tea(self, cvw, cvb):
        """The total error the analyte allows: allowable bias + k x allowable imprecision.

        @param name: cvw, cvb
        @return: total error allowable %
        @rtype: float
        """
        return round(self.get_allowable_bias(cvw, cvb)
                     + (self.get_zscore() * self.get_imp(cvw)), 2)

    def get_sigma(self, cvw, cvb, target, series):
        """The sigma metric: (TEa - |bias|) / CV, how many CVs fit in the goal.

        Six is world class, three is the least a method can run at. A series
        with no spread at all has no sigma to compute, and is 0.

        @param name: cvw, cvb, target, series
        @return: sigma
        @rtype: float
        """
        cv = self.get_cv(series)

        found = 0.0
        if cv != 0:
            tea = self.get_tea(cvw, cvb)
            bias = self.get_bias(self.get_mean(series), target)
            found = round((tea - abs(bias)) / cv, 2)

        return found

    def get_uncertainty(self, cva, bias, k=None):
        """The measurement uncertainty of a result, as a percentage.

        ISO/TS 20914: the imprecision as it is, the bias treated as a
        rectangular distribution and so divided by the square root of three,
        the two added in quadrature, and the whole multiplied by the coverage
        factor.

        @param name: cva, bias, k
        @return: expanded uncertainty %
        @rtype: float
        """
        if k is None:
            k = self.get_zscore()

        combined = math.sqrt(math.pow(float(cva), 2)
                             + math.pow(abs(float(bias)) / math.sqrt(3.0), 2))

        return round(k * combined, 1)

    def percentage(self, percent, whole):
        """That percentage of that number.

        @param name: percent, whole
        @return: the part
        @rtype: float
        """
        return (percent * whole) / 100.0
