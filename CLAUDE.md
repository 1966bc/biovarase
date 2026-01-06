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

The `Engine` class combines specialized functionality through multiple inheritance:

```python
class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Launcher, Tools):
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
- Configuration files: accessed via `get_section_id()`, `get_ddof()`, `get_zscore()`
- Error logging: `on_log()` method

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

**Master windows** (singleton via `__new__()`):
- One instance only, list/tree-based views
- Register in `Engine.dict_instances`
- All in `frames/` directory

**Editor windows** (multiple instances allowed):
- Fresh instance each time
- Update parent via `self.parent._load_tree()` after save

**Cross-window refresh:** `self.engine.refresh_windows_for_table("table_name")`

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
5. **Singleton master windows** via `__new__()` pattern

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
- **Config encryption:** AES-256-GCM tied to hardware (MAC + machine-id)
- **Roles:** 0=Admin, 1=Superuser, 2=Technician, 3=Autologin (read-only)

## Notes for AI Assistants

- This is a **production system** in active use at medical laboratories
- **Data integrity is paramount** - QC data impacts patient safety decisions
- Follow **ISO 15189:2022** medical laboratory standards
- The codebase is in **active refactoring** (2025 rewrite)
- **Communication in Italian, code in English** - strictly enforced
- Reference `PROJECT_RULES.md` as the authoritative source when in doubt
