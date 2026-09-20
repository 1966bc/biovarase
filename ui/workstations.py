# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The list of instruments on the bench. Everything but the names is in ui.list_window."""

import ui.workstation

from ui.list_window import ListWindow


class UI(ListWindow):
    TABLE = "workstations"
    CAPTION = "description"
    DIALOG = ui.workstation.UI
