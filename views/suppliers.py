from views.lookup import LookupUI

class UI(LookupUI):
    def __init__(self, parent):
        super().__init__(parent, table="suppliers")
