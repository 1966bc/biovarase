# -*- mode: python ; coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""PyInstaller recipe. The build lives in a file, not in a command line.
#
# Run it with:
#
#     py -m PyInstaller --clean --noconfirm biovarase.spec
#
# One directory and not one file. A --onefile build unpacks itself into a
# temporary folder at every launch, which with Tk and reportlab is tens of
# megabytes each time; on a machine with an antivirus that is a fresh set of
# files to be scanned at every start. A directory starts at once, can be
# looked inside, and on the PC beside an instrument that difference is felt.
#
# It is also what the program expects: everything it reads at run time -
# biovarase.ini, the icon, LICENSE, the database - it finds beside itself
# through Engine.get_file, so the whole installation is one folder that can be
# copied, backed up and versioned as a unit.
#
# The sample database is NOT bundled. sql/biovarase.sl3 holds a laboratory's
# worth of invented results and has no business inside a program somebody is
# about to use for their own; sql/starter/biovarase.sl3 travels instead, which
# is the schema and the master data, and the DDL travels with it so that an
# installation whose database is lost can be rebuilt from the folder it lives
# in.
#
# And nothing but that ever goes into dist/. This build deletes and rewrites
# that directory - --clean --noconfirm is not a question - so a working
# installation left there would be destroyed by the next build. An
# installation is made by copying dist/Biovarase somewhere else.
"""

import os

from PyInstaller.utils.hooks import collect_submodules

# What has to be there at run time.
DATAS = [# The settings, read by Config at start-up. The copy that travels is
         # the one in the repository: whoever installs it writes their own
         # laboratory into it, and the database path if the file is elsewhere.
         ("biovarase.ini", "."),
         # The icon, as the lines of base64 the windows read.
         ("icon", "."),
         # The schema, so a database can be rebuilt where the program is.
         ("sql/ddl/*.sql", "sql/ddl"),
         ("sql/dml/*.sql", "sql/dml"),
         # The queries worth reading, which travel for the same reason the
         # schema does: an installation nobody can inspect is one nobody can
         # repair.
         ("sql/dql/*.sql", "sql/dql"),
         # A database to start from: the schema and the master data, with one
         # administrator and no results.
         ("sql/starter/biovarase.sl3", "sql/starter"),
         # Read by the About window and by the Licence window.
         ("LICENSE", ".")]

# Imported where they are used rather than at the top of a module - openpyxl
# only when a sheet is written, reportlab only when a form is printed - so
# that starting the program does not pay for either. PyInstaller does find
# imports inside functions; naming them here costs nothing and removes the
# question.
HIDDEN = collect_submodules("openpyxl") + collect_submodules("reportlab")

# What is on the build machine because something else needed it.
EXCLUDES = ["PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
            "matplotlib", "numpy", "pandas", "scipy", "sympy",
            "IPython", "jupyter", "notebook", "nbconvert",
            "pytest", "sphinx", "mariadb", "cryptography",
            "tkinter.test", "test", "lib2to3", "pydoc_data"]


analysis = Analysis(
    ["biovarase.py"],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN,
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False)

pyz = PYZ(analysis.pure, analysis.zipped_data)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Biovarase",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX compression is what an antivirus looks at twice
    console=False,      # a failure to start is shown in a dialog, not a shell
    icon="ui/biovarase.ico")

collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=False,
    name="Biovarase")
