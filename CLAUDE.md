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

## Key Patterns

**Multi-tenant org_id usage:**
- `org_id` = `lab_id` for lab-level data (results, batches, categories)
- `org_id` = `section_id` for section-level data (test_methods, workstations)
- Use `self.engine.get_lab_id()` to get current lab's org_id
- Use `build_sql()` for dynamic INSERT/UPDATE (reads columns from DB schema)

**Technical validation workflow:**
- Abbott import sets `tech_validated=1`, `operator_code` from workstation (ALCI-1/2/3)
- Manual entry sets `tech_validated_by` to logged-in user
- Daily validation shows "Operator" column with operator_code or technician name

**Notes system (migration 025):**
- Notes have `created_by` field tracking who created the note
- Only the creator (or admin, role=0) can edit a note
- Notes are visible in daily_validation with `[N]` indicator in status column
- Quick action combobox: add notes to multiple results at once
- Observer pattern: `note_changed` event refreshes views

**Performance Dashboard (`views/performance_dashboard.py`):**
- Menu QC → Performances (IT: Performances)
- Shows aggregated QC metrics per test_method + workstation for a date range
- Metrics: Total results, Viol% (|z|≥3), Warn% (|z|≥2), Note%, CV%, Bias%
- Color coding: red (viol≥5%), yellow (viol≥2% or warn≥10%), green (OK)
- Color filter combobox: All, Critical (red), Warning (yellow), Good (green)
- Click column headers to sort
- Select row to see action breakdown (which corrective actions were used)
- Export with preview: shows colored table before saving, Excel has colored rows

**Test Methods view (`views/test_methods.py`):**
- Search box to filter tests by name
- Treeview shows: code, sample, method, unit, section, category
- Window size 1000x600

**Daily Validation (`views/daily_validation.py`):**
- Hotkey: Alt-L to load (underline on "L" in Load button)
- "Only problems" filter: shows "No problems in X results" when filter active but no problems found
- Query counts only results with complete chain (batch → test_method → test)

**Window management (GUI policy):**

| Type | transient | grab_set | resizable | Examples |
|------|-----------|----------|-----------|----------|
| Modal dialog | ✓ | ✓ | False | lab_selector, observations, set_zscore |
| Utility dialog | ✓ | ✗ | False | notes, export_notes, analytical |
| Work window | ✗ | ✗ | True | performance_dashboard, daily_validation, plots, batches |
| Editor (ChildView) | ✓ | ✗ | False | batch, result, note, goal |

**Important:** `transient()` breaks resize on Windows! Never use it for windows that need to resize.

- Modal dialogs: block interaction with parent until closed
- Utility dialogs: small popups, fixed size, stay with parent
- Work windows: independent, resizable, appear in taskbar
- Avoid `-topmost` except for critical alerts

**Abbott import lock:** Creates `/tmp/abbott_import.lock` during execution - other processes (Bland-Altman scanner) check this before DB access.

**Background operations with threading:**
For long-running operations (exports, reports) that need animated progress bars:

1. Use `BackgroundConnection` for dedicated DB connection in worker thread
2. Use `queue.Queue` for thread-to-main communication
3. Use `after()` to poll the queue from main thread

```python
import threading
import queue

def _on_export(self):
    def worker():
        # Dedicated connection for this thread
        with self.engine.get_background_connection() as bg:
            rows = bg.read(True, "SELECT ...", ())
            # ... process data ...
        self.async_queue.put(("done", result))

    def check_queue():
        try:
            status, data = self.async_queue.get_nowait()
            self._stop_progress()
            # handle result
        except queue.Empty:
            self.after(50, check_queue)

    self._start_progress()
    threading.Thread(target=worker, daemon=True).start()
    self.after(50, check_queue)
```

**Progress bar pattern:**
```python
# In view's __init__:
self.progress = ttk.Progressbar(frm, mode="indeterminate", length=120)

# Use engine helpers:
self.engine.start_progress(self.progress, self)
self.engine.stop_progress(self.progress, self)
```

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
6. **Multi-tenant filtering** - Filter by org_id using organizations table

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
| `Exporter` | exporter.py | Excel/data export |
| `Importer` | importer.py | QC data import |
| `Launcher` | launcher.py | Window management |
| `Tools` | tools.py | GUI utilities |

