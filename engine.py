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

import datetime
import os
import subprocess
import webbrowser

import bcrypt

from config import Config
from dbms import DBMS
from events import Events
from exporter import Exporter
from qc import QC
from report import Report
from tools import Tools
from westgards import Westgards
from windows import Windows

#: The user manual, beside the program, and where it is read if it is not.
MANUAL = os.path.join("documents", "USER_MANUAL.pdf")
MANUAL_URL = "https://github.com/1966bc/Biovarase/blob/main/documents/USER_MANUAL.md"

#: The laboratory has two roles - whoever runs it and whoever works in it -
#: and one question to ask about them, which is whether this is the first.
#: ui/user.py has the pair, as the two lines of its combo box.
ROLE_ADMIN = 0


class Engine:
    """The parts of the application, and what belongs to none of them."""

    def __init__(self, log):
        self.log = log
        # The settings, read by the Config class from biovarase.ini.
        self.config = Config(self.get_file("biovarase.ini"))
        # The database: beside the program, or wherever the settings say.
        self.db = DBMS(self.get_database(), log)
        # Styles and widget helpers.
        self.tools = Tools()
        # The statistics of a series, and the rules read on them.
        self.qc = QC(self.config)
        self.westgards = Westgards()
        # Sheets out of the data, and the form that is signed.
        self.exporter = Exporter(self)
        self.report = Report(self)
        # Who changed what, told to the windows that show it: the Observer.
        self.events = Events(log)
        # The open windows, one per name: the Singleton pattern, by name.
        self.windows = Windows(log)

        self.app_title = "Biovarase"
        #: What version is running, put here by the application when it
        #: starts: the number lives once, in ui/app.py, and whatever needs it
        #: - the About window, the footer of a report - asks for it here
        #: rather than importing a window to find out.
        self.version = ""
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
        return "class: {0}\nparts: log, config, db, tools, qc, westgards, exporter, report, events, windows".format(
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

    def get_version(self):
        """The version of the program that is running."""
        return self.version

    def get_laboratory(self):
        """Whose laboratory this is: the site, the laboratory, the section.

        @return: site, lab, section
        @rtype: tuple
        """
        return (self.config.get("laboratory", "site"),
                self.config.get("laboratory", "lab"),
                self.config.get("laboratory", "section"))

    def get_database(self):
        """The database file, from the settings.

        A bare name is taken beside the program, so it is found wherever the
        program is started from; an absolute path is taken as it is, for a
        file kept somewhere else.

        @return: path
        @rtype: string
        """
        written = self.config.get("database", "file")

        if os.path.isabs(written):
            path = written
        else:
            path = self.get_file(written)

        return path

    def get_icons(self):
        """Every size of the application icon: one base64 PNG per line.

        The window manager picks the size each place needs - the title bar,
        the task list, the switcher - so none of them is scaled up and
        blurred. The file is written by forge/make_icon.py.

        @return: the icons, as base64
        @rtype: list
        """
        with open(self.get_file("icon"), "r") as f:
            return f.read().split()

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

    def open_url(self, url):
        """Open an address in the browser the system uses.

        webbrowser and not xdg-open: it is the one thing in the standard
        library that knows what a browser is on every system this runs on,
        and it does not block.

        @param name: url
        """
        webbrowser.open(url)

    def open_manual(self):
        """Open the user manual, where the program keeps it.

        The PDF ships with the program, so the manual is at hand on a bench
        with no network. If it was left out of the build, the copy in the
        repository answers instead.
        """
        path = self.get_file(MANUAL)

        if os.path.exists(path):
            self.open_file(path)
        else:
            self.open_url(MANUAL_URL)

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

    def is_admin(self):
        """True when whoever is logged in runs the laboratory.

        There are two roles: an administrator, who keeps the master data and
        the users, and a technician, who enters results. Everything about a
        result is open to both - what is entered is written down by the audit
        trail, which is a better guard than a permission.
        """
        return self.log_user.get("role") == ROLE_ADMIN

    def get_hash(self, password):
        """The hash of a password, as it is stored.

        gensalt() makes a new salt every time, so two users with the same
        password have different hashes, and the cost of the hashing is part
        of what comes back. What is stored is never the password.

        @param name: password
        @return: the hash
        @rtype: string
        """
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

    def get_new_password(self):
        """A hash of the password every new user starts with."""
        return self.get_hash(b"pass")

    # ------------------------------------------------------- the laboratory

    def get_series(self, batch_id, limit, result_id=None, db=None, since=None):
        """The results of a lot, oldest first, as the chart draws them.

        Only the results that count: status 0 is a point excluded from the
        statistics on purpose, and it is left out here rather than in every
        window that asks. The newest 'limit' of them are taken, then turned
        round, because a chart reads left to right and a query reads newest
        first.

        result_id draws the series as it was when that result was entered:
        the Westgard rules are read on the points up to it, not on the ones
        that came after.

        since cuts the series at a day: the Period menu decides how far back
        a window looks, and a mean of the last thirty results is a different
        number from a mean of the last thirty within three months.

        db is a second connection, for a worker thread doing an export.

        @param name: batch_id, limit, result_id, db, since
        @return: results
        @rtype: list
        """
        sql = """SELECT ROUND(result, 2) AS result
                   FROM results
                  WHERE batch_id = ? AND status = 1
                    AND (? IS NULL OR result_id <= ?)
                    AND (? IS NULL OR received >= ?)
               ORDER BY received DESC
                  LIMIT ?"""
        args = (batch_id, result_id, result_id, since, since, limit)

        rows = (db or self.db).read(True, sql, args)

        return [row["result"] for row in reversed(rows)]

    #: The periods the program offers, as (code, months). A code that is not
    #: one of these is read as a date.
    PERIODS = {"last_month": 1,
               "last_3_months": 3,
               "last_6_months": 6,
               "last_12_months": 12,
               "all": None}

    def get_period(self):
        """How far back the windows look, as a code and the day it starts.

        The day is None for "all", which is what a query reads as "no lower
        bound". A code that is not one of the known ones is a date: the
        Period menu writes one there when somebody asks for "Since...".

        @return: code, first day
        @rtype: tuple
        """
        code = self.config.get("display", "period")

        if code in self.PERIODS:
            months = self.PERIODS[code]
            if months is None:
                first = None
            else:
                first = self.get_today() - datetime.timedelta(days=months * 31)
        else:
            first = datetime.date.fromisoformat(code)

        return (code, first)

    def set_period(self, code):
        """Remember how far back to look, so the program opens where it was left.

        @param name: code
        """
        self.config.set("display", "period", code)

    def get_records(self):
        """How many results the main window loads at once."""
        return self.config.get_int("display", "records")

    def get_elements(self):
        """How many points the chart draws."""
        return self.config.get_int("display", "elements")

    def get_observations(self):
        """How many results a series needs before the rules are read on it."""
        return self.config.get_int("statistics", "observations")

    # -------------------------------------------------------------- the dates

    #: How a date is written, and what strftime makes of it.
    DATE_FORMATS = {"dd-mm-yyyy": "%d-%m-%Y",
                    "mm-dd-yyyy": "%m-%d-%Y",
                    "yyyy-mm-dd": "%Y-%m-%d"}

    def backup(self):
        """Copy the database into sql/bks, named after the moment.

        sqlite3's own backup and not a file copy: it goes through the
        connection, so a copy taken while something is writing is a database
        and not half of one. The name sorts by date and never overwrites.

        @return: path of the copy
        @rtype: string
        """
        import sqlite3

        folder = self.get_file(os.path.join("sql", "bks"))
        os.makedirs(folder, exist_ok=True)

        name = "biovarase_{0}.sl3".format(
            datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        path = os.path.join(folder, name)

        copy = sqlite3.connect(path)
        with copy:
            self.db.con.backup(copy)
        copy.close()

        return path

    def get_today(self):
        """Today, as a date: what an expiration is compared against.

        @return: today
        @rtype: date
        """
        return datetime.date.today()

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
