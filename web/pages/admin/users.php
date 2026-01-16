<?php
/**
 * CRUD for Users
 * Lab Admin (role ≤ 3) can manage users
 * Can only create users with equal or lower privileges
 */

$pageTitle = 'Users - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

// Check permission - Lab Admin or higher
if (!isAdmin()) {
    header('Location: /biovarase/admin');
    exit;
}

$currentRole = getCurrentRole();
$isAppAdmin = ($currentRole === 0);

// Role definitions
$roles = [
    0 => ['label' => 'App Admin', 'description' => 'Full system access'],
    1 => ['label' => 'Country Admin', 'description' => 'Country-level administration'],
    2 => ['label' => 'Regional Admin', 'description' => 'Regional administration'],
    3 => ['label' => 'Lab Admin', 'description' => 'Laboratory administration'],
    4 => ['label' => 'Superuser', 'description' => 'QC validation, batch management'],
    5 => ['label' => 'Technician', 'description' => 'Data entry'],
    6 => ['label' => 'Viewer', 'description' => 'Read-only access'],
];

// Filter roles user can assign (only equal or lower privileges)
$assignableRoles = array_filter($roles, function($role) use ($currentRole) {
    return $role >= $currentRole;
}, ARRAY_FILTER_USE_KEY);

// Handle POST actions
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? $_POST['action'] : '';

    try {
        $pdo = getDbConnection();

        if ($action === 'create') {
            $last_name = trim($_POST['last_name']);
            $first_name = trim($_POST['first_name']);
            $nickname = trim($_POST['nickname']);
            $email = trim($_POST['email']);
            $password = $_POST['password'];
            $role = intval($_POST['role']);
            $org_id = !empty($_POST['org_id']) ? intval($_POST['org_id']) : null;

            if (empty($last_name)) {
                throw new Exception(t('Last name is required'));
            }
            if (empty($nickname)) {
                throw new Exception(t('Username is required'));
            }
            if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
                throw new Exception(t('Valid email is required'));
            }
            if (empty($password) || strlen($password) < 6) {
                throw new Exception(t('Password must be at least 6 characters'));
            }
            if ($role < $currentRole) {
                throw new Exception(t('Cannot create user with higher privileges'));
            }

            // Check nickname uniqueness
            $stmt = $pdo->prepare("SELECT COUNT(*) FROM users WHERE nickname = ?");
            $stmt->execute([$nickname]);
            if ($stmt->fetchColumn() > 0) {
                throw new Exception(t('Username already exists'));
            }

            // Hash password with bcrypt
            $hashedPassword = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);

            $stmt = $pdo->prepare("INSERT INTO users (last_name, first_name, nickname, email, pswrd, role, org_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, 1)");
            $stmt->execute([$last_name, $first_name ?: null, $nickname, $email, $hashedPassword, $role, $org_id]);
            $message = t('User') . " '$nickname' " . t('created successfully');
            $messageType = 'success';

        } elseif ($action === 'update') {
            $id = intval($_POST['user_id']);
            $last_name = trim($_POST['last_name']);
            $first_name = trim($_POST['first_name']);
            $nickname = trim($_POST['nickname']);
            $email = trim($_POST['email']);
            $role = intval($_POST['role']);
            $org_id = !empty($_POST['org_id']) ? intval($_POST['org_id']) : null;
            $status = isset($_POST['status']) ? 1 : 0;

            if (empty($last_name)) {
                throw new Exception(t('Last name is required'));
            }
            if (empty($nickname)) {
                throw new Exception(t('Username is required'));
            }
            if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
                throw new Exception(t('Valid email is required'));
            }

            // Check we're not editing a user with higher privileges
            $stmt = $pdo->prepare("SELECT role FROM users WHERE user_id = ?");
            $stmt->execute([$id]);
            $existingRole = $stmt->fetchColumn();
            if ($existingRole < $currentRole) {
                throw new Exception(t('Cannot edit user with higher privileges'));
            }

            // Check nickname uniqueness (excluding self)
            $stmt = $pdo->prepare("SELECT COUNT(*) FROM users WHERE nickname = ? AND user_id != ?");
            $stmt->execute([$nickname, $id]);
            if ($stmt->fetchColumn() > 0) {
                throw new Exception(t('Username already exists'));
            }

            $stmt = $pdo->prepare("UPDATE users SET last_name = ?, first_name = ?, nickname = ?, email = ?, role = ?, org_id = ?, status = ? WHERE user_id = ?");
            $stmt->execute([$last_name, $first_name ?: null, $nickname, $email, $role, $org_id, $status, $id]);
            $message = t('User') . ' ' . t('updated successfully');
            $messageType = 'success';

        } elseif ($action === 'reset_password') {
            $id = intval($_POST['user_id']);
            $password = $_POST['new_password'];

            if (empty($password) || strlen($password) < 6) {
                throw new Exception(t('Password must be at least 6 characters'));
            }

            // Check we're not resetting password for user with higher privileges
            $stmt = $pdo->prepare("SELECT role FROM users WHERE user_id = ?");
            $stmt->execute([$id]);
            $existingRole = $stmt->fetchColumn();
            if ($existingRole < $currentRole) {
                throw new Exception(t('Cannot reset password for user with higher privileges'));
            }

            $hashedPassword = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
            $stmt = $pdo->prepare("UPDATE users SET pswrd = ? WHERE user_id = ?");
            $stmt->execute([$hashedPassword, $id]);
            $message = t('Password reset successfully');
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
    $filterRole = isset($_GET['role']) && $_GET['role'] !== '' ? intval($_GET['role']) : -1;

    // Get organizations for filter and forms
    $stmt = $pdo->query("SELECT org_id, org_type, description FROM organizations WHERE status = 1 ORDER BY org_type, description");
    $organizations = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Build query
    $sql = "SELECT u.user_id, u.last_name, u.first_name, u.nickname, u.email, u.role, u.org_id, u.status,
                   o.description as org_name, o.org_type
            FROM users u
            LEFT JOIN organizations o ON u.org_id = o.org_id
            WHERE 1=1";
    $params = [];

    // Non-app-admin can only see users with equal or lower privileges
    if (!$isAppAdmin) {
        $sql .= " AND u.role >= ?";
        $params[] = $currentRole;
    }

    if (!empty($search)) {
        $sql .= " AND (u.last_name LIKE ? OR u.first_name LIKE ? OR u.nickname LIKE ?)";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }
    if (!$showDisabled) {
        $sql .= " AND u.status = 1";
    }
    if ($filterRole >= 0) {
        $sql .= " AND u.role = ?";
        $params[] = $filterRole;
    }
    $sql .= " ORDER BY u.last_name, u.first_name";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Counts
    $countSql = "SELECT COUNT(*) FROM users WHERE status = 1";
    if (!$isAppAdmin) {
        $countSql .= " AND role >= $currentRole";
    }
    $stmt = $pdo->query($countSql);
    $activeCount = $stmt->fetchColumn();

    $countSql = "SELECT COUNT(*) FROM users WHERE status = 0";
    if (!$isAppAdmin) {
        $countSql .= " AND role >= $currentRole";
    }
    $stmt = $pdo->query($countSql);
    $disabledCount = $stmt->fetchColumn();

} catch (PDOException $e) {
    $rows = [];
    $organizations = [];
    $message = t('Data loading error') . ': ' . $e->getMessage();
    $messageType = 'error';
    $activeCount = 0;
    $disabledCount = 0;
}
?>

