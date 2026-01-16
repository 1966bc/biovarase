<?php
/**
 * Header with dynamic navigation menu
 *
 * Include this at the top of each page after auth.php
 * Menu items change based on user role
 */

require_once __DIR__ . '/../engine/auth.php';

$currentUser = getCurrentUser();
$currentRole = getCurrentRole();
$currentPage = basename($_SERVER['PHP_SELF'], '.php');

// Get lab_id from session or URL
$labId = isset($_GET['lab_id']) ? $_GET['lab_id'] : (isLoggedIn() ? $currentUser['org_id'] : null);
$labIdParam = $labId ? '?lab_id=' . htmlspecialchars($labId) : '';
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= isset($pageTitle) ? htmlspecialchars($pageTitle) : 'Biovarase - QC Management' ?></title>
    <link rel="icon" type="image/x-icon" href="/biovarase/favicon.ico">
    <link rel="shortcut icon" type="image/x-icon" href="/biovarase/favicon.ico">
    <link rel="stylesheet" href="/biovarase/css/dashboard.css">
    <?php if (isset($pageCSS)): ?>
    <link rel="stylesheet" href="/biovarase/css/<?= $pageCSS ?>">
    <?php endif; ?>
    <style>
        /* Navigation styles */
        .nav-bar {
            background: #2c3e50;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-brand {
            color: #fff;
            font-size: 1.2rem;
            font-weight: bold;
            text-decoration: none;
            padding: 15px 0;
        }
        .nav-menu {
            display: flex;
            list-style: none;
            margin: 0;
            padding: 0;
            gap: 5px;
        }
        .nav-menu a {
            color: #ecf0f1;
            text-decoration: none;
            padding: 15px 15px;
            display: block;
            transition: background 0.2s;
        }
        .nav-menu a:hover {
            background: #34495e;
        }
        .nav-menu a.active {
            background: #3498db;
        }
        .nav-user {
            display: flex;
            align-items: center;
            gap: 15px;
            color: #ecf0f1;
        }
        .nav-user-info {
            text-align: right;
            font-size: 0.85rem;
        }
        .nav-user-name {
            font-weight: bold;
        }
        .nav-user-role {
            opacity: 0.7;
            font-size: 0.75rem;
        }
        .nav-btn {
            background: #3498db;
            color: #fff;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .nav-btn:hover {
            background: #2980b9;
        }
        .nav-btn-logout {
            background: #e74c3c;
        }
        .nav-btn-logout:hover {
            background: #c0392b;
        }
    </style>
</head>
<body>
    <nav class="nav-bar">
        <a href="/biovarase/dashboard<?= $labIdParam ?>" class="nav-brand">Biovarase</a>

        <ul class="nav-menu">
            <!-- Always visible -->
            <li><a href="/biovarase/dashboard<?= $labIdParam ?>" class="<?= $currentPage === 'dashboard' ? 'active' : '' ?>">Dashboard</a></li>

            <?php if (isLoggedIn()): ?>
                <!-- Logged in users -->
                <?php if (canValidateQC()): ?>
                <li><a href="/biovarase/validation<?= $labIdParam ?>" class="<?= $currentPage === 'validation' ? 'active' : '' ?>">Validazione</a></li>
                <?php endif; ?>

                <?php if (canModifyData()): ?>
                <li><a href="/biovarase/batches<?= $labIdParam ?>" class="<?= $currentPage === 'batches' ? 'active' : '' ?>">Batch</a></li>
                <li><a href="/biovarase/results<?= $labIdParam ?>" class="<?= $currentPage === 'results' ? 'active' : '' ?>">Risultati</a></li>
                <?php endif; ?>

                <?php if (isAdmin()): ?>
                <li><a href="/biovarase/admin<?= $labIdParam ?>" class="<?= $currentPage === 'admin' ? 'active' : '' ?>">Admin</a></li>
                <?php endif; ?>
            <?php endif; ?>
        </ul>

        <div class="nav-user">
            <?php if (isLoggedIn()): ?>
                <div class="nav-user-info">
                    <div class="nav-user-name"><?= htmlspecialchars($currentUser['last_name'] . ' ' . $currentUser['first_name']) ?></div>
                    <div class="nav-user-role"><?= getRoleName($currentRole) ?></div>
                </div>
                <a href="/biovarase/profile<?= $labIdParam ?>" class="nav-btn">Profilo</a>
                <a href="/biovarase/logout" class="nav-btn nav-btn-logout">Esci</a>
            <?php else: ?>
                <a href="/biovarase/login" class="nav-btn">Accedi</a>
            <?php endif; ?>
        </div>
    </nav>