### Engine Manages
- **Global state:** `current_ids` (site_id, lab_id, section_id)
- **Window registry:** `dict_instances`
- **Observer pattern:** `subscribe()`, `unsubscribe()`, `notify()`
- **Logging:** `on_log()`

### Data Hierarchy
**Country → Region → Site → Lab → Section → Workstation → Batch → Result**

All hierarchy levels are stored in the `organizations` table with `org_type` field.

### Multi-Tenant Architecture

**Primary isolation: `organizations` table with `org_id`**

The hierarchy is stored in a self-referential `organizations` table:
- `org_type`: 'country', 'region', 'site', 'lab', 'section'
- `parent_id`: References parent organization

At login, `current_ids` is populated from the user's `org_id`:
```python
# Engine stores current context
self.engine.current_ids = {
    "lab_id": 2002,      # User's lab org_id
    "site_id": 2001,     # Parent site org_id
    "section_id": None,  # Set when section selected
    "comp_id": 1,        # Supplier ID
}
```

**Filtering pattern (uses organizations table):**
```python
lab_id = self.engine.current_ids.get("lab_id")

# Filter sections under current lab
sql = """
    SELECT * FROM organizations section
    JOIN test_methods tm ON tm.org_id = section.org_id
    WHERE section.parent_id = ? AND section.org_type = 'section'
"""
rows = self.engine.read(True, sql, (lab_id,))
```

**Tables with org_id:**
| Table | org_id Usage |
|-------|--------------|
| `results` | `org_id` = lab's org_id |
| `batches` | `org_id` = lab's org_id |
| `test_methods` | `org_id` = section's org_id |
| `workstations` | `org_id` = section's org_id |
| `categories` | `org_id` = lab's org_id |
| `users` | `org_id` = assigned lab/section org_id |

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

Events: `batch_changed`, `result_changed`, `section_changed`, `supplier_changed`, `equipment_changed`, `test_method_changed`, `note_changed`, `tests_changed`

**IMPORTANT:** `notify()` is **synchronous** - callbacks execute immediately. If a callback clears dictionaries or reloads data, extract any needed values BEFORE calling notify:
```python
# WRONG - dict_results cleared by _on_result_changed during notify
self.engine.notify("result_changed", result_id)
ws_id = self.dict_results[item_id]["workstation_id"]  # KeyError!

# CORRECT - extract before notify
ws_id = self.dict_results[item_id]["workstation_id"]
self.engine.notify("result_changed", result_id)
```

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

### User Scope via org_id

Each user has an `org_id` field in the `users` table that references the `organizations` table:

```python
# At login, context is initialized from user's org_id
user_org_id = self.engine.log_user.get("org_id")  # Returns org_id (e.g., 2002)
self.engine.init_current_ids_from_user(user_org_id)

# IMPORTANT: Use org_id, NOT lab_id (legacy field)
# log_user["org_id"] = 2002 (correct - organizations table)
# log_user["lab_id"] = 2    (legacy - old labs table, DO NOT USE)
```

### Permission Methods

```python
self.engine.can_validate_qc()       # Admin or Superuser
self.engine.can_configure_system()  # Admin only
self.engine.can_modify_data()       # Admin, Superuser, Technician
self.engine.is_read_only()          # Viewer
```

Admin (role=0) can change lab via menu (Ctrl+E), others are filtered to their org_id.

### Organizations (Flexible Hierarchy)

Single `organizations` table with `parent_id` for any depth:

```
organizations (org_type, parent_id)
├── Italia (country, NULL)
│   ├── Lazio (region, parent=Italia)
│   │   ├── Azienda Ospedaliera San Camillo (site, parent=Lazio)
│   │   │   ├── Laboratorio Analisi (lab, parent=San Camillo)
│   │   │   │   ├── Chimica Clinica (section, parent=Lab)
│   │   │   │   └── Ematologia (section, parent=Lab)
│   │   │   └── Laboratorio Microbiologia (lab, parent=San Camillo)
│   │   └── Policlinico Umberto I (site, parent=Lazio)
│   └── Lombardia (region, parent=Italia)
└── France (country, NULL)
```

