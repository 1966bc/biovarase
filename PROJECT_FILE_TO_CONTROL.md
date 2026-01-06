# Biovarase - Project File Inventory

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
