# Biovarase - Project File Inventory

**Generated:** 2025-11-30
**Purpose:** Complete listing of all project files organized by directory
**Excludes:** venv/, __pycache__/, .pyc files, .git/, backup files

---

## 📁 Root Directory (Main Application Files)

### Core Application
- `biovarase.py` - Main application entry point
- `engine.py` - Main orchestrator class (combines all mixins)
- `dbms.py` - Database handler class (connection management)
- `controller.py` - SQL builder and domain logic
- `launcher.py` - Alternative application launcher

### Quality Control Modules
- `qc.py` - Quality control main module
- `westgards.py` - Westgard rules implementation
- `tools.py` - Utility functions (current)

### Canvas/Plotting Modules
- `bias_canvas.py` - Bias visualization canvas
- `ljcanvas.py` - Levey-Jennings chart canvas
- `frequency_histogram_canvas.py` - Histogram visualization
- `total_error_canvas.py` - Total error visualization
- `youden_canvas.py` - Youden plot canvas

### Import/Export Modules
- `exporter.py` - Data export functionality
- `importer.py` - Data import functionality
- `import_profiles.ini` - Import profile configurations
- `workstation_profiles.ini` - Workstation configuration profiles

### Utility Scripts
- `calendarium.py` - Calendar/date utilities
- `update_passwords.py` - Password update utility

### Configuration Files
- `config.txt` - Database credentials (PLAINTEXT - TO BE REPLACED)
- `requirements.txt` - Python dependencies

### Documentation
- `PROJECT_RULES.md` - Authoritative development rules (CRITICAL)
- `SESSION_CONTEXT.md` - Project context and architecture overview
- `CHANGELOG.md` - Complete project change history
- `DATABASE_CREDENTIALS_SECURITY.md` - Security implementation decision document
- `LICENSE` - Project license
- `README.md` - (if exists)
- `internal_quality_control_ISO15189.txt` - ISO 15189 QC guidelines

### Database
- `schema.sql` - Complete database schema with triggers and views

### Build/Deployment
- `biovarase.ico` - Application icon
- `build_biovarase.cmd` - Build script

### Development Notes (Text Files)
- `autologin` - Autologin notes
- `bvv` - Notes
- `correlation_coefficient` - Notes
- `date_format` - Notes
- `ddof` - Degrees of freedom notes
- `dimensions` - Notes
- `elements` - Notes
- `guidelines` - Guidelines reference
- `howto_pylint.txt` - Pylint usage guide
- `how_to_virtual_env` - Virtual environment setup guide
- `icon` - Icon notes
- `lot_description_lenght` - Notes
- `lot_lenght` - Notes
- `manual` - Manual reference
- `observations` - Notes
- `qc_thecnical_manual` - QC technical manual reference
- `records` - Notes
- `remember_batch` - Batch notes
- `section_id` - Notes
- `zscore` - Z-score notes

### Logs
- `log.txt` - Application log file

---

## 📁 frames/ (GUI Windows - 51 files)

### Master Windows (List/Tree Views - Singletons)
- `main.py` - Main application window
- `actions.py` - Actions management
- `batches.py` - Batches list view
- `categories.py` - Categories management
- `controls.py` - Quality controls list
- `counts.py` - Statistical counts
- `equipments.py` - Equipment list
- `labs.py` - Laboratories list
- `methods.py` - Methods list
- `notes.py` - Notes list
- `observations.py` - Observations window
- `samples.py` - Sample types list
- `sections.py` - Sections list
- `sites.py` - Sites list
- `suppliers.py` - Suppliers list
- `tests.py` - Tests list
- `units.py` - Units list
- `users.py` - Users list
- `workstations.py` - Workstations list

### Editor Windows (Detail/Edit Views - Non-Singletons)
- `batch.py` - Batch editor
- `control.py` - Control editor
- `equipment.py` - Equipment editor
- `goal.py` - Analytical goal editor
- `lab.py` - Laboratory editor
- `note.py` - Note editor
- `result.py` - Result editor
- `sample.py` - Sample editor
- `section.py` - Section editor
- `site.py` - Site editor
- `test_method.py` - Test method editor
- `user.py` - User editor
- `workstation.py` - Workstation editor

