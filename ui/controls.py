# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The list of control materials. Everything but the names is in ui.list_window."""

import ui.control

from ui.list_window import ListWindow


class UI(ListWindow):
    TABLE = "controls"
    CAPTION = "description"
    DIALOG = ui.control.UI
