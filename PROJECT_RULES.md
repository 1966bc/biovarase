Biovarase – Project Development Rules
Professional Edition (Full Rewrite – 2025)
1. Purpose and Scope

This document defines the official development rules for the Biovarase project.
It acts as the authoritative reference for:

software architecture

class responsibilities

database access patterns

Tkinter GUI conventions

quality control (QC) computations

error logging

multi-site behavior

coding style and naming conventions

forbidden practices

All development must follow this document.

2. Terminology

MUST → mandatory requirement

SHOULD → recommended best practice

MUST NOT → explicitly forbidden

Engine → main orchestrator class

DBMS → database handler class

Controller → SQL builder and domain logic

GUI / Window / Toplevel → Tkinter interface components

Master window → list/tree-based main view

Editor window → child window used to edit or insert a record

3. Core Principles
3.1 KISS — Keep It Simple, Stupid

The project MUST remain simple, predictable, and linear.

3.2 DRY — Don’t Repeat Yourself

Repeated logic MUST be moved into Engine, Controller, DBMS, or Tools.

3.3 Fail Fast / Fail Safe

On error, operations MUST stop immediately and record the issue via on_log().

3.4 Readability First

Code MUST be understandable without opening another file.

3.5 PEP 8 Compliance

All Python code MUST follow PEP 8 guidelines.

3.6 Comments and Docstrings — (Strengthened Rule)

All comments and docstrings MUST be written in clear, professional English.
This includes:

class docstrings

method/function docstrings

inline comments

module headers

TODO / FIXME notes

logging messages

Comments MUST explain why a decision is made, not mechanically restate the code.

4. Language Policy / Politica Linguistica

**Communication Language:** Italian (Italiano)

All discussions, explanations, architectural decisions, and human communication
with the development team MUST be conducted in Italian.

This includes:

- Design discussions
- Code reviews and feedback
- Technical explanations
- Requirements clarification
- Problem-solving conversations
- Project planning

**Code Language:** English

All code artifacts MUST remain in English to maintain international standards.

This includes:

- Variable names, function names, class names
- Docstrings and code comments
- Commit messages
- Technical documentation
- Error messages and logging
- Database schema and column names
- Configuration file names

**Rationale:**

Italian enables natural, nuanced communication among team members and facilitates
better understanding of subtle requirements and design decisions.

English in code ensures the project remains accessible to international developers
and follows industry-wide conventions.

**Example:**

```python
# CORRECT: English code, Italian discussion
def calculate_westgard_rule(target: float, sd: float, series: List[float]) -> str:
    """Calculate Westgard QC violation rule for given series."""
    # Discussion: "Questa funzione implementa le regole di Westgard..."
    pass

# INCORRECT: Mixed languages in code
def calcola_regola_westgard(obiettivo: float, ds: float, serie: List[float]) -> str:
    pass
```

5. File System Rules

Biovarase uses several configuration files (section_id, ddof, zscore, loop, remember_batch, icon, manual, bvv, dimensions, etc.).

5.1 File Format

Each configuration file MUST contain one value per line.

No JSON, lists, dictionaries or binary content.

5.2 File Access

Files MUST be read only through Engine helper methods such as:

get_section_id()

get_ddof()

get_zscore()

get_loop()

get_observations()

5.3 Error Handling

Any file I/O failure MUST be logged using self.on_log().

5.4 GUI Restrictions

GUI windows MUST NOT read or write configuration files directly.

6. Database Access Rules
6.1 Mandatory use of read()

All SELECT queries MUST use:

self.engine.read(fetch, sql, args)

6.2 No positional indexing

Forbidden:

row[0]
row[1]


Correct:

row["test_method_id"]
row["description"]

6.3 SQL Safety

Placeholders MUST always be used:

WHERE field = ?


Manual string concatenation MUST NOT be used.

Queries MUST be enclosed in triple quotes """ ... """.

Queries SHOULD avoid SELECT * except for legacy compatibility.

6.4 Multi-site filtering

Every SQL statement MUST filter by:

site_id

lab_id

section_id

