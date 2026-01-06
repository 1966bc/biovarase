# Biovarase - Session Context Summary

**Read this file at the start of each new Claude Code session for project context**

## Project Overview

**Biovarase** is a laboratory quality control (QC) management system for clinical laboratories.
- **Version:** 4.2 (Professional Edition - Full Rewrite 2025)
- **Author:** 1966bc (Giuseppe Costanzi)
- **License:** GNU GPL v3
- **Tech Stack:** Python 3.11, Tkinter (GUI), MariaDB 10.11+
- **Purpose:** Manage laboratory QC data, Westgard rules, analytical goals, batch tracking, and multi-site lab operations

## Architecture (CRITICAL - Read First!)

The project follows a **strict architectural pattern** defined in `PROJECT_RULES.md`:

### Core Components
1. **Engine** (`engine.py`) - Main orchestrator combining all mixins
   - Holds global context (`current_ids`) for multi-site operations
   - Manages window registry (`dict_instances`)
   - Coordinates cross-component communication

2. **DBMS** (`dbms.py`) - Database connection layer
   - Handles MariaDB connections with auto-reconnect
   - Provides `read_dict()`, `read()`, `write()` methods
   - No business logic allowed

3. **Controller** (`controller.py`) - SQL builder + domain logic
   - Extends DBMS
   - Builds SQL queries
   - Returns dictionaries (never tuples)
   - GUI-independent

4. **Mixins** - Specialized functionality
   - `QC` - Quality control computations
   - `Westgards` - Westgard rules evaluation
   - `Exporter` / `Importer` - Data import/export
   - `Launcher` - File opening
   - `Tools` - Shared utilities

5. **GUI** (`frames/`) - Tkinter windows
   - Master windows: Singleton list/tree views
   - Editor windows: Non-singleton edit forms
   - All opened via `engine.on_open()`

### Key Design Rules (FROM PROJECT_RULES.md)

**MANDATORY:**
- All DB queries use `engine.read_dict()` - NO `row[0]` indexing
- All SQL uses placeholders (`WHERE field = ?`) - NO string concatenation
- Multi-site filtering: Always filter by `site_id`, `lab_id`, `section_id`
- GUI windows NEVER read/write files directly - use Engine methods
- Master windows are singletons, editors are not
- All errors logged via `self.on_log()`

**FORBIDDEN:**
- Positional tuple indexing (`row[0]`)
- SQL string concatenation
- Direct parent-chain navigation (`self.parent.parent`)
- Multiple instances of master windows
- Business logic in Tkinter callbacks

## Database

- **DBMS:** MariaDB 10.11+
- **Connection:** Via `config.txt` (user/password/database/host)
- **Schema:** Multi-site laboratory structure (sites → labs → sections)
- **Status:** Most improvements applied (CHECK constraints, indexes, DECIMAL types, etc.)
- **Pending:** Foreign key constraints (see `migrations/README.md`)

## Project Structure

```
biovarase/
├── biovarase.py          # Entry point (launches login)
├── engine.py             # Main orchestrator
├── dbms.py               # Database layer
├── controller.py         # SQL builder + domain logic
├── qc.py                 # QC computations
├── westgards.py          # Westgard rules
├── exporter.py/importer.py
├── launcher.py           # File opening
├── tools.py              # Utilities
├── frames/               # All GUI windows
│   ├── main.py          # Main application window
│   ├── login.py         # Login window
│   ├── batches.py       # Batch management
│   ├── result.py        # QC results
│   └── [50+ other windows]
├── migrations/           # Database migration scripts
├── sql/                  # SQL scripts
├── qc/                   # QC data files
├── imports/              # Import data
├── backups/              # Database backups
├── config.txt            # DB credentials
└── PROJECT_RULES.md      # **AUTHORITATIVE development rules**
```

## Configuration Files

The app uses simple text files (one value per line):
- `section_id` - Current lab section
- `ddof` - Degrees of freedom for statistics
- `zscore` - Z-score threshold
- `loop` - Polling interval
- `remember_batch` - Batch persistence flag
- `autologin` - Auto-login flag
- And more...

