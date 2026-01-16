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

// Profile
$router->get('/profile', 'pages/profile.php');
$router->post('/change-password', 'pages/change_password.php');

// Protected pages (will require auth middleware)
$router->get('/validation', 'pages/validation.php');
$router->get('/batches', 'pages/batches.php');
$router->get('/results', 'pages/results.php');

// =============================================================================
// Run
// =============================================================================

$router->run();
