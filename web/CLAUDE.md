# CLAUDE.md - Biovarase Web

This file provides guidance to Claude Code (claude.ai/code) when working with the web version of Biovarase.

## Project Overview

**Biovarase Web** - Web interface for the Biovarase QC management system.

| | |
|---|---|
| **Stack** | PHP 8+ / JavaScript (vanilla) / MariaDB 10.11+ / Chart.js |
| **Server** | Apache with mod_rewrite |
| **Author** | Giuseppe Costanzi (1966bc) - giuseppecostanzi@gmail.com |
| **Standards** | ISO 15189:2022, ISO/TS 20914:2019, Westgard QC |

## Directory Structure

```
/var/www/html/biovarase/
├── index.php           # Router - all requests go through here
├── api/                # JSON API endpoints
│   ├── config.php      # DB connection, auth helpers, JSON helpers
│   ├── workstations.php
│   ├── workstation_tests.php
│   ├── workstation_assays.php
│   ├── test_controls.php
│   ├── series.php
│   ├── notes.php
│   ├── actions.php
│   ├── result.php
│   └── settings.php
├── pages/              # HTML pages
│   ├── dashboard.php   # Main view - workstations and tests
│   ├── charts.php      # Levey-Jennings charts
│   ├── batches.php     # QC batch management
│   ├── login.php
│   ├── profile.php
│   └── admin/          # Admin pages (Lab Admin+)
│       ├── tests.php
│       ├── methods.php
│       ├── units.php
│       ├── samples.php
│       ├── categories.php
│       ├── controls.php
│       ├── equipments.php
│       ├── suppliers.php
│       ├── actions.php
│       ├── organizations.php
│       ├── assays.php
│       ├── users.php
│       └── workstations.php
├── includes/
│   ├── header.php      # Navigation, theme, language switcher
│   └── footer.php      # JS includes
├── engine/
│   ├── auth.php        # Authentication and authorization
│   ├── router.php      # URL routing
│   └── i18n.php        # Internationalization (EN/IT)
├── css/
│   ├── dashboard.css
│   └── charts.css
├── js/
│   ├── chart.min.js
│   ├── chartjs-plugin-annotation.min.js
│   ├── chartjs-plugin-datalabels.min.js
│   └── charts.js       # Chart rendering logic
└── migrations/         # Database migrations
```

## Key Patterns

### Routing

All requests go through `index.php` which uses the Router class:

```php
$router = new Router();
$router->setBasePath('/biovarase');

// API routes (JSON)
$router->get('/api/workstations', 'api/workstations.php');
$router->post('/api/notes', 'api/notes.php');

// Page routes (HTML)
$router->get('/dashboard', 'pages/dashboard.php');
$router->get('/admin/tests', 'pages/admin/tests.php');
$router->post('/admin/tests', 'pages/admin/tests.php');

$router->run();
```

### Authentication & Authorization

```php
// In pages - require login
requireAuth();

// Get current user info
$user = getCurrentUser();
$role = getCurrentRole();

// Permission checks
isLoggedIn()        // Any logged in user
isAppAdmin()        // Role 0 only
isAdmin()           // Roles 0-3 (Lab Admin+)
canValidateQC()     // Roles 0-4 (Superuser+)
canModifyData()     // Roles 0-5 (Technician+)

// Working lab context
requireWorkingLab();
$labId = getWorkingLabId();
$labName = getWorkingLabName();
```

### Role Hierarchy

| Role | Constant | Menu Access |
|------|----------|-------------|
| 0 | App Admin | All |
| 1 | Country Admin | Dashboard, Batches, Admin |
| 2 | Regional Admin | Dashboard, Batches, Admin |
| 3 | Lab Admin | Dashboard, Batches, Admin |
| 4 | Superuser | Dashboard, Batches |
| 5 | Technician | Dashboard |
| 6 | Viewer | Dashboard (read-only) |

### Multi-tenant Filtering

Always filter by `org_id` (lab context):

```php
$labId = getWorkingLabId();

// Get sections for this lab
$stmt = $pdo->prepare("
    SELECT org_id FROM organizations
    WHERE parent_id = ? AND org_type = 'section'
");
$stmt->execute([$labId]);

// Filter batches by lab
$stmt = $pdo->prepare("
    SELECT * FROM batches WHERE org_id = ?
");
$stmt->execute([$labId]);
```

