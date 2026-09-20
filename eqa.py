# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""External quality assessment: how far this laboratory fell from everybody else.

Internal control answers one question and only one: is the method doing today
what it did yesterday. It cannot answer whether what it does is right,
because the target it is judged against is the laboratory's own. A method can
sit perfectly in control on a mean that moved six months ago, and no
Levey-Jennings chart will ever say so.

A proficiency scheme is the other half. The same material goes to every
participant, the value is assigned from outside, and what comes back is:

    z = (result - assigned) / sd

sd there is not the spread of the participants. It is the standard deviation
the scheme judges by - sigma-pt in ISO 13528 - which is a decision about what
a result has to be worth to be fit for purpose. A z of 1 means this
laboratory was one of those standard deviations out.

One z is about one analyte on one day. The two combined scores read a whole
round at once, and they answer different questions:

    RSZ = sum(z) / sqrt(n)      are we out on the same side, on everything?
    SZ2 = sum(z^2) / n          how far out are we, whichever side?

RSZ keeps the sign, so pluses and minuses cancel: a laboratory scattered
around the assigned values comes out near zero however wide the scatter, and
a laboratory that reads high on everything does not. That is a bias of the
laboratory rather than of one method - a calibrator, a weighing, a way of
working - and nothing in internal control can see it.

SZ2 squares, so nothing cancels: it is the size of the misses regardless of
direction, which is imprecision, and a single bad analyte will raise it while
leaving RSZ where it was. Read together they say which of the two kinds of
error a round had.

References:
    ISO 13528:2015, statistical methods for use in proficiency testing by
    interlaboratory comparison.
    ISO 15189:2022, which asks for participation and for the records of it.
"""

import math

#: Where a z stops being satisfactory, as ISO 13528 sets it. Two is where a
#: result is looked at, three is where it is not defensible. The same two
#: numbers are used for RSZ, which is scaled to be read like a z.
QUESTIONABLE = 2.0
UNSATISFACTORY = 3.0

#: What each verdict is called, in the one place that decides it.
SATISFACTORY_SAID = "Satisfactory"
QUESTIONABLE_SAID = "Questionable"
UNSATISFACTORY_SAID = "Unsatisfactory"


class Eqa:
    """The arithmetic of a proficiency round: one z, and two scores over many."""

    def __str__(self):
        return "class: {0}\nscores: z, RSZ, SZ2".format(self.__class__.__name__)

    def get_z(self, result, assigned, sd):
        """How many of the scheme's standard deviations this result fell from it.

        The sign is kept: reading high and reading low are two different
        problems, and it is the whole point of RSZ that they do not look
        alike.

        @param name: result, assigned, sd
        @return: z
        @rtype: float
        """
        if sd <= 0:
            raise ValueError("a standard deviation of {0} judges nothing".format(sd))

        return round((float(result) - float(assigned)) / float(sd), 2)

    def get_rsz(self, scores):
        """The rescaled sum of the z scores of a round: sum(z) / sqrt(n).

        Read like a z, because that is what the scaling is for. Away from
        zero it says this laboratory was out on the same side across the
        analytes of the round, which is a bias of the laboratory and not of
        any one method.

        An empty round has nothing to sum, and is 0.

        @param name: scores
        @return: RSZ
        @rtype: float
        """
        found = 0.0

        if scores:
            found = round(sum(scores) / math.sqrt(len(scores)), 2)

        return found

    def get_sz2(self, scores):
        """The mean of the squared z scores of a round: sum(z^2) / n.

        Nothing cancels here, so this is the size of the misses whichever way
        they went. A round where every analyte was a little out and a round
        with one analyte badly out can share an RSZ of zero and differ here.

        An empty round has nothing to square, and is 0.

        @param name: scores
        @return: SZ2
        @rtype: float
        """
        found = 0.0

        if scores:
            found = round(sum(score * score for score in scores) / len(scores), 2)

        return found

    def get_verdict(self, score):
        """Satisfactory, questionable or unsatisfactory, by its distance from zero.

        The thresholds are ISO 13528's and they are read on the size of the
        score, not on its sign: two standard deviations out is two standard
        deviations out either way.

        @param name: score
        @return: the verdict
        @rtype: string
        """
        away = abs(score)

        if away >= UNSATISFACTORY:
            found = UNSATISFACTORY_SAID
        elif away >= QUESTIONABLE:
            found = QUESTIONABLE_SAID
        else:
            found = SATISFACTORY_SAID

        return found