whenever logically required.

7. Architecture: Engine / Controller / DBMS
7.1 DBMS

DBMS MUST:

handle connection setup and reconnection (_ensure_connection())

provide:

read()

write()

contain no domain logic

implement full logging on error

7.2 Controller

Controller MUST:

extend DBMS

build SQL

implement domain logic only

return dictionaries, not tuples

remain free of GUI dependencies

7.3 Engine

Engine MUST:

combine DBMS, Controller, QC, Westgards, Tools, Launcher, Exporter, Importer

keep the global context (current_ids)

store active windows in:

self.dict_instances


expose shared utilities (logging, busy-state, file resolving, etc.)

mediate all cross-window communication

NEVER assume the existence of mixin attributes not defined consistently

7.4 Mixin Integrity Rule

Mixin classes (QC, Westgards, Exporter, Importer, Tools, Launcher) MUST NOT:

depend on GUI widgets

depend on attributes created in other mixins

create or store global state

write files except during export operations

8. Tkinter GUI Rules
8.1 Window Lifecycle
Master windows:

MUST be singletons

MUST implement:

def _load_tree(self): ...
def _set_index(self, id): ...

Editor windows:

MUST NOT be singletons

MUST be freshly instantiated each time

Window opening:

All windows MUST be opened using:

on_open()


Not via direct constructor calls deep inside other classes.

Window registry:

Each window MUST register itself:

self.engine.dict_instances[self.winfo_name()] = self


On closing:

self.engine.dict_instances.pop(self.winfo_name(), None)

8.2 Layout Rules

Master windows MUST use pack().

Editors MUST use grid().

Split views SHOULD use PanedWindow.

8.3 Reload & Reselect Pattern

After saving an edited record:

parent._load_tree()
parent._set_index(last_id)

8.4 Naming Conventions

GUI callback functions MUST be on_action().

Private methods inside Toplevel windows SHOULD start with _:

_load_tree()

_get_values()

_set_values()

_set_index()

9. Coding Standards
9.1 Naming

snake_case → variables and functions

PascalCase → classes

ALL_CAPS → constants

Valid boolean names → is_x, has_x, can_x

9.2 Type Hints

Type hints SHOULD be used throughout all new code.

9.3 Function Size

Functions MUST remain short and readable.

9.4 Comments

Comments MUST explain why, not what.

9.5 Maximum Line Length

Lines SHOULD be 100 characters or less.

10. Quality Control (QC / Westgard / Youden)
10.1 Separation of Concerns

QC computations MUST:

remain pure functions

avoid GUI code

avoid side effects

accept and return primitive structures (lists, floats, dicts)

10.2 Minimum Series Length

Westgard rules MUST only be evaluated when:

len(series) ≥ 10


Otherwise return "NED".

10.3 Graph Rules

Graphs MUST include axis labels

Date labels MUST remain readable

Excess whitespace MUST be avoided

11. Logging Rules
11.1 Mandatory Logging

Every caught exception MUST call:

self.on_log(function, exc_value, exc_type, module, caller)

11.2 Log Content

Logs MUST include:

ISO datetime timestamp

class.method

caller (if available)

exception type + message

full traceback

11.3 Logging MUST NOT fail

Logging errors must never interrupt execution.

12. Security Rules

SQL placeholders MUST be used everywhere

User input MUST be validated

Plain-text passwords MUST NOT exist in code

Sensitive data MUST NOT be logged

System paths MUST NOT be hard-coded

13. File Launcher Rules
13.1 File Opening

Files MUST be opened using:

self.launch(path)


GUI windows MUST NOT invoke os.startfile() or xdg-open() manually.

14. Mandatory Editor Behavior

Editors MUST NOT:

rebuild toolbar/buttons on each refresh

re-create widgets unnecessarily

perform database writes without validation

Editors MUST:

validate data using:

self.engine.on_fields_control(self)


only write changes after explicit user confirmation (Save button)

15. Removal of Dead Code

Legacy, unused, duplicated, or unreachable code MUST be removed during refactoring.