Access via `engine.get_section_id()`, `engine.get_ddof()`, etc. - NEVER read directly!

## Common Development Patterns

### Opening a Window
```python
self.engine.on_open("window_name", WindowClass, parent=self)
```

### Database Query
```python
sql = """SELECT test_id, description
         FROM tests
         WHERE section_id = ? AND enable = 1"""
rows = self.engine.read_dict(True, sql, (section_id,))
for row in rows:
    print(row["test_id"], row["description"])  # NOT row[0], row[1]
```

### Updating Another Window
```python
# Update master window via registry
win = self.engine.dict_instances.get("batches")
if win and win.winfo_exists():
    win._load_tree()

# Update parent from editor
self.parent._load_tree()
self.parent._set_index(record_id)
```

## Code Review & Refactoring Plan

**IMPORTANT:** The project has a defined list of Python files requiring code review and refactoring for 100% PROJECT_RULES.md compliance.

### Reference File
- **`PROJECT_FILE_TO_CONTROL.md`** - Contains ~66 essential Python files to review

### Scope
This file lists all core Python modules that need:
- ✅ **Code Review** - Check compliance with PROJECT_RULES.md
- ✅ **Refactoring** - Modernize to project standards
- ✅ **Type Hints** - Add Python 3.7+ type annotations
- ✅ **Documentation** - English docstrings (Google Style)
- ✅ **Quality Check** - PEP 8, security, error handling

### Categories Covered
- Root Directory: 16 core files (engine.py, dbms.py, controller.py, qc.py, etc.)
- frames/: 50 GUI windows (master, editor, specialized, analysis)

### Priority
Start with core files (engine, dbms, controller) then proceed to GUI frames.

### Status
- ✅ **frames/login.py** - Refactored 2025-11-30 (100% compliant)
- ⏳ Remaining 65 files pending review

**Read `PROJECT_FILE_TO_CONTROL.md` to see complete list of files requiring attention.**

---

## Current Focus / Recent Work

- Database migrations (foreign keys pending)
- Code modernization following PROJECT_RULES.md
- Multi-site functionality
- QC computations and Westgard rules
- **NEW:** Security implementation (hardware-locked credentials encryption)

## Important Notes

1. **ALWAYS read PROJECT_RULES.md when making changes** - it's authoritative
2. Code quality: PEP 8, type hints, English comments/docstrings
3. Security: No hardcoded passwords, parameterized queries only
4. Logging: All exceptions logged via `on_log()`
5. Keep it KISS (Keep It Simple, Stupid) and DRY (Don't Repeat Yourself)

## Quick Start Commands

```bash
# Run the application
python3 biovarase.py

# Database backup
mysqldump -u biovarase -p biovarase > backups/backup_$(date +%Y%m%d).sql

# Apply pending migrations
mysql -u biovarase -p biovarase < migrations/001_add_foreign_keys.sql
```

## Key Files to Reference

- `PROJECT_RULES.md` - **Read this for ANY architectural questions**
- `SESSION_CONTEXT.md` - This file (quick project overview)
- `PROJECT_FILE_TO_CONTROL.md` - **Files requiring code review/refactoring**
- `PROJECT_FILE_INVENTORY.md` - Complete file structure inventory
- `CHANGELOG.md` - **Project change history and logbook**
- `DATABASE_CREDENTIALS_SECURITY.md` - Security implementation decision (NEW 2025-11-30)
- `engine.py` - Understand the Engine class
- `frames/main.py` - Main application window
- `migrations/README.md` - Database migration status
- `config.txt` - Database credentials (TO BE REPLACED with config.enc)

---

## Maintaining the Changelog

When making changes to the project:
1. **Document in CHANGELOG.md** using the provided template
2. Include: date, files changed, what/why, technical details
3. Create timestamped backups for significant changes
4. Note any breaking changes or migration requirements

---

**When starting a new session:** Read this file + PROJECT_RULES.md to get full context.
