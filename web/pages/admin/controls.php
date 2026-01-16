<?php
/**
 * CRUD for Controls
 * Global table (App Admin only) - QC control materials (Bio-Rad, Roche, etc.)
 */

$pageTitle = 'Controls - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

// Check permission - App Admin only
if (getCurrentRole() > 0) {
    header('Location: /biovarase/admin');
    exit;
}

// Handle POST actions
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? $_POST['action'] : '';

    try {
        $pdo = getDbConnection();

        if ($action === 'create') {
            $supplier_id = intval($_POST['supplier_id']);
            $description = trim($_POST['description']);
            $reference = trim($_POST['reference']);

            if (empty($description)) {
                throw new Exception(t('Description is required'));
            }
            if ($supplier_id <= 0) {
                throw new Exception(t('Supplier is required'));
            }

            $stmt = $pdo->prepare("INSERT INTO controls (supplier_id, description, reference, status) VALUES (?, ?, ?, 1)");
            $stmt->execute([$supplier_id, $description, $reference ?: null]);
            $message = t('Control') . " '$description' " . t('created successfully');
            $messageType = 'success';

        } elseif ($action === 'update') {
            $id = intval($_POST['control_id']);
            $supplier_id = intval($_POST['supplier_id']);
            $description = trim($_POST['description']);
            $reference = trim($_POST['reference']);
            $status = isset($_POST['status']) ? 1 : 0;

            if (empty($description)) {
                throw new Exception(t('Description is required'));
            }
            if ($supplier_id <= 0) {
                throw new Exception(t('Supplier is required'));
            }

            $stmt = $pdo->prepare("UPDATE controls SET supplier_id = ?, description = ?, reference = ?, status = ? WHERE control_id = ?");
            $stmt->execute([$supplier_id, $description, $reference ?: null, $status, $id]);
            $message = t('Control') . ' ' . t('updated successfully');
            $messageType = 'success';

        }
    } catch (PDOException $e) {
        if (strpos($e->getMessage(), 'Duplicate entry') !== false) {
            $message = t('A control with this description already exists');
        } else {
            $message = t('Database error') . ': ' . $e->getMessage();
        }
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
    $filterSupplier = isset($_GET['supplier_id']) ? intval($_GET['supplier_id']) : 0;

    // Get suppliers for filter and forms
    $stmt = $pdo->query("SELECT supplier_id, description FROM suppliers WHERE status = 1 ORDER BY description");
    $suppliers = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Build query
    $sql = "SELECT c.control_id, c.supplier_id, c.description, c.reference, c.status,
                   s.description as supplier_name
            FROM controls c
            LEFT JOIN suppliers s ON c.supplier_id = s.supplier_id
            WHERE 1=1";
    $params = [];

    if (!empty($search)) {
        $sql .= " AND (c.description LIKE ? OR c.reference LIKE ? OR s.description LIKE ?)";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }
    if (!$showDisabled) {
        $sql .= " AND c.status = 1";
    }
    if ($filterSupplier > 0) {
        $sql .= " AND c.supplier_id = ?";
        $params[] = $filterSupplier;
    }
    $sql .= " ORDER BY s.description, c.description";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Counts
    $stmt = $pdo->query("SELECT COUNT(*) FROM controls WHERE status = 1");
    $activeCount = $stmt->fetchColumn();
    $stmt = $pdo->query("SELECT COUNT(*) FROM controls WHERE status = 0");
    $disabledCount = $stmt->fetchColumn();

} catch (PDOException $e) {
    $rows = [];
    $suppliers = [];
    $message = t('Data loading error') . ': ' . $e->getMessage();
    $messageType = 'error';
    $activeCount = 0;
    $disabledCount = 0;
}
?>

