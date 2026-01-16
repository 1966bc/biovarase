<?php
/**
 * Generic CRUD component for simple tables (pk, description, status)
 *
 * Usage:
 *   $config = [
 *       'table' => 'methods',
 *       'pk' => 'method_id',
 *       'title' => 'Methods',
 *       'title_singular' => 'Method',
 *       'description_maxlen' => 30,
 *       'description_unique' => true,
 *       'extra_fields' => [],  // Optional: ['sample' => ['label' => 'Symbol', 'maxlen' => 1]]
 *       'check_fk_tables' => ['assays', 'test_methods'],  // Tables to check before delete
 *       'fk_field' => 'method_id',  // FK field name in related tables
 *       'role_required' => 0,  // 0 = App Admin only
 *   ];
 *   include __DIR__ . '/../includes/crud_simple.php';
 */

// Validate config
if (!isset($config) || !is_array($config)) {
    die('CRUD config not set');
}

$table = $config['table'];
$pk = $config['pk'];
$title = $config['title'];
$titleSingular = $config['title_singular'];
$descMaxLen = isset($config['description_maxlen']) ? $config['description_maxlen'] : 255;
$descUnique = isset($config['description_unique']) ? $config['description_unique'] : false;
$extraFields = isset($config['extra_fields']) ? $config['extra_fields'] : [];
$checkFkTables = isset($config['check_fk_tables']) ? $config['check_fk_tables'] : [];
$fkField = isset($config['fk_field']) ? $config['fk_field'] : $pk;
$roleRequired = isset($config['role_required']) ? $config['role_required'] : 0;
$allowDelete = isset($config['allow_delete']) ? $config['allow_delete'] : false;

