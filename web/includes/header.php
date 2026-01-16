<?php
/**
 * Header with dynamic navigation menu
 *
 * Include this at the top of each page after auth.php
 * Menu items change based on user role
 */

require_once __DIR__ . '/../engine/auth.php';
require_once __DIR__ . '/../engine/i18n.php';

$currentUser = getCurrentUser();
$currentRole = getCurrentRole();
$currentPage = basename($_SERVER['PHP_SELF'], '.php');
$currentLang = getCurrentLanguage();

// Get working lab
$workingLabId = getWorkingLabId();
$workingLabName = getWorkingLabName();
$labIdParam = $workingLabId ? '?lab_id=' . htmlspecialchars($workingLabId) : '';
?>
<!DOCTYPE html>
<html lang="<?= $currentLang ?>" data-theme="light">
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
        /* Theme CSS Variables */
        :root, [data-theme="light"] {
            --bg-primary: #ecf0f1;
            --bg-secondary: #fff;
            --bg-card: #fff;
            --bg-nav: #2c3e50;
            --bg-nav-hover: #34495e;
            --bg-nav-active: #3498db;
            --text-primary: #2c3e50;
            --text-secondary: #7f8c8d;
            --text-nav: #ecf0f1;
            --border-color: #ddd;
            --border-light: #ecf0f1;
            --shadow: rgba(0,0,0,0.1);
            --success: #27ae60;
            --danger: #e74c3c;
            --warning: #f39c12;
            --info: #3498db;
        }
        [data-theme="dark"] {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #1f2940;
            --bg-nav: #0f0f23;
            --bg-nav-hover: #1a1a3e;
            --bg-nav-active: #2980b9;
            --text-primary: #ecf0f1;
            --text-secondary: #95a5a6;
            --text-nav: #ecf0f1;
            --border-color: #2c3e50;
            --border-light: #34495e;
            --shadow: rgba(0,0,0,0.3);
            --success: #2ecc71;
            --danger: #e74c3c;
            --warning: #f1c40f;
            --info: #3498db;
        }
        body {
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        /* Dark mode table overrides */
        .data-table {
            background: var(--bg-card) !important;
        }
        .data-table th {
            background: var(--bg-nav) !important;
            color: var(--text-nav) !important;
        }
        .data-table td {
            border-bottom-color: var(--border-light) !important;
            color: var(--text-primary) !important;
        }
        .data-table tr:hover {
            background: var(--bg-secondary) !important;
        }
        .data-table tr.disabled {
            color: var(--text-secondary) !important;
            background: var(--bg-secondary) !important;
        }
        /* Dark mode form inputs */
        input[type="text"], input[type="password"], input[type="email"],
        input[type="number"], select, textarea {
            background: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        input:focus, select:focus, textarea:focus {
            border-color: var(--info) !important;
        }
        /* Dark mode modals */
        .modal {
            background: var(--bg-card) !important;
            color: var(--text-primary) !important;
        }
        .modal h2 {
            color: var(--text-primary) !important;
        }
        .form-group label {
            color: var(--text-primary) !important;
        }
        /* Dark mode cards and containers */
        .admin-container, .stats-bar, .empty-state {
            color: var(--text-primary);
        }
        .stats-bar {
            background: var(--bg-secondary) !important;
        }
        .stat-value {
            color: var(--text-primary) !important;
        }
        .stat-label {
            color: var(--text-secondary) !important;
        }
        .breadcrumb {
            color: var(--text-secondary) !important;
        }
        .message {
            color: var(--text-primary);
        }
        /* Dark mode badges - keep colors visible */
        .badge-success {
            background: rgba(39, 174, 96, 0.2) !important;
            color: var(--success) !important;
        }
        .badge-secondary {
            background: rgba(149, 165, 166, 0.2) !important;
            color: var(--text-secondary) !important;
        }
        /* Dark mode search/toolbar */
        .search-box input[type="text"],
        .search-box select {
            background: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }
        .search-box label {
            color: var(--text-secondary) !important;
        }
        /* Dark mode links */
        .breadcrumb a {
            color: var(--info) !important;
        }
        /* Admin page header */
        .admin-header h1 {
            color: var(--text-primary) !important;
        }
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
        .nav-lab {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #34495e;
            padding: 8px 12px;
            border-radius: 4px;
            margin-right: 10px;
        }
        .nav-lab-icon {
            font-size: 1rem;
        }
        .nav-lab-name {
            font-weight: 500;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .nav-lab-switch {
            background: none;
            border: 1px solid rgba(255,255,255,0.3);
            color: #fff;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.75rem;
            margin-left: 5px;
        }
        .nav-lab-switch:hover {
            background: rgba(255,255,255,0.1);
        }
        /* Settings dropdown */
        .nav-settings {
            position: relative;
        }
        .nav-settings-btn {
            background: none;
            border: 1px solid rgba(255,255,255,0.3);
            color: var(--text-nav);
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .nav-settings-btn:hover {
            background: rgba(255,255,255,0.1);
        }
        .nav-settings-dropdown {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            box-shadow: 0 4px 12px var(--shadow);
            min-width: 180px;
            z-index: 1000;
            margin-top: 5px;
        }
        .nav-settings-dropdown.open {
            display: block;
        }
        .nav-settings-section {
            padding: 10px 15px;
            border-bottom: 1px solid var(--border-light);
        }
        .nav-settings-section:last-child {
            border-bottom: none;
        }
        .nav-settings-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .nav-settings-options {
            display: flex;
            gap: 5px;
        }
        .nav-settings-option {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid var(--border-color);
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            text-align: center;
            transition: all 0.2s;
        }
        .nav-settings-option:hover {
            border-color: var(--info);
        }
        .nav-settings-option.active {
            background: var(--info);
            color: #fff;
            border-color: var(--info);
        }
    </style>
</head>
<body>
    <nav class="nav-bar">
        <a href="/biovarase/dashboard<?= $labIdParam ?>" class="nav-brand">Biovarase</a>

        <ul class="nav-menu">
            <!-- Always visible -->
            <li><a href="/biovarase/dashboard<?= $labIdParam ?>" class="<?= $currentPage === 'dashboard' ? 'active' : '' ?>"><?= t('Workstations') ?></a></li>

            <?php if (isLoggedIn()): ?>
                <!-- Logged in users -->
                <?php if (canValidateQC()): ?>
                <li><a href="/biovarase/batches<?= $labIdParam ?>" class="<?= $currentPage === 'batches' ? 'active' : '' ?>"><?= t('Batches') ?></a></li>
                <?php endif; ?>

                <?php if (isAdmin()): ?>
                <li><a href="/biovarase/admin<?= $labIdParam ?>" class="<?= $currentPage === 'admin' ? 'active' : '' ?>"><?= t('Admin') ?></a></li>
                <?php endif; ?>
            <?php endif; ?>
        </ul>

        <div class="nav-user">
            <?php if (isLoggedIn()): ?>
                <?php if ($workingLabName): ?>
                <div class="nav-lab">
                    <span class="nav-lab-icon">🏥</span>
                    <span class="nav-lab-name"><?= htmlspecialchars($workingLabName) ?></span>
                    <?php if (isAppAdmin()): ?>
                    <a href="/biovarase/select-lab" class="nav-lab-switch"><?= t('Change') ?></a>
                    <?php endif; ?>
                </div>
                <?php endif; ?>
                <div class="nav-user-info">
                    <div class="nav-user-name"><?= htmlspecialchars($currentUser['last_name'] . ' ' . ($currentUser['first_name'] ?? '')) ?></div>
                    <div class="nav-user-role"><?= getRoleName($currentRole) ?></div>
                </div>
            <?php endif; ?>

            <!-- Settings dropdown -->
            <div class="nav-settings">
                <button class="nav-settings-btn" onclick="toggleSettings()" title="<?= t('Settings') ?>">
                    ⚙️
                </button>
                <div class="nav-settings-dropdown" id="settingsDropdown">
                    <div class="nav-settings-section">
                        <div class="nav-settings-label"><?= t('Language') ?></div>
                        <div class="nav-settings-options">
                            <button class="nav-settings-option <?= $currentLang === 'it' ? 'active' : '' ?>" onclick="setLanguage('it')">🇮🇹 IT</button>
                            <button class="nav-settings-option <?= $currentLang === 'en' ? 'active' : '' ?>" onclick="setLanguage('en')">🇬🇧 EN</button>
                        </div>
                    </div>
                    <div class="nav-settings-section">
                        <div class="nav-settings-label"><?= t('Theme') ?></div>
                        <div class="nav-settings-options">
                            <button class="nav-settings-option" id="themeLightBtn" onclick="setTheme('light')">☀️ <?= t('Light') ?></button>
                            <button class="nav-settings-option" id="themeDarkBtn" onclick="setTheme('dark')">🌙 <?= t('Dark') ?></button>
                        </div>
                    </div>
                </div>
            </div>

            <?php if (isLoggedIn()): ?>
                <a href="/biovarase/logout" class="nav-btn nav-btn-logout"><?= t('Logout') ?></a>
            <?php else: ?>
                <a href="/biovarase/login" class="nav-btn"><?= t('Login') ?></a>
            <?php endif; ?>
        </div>
    </nav>

    <script>
    // Settings dropdown toggle
    function toggleSettings() {
        document.getElementById('settingsDropdown').classList.toggle('open');
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.nav-settings')) {
            document.getElementById('settingsDropdown').classList.remove('open');
        }
    });

    // Language switcher - set cookie directly from JS
    function setLanguage(lang) {
        // Set cookie for 1 year
        const expires = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toUTCString();
        document.cookie = 'biovarase_lang=' + lang + '; expires=' + expires + '; path=/biovarase; SameSite=Strict';
        location.reload();
    }

    // Theme switcher
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('biovarase-theme', theme);
        updateThemeButtons(theme);
    }

    function updateThemeButtons(theme) {
        document.getElementById('themeLightBtn').classList.toggle('active', theme === 'light');
        document.getElementById('themeDarkBtn').classList.toggle('active', theme === 'dark');
    }

    // Load saved theme on page load
    (function() {
        const savedTheme = localStorage.getItem('biovarase-theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => updateThemeButtons(savedTheme));
        } else {
            updateThemeButtons(savedTheme);
        }
    })();
    </script>