<style>
    .admin-container { max-width: 1400px; margin: 0 auto; padding: 20px; }
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
    .btn-warning { background: #f39c12; color: #fff; }
    .btn-warning:hover { background: #d68910; }
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
    .badge-role { padding: 3px 8px; border-radius: 3px; font-size: 0.75rem; }
    .badge-role-0 { background: #f8d7da; color: #721c24; }
    .badge-role-1, .badge-role-2 { background: #fff3cd; color: #856404; }
    .badge-role-3 { background: #d4edda; color: #155724; }
    .badge-role-4 { background: #d1ecf1; color: #0c5460; }
    .badge-role-5 { background: #e2e3e5; color: #383d41; }
    .badge-role-6 { background: #f5f5f5; color: #6c757d; }
    .message { padding: 12px 15px; border-radius: 4px; margin-bottom: 20px; }
    .message-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .message-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; }
    .modal-overlay.active { display: flex; }
    .modal { background: #fff; border-radius: 8px; padding: 20px; min-width: 500px; max-width: 600px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .modal h2 { margin: 0 0 20px 0; color: #2c3e50; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #2c3e50; }
    .form-group input[type="text"], .form-group input[type="password"], .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
    .form-group input[type="checkbox"] { margin-right: 8px; }
    .form-group small { color: #7f8c8d; font-size: 0.85rem; }
    .form-row { display: flex; gap: 15px; }
    .form-row .form-group { flex: 1; }
    .form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
    .empty-state { text-align: center; padding: 40px; color: #7f8c8d; }
</style>

<div class="admin-container">
    <div class="breadcrumb">
        <a href="/biovarase/admin"><?= t('Admin') ?></a> / <?= t('Users') ?>
    </div>

    <div class="admin-header">
        <h1><?= t('Users') ?></h1>
        <button class="btn btn-success" onclick="openCreateModal()">+ <?= t('New') ?> <?= t('User') ?></button>
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
            <select name="role" onchange="this.form.submit()">
                <option value=""><?= t('All roles') ?></option>
                <?php foreach ($assignableRoles as $roleId => $roleInfo): ?>
                <option value="<?= $roleId ?>" <?= $filterRole === $roleId ? 'selected' : '' ?>><?= t($roleInfo['label']) ?></option>
                <?php endforeach; ?>
            </select>
            <label>
                <input type="checkbox" name="show_disabled" <?= $showDisabled ? 'checked' : '' ?> onchange="this.form.submit()">
                <?= t('Show disabled') ?>
            </label>
            <button type="submit" class="btn btn-primary"><?= t('Search') ?></button>
            <?php if ($search || $showDisabled || $filterRole >= 0): ?>
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
                <th><?= t('Name') ?></th>
                <th><?= t('Username') ?></th>
                <th><?= t('Email') ?></th>
                <th><?= t('Role') ?></th>
                <th><?= t('Organization') ?></th>
                <th><?= t('Status') ?></th>
                <th><?= t('Actions') ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($rows as $row): ?>
            <tr class="<?= $row['status'] ? '' : 'disabled' ?>">
                <td><?= $row['user_id'] ?></td>
                <td><?= htmlspecialchars($row['last_name'] . ($row['first_name'] ? ', ' . $row['first_name'] : '')) ?></td>
                <td><?= htmlspecialchars($row['nickname']) ?></td>
                <td><?= htmlspecialchars($row['email'] ?? '') ?></td>
                <td><span class="badge-role badge-role-<?= $row['role'] ?>"><?= t($roles[$row['role']]['label']) ?></span></td>
                <td><?= htmlspecialchars($row['org_name'] ?? '-') ?></td>
                <td>
                    <?php if ($row['status']): ?>
                    <span class="badge badge-success"><?= t('Active') ?></span>
                    <?php else: ?>
                    <span class="badge badge-secondary"><?= t('Disabled') ?></span>
                    <?php endif; ?>
                </td>
                <td class="actions-cell">
                    <button class="btn btn-primary btn-sm" onclick="openEditModal(<?= htmlspecialchars(json_encode($row)) ?>)"><?= t('Edit') ?></button>
                    <button class="btn btn-warning btn-sm" onclick="openPasswordModal(<?= $row['user_id'] ?>, '<?= htmlspecialchars(addslashes($row['nickname'])) ?>')"><?= t('Reset Password') ?></button>
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
        <h2 id="modalTitle"><?= t('New') ?> <?= t('User') ?></h2>
        <form method="post" id="editForm">
            <input type="hidden" name="action" id="formAction" value="create">
            <input type="hidden" name="user_id" id="formPk" value="">

            <div class="form-row">
                <div class="form-group">
                    <label for="last_name"><?= t('Last Name') ?> *</label>
                    <input type="text" id="last_name" name="last_name" required maxlength="35">
                </div>
                <div class="form-group">
                    <label for="first_name"><?= t('First Name') ?></label>
                    <input type="text" id="first_name" name="first_name" maxlength="35">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="nickname"><?= t('Username') ?> *</label>
                    <input type="text" id="nickname" name="nickname" required maxlength="35">
                </div>
                <div class="form-group">
                    <label for="email"><?= t('Email') ?> *</label>
                    <input type="email" id="email" name="email" required maxlength="100">
                </div>
            </div>

            <div class="form-group" id="passwordGroup">
                <label for="password"><?= t('Password') ?> *</label>
                <input type="password" id="password" name="password" minlength="6">
                <small><?= t('Minimum 6 characters') ?></small>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="role"><?= t('Role') ?> *</label>
                    <select id="role" name="role" required>
                        <?php foreach ($assignableRoles as $roleId => $roleInfo): ?>
                        <option value="<?= $roleId ?>"><?= t($roleInfo['label']) ?> - <?= t($roleInfo['description']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="form-group">
                    <label for="org_id"><?= t('Organization') ?></label>
                    <select id="org_id" name="org_id">
                        <option value=""><?= t('No organization (global)') ?></option>
                        <?php foreach ($organizations as $org): ?>
                        <option value="<?= $org['org_id'] ?>"><?= htmlspecialchars($org['description']) ?> (<?= $org['org_type'] ?>)</option>
                        <?php endforeach; ?>
                    </select>
                </div>
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

<!-- Password Reset Modal -->
<div class="modal-overlay" id="passwordModal">
    <div class="modal">
        <h2><?= t('Reset Password') ?></h2>
        <p><?= t('Reset password for user') ?>: <strong id="passwordUserName"></strong></p>
        <form method="post" id="passwordForm">
            <input type="hidden" name="action" value="reset_password">
            <input type="hidden" name="user_id" id="passwordUserId" value="">

            <div class="form-group">
                <label for="new_password"><?= t('New Password') ?> *</label>
                <input type="password" id="new_password" name="new_password" required minlength="6">
                <small><?= t('Minimum 6 characters') ?></small>
            </div>

            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closePasswordModal()"><?= t('Cancel') ?></button>
                <button type="submit" class="btn btn-warning"><?= t('Reset Password') ?></button>
            </div>
        </form>
    </div>
</div>

<script>
function openCreateModal() {
    document.getElementById('modalTitle').textContent = '<?= t('New') ?> <?= t('User') ?>';
    document.getElementById('formAction').value = 'create';
    document.getElementById('formPk').value = '';
    document.getElementById('last_name').value = '';
    document.getElementById('first_name').value = '';
    document.getElementById('nickname').value = '';
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
    document.getElementById('password').required = true;
    document.getElementById('passwordGroup').style.display = 'block';
    document.getElementById('role').value = '<?= max(array_keys($assignableRoles)) ?>';
    document.getElementById('org_id').value = '';
    document.getElementById('status').checked = true;
    document.getElementById('statusGroup').style.display = 'none';
    document.getElementById('submitBtn').textContent = '<?= t('Create') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('last_name').focus();
}

function openEditModal(row) {
    document.getElementById('modalTitle').textContent = '<?= t('Edit') ?> <?= t('User') ?>';
    document.getElementById('formAction').value = 'update';
    document.getElementById('formPk').value = row.user_id;
    document.getElementById('last_name').value = row.last_name;
    document.getElementById('first_name').value = row.first_name || '';
    document.getElementById('nickname').value = row.nickname;
    document.getElementById('email').value = row.email || '';
    document.getElementById('password').value = '';
    document.getElementById('password').required = false;
    document.getElementById('passwordGroup').style.display = 'none';
    document.getElementById('role').value = row.role;
    document.getElementById('org_id').value = row.org_id || '';
    document.getElementById('status').checked = row.status == 1;
    document.getElementById('statusGroup').style.display = 'block';
    document.getElementById('submitBtn').textContent = '<?= t('Save') ?>';
    document.getElementById('editModal').classList.add('active');
    document.getElementById('last_name').focus();
}

function closeModal() { document.getElementById('editModal').classList.remove('active'); }

function openPasswordModal(userId, userName) {
    document.getElementById('passwordUserId').value = userId;
    document.getElementById('passwordUserName').textContent = userName;
    document.getElementById('new_password').value = '';
    document.getElementById('passwordModal').classList.add('active');
    document.getElementById('new_password').focus();
}

function closePasswordModal() { document.getElementById('passwordModal').classList.remove('active'); }

document.getElementById('editModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
document.getElementById('passwordModal').addEventListener('click', function(e) { if (e.target === this) closePasswordModal(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeModal(); closePasswordModal(); } });
</script>

<?php require_once __DIR__ . '/../../includes/footer.php'; ?>
