<?php
/**
 * CRUD for Organizations
 * Hierarchical structure: country → region → site → lab → section
 * App Admin only
 */

$pageTitle = 'Organizations - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

// Check permission - App Admin only
if (getCurrentRole() > 0) {
    header('Location: /biovarase/admin');
    exit;
}

// Org types and their allowed parents
$orgTypes = [
    'country' => ['label' => 'Country', 'parent_types' => []],
    'region' => ['label' => 'Region', 'parent_types' => ['country']],
    'site' => ['label' => 'Site', 'parent_types' => ['region']],
    'lab' => ['label' => 'Laboratory', 'parent_types' => ['site']],
    'section' => ['label' => 'Section', 'parent_types' => ['lab']],
];

// Handle POST actions
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? $_POST['action'] : '';

    try {
        $pdo = getDbConnection();

        if ($action === 'create') {
            $org_type = $_POST['org_type'];
            $parent_id = !empty($_POST['parent_id']) ? intval($_POST['parent_id']) : null;
            $code = trim($_POST['code']) ?: null;
            $description = trim($_POST['description']);

            if (empty($description)) {
                throw new Exception(t('Description is required'));
            }
            if (!isset($orgTypes[$org_type])) {
                throw new Exception(t('Invalid organization type'));
            }

            // Validate parent based on org_type
            $parentTypes = $orgTypes[$org_type]['parent_types'];
            if (empty($parentTypes) && $parent_id !== null) {
                throw new Exception(t('Countries cannot have a parent'));
            }
            if (!empty($parentTypes) && $parent_id === null) {
                throw new Exception(t('Parent is required for this type'));
            }

            $stmt = $pdo->prepare("INSERT INTO organizations (org_type, parent_id, code, description, status) VALUES (?, ?, ?, ?, 1)");
            $stmt->execute([$org_type, $parent_id, $code, $description]);
            $message = t('Organization') . " '$description' " . t('created successfully');
            $messageType = 'success';

        } elseif ($action === 'update') {
            $id = intval($_POST['org_id']);
            $org_type = $_POST['org_type'];
            $parent_id = !empty($_POST['parent_id']) ? intval($_POST['parent_id']) : null;
            $code = trim($_POST['code']) ?: null;
            $description = trim($_POST['description']);
            $status = isset($_POST['status']) ? 1 : 0;

            if (empty($description)) {
                throw new Exception(t('Description is required'));
            }

            // Prevent circular reference
            if ($parent_id === $id) {
                throw new Exception(t('Organization cannot be its own parent'));
            }

            $stmt = $pdo->prepare("UPDATE organizations SET org_type = ?, parent_id = ?, code = ?, description = ?, status = ? WHERE org_id = ?");
            $stmt->execute([$org_type, $parent_id, $code, $description, $status, $id]);
            $message = t('Organization') . ' ' . t('updated successfully');
            $messageType = 'success';

        }
    } catch (PDOException $e) {
        $message = t('Database error') . ': ' . $e->getMessage();
        $messageType = 'error';
    } catch (Exception $e) {
        $message = $e->getMessage();
        $messageType = 'error';
    }
}