<style>
    .admin-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .admin-header h1 { margin: 0; color: #2c3e50; }
    .breadcrumb { color: #7f8c8d; margin-bottom: 10px; }
    .breadcrumb a { color: #3498db; text-decoration: none; }
    .breadcrumb a:hover { text-decoration: underline; }
    .stats-bar { display: flex; gap: 20px; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
    .stat-item { display: flex; align-items: center; gap: 8px; }
    .stat-value { font-size: 1.5rem; font-weight: bold; color: #2c3e50; }
    .stat-label { color: #7f8c8d; font-size: 0.9rem; }
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
    .badge { padding: 3px 8px; border-radius: 3px; font-size: 0.8rem; }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-secondary { background: #e2e3e5; color: #6c757d; }
    .message { padding: 12px 15px; border-radius: 4px; margin-bottom: 20px; }
    .message-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .message-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; }
    .modal-overlay.active { display: flex; }
    .modal { background: #fff; border-radius: 8px; padding: 20px; min-width: 450px; max-width: 550px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .modal h2 { margin: 0 0 20px 0; color: #2c3e50; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #2c3e50; }
    .form-group input[type="text"], .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
    .form-group input[type="checkbox"] { margin-right: 8px; }
    .form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
    .empty-state { text-align: center; padding: 40px; color: #7f8c8d; }
</style>

<div class="admin-container">
    <div class="breadcrumb">
        <a href="/biovarase/admin"><?= t('Admin') ?></a> / <?= t('Controls') ?>
    </div>

    <div class="admin-header">
        <h1><?= t('Controls') ?></h1>
        <button class="btn btn-success" onclick="openCreateModal()">+ <?= t('New') ?> <?= t('Control') ?></button>
    </div>

    <?php if ($message): ?>
    <div class="message message-<?= $messageType ?>">
        <?= htmlspecialchars($message) ?>
    </div>
    <?php endif; ?>

    <div class="stats-bar">
        <div class="stat-item">
            <span class="stat-value"><?= $activeCount ?></span>
            <span class="stat-label"><?= t('Active') ?></span>
        </div>
        <div class="stat-item">
            <span class="stat-value"><?= $disabledCount ?></span>
            <span class="stat-label"><?= t('Disabled') ?></span>
        </div>
    </div>

    <div class="toolbar">
        <form class="search-box" method="get">
            <input type="text" name="search" placeholder="<?= t('Search...') ?>" value="<?= htmlspecialchars($search) ?>">
            <select name="supplier_id" onchange="this.form.submit()">
                <option value=""><?= t('All suppliers') ?></option>
                <?php foreach ($suppliers as $s): ?>
                <option value="<?= $s['supplier_id'] ?>" <?= $filterSupplier == $s['supplier_id'] ? 'selected' : '' ?>><?= htmlspecialchars($s['description']) ?></option>
                <?php endforeach; ?>
            </select>
            <label>
                <input type="checkbox" name="show_disabled" <?= $showDisabled ? 'checked' : '' ?> onchange="this.form.submit()">
                <?= t('Show disabled') ?>
            </label>
            <button type="submit" class="btn btn-primary"><?= t('Search') ?></button>
            <?php if ($search || $showDisabled || $filterSupplier): ?>
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
                <th><?= t('Supplier') ?></th>
                <th><?= t('Description') ?></th>
                <th><?= t('Reference') ?></th>
                <th><?= t('Status') ?></th>
                <th><?= t('Actions') ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($rows as $row): ?>
            <tr class="<?= $row['status'] ? '' : 'disabled' ?>">
                <td><?= $row['control_id'] ?></td>
                <td><?= htmlspecialchars($row['supplier_name'] ?? '-') ?></td>
                <td><?= htmlspecialchars($row['description']) ?></td>
                <td><?= htmlspecialchars($row['reference'] ?? '-') ?></td>
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
        <h2 id="modalTitle"><?= t('New') ?> <?= t('Control') ?></h2>
        <form method="post" id="editForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="control_id" id="formPk" value="">

            <div class="form-group">
                <label for="supplier_id"><?= t('Supplier') ?> *</label>
                <select id="supplier_id" name="supplier_id" required>
                    <option value=""><?= t('Select supplier...') ?></option>
                    <?php foreach ($suppliers as $s): ?>
                    <option value="<?= $s['supplier_id'] ?>"><?= htmlspecialchars($s['description']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="form-group">
                <label for="description"><?= t('Description') ?> *</label>
                <input type="text" id="description" name="description" required maxlength="100">
            </div>

            <div class="form-group">
                <label for="reference"><?= t('Reference') ?></label>
                <input type="text" id="reference" name="reference" maxlength="30">
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
function openCreateModal() {
    document.getElementById('modalTitle').textContent = '<?= t('New') ?> <?= t('Control') ?>';
    document.getElementById('formAction').value = 'create';
    document.getElementById('formPk').value = '';
    document.getElementById('supplier_id').value = '';
    document.getElementById('description').value = '';
    document.getElementById('reference').value = '';
    document.getElementById('status').checked = true;
    document.getElementById('statusGroup').style.display = 'none';
    document.getElementById('submitBtn').textContent = '<?= t('Create') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('supplier_id').focus();
}

function openEditModal(row) {
    document.getElementById('modalTitle').textContent = '<?= t('Edit') ?> <?= t('Control') ?>';
    document.getElementById('formAction').value = 'update';
    document.getElementById('formPk').value = row.control_id;
    document.getElementById('supplier_id').value = row.supplier_id;
    document.getElementById('description').value = row.description;
    document.getElementById('reference').value = row.reference || '';
    document.getElementById('status').checked = row.status == 1;
    document.getElementById('statusGroup').style.display = 'block';
    document.getElementById('submitBtn').textContent = '<?= t('Save') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('supplier_id').focus();
}

function closeModal() { document.getElementById('editModal').classList.remove('active'); }

document.getElementById('editModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeModal(); } });
</script>

<?php require_once __DIR__ . '/../../includes/footer.php'; ?>
