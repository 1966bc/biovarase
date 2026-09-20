# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The few numbers the windows agree on."""

#: Tries before the program gives up and closes.
MAX_LOGIN_ATTEMPTS = 3

#: As long as the column in the database, so the window refuses what the
#: database would refuse.
BATCH_DESCRIPTION_MAX_LENGTH = 15
LOT_NUMBER_MAX_LENGTH = 20

#: The main window never gets smaller than this: below it the chart and the
#: list of results stop being readable together.
MAIN_WINDOW_MIN_WIDTH = 1400
MAIN_WINDOW_MIN_HEIGHT = 700