// Fetch data
try {
    $pdo = getDbConnection();

    $search = isset($_GET['search']) ? trim($_GET['search']) : '';
    $showDisabled = isset($_GET['show_disabled']);
    $filterType = isset($_GET['org_type']) ? $_GET['org_type'] : '';

    // Get all organizations for hierarchy display and parent selection
    $stmt = $pdo->query("SELECT org_id, parent_id, org_type, code, description, status FROM organizations ORDER BY org_type, description");
    $allOrgs = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Build lookup by id
    $orgsById = [];
    foreach ($allOrgs as $org) {
        $orgsById[$org['org_id']] = $org;
    }

    // Function to get full path
    function getOrgPath($orgId, &$orgsById) {
        $path = [];
        $current = $orgId;
        $maxDepth = 10;
        while ($current && $maxDepth-- > 0) {
            if (isset($orgsById[$current])) {
                array_unshift($path, $orgsById[$current]['description']);
                $current = $orgsById[$current]['parent_id'];
            } else {
                break;
            }
        }
        return implode(' → ', $path);
    }

    // Build query for display
    $sql = "SELECT o.org_id, o.parent_id, o.org_type, o.code, o.description, o.status,
                   p.description as parent_name
            FROM organizations o
            LEFT JOIN organizations p ON o.parent_id = p.org_id
            WHERE 1=1";
    $params = [];

    if (!empty($search)) {
        $sql .= " AND (o.description LIKE ? OR o.code LIKE ?)";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }
    if (!$showDisabled) {
        $sql .= " AND o.status = 1";
    }
    if (!empty($filterType)) {
        $sql .= " AND o.org_type = ?";
        $params[] = $filterType;
    }
    $sql .= " ORDER BY FIELD(o.org_type, 'country', 'region', 'site', 'lab', 'section'), o.description";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Counts by type
    $stmt = $pdo->query("SELECT org_type, COUNT(*) as cnt FROM organizations WHERE status = 1 GROUP BY org_type");
    $typeCounts = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $typeCounts[$row['org_type']] = $row['cnt'];
    }

} catch (PDOException $e) {
    $rows = [];
    $allOrgs = [];
    $orgsById = [];
    $typeCounts = [];
    $message = t('Data loading error') . ': ' . $e->getMessage();
    $messageType = 'error';
}
?>

