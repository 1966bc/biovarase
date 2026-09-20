# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The list of units of measurement. Everything but the names is in ui.list_window."""

import ui.unit

from ui.list_window import ListWindow


class UI(ListWindow):
    TABLE = "units"
    CAPTION = "description"
    DIALOG = ui.unit.UI
