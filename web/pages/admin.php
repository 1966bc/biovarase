<?php
/**
 * Admin Hub - Landing page for administration
 *
 * Shows different menu items based on user role:
 * - App Admin (role 0): All master data tables
 * - Lab Admin (role 1-3): Users only
 */

$pageTitle = 'Admin - Biovarase';
require_once __DIR__ . '/../includes/header.php';

// Check permission - must be at least Lab Admin
if (!isAdmin()) {
    header('Location: /biovarase/dashboard');
    exit;
}

$currentRole = getCurrentRole();
$isAppAdmin = ($currentRole === 0);

// Pages that are ready (not WIP)
$readyPages = ['tests', 'methods', 'units', 'samples', 'categories', 'controls', 'equipments', 'suppliers', 'actions', 'organizations', 'users', 'assays', 'workstations'];

// Admin menu items: [label_key, icon, url, app_admin_only, description_key, page_key]
// Labels and descriptions are translation keys
$adminItems = [
    // Master Data (App Admin only)
    ['Tests', 'flask', '/biovarase/admin/tests', true, 'Analytes and laboratory tests', 'tests'],
    ['Methods', 'microscope', '/biovarase/admin/methods', true, 'Analytical methods', 'methods'],
    ['Units', 'ruler', '/biovarase/admin/units', true, 'Units of measurement', 'units'],
    ['Samples', 'vial', '/biovarase/admin/samples', true, 'Sample types', 'samples'],
    ['Categories', 'folder', '/biovarase/admin/categories', false, 'Test categories', 'categories'],
    ['Controls', 'box', '/biovarase/admin/controls', true, 'QC control materials', 'controls'],
    ['Equipments', 'server', '/biovarase/admin/equipments', true, 'Instrumentation', 'equipments'],
    ['Suppliers', 'truck', '/biovarase/admin/suppliers', true, 'Suppliers and manufacturers', 'suppliers'],
    ['Corrective Actions', 'clipboard-check', '/biovarase/admin/actions', true, 'QC corrective actions', 'actions'],
    ['Organizations', 'sitemap', '/biovarase/admin/organizations', true, 'Organizational structure', 'organizations'],
    // Lab management
    ['Workstations', 'desktop', '/biovarase/admin/workstations', false, 'Analytical workstations', 'workstations'],
    ['Assays', 'list-check', '/biovarase/admin/assays', false, 'QC test configuration', 'assays'],
    ['Users', 'users', '/biovarase/admin/users', false, 'User management', 'users'],
];

// Filter items based on role
$visibleItems = array_filter($adminItems, function($item) use ($isAppAdmin) {
    return $isAppAdmin || !$item[3]; // Show if app admin OR not app_admin_only
});
?>

<style>
    .admin-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    .admin-header {
        margin-bottom: 30px;
    }
    .admin-header h1 {
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .admin-header p {
        color: #7f8c8d;
    }
    .admin-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px;
    }
    .admin-card {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-decoration: none;
        color: inherit;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        align-items: flex-start;
        gap: 15px;
    }
    .admin-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .admin-card-icon {
        width: 48px;
        height: 48px;
        background: #3498db;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    .admin-card-content h3 {
        margin: 0 0 5px 0;
        color: #2c3e50;
        font-size: 1.1rem;
    }
    .admin-card-content p {
        margin: 0;
        color: #7f8c8d;
        font-size: 0.9rem;
    }
    .admin-section {
        margin-bottom: 40px;
    }
    .admin-section h2 {
        color: #2c3e50;
        font-size: 1.2rem;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #ecf0f1;
    }
    .admin-card.disabled {
        opacity: 0.5;
        pointer-events: none;
    }
    .badge-wip {
        background: #f39c12;
        color: #fff;
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 3px;
        margin-left: 8px;
    }

    /* Simple icons using CSS */
    .icon-flask::before { content: "🧪"; }
    .icon-microscope::before { content: "🔬"; }
    .icon-ruler::before { content: "📏"; }
    .icon-vial::before { content: "🧫"; }
    .icon-folder::before { content: "📁"; }
    .icon-box::before { content: "📦"; }
    .icon-server::before { content: "🖥️"; }
    .icon-truck::before { content: "🚚"; }
    .icon-clipboard-check::before { content: "📋"; }
    .icon-sitemap::before { content: "🏛️"; }
    .icon-list-check::before { content: "✅"; }
    .icon-users::before { content: "👥"; }
    .icon-desktop::before { content: "🖥️"; }
</style>

<div class="admin-container">
    <div class="admin-header">
        <h1><?= t('Administration') ?></h1>
        <p><?= t('System tables and configuration management') ?></p>
    </div>

    <?php if ($isAppAdmin): ?>
    <div class="admin-section">
        <h2><?= t('Master Data (Global Data)') ?></h2>
        <div class="admin-grid">
            <?php foreach ($visibleItems as $item):
                if (!$item[3]) continue; // Skip non-app-admin items
                $isReady = in_array($item[5], $readyPages);
            ?>
            <a href="<?= htmlspecialchars($item[2]) ?>" class="admin-card<?= $isReady ? '' : ' disabled' ?>">
                <div class="admin-card-icon">
                    <span class="icon-<?= $item[1] ?>"></span>
                </div>
                <div class="admin-card-content">
                    <h3><?= t($item[0]) ?><?= $isReady ? '' : '<span class="badge-wip">WIP</span>' ?></h3>
                    <p><?= t($item[4]) ?></p>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
    </div>
    <?php endif; ?>

    <div class="admin-section">
        <h2><?= t('Laboratory Management') ?></h2>
        <div class="admin-grid">
            <?php foreach ($visibleItems as $item):
                if ($item[3]) continue; // Skip app-admin-only items
                $isReady = in_array($item[5], $readyPages);
            ?>
            <a href="<?= htmlspecialchars($item[2]) ?>" class="admin-card<?= $isReady ? '' : ' disabled' ?>">
                <div class="admin-card-icon">
                    <span class="icon-<?= $item[1] ?>"></span>
                </div>
                <div class="admin-card-content">
                    <h3><?= t($item[0]) ?><?= $isReady ? '' : '<span class="badge-wip">WIP</span>' ?></h3>
                    <p><?= t($item[4]) ?></p>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
