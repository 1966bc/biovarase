# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Biovarase** - Professional QC management system for medical laboratories (ISO 15189:2022).

| | |
|---|---|
| **Stack** | Python 3.7+ / Tkinter / MariaDB 10.11+ |
| **Dependencies** | `mariadb`, `openpyxl`, `Pillow`, `bcrypt`, `cryptography` |
| **Author** | Giuseppe Costanzi (1966bc) - giuseppecostanzi@gmail.com |
| **Standards** | ISO 15189:2022, ISO/TS 20914:2019, Westgard QC |

## Language Policy

- **Communication:** Italian
- **Code:** English (variables, functions, comments, docstrings, commits)

## Critical Rules

**This is a production system in active medical laboratories. Data integrity impacts patient safety.**

### MUST DO
1. **Dictionary access only** - `row["field"]`, never `row[0]`
2. **Parameterized SQL** - Always `?` placeholders, never string concatenation
3. **Log all exceptions** via `self.on_log()`
4. **Specific exceptions** - No bare `except:`
5. **File I/O via Engine** - `self.get_file("filename")` for paths
6. **Multi-site filtering** - Filter by site_id, lab_id, section_id

### MUST NOT
- Positional tuple indexing on DB results
- SQL string concatenation
- Direct parent-chain navigation (`self.parent.parent`)
- Multiple instances of master windows
- Business logic in Tkinter callbacks
- Call `on_open()` inside `__init__()`

### Error Handling
```python
try:
    # operation
except (SpecificError, AnotherError) as e:
    self.on_log(inspect.stack()[0][3], sys.exc_info()[1], sys.exc_info()[0], sys.modules[__name__])
```

## Development Commands

```bash
# Run
python3 biovarase.py                    # Linux
py biovarase.py                         # Windows

# Test
pytest tests/ -v                        # All tests
pytest -m critical -v                   # Medical safety
pytest -m westgard -v                   # Westgard rules
pytest tests/test_qc.py::TestQC::test_get_mean_with_valid_series -v  # Single

# Database
mysql -u root -p < biovarase.sql        # Initial setup

# Build (Windows)
build_biovarase.cmd                     # Output: dist/biovarase.dist/biovarase.exe
```

## Architecture

### Mixin Pattern (Singleton Engine)

```python
class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Launcher, Tools, metaclass=_EngineMeta):
    pass
```

| Mixin | File | Purpose |
|-------|------|---------|
| `DBMS` | dbms.py | `read()`, `write()` |
| `Controller` | controller.py | SQL builders, domain logic |
| `QC` | qc.py | Statistical calculations |
| `Westgards` | westgards.py | Multirule QC evaluation |
| `Tools` | tools.py | GUI utilities |

### Engine Manages
- **Global state:** `current_ids` (site_id, lab_id, section_id)
- **Window registry:** `dict_instances`
- **Observer pattern:** `subscribe()`, `unsubscribe()`, `notify()`
- **Logging:** `on_log()`

### Data Hierarchy
**Site → Lab → Section → Workstation → Batch → Result**

### Database Access
```python
# Read - ALWAYS dictionary access
rows = self.engine.read(True, "SELECT * FROM tests WHERE enable = ?", (1,))
for row in rows:
    print(row["description"])  # CORRECT
    # print(row[0])            # FORBIDDEN

# Write
new_id = self.engine.write(True, "INSERT INTO batches (control_id) VALUES (?)", (id,))  # returns lastrowid
affected = self.engine.write(False, "UPDATE results SET validated = 1 WHERE result_id = ?", (id,))  # returns rowcount
```

### Observer Pattern
```python
self.engine.subscribe("batch_changed", self.on_batch_changed)    # in __init__
self.engine.notify("batch_changed", batch_id)                    # after changes
self.engine.unsubscribe("batch_changed", self.on_batch_changed)  # in on_cancel()
```

Events: `batch_changed`, `result_changed`, `section_changed`, `supplier_changed`, `equipment_changed`, `test_method_changed`

### GUI Windows

**ParentView** - Singleton master windows:
```python
class UI(ParentView):
    def __init__(self, parent):
        super().__init__(parent, name="myview")
        if self._reusing: return
        # build UI
        self.show()
```

**ChildView** - Editor dialogs:
```python
class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="myeditor")
        self.index = index  # PK or None for INSERT
        # build UI
        self.show()
```

### Tools Helpers
```python
self.engine.clear_treeview(tree)
self.engine.clear_listbox(listbox)
self.engine.add_button(frm, "Save", self.on_save, "<Alt-s>", self)
self.engine.open_child(self, EditorClass, index=pk)
self.engine.center_window(self, on_screen=False)
```

## GUI Conventions

```python
# Treeview with tags
tree.tag_configure("disabled", foreground="gray")
tree.tag_configure("violation_3s", foreground="red")
tree.tag_configure("has_notes", background="#fff2cc")

# Map item_id to PK
dict_items[item_id] = row["pk_field"]
```

