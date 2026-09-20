# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
from ui.lookup import LookupUI

class UI(LookupUI):
    def __init__(self, parent):
        super().__init__(parent, table="suppliers")
