# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The Westgard multirule: whether a series of control results stops the run.

One rule cannot do it. Limits at two standard deviations reject one good run
in twenty, which teaches a laboratory to ignore them; limits at three let a
whole morning of drift through, because every single point is still inside.
The multirule reads several narrow rules together instead, and each one is
sensitive to a different kind of error:

    1:3S   one result beyond 3 SD                     random error, reject
    2:2S   two in a row beyond 2 SD, the same side    systematic error
    R:4S   two in a row 4 SD apart                    imprecision
    4:1S   four in a row beyond 1 SD, the same side   a shift beginning
    10:X   ten in a row on the same side of target    a bias that has settled
    1:2S   one result beyond 2 SD                     warning, look

The order is the answer. Several of these can be true of the same series -
the ten points that broke 10:X contain the four that broke 4:1S - and what
is wanted is the one that says most about what happened, so the rules are
read from the most specific to the least.

1:2S is the screening rule and it is read first: within two standard
deviations there is nothing for the rejection rules to find in the last
result. What is still looked for in that case is 4:1S and 10:X, because
those two are about where the series has been sitting and not about the
result just run: a method can walk a long way from its target without a
single point going out.

Every rule reads the end of the series, which is the run being judged; the
series arrives oldest first, newest last.

References:
    Westgard JO. Basic QC Practices, 4th edition, 2016.
    ISO 15189:2022, medical laboratories.
"""

#: What the multirule answers when nothing was broken. Not translated and
#: not a colour: it is written into sheets and read back by comparisons.
ACCEPT = "Accept"


class Westgards:
    """The six rules, and the order that turns them into an answer."""

    def __str__(self):
        return "class: {0}\nrules: 1:3S, 2:2S, R:4S, 4:1S, 10:X, 1:2S".format(
            self.__class__.__name__)

    def get_rule(self, target, sd, series):
        """The rule this series breaks, or Accept.

        The first rule broken, read from the most specific to the least, so
        that a series which breaks three of them is reported by the one that
        names the error.

        @param name: target, sd, series
        @return: 1:3S, 2:2S, R:4S, 4:1S, 10:X, 1:2S or Accept
        @rtype: string
        """
        if not series:
            raise ValueError("no results: there is nothing to read a rule on")

        if self.get_rule_12S(series, target, sd):
            if self.get_rule_13S(series, target, sd):
                found = "1:3S"
            elif self.get_rule_22S(series, target, sd):
                found = "2:2S"
            elif self.get_rule_R4S(series, target, sd):
                found = "R:4S"
            elif self.get_rule_41S(series, target, sd):
                found = "4:1S"
            elif self.get_rule_10X(series, target, sd):
                found = "10:X"
            else:
                found = "1:2S"
        elif self.get_rule_41S(series, target, sd):
            found = "4:1S"
        elif self.get_rule_10X(series, target, sd):
            found = "10:X"
        else:
            found = ACCEPT

        return found

    # ---------------------------------------------------------- the six rules
    #
    # One shape for all of them: the series, the target and the standard
    # deviation, and an answer of true or false. Each says how many results it
    # needs and finds nothing in a series shorter than that - a lot opened on
    # Monday has not broken 10:X by Tuesday.
    #
    # They are public because the Statistics window asks each one separately:
    # the main window reports the rule that stops the run, and that window
    # says whether it was the only one.

    def get_rule_12S(self, series, target, sd):
        """One result beyond 2 SD: the warning, and the door to the others.

        @param name: series, target, sd
        @return: broken
        @rtype: boolean
        """
        return abs(series[-1] - target) > 2 * sd

    def get_rule_13S(self, series, target, sd):
        """One result beyond 3 SD: reject the run.

        Three standard deviations is three results in a thousand by chance,
        so this is not chance.

        @param name: series, target, sd
        @return: broken
        @rtype: boolean
        """
        return abs(series[-1] - target) > 3 * sd

    def get_rule_22S(self, series, target, sd):
        """Two in a row beyond 2 SD on the same side: systematic error.

        The same side is what makes it systematic. Two results that far out
        in opposite directions are R:4S and a different problem.

        @param name: series, target, sd
        @return: broken
        @rtype: boolean
        """
        found = False

        if len(series) >= 2:
            last_two = series[-2:]
            found = (all(value >= target + 2 * sd for value in last_two)
                     or all(value <= target - 2 * sd for value in last_two))

        return found

    def get_rule_41S(self, series, target, sd):
        """Four in a row beyond 1 SD on the same side: a shift beginning.

        One standard deviation is not far. Four times running on the same
        side of the target is: a calibration going, a reagent ageing.

        @param name: series, target, sd
        @return: broken
        @rtype: boolean
        """
        found = False

        if len(series) >= 4:
            last_four = series[-4:]
            found = (all(value > target + sd for value in last_four)
                     or all(value < target - sd for value in last_four))

        return found

    def get_rule_R4S(self, series, target, sd):
        """Two in a row four standard deviations apart: imprecision.

        The range and not the position: both results can be inside their
        limits and still be too far from each other for the method's spread.

        Read within a run. Across runs, two results that far apart are two
        different days and the rule says less than it seems to.

        @param name: series, target, sd
        @return: broken
        @rtype: boolean
        """
        found = False

        if len(series) >= 2:
            last_two = series[-2:]
            found = max(last_two) - min(last_two) >= 4 * sd

        return found

    def get_rule_10X(self, series, target, sd):
        """Ten in a row on the same side of the target: a settled bias.

        Not one of them has to be out. That is the point of the rule: a
        method reading consistently high is wrong in a way no single result
        will ever show, and ten consecutive on one side is one chance in five
        hundred.

        The standard deviation is not used and is taken all the same, so that
        every rule in this class is called the same way.

        @param name: series, target, sd
        @return: broken
        @rtype: boolean
        """
        found = False

        if len(series) >= 10:
            last_ten = series[-10:]
            found = (all(value > target for value in last_ten)
                     or all(value < target for value in last_ten))

        return found
