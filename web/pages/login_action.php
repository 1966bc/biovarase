<?php
/**
 * Login Action - Handles POST from login form
 */

require_once __DIR__ . '/../engine/auth.php';
require_once __DIR__ . '/../api/config.php';

// Only accept POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /biovarase/login');
    exit;
}

$username = isset($_POST['username']) ? $_POST['username'] : '';
$password = isset($_POST['password']) ? $_POST['password'] : '';

// Get database connection
$pdo = getDBConnection();

// Attempt login
$result = attemptLogin($username, $password, $pdo);

if ($result['success']) {
    // Check if App Admin needs to select a lab
    if (isAppAdmin()) {
        header('Location: /biovarase/select-lab');
        exit;
    }

    // Other users go directly to dashboard
    header('Location: /biovarase/dashboard');
    exit;
} else {
    // Redirect back to login with error
    header('Location: /biovarase/login?error=' . urlencode($result['message']));
    exit;
}
