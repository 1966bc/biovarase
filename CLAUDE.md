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

# Database setup
mysql -u root -p < schema.sql
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

Events: `batch_changed`, `result_changed`, `section_changed`, `supplier_changed`, `equipment_changed`, `test_method_changed`

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
ROLE_ADMIN = 0       # Full system access
ROLE_SUPERUSER = 1   # QC validation, lab-wide
ROLE_TECHNICIAN = 2  # Data entry, section-only
ROLE_AUTOLOGIN = 3   # Read-only guest

self.engine.can_validate_qc()      # Admin or Superuser
self.engine.can_configure_system() # Admin only
self.engine.can_modify_data()      # Admin, Superuser, or Technician
self.engine.is_read_only()         # Autologin
```

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
| `section_id` | `get_section_id()` | Current working section |
| `ddof` | `get_ddof()` | Degrees of freedom (0 or 1) |
| `zscore` | `get_zscore()` | Coverage factor (1.96 = 95% CI) |
| `language` | `get_language()` | UI language (en, it) |
| `observations` | `get_observations()` | Minimum QC observations |
| `date_format` | `get_date_format()` | Date display format |
| `remember_batch` | `get_remember_batch()` | Remember last batch selection |

### Constants (app_config.py)
| Constant | Value | Purpose |
|----------|-------|---------|
| `BATCH_DESCRIPTION_MAX_LENGTH` | 15 | Max chars for batch level (L1, Normal, etc.) |
| `LOT_NUMBER_MAX_LENGTH` | 20 | Max chars for lot number |
| `MAX_LOGIN_ATTEMPTS` | 3 | Failed login attempts before lockout |

## Testing

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

## Project Structure

```
biovarase/
├── biovarase.py          # Entry point
├── engine.py             # Main orchestrator (Singleton)
├── app_config.py         # Application constants and config utilities
├── dbms.py               # Database layer
├── controller.py         # SQL builder + domain logic
├── qc.py                 # QC computations
├── westgards.py          # Westgard rules
├── tools.py              # GUI utilities
├── exporter.py           # Data export
├── importer.py           # Data import
├── launcher.py           # File opening
├── security.py           # Encryption (hardware-locked)
├── i18n.py               # Internationalization (translations)
├── views/                # GUI windows (~50 windows)
│   ├── parent_view.py    # Base class (singleton master windows)
│   ├── child_view.py     # Base class (editor dialogs)
│   ├── main.py           # Main application window
│   ├── login.py          # Authentication dialog
│   ├── batches.py        # QC batch management
│   └── ...               # Domain-specific views
├── migrations/           # Database migrations (SQL)
├── schema.sql            # Database schema
├── pytest.ini            # Test configuration
└── docs/                 # Additional documentation

# Local service folders (gitignored, not in repository):
# pics/                   # Screenshots for debugging
# quarantine/             # Old/backup files for reference
```

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
