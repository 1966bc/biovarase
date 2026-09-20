# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""A combo box holding the rows of another table, filled from it.

Three forms point at a row of another table - a control and an instrument at
their supplier, a workstation at its model - and the three did the same four
things: read the table, put the captions in the box, show the one the row
points at, and read back the key of the one chosen.

The box holds the captions and this class holds the keys, position by
position: a caption can change meaning between one release and the next, a
primary key cannot.
"""


class Lookup:
    """The rows of one table in a combo box, by caption, giving back the key."""

    def __init__(self, engine, combo, table, caption="description"):
        self.engine = engine
        self.combo = combo
        self.table = table
        self.caption = caption
        #: position in the box -> primary key
        self.ids = {}
        self.set_values()

    def __str__(self):
        return "class: {0}\ntable: {1}, rows: {2}".format(self.__class__.__name__,
                                                          self.table,
                                                          len(self.ids))

    def set_values(self):
        """Read the table and fill the box: the rows in use, in order."""
        key = self.engine.db.get_primary_key(self.table)
        sql = "SELECT * FROM {0} WHERE status = 1 ORDER BY {1}".format(self.table,
                                                                       self.caption)
        rows = self.engine.db.read(True, sql, ())

        self.ids.clear()
        captions = []
        for index, row in enumerate(rows):
            self.ids[index] = row[key]
            captions.append(row[self.caption])

        self.engine.tools.set_combo(self.combo, captions)

    def set_id(self, value):
        """Show the row this key stands for, or nothing when it is not there."""
        self.engine.tools.set_combo_id(self.combo, self.ids, value)

    def get_id(self):
        """The key of the row chosen, or None when nothing is."""
        return self.engine.tools.get_combo_id(self.combo, self.ids)
