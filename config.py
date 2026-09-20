# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The configuration file, an .ini read and written by hand.

The standard library has `configparser`, which does this and much more:
defaults, interpolation, values on several lines. This class does only what
Biovarase needs, so that a reader can see what reading an .ini file means: go
through it line by line and decide, for each line, what it is.

    ; a comment, and so is a line starting with #
    [statistics]
    ddof = 0
    zscore = 1.65

What it has that Tkinterlite's has not is set() and save(): the program writes
some of these back - the coverage factor, the degrees of freedom, the language
- from its own windows. The file is kept as it was read, line by line, and
only the line that changed is rewritten: the comments that say what a setting
means are still there afterwards, which is the reason they were written.
"""

import os


class Config:
    """Sections of key = value pairs, read once from an .ini file."""

    def __init__(self, path):
        self.path = path
        #: section -> {key: value}, the settings as text
        self.sections = {}
        #: the file as it was read, one string per line
        self.lines = []
        #: (section, key) -> which line holds it, so save() rewrites that one
        self.places = {}
        self.read()

    def __str__(self):
        return "class: {0}\npath: {1}".format(self.__class__.__name__, self.path)

    def read(self):
        """Read the file line by line into self.sections.

        Anything that is not a blank line, a comment, a [section] or a
        key = value inside a section is refused, naming the line: a typo in
        the file stops the program here rather than somewhere else.
        """
        section = None

        with open(self.path, "r", encoding="utf-8") as f:
            self.lines = f.readlines()

        for number, line in enumerate(self.lines, start=1):
            text = line.strip()

            if text == "" or text[0] in (";", "#"):
                pass
            elif text.startswith("[") and text.endswith("]"):
                section = text[1:-1].strip()
                if section in self.sections:
                    raise self.get_error(number, "section [{0}] twice".format(section))
                self.sections[section] = {}
            elif section is None:
                raise self.get_error(number, "outside any section: {0}".format(text))
            elif "=" not in text:
                raise self.get_error(number, 'no "=" in "{0}"'.format(text))
            else:
                # On the first "=" only, so a value may contain one.
                key, value = text.split("=", 1)
                key = key.strip()
                if key == "":
                    raise self.get_error(number, 'no key before "="')
                if key in self.sections[section]:
                    raise self.get_error(number, "{0} twice in [{1}]".format(key, section))
                self.sections[section][key] = value.strip()
                self.places[(section, key)] = number - 1

    def get_error(self, number, message):
        """A ValueError that says which file and which line."""
        return ValueError("{0}, line {1}: {2}".format(os.path.basename(self.path),
                                                      number,
                                                      message))

    def get(self, section, key):
        """The value of a key, as text."""
        if section not in self.sections:
            raise ValueError("{0}: no section [{1}]".format(os.path.basename(self.path),
                                                            section))
        if key not in self.sections[section]:
            raise ValueError("{0}: no {1} in [{2}]".format(os.path.basename(self.path),
                                                            key,
                                                            section))

        return self.sections[section][key]

    def get_int(self, section, key):
        """The value of a key, as a whole number."""
        value = self.get(section, key)

        if not value.lstrip("-").isdigit():
            raise ValueError("{0}: {1} in [{2}] is not a whole number: {3}".format(
                os.path.basename(self.path), key, section, value))

        return int(value)

    def get_float(self, section, key):
        """The value of a key, as a number with a decimal point.

        The coverage factor and the correlation coefficient are read with
        this: 1.65 has to stay 1.65 and not become 1.
        """
        value = self.get(section, key)

        try:
            number = float(value)
        except ValueError:
            raise ValueError("{0}: {1} in [{2}] is not a number: {3}".format(
                os.path.basename(self.path), key, section, value))

        return number

    def set(self, section, key, value):
        """Change a setting, in memory and in the file.

        Only a key already in the file can be changed: a new one would have
        no comment saying what it is for, and nothing in the program reads a
        setting it did not ask for.
        """
        self.get(section, key)

        self.sections[section][key] = str(value)
        number = self.places[(section, key)]
        self.lines[number] = "{0} = {1}\n".format(key, value)
        self.save()

    def save(self):
        """Write the file back, line by line, comments and all."""
        with open(self.path, "w", encoding="utf-8") as f:
            f.writelines(self.lines)