16. Forbidden Practices (Anti-Patterns)
16.1 MUST NOT

Positional tuple indexing (row[0])

Multiple instances of master windows

Calling on_open() inside __init__()

Direct access to parent widgets (self.parent.parent.xyz)

SQL string concatenation

Hidden global state

Data-model manipulation inside the GUI

Editor-to-editor direct communication without Engine mediation

Embedding business logic inside Tkinter callbacks

16.2 Strongly Discouraged

excessively long functions

lambdas containing business logic

redesigning widget trees inside loops

duplicating SQL across multiple windows

17. Multi-Site Laboratory Rules
17.1 Context Handling

The hierarchical identifiers:

site_id

supplier_id

comp_id

lab_id

section_id

MUST always be retrieved through:

self.engine.current_ids

17.2 Query Requirements

All multi-site queries MUST filter by these identifiers when necessary.

17.3 Cross-Window Updates

Updating another window MUST be done through:

win = self.engine.dict_instances.get("batches")
if win and win.winfo_exists():
    win._load_tree()


Not through parent chains.

17.4 Parent-Chain vs Registry — Mandatory Rule (NEW)

Editor windows MUST update only their direct parent, using:

self.parent._load_tree()
self.parent._set_index(record_id)


because the parent–child relationship is deterministic and stable.

Master windows MUST be updated through the Engine registry:

win = self.engine.dict_instances.get("window_name")
if win and win.winfo_exists():
    win._load_tree()


because they are singletons, can be opened or closed independently,
and MUST NOT be referenced via parent chains.

Parent chains such as:

self.parent.parent...
self.master.master...


are FORBIDDEN.

18. Evolution of This Document
18.1 Rule Updates

Any architectural change MUST be reflected in this document.

18.2 Code Evolution

As Biovarase grows, rules MUST evolve to maintain consistency, clarity, and safety.

18.3 CHANGELOG Documentation (MANDATORY)

Every code change MUST be documented in CHANGELOG.md.

This includes:

file refactoring

bug fixes

new features

database migrations

architectural changes

dependency updates

configuration changes

Documentation MUST include:

Date in [YYYY-MM-DD] format

Clear title describing the change

Category: Added / Changed / Fixed / Removed

File(s) modified with backup timestamp

Reason for the change

Impact and benefits

Technical details (before/after code examples)

Breaking changes or migration steps

Format example:

### [YYYY-MM-DD] - Brief Description of Change

#### Changed
- **file.py**: What was changed and why
  - **Reason**: Why this change was necessary
  - **Impact**: What effect it has on the system
  - **Backup**: `file.py.bak.[timestamp]`

  **Details**:
  - Bullet point list of specific changes
  - Code examples showing before/after

  **Benefits**:
  - ✅ Benefit 1
  - ✅ Benefit 2


Exception: Only trivial changes like typo fixes in comments MAY skip CHANGELOG if they don't affect functionality.

19. User Interface Guidelines

This project follows platform Human Interface Guidelines where applicable.

19.1 References

- **Primary**: GNOME Human Interface Guidelines (https://developer.gnome.org/hig/)
- **Secondary**: Windows UX Guidelines (https://learn.microsoft.com/en-us/windows/win32/uxguide/guidelines)

19.2 Key Principles

1. **Consistency**: Same patterns across all windows
2. **Feedback**: Immediate visual response to user actions
3. **Error Prevention**: Validate before destructive actions
4. **Clear Language**: Action verbs for buttons (Add, Save, Cancel)
5. **Keyboard Navigation**: All actions accessible via keyboard
6. **Forgiveness**: Confirm before delete, allow undo where possible

19.3 Biovarase-Specific Conventions

- Date format: Italian `dd-mm-yyyy`
- Window titles: descriptive with context (e.g., "Notes - TestName")
- Lists: date left-aligned, numbers right-aligned
- Colors: red (>3SD), orange (>2SD), gray (disabled), yellow background (has notes)
- No bold fonts in labels, use `ttk.Label` standard style

20. Final Rule

If a developer can understand a piece of code without opening another file, then it is correct.