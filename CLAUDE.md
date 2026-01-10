# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Biovarase** is a professional laboratory Quality Control (QC) management system for medical laboratories implementing ISO 15189:2022 standards. It tracks quality control samples, calculates statistical metrics (mean, SD, CV, bias, uncertainty), evaluates Westgard multirule violations, and generates Levey-Jennings control charts.

**Technology Stack:**
- Python 3.7+ with Tkinter (GUI framework)
- MariaDB 10.11+ (database)
- Dependencies: `mariadb`, `openpyxl`, `Pillow`, `bcrypt`, `cryptography`

**Author:** Giuseppe Costanzi (1966bc) - giuseppecostanzi@gmail.com

## Language Policy

- **Communication:** Italian (discussions, explanations, feedback)
- **Code:** English (variables, functions, comments, docstrings, commits)

## Development Commands

```bash
# Run application
python3 biovarase.py              # Linux
py biovarase.py                   # Windows

# Run all tests
pytest tests/ -v

# Run tests by marker
pytest -m critical -v             # Medical safety tests
pytest -m westgard -v             # Westgard rule tests
pytest -m security -v             # Security tests
pytest -m qc -v                   # QC statistical tests

# Run single test
pytest tests/test_qc.py::TestQC::test_get_mean_with_valid_series -v

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# Database setup (initial)
mysql -u root -p < biovarase.sql

# Build Windows executable (from Windows)
build_biovarase.cmd               # Output: dist/biovarase.dist/biovarase.exe
```

## Architecture

### Mixin Pattern (Singleton Engine)

```python
class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Launcher, Tools,
             metaclass=_EngineMeta):
    pass
```

| Mixin | File | Responsibility |
|-------|------|----------------|
| `DBMS` | dbms.py | Database connection, `read()`, `write()` |
| `Controller` | controller.py | SQL builders, domain logic |
| `QC` | qc.py | Statistical calculations (mean, SD, CV, bias) |
| `Westgards` | westgards.py | Westgard multirule QC evaluation |
| `Exporter`/`Importer` | exporter.py, importer.py | Data import/export |
| `Tools` | tools.py | GUI utilities, helper methods |
| `Launcher` | launcher.py | File opening |

### Engine Manages

- **Global state:** `current_ids` (site_id, lab_id, section_id)
- **Window registry:** `dict_instances` (track open GUI windows)
- **Observer pattern:** `subscribe()`, `unsubscribe()`, `notify()`
- **Config files:** `get_section_id()`, `get_ddof()`, `get_zscore()`
- **Logging:** `on_log()` method

### Multi-Site Hierarchy

Data hierarchy: **Site → Lab → Section → Workstation → Batch → Result**

```python
self.engine.current_ids = {
    "site_id": 1, "lab_id": 1, "section_id": 1,
    "supplier_id": 1, "comp_id": 1
}
```

### Database Access Pattern

```python
# Dictionary-based results - NEVER positional indexing
rows = self.engine.read(True, "SELECT * FROM tests WHERE enable = ?", (1,))
for row in rows:
    print(row["description"])  # ✅ CORRECT
    # print(row[0])            # ❌ FORBIDDEN

# Insert returning lastrowid
new_id = self.engine.write(True, "INSERT INTO batches (control_id) VALUES (?)", (id,))

# Update returning rowcount
affected = self.engine.write(False, "UPDATE results SET validated = 1 WHERE result_id = ?", (id,))
```

### Observer Pattern

```python
# Subscribe in __init__
self.engine.subscribe("batch_changed", self.on_batch_changed)

# Notify after changes
self.engine.notify("batch_changed", batch_id)

# Unsubscribe in on_cancel()
self.engine.unsubscribe("batch_changed", self.on_batch_changed)
```

**Events:**
- `batch_changed` - Batch created/modified/deleted
- `result_changed` - QC result added/modified/deleted
- `section_changed` - Section context changed
- `supplier_changed` - Supplier modified
- `equipment_changed` - Equipment modified
- `test_method_changed` - Test method modified

### GUI Window Types

**ParentView** (views/parent_view.py) - Singleton master windows:
```python
class UI(ParentView):
    def __init__(self, parent):
        super().__init__(parent, name="myview")
        if self._reusing:
            return
        # ... build UI ...
        self.show()

    def on_cancel(self, evt=None):
        super().on_cancel()
```

**ChildView** (views/child_view.py) - Editor dialogs:
```python
class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="myeditor")
        self.index = index  # PK or None for INSERT
        # ... build UI ...
        self.show()

    def on_cancel(self, evt=None):
        super().on_cancel()
```

**Cross-window updates:**
```python
# Via registry
win = self.engine.dict_instances.get("batches")
if win and win.winfo_exists():
    win._load_tree()

# Via observer (preferred)
self.engine.notify("batch_changed", batch_id)
```

### Tools Helper Methods

```python
self.engine.clear_treeview(tree)          # Clear Treeview
self.engine.clear_listbox(listbox)        # Clear Listbox
self.engine.add_button(frm, "Save", self.on_save, "<Alt-s>", self)
self.engine.open_child(self, EditorClass, index=pk)
self.engine.center_window(self, on_screen=False)
```

## Critical Rules

### MUST DO
1. **Dictionary access only** - `row["field"]`, never `row[0]`
2. **Parameterized SQL** - Always `?` placeholders, never string concatenation
3. **Log all exceptions** via `self.on_log()`
4. **Specific exceptions** - No bare `except:`
5. **File I/O via Engine** - `self.get_file("filename")` for paths
6. **Multi-site filtering** - Filter by site_id, lab_id, section_id

### MUST NOT
- Positional tuple indexing
- SQL string concatenation
- Direct parent-chain navigation (`self.parent.parent`)
- Multiple instances of master windows
- Business logic in Tkinter callbacks
- Call `on_open()` inside `__init__()`

### Error Handling Pattern

```python
try:
    # operation
except (SpecificError, AnotherError) as e:
    self.on_log(
        inspect.stack()[0][3],
        sys.exc_info()[1],
        sys.exc_info()[0],
        sys.modules[__name__]
    )
```

## GUI Conventions

**Treeview pattern:**
```python
cols = ("date", "result")
tree = ttk.Treeview(parent, columns=cols, show="headings", height=8)
tree.column("date", width=90, anchor=tk.W)
tree.heading("date", text="Date")

# Tags for row colors
tree.tag_configure("disabled", foreground="gray")
tree.tag_configure("violation_3s", foreground="red")
tree.tag_configure("has_notes", background="#fff2cc")

# Map item_id to database PK
dict_items[item_id] = row["pk_field"]
```

**Styles:**
- `Panel.TFrame` - Reusable frame with groove relief
- Date format: Italian `dd-mm-yyyy`
- Row colors: red (>3SD), orange (>2SD), gray (disabled), yellow (#fff2cc for notes)

## Internationalization (i18n)

Biovarase supports multiple languages (English default, Italian). The i18n system is in `i18n.py`.

### Usage Pattern

```python
from i18n import _

# Wrap all user-facing strings
ttk.Label(frm, text=_("Save"))
ttk.Button(frm, text=_("Cancel"), command=self.on_cancel)
messagebox.showinfo(title, _("Operation completed."))
self.title(_("Batch Editor"))

# Dynamic strings with f-strings
self.title(f"{test_name} — {_('Total Error')}")
msg = f"{_('Imported rows')}: {count}"
```

### Adding Translations

Add to `TRANSLATIONS` dictionary in `i18n.py`:
```python
TRANSLATIONS = {
    "Save": {"it": "Salva", "en": "Save"},
    "Cancel": {"it": "Annulla", "en": "Cancel"},
    # ... add new translations here
}
```

### Language Configuration

- **Config file:** `language` (contains "en" or "it")
- **Menu:** Help → Language (requires restart)
- **Engine methods:** `get_language()`, `set_language(lang)`

### Coverage

- **44 views** with i18n support (83% of all views)
- Entry point `biovarase.py` has i18n (exit confirmation dialog)
- Base classes (`parent_view.py`, `child_view.py`) have no UI strings
- Lookup views inherit i18n from `LookupUI` base class

## Role-Based Access Control

```python
ROLE_ADMIN = 0       # Full system access, can change laboratory
ROLE_SUPERUSER = 1   # QC validation, lab-wide
ROLE_TECHNICIAN = 2  # Data entry, section-only
ROLE_AUTOLOGIN = 3   # Read-only guest

self.engine.can_validate_qc()      # Admin or Superuser
self.engine.can_configure_system() # Admin only
self.engine.can_modify_data()      # Admin, Superuser, or Technician
self.engine.is_read_only()         # Autologin
```

### Lab-Based Access Control

Each user has a `lab_id` in the users table (required for all users):

- **Admin (role=0):** Can select laboratory at login and change via menu (Ctrl+E)
- **Other users:** Filtered to their assigned laboratory only

```python
# At login, context is initialized from user's lab_id
self.engine.init_current_ids_from_user(lab_id)

# Admin can change lab without logout
# Menu: File → Change Laboratory (Ctrl+E)

# Get current lab for filtering
lab_id = self.engine.get_lab_id()
```

**Lab selector dialog** (`views/lab_selector.py`):
- Shows all labs with site name: "Lab Name - Site Name"
- Pre-selects user's default lab
- Used at login (admin) and for "Change Laboratory" menu

## QC Domain Knowledge

### Levey-Jennings Chart (`ljcanvas.py`)

The Levey-Jennings chart uses **±4SD scale with clipping** per Westgard recommendation:

- **Y-axis scale:** Fixed at target ±4SD (not auto-scaled to data)
- **Clipping:** Values beyond ±4SD are clipped to chart edge
- **Outlier markers:** Clipped points shown as triangles (▲ above, ▼ below) instead of circles
- **Value labels:** Always show the real value, even for clipped points

Point colors by SD distance:
- **Green:** |z| < 2SD (normal)
- **Yellow/Orange:** 2SD ≤ |z| < 3SD (warning)
- **Red:** |z| ≥ 3SD (violation)

### QC Plot Canvas Files
| File | Purpose |
|------|---------|
| `ljcanvas.py` | Levey-Jennings control chart |
| `youden_canvas.py` | Youden plot for paired levels |
| `total_error_canvas.py` | Total Error visualization |
| `frequency_histogram_canvas.py` | Result distribution histogram |
| `bias_canvas.py` | Bias comparison plots |

### Bland-Altman Scanner (`views/bland_altman_alert.py`)

Automatic scanner for workstation comparison across all tests.

**Features:**
- Runs in background thread (no UI freeze)
- Filters by current lab_id
- Shows only alerts and warnings (hides OK results)
- Uses foreground colors for GTK/Debian compatibility

**Thresholds:**
- Bias threshold: default 10%
- % out threshold: default 5%

**Color coding:**
- Red (foreground): Alert - bias or % out exceeds threshold
- Orange (foreground): Warning - 70% of threshold
- Gray (foreground): Insufficient data (<10 pairs)

### Westgard Multirule Evaluation Order
1. **1:3S** - Single value > 3SD (reject)
2. **2:2S** - Two consecutive > 2SD same side
3. **R:4S** - Range of 2 values >= 4SD
4. **4:1S** - Four consecutive > 1SD same side
5. **10:X** - Ten consecutive same side of mean
6. **1:2S** - Single value > 2SD (warning)

**Minimum series:** 10 values required, otherwise return "NED"

### Configuration Files
| File | Access Method | Purpose |
|------|---------------|---------|
| `ddof` | `get_ddof()` | Degrees of freedom (0 or 1) |
| `zscore` | `get_zscore()` | Coverage factor (1.96 = 95% CI) |
| `language` | `get_language()` | UI language (en, it) |
| `observations` | `get_observations()` | Minimum QC observations |
| `date_format` | `get_date_format()` | Date display format |
| `remember_batch` | `get_remember_batch()` | Remember last batch selection |
| `autologin` | `get_autologin_flag()` | Enable auto-login for viewer user |
| `correlation_coefficient` | `get_correlation_coefficient()` | Youden plot correlation threshold |

**Note:** `section_id` and `lab_id` are now stored in `current_ids` (initialized from user's lab at login), not in config files.

### Constants (app_config.py)
| Constant | Value | Purpose |
|----------|-------|---------|
| `BATCH_DESCRIPTION_MAX_LENGTH` | 15 | Max chars for batch level (L1, Normal, etc.) |
| `LOT_NUMBER_MAX_LENGTH` | 20 | Max chars for lot number |
| `MAX_LOGIN_ATTEMPTS` | 3 | Failed login attempts before lockout |
| `LOG_MAX_SIZE_MB` | 10 | Maximum log file size before rotation |
| `LOG_KEEP_COUNT` | 5 | Number of old log files to keep |
| `DB_CONNECTION_TIMEOUT` | 5 | Database connection timeout in seconds |

## Database Migrations

Migrations are in `migrations/` directory. Run in order after initial `biovarase.sql` setup:

```bash
# Run all migrations in sequence
mysql -u root -p biovarase < migrations/001_reduce_batch_description_size.sql
mysql -u root -p biovarase < migrations/002_add_external_code.sql
mysql -u root -p biovarase < migrations/003_add_daily_approvals.sql
mysql -u root -p biovarase < migrations/004_reduce_lot_number_size.sql
mysql -u root -p biovarase < migrations/005_add_lab_id_to_categories.sql
mysql -u root -p biovarase < migrations/006_abbott_import.sql
mysql -u root -p biovarase < migrations/007_add_lab_id_to_users.sql
```

| Migration | Purpose |
|-----------|---------|
| 001 | Reduce batches.description to VARCHAR(15) |
| 002 | Add external_code to workstation_test_methods |
| 003 | Add daily_approvals table |
| 004 | Reduce batches.lot_number to VARCHAR(20) |
| 005 | Add lab_id to categories (multi-tenant filtering) |
| 006 | Add abbott_imported_files table for import tracking |
| 007 | Add lab_id to users (lab-based access control) |

## Testing

Tests are in `tests/` directory with pytest infrastructure configured via `pytest.ini`.

| Test File | Coverage |
|-----------|----------|
| `test_qc.py` | QC statistical calculations |
| `test_westgards.py` | Westgard multirule validation |
| `test_security.py` | Encryption and password hashing |
| `test_log_rotation.py` | Log file rotation |
| `conftest.py` | Shared fixtures |

### Test Markers (pytest.ini)
- `@pytest.mark.critical` - Medical safety tests
- `@pytest.mark.westgard` - Westgard rule tests
- `@pytest.mark.qc` - QC statistical tests
- `@pytest.mark.security` - Security/encryption tests
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Database/file I/O tests

### Test Pattern (AAA)
```python
@pytest.mark.unit
@pytest.mark.qc
def test_calculate_mean_returns_correct_value():
    # Arrange
    values = [10.0, 20.0, 30.0]
    expected = 20.0

    # Act
    result = qc.get_mean(values)

    # Assert
    assert result == pytest.approx(expected, abs=0.01)
```

## Security

- **Passwords:** bcrypt with cost factor 12
- **Config encryption:** Fernet (AES-128-CBC) tied to hardware (MAC + machine-id)
- **Key derivation:** PBKDF2-HMAC-SHA256 (100,000 iterations)
- **SQL:** Parameterized queries only (SQL injection prevention)

## Abbott Alinity Integration

Biovarase imports QC data from Abbott Alinity instruments via network share.

### Architecture

```
Abbott Instruments → Windows Share → Linux Mount → abbott_import.py → MariaDB
     (ALCI-1/2/3)    \\172.16.145.11   /mnt/biovarase_qc
```

### File Format

Abbott exports pipe-delimited `.txt` files with QC results. Key fields by position:
| Position | Field | Example |
|----------|-------|---------|
| 7 | Control name | MCHEMIA, PCT |
| 8 | Lot number | 032807240 |
| 9 | Expiration | YYYYMMDD |
| 10 | Level | 1, 2, 3 |
| 12 | Test code | 311, VITD, GLUC |
| 14 | DateTime | YYYYMMDDHHMMSSmmm |
| 15 | Result value | 5.23 |
| 16 | Workstation | ALCI-1, ALCI-2, ALCI-3 |
| 18 | Target | 5.0 |
| 19 | SD | 0.3 |

### Import Script (`abbott_import_v2.py`)

Simplified importer - requires pre-configured test_methods and workstation_test_methods.

```bash
# Test run (no DB changes)
python3 abbott_import_v2.py --dry-run --verbose

# Import with limit
python3 abbott_import_v2.py --limit 100 -v

# Full import (run in batches to avoid server overload)
python3 abbott_import_v2.py --limit 300
python3 abbott_import_v2.py --limit 600   # skips duplicates automatically
python3 abbott_import_v2.py               # complete remaining
```

**Import flow:**
```
File Abbott → TESTCODE (field 12) + workstation (field 16)
           → workstation_test_methods.external_code lookup
           → test_method_id
           → batch (per workstation/lot/level)
           → result (with duplicate detection)
```

**Auto-creates on import:**
- `tests` - New test with description from `CFGTESTQNRANGE.xlsx` or `MANUAL_MAPPINGS`
- `test_methods` - Linked to section_id=6 (Alinity), category_id=29
- `workstation_test_methods` - External code mapping
- `batches` - With target/SD from file, lot format: `{lot}-L{level}`
- `results` - Duplicate detection by (batch_id, workstation_id, received)

### Configuration

| Constant | Value | Description |
|----------|-------|-------------|
| `ABBOTT_PATH` | `/mnt/biovarase_qc/EXPQC/Biovarase` | Network share mount point |
| `SECTION_ID` | 6 | Sezione Alinity |
| `LAB_ID` | 2 | Laboratory ID for Abbott batches |
| `CONTROL_ID` | 71 | Control type ID for Abbott QC |
| `VALID_WORKSTATIONS` | ALCI-1, ALCI-2, ALCI-3 | Accepted device IDs |
| `MAPPING_FILE` | `CFGTESTQNRANGE.xlsx` | Excel with test code→description |

### Test Code Mapping

The importer maps Abbott test codes to descriptions using:
1. **Excel file** (`CFGTESTQNRANGE.xlsx`) - Primary source
2. **MANUAL_MAPPINGS dict** - Fallback for codes not in Excel

Common mappings:
```python
'LIPLD': 'Lipasi', 'VITD': 'Vitamina D', 'B12': 'Vitamina B12',
'GLUC': 'Glucosio', 'CREA': 'Creatinina', 'AST': 'AST/GOT', ...
```

### Test Methods Configuration

When creating `test_methods` for Abbott tests, use these default values:

| Field | Value | Description |
|-------|-------|-------------|
| `section_id` | 6 | Sezione Alinity |
| `category_id` | 29 | Abbott category |
| `sample_id` | 1 | Default sample type |
| `method_id` | 18 | Abbott method |
| `unit_id` | 40 | NA (to be refined with Excel units) |
| `is_mandatory` | 0 | Not mandatory |
| `status` | 1 | Active |
| `code` | LISCODE from Excel | Max 10 chars, from CFGTESTQNRANGE.xlsx column C |

### Excel File Structure (`CFGTESTQNRANGE.xlsx`)

| Column | Field | Example |
|--------|-------|---------|
| A | TESTCODE | 311, VITD, GLUC |
| B | DESCRIPTION | FT3 (Triiodiotironina libera) |
| C | LISCODE | FT3, GLU, CREA |
| D | UNIT | pg/mL, mg/dL, U/L |
| E-N | Reference ranges | SESSO, AGEUNIT, NORMLOW, NORMHIGH, etc. |

The LISCODE is used as `test_methods.code` for LIS integration.

### Network Share Setup (Debian)

```bash
# Credentials file
sudo nano /root/omnilab-creds
# username=gcostanzi
# password=PASSWORD
# domain=INTRAOSA

# Mount point
sudo mkdir -p /mnt/biovarase_qc

# Manual mount
sudo mount -t cifs //172.16.145.11/Omnilab/EXPQC/Biovarase /mnt/biovarase_qc \
  -o credentials=/root/omnilab-creds,vers=3.0,sec=ntlmssp

# Automatic mount via cron (check_qc_share.sh)
```

### Cron Setup

```bash
# Crontab entry (every 5 minutes)
*/5 * * * * /home/gcostanzi@intraosa.net/Documents/projects/biovarase/run_abbott_import.sh

# Wrapper script: run_abbott_import.sh
cd /home/gcostanzi@intraosa.net/Documents/projects/biovarase
python3 abbott_import_v2.py >> abbott_import.log 2>&1
```

## Key Files

| File | Purpose |
|------|---------|
| `biovarase.py` | Entry point |
| `engine.py` | Main orchestrator (Singleton, combines all mixins) |
| `biovarase.sql` | Database schema for initial setup |
| `config.enc` | Encrypted database credentials (hardware-locked, gitignored) |
| `setup_wizard.py` | First-run configuration wizard |
| `build_biovarase.cmd` | Windows build script (uses Nuitka) |
| `abbott_import_v2.py` | Abbott Alinity QC data importer (v2) |
| `CFGTESTQNRANGE.xlsx` | Abbott test code→description mapping |
| `run_abbott_import.sh` | Cron wrapper for Abbott import |
| `views/lab_selector.py` | Lab selection dialog for admin users |
| `views/qc_report.py` | QC Report generator for documentation |

## Standards Compliance

- **ISO 15189:2022** - Medical laboratories quality requirements
- **ISO/TS 20914:2019** - Measurement uncertainty guidance
- **Westgard JO** - Basic QC Practices, 4th Edition, 2016
- **PEP 8** - Python style guide
- **GNOME HIG** - Human Interface Guidelines

## Notes for AI Assistants

- This is a **production system** in active medical laboratories
- **Data integrity is paramount** - QC data impacts patient safety
- **Communication in Italian, code in English** - strictly enforced
- Always use dictionary access for database rows
- Always use parameterized SQL queries
- Log all exceptions via `on_log()`
