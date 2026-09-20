# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The list of samples. Everything but the names is in ui.list_window."""

import ui.sample

from ui.list_window import ListWindow


class UI(ListWindow):
    TABLE = "samples"
    CAPTION = "description"
    DIALOG = ui.sample.UI