### Specialized Windows
- `login.py` - Login/authentication window ✅ REFACTORED 2025-11-30
- `change_password.py` - Password change dialog
- `license.py` - License information
- `lookup.py` - Lookup/search dialog

### Assignment/Configuration Windows
- `assign_test_methods.py` - Test method assignment
- `workstation_test_methods.py` - Workstation-test method mapping

### Analysis Windows
- `analytical.py` - Analytical analysis
- `analitycal_goals.py` - Analytical goals (typo in filename)
- `daily_validation.py` - Daily validation window
- `quick_data_analysis.py` - Quick data analysis tool
- `plots.py` - Plot generation
- `set_zscore.py` - Z-score configuration
- `tea.py` - Total error allowable
- `youden.py` - Youden plot
- `zscore.py` - Z-score analysis

### Import/Export Windows
- `export_notes.py` - Notes export
- `importer.py` - Data import window

### Base Classes
- `editor.py` - Base editor window class
- `__init__.py` - Package initialization

---

## 📁 deploy/ (Security POC - 5 files) ✅ NEW 2025-11-30

**Purpose:** Proof of Concept for hardware-locked database credentials encryption

- `security.py` - Core encryption/decryption module (342 lines)
- `test_setup.py` - Setup wizard simulation (115 lines)
- `test_app.py` - Application startup simulation (110 lines)
- `README.md` - Testing instructions and integration guide
- `config.enc` - Generated encrypted configuration (binary, 184 bytes)

**Status:** POC complete on Debian, awaiting Windows testing

---

## 📁 services/ (Service Layer - 4 files)

**Purpose:** Separation of concerns architecture experiment

- `auth_service.py` - Authentication service
- `database_service.py` - Database service
- `service_container.py` - Service dependency injection container
- `__init__.py` - Package initialization

---

## 📁 migrations/ (Database Migrations - 14 files)

**Purpose:** Database schema evolution tracking

### Migration Scripts
- `001_add_foreign_keys.sql` - Add foreign key constraints
- `001_add_foreign_keys_FIXED.sql` - Fixed version
- `001a_cleanup_orphaned_data.sql` - Cleanup orphaned records
- `002_add_check_constraints.sql` - Add check constraints
- `003_convert_float_to_decimal.sql` - Convert float to decimal
- `004_add_missing_indexes.sql` - Add performance indexes
- `005_fix_character_sets_and_unique_constraints.sql` - Character set fixes
- `006_improve_audit_tables.sql` - Audit table improvements
- `007_add_reagent_lot_tracking.sql` - Reagent lot tracking
- `007_add_reagent_lot_tracking_ROLLBACK.sql` - Rollback script

### Utility Scripts
- `cleanup_orphans.sql` - Orphaned data cleanup
- `find_orphans.sql` - Find orphaned records
- `apply_foreign_keys.sh` - Shell script to apply migrations

### Documentation
- `README.md` - Migration guide
- `QUICK_START.md` - Quick start guide

### Backups
- `backups/` - Migration backups directory

---

## 📁 sql/ (SQL Scripts - 14 files)

**Purpose:** Database queries, schema, and maintenance scripts

### DDL (Data Definition Language)
- `ddl/001_add_foreign_keys.sql`
- `ddl/001_add_foreign_keys_FIXED.sql`
- `ddl/001a_cleanup_orphaned_data.sql`
- `ddl/002_add_check_constraints.sql`
- `ddl/003_convert_float_to_decimal.sql`
- `ddl/004_add_missing_indexes.sql`
- `ddl/005_fix_character_sets_and_unique_constraints.sql`
- `ddl/006_improve_audit_tables.sql`
- `ddl/cleanup_orphans.sql`
- `ddl/find_orphans.sql`

### DQL (Data Query Language)
- `dql/alter_statment.sql` - ALTER statements
- `dql/batch_1.sql` - Batch queries
- `dql/biovarase.sql` - General queries
- `dql/validazioni.sql` - Validation queries

### Maintenance Scripts
- `delete_today_test_records.sql` - Delete test records
- `schema.sql` - Full database schema
- `statement.sql` - SQL statements
- `updates.sql` - Update scripts
- `mysql.txt` - MySQL notes