**Benefits:**
- Flexible depth without schema changes
- Single `org_id` field for all scopes
- Easy recursive queries with CTEs
- Add levels (district, department) without migration

**Query descendants:**
```sql
WITH RECURSIVE tree AS (
    SELECT org_id, parent_id, org_type, description
    FROM organizations WHERE org_id = ?  -- Start point
    UNION ALL
    SELECT o.org_id, o.parent_id, o.org_type, o.description
    FROM organizations o JOIN tree t ON o.parent_id = t.org_id
)
SELECT * FROM tree;
```

### Role Hierarchy

| Role | Constant | Scope | Permissions |
|------|----------|-------|-------------|
| 0 | `ROLE_APP_ADMIN` | Global | All orgs, master data, system config |
| 1 | `ROLE_COUNTRY_ADMIN` | Country | All descendants of country org |
| 2 | `ROLE_REGIONAL_ADMIN` | Region | All descendants of region org |
| 3 | `ROLE_LAB_ADMIN` | Lab | Lab config, users, workstations |
| 4 | `ROLE_SUPERUSER` | Lab | QC validation, batch management |
| 5 | `ROLE_TECHNICIAN` | Lab | Data entry only |
| 6 | `ROLE_VIEWER` | Lab | Read-only |

**User scope:** Single `org_id` field
- `org_id = NULL` → App Admin (sees everything)
- `org_id = X` → User sees org X and all its descendants

**Visual Role Reference:**

```
Role 0: APP ADMIN (God mode)
   ├── Sees ALL organizations worldwide
   ├── Manages global master data (tests, controls, units, etc.)
   ├── Full Admin menu access
   └── org_id = NULL (no restrictions)

Role 1: COUNTRY ADMIN (e.g., Italia)
   ├── Sees all regions/labs in their country
   ├── Can create Regional Admins
   └── org_id = country's org_id

Role 2: REGIONAL ADMIN (e.g., Lazio)
   ├── Sees all labs/sites in their region
   ├── Can create Lab Admins
   └── org_id = region's org_id

Role 3: LAB ADMIN (e.g., Laboratorio Analisi)
   ├── Manages ONE laboratory
   ├── Creates users, workstations, test methods
   ├── Full Edit menu access
   └── org_id = lab's org_id

Role 4: SUPERUSER
   ├── Validates QC results
   ├── Manages batches
   ├── NO user management
   └── org_id = lab's org_id

Role 5: TECHNICIAN
   ├── Enters QC data
   ├── NO validation permissions
   └── org_id = lab's org_id

Role 6: VIEWER
   ├── Read-only access
   ├── NO Edit/Import menus
   └── org_id = lab's org_id
```

**Menu Visibility by Role:**

| Menu | Role 0 | Role 1-3 | Role 4-5 | Role 6 |
|------|--------|----------|----------|--------|
| Admin | ✅ (all items) | ✅ (Users only) | ❌ | ❌ |
| Edit | ✅ | ✅ | ✅ | ❌ |
| Imports | ✅ | ✅ | ✅ | ❌ |
| QC | ✅ | ✅ | ✅ | ✅ |
| Exports | ✅ | ✅ | ✅ | ✅ |
| Documents | ✅ | ✅ | ✅ | ✅ |

**Admin Menu Items by Role:**
| Item | Role 0 | Role 1-3 |
|------|--------|----------|
| Actions, Controls, Equipments, Methods, Organizations, Samples, Suppliers, Tests, Units | ✅ | ❌ |
| Users | ✅ | ✅ |

### Data Governance

**Global Master Data (App Admin only):**
| Table | Scope | Reason |
|-------|-------|--------|
| `tests` | Global | Consistent analyte naming worldwide |
| `units` | Global | Standard units of measurement |
| `methods` | Global | Analytical methods catalog |
| `samples` | Global | Sample types |
| `equipments` | Global | Instrument manufacturers/models |
| `controls` | Global | QC materials (Bio-Rad, Roche, etc.) |
| `actions` | Global | QC corrective actions (peer lab comparison) |
| `suppliers` | Global | Control/reagent manufacturers |

**Local Data (Lab Admin can manage):**
| Table | Scope | Reason |
|-------|-------|--------|
| `test_methods` | Lab | Local test configuration |
| `workstations` | Lab | Lab's instruments |
| `batches` | Lab | QC lots |
| `results` | Lab | QC data |

