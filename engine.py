# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The one object every window reaches: it owns the parts, it is none of them.

Composition, each part is an attribute, a call says who does the work -
engine.db.read(...), engine.qc.get_mean(...) - and each part can be built and
tested on its own, as the tests do with a database in memory.

What is here is what belongs to nobody else: who is logged in, where the files
are, and the few questions about this laboratory that are asked from more than
one window.
"""

import os
import subprocess
import sys

import bcrypt

from config import Config
from dbms import DBMS
from events import Events
from exporter import Exporter
from qc import QC
from tools import Tools
from westgards import Westgards
from windows import Windows

#: The roles. The laboratory has two: whoever runs it, and whoever works in it.
ROLE_ADMIN = 0
ROLE_TECHNICIAN = 1


class Engine:
    """The parts of the application, and what belongs to none of them."""

    def __init__(self, log):
        self.log = log
        # The settings, read by the Config class from biovarase.ini.
        self.config = Config(self.get_file("biovarase.ini"))
        # The database beside the program, wherever it is started from.
        self.db = DBMS(self.get_file("biovarase.sl3"), log)
        # Styles and widget helpers.
        self.tools = Tools()
        # The statistics of a series, and the rules read on them.
        self.qc = QC(self.config)
        self.westgards = Westgards()
        # Sheets out of the data.
        self.exporter = Exporter(self)
        # Who changed what, told to the windows that show it: the Observer.
        self.events = Events(log)
        # The open windows, one per name: the Singleton pattern, by name.
        self.windows = Windows(log)

        self.app_title = "Biovarase"
        #: The row of the user who logged in; empty until someone does.
        self.log_user = {}
        #: The lot the main window is on, remembered while the program runs.
        self.batch_data = None

        self.no_selected = "Attention!\nNo record selected!"
        self.ask_to_delete = "Delete data?"
        self.ask_to_save = "Save data?"
        self.abort = "Operation aborted!"
        self.user_not_enable = "You are not allowed to do this."

    def __str__(self):
        return "class: {0}\nparts: log, config, db, tools, qc, westgards, exporter, events, windows".format(
            self.__class__.__name__)

    # ------------------------------------------------------------- the files

    def get_file(self, file):
        """The full path of a file beside the program.

        So the database, the log and the settings are found wherever the
        program is started from.

        @param name: file
        @return: path
        @rtype: string
        """
        return os.path.join(os.path.dirname(__file__), file)

    def get_python_version(self):
        """The Python this is running on, for the About window."""
        return "Python version:\n{0}".format(".".join(map(str, sys.version_info[:3])))

    def get_icon(self):
        """The icon of the windows: its file holds one base64 PNG."""
        with open(self.get_file("biovarase.png"), "r") as f:
            return f.readline()

    def get_license(self):
        """The licence, as the About window shows it."""
        with open(self.get_file("LICENSE"), "r") as f:
            return f.read()

    def open_file(self, path):
        """Open a file with the program the system uses for it.

        Popen and not call: call would wait for that program to be closed, and
        the whole application would stand still meanwhile. A file that is not
        there raises, rather than nothing happening at all.

        @param name: path
        """
        if not os.path.exists(path):
            raise FileNotFoundError("no such file: {0}".format(path))

        if os.name == "posix":
            subprocess.Popen(["xdg-open", path])
        else:
            os.startfile(path)

    def open_log(self):
        """Open the log file with the program the system uses for text."""
        self.open_file(self.log.path)

    # ----------------------------------------------------- who is working

    def on_login(self, nickname, password):
        """The user with this nickname, if the password is theirs.

        bcrypt holds the salt and the cost inside the hash it made, so
        checkpw takes the password as typed and the hash as stored and needs
        nothing else. What is stored is never the password.

        @param name: nickname, password
        @return: the user, or None
        @rtype: dictionary
        """
        found = None

        sql = "SELECT * FROM users WHERE nickname = ? AND status = 1"
        user = self.db.read(False, sql, (nickname,))

        if user is not None and bcrypt.checkpw(password, user["pswrd"].encode("utf-8")):
            found = dict(user)

        return found

    def set_log_user(self, user):
        """Remember who logged in, and tell the database, for the audit.

        @param name: user
        """
        self.log_user = user
        self.db.set_session_user(user["user_id"])
        self.log.trace("logged in: {0}".format(user["nickname"]))

    def on_logout(self):
        """Forget who was working, here and in the database."""
        self.log_user = {}
        self.db.set_session_user(None)

    def is_admin(self):
        """True when whoever is logged in runs the laboratory.

        There are two roles: an administrator, who keeps the master data and
        the users, and a technician, who enters results. Everything about a
        result is open to both - what is entered is written down by the audit
        trail, which is a better guard than a permission.
        """
        return self.log_user.get("role") == ROLE_ADMIN

    def get_new_password(self):
        """A hash of the password every new user starts with.

        gensalt() makes a new salt every time, so two users with the same
        password have different hashes, and the cost of the hashing is part
        of what it returns.
        """
        return bcrypt.hashpw(b"pass", bcrypt.gensalt()).decode("utf-8")

    # ------------------------------------------------------- the laboratory

    def get_series(self, batch_id, limit, result_id=None, db=None):
        """The results of a lot, oldest first, as the chart draws them.

        Only the results that count: status 0 is a point excluded from the
        statistics on purpose, and it is left out here rather than in every
        window that asks. The newest 'limit' of them are taken, then turned
        round, because a chart reads left to right and a query reads newest
        first.

        result_id draws the series as it was when that result was entered:
        the Westgard rules are read on the points up to it, not on the ones
        that came after.

        db is a second connection, for a worker thread doing an export.

        @param name: batch_id, limit, result_id, db
        @return: results
        @rtype: list
        """
        if result_id is None:
            sql = """SELECT ROUND(result, 2) AS result
                     FROM results
                     WHERE batch_id = ? AND status = 1
                     ORDER BY received DESC
                     LIMIT ?"""
            args = (batch_id, limit)
        else:
            sql = """SELECT ROUND(result, 2) AS result
                     FROM results
                     WHERE batch_id = ? AND status = 1 AND result_id <= ?
                     ORDER BY received DESC
                     LIMIT ?"""
            args = (batch_id, result_id, limit)

        rows = (db or self.db).read(True, sql, args)

        return [row["result"] for row in reversed(rows)]

    def get_test_name(self, test_id):
        """The name of an analyte."""
        row = self.db.get_selected("tests", "test_id", test_id)

        return row["description"]

    def get_control_name(self, control_id):
        """The name of a control material."""
        row = self.db.get_selected("controls", "control_id", control_id)

        return row["description"]

    def get_um(self, unit_id):
        """The unit a result is measured in."""
        row = self.db.get_selected("units", "unit_id", unit_id)

        return row["description"]

    def get_records(self):
        """How many results the main window loads at once."""
        return self.config.get_int("display", "records")

    def get_elements(self):
        """How many points the chart draws."""
        return self.config.get_int("display", "elements")

    def get_observations(self):
        """How many results a series needs before the rules are read on it."""
        return self.config.get_int("statistics", "observations")

    def get_correlation_coefficient(self):
        """Above this, a Youden plot says the two controls agree."""
        return self.config.get_float("statistics", "correlation_coefficient")

    def get_remember_batch(self):
        """Open the main window on the lot it was left on."""
        return self.config.get_int("display", "remember_batch")

    def get_show_expired_batches(self):
        """Show lots past their expiration date in the lists."""
        return self.config.get_int("display", "show_expired_batches")

    def get_show_recent_only(self):
        """Show only the lots with a result in the last months."""
        return self.config.get_int("display", "show_recent_only")

    # -------------------------------------------------------------- the dates

    #: How a date is written, and what strftime makes of it.
    DATE_FORMATS = {"dd-mm-yyyy": "%d-%m-%Y",
                    "mm-dd-yyyy": "%m-%d-%Y",
                    "yyyy-mm-dd": "%Y-%m-%d"}

    def get_date_format(self):
        """The date format from the settings, as strftime wants it.

        A format that is not one of the three is refused here, naming the
        file: a date shown the wrong way round is read wrong by whoever
        reads it, and 03-04 is a different day in two of these three.

        @return: format
        @rtype: string
        """
        written = self.config.get("display", "date_format")

        if written not in self.DATE_FORMATS:
            raise ValueError("biovarase.ini: date_format is {0}; it is one of {1}".format(
                written, ", ".join(self.DATE_FORMATS)))

        return self.DATE_FORMATS[written]

    def format_date(self, value):
        """A date as the settings ask for it; None is an empty cell.

        @param name: value
        @return: the date, written
        @rtype: string
        """
        written = ""
        if value is not None:
            written = value.strftime(self.get_date_format())

        return written

    def format_datetime(self, value):
        """The same, with the time after it: a control has an hour, not only a day.

        @param name: value
        @return: the date and time, written
        @rtype: string
        """
        written = ""
        if value is not None:
            written = value.strftime("{0} %H:%M".format(self.get_date_format()))

        return written
