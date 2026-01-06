# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Biovarase** is a professional laboratory Quality Control (QC) management system for medical laboratories implementing ISO 15189:2022 standards. It tracks quality control samples, calculates statistical metrics (mean, SD, CV, bias, uncertainty), evaluates Westgard multirule violations, and generates Levey-Jennings control charts.

**Technology Stack:**
- Python 3.7+ with Tkinter (GUI framework)
- MariaDB 10.11+ (database)
- Dependencies: `mariadb`, `openpyxl`, `Pillow`, `bcrypt`

## Development Commands

```bash
# Run application
python3 biovarase.py              # Linux
py biovarase.py                   # Windows

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_westgards.py -v

# Run single test by name
pytest tests/test_qc.py::TestQC::test_get_mean_with_valid_series -v

# Run tests by marker
pytest -m critical -v             # Medical safety tests
pytest -m westgard -v             # Westgard rule tests
pytest -m security -v             # Security tests

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# Database setup
mysql -u root -p < schema.sql

# Apply migrations (in order)
mysql -u biovarase -p biovarase < migrations/001_add_foreign_keys_FIXED.sql

# Build standalone executable (Windows)
build_biovarase.cmd
```

## Architecture

### Mixin Pattern (Multiple Inheritance)

The `Engine` class combines specialized functionality through multiple inheritance.
Uses `_EngineMeta` metaclass to ensure only one instance exists (Singleton pattern).

```python
class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Launcher, Tools,
             metaclass=_EngineMeta):
    pass
```

**Mixin responsibilities:**
- `DBMS` (dbms.py) - Database connection, `read()`, `write()` methods
- `Controller` (controller.py) - SQL builders and domain logic
- `QC` (qc.py) - Statistical calculations (mean, SD, CV, bias, uncertainty)
- `Westgards` (westgards.py) - Westgard multirule QC evaluation
- `Exporter`/`Importer` - Data import/export
- `Tools` (tools.py) - Tkinter GUI utilities

**Engine manages:**
- Global state: `current_ids` (site_id, lab_id, section_id)
- Window registry: `dict_instances` (track open GUI windows)
- Observer pattern: `subscribe()`, `unsubscribe()`, `notify()` for decoupled view communication
- Configuration files: accessed via `get_section_id()`, `get_ddof()`, `get_zscore()`
- Error logging: `on_log()` method

**File path consistency:**
Always use `self.get_file("filename")` for config files to ensure consistent paths:
```python
# CORRECT - uses app directory
path = self.get_file("section_id")
with open(path, "w") as f: ...

# WRONG - uses current working directory (may differ!)
with open("section_id", "w") as f: ...
```

**Context switching (section/lab change):**
When changing section, update ALL hierarchical IDs:
```python
# Get all IDs for the new section
ids = self.engine.get_idd_by_section_id(new_section_id)
if ids:
    self.engine.current_ids.update(ids)  # Updates site_id, lab_id, section_id, etc.
```

### Observer Pattern (Event System)

Engine provides decoupled communication between views:

```python
# Subscribe to events in __init__:
self.engine.subscribe("batch_changed", self.on_batch_changed)

# Notify after changes:
self.engine.notify("batch_changed", batch_id)

# Unsubscribe in on_cancel() to avoid dead references:
self.engine.unsubscribe("batch_changed", self.on_batch_changed)
```

**Events:** `batch_changed`, `result_changed`, `section_changed`, `supplier_changed`, `equipment_changed`, `test_method_changed`

### Database Access Pattern

```python
# Dictionary-based result sets - NEVER use positional indexing
rows = self.engine.read(True, "SELECT * FROM tests WHERE enable = ?", (1,))
for row in rows:
    print(row["description"])  # Always dict key access, never row[0]

# Insert returning lastrowid
new_id = self.engine.write(True, "INSERT INTO batches (control_id) VALUES (?)", (id,))

# Update returning rowcount
affected = self.engine.write(False, "UPDATE results SET validated = 1 WHERE result_id = ?", (id,))
```

