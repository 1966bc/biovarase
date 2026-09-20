#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Start Biovarase.

    python3 biovarase.py            start it
    python3 biovarase.py --trace    start it, and print on the terminal what it
                                    does and what its variables hold

To see where the time goes, the standard library's profiler runs it as it is,
without a line of code here:

    python3 -m cProfile -s cumulative biovarase.py
"""

import os
import sys
from tkinter import messagebox

from log import Log
from ui.app import App

#: The folder of this file: the log and the database live here, beside the
#: program, so it can be started from any folder.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

#: The options the program knows. Anything else is refused, not ignored.
OPTIONS = ("--trace",)


def main():

    # The options, read by hand: sys.argv[0] is the program, the rest is ours.
    options = sys.argv[1:]
    unknown = [option for option in options if option not in OPTIONS]
    if unknown:
        raise SystemExit("unknown option: {0}\nusage: python3 biovarase.py [--trace]".format(
            " ".join(unknown)))

    # The log comes first, so that even a failure to start is written down.
    log = Log(os.path.join(PROJECT_DIR, "biovarase.log"), "--trace" in options)
    log.trace("options = {0}".format(options))

    # Before the main loop there is no report_callback_exception yet: a failure
    # here is written to the log, shown, and raised again.
    try:
        app = App("Biovarase", log)
    except Exception as exc:
        log.exception("start failed: {0}".format(exc))
        messagebox.showerror("Biovarase", "{0}\n\n{1}".format(exc, log.path))
        raise

    app.mainloop()


if __name__ == "__main__":
    main()
