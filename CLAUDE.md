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

## Development Notes (January 2026)

Note for future Claude instances working on this codebase:

**Recent changes:**
- Migration 013 added `org_id` to all tenant-scoped tables (results, batches, test_methods, workstations, categories)
- All views now include `org_id` in INSERT/UPDATE operations via `_get_values()` or explicit SQL
- Observer pattern implemented: `daily_validation` auto-refreshes when results change (`engine.notify("result_changed")`)
- Window management: utility windows (daily_validation, bland_altman, result, batch, plots) use `-topmost` attribute
- **Bug fix:** `notify()` is synchronous - extract needed data BEFORE calling notify if the callback modifies state (e.g., `dict_results.clear()`)
- **Role-based access control (RBAC):** All list views (users, batches, workstations, categories) now filter data by user's org_id and role
- **User management:** Lab Admin (role 3) can now manage users in their lab via Admin → Users menu
- **Schema cleanup:** `lab_id` column completely removed from `batches` and `results` tables - only `org_id` is used
- **Triggers updated (migration 020):** Audit triggers no longer reference `lab_id`
- **Abbott import:** `abbott_import_v2.py` updated to use only `org_id`, filters by `test_methods.status = 1`
- **Abbott import lock:** Creates `/tmp/abbott_import.lock` during execution to prevent DB conflicts
- **Main view:** `set_categories()` now filters by `tests.status = 1` in addition to `test_methods.status = 1`
- **Bland-Altman scanner:** Blocks scan if Abbott import is running (checks lock file)
- **Bland-Altman view:** Fixed `categories` queries to use `org_id` instead of `lab_id`

**Testing:**
- Run tests with venv: `./venv/bin/pytest tests/ -v`
- 721 tests passing, 11 skipped (empty test DB tables)

**Key patterns to follow:**
- `org_id` = `lab_id` for lab-level data (results, batches, categories)
- `org_id` = `section_id` for section-level data (test_methods, workstations)
- Use `self.engine.get_lab_id()` to get current lab's org_id
- Use `build_sql()` for dynamic INSERT/UPDATE (reads columns from DB schema)

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

Events: `batch_changed`, `result_changed`, `section_changed`, `supplier_changed`, `equipment_changed`, `test_method_changed`

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
```

### Production Migration Guide (008-011)

**Step 1: Run migrations in order**
```bash
cd /path/to/biovarase/migrations
mysql -u root -p biovarase < 008_add_lab_id_to_results.sql
# If FK fails, continue to Step 2 before retrying
mysql -u root -p biovarase < 009_add_lab_id_to_audit_batches.sql
mysql -u root -p biovarase < 010_add_lab_id_to_audit_results.sql
mysql -u root -p biovarase < 011_add_lab_id_to_test_methods.sql
```

**Step 2: Fix orphan data (if FK constraint fails)**
```sql
-- Check which lab_ids exist
SELECT lab_id, description FROM labs;

-- Check invalid lab_ids in batches
SELECT DISTINCT lab_id, COUNT(*) FROM batches GROUP BY lab_id;

-- Check invalid lab_ids in results
SELECT DISTINCT lab_id, COUNT(*) FROM results GROUP BY lab_id;

-- Option A: Delete orphan data (if test data)
DELETE FROM results WHERE lab_id IS NULL OR lab_id NOT IN (SELECT lab_id FROM labs);
DELETE FROM batches WHERE lab_id NOT IN (SELECT lab_id FROM labs);

-- Option B: Fix to valid lab_id (if real data)
UPDATE batches SET lab_id = 2 WHERE lab_id NOT IN (SELECT lab_id FROM labs);
UPDATE results SET lab_id = 2 WHERE lab_id IS NULL OR lab_id NOT IN (SELECT lab_id FROM labs);

-- Retry FK constraint
ALTER TABLE results
ADD CONSTRAINT fk_results_lab
FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
ON DELETE RESTRICT ON UPDATE CASCADE;
```

**Step 3: Fix test_methods with section_id = 0**
```sql
-- Check orphan test_methods
SELECT tm.test_method_id, tm.section_id, COUNT(b.batch_id) as batches
FROM test_methods tm
LEFT JOIN batches b ON tm.test_method_id = b.test_method_id
WHERE tm.section_id = 0
GROUP BY tm.test_method_id;

-- If batches exist, fix to valid section/lab
UPDATE test_methods SET section_id = 6, lab_id = 2 WHERE section_id = 0;

-- If no batches, delete
DELETE FROM test_methods WHERE section_id = 0;
```

**Step 4: Verify**
```sql
SELECT 'results' AS tbl, COUNT(*) AS nulls FROM results WHERE lab_id IS NULL
UNION ALL SELECT 'test_methods', COUNT(*) FROM test_methods WHERE lab_id IS NULL;
-- Should be 0 for both

SHOW TRIGGERS;
-- Should show 4 triggers with lab_id in INSERT statements
```

Code already updated for lab_id support:
- `views/result.py` `_get_values()` - includes lab_id from batch
- `views/main.py` test data INSERT - includes lab_id from batch
- `controller.py` `import_qc_file_auto()` - includes lab_id from context
- `abbott_import_v2.py` / `abbott_import.py` - includes LAB_ID constant

## Key Files

| File | Purpose |
|------|---------|
| `biovarase.py` | Entry point |
| `engine.py` | Main orchestrator |
| `biovarase.sql` | Database schema |
| `config.enc` | Encrypted DB credentials (gitignored) |
| `abbott_import_v2.py` | Abbott importer |
| `run_abbott_import.sh` | Cron wrapper |
