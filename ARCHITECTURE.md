# Biovarase — Architecture

How the program is put together, and why.

## One laboratory

There is no tenant column anywhere. No `organizations`, no `lab_id`, no
`section_id`, no hierarchy of country, region, site, laboratory and section:
**the database is the laboratory**. Whose laboratory it is lives in three
lines of `biovarase.ini`, because with one of them it is a setting and not a
table.

Everything follows from that. A query is the query, not the query plus a
filter somebody might forget. There are two roles instead of seven. The
window that asked which laboratory to open does not exist.

## The engine owns its parts

```python
class Engine:
    def __init__(self, log):
        self.log = log
        self.config = Config(self.get_file("biovarase.ini"))
        self.db = DBMS(self.get_database(), log)
        self.tools = Tools()
        self.qc = QC(self.config)
        self.westgards = Westgards()
        self.exporter = Exporter(self)
        self.report = Report(self)
        self.events = Events(log)
        self.windows = Windows(log)
```

Composition, each part an attribute: a call says who does the work —
`engine.db.read(...)`, `engine.qc.get_mean(...)`, `engine.tools.center_me(...)`
— and each part can be built and tested on its own, which is what the tests
do with a database in memory.

What is left in the engine itself is what belongs to nobody else: who is
logged in, where the files are, the period the windows look back over, and
the few questions about this laboratory that are asked from more than one
window.

## The parts

| | |
|---|---|
| `Log` | one file, one entry per event; rotates at a megabyte, keeps three |
| `Config` | an `.ini` read line by line, and written back one line at a time |
| `DBMS` | the connection, `read`, `write`, and statements built from the schema |
| `Tools` | the widgets, the styles, the validation, the cursor |
| `QC` | the statistics of a series and the goals it is held to |
| `Westgards` | the multirule, one method per rule |
| `Exporter` | sheets |
| `Report` | the forms that get signed |
| `Events` | the Observer |
| `Windows` | one open window per name |

Four of them — `Log`, `Config`, `Events`, `Windows` — are written by hand
where the standard library has a module that would do it. This is a program
to be read as well as run, and forty lines show what `logging`,
`configparser` and an event bus do underneath. Each docstring names the
library it stands in for.

## Errors rise to one net

A failed statement is written to the log and raised again. It never comes
back as `None` or as an empty list: a read that fails must not look like a
table with no rows in it, because that is how a laboratory ends up believing
a control was never run.

What catches them is `App.report_callback_exception`. Tkinter calls it for
every exception raised inside a callback — a button, a menu, an `after()` —
so there is one place where an error is logged with its traceback and shown,
and the program carries on.

## The Observer

Whoever changes something says so; whoever shows it is told. The window that
saves a result does not know that a chart is open on that lot.

```python
engine.events.subscribe("results", self.on_results_changed)   # window opens
engine.events.notify("results", result_id)                    # row is saved
engine.events.unsubscribe("results", self.on_results_changed) # window closes
```

The events are named after the tables, and a name not in `Events.NAMES` is
refused where it is written: a typo in a `notify` would otherwise be an event
nobody ever hears, which is a bug that looks like nothing at all.

`notify` is synchronous. A window that reads its own dictionaries after
calling it may find them already cleared by a callback, so whatever is needed
goes into a variable first.

A window that subscribes and forgets to unsubscribe is called after it has
been destroyed, and the error lands on whoever saved. `tests/test_windows.py`
opens the real windows, closes them, and checks that nobody is left
listening.

## One window per name

`Windows` is a register: `show(name, build)` brings the one open to the
front, `replace(name, build)` closes it through its own `on_cancel` and
builds a new one. `build` is a function and not a window, so when the answer
is "it is already open" nothing is built.

The textbook Singleton — override `__new__` and hand back the instance — was
what the views used to do, and Python then calls `__init__` again on the
instance it just returned, so every window had to begin by asking whether it
was being reused. A register does the same thing in plain sight.

## The schema

Eighteen tables. Master data (`tests`, `units`, `samples`, `methods`,
`categories`, `suppliers`, `equipments`, `controls`, `actions`), the
laboratory (`users`, `session`, `workstations`, `test_methods`), the work
(`batches`, `results`, `notes`) and the audit (`audit_results`,
`audit_batches`).

Two distinctions carry most of the model.

**An analyte and a method are two things.** `tests` is the substance;
`test_methods` is how this laboratory measures it — the matrix, the method,
the unit, the goals. Cocaine in urine, in keratin and in blood is one
substance and three methods, with three units and three sets of goals.

**A lot is a series.** `batches` is a lot of control material on one analyte
and one instrument, with the target and the standard deviation the chart is
drawn against. Two levels of the same control are two lots, and the same
analyte on two benches is two more.

## The audit trail

Six triggers, on `results` and `batches`, for insert, update and delete. An
insert keeps the new row; an update and a delete keep the row **as it was**.
Put the rows of one result in order and its whole life is there, including
the values it used to have.

SQLite has no `CURRENT_USER`, so the login writes the user into `session` —
one row, enforced by a `CHECK` — and the triggers read it from there. In the
open, where it can be read, rather than hidden in a driver.

Nothing in the program deletes a result. The delete trigger is there because
somebody can always reach the file with `sqlite3`, and that is the case an
audit trail is for.

## The two halves of quality

`qc.py` and `westgards.py` are about the laboratory against itself: a series,
its own target, the rules read on it. `eqa.py` is about the laboratory
against everybody else, and it is a separate module for a reason that is not
tidiness. The two must not borrow from each other — the whole value of a
proficiency score is that nothing in it comes from the laboratory's own
target, and a shared function would be the beginning of that going wrong.

It holds three formulae and the thresholds of ISO 13528, and it knows nothing
about the database: it is handed numbers.

## The charts

Six canvases, drawn by hand on `tk.Canvas`: Levey-Jennings, the profile
beside it, Youden, total error, Bland-Altman and the frequency histogram. No plotting
library, which is why the program has three dependencies and starts instantly
on a slow machine — and why a reader can see how a control chart is built,
from the scale to the clipping of points beyond four standard deviations.

`tk.Canvas` deserves its reputation. It is a retained-mode surface: every
line, rectangle, polygon and string is an item it remembers and can be asked
about afterwards, which is what makes a double click on a point find the
result behind it without any hit-testing code worth the name. It has been
there, unchanged, since Tk — and everything above it here is arithmetic that
a reader can check.

Each one has the same shape: a `draw_*` method that takes numbers, a
`redraw` that decides whether there is room for a chart, an empty grid or
nothing, and a handful of `get_x` / `get_y` that turn a value into a
coordinate. None of them knows the database exists.

One of the seven depends on another, and it is the only one that does.
`ProfileCanvas` reads its margins, its scale and its colours off
`LeveyJenningsCanvas` instead of having its own. That is the point of it: it
is drawn beside the chart and is meaningless anywhere else, and a profile
that chose its own limits would line up with nothing. A margin changed on
the chart and not on the profile would slide the bars against the bands by a
few pixels - the kind of wrong nobody notices and nobody can then trust.
