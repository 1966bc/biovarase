# Building an executable

The program runs from its folder with Python installed, which is how it is
developed and how it runs on Linux:

    python3 biovarase.py

On the PC beside an instrument there is often no Python and no way to put one
there, so the program is frozen into an executable with PyInstaller. The
recipe is `biovarase.spec`, which is a file and not a command line: what goes
into the build, and why, is written down where the next person will look.

    py -m pip install pyinstaller
    py -m PyInstaller --clean --noconfirm biovarase.spec

What comes out is `dist/Biovarase`, a folder. **An installation is a copy of
that folder somewhere else** - `--clean --noconfirm` deletes and rewrites
`dist/`, so a working installation left there is destroyed by the next build,
with the database inside it.

## One directory, not one file

`--onefile` produces a single executable that unpacks itself into a temporary
folder at every launch. With Tk and reportlab that is tens of megabytes each
time, and on a machine with an antivirus it is a fresh set of files to be
scanned at every start. A directory starts at once, can be looked inside when
something is wrong, and can be backed up as a unit.

It is also what the program expects. Everything it reads at run time - the
settings, the icon, the licence, the database - it finds beside itself, so
the whole installation is one folder that can be copied, versioned and
restored without anybody knowing where Python keeps things.

## What travels, and what does not

`biovarase.ini` travels, and whoever installs the program writes their own
laboratory into it, and the path of the database if the file lives elsewhere -
on a shared folder, for instance.

The schema, the master data and the named queries travel: an installation
whose database cannot be rebuilt from the folder it lives in is one nobody can
repair.

`sql/starter/biovarase.sl3` travels: the schema and the master data, one
administrator, no results. It is what a new installation starts from.

**The sample database does not.** `sql/biovarase.sl3` holds a laboratory's
worth of invented results, and it has no business inside a program somebody is
about to use for their own.

## After the build

1. Copy `dist/Biovarase` where it is to live.
2. Copy `sql/starter/biovarase.sl3` to `sql/biovarase.sl3` inside the copy, or
   point `[database] file` in `biovarase.ini` at the database it should open.
3. Start it, log in as `admin` with `pass`, and change that password before
   anything else.