**Benefits:**
- International scalability (Abbott partnership)
- Consistent nomenclature across countries
- Hierarchical reporting (lab → region → country → global)
- Single point of maintenance for master data

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
python3 abbott_import_v2.py --dry-run --verbose    # Test (no DB changes)
python3 abbott_import_v2.py --days 7 -v            # Last 7 days (cron default)
python3 abbott_import_v2.py --since 2026-01-01 -v  # Since specific date
python3 abbott_import_v2.py --months 1 -v          # Last month
python3 abbott_import_v2.py --months 0             # All files (no date filter)
python3 abbott_import_v2.py --limit 100 -v         # Limit to 100 files
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
# Runs every 5 minutes, imports only last 7 days (lightweight)
*/5 * * * * /home/gcostanzi@intraosa.net/Documents/projects/biovarase/run_abbott_import.sh
```

**TODO:** Add fstab entry and firewall (port 445) documentation from production server.

### Data Cleanup (Optional)
To start fresh from a specific date:
```bash
# 1. Backup first!
mysqldump -u root -p --single-transaction biovarase results batches > backup.sql

# 2. Run cleanup migration (removes Abbott data before 2026-01-01)
mysql -u root -p biovarase < migrations/023_cleanup_abbott_pre_2026.sql

# 3. Reimport from desired date
python3 abbott_import_v2.py --since 2026-01-01 --verbose
```

## Database Migrations

Run in order after `biovarase.sql`:
```bash
mysql -u root -p biovarase < migrations/001_reduce_batch_description_size.sql
mysql -u root -p biovarase < migrations/002_add_external_code.sql
mysql -u root -p biovarase < migrations/003_add_daily_approvals.sql
mysql -u root -p biovarase < migrations/004_reduce_lot_number_size.sql
mysql -u root -p biovarase < migrations/005_add_lab_id_to_categories.sql
mysql -u root -p biovarase < migrations/006_abbott_import.sql
mysql -u root -p biovarase < migrations/007_add_lab_id_to_users.sql

# Multi-tenant enhancement (full lab_id isolation)
mysql -u root -p biovarase < migrations/008_add_lab_id_to_results.sql
mysql -u root -p biovarase < migrations/009_add_lab_id_to_audit_batches.sql
mysql -u root -p biovarase < migrations/010_add_lab_id_to_audit_results.sql
mysql -u root -p biovarase < migrations/011_add_lab_id_to_test_methods.sql

# Organizations hierarchy (replaces countries/sites/labs/sections)
mysql -u root -p biovarase < migrations/012_create_organizations.sql
mysql -u root -p biovarase < migrations/013_add_org_id_to_tables.sql
mysql -u root -p biovarase < migrations/014_update_roles_and_triggers.sql
# mysql -u root -p biovarase < migrations/015_cleanup_old_hierarchy.sql  # ONLY after full testing!

# Admin user (after organizations migration)
mysql -u root -p biovarase < migrations/016_create_admin_user.sql

# Site org_type (physical hospital locations)
mysql -u root -p biovarase < migrations/017_add_site_org_type.sql

# English actions for international peer lab comparison
mysql -u root -p biovarase < migrations/018_actions_to_english.sql

# Fix triggers to remove lab_id (after lab_id column removal)
mysql -u root -p biovarase < migrations/020_fix_triggers_remove_lab_id.sql

# Technical validation (dual validation workflow)
mysql -u root -p biovarase < migrations/021_add_technical_validation.sql

# result_id capacity upgrade (INT → BIGINT UNSIGNED) - includes audit_results
mysql -u root -p biovarase < migrations/022_result_id_to_bigint.sql

# Cleanup Abbott data before 2026 (removes results, batches, audit_results orphans)
mysql -u root -p biovarase < migrations/023_cleanup_abbott_pre_2026.sql
# Then manually: DELETE FROM audit_results WHERE result_id NOT IN (SELECT result_id FROM results);

# Translate methods to English (international naming)
mysql -u root -p biovarase < migrations/024_methods_to_english.sql

# Notes permission control (created_by field)
mysql -u root -p biovarase < migrations/025_add_created_by_to_notes.sql
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
