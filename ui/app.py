# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The application: the root window, the engine, the login.

The facts about the program live here too, once: its version and date, who
wrote it, under which licence. The About window shows them.

Version 5 because the database is another one: another engine, another
schema, and a file of either version unreadable by the other. Version 4 was
numbered 4.2, after the Answer to the Ultimate Question of Life, the
Universe, and Everything, and it kept that number for as long as it ran.
"""

import tkinter as tk
from tkinter import messagebox

from engine import Engine
from ui.login import Login
from ui.main import Main

#: The main window never gets smaller than this: below it the chart and the
#: list of results stop being readable together, which is the whole layout.
MAIN_WINDOW_MIN_WIDTH = 1400
MAIN_WINDOW_MIN_HEIGHT = 700

__author__ = "Giuseppe Costanzi (1966bc)"
__copyright__ = "Copyleft"
__credits__ = ["hal9000", ]
__license__ = "GNU GPL, version 3 or later"
__version__ = "5.0"
__maintainer__ = "1966bc"
__email__ = "giuseppecostanzi@gmail.com"
__date__ = "autumnus MMXXVI"
__status__ = "production"


class App(tk.Tk):
    """The application: the root window, the engine, the login."""

    def __init__(self, title, log):
        super().__init__()

        self.engine = Engine(log)
        self.engine.version = __version__

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        # The name of the program, kept apart from the title of the window:
        # the title also carries whose laboratory this is, and the About
        # window wants the name alone.
        self.name = title
        site, lab, section = self.engine.get_laboratory()
        self.title("{0} - {1} - {2}".format(title, site, lab))
        self.resizable(0, 0)
        self.engine.tools.set_style(self.engine.config.get("window", "theme"))
        self.set_icon()
        self.set_info()

        login = Login(self)
        login.on_open()
        self.engine.log.trace("ready; the engine holds log, config, db, tools, events, windows")

    def show_main(self):
        """The main window takes the place of the login, once it is passed.

        The root window grows and becomes resizable here and not before: the
        login is a small fixed form, the main window is a chart beside a
        table and wants the room.
        """
        self.resizable(1, 1)
        self.minsize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        main = Main(self)
        main.on_open()
        main.pack(fill=tk.BOTH, expand=1)
        self.engine.tools.center_me(self)

    def set_icon(self):
        """The icon, in every size the window manager may ask for.

        The images are kept on the instance: Tk holds them by name and a
        PhotoImage nobody keeps is collected, leaving an empty icon.
        """
        self.icons = [tk.PhotoImage(data=data) for data in self.engine.get_icons()]
        self.iconphoto(True, *self.icons)

    def set_info(self):
        """The facts the About window shows, from the metadata above."""
        self.info = {"name": self.name,
                     "version": __version__,
                     "date": __date__,
                     "author": __author__,
                     "licence": __license__}

    def report_callback_exception(self, exc, val, tb):
        """Tkinter calls this for an exception raised in a callback.

        A button, a menu, an after(): every error coming out of the interface
        ends up here, the one place where it is handled. It is written to the
        log with its traceback and shown, so the application goes on and
        nothing fails in silence. Tkinter calls this from inside its own
        except block, which is what log.exception() needs.
        """
        self.engine.log.trace("{0}: {1}".format(exc.__name__, val))
        self.engine.log.exception("{0}: {1}".format(exc.__name__, val))
        messagebox.showerror(self.engine.app_title,
                             "{0}\n\n{1}".format(val, self.engine.log.path),
                             parent=self)

    def on_exit(self, evt=None):
        """Close the database and go, once the question has been answered.

        The title bar carries the laboratory, the site and the name of the
        program, which is right where it is; a box asking one question does
        not need any of it. It asks the question.
        """
        if messagebox.askokcancel(self.engine.app_title, "Quit?", parent=self):
            self.engine.db.close()
            self.engine.log.trace("database closed: goodbye")
            self.destroy()
