<?php
/**
 * Profile Page - Change Password
 */

$pageTitle = 'Profilo - Biovarase';

require_once __DIR__ . '/../engine/auth.php';

// Require login
requireAuth();

$currentUser = getCurrentUser();

// Check for messages
$success = isset($_GET['success']) ? $_GET['success'] : null;
$error = isset($_GET['error']) ? $_GET['error'] : null;

// Get lab_id for links
$labId = isset($_GET['lab_id']) ? $_GET['lab_id'] : $currentUser['org_id'];
$labIdParam = $labId ? '?lab_id=' . htmlspecialchars($labId) : '';
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($pageTitle) ?></title>
    <link rel="stylesheet" href="/biovarase/css/dashboard.css">
    <style>
        .profile-container {
            max-width: 500px;
            margin: 40px auto;
            padding: 0 20px;
        }
        .profile-card {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        .profile-header {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .profile-header h1 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .profile-info {
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        .profile-info p {
            margin: 5px 0;
        }
        .form-section {
            margin-top: 30px;
        }
        .form-section h2 {
            font-size: 1.1rem;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #2c3e50;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
            box-sizing: border-box;
        }
        .form-group input:focus {
            border-color: #3498db;
            outline: none;
            box-shadow: 0 0 0 2px rgba(52,152,219,0.2);
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-primary {
            background: #3498db;
            color: #fff;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-secondary {
            background: #95a5a6;
            color: #fff;
            text-decoration: none;
            display: inline-block;
        }
        .btn-secondary:hover {
            background: #7f8c8d;
        }
        .form-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .alert {
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <?php
    $pageTitle = 'Profilo - Biovarase';
    require_once __DIR__ . '/../includes/header.php';
    ?>

    <div class="profile-container">
        <div class="profile-card">
            <div class="profile-header">
                <h1>Profilo Utente</h1>
                <div class="profile-info">
                    <p><strong>Nome:</strong> <?= htmlspecialchars($currentUser['first_name'] . ' ' . $currentUser['last_name']) ?></p>
                    <p><strong>Username:</strong> <?= htmlspecialchars($currentUser['username']) ?></p>
                    <p><strong>Ruolo:</strong> <?= getRoleName($currentUser['role']) ?></p>
                    <?php if ($currentUser['org_name']): ?>
                    <p><strong>Organizzazione:</strong> <?= htmlspecialchars($currentUser['org_name']) ?></p>
                    <?php endif; ?>
                </div>
            </div>

            <?php if ($success): ?>
            <div class="alert alert-success">
                <?= htmlspecialchars($success) ?>
            </div>
            <?php endif; ?>

            <?php if ($error): ?>
            <div class="alert alert-error">
                <?= htmlspecialchars($error) ?>
            </div>
            <?php endif; ?>

            <div class="form-section">
                <h2>Cambia Password</h2>
                <form action="/biovarase/change-password" method="POST">
                    <input type="hidden" name="lab_id" value="<?= htmlspecialchars($labId) ?>">

                    <div class="form-group">
                        <label for="current_password">Password Attuale</label>
                        <input type="password" id="current_password" name="current_password" required>
                    </div>

                    <div class="form-group">
                        <label for="new_password">Nuova Password</label>
                        <input type="password" id="new_password" name="new_password" required minlength="6">
                    </div>

                    <div class="form-group">
                        <label for="confirm_password">Conferma Nuova Password</label>
                        <input type="password" id="confirm_password" name="confirm_password" required minlength="6">
                    </div>

                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Cambia Password</button>
                        <a href="/biovarase/dashboard<?= $labIdParam ?>" class="btn btn-secondary">Annulla</a>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <?php require_once __DIR__ . '/../includes/footer.php'; ?>
</body>
</html>
