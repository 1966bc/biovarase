<?php
/**
 * CRUD for Assays
 * Lab-level configuration (Lab Admin can manage)
 * Links test + method + unit + sample + category + section
 */

$pageTitle = 'Assays - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

// Check permission - Lab Admin or higher
if (!isAdmin()) {
    header('Location: /biovarase/admin');
    exit;
}

// Require working lab selection
requireWorkingLab();

$currentRole = getCurrentRole();
$workingLabId = getWorkingLabId();

// Handle POST actions
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? $_POST['action'] : '';

    try {
        $pdo = getDbConnection();

        if ($action === 'create') {
            $test_id = intval($_POST['test_id']);
            $method_id = intval($_POST['method_id']);
            $unit_id = intval($_POST['unit_id']);
            $sample_id = intval($_POST['sample_id']);
            $category_id = !empty($_POST['category_id']) ? intval($_POST['category_id']) : null;
            $org_id = !empty($_POST['org_id']) ? intval($_POST['org_id']) : null;
            $code = trim($_POST['code']);
            $description = trim($_POST['description']) ?: null;

            // Goals
            $cvw = floatval($_POST['cvw']);
            $cvb = floatval($_POST['cvb']);
            $imp = floatval($_POST['imp']);
            $bias = floatval($_POST['bias']);
            $teap005 = floatval($_POST['teap005']);
            $teap001 = floatval($_POST['teap001']);
            $to_export = isset($_POST['to_export']) ? 1 : 0;
            $is_mandatory = isset($_POST['is_mandatory']) ? 1 : 0;

            if ($test_id <= 0) throw new Exception(t('Test is required'));
            if ($method_id <= 0) throw new Exception(t('Method is required'));
            if ($unit_id <= 0) throw new Exception(t('Unit is required'));
            if ($sample_id <= 0) throw new Exception(t('Sample is required'));
            if (empty($code)) throw new Exception(t('Code is required'));

            $userId = getCurrentUserId();

            $stmt = $pdo->prepare("INSERT INTO assays (test_id, method_id, unit_id, sample_id, category_id, org_id, code, description, cvw, cvb, imp, bias, teap005, teap001, to_export, is_mandatory, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)");
            $stmt->execute([$test_id, $method_id, $unit_id, $sample_id, $category_id, $org_id, $code, $description, $cvw, $cvb, $imp, $bias, $teap005, $teap001, $to_export, $is_mandatory, $userId]);
            $message = t('Assay') . " '$code' " . t('created successfully');
            $messageType = 'success';

        } elseif ($action === 'update') {
            $id = intval($_POST['assay_id']);
            $test_id = intval($_POST['test_id']);
            $method_id = intval($_POST['method_id']);
            $unit_id = intval($_POST['unit_id']);
            $sample_id = intval($_POST['sample_id']);
            $category_id = !empty($_POST['category_id']) ? intval($_POST['category_id']) : null;
            $org_id = !empty($_POST['org_id']) ? intval($_POST['org_id']) : null;
            $code = trim($_POST['code']);
            $description = trim($_POST['description']) ?: null;

            // Goals
            $cvw = floatval($_POST['cvw']);
            $cvb = floatval($_POST['cvb']);
            $imp = floatval($_POST['imp']);
            $bias = floatval($_POST['bias']);
            $teap005 = floatval($_POST['teap005']);
            $teap001 = floatval($_POST['teap001']);
            $to_export = isset($_POST['to_export']) ? 1 : 0;
            $is_mandatory = isset($_POST['is_mandatory']) ? 1 : 0;
            $status = isset($_POST['status']) ? 1 : 0;

            if ($test_id <= 0) throw new Exception(t('Test is required'));
            if ($method_id <= 0) throw new Exception(t('Method is required'));
            if ($unit_id <= 0) throw new Exception(t('Unit is required'));
            if ($sample_id <= 0) throw new Exception(t('Sample is required'));
            if (empty($code)) throw new Exception(t('Code is required'));

            $userId = getCurrentUserId();

            $stmt = $pdo->prepare("UPDATE assays SET test_id = ?, method_id = ?, unit_id = ?, sample_id = ?, category_id = ?, org_id = ?, code = ?, description = ?, cvw = ?, cvb = ?, imp = ?, bias = ?, teap005 = ?, teap001 = ?, to_export = ?, is_mandatory = ?, status = ?, updated_by = ? WHERE assay_id = ?");
            $stmt->execute([$test_id, $method_id, $unit_id, $sample_id, $category_id, $org_id, $code, $description, $cvw, $cvb, $imp, $bias, $teap005, $teap001, $to_export, $is_mandatory, $status, $userId, $id]);
            $message = t('Assay') . ' ' . t('updated successfully');
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
    $filterSection = isset($_GET['org_id']) ? intval($_GET['org_id']) : 0;

    // Get lookup data for dropdowns (include disabled for existing records)
    $stmt = $pdo->query("SELECT test_id, description, status FROM tests ORDER BY description");
    $tests = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $stmt = $pdo->query("SELECT method_id, description FROM methods WHERE status = 1 ORDER BY description");
    $methods = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $stmt = $pdo->query("SELECT unit_id, description FROM units WHERE status = 1 ORDER BY description");
    $units = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $stmt = $pdo->query("SELECT sample_id, sample, description FROM samples WHERE status = 1 ORDER BY description");
    $samples = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Categories filtered by working lab
    $stmt = $pdo->prepare("SELECT c.category_id, c.description FROM categories c WHERE c.status = 1 AND c.org_id = ? ORDER BY c.description");
    $stmt->execute([$workingLabId]);
    $categories = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Sections under working lab
    $stmt = $pdo->prepare("SELECT org_id, description FROM organizations WHERE parent_id = ? AND org_type = 'section' AND status = 1 ORDER BY description");
    $stmt->execute([$workingLabId]);
    $sections = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Build query for assays list
    $sql = "SELECT a.assay_id, a.test_id, a.method_id, a.unit_id, a.sample_id, a.category_id, a.org_id,
                   a.code, a.description, a.cvw, a.cvb, a.imp, a.bias, a.teap005, a.teap001,
                   a.to_export, a.is_mandatory, a.status,
                   t.description as test_name,
                   m.description as method_name,
                   u.description as unit_name,
                   s.description as sample_name,
                   cat.description as category_name,
                   sec.description as section_name
            FROM assays a
            JOIN tests t ON a.test_id = t.test_id
            JOIN methods m ON a.method_id = m.method_id
            JOIN units u ON a.unit_id = u.unit_id
            JOIN samples s ON a.sample_id = s.sample_id
            LEFT JOIN categories cat ON a.category_id = cat.category_id
            LEFT JOIN organizations sec ON a.org_id = sec.org_id
            WHERE 1=1";
    $params = [];

    // Filter by working lab's sections
    $sql .= " AND (a.org_id IN (SELECT org_id FROM organizations WHERE parent_id = ? AND org_type = 'section') OR a.org_id IS NULL)";
    $params[] = $workingLabId;

    if (!empty($search)) {
        $sql .= " AND (a.code LIKE ? OR a.description LIKE ? OR t.description LIKE ?)";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }
    if (!$showDisabled) {
        $sql .= " AND a.status = 1";
    }
    if ($filterSection > 0) {
        $sql .= " AND a.org_id = ?";
        $params[] = $filterSection;
    }
    $sql .= " ORDER BY t.description, a.code";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Counts (filtered by working lab)
    $countSql = "SELECT COUNT(*) FROM assays WHERE status = 1 AND (org_id IN (SELECT org_id FROM organizations WHERE parent_id = ? AND org_type = 'section') OR org_id IS NULL)";
    $stmt = $pdo->prepare($countSql);
    $stmt->execute([$workingLabId]);
    $activeCount = $stmt->fetchColumn();

    $countSql = "SELECT COUNT(*) FROM assays WHERE status = 0 AND (org_id IN (SELECT org_id FROM organizations WHERE parent_id = ? AND org_type = 'section') OR org_id IS NULL)";
    $stmt = $pdo->prepare($countSql);
    $stmt->execute([$workingLabId]);
    $disabledCount = $stmt->fetchColumn();

} catch (PDOException $e) {
    $rows = [];
    $tests = $methods = $units = $samples = $categories = $sections = [];
    $message = t('Data loading error') . ': ' . $e->getMessage();
    $messageType = 'error';
    $activeCount = 0;
    $disabledCount = 0;
}
?>

<style>
    .disabled-option { color: #999; font-style: italic; }
    .admin-container { max-width: 1600px; margin: 0 auto; padding: 20px; }
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
    .data-table th, .data-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #ecf0f1; font-size: 0.9rem; }
    .data-table th { background: #2c3e50; color: #fff; font-weight: 500; }
    .data-table tr:hover { background: #f8f9fa; }
    .data-table tr.disabled { color: #999; background: #f5f5f5; }
    .actions-cell { white-space: nowrap; }
    .badge { padding: 3px 8px; border-radius: 3px; font-size: 0.75rem; }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-secondary { background: #e2e3e5; color: #6c757d; }
    .message { padding: 12px 15px; border-radius: 4px; margin-bottom: 20px; }
    .message-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .message-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; overflow-y: auto; padding: 20px; }
    .modal-overlay.active { display: flex; }
    .modal { background: #fff; border-radius: 8px; padding: 20px; width: 700px; max-width: 95vw; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 20px rgba(0,0,0,0.3); margin: auto; }
    .modal h2 { margin: 0 0 20px 0; color: #2c3e50; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #2c3e50; }
    .form-group input[type="text"], .form-group input[type="number"], .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
    .form-group input[type="checkbox"] { margin-right: 8px; }
    .form-group small { color: #7f8c8d; font-size: 0.85rem; }
    .form-row { display: flex; gap: 15px; }
    .form-row .form-group { flex: 1; }
    .form-section { margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; }
    .form-section h3 { margin: 0 0 15px 0; font-size: 1rem; color: #7f8c8d; }
    .form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
    .empty-state { text-align: center; padding: 40px; color: #7f8c8d; }
    .code-cell { font-family: monospace; font-weight: bold; color: #2c3e50; }
</style>

<div class="admin-container">
    <div class="breadcrumb">
        <a href="/biovarase/admin"><?= t('Admin') ?></a> / <?= t('Assays') ?>
    </div>

    <div class="admin-header">
        <h1><?= t('Assays') ?></h1>
        <button class="btn btn-success" onclick="openCreateModal()">+ <?= t('New') ?> <?= t('Assay') ?></button>
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
            <input type="text" name="search" placeholder="<?= t('Search code or test...') ?>" value="<?= htmlspecialchars($search) ?>">
            <select name="org_id" onchange="this.form.submit()">
                <option value=""><?= t('All sections') ?></option>
                <?php foreach ($sections as $sec): ?>
                <option value="<?= $sec['org_id'] ?>" <?= $filterSection == $sec['org_id'] ? 'selected' : '' ?>><?= htmlspecialchars($sec['description']) ?></option>
                <?php endforeach; ?>
            </select>
            <label>
                <input type="checkbox" name="show_disabled" <?= $showDisabled ? 'checked' : '' ?> onchange="this.form.submit()">
                <?= t('Show disabled') ?>
            </label>
            <button type="submit" class="btn btn-primary"><?= t('Search') ?></button>
            <?php if ($search || $showDisabled || $filterSection): ?>
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
                <th><?= t('Code') ?></th>
                <th><?= t('Test') ?></th>
                <th><?= t('Method') ?></th>
                <th><?= t('Unit') ?></th>
                <th><?= t('Sample') ?></th>
                <th><?= t('Category') ?></th>
                <th><?= t('Section') ?></th>
                <th><?= t('Status') ?></th>
                <th><?= t('Actions') ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($rows as $row): ?>
            <tr class="<?= $row['status'] ? '' : 'disabled' ?>">
                <td class="code-cell"><?= htmlspecialchars($row['code']) ?></td>
                <td><?= htmlspecialchars($row['test_name']) ?></td>
                <td><?= htmlspecialchars($row['method_name']) ?></td>
                <td><?= htmlspecialchars($row['unit_name']) ?></td>
                <td><?= htmlspecialchars($row['sample_name']) ?></td>
                <td><?= htmlspecialchars($row['category_name'] ?? '-') ?></td>
                <td><?= htmlspecialchars($row['section_name'] ?? '-') ?></td>
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
        <h2 id="modalTitle"><?= t('New') ?> <?= t('Assay') ?></h2>
        <form method="post" id="editForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="assay_id" id="formPk" value="">

            <div class="form-row">
                <div class="form-group">
                    <label for="test_id"><?= t('Test') ?> *</label>
                    <select id="test_id" name="test_id" required>
                        <option value=""><?= t('Select test...') ?></option>
                        <?php foreach ($tests as $t): ?>
                        <option value="<?= $t['test_id'] ?>"<?= $t['status'] ? '' : ' class="disabled-option"' ?>><?= htmlspecialchars($t['description']) ?><?= $t['status'] ? '' : ' [' . t('Disabled') . ']' ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="form-group">
                    <label for="code"><?= t('Code') ?> *</label>
                    <input type="text" id="code" name="code" required maxlength="10">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="method_id"><?= t('Method') ?> *</label>
                    <select id="method_id" name="method_id" required>
                        <option value=""><?= t('Select method...') ?></option>
                        <?php foreach ($methods as $m): ?>
                        <option value="<?= $m['method_id'] ?>"><?= htmlspecialchars($m['description']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="form-group">
                    <label for="unit_id"><?= t('Unit') ?> *</label>
                    <select id="unit_id" name="unit_id" required>
                        <option value=""><?= t('Select unit...') ?></option>
                        <?php foreach ($units as $u): ?>
                        <option value="<?= $u['unit_id'] ?>"><?= htmlspecialchars($u['description']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="sample_id"><?= t('Sample') ?> *</label>
                    <select id="sample_id" name="sample_id" required>
                        <option value=""><?= t('Select sample...') ?></option>
                        <?php foreach ($samples as $s): ?>
                        <option value="<?= $s['sample_id'] ?>"><?= htmlspecialchars($s['description']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="form-group">
                    <label for="category_id"><?= t('Category') ?></label>
                    <select id="category_id" name="category_id">
                        <option value=""><?= t('No category') ?></option>
                        <?php foreach ($categories as $c): ?>
                        <option value="<?= $c['category_id'] ?>"><?= htmlspecialchars($c['description']) ?><?= isset($c['org_name']) ? ' (' . $c['org_name'] . ')' : '' ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="org_id"><?= t('Section') ?></label>
                    <select id="org_id" name="org_id">
                        <option value=""><?= t('No section (global)') ?></option>
                        <?php foreach ($sections as $sec): ?>
                        <option value="<?= $sec['org_id'] ?>"><?= htmlspecialchars($sec['description']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="form-group">
                    <label for="description"><?= t('Local Name') ?></label>
                    <input type="text" id="description" name="description" maxlength="100" placeholder="<?= t('Optional local lab name') ?>">
                </div>
            </div>

            <div class="form-section">
                <h3><?= t('Analytical Goals') ?></h3>
                <div class="form-row">
                    <div class="form-group">
                        <label for="cvw">CVw (%)</label>
                        <input type="number" id="cvw" name="cvw" step="0.01" min="0" value="0">
                    </div>
                    <div class="form-group">
                        <label for="cvb">CVb (%)</label>
                        <input type="number" id="cvb" name="cvb" step="0.01" min="0" value="0">
                    </div>
                    <div class="form-group">
                        <label for="imp"><?= t('Imprecision') ?> (%)</label>
                        <input type="number" id="imp" name="imp" step="0.01" min="0" value="0">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="bias"><?= t('Bias') ?> (%)</label>
                        <input type="number" id="bias" name="bias" step="0.01" min="0" value="0">
                    </div>
                    <div class="form-group">
                        <label for="teap005">TEa p=0.05 (%)</label>
                        <input type="number" id="teap005" name="teap005" step="0.01" min="0" value="0">
                    </div>
                    <div class="form-group">
                        <label for="teap001">TEa p=0.01 (%)</label>
                        <input type="number" id="teap001" name="teap001" step="0.01" min="0" value="0">
                    </div>
                </div>
            </div>

            <div class="form-section">
                <div class="form-row">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="is_mandatory" name="is_mandatory" checked>
                            <?= t('Mandatory') ?>
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="to_export" name="to_export">
                            <?= t('Export to reports') ?>
                        </label>
                    </div>
                    <div class="form-group" id="statusGroup" style="display: none;">
                        <label>
                            <input type="checkbox" id="status" name="status" checked>
                            <?= t('Active') ?>
                        </label>
                    </div>
                </div>
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
    document.getElementById('modalTitle').textContent = '<?= t('New') ?> <?= t('Assay') ?>';
    document.getElementById('formAction').value = 'create';
    document.getElementById('formPk').value = '';
    document.getElementById('test_id').value = '';
    document.getElementById('method_id').value = '';
    document.getElementById('unit_id').value = '';
    document.getElementById('sample_id').value = '';
    document.getElementById('category_id').value = '';
    document.getElementById('org_id').value = '';
    document.getElementById('code').value = '';
    document.getElementById('description').value = '';
    document.getElementById('cvw').value = '0';
    document.getElementById('cvb').value = '0';
    document.getElementById('imp').value = '0';
    document.getElementById('bias').value = '0';
    document.getElementById('teap005').value = '0';
    document.getElementById('teap001').value = '0';
    document.getElementById('is_mandatory').checked = true;
    document.getElementById('to_export').checked = false;
    document.getElementById('status').checked = true;
    document.getElementById('statusGroup').style.display = 'none';
    document.getElementById('submitBtn').textContent = '<?= t('Create') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('test_id').focus();
}

function openEditModal(row) {
    document.getElementById('modalTitle').textContent = '<?= t('Edit') ?> <?= t('Assay') ?>';
    document.getElementById('formAction').value = 'update';
    document.getElementById('formPk').value = row.assay_id;
    document.getElementById('test_id').value = row.test_id;
    document.getElementById('method_id').value = row.method_id;
    document.getElementById('unit_id').value = row.unit_id;
    document.getElementById('sample_id').value = row.sample_id;
    document.getElementById('category_id').value = row.category_id || '';
    document.getElementById('org_id').value = row.org_id || '';
    document.getElementById('code').value = row.code;
    document.getElementById('description').value = row.description || '';
    document.getElementById('cvw').value = row.cvw || '0';
    document.getElementById('cvb').value = row.cvb || '0';
    document.getElementById('imp').value = row.imp || '0';
    document.getElementById('bias').value = row.bias || '0';
    document.getElementById('teap005').value = row.teap005 || '0';
    document.getElementById('teap001').value = row.teap001 || '0';
    document.getElementById('is_mandatory').checked = row.is_mandatory == 1;
    document.getElementById('to_export').checked = row.to_export == 1;
    document.getElementById('status').checked = row.status == 1;
    document.getElementById('statusGroup').style.display = 'block';
    document.getElementById('submitBtn').textContent = '<?= t('Save') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('test_id').focus();
}

function closeModal() { document.getElementById('editModal').classList.remove('active'); }

document.getElementById('editModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });
</script>

<?php require_once __DIR__ . '/../../includes/footer.php'; ?>
