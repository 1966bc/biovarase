<?php
/**
 * Batches Management
 *
 * CRUD for QC batches (lots).
 * Superuser and above can create/edit.
 * No deletion - only enable/disable.
 */

$pageTitle = 'Batches - Biovarase';

require_once __DIR__ . '/../includes/header.php';
require_once __DIR__ . '/../api/config.php';

// Must be logged in
requireAuth();

// Get working lab
requireWorkingLab();
$workingLabId = getWorkingLabId();

// Permission flags
$canEdit = canValidateQC(); // Superuser+

$message = '';
$messageType = '';

// Handle POST actions (only if can edit)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $canEdit) {
    $action = $_POST['action'] ?? '';

    try {
        $pdo = getDbConnection();
        $userId = getCurrentUser()['user_id'] ?? null;

        switch ($action) {
            case 'create':
                $workstationId = (int)($_POST['workstation_id'] ?? 0);
                $assayId = (int)($_POST['assay_id'] ?? 0);
                $controlId = (int)($_POST['control_id'] ?? 0);
                $lotNumber = trim($_POST['lot_number'] ?? '');
                $description = trim($_POST['description'] ?? '');
                $target = floatval($_POST['target'] ?? 0);
                $sd = floatval($_POST['sd'] ?? 0);
                $lower = $_POST['lower'] !== '' ? floatval($_POST['lower']) : null;
                $upper = $_POST['upper'] !== '' ? floatval($_POST['upper']) : null;
                $rank = (int)($_POST['rank'] ?? 1);
                $expiration = $_POST['expiration'] ?? null;

                if ($workstationId <= 0 || $assayId <= 0 || $controlId <= 0) {
                    throw new Exception(t('Workstation, Assay and Control are required'));
                }
                if (empty($lotNumber)) {
                    throw new Exception(t('Lot number is required'));
                }
                if ($target <= 0 || $sd <= 0) {
                    throw new Exception(t('Target and SD must be greater than zero'));
                }

                $stmt = $pdo->prepare("
                    INSERT INTO batches (workstation_id, assay_id, test_method_id, control_id, lot_number, description, target, sd, `lower`, `upper`, `rank`, expiration, org_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ");
                $stmt->execute([
                    $workstationId, $assayId, $assayId, $controlId,
                    $lotNumber, $description, $target, $sd,
                    $lower, $upper, $rank,
                    $expiration ?: null, $workingLabId
                ]);

                $message = t('Batch created successfully');
                $messageType = 'success';
                break;

            case 'update':
                $batchId = (int)($_POST['batch_id'] ?? 0);
                $workstationId = (int)($_POST['workstation_id'] ?? 0);
                $assayId = (int)($_POST['assay_id'] ?? 0);
                $controlId = (int)($_POST['control_id'] ?? 0);
                $lotNumber = trim($_POST['lot_number'] ?? '');
                $description = trim($_POST['description'] ?? '');
                $target = floatval($_POST['target'] ?? 0);
                $sd = floatval($_POST['sd'] ?? 0);
                $lower = $_POST['lower'] !== '' ? floatval($_POST['lower']) : null;
                $upper = $_POST['upper'] !== '' ? floatval($_POST['upper']) : null;
                $rank = (int)($_POST['rank'] ?? 1);
                $expiration = $_POST['expiration'] ?? null;
                $status = isset($_POST['status']) ? 1 : 0;

                if ($batchId <= 0 || $workstationId <= 0 || $assayId <= 0 || $controlId <= 0) {
                    throw new Exception(t('All required fields must be filled'));
                }
                if (empty($lotNumber)) {
                    throw new Exception(t('Lot number is required'));
                }
                if ($target <= 0 || $sd <= 0) {
                    throw new Exception(t('Target and SD must be greater than zero'));
                }

                $stmt = $pdo->prepare("
                    UPDATE batches
                    SET workstation_id = ?, assay_id = ?, test_method_id = ?, control_id = ?,
                        lot_number = ?, description = ?, target = ?, sd = ?, `lower` = ?, `upper` = ?, `rank` = ?, expiration = ?, status = ?
                    WHERE batch_id = ? AND org_id = ?
                ");
                $stmt->execute([
                    $workstationId, $assayId, $assayId, $controlId,
                    $lotNumber, $description, $target, $sd,
                    $lower, $upper, $rank,
                    $expiration ?: null, $status,
                    $batchId, $workingLabId
                ]);

                $message = t('Batch updated successfully');
                $messageType = 'success';
                break;
        }

    } catch (Exception $e) {
        $message = $e->getMessage();
        $messageType = 'error';
    }
}

// Get filter values
$filterWorkstation = isset($_GET['workstation_id']) ? (int)$_GET['workstation_id'] : 0;
$filterAssay = isset($_GET['assay_id']) ? (int)$_GET['assay_id'] : 0;
$filterStatus = isset($_GET['status']) ? $_GET['status'] : '';
$searchTerm = trim($_GET['search'] ?? '');

// Fetch data
try {
    $pdo = getDbConnection();

    // Get sections for this lab
    $stmtSections = $pdo->prepare("
        SELECT org_id FROM organizations
        WHERE parent_id = ? AND org_type = 'section' AND status = 1
    ");
    $stmtSections->execute([$workingLabId]);
    $sectionIds = $stmtSections->fetchAll(PDO::FETCH_COLUMN);

    // Get workstations for filters
    if (!empty($sectionIds)) {
        $placeholders = implode(',', array_fill(0, count($sectionIds), '?'));
        $stmtWs = $pdo->prepare("
            SELECT w.workstation_id, w.description
            FROM workstations w
            WHERE w.org_id IN ($placeholders) AND w.status = 1
            ORDER BY w.description
        ");
        $stmtWs->execute($sectionIds);
        $workstations = $stmtWs->fetchAll(PDO::FETCH_ASSOC);
    } else {
        $workstations = [];
    }

    // Get controls (global)
    $stmtControls = $pdo->query("
        SELECT control_id, description FROM controls WHERE status = 1 ORDER BY description
    ");
    $controls = $stmtControls->fetchAll(PDO::FETCH_ASSOC);

    // Build batches query
    $sql = "
        SELECT b.batch_id, b.workstation_id, b.assay_id, b.control_id,
               b.lot_number, b.description, b.target, b.sd, b.lower, b.upper, b.rank, b.expiration, b.status,
               w.description as workstation_name,
               t.description as test_name,
               c.description as control_name,
               (SELECT COUNT(*) FROM results r WHERE r.batch_id = b.batch_id AND r.is_delete = 0) as result_count
        FROM batches b
        JOIN workstations w ON b.workstation_id = w.workstation_id
        JOIN assays a ON b.assay_id = a.assay_id
        JOIN tests t ON a.test_id = t.test_id
        JOIN controls c ON b.control_id = c.control_id
        WHERE b.org_id = ?
    ";
    $params = [$workingLabId];

    if ($filterWorkstation > 0) {
        $sql .= " AND b.workstation_id = ?";
        $params[] = $filterWorkstation;
    }
    if ($filterAssay > 0) {
        $sql .= " AND b.assay_id = ?";
        $params[] = $filterAssay;
    }
    if ($filterStatus !== '') {
        $sql .= " AND b.status = ?";
        $params[] = (int)$filterStatus;
    }
    if ($searchTerm) {
        $sql .= " AND (b.lot_number LIKE ? OR b.description LIKE ? OR t.description LIKE ?)";
        $searchPattern = "%$searchTerm%";
        $params[] = $searchPattern;
        $params[] = $searchPattern;
        $params[] = $searchPattern;
    }

    $sql .= " ORDER BY w.description, t.description, b.lot_number";

    $stmtBatches = $pdo->prepare($sql);
    $stmtBatches->execute($params);
    $batches = $stmtBatches->fetchAll(PDO::FETCH_ASSOC);

} catch (PDOException $e) {
    $workstations = [];
    $controls = [];
    $batches = [];
    $message = t('Error loading data');
    $messageType = 'error';
}
?>

<div class="admin-container">
    <header class="admin-header">
        <h1><?= t('Batches') ?></h1>
        <?php if ($canEdit): ?>
        <button class="btn btn-primary" onclick="openModal('create')"><?= t('New Batch') ?></button>
        <?php endif; ?>
    </header>

    <?php if ($message): ?>
    <div class="message <?= $messageType ?>"><?= htmlspecialchars($message) ?></div>
    <?php endif; ?>

    <!-- Filters -->
    <div class="toolbar">
        <form class="search-box" method="GET">
            <input type="text" name="search" placeholder="<?= t('Search lot, test...') ?>" value="<?= htmlspecialchars($searchTerm) ?>">
            <select name="workstation_id" onchange="this.form.submit()">
                <option value=""><?= t('All Workstations') ?></option>
                <?php foreach ($workstations as $ws): ?>
                <option value="<?= $ws['workstation_id'] ?>" <?= $filterWorkstation == $ws['workstation_id'] ? 'selected' : '' ?>>
                    <?= htmlspecialchars($ws['description']) ?>
                </option>
                <?php endforeach; ?>
            </select>
            <select name="status" onchange="this.form.submit()">
                <option value=""><?= t('All Status') ?></option>
                <option value="1" <?= $filterStatus === '1' ? 'selected' : '' ?>><?= t('Enabled') ?></option>
                <option value="0" <?= $filterStatus === '0' ? 'selected' : '' ?>><?= t('Disabled') ?></option>
            </select>
            <button type="submit" class="btn"><?= t('Search') ?></button>
            <?php if ($searchTerm || $filterWorkstation || $filterStatus !== ''): ?>
            <a href="?" class="btn"><?= t('Clear') ?></a>
            <?php endif; ?>
        </form>
        <div class="stats">
            <span class="badge badge-info"><?= count($batches) ?> <?= t('batches') ?></span>
        </div>
    </div>

    <?php if (empty($batches)): ?>
    <div class="empty-state">
        <p><?= t('No batches found.') ?></p>
    </div>
    <?php else: ?>
    <table class="data-table">
        <thead>
            <tr>
                <th><?= t('Workstation') ?></th>
                <th><?= t('Test') ?></th>
                <th><?= t('Control') ?></th>
                <th><?= t('Lot') ?></th>
                <th><?= t('Target') ?></th>
                <th><?= t('SD') ?></th>
                <th><?= t('Expiration') ?></th>
                <th><?= t('Results') ?></th>
                <th><?= t('Status') ?></th>
                <?php if ($canEdit): ?>
                <th><?= t('Actions') ?></th>
                <?php endif; ?>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($batches as $batch):
                $isExpired = $batch['expiration'] && strtotime($batch['expiration']) < strtotime('today');
            ?>
            <tr class="<?= $batch['status'] ? '' : 'disabled' ?><?= $isExpired ? ' expired' : '' ?>">
                <td><?= htmlspecialchars($batch['workstation_name']) ?></td>
                <td><strong><?= htmlspecialchars($batch['test_name']) ?></strong></td>
                <td><?= htmlspecialchars($batch['control_name']) ?></td>
                <td><code><?= htmlspecialchars($batch['lot_number']) ?></code></td>
                <td class="number"><?= number_format($batch['target'], 2) ?></td>
                <td class="number"><?= number_format($batch['sd'], 3) ?></td>
                <td>
                    <?php if ($batch['expiration']): ?>
                        <span class="<?= $isExpired ? 'text-danger' : '' ?>">
                            <?= date('d/m/Y', strtotime($batch['expiration'])) ?>
                        </span>
                        <?php if ($isExpired): ?>
                        <span class="badge badge-danger"><?= t('Expired') ?></span>
                        <?php endif; ?>
                    <?php else: ?>
                        <span class="text-muted">-</span>
                    <?php endif; ?>
                </td>
                <td class="number"><?= $batch['result_count'] ?></td>
                <td>
                    <span class="badge <?= $batch['status'] ? 'badge-success' : 'badge-secondary' ?>">
                        <?= $batch['status'] ? t('Enabled') : t('Disabled') ?>
                    </span>
                </td>
                <?php if ($canEdit): ?>
                <td>
                    <button class="btn btn-small" onclick="openModal('edit', <?= htmlspecialchars(json_encode($batch)) ?>)">
                        <?= t('Edit') ?>
                    </button>
                </td>
                <?php endif; ?>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</div>

<?php if ($canEdit): ?>
<!-- Create/Edit Modal -->
<div class="modal-overlay" id="batchModal">
    <div class="modal">
        <div class="modal-header">
            <h2 id="modalTitle"><?= t('New Batch') ?></h2>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <form method="POST" id="batchForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="batch_id" id="batchId" value="">

            <div class="form-group">
                <label for="workstation_id"><?= t('Workstation') ?> *</label>
                <select name="workstation_id" id="workstation_id" required onchange="loadAssays(this.value)">
                    <option value=""><?= t('Select...') ?></option>
                    <?php foreach ($workstations as $ws): ?>
                    <option value="<?= $ws['workstation_id'] ?>"><?= htmlspecialchars($ws['description']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="form-group">
                <label for="assay_id"><?= t('Assay') ?> *</label>
                <select name="assay_id" id="assay_id" required>
                    <option value=""><?= t('Select workstation first...') ?></option>
                </select>
            </div>

            <div class="form-group">
                <label for="control_id"><?= t('Control') ?> *</label>
                <select name="control_id" id="control_id" required>
                    <option value=""><?= t('Select...') ?></option>
                    <?php foreach ($controls as $ctrl): ?>
                    <option value="<?= $ctrl['control_id'] ?>"><?= htmlspecialchars($ctrl['description']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="lot_number"><?= t('Lot Number') ?> *</label>
                    <input type="text" name="lot_number" id="lot_number" required maxlength="20">
                </div>
                <div class="form-group">
                    <label for="description"><?= t('Description') ?></label>
                    <input type="text" name="description" id="description" maxlength="15">
                </div>
            </div>

            <div class="form-group">
                <label for="target"><?= t('Target') ?> *</label>
                <input type="number" name="target" id="target" required step="0.01" min="0">
            </div>

            <fieldset class="sd-mode-fieldset">
                <legend><?= t('SD Mode') ?></legend>
                <div class="radio-group">
                    <label class="radio-label">
                        <input type="radio" name="sd_mode" value="manual" checked onchange="setSDMode('manual')">
                        <?= t('Manual') ?>
                    </label>
                    <label class="radio-label">
                        <input type="radio" name="sd_mode" value="computed" onchange="setSDMode('computed')">
                        <?= t('Computed') ?>
                    </label>
                </div>
            </fieldset>

            <div class="form-row">
                <div class="form-group">
                    <label for="lower"><?= t('Lower Limit') ?></label>
                    <input type="number" name="lower" id="lower" step="0.01" oninput="computeSD()" disabled>
                </div>
                <div class="form-group">
                    <label for="upper"><?= t('Upper Limit') ?></label>
                    <input type="number" name="upper" id="upper" step="0.01" oninput="computeSD()" disabled>
                </div>
                <div class="form-group">
                    <label for="sd"><?= t('SD') ?> *</label>
                    <input type="number" name="sd" id="sd" required step="0.001" min="0">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="expiration"><?= t('Expiration Date') ?></label>
                    <input type="date" name="expiration" id="expiration">
                </div>
                <div class="form-group">
                    <label for="rank"><?= t('Rank') ?></label>
                    <input type="number" name="rank" id="rank" min="1" value="1">
                </div>
            </div>

            <div class="form-group" id="statusGroup" style="display: none;">
                <label>
                    <input type="checkbox" name="status" id="status" value="1" checked>
                    <?= t('Enabled') ?>
                </label>
            </div>

            <div class="form-actions">
                <button type="button" class="btn" onclick="closeModal()"><?= t('Cancel') ?></button>
                <button type="submit" class="btn btn-primary"><?= t('Save') ?></button>
            </div>
        </form>
    </div>
</div>
<?php endif; ?>

<style>
/* Modal styling */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}
.modal-overlay.active {
    display: flex;
}
.modal {
    background: var(--bg-card, #fff);
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    width: 90%;
    max-width: 550px;
    max-height: 90vh;
    overflow-y: auto;
}
.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid var(--border-color, #ddd);
    background: var(--bg-nav, #2c3e50);
    border-radius: 8px 8px 0 0;
}
.modal-header h2 {
    margin: 0;
    font-size: 1.1rem;
    color: #fff;
}
.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #fff;
    opacity: 0.8;
    line-height: 1;
}
.modal-close:hover {
    opacity: 1;
}
.modal form {
    padding: 20px;
}
.form-group {
    margin-bottom: 15px;
}
.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    color: var(--text-primary, #2c3e50);
}
.form-group input[type="text"],
.form-group input[type="number"],
.form-group input[type="date"],
.form-group select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    font-size: 0.95rem;
    background: var(--bg-card, #fff);
    color: var(--text-primary, #2c3e50);
    box-sizing: border-box;
}
.form-group input:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--info, #3498db);
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}
.form-group input[type="checkbox"] {
    width: auto;
    margin-right: 8px;
}
.form-row {
    display: flex;
    gap: 15px;
}
.form-row .form-group {
    flex: 1;
}
.sd-mode-fieldset {
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    padding: 10px 15px;
    margin-bottom: 15px;
}
.sd-mode-fieldset legend {
    font-weight: 500;
    padding: 0 8px;
    color: var(--text-primary, #2c3e50);
    font-size: 0.9rem;
}
.radio-group {
    display: flex;
    gap: 20px;
}
.radio-label {
    display: flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    font-weight: normal;
}
.radio-label input[type="radio"] {
    width: auto;
    margin: 0;
}
.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding-top: 15px;
    border-top: 1px solid var(--border-light, #ecf0f1);
    margin-top: 10px;
}

/* Page styles */
.admin-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}
.admin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.admin-header h1 {
    margin: 0;
    color: var(--text-primary, #2c3e50);
}
.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    gap: 15px;
    flex-wrap: wrap;
}
.search-box {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
}
.search-box input[type="text"] {
    padding: 8px 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    width: 180px;
    background: var(--bg-card, #fff);
    color: var(--text-primary);
}
.search-box select {
    padding: 8px 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    background: var(--bg-card, #fff);
    color: var(--text-primary);
}
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    background: var(--bg-secondary, #ecf0f1);
    color: var(--text-primary, #2c3e50);
    text-decoration: none;
}
.btn:hover {
    background: var(--border-color, #ddd);
}
.btn-primary {
    background: #3498db;
    color: #fff;
}
.btn-primary:hover {
    background: #2980b9;
}
.btn-small {
    padding: 5px 10px;
    font-size: 0.8rem;
}
.data-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-card, #fff);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px var(--shadow, rgba(0,0,0,0.1));
}
.data-table th,
.data-table td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid var(--border-light, #ecf0f1);
}
.data-table th {
    background: var(--bg-nav, #2c3e50);
    color: var(--text-nav, #fff);
    font-weight: 500;
}
.data-table tr:hover {
    background: var(--bg-secondary, #f8f9fa);
}
.data-table td.number {
    text-align: right;
    font-family: monospace;
}
tr.disabled {
    opacity: 0.5;
    background: var(--bg-secondary, #f5f5f5) !important;
}
tr.disabled td {
    color: var(--text-secondary, #999) !important;
}
tr.expired {
    background: rgba(231, 76, 60, 0.05) !important;
}
.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
}
.badge-success {
    background: rgba(39, 174, 96, 0.2);
    color: #27ae60;
}
.badge-secondary {
    background: rgba(149, 165, 166, 0.2);
    color: #7f8c8d;
}
.badge-danger {
    background: rgba(231, 76, 60, 0.2);
    color: #e74c3c;
}
.badge-info {
    background: rgba(52, 152, 219, 0.2);
    color: #2980b9;
}
.text-muted {
    color: var(--text-secondary, #7f8c8d);
}
.text-danger {
    color: #e74c3c;
}
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-secondary, #7f8c8d);
}
.message {
    padding: 12px 16px;
    border-radius: 4px;
    margin-bottom: 20px;
}
.message.success {
    background: rgba(39, 174, 96, 0.1);
    color: #27ae60;
    border: 1px solid rgba(39, 174, 96, 0.3);
}
.message.error {
    background: rgba(231, 76, 60, 0.1);
    color: #e74c3c;
    border: 1px solid rgba(231, 76, 60, 0.3);
}
</style>

<script>
// Assays per workstation (loaded dynamically)
const assaysByWorkstation = {};

function loadAssays(workstationId) {
    const select = document.getElementById('assay_id');
    select.innerHTML = '<option value=""><?= t('Loading...') ?></option>';

    if (!workstationId) {
        select.innerHTML = '<option value=""><?= t('Select workstation first...') ?></option>';
        return;
    }

    // Fetch assays for this workstation
    fetch('/biovarase/api/workstation_assays.php?workstation_id=' + workstationId)
        .then(r => r.json())
        .then(data => {
            select.innerHTML = '<option value=""><?= t('Select...') ?></option>';
            if (data.assays && data.assays.length > 0) {
                data.assays.forEach(a => {
                    const opt = document.createElement('option');
                    opt.value = a.assay_id;
                    opt.textContent = a.test_name + ' - ' + a.method_name;
                    select.appendChild(opt);
                });
                assaysByWorkstation[workstationId] = data.assays;
            } else {
                select.innerHTML = '<option value=""><?= t('No assays assigned to this workstation') ?></option>';
            }
        })
        .catch(err => {
            select.innerHTML = '<option value=""><?= t('Error loading assays') ?></option>';
        });
}

function openModal(mode, data = null) {
    const modal = document.getElementById('batchModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('batchForm');
    const statusGroup = document.getElementById('statusGroup');

    form.reset();
    document.getElementById('assay_id').innerHTML = '<option value=""><?= t('Select workstation first...') ?></option>';

    if (mode === 'edit' && data) {
        title.textContent = '<?= t('Edit Batch') ?>';
        document.getElementById('formAction').value = 'update';
        document.getElementById('batchId').value = data.batch_id;
        document.getElementById('workstation_id').value = data.workstation_id;
        document.getElementById('control_id').value = data.control_id;
        document.getElementById('lot_number').value = data.lot_number;
        document.getElementById('description').value = data.description || '';
        document.getElementById('target').value = data.target;
        document.getElementById('sd').value = data.sd;
        document.getElementById('lower').value = data.lower || '';
        document.getElementById('upper').value = data.upper || '';
        document.getElementById('rank').value = data.rank || 1;
        document.getElementById('expiration').value = data.expiration || '';
        document.getElementById('status').checked = data.status == 1;
        statusGroup.style.display = 'block';

        // Determine SD mode based on whether lower/upper have values
        if (data.lower && data.upper) {
            document.querySelector('input[name="sd_mode"][value="computed"]').checked = true;
            setSDMode('computed');
        } else {
            document.querySelector('input[name="sd_mode"][value="manual"]').checked = true;
            setSDMode('manual');
        }

        // Load assays for this workstation, then select the right one
        loadAssays(data.workstation_id);
        setTimeout(() => {
            document.getElementById('assay_id').value = data.assay_id;
        }, 500);
    } else {
        title.textContent = '<?= t('New Batch') ?>';
        document.getElementById('formAction').value = 'create';
        document.getElementById('batchId').value = '';
        statusGroup.style.display = 'none';
        // Reset SD mode to manual
        document.querySelector('input[name="sd_mode"][value="manual"]').checked = true;
        setSDMode('manual');
    }

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('batchModal').classList.remove('active');
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
});

// SD Mode logic
function setSDMode(mode) {
    const lowerInput = document.getElementById('lower');
    const upperInput = document.getElementById('upper');
    const sdInput = document.getElementById('sd');

    if (mode === 'computed') {
        // Computed mode: enable lower/upper, make SD readonly
        lowerInput.disabled = false;
        upperInput.disabled = false;
        sdInput.readOnly = true;
        sdInput.style.backgroundColor = 'var(--bg-secondary, #f5f5f5)';
        computeSD();
    } else {
        // Manual mode: disable lower/upper, enable SD
        lowerInput.disabled = true;
        upperInput.disabled = true;
        sdInput.readOnly = false;
        sdInput.style.backgroundColor = '';
    }
}

// Compute SD from Lower/Upper: SD = (Upper - Lower) / 4 (assuming ±2SD limits)
function computeSD() {
    const mode = document.querySelector('input[name="sd_mode"]:checked')?.value;
    if (mode !== 'computed') return;

    const lower = parseFloat(document.getElementById('lower').value) || 0;
    const upper = parseFloat(document.getElementById('upper').value) || 0;

    if (upper > lower) {
        const sd = (upper - lower) / 4;
        document.getElementById('sd').value = sd.toFixed(3);
    }
}
</script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
