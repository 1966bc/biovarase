# Biovarase — Conventions

The rules this code is written by.

## Rules

- **English in the code**: identifiers, comments, docstrings, interface. The
  conversation about the program happens in Italian; the program does not.
- **PEP 8**: 4 spaces, lines up to 100 columns, `lower_case_with_underscores`
  for functions and variables, `CapWords` for classes, `UPPER_CASE` for module
  constants.
- **Object-oriented**: the logic lives in classes, one responsibility each,
  and one class per module, named after it. Tests may keep their small
  stand-ins beside them.
- **Böhm–Jacopini**: only sequence, `if`, loops and assignments. One exit per
  function: no `return` in the middle, no `break`/`continue`. A function that
  needs several exits is doing several things and must be split. `raise` is
  allowed, for real errors only.
- **One thing per line**: a plain `if`/`else`, never `x if condition else y`.
- **DRY**: every piece of knowledge is written once. Two copies start
  identical, one gets fixed and the other does not: a list or a form repeated
  goes to a base class, a helper used twice goes to `Tools` or `DBMS`.
- **KISS and YAGNI**: the simplest solution that still reads clearly in two
  years; nothing written for an imagined future.
- **Least surprise**: a name promises what the code does, no more. A `get_*`
  returns and writes nothing, no hidden side effects. Windows that do similar
  things behave the same way.
- **Fail fast, fail safe, never silently**: on error stop near the cause and
  leave the database consistent. A failed read must not look like "no rows",
  and a statistic must never come back as 0.0 because something went wrong —
  a CV of zero and a CV that failed are indistinguishable to whoever reads it.
- **By hand where it teaches**: where a library is not really needed, a small
  class written by hand shows what it does underneath (`Log`, `Config`,
  `Events`, `Windows`), and its docstring names the library it stands in for.
- **Nothing is deleted**: a result is corrected, moved or excluded, never
  removed. What happened, happened, and a record that can be made to say
  otherwise is not a record.
- **No history in docstrings**: a docstring says what the thing does, not what
  it used to do. Whoever opens the file today has not followed the project
  from the beginning. The story of a change belongs in its commit message.

## Style

- File header block with `project: biovarase`, `authors: Giuseppe Costanzi
  (1966bc)`, `licence: GPL-3.0-or-later, see LICENSE`. No modification date:
  git keeps it per file. The release date, Latin season + Roman year (e.g.
  `autumnus MMXXVI`), lives once, in `__date__` next to `__version__` in
  `ui/app.py`.
- A shebang only on the file that is started, `biovarase.py`, and the
  executable bit with it. A module that announces itself as a program invites
  somebody to run it as one.
- Widget prefixes: `lst_`, `cb_`, `txt_`, `lbl_`, `frm_`, `btn_`, `ent_`,
  `chk_`.
- Widgets used often are built by `Tools`: `get_tree`, `get_listbox`,
  `get_combo` (readonly), `get_entry` (text, integer, float), `get_text`.
  Buttons come from `get_button_column`, given `(label, command)` pairs: it
  underlines the first free letter and binds it to Alt, on the window that has
  the keyboard focus and not on the frame.
- **No `__str__` on a widget.** Tk uses `str(widget)` as the widget's path
  name, so a class that overrides it becomes unusable as an argument:
  `parent=self` in a messagebox fails with `bad window path name`. Diagnostics
  go in a `get_state()` method, which nothing converts silently.
- A list window is a `ui.list_window.ListWindow`, a one-row form is a
  `ui.dialog.Dialog`. A window reaches the engine through `ui.window.Window`,
  which is a property and not a constructor argument.
- A window is built hidden (`tools.hide_me`) and shown in place
  (`tools.center_me`): a Toplevel is mapped the moment it is created, and
  without that it appears empty in a corner, fills in, and jumps.
- ttk styles (`App.*`, `StatusBar.TLabel`, …) are all defined in
  `Tools.set_style()`.
- `.format()` strings, not f-strings.
- Confirmations through `messagebox`, with the texts held by the engine
  (`ask_to_save`, `ask_to_delete`, `abort`, `no_selected`).

## The database

- **Dictionary access only**: `row["field"]`, never `row[0]`. A column added
  one day would silently change the meaning of every number.
- **Parameterised SQL**: always `?`, never string concatenation.
- **Statements built from the schema**: `db.get_insert(table, values)` and
  `db.get_update(table, key, values)` take the values keyed by column name and
  ask `PRAGMA table_info` which column is the key. Nothing depends on the
  order of the columns, and a missing or unknown column is refused, naming the
  table.
- **A query worth a name goes in `sql/dql/`**, as a file. A statement in a
  file can be read, reviewed and run at the shell; one in a Python string
  cannot.