<style>
    .admin-container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    .admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .admin-header h1 { margin: 0; color: #2c3e50; }
    .breadcrumb { color: #7f8c8d; margin-bottom: 10px; }
    .breadcrumb a { color: #3498db; text-decoration: none; }
    .breadcrumb a:hover { text-decoration: underline; }
    .stats-bar { display: flex; gap: 15px; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; flex-wrap: wrap; }
    .stat-item { display: flex; align-items: center; gap: 8px; padding: 5px 10px; background: #fff; border-radius: 4px; }
    .stat-value { font-size: 1.2rem; font-weight: bold; color: #2c3e50; }
    .stat-label { color: #7f8c8d; font-size: 0.85rem; }
    .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; gap: 15px; flex-wrap: wrap; }
    .search-box { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .search-box input[type="text"] { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; width: 200px; }
    .search-box select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; }
    .search-box label { display: flex; align-items: center; gap: 5px; font-size: 0.9rem; color: #666; }
    .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; }
    .btn-primary { background: #3498db; color: #fff; }
    .btn-primary:hover { background: #2980b9; }
    .btn-success { background: #27ae60; color: #fff; }
    .btn-success:hover { background: #219a52; }
    .btn-danger { background: #e74c3c; color: #fff; }
    .btn-danger:hover { background: #c0392b; }
    .btn-secondary { background: #95a5a6; color: #fff; }
    .btn-secondary:hover { background: #7f8c8d; }
    .btn-sm { padding: 4px 8px; font-size: 0.8rem; }
    .data-table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
    .data-table th, .data-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ecf0f1; }
    .data-table th { background: #2c3e50; color: #fff; font-weight: 500; }
    .data-table tr:hover { background: #f8f9fa; }
    .data-table tr.disabled { color: #999; background: #f5f5f5; }
    .actions-cell { white-space: nowrap; }
    .badge { padding: 3px 8px; border-radius: 3px; font-size: 0.75rem; }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-secondary { background: #e2e3e5; color: #6c757d; }
    .badge-type { background: #e3f2fd; color: #1565c0; }
    .badge-type.country { background: #ffebee; color: #c62828; }
    .badge-type.region { background: #fff3e0; color: #e65100; }
    .badge-type.site { background: #e8f5e9; color: #2e7d32; }
    .badge-type.lab { background: #e3f2fd; color: #1565c0; }
    .badge-type.section { background: #f3e5f5; color: #7b1fa2; }
    .message { padding: 12px 15px; border-radius: 4px; margin-bottom: 20px; }
    .message-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .message-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; }
    .modal-overlay.active { display: flex; }
    .modal { background: #fff; border-radius: 8px; padding: 20px; min-width: 500px; max-width: 600px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .modal h2 { margin: 0 0 20px 0; color: #2c3e50; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #2c3e50; }
    .form-group input[type="text"], .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
    .form-group input[type="checkbox"] { margin-right: 8px; }
    .form-group small { color: #7f8c8d; font-size: 0.85rem; }
    .form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
    .empty-state { text-align: center; padding: 40px; color: #7f8c8d; }
    .path-cell { font-size: 0.85rem; color: #666; }
</style>

<div class="admin-container">
    <div class="breadcrumb">
        <a href="/biovarase/admin"><?= t('Admin') ?></a> / <?= t('Organizations') ?>
    </div>

    <div class="admin-header">
        <h1><?= t('Organizations') ?></h1>
        <button class="btn btn-success" onclick="openCreateModal()">+ <?= t('New') ?> <?= t('Organization') ?></button>
    </div>

    <?php if ($message): ?>
    <div class="message message-<?= $messageType ?>">
        <?= htmlspecialchars($message) ?>
    </div>
    <?php endif; ?>

    <div class="stats-bar">
        <?php foreach ($orgTypes as $type => $typeInfo): ?>
        <div class="stat-item">
            <span class="stat-value"><?= $typeCounts[$type] ?? 0 ?></span>
            <span class="stat-label"><?= t($typeInfo['label']) ?></span>
        </div>
        <?php endforeach; ?>
    </div>

    <div class="toolbar">
        <form class="search-box" method="get">
            <input type="text" name="search" placeholder="<?= t('Search...') ?>" value="<?= htmlspecialchars($search) ?>">
            <select name="org_type" onchange="this.form.submit()">
                <option value=""><?= t('All types') ?></option>
                <?php foreach ($orgTypes as $type => $typeInfo): ?>
                <option value="<?= $type ?>" <?= $filterType === $type ? 'selected' : '' ?>><?= t($typeInfo['label']) ?></option>
                <?php endforeach; ?>
            </select>
            <label>
                <input type="checkbox" name="show_disabled" <?= $showDisabled ? 'checked' : '' ?> onchange="this.form.submit()">
                <?= t('Show disabled') ?>
            </label>
            <button type="submit" class="btn btn-primary"><?= t('Search') ?></button>
            <?php if ($search || $showDisabled || $filterType): ?>
            <a href="?" class="btn btn-secondary"><?= t('Reset') ?></a>
            <?php endif; ?>
        </form>
    </div>

    <?php if (empty($rows)): ?>
    <div class="empty-state">
        <p><?= t('No records found') ?></p>
    </div>
    <?php else: ?>
    <table class="data-table">
        <thead>
            <tr>
                <th><?= t('ID') ?></th>
                <th><?= t('Type') ?></th>
                <th><?= t('Code') ?></th>
                <th><?= t('Description') ?></th>
                <th><?= t('Path') ?></th>
                <th><?= t('Status') ?></th>
                <th><?= t('Actions') ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($rows as $row): ?>
            <tr class="<?= $row['status'] ? '' : 'disabled' ?>">
                <td><?= $row['org_id'] ?></td>
                <td><span class="badge badge-type <?= $row['org_type'] ?>"><?= t($orgTypes[$row['org_type']]['label']) ?></span></td>
                <td><?= htmlspecialchars($row['code'] ?? '-') ?></td>
                <td><?= htmlspecialchars($row['description']) ?></td>
                <td class="path-cell"><?= htmlspecialchars(getOrgPath($row['org_id'], $orgsById)) ?></td>
                <td>
                    <?php if ($row['status']): ?>
                    <span class="badge badge-success"><?= t('Active') ?></span>
                    <?php else: ?>
                    <span class="badge badge-secondary"><?= t('Disabled') ?></span>
                    <?php endif; ?>
                </td>
                <td class="actions-cell">
                    <button class="btn btn-primary btn-sm" onclick="openEditModal(<?= htmlspecialchars(json_encode($row)) ?>)"><?= t('Edit') ?></button>
                </td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</div>

<!-- Create/Edit Modal -->
<div class="modal-overlay" id="editModal">
    <div class="modal">
        <h2 id="modalTitle"><?= t('New') ?> <?= t('Organization') ?></h2>
        <form method="post" id="editForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="org_id" id="formPk" value="">

            <div class="form-group">
                <label for="org_type"><?= t('Type') ?> *</label>
                <select id="org_type" name="org_type" required onchange="updateParentOptions()">
                    <?php foreach ($orgTypes as $type => $typeInfo): ?>
                    <option value="<?= $type ?>"><?= t($typeInfo['label']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="form-group" id="parentGroup">
                <label for="parent_id"><?= t('Parent') ?> *</label>
                <select id="parent_id" name="parent_id">
                    <option value=""><?= t('Select parent...') ?></option>
                </select>
                <small id="parentHelp"></small>
            </div>

            <div class="form-group">
                <label for="code"><?= t('Code') ?></label>
                <input type="text" id="code" name="code" maxlength="20" placeholder="e.g., ITA, LAZ">
            </div>

            <div class="form-group">
                <label for="description"><?= t('Description') ?> *</label>
                <input type="text" id="description" name="description" required maxlength="255">
            </div>

            <div class="form-group" id="statusGroup" style="display: none;">
                <label>
                    <input type="checkbox" id="status" name="status" checked>
                    <?= t('Active') ?>
                </label>
            </div>

            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()"><?= t('Cancel') ?></button>
                <button type="submit" class="btn btn-success" id="submitBtn"><?= t('Create') ?></button>
            </div>
        </form>
    </div>
</div>

<script>
// Organization data for parent selection
const allOrgs = <?= json_encode($allOrgs) ?>;
const orgTypes = <?= json_encode($orgTypes) ?>;

function updateParentOptions() {
    const typeSelect = document.getElementById('org_type');
    const parentSelect = document.getElementById('parent_id');
    const parentGroup = document.getElementById('parentGroup');
    const parentHelp = document.getElementById('parentHelp');
    const selectedType = typeSelect.value;
    const typeConfig = orgTypes[selectedType];

    // Clear options
    parentSelect.innerHTML = '<option value=""><?= t('Select parent...') ?></option>';

    if (typeConfig.parent_types.length === 0) {
        // Country has no parent
        parentGroup.style.display = 'none';
        parentSelect.required = false;
        parentHelp.textContent = '';
    } else {
        parentGroup.style.display = 'block';
        parentSelect.required = true;

        // Add matching parents
        const allowedTypes = typeConfig.parent_types;
        allOrgs.filter(o => allowedTypes.includes(o.org_type) && o.status == 1)
            .forEach(org => {
                const opt = document.createElement('option');
                opt.value = org.org_id;
                opt.textContent = org.description + (org.code ? ' (' + org.code + ')' : '');
                parentSelect.appendChild(opt);
            });

        parentHelp.textContent = '<?= t('Select a') ?> ' + allowedTypes.map(t => orgTypes[t].label).join(' <?= t('or') ?> ');
    }
}

function openCreateModal() {
    document.getElementById('modalTitle').textContent = '<?= t('New') ?> <?= t('Organization') ?>';
    document.getElementById('formAction').value = 'create';
    document.getElementById('formPk').value = '';
    document.getElementById('org_type').value = 'country';
    document.getElementById('code').value = '';
    document.getElementById('description').value = '';
    document.getElementById('status').checked = true;
    document.getElementById('statusGroup').style.display = 'none';
    document.getElementById('submitBtn').textContent = '<?= t('Create') ?>';
    updateParentOptions();
    document.getElementById('editModal').classList.add('active');
    document.getElementById('org_type').focus();
}

function openEditModal(row) {
    document.getElementById('modalTitle').textContent = '<?= t('Edit') ?> <?= t('Organization') ?>';
    document.getElementById('formAction').value = 'update';
    document.getElementById('formPk').value = row.org_id;
    document.getElementById('org_type').value = row.org_type;
    updateParentOptions();
    document.getElementById('parent_id').value = row.parent_id || '';
    document.getElementById('code').value = row.code || '';
    document.getElementById('description').value = row.description;
    document.getElementById('status').checked = row.status == 1;
    document.getElementById('statusGroup').style.display = 'block';
    document.getElementById('submitBtn').textContent = '<?= t('Save') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('org_type').focus();
}

function closeModal() { document.getElementById('editModal').classList.remove('active'); }

document.getElementById('editModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeModal(); } });

// Initialize
updateParentOptions();
</script>

<?php require_once __DIR__ . '/../../includes/footer.php'; ?>