### References
- `aggiornamenti/` - Updates directory
- `biovarase_hotocreate/` - Database creation reference

---

## 📁 scripts/ (Build Scripts - 3 files)

**Purpose:** Build and compilation scripts

- `build_biovarase.cmd` - Windows build script
- `compilare_nuitka` - Nuitka compilation notes
- `compilare.txt` - Compilation instructions

---

## 📁 tests/ (Unit Tests - 2 files)

**Purpose:** Automated testing

- `test_auth_service.py` - Authentication service tests
- `services/` - Service tests directory

**Note:** Test coverage is minimal - needs expansion

---

## 📁 examples/ (Code Examples - 1 file)

**Purpose:** Example implementations

- `login_with_services.py` - Login using services architecture

---

## 📁 backups/ (File Backups - 1 file)

**Purpose:** Timestamped backup files

- `workstation_test_methods.py.bak_20251129_211024` - Backup from 2025-11-29

---

## 📁 documents/ (Documentation & References - 50+ files)

**Purpose:** Technical documentation, PDFs, spreadsheets, and reference materials

### Root Documents
- `BIOVARASE.docx` - Project documentation
- `biovarase_user_manual.pdf` - User manual
- `biological-variation-Q-1680.pdf` - Biological variation reference
- `BVValues1Final.pdf` - BV values reference
- `guidelines.pdf` - Guidelines
- `nt_tr_569_ed4.pdf` - Technical reference
- `test_uncertain.xlsx` - Uncertainty testing

### QC Control Data
- `0250-xt_lot1123_masscheck_antiepileptic_drugs-xt_lv1_excel_.xlsx`
- `0251-xt_lot1123_masscheck_antiepileptic_drugs-xt_lv2_excel_.xlsx`
- `LC04916_CAL-ANTIEPILEPTICS_Lot-009.pdf`
- `Z04319_CTRL-BILEVEL-LEVETIRACETAM_Lotto-010.pdf`

### Build Notes
- `compilazione_in_c` - C compilation notes
- `compilazione_in_c_su_linux` - Linux C compilation
- `ottimizzazione_pyinstaller` - PyInstaller optimization

### QC Data Subdirectories
- `qc/` - Quality control test data
  - `5500/` - 5500 instrument data (8 files)
  - `6500/` - 6500 instrument data (2 runs)
  - `20250204_DOA/`, `20250402_DOA/` - DOA test runs
  - `0250-xt_*.xls`, `0251-xt_*.xlsx` - QC spreadsheets
  - `20250423nl1.txt` - Test results

---

## 📁 icons/ (Application Icons - Duplicate of documents/)

**Purpose:** Icons and images

**Note:** Appears to be duplicate of documents/ - needs cleanup

- `biovarase.ico` - Main application icon
- `documents/` - (Duplicate structure of documents/ directory)

---

## 📁 batches/ (QC Batch Data Files - 10 files)

**Purpose:** Quality control batch/lot data files

### Data Files
- `H52449.DAT` - High level control data
- `L52449.DAT` - Low level control data
- `N52449.DAT` - Normal level control data

### MQI Files (MassCheck Quality Interface)
- `MB1125AH(H).mqi` - High level
- `MB1125AL(L).mqi` - Low level
- `MB1125AN(N).mqi` - Normal level
- `ME1125A-1(L).mqi` - Level 1 (Low)
- `ME1125A-2(N).mqi` - Level 2 (Normal)
- `ME1125A-3(H).mqi` - Level 3 (High)

### XML Files
- `QC_Multichem_U_(Alinity)(08P89-10)_029105240.xml` - Alinity QC data

---

## 📁 imports/ (Import Data Files - 6 files)

**Purpose:** Data files for import functionality

- `0346_lot0223_masscheck_steroid_panel-2_lv2_excel_.xlsx`
- `0347_lot0223_masscheck_steroid_panel-2_lv3_excel_.xlsx`
- `0410_lot0623_drugs_of_abuse_testing_control_set_lv1_excel_.xlsx`
- `doa.txt` - DOA import data
- `p1.txt` - Panel 1 import data
- `p2.txt` - Panel 2 import data

---

## 📁 qc/ (QC Runtime Data - 50+ directories/files)

**Purpose:** Runtime QC data from instruments

