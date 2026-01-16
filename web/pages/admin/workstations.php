<?php
/**
 * Workstations Management
 *
 * CRUD for workstations with assigned assays management.
 * No deletion - only enable/disable.
 */

$pageTitle = 'Workstations - Biovarase';

require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

// Must be logged in and be Lab Admin or higher (roles 0-3)
requireAuth();
if (!isAdmin()) {
    header('Location: /biovarase/dashboard');
    exit;
}

// Get working lab
requireWorkingLab();
$workingLabId = getWorkingLabId();

$message = '';
$messageType = '';

// Get sections for this lab
try {
    $pdo = getDbConnection();

    // Get sections under this lab
    $stmtSections = $pdo->prepare("
        SELECT org_id, description
        FROM organizations
        WHERE parent_id = ? AND org_type = 'section' AND status = 1
        ORDER BY description
    ");
    $stmtSections->execute([$workingLabId]);
    $sections = $stmtSections->fetchAll(PDO::FETCH_ASSOC);

    // Get equipments (global)
    $stmtEquip = $pdo->query("
        SELECT equipment_id, description
        FROM equipments
        WHERE status = 1
        ORDER BY description
    ");
    $equipments = $stmtEquip->fetchAll(PDO::FETCH_ASSOC);

} catch (PDOException $e) {
    $sections = [];
    $equipments = [];
    $message = t('Error loading data');
    $messageType = 'error';
}

// Handle POST actions (Lab Admin or higher)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isAdmin()) {
    $action = $_POST['action'] ?? '';

    try {
        $pdo = getDbConnection();

        switch ($action) {
            case 'create':
                $description = trim($_POST['description'] ?? '');
                $equipmentId = (int)($_POST['equipment_id'] ?? 0);
                $sectionId = (int)($_POST['section_id'] ?? 0);
                $serial = trim($_POST['serial'] ?? 'NOT ASSIGNED');
                $deviceId = trim($_POST['device_id'] ?? '');

                if (empty($description) || $equipmentId <= 0 || $sectionId <= 0) {
                    throw new Exception(t('All required fields must be filled'));
                }

                // Generate device_id if empty
                if (empty($deviceId)) {
                    $deviceId = uniqid('WS-', true);
                }

                $stmt = $pdo->prepare("
                    INSERT INTO workstations (description, equipment_id, org_id, serial, device_id, status)
                    VALUES (?, ?, ?, ?, ?, 1)
                ");
                $stmt->execute([$description, $equipmentId, $sectionId, $serial, $deviceId]);

                $message = t('Workstation created successfully');
                $messageType = 'success';
                break;

            case 'update':
                $workstationId = (int)($_POST['workstation_id'] ?? 0);
                $description = trim($_POST['description'] ?? '');
                $equipmentId = (int)($_POST['equipment_id'] ?? 0);
                $sectionId = (int)($_POST['section_id'] ?? 0);
                $serial = trim($_POST['serial'] ?? 'NOT ASSIGNED');
                $status = isset($_POST['status']) ? 1 : 0;

                if ($workstationId <= 0 || empty($description) || $equipmentId <= 0 || $sectionId <= 0) {
                    throw new Exception(t('All required fields must be filled'));
                }

                $stmt = $pdo->prepare("
                    UPDATE workstations
                    SET description = ?, equipment_id = ?, org_id = ?, serial = ?, status = ?
                    WHERE workstation_id = ?
                ");
                $stmt->execute([$description, $equipmentId, $sectionId, $serial, $status, $workstationId]);

                $message = t('Workstation updated successfully');
                $messageType = 'success';
                break;

            case 'assign_assay':
                $workstationId = (int)($_POST['workstation_id'] ?? 0);
                $testMethodId = (int)($_POST['test_method_id'] ?? 0);
                $externalCode = trim($_POST['external_code'] ?? '');

                if ($workstationId <= 0 || $testMethodId <= 0) {
                    throw new Exception(t('Invalid selection'));
                }

                // Check if already assigned
                $stmtCheck = $pdo->prepare("
                    SELECT 1 FROM workstation_test_methods
                    WHERE workstation_id = ? AND test_method_id = ?
                ");
                $stmtCheck->execute([$workstationId, $testMethodId]);

                if ($stmtCheck->fetch()) {
                    throw new Exception(t('Assay already assigned to this workstation'));
                }

                $stmt = $pdo->prepare("
                    INSERT INTO workstation_test_methods (workstation_id, test_method_id, external_code)
                    VALUES (?, ?, ?)
                ");
                $stmt->execute([$workstationId, $testMethodId, $externalCode ?: null]);

                $message = t('Assay assigned successfully');
                $messageType = 'success';
                break;

            case 'remove_assay':
                $workstationId = (int)($_POST['workstation_id'] ?? 0);
                $testMethodId = (int)($_POST['test_method_id'] ?? 0);

                if ($workstationId <= 0 || $testMethodId <= 0) {
                    throw new Exception(t('Invalid selection'));
                }

                $stmt = $pdo->prepare("
                    DELETE FROM workstation_test_methods
                    WHERE workstation_id = ? AND test_method_id = ?
                ");
                $stmt->execute([$workstationId, $testMethodId]);

                $message = t('Assay removed successfully');
                $messageType = 'success';
                break;

            case 'update_external_code':
                $workstationId = (int)($_POST['workstation_id'] ?? 0);
                $testMethodId = (int)($_POST['test_method_id'] ?? 0);
                $externalCode = trim($_POST['external_code'] ?? '');

                $stmt = $pdo->prepare("
                    UPDATE workstation_test_methods
                    SET external_code = ?
                    WHERE workstation_id = ? AND test_method_id = ?
                ");
                $stmt->execute([$externalCode ?: null, $workstationId, $testMethodId]);

                $message = t('External code updated');
                $messageType = 'success';
                break;
        }

    } catch (Exception $e) {
        $message = $e->getMessage();
        $messageType = 'error';
    }
}

// Fetch workstations for all sections of this lab
try {
    $pdo = getDbConnection();

    // Get section IDs for this lab
    $sectionIds = array_column($sections, 'org_id');

    if (!empty($sectionIds)) {
        $placeholders = implode(',', array_fill(0, count($sectionIds), '?'));

        $stmt = $pdo->prepare("
            SELECT
                w.workstation_id,
                w.description,
                w.serial,
                w.device_id,
                w.status,
                w.org_id as section_id,
                e.description as equipment_name,
                e.equipment_id,
                s.description as section_name,
                (SELECT COUNT(*) FROM workstation_test_methods wtm WHERE wtm.workstation_id = w.workstation_id) as assay_count
            FROM workstations w
            JOIN equipments e ON w.equipment_id = e.equipment_id
            JOIN organizations s ON w.org_id = s.org_id
            WHERE w.org_id IN ($placeholders)
            ORDER BY s.description, w.description
        ");
        $stmt->execute($sectionIds);
        $workstations = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } else {
        $workstations = [];
    }

} catch (PDOException $e) {
    $workstations = [];
    if (empty($message)) {
        $message = t('Error loading workstations');
        $messageType = 'error';
    }
}

// Function to get assigned assays for a workstation
function getAssignedAssays($pdo, $workstationId) {
    $stmt = $pdo->prepare("
        SELECT
            tm.test_method_id,
            t.description as test_name,
            m.description as method_name,
            wtm.external_code
        FROM workstation_test_methods wtm
        JOIN test_methods tm ON wtm.test_method_id = tm.test_method_id
        JOIN tests t ON tm.test_id = t.test_id
        JOIN methods m ON tm.method_id = m.method_id
        WHERE wtm.workstation_id = ?
        ORDER BY t.description
    ");
    $stmt->execute([$workstationId]);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

// Get available assays for assignment (test_methods from sections of this lab)
function getAvailableAssays($pdo, $sectionIds, $workstationId) {
    if (empty($sectionIds)) return [];

    $placeholders = implode(',', array_fill(0, count($sectionIds), '?'));
    $params = $sectionIds;
    $params[] = $workstationId;

    $stmt = $pdo->prepare("
        SELECT
            tm.test_method_id,
            t.description as test_name,
            m.description as method_name,
            s.description as section_name
        FROM test_methods tm
        JOIN tests t ON tm.test_id = t.test_id
        JOIN methods m ON tm.method_id = m.method_id
        JOIN organizations s ON tm.org_id = s.org_id
        WHERE tm.org_id IN ($placeholders)
          AND tm.status = 1
          AND tm.test_method_id NOT IN (
              SELECT test_method_id FROM workstation_test_methods WHERE workstation_id = ?
          )
        ORDER BY t.description, m.description
    ");
    $stmt->execute($params);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}
?>

<div class="admin-container">
    <header class="admin-header">
        <h1><?= t('Workstations') ?></h1>
        <button class="btn btn-primary" onclick="openModal('create')"><?= t('New Workstation') ?></button>
    </header>

    <?php if ($message): ?>
    <div class="message <?= $messageType ?>"><?= htmlspecialchars($message) ?></div>
    <?php endif; ?>

    <?php if (empty($sections)): ?>
    <div class="empty-state">
        <p><?= t('No sections found for this lab. Create sections first.') ?></p>
    </div>
    <?php elseif (empty($workstations)): ?>
    <div class="empty-state">
        <p><?= t('No workstations found.') ?></p>
    </div>
    <?php else: ?>
    <table class="data-table">
        <thead>
            <tr>
                <th></th>
                <th><?= t('Name') ?></th>
                <th><?= t('Equipment') ?></th>
                <th><?= t('Section') ?></th>
                <th><?= t('Serial') ?></th>
                <th><?= t('Assays') ?></th>
                <th><?= t('Status') ?></th>
                <th><?= t('Actions') ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($workstations as $ws):
                $assays = getAssignedAssays($pdo, $ws['workstation_id']);
                $assayCount = count($assays);
            ?>
            <tr class="<?= $ws['status'] ? '' : 'disabled' ?>" data-workstation-id="<?= $ws['workstation_id'] ?>">
                <td class="expand-cell">
                    <?php if (!empty($assays)): ?>
                    <button class="btn-expand" onclick="toggleExpand(<?= $ws['workstation_id'] ?>)" title="<?= t('Show assigned assays') ?>">▶</button>
                    <?php endif; ?>
                </td>
                <td><strong><?= htmlspecialchars($ws['description']) ?></strong></td>
                <td><?= htmlspecialchars($ws['equipment_name']) ?></td>
                <td><?= htmlspecialchars($ws['section_name']) ?></td>
                <td><?= htmlspecialchars($ws['serial']) ?></td>
                <td>
                    <?php if ($assayCount === 0): ?>
                        <span class="text-muted">-</span>
                    <?php else: ?>
                        <span class="badge badge-info"><?= $assayCount ?> <?= $assayCount === 1 ? t('assay') : t('assays') ?></span>
                    <?php endif; ?>
                </td>
                <td>
                    <span class="badge <?= $ws['status'] ? 'badge-success' : 'badge-secondary' ?>">
                        <?= $ws['status'] ? t('Enabled') : t('Disabled') ?>
                    </span>
                </td>
                <td>
                    <button class="btn btn-small" onclick="openModal('edit', <?= htmlspecialchars(json_encode($ws)) ?>)"><?= t('Edit') ?></button>
                </td>
            </tr>
            <!-- Expanded row for assay list -->
            <tr class="expanded-row" id="expanded-<?= $ws['workstation_id'] ?>" style="display: none;">
                <td colspan="8">
                    <div class="expanded-content">
                        <div class="expanded-header">
                            <strong><?= t('Assigned Assays') ?></strong>
                            <button class="btn btn-small btn-primary" onclick="openAssignModal(<?= $ws['workstation_id'] ?>, '<?= htmlspecialchars($ws['description'], ENT_QUOTES) ?>')"><?= t('Assign Assay') ?></button>
                        </div>
                        <?php if (empty($assays)): ?>
                        <p class="text-muted"><?= t('No assays assigned') ?></p>
                        <?php else: ?>
                        <table class="inner-table">
                            <thead>
                                <tr>
                                    <th><?= t('Test') ?></th>
                                    <th><?= t('Method') ?></th>
                                    <th><?= t('External Code') ?></th>
                                    <th><?= t('Actions') ?></th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($assays as $assay): ?>
                                <tr>
                                    <td><?= htmlspecialchars($assay['test_name']) ?></td>
                                    <td><?= htmlspecialchars($assay['method_name']) ?></td>
                                    <td>
                                        <?php if ($assay['external_code']): ?>
                                            <code><?= htmlspecialchars($assay['external_code']) ?></code>
                                        <?php else: ?>
                                            <span class="text-muted">-</span>
                                        <?php endif; ?>
                                    </td>
                                    <td class="actions-cell">
                                        <button class="btn btn-small"
                                                onclick="openExternalCodeModal(<?= $ws['workstation_id'] ?>, <?= $assay['test_method_id'] ?>, '<?= htmlspecialchars($assay['test_name'], ENT_QUOTES) ?>', '<?= htmlspecialchars($assay['external_code'] ?? '', ENT_QUOTES) ?>')"
                                                title="<?= t('Edit external code') ?>">
                                            <?= t('Edit') ?>
                                        </button>
                                        <button class="btn btn-small btn-danger"
                                                onclick="removeAssay(<?= $ws['workstation_id'] ?>, <?= $assay['test_method_id'] ?>, '<?= htmlspecialchars($assay['test_name'], ENT_QUOTES) ?>')"
                                                title="<?= t('Remove assignment') ?>">
                                            <?= t('Remove') ?>
                                        </button>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                        <?php endif; ?>
                    </div>
                </td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</div>

<!-- Create/Edit Modal -->
<div class="modal-overlay" id="workstationModal">
    <div class="modal">
        <div class="modal-header">
            <h2 id="modalTitle"><?= t('New Workstation') ?></h2>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <form method="POST" id="workstationForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="workstation_id" id="workstationId" value="">

            <div class="form-group">
                <label for="description"><?= t('Name') ?> *</label>
                <input type="text" name="description" id="description" required maxlength="36">
            </div>

            <div class="form-group">
                <label for="equipment_id"><?= t('Equipment') ?> *</label>
                <select name="equipment_id" id="equipment_id" required>
                    <option value=""><?= t('Select...') ?></option>
                    <?php foreach ($equipments as $eq): ?>
                    <option value="<?= $eq['equipment_id'] ?>"><?= htmlspecialchars($eq['description']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="form-group">
                <label for="section_id"><?= t('Section') ?> *</label>
                <select name="section_id" id="section_id" required>
                    <option value=""><?= t('Select...') ?></option>
                    <?php foreach ($sections as $sec): ?>
                    <option value="<?= $sec['org_id'] ?>"><?= htmlspecialchars($sec['description']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>

            <div class="form-group">
                <label for="serial"><?= t('Serial Number') ?></label>
                <input type="text" name="serial" id="serial" maxlength="255" placeholder="NOT ASSIGNED">
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

<!-- Assign Assay Modal -->
<div class="modal-overlay" id="assignModal">
    <div class="modal">
        <div class="modal-header">
            <h2 id="assignModalTitle"><?= t('Assign Assay') ?></h2>
            <button class="modal-close" onclick="closeAssignModal()">&times;</button>
        </div>
        <form method="POST" id="assignForm">
            <input type="hidden" name="action" value="assign_assay">
            <input type="hidden" name="workstation_id" id="assignWorkstationId" value="">

            <div class="form-group">
                <label for="test_method_id"><?= t('Assay') ?> *</label>
                <select name="test_method_id" id="test_method_id" required>
                    <option value=""><?= t('Select...') ?></option>
                </select>
            </div>

            <div class="form-group">
                <label for="external_code"><?= t('External Code') ?></label>
                <input type="text" name="external_code" id="assign_external_code" maxlength="50" placeholder="<?= t('Optional') ?>">
            </div>

            <div class="form-actions">
                <button type="button" class="btn" onclick="closeAssignModal()"><?= t('Cancel') ?></button>
                <button type="submit" class="btn btn-primary"><?= t('Assign') ?></button>
            </div>
        </form>
    </div>
</div>

<!-- Edit External Code Modal -->
<div class="modal-overlay" id="externalCodeModal">
    <div class="modal modal-small">
        <div class="modal-header">
            <h2 id="externalCodeModalTitle"><?= t('Edit External Code') ?></h2>
            <button class="modal-close" onclick="closeExternalCodeModal()">&times;</button>
        </div>
        <form method="POST" id="externalCodeForm">
            <input type="hidden" name="action" value="update_external_code">
            <input type="hidden" name="workstation_id" id="extcode_workstation_id" value="">
            <input type="hidden" name="test_method_id" id="extcode_test_method_id" value="">

            <div class="form-group">
                <label for="extcode_value"><?= t('External Code') ?></label>
                <input type="text" name="external_code" id="extcode_value" maxlength="50" placeholder="<?= t('Enter external code') ?>">
                <small class="form-help"><?= t('Code used by external systems (e.g., Abbott)') ?></small>
            </div>

            <div class="form-actions">
                <button type="button" class="btn" onclick="closeExternalCodeModal()"><?= t('Cancel') ?></button>
                <button type="submit" class="btn btn-primary"><?= t('Save') ?></button>
            </div>
        </form>
    </div>
</div>

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
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
}
.modal.modal-small {
    max-width: 400px;
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
.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding-top: 15px;
    border-top: 1px solid var(--border-light, #ecf0f1);
    margin-top: 10px;
}

/* Buttons */
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    background: var(--bg-secondary, #ecf0f1);
    color: var(--text-primary, #2c3e50);
    transition: background 0.2s;
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

/* Table and buttons */
.expand-cell {
    width: 30px;
    text-align: center;
}
.btn-expand {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.8rem;
    padding: 5px;
    color: var(--text-secondary);
    transition: transform 0.2s;
}
.btn-expand.expanded {
    transform: rotate(90deg);
}
.expanded-row td {
    padding: 0 !important;
    background: var(--bg-secondary) !important;
}
.expanded-content {
    padding: 15px 20px;
    border-top: 1px solid var(--border-color);
}
.expanded-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.inner-table {
    width: 100%;
    font-size: 0.9rem;
}
.inner-table th,
.inner-table td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-light);
}
.inner-table th {
    background: var(--bg-primary);
    font-weight: 500;
}
.input-small {
    padding: 4px 8px;
    font-size: 0.85rem;
    width: 120px;
}
.btn-danger {
    background: #e74c3c;
    color: #fff;
}
.btn-danger:hover {
    background: #c0392b;
}
.badge-info {
    background: rgba(52, 152, 219, 0.2);
    color: #2980b9;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
}
.text-muted {
    color: var(--text-secondary);
}
tr.disabled {
    opacity: 0.5;
    background: var(--bg-secondary, #f5f5f5) !important;
}
tr.disabled td {
    color: var(--text-secondary, #999) !important;
}
.form-help {
    display: block;
    margin-top: 5px;
    font-size: 0.8rem;
    color: var(--text-secondary, #7f8c8d);
}
.actions-cell {
    white-space: nowrap;
}
.actions-cell .btn {
    margin-right: 5px;
}
.actions-cell .btn:last-child {
    margin-right: 0;
}
</style>

<script>
// Available assays data (loaded via PHP)
const availableAssaysData = <?= json_encode(
    !empty($sections) ? getAvailableAssays($pdo, array_column($sections, 'org_id'), 0) : []
) ?>;

// Assigned assays per workstation
const assignedAssaysData = {};
<?php foreach ($workstations as $ws): ?>
assignedAssaysData[<?= $ws['workstation_id'] ?>] = <?= json_encode(array_column(getAssignedAssays($pdo, $ws['workstation_id']), 'test_method_id')) ?>;
<?php endforeach; ?>

function toggleExpand(workstationId) {
    const row = document.getElementById('expanded-' + workstationId);
    const btn = document.querySelector(`tr[data-workstation-id="${workstationId}"] .btn-expand`);

    if (row.style.display === 'none') {
        row.style.display = 'table-row';
        btn.classList.add('expanded');
    } else {
        row.style.display = 'none';
        btn.classList.remove('expanded');
    }
}

function openModal(mode, data = null) {
    const modal = document.getElementById('workstationModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('workstationForm');
    const statusGroup = document.getElementById('statusGroup');

    form.reset();

    if (mode === 'edit' && data) {
        title.textContent = '<?= t('Edit Workstation') ?>';
        document.getElementById('formAction').value = 'update';
        document.getElementById('workstationId').value = data.workstation_id;
        document.getElementById('description').value = data.description;
        document.getElementById('equipment_id').value = data.equipment_id;
        document.getElementById('section_id').value = data.section_id;
        document.getElementById('serial').value = data.serial;
        document.getElementById('status').checked = data.status == 1;
        statusGroup.style.display = 'block';
    } else {
        title.textContent = '<?= t('New Workstation') ?>';
        document.getElementById('formAction').value = 'create';
        document.getElementById('workstationId').value = '';
        statusGroup.style.display = 'none';
    }

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('workstationModal').classList.remove('active');
}

function openAssignModal(workstationId, workstationName) {
    const modal = document.getElementById('assignModal');
    const title = document.getElementById('assignModalTitle');
    const select = document.getElementById('test_method_id');

    title.textContent = '<?= t('Assign Assay to') ?> ' + workstationName;
    document.getElementById('assignWorkstationId').value = workstationId;
    document.getElementById('assign_external_code').value = '';

    // Populate available assays (exclude already assigned)
    const assigned = assignedAssaysData[workstationId] || [];
    select.innerHTML = '<option value=""><?= t('Select...') ?></option>';

    availableAssaysData.forEach(assay => {
        if (!assigned.includes(assay.test_method_id)) {
            const option = document.createElement('option');
            option.value = assay.test_method_id;
            option.textContent = assay.test_name + ' - ' + assay.method_name + ' (' + assay.section_name + ')';
            select.appendChild(option);
        }
    });

    modal.classList.add('active');
}

function closeAssignModal() {
    document.getElementById('assignModal').classList.remove('active');
}

function openExternalCodeModal(workstationId, testMethodId, testName, currentCode) {
    const modal = document.getElementById('externalCodeModal');
    const title = document.getElementById('externalCodeModalTitle');

    title.textContent = '<?= t('Edit External Code') ?> - ' + testName;
    document.getElementById('extcode_workstation_id').value = workstationId;
    document.getElementById('extcode_test_method_id').value = testMethodId;
    document.getElementById('extcode_value').value = currentCode || '';

    modal.classList.add('active');
    document.getElementById('extcode_value').focus();
}

function closeExternalCodeModal() {
    document.getElementById('externalCodeModal').classList.remove('active');
}

function removeAssay(workstationId, testMethodId, testName) {
    if (!confirm('<?= t('Remove') ?> "' + testName + '" <?= t('from this workstation?') ?>')) {
        return;
    }

    const form = document.createElement('form');
    form.method = 'POST';
    form.innerHTML = `
        <input type="hidden" name="action" value="remove_assay">
        <input type="hidden" name="workstation_id" value="${workstationId}">
        <input type="hidden" name="test_method_id" value="${testMethodId}">
    `;
    document.body.appendChild(form);
    form.submit();
}

function updateExternalCode(workstationId, testMethodId, value) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.innerHTML = `
        <input type="hidden" name="action" value="update_external_code">
        <input type="hidden" name="workstation_id" value="${workstationId}">
        <input type="hidden" name="test_method_id" value="${testMethodId}">
        <input type="hidden" name="external_code" value="${value}">
    `;
    document.body.appendChild(form);
    form.submit();
}

// Close modals on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });
});

// Close modals on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
});
</script>

<?php require_once __DIR__ . '/../../includes/footer.php'; ?>