### GUI Window Types

**Base classes** (in `views/`):
- `ParentView` - Singleton master windows with anti-flash
- `ChildView` - Editor dialogs with auto-registration

**ParentView pattern (master windows):**
```python
class UI(ParentView):
    def __init__(self, parent):
        super().__init__(parent, name="myview")
        if self._reusing:  # Singleton reuse - skip rebuild
            return
        # ... build UI ...
        self.show()

    def on_cancel(self, evt=None):
        # cleanup...
        super().on_cancel()  # Clears _instance
```

**ChildView pattern (editor dialogs):**
```python
class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="myeditor")
        self.index = index  # Primary key or None for INSERT
        # ... build UI ...
        self.show()

    def on_cancel(self, evt=None):
        # cleanup...
        super().on_cancel()  # Unregisters from dict_instances
```

**Window positioning:**
- `self.show()` - Center on parent (default)
- `self.show(on_screen=True)` - Center on screen

**Cross-window updates:**
```python
# Via registry (master windows):
win = self.engine.dict_instances.get("batches")
if win and win.winfo_exists():
    win._load_tree()

# Via observer (preferred):
self.engine.notify("batch_changed", batch_id)
```

## Project Rules

### Mandatory Reading at Session Start
1. `PROJECT_RULES.md` - Authoritative development rules
2. `BEST_PRACTICES.md` - SOLID principles and design patterns

### Language Policy
- **Communication:** Italian (discussions, explanations, feedback)
- **Code:** English (variables, functions, comments, docstrings, commits)

### Critical Constraints

1. **No positional indexing** - Use `row["field"]`, never `row[0]`
2. **Parameterized SQL only** - Always use `?` placeholders, never string concatenation
3. **No direct file I/O from GUI** - Use Engine helper methods
4. **Log all exceptions** via `self.on_log()`
5. **No bare `except:`** - Always catch specific exceptions

### Error Handling Pattern

```python
try:
    # operation
except Exception as e:
    self.on_log(
        inspect.stack()[0][3],      # function name
        sys.exc_info()[1],           # exception value
        sys.exc_info()[0],           # exception type
        sys.modules[__name__]        # module
    )
```

### Role-Based Access Control

```python
# Permission helpers in Engine:
self.engine.can_validate_qc()      # Admin (0) or Superuser (1)
self.engine.can_configure_system() # Admin (0) only
self.engine.can_modify_data()      # Admin, Superuser, or Technician (0-2)
self.engine.is_read_only()         # Autologin (3) or higher
```

## QC Domain Knowledge

### Westgard Multirule Evaluation Order
1. **1:3S** - Single value > 3SD (reject immediately)
2. **2:2S** - Two consecutive > 2SD same side
3. **R:4S** - Range of 2 values >= 4SD
4. **4:1S** - Four consecutive > 1SD same side
5. **10:X** - Ten consecutive same side of mean
6. **1:2S** - Single value > 2SD (warning only)

**Minimum series length:** 10 values required, otherwise return "NED"

### Configuration Files
- `ddof` - Degrees of freedom (0 or 1) for SD calculation
- `zscore` - Coverage factor (1.96 = 95% CI)
- Access via Engine: `self.engine.get_ddof()`, `self.engine.get_zscore()`

## Security

- **Passwords:** bcrypt with cost factor 12
- **Config encryption:** Fernet (AES-128-CBC) tied to hardware (MAC + machine-id)
- **Roles:** 0=Admin, 1=Superuser, 2=Technician, 3=Autologin (read-only)

## Notes for AI Assistants

- This is a **production system** in active use at medical laboratories
- **Data integrity is paramount** - QC data impacts patient safety decisions
- Follow **ISO 15189:2022** medical laboratory standards
- **Communication in Italian, code in English** - strictly enforced
- Reference `PROJECT_RULES.md` as the authoritative source when in doubt