// Check permission
if (getCurrentRole() > $roleRequired) {
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
            $description = trim($_POST['description']);
            if (empty($description)) {
                throw new Exception(t('Description is required'));
            }

            $fields = ['description', 'status'];
            $values = [$description, 1];
            $placeholders = ['?', '?'];

            // Extra fields
            foreach ($extraFields as $field => $fieldConfig) {
                $fields[] = $field;
                $values[] = trim($_POST[$field]);
                $placeholders[] = '?';
            }

            $sql = "INSERT INTO $table (" . implode(', ', $fields) . ") VALUES (" . implode(', ', $placeholders) . ")";
            $stmt = $pdo->prepare($sql);
            $stmt->execute($values);
            $message = t($titleSingular) . " '$description' " . t('created successfully');
            $messageType = 'success';

        } elseif ($action === 'update') {
            $id = intval($_POST[$pk]);
            $description = trim($_POST['description']);
            $status = isset($_POST['status']) ? 1 : 0;

            if (empty($description)) {
                throw new Exception(t('Description is required'));
            }

            $sets = ['description = ?', 'status = ?'];
            $values = [$description, $status];

            // Extra fields
            foreach ($extraFields as $field => $fieldConfig) {
                $sets[] = "$field = ?";
                $values[] = trim($_POST[$field]);
            }

            $values[] = $id;
            $sql = "UPDATE $table SET " . implode(', ', $sets) . " WHERE $pk = ?";
            $stmt = $pdo->prepare($sql);
            $stmt->execute($values);
            $message = t($titleSingular) . ' ' . t('updated successfully');
            $messageType = 'success';

        } elseif ($action === 'delete' && $allowDelete) {
            $id = intval($_POST[$pk]);

            // Check FK constraints
            foreach ($checkFkTables as $fkTable) {
                $stmt = $pdo->prepare("SELECT COUNT(*) FROM $fkTable WHERE $fkField = ?");
                $stmt->execute([$id]);
                if ($stmt->fetchColumn() > 0) {
                    throw new Exception(t('Cannot delete: record is in use') . " ($fkTable)");
                }
            }

            $stmt = $pdo->prepare("DELETE FROM $table WHERE $pk = ?");
            $stmt->execute([$id]);
            $message = t($titleSingular) . ' ' . t('deleted successfully');
            $messageType = 'success';
        }
    } catch (PDOException $e) {
        if (strpos($e->getMessage(), 'Duplicate entry') !== false) {
            $message = t('A record with this description already exists');
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

    // Build SELECT with extra fields
    $selectFields = ["$pk", 'description', 'status'];
    foreach ($extraFields as $field => $fieldConfig) {
        $selectFields[] = $field;
    }

    $sql = "SELECT " . implode(', ', $selectFields) . " FROM $table WHERE 1=1";
    $params = [];

    if (!empty($search)) {
        $sql .= " AND description LIKE ?";
        $params[] = "%$search%";
    }
    if (!$showDisabled) {
        $sql .= " AND status = 1";
    }
    $sql .= " ORDER BY description";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Counts
    $stmt = $pdo->query("SELECT COUNT(*) FROM $table WHERE status = 1");
    $activeCount = $stmt->fetchColumn();
    $stmt = $pdo->query("SELECT COUNT(*) FROM $table WHERE status = 0");
    $disabledCount = $stmt->fetchColumn();

} catch (PDOException $e) {
    $rows = [];
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
    .search-box { display: flex; gap: 10px; align-items: center; }
    .search-box input[type="text"] { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; width: 250px; }
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
    .modal { background: #fff; border-radius: 8px; padding: 20px; min-width: 400px; max-width: 500px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
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
        <a href="/biovarase/admin"><?= t('Admin') ?></a> / <?= t($title) ?>
    </div>

    <div class="admin-header">
        <h1><?= t($title) ?></h1>
        <button class="btn btn-success" onclick="openCreateModal()">+ <?= t('New') ?> <?= t($titleSingular) ?></button>
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
            <label>
                <input type="checkbox" name="show_disabled" <?= $showDisabled ? 'checked' : '' ?> onchange="this.form.submit()">
                <?= t('Show disabled') ?>
            </label>
            <button type="submit" class="btn btn-primary"><?= t('Search') ?></button>
            <?php if ($search || $showDisabled): ?>
            <a href="?reset=1" class="btn btn-secondary"><?= t('Reset') ?></a>
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
                <?php foreach ($extraFields as $field => $fieldConfig): ?>
                <th><?= t($fieldConfig['label']) ?></th>
                <?php endforeach; ?>
                <th><?= t('Description') ?></th>
                <th><?= t('Status') ?></th>
                <th><?= t('Actions') ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($rows as $row): ?>
            <tr class="<?= $row['status'] ? '' : 'disabled' ?>">
                <td><?= $row[$pk] ?></td>
                <?php foreach ($extraFields as $field => $fieldConfig): ?>
                <td><?= htmlspecialchars($row[$field]) ?></td>
                <?php endforeach; ?>
                <td><?= htmlspecialchars($row['description']) ?></td>
                <td>
                    <?php if ($row['status']): ?>
                    <span class="badge badge-success"><?= t('Active') ?></span>
                    <?php else: ?>
                    <span class="badge badge-secondary"><?= t('Disabled') ?></span>
                    <?php endif; ?>
                </td>
                <td class="actions-cell">
                    <button class="btn btn-primary btn-sm" onclick="openEditModal(<?= htmlspecialchars(json_encode($row)) ?>)"><?= t('Edit') ?></button>
                    <?php if ($allowDelete): ?>
                    <button class="btn btn-danger btn-sm" onclick="confirmDelete(<?= $row[$pk] ?>, '<?= htmlspecialchars(addslashes($row['description'])) ?>')"><?= t('Delete') ?></button>
                    <?php endif; ?>
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
        <h2 id="modalTitle"><?= t('New') ?> <?= t($titleSingular) ?></h2>
        <form method="post" id="editForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="<?= $pk ?>" id="formPk" value="">

            <?php foreach ($extraFields as $field => $fieldConfig): ?>
            <div class="form-group">
                <label for="<?= $field ?>"><?= t($fieldConfig['label']) ?> *</label>
                <input type="text" id="<?= $field ?>" name="<?= $field ?>" required maxlength="<?= $fieldConfig['maxlen'] ?>">
            </div>
            <?php endforeach; ?>

            <div class="form-group">
                <label for="description"><?= t('Description') ?> *</label>
                <input type="text" id="description" name="description" required maxlength="<?= $descMaxLen ?>">
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

<?php if ($allowDelete): ?>
<!-- Delete Confirmation Modal -->
<div class="modal-overlay" id="deleteModal">
    <div class="modal">
        <h2><?= t('Confirm Deletion') ?></h2>
        <p><?= t('Are you sure you want to delete') ?> "<span id="deleteItemName"></span>"?</p>
        <p style="color: #e74c3c; font-size: 0.9rem;"><?= t('This action cannot be undone.') ?></p>
        <form method="post" id="deleteForm">
            <input type="hidden" name="action" value="delete">
            <input type="hidden" name="<?= $pk ?>" id="deletePk" value="">
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeDeleteModal()"><?= t('Cancel') ?></button>
                <button type="submit" class="btn btn-danger"><?= t('Delete') ?></button>
            </div>
        </form>
    </div>
</div>
<?php endif; ?>

<script>
const pkField = '<?= $pk ?>';
const extraFields = <?= json_encode(array_keys($extraFields)) ?>;

function openCreateModal() {
    document.getElementById('modalTitle').textContent = '<?= t('New') ?> <?= t($titleSingular) ?>';
    document.getElementById('formAction').value = 'create';
    document.getElementById('formPk').value = '';
    document.getElementById('description').value = '';
    extraFields.forEach(f => { if(document.getElementById(f)) document.getElementById(f).value = ''; });
    document.getElementById('status').checked = true;
    document.getElementById('statusGroup').style.display = 'none';
    document.getElementById('submitBtn').textContent = '<?= t('Create') ?>';
    document.getElementById('editModal').classList.add('active');
    (extraFields.length > 0 ? document.getElementById(extraFields[0]) : document.getElementById('description')).focus();
}

function openEditModal(row) {
    document.getElementById('modalTitle').textContent = '<?= t('Edit') ?> <?= t($titleSingular) ?>';
    document.getElementById('formAction').value = 'update';
    document.getElementById('formPk').value = row[pkField];
    document.getElementById('description').value = row.description;
    extraFields.forEach(f => { if(document.getElementById(f)) document.getElementById(f).value = row[f] || ''; });
    document.getElementById('status').checked = row.status == 1;
    document.getElementById('statusGroup').style.display = 'block';
    document.getElementById('submitBtn').textContent = '<?= t('Save') ?>';
    document.getElementById('editModal').classList.add('active');
    (extraFields.length > 0 ? document.getElementById(extraFields[0]) : document.getElementById('description')).focus();
}

function closeModal() { document.getElementById('editModal').classList.remove('active'); }

<?php if ($allowDelete): ?>
function confirmDelete(id, name) {
    document.getElementById('deletePk').value = id;
    document.getElementById('deleteItemName').textContent = name;
    document.getElementById('deleteModal').classList.add('active');
}

function closeDeleteModal() { document.getElementById('deleteModal').classList.remove('active'); }
<?php endif; ?>

document.getElementById('editModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
<?php if ($allowDelete): ?>
document.getElementById('deleteModal').addEventListener('click', function(e) { if (e.target === this) closeDeleteModal(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeModal(); closeDeleteModal(); } });
<?php else: ?>
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeModal(); } });
<?php endif; ?>
</script>

<?php require_once __DIR__ . '/footer.php'; ?>