- Date format: from `date_format` config file
- Colors: red (>3SD), orange (>2SD), gray (disabled), yellow (#fff2cc notes)

## i18n

```python
from i18n import _
ttk.Label(frm, text=_("Save"))
msg = f"{_('Imported rows')}: {count}"
```

Config: `language` file contains "en" or "it". Engine: `get_language()`, `set_language(lang)`

## Access Control

```python
ROLE_ADMIN = 0       # Full access, can change laboratory
ROLE_SUPERUSER = 1   # QC validation
ROLE_TECHNICIAN = 2  # Data entry
ROLE_AUTOLOGIN = 3   # Read-only

self.engine.can_validate_qc()       # Admin or Superuser
self.engine.can_configure_system()  # Admin only
self.engine.can_modify_data()       # Admin, Superuser, Technician
self.engine.is_read_only()          # Autologin
```

Each user has `lab_id` - Admin can change lab (Ctrl+E), others are filtered.

## QC Domain

### Westgard Rules (evaluation order)
1. **1:3S** - Single > 3SD (reject)
2. **2:2S** - Two consecutive > 2SD same side
3. **R:4S** - Range >= 4SD
4. **4:1S** - Four consecutive > 1SD same side
5. **10:X** - Ten consecutive same side of mean
6. **1:2S** - Single > 2SD (warning)

Minimum: 10 values required, otherwise "NED"

### Levey-Jennings Chart (`ljcanvas.py`)
- Y-axis: target ±4SD (fixed scale)
- Clipping: beyond ±4SD shown as triangles
- Colors: green (<2SD), orange (2-3SD), red (>3SD)

### Canvas Files
| File | Purpose |
|------|---------|
| `ljcanvas.py` | Levey-Jennings |
| `youden_canvas.py` | Youden plot |
| `total_error_canvas.py` | Total Error |
| `frequency_histogram_canvas.py` | Distribution |
| `bias_canvas.py` | Bias comparison |

## Configuration

### Files (machine-specific, gitignored)
| File | Method | Purpose |
|------|--------|---------|
| `ddof` | `get_ddof()` | Degrees of freedom (0/1) |
| `zscore` | `get_zscore()` | Coverage factor |
| `language` | `get_language()` | UI language |
| `observations` | `get_observations()` | Min QC observations |
| `date_format` | `get_date_format()` | Date display |
| `remember_batch` | `get_remember_batch()` | Remember batch |
| `autologin` | `get_autologin_flag()` | Auto-login |
| `correlation_coefficient` | `get_correlation_coefficient()` | Youden threshold |

### Constants (app_config.py)
| Constant | Value |
|----------|-------|
| `BATCH_DESCRIPTION_MAX_LENGTH` | 15 |
| `LOT_NUMBER_MAX_LENGTH` | 20 |
| `MAX_LOGIN_ATTEMPTS` | 3 |
| `LOG_MAX_SIZE_MB` | 10 |
| `DB_CONNECTION_TIMEOUT` | 5 |

## Testing

```bash
pytest tests/ -v
pytest -m critical -v    # Medical safety
pytest -m westgard -v    # Westgard rules
pytest -m qc -v          # Statistics
pytest -m security -v    # Security
```

Markers: `@pytest.mark.critical`, `@pytest.mark.westgard`, `@pytest.mark.qc`, `@pytest.mark.security`, `@pytest.mark.unit`, `@pytest.mark.integration`

## Security

- **Passwords:** bcrypt (cost 12)
- **Config:** Fernet AES-128-CBC, hardware-locked (MAC + machine-id)
- **Key derivation:** PBKDF2-HMAC-SHA256 (100k iterations)
- **SQL:** Parameterized queries only

## Abbott Alinity Integration

### Architecture
```
Abbott (ALCI-1/2/3) → Windows Share (\\172.16.145.11) → Linux Mount (/mnt/biovarase_qc) → abbott_import_v2.py → MariaDB
```

### Import Commands
```bash
python3 abbott_import_v2.py --dry-run --verbose  # Test
python3 abbott_import_v2.py --limit 100 -v       # Limited
python3 abbott_import_v2.py                       # Full
```

### Configuration
| Constant | Value |
|----------|-------|
| `ABBOTT_PATH` | `/mnt/biovarase_qc/EXPQC/Biovarase` |
| `SECTION_ID` | 6 (Alinity) |
| `LAB_ID` | 2 |
| `CONTROL_ID` | 71 |
| `VALID_WORKSTATIONS` | ALCI-1, ALCI-2, ALCI-3 |

### Network Share Setup
```bash
# Credentials
sudo nano /root/omnilab-creds
# username=gcostanzi
# password=PASSWORD
# domain=INTRAOSA

# Mount
sudo mkdir -p /mnt/biovarase_qc
sudo mount -t cifs //172.16.145.11/Omnilab/EXPQC/Biovarase /mnt/biovarase_qc \
  -o credentials=/root/omnilab-creds,vers=3.0,sec=ntlmssp
```

### Cron
```bash
*/5 * * * * /home/gcostanzi@intraosa.net/Documents/projects/biovarase/run_abbott_import.sh
```

**TODO:** Add fstab entry and firewall (port 445) documentation from production server.

## Database Migrations

Run in order after `biovarase.sql`:
```bash
mysql -u root -p biovarase < migrations/001_reduce_batch_description_size.sql
mysql -u root -p biovarase < migrations/002_add_external_code.sql
mysql -u root -p biovarase < migrations/003_add_daily_approvals.sql
mysql -u root -p biovarase < migrations/004_reduce_lot_number_size.sql
mysql -u root -p biovarase < migrations/005_add_lab_id_to_categories.sql
mysql -u root -p biovarese < migrations/006_abbott_import.sql
mysql -u root -p biovarase < migrations/007_add_lab_id_to_users.sql
```

## Key Files

| File | Purpose |
|------|---------|
| `biovarase.py` | Entry point |
| `engine.py` | Main orchestrator |
| `biovarase.sql` | Database schema |
| `config.enc` | Encrypted DB credentials (gitignored) |
| `abbott_import_v2.py` | Abbott importer |
| `run_abbott_import.sh` | Cron wrapper |
