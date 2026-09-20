# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The proficiency schemes. Everything but the names is in ui.list_window."""

import ui.eqa_scheme

from ui.list_window import ListWindow


class UI(ListWindow):
    TABLE = "eqa_schemes"
    CAPTION = "description"
    DIALOG = ui.eqa_scheme.UI