### API Response Pattern

```php
// In api/config.php
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}

function jsonError($message, $statusCode = 400) {
    jsonResponse(['error' => $message], $statusCode);
}

// Usage
jsonResponse(['workstations' => $data]);
jsonError('Not found', 404);
```

### Internationalization (i18n)

```php
// In engine/i18n.php
$TRANSLATIONS = [
    'Save' => ['it' => 'Salva', 'en' => 'Save'],
    'Batches' => ['it' => 'Lotti QC', 'en' => 'Batches'],
];

// Usage in pages
<?= t('Save') ?>
<?= t('Batches') ?>
```

Language is stored in cookie `biovarase_lang` (1 year expiry).

### Modal Pattern (CRUD pages)

```html
<!-- Modal overlay -->
<div class="modal-overlay" id="editModal">
    <div class="modal">
        <div class="modal-header">
            <h2 id="modalTitle">Edit</h2>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <form method="POST" id="editForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <!-- form fields -->
            <div class="form-actions">
                <button type="button" class="btn" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save</button>
            </div>
        </form>
    </div>
</div>

<script>
function openModal(mode, data = null) {
    const modal = document.getElementById('editModal');
    // populate form...
    modal.classList.add('active');
}
function closeModal() {
    document.getElementById('editModal').classList.remove('active');
}
</script>
```

## Charts (Levey-Jennings)

### Features

- **Y-axis**: Target ±4SD (fixed scale)
- **Clipping**: Values beyond ±4SD shown as triangles at edges
- **Colors**: Green (<2SD), Orange (2-3SD), Red (>3SD), Gray (voided)
- **Data labels**: Value + time shown only for problem points (|z-score| ≥ 2)
- **Click handling**: Click point to open modal (add note, edit value, void result)

### Plugins Used

- `chart.js` - Core charting
- `chartjs-plugin-annotation` - SD lines
- `chartjs-plugin-datalabels` - Value/time labels on points

### Clipping Logic

```javascript
// Values beyond ±4SD are clipped to edge
const clippedValues = series.map(s => {
    if (s.value > yMax) return yMax - clippingMargin;
    if (s.value < yMin) return yMin + clippingMargin;
    return s.value;
});

// Clipped points shown as triangles
const pointStyles = series.map((s, idx) => {
    if (isClippedHigh[idx] || isClippedLow[idx]) return 'triangle';
    return 'circle';
});
```

## Batches

### SD Calculation Modes

1. **Manual**: User enters SD directly
2. **Computed**: SD = (Upper - Lower) / 4 (assumes ±2SD limits)

```javascript
function computeSD() {
    const lower = parseFloat(document.getElementById('lower').value);
    const upper = parseFloat(document.getElementById('upper').value);
    if (upper > lower) {
        const sd = (upper - lower) / 4;
        document.getElementById('sd').value = sd.toFixed(3);
    }
}
```

### Dynamic Assay Loading

When workstation is selected, assays are loaded via API:

```javascript
fetch('/biovarase/api/workstation_assays.php?workstation_id=' + wsId)
    .then(r => r.json())
    .then(data => {
        // populate assay dropdown
    });
```

## Workstations Admin

### Features

- Expandable rows showing assigned assays
- Assay assignment with external code
- External code editing via modal
- Assay count badge on collapsed rows

### Permissions

- View: Lab Admin+ (isAdmin())
- Edit: Lab Admin+ (isAdmin())
- No deletion - only enable/disable

## Critical Rules

### MUST DO

1. **Parameterized SQL** - Always use `?` placeholders
2. **Multi-tenant filtering** - Always filter by org_id
3. **Permission checks** - Check role before showing/processing
4. **Escape output** - Use `htmlspecialchars()` for user data

### MUST NOT

- SQL string concatenation
- Direct `$_GET`/`$_POST` in SQL
- Skip permission checks
- Hardcode lab_id values

## Development

### Apache Config

```apache
<Directory /var/www/html/biovarase>
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^(.*)$ index.php [QSA,L]
</Directory>
```

### Database

Same MariaDB database as desktop app. Run migrations in order after `biovarase.sql`.

### Testing URLs

- Dashboard: `/biovarase/dashboard`
- Charts: `/biovarase/charts?lab_id=X&workstation_id=Y`
- Batches: `/biovarase/batches`
- Admin: `/biovarase/admin`
