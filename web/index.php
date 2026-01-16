<?php
/**
 * Biovarase Web - Entry Point
 *
 * All requests are routed through this file.
 * Apache/Nginx must rewrite URLs to this file.
 */

require_once __DIR__ . '/engine/router.php';

$router = new Router();
$router->setBasePath('/biovarase');

// =============================================================================
// API Routes (JSON responses)
// =============================================================================

// Workstations
$router->get('/api/workstations', 'api/workstations.php');
$router->get('/api/workstations/{id}', 'api/workstation_detail.php');
$router->get('/api/workstations/{id}/tests', 'api/workstation_tests.php');

// Tests & Controls
$router->get('/api/tests/{id}/controls', 'api/test_controls.php');
$router->get('/api/tests/{id}/availability', 'api/test_availability.php');

// Series (for charts)
$router->get('/api/series', 'api/series.php');

// Notes
$router->get('/api/notes', 'api/notes.php');
$router->post('/api/notes', 'api/notes.php');

// Actions
$router->get('/api/actions', 'api/actions.php');

// Result (single)
$router->get('/api/result', 'api/result.php');
$router->put('/api/result', 'api/result.php');

// Settings (language, theme)
$router->post('/api/settings', 'api/settings.php');

// Workstation assays (for batch creation)
$router->get('/api/workstation_assays', 'api/workstation_assays.php');

// =============================================================================
// Page Routes (HTML responses)
// =============================================================================

// Public pages
$router->get('/', function($router) {
    header('Location: /biovarase/dashboard');
    exit;
});

$router->get('/dashboard', 'pages/dashboard.php');
$router->get('/charts', 'pages/charts.php');

// Authentication
$router->get('/login', 'pages/login.php');
$router->post('/login', 'pages/login_action.php');
$router->get('/logout', 'pages/logout.php');
$router->get('/select-lab', 'pages/select_lab.php');
$router->post('/select-lab', 'pages/select_lab.php');

// Profile
$router->get('/profile', 'pages/profile.php');
$router->post('/change-password', 'pages/change_password.php');

// Protected pages (will require auth middleware)
$router->get('/validation', 'pages/validation.php');
$router->get('/batches', 'pages/batches.php');
$router->post('/batches', 'pages/batches.php');
$router->get('/results', 'pages/results.php');

// Admin pages (GET + POST for CRUD operations)
$router->get('/admin', 'pages/admin.php');
$router->get('/admin/tests', 'pages/admin/tests.php');
$router->post('/admin/tests', 'pages/admin/tests.php');
$router->get('/admin/methods', 'pages/admin/methods.php');
$router->post('/admin/methods', 'pages/admin/methods.php');
$router->get('/admin/units', 'pages/admin/units.php');
$router->post('/admin/units', 'pages/admin/units.php');
$router->get('/admin/samples', 'pages/admin/samples.php');
$router->post('/admin/samples', 'pages/admin/samples.php');
$router->get('/admin/categories', 'pages/admin/categories.php');
$router->post('/admin/categories', 'pages/admin/categories.php');
$router->get('/admin/controls', 'pages/admin/controls.php');
$router->post('/admin/controls', 'pages/admin/controls.php');
$router->get('/admin/equipments', 'pages/admin/equipments.php');
$router->post('/admin/equipments', 'pages/admin/equipments.php');
$router->get('/admin/suppliers', 'pages/admin/suppliers.php');
$router->post('/admin/suppliers', 'pages/admin/suppliers.php');
$router->get('/admin/actions', 'pages/admin/actions.php');
$router->post('/admin/actions', 'pages/admin/actions.php');
$router->get('/admin/organizations', 'pages/admin/organizations.php');
$router->post('/admin/organizations', 'pages/admin/organizations.php');
$router->get('/admin/assays', 'pages/admin/assays.php');
$router->post('/admin/assays', 'pages/admin/assays.php');
$router->get('/admin/users', 'pages/admin/users.php');
$router->post('/admin/users', 'pages/admin/users.php');
$router->get('/admin/workstations', 'pages/admin/workstations.php');
$router->post('/admin/workstations', 'pages/admin/workstations.php');

// =============================================================================
// Run
// =============================================================================

$router->run();