### DOA (Drugs of Abuse) Runs
- `20241122 _DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `20241205 _DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `202500225_DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `20250217_DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `20250305_DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `20250313_DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `20250401_DOA/device_123e4567-e89b-12d3-a456-426614174001`
- `20250402_DOA/device_123e4567-e89b-12d3-a456-426614174001`

### Asteroidi (Steroid Panel) Runs
- `asteroidi/p1/` - Panel 1 runs (8 dated runs)
  - `20250211_P1/`, `20250218_P1/`, `20250224_P1/`, etc.
- `asteroidi/p2/` - Panel 2 runs (8 dated runs)
  - `20250204_P2/`, `20250211/`, `20250218/`, etc.

Each run directory contains:
- `device_123e4567-e89b-12d3-a456-426614174001` or `.txt` - Device data files

---

## 📁 .claude/ (Claude Code Configuration - 1 file)

**Purpose:** Claude Code IDE settings

- `settings.local.json` - Local Claude Code settings

---

## Summary Statistics

### File Count by Category

| Category | Count | Purpose |
|----------|-------|---------|
| **frames/** | 51 | GUI windows (master + editor + specialized) |
| **qc/** | 50+ | Runtime QC data from instruments |
| **documents/** | 50+ | Documentation, PDFs, references |
| **icons/** | 50+ | Icons (duplicate - needs cleanup) |
| **sql/** | 14 | SQL scripts and migrations |
| **migrations/** | 14 | Database schema evolution |
| **batches/** | 10 | QC batch/lot data files |
| **imports/** | 6 | Import data files |
| **deploy/** | 5 | Security POC (NEW 2025-11-30) |
| **services/** | 4 | Service layer (experimental) |
| **scripts/** | 3 | Build scripts |
| **tests/** | 2 | Unit tests (minimal) |
| **examples/** | 1 | Code examples |
| **Root** | 30+ | Core application + config + docs |
| **TOTAL** | ~324 | Files (excluding venv, __pycache__, .git) |

### Code Files by Type

| Type | Approx Count | Purpose |
|------|--------------|---------|
| `.py` (Python) | ~80 | Application code |
| `.sql` | ~20 | Database scripts |
| `.txt` | ~40 | Notes, data, logs |
| `.xlsx/.xls` | ~10 | Spreadsheets |
| `.pdf` | ~7 | Documentation |
| `.md` | ~5 | Markdown documentation |
| `.dat/.mqi` | ~10 | QC data files |
| `.xml` | ~2 | Configuration/data |
| Other | ~150 | Device data, temp files, etc. |

---

## Key Files for Development

### CRITICAL - Must Read First
1. `PROJECT_RULES.md` - Authoritative development rules
2. `SESSION_CONTEXT.md` - Project architecture and context
3. `CHANGELOG.md` - Complete change history
4. `schema.sql` - Database structure

### Core Application Architecture
1. `biovarase.py` - Entry point
2. `engine.py` - Main orchestrator
3. `dbms.py` - Database handler
4. `controller.py` - SQL builder + logic
5. `frames/login.py` - Authentication

### Security (NEW - 2025-11-30)
1. `DATABASE_CREDENTIALS_SECURITY.md` - Security decision document
2. `deploy/security.py` - Encryption module
3. `deploy/README.md` - Security POC guide

### Quality Control
1. `qc.py` - QC main module
2. `westgards.py` - Westgard rules
3. `internal_quality_control_ISO15189.txt` - ISO 15189 guidelines

---

## Directory Recommendations

### Should Be Cleaned Up
- `icons/` - Duplicate of `documents/`, merge or remove
- Root directory text files - Consolidate into `docs/` or `notes/`
- `qc/` device data - Consider archiving old runs

### Missing Directories (Consider Adding)
- `docs/` - Consolidated documentation
- `config/` - Configuration files
- `data/` - Sample/test data
- `logs/` - Application logs
- `dist/` - Build artifacts (git-ignored)

---

**END OF FILE INVENTORY**

**Last Updated:** 2025-11-30
**Total Files:** 324 (excluding venv, cache, git)
**Total Directories:** ~80

---

**Usage:**
Read this file to quickly understand the complete project structure and locate specific files.
