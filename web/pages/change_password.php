<?php
/**
 * Change Password Action
 */

require_once __DIR__ . '/../engine/auth.php';
require_once __DIR__ . '/../api/config.php';

// Require login
requireAuth();

// Only accept POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /biovarase/profile');
    exit;
}

$currentUser = getCurrentUser();
$labId = isset($_POST['lab_id']) ? $_POST['lab_id'] : $currentUser['org_id'];
$labIdParam = $labId ? '&lab_id=' . urlencode($labId) : '';

$currentPassword = isset($_POST['current_password']) ? $_POST['current_password'] : '';
$newPassword = isset($_POST['new_password']) ? $_POST['new_password'] : '';
$confirmPassword = isset($_POST['confirm_password']) ? $_POST['confirm_password'] : '';

// Validate inputs
if (empty($currentPassword) || empty($newPassword) || empty($confirmPassword)) {
    header('Location: /biovarase/profile?error=' . urlencode('Tutti i campi sono obbligatori') . $labIdParam);
    exit;
}

if ($newPassword !== $confirmPassword) {
    header('Location: /biovarase/profile?error=' . urlencode('Le password non coincidono') . $labIdParam);
    exit;
}

if (strlen($newPassword) < 6) {
    header('Location: /biovarase/profile?error=' . urlencode('La password deve essere di almeno 6 caratteri') . $labIdParam);
    exit;
}

try {
    $pdo = getDBConnection();

    // Verify current password
    $stmt = $pdo->prepare("SELECT pswrd FROM users WHERE user_id = ?");
    $stmt->execute([$currentUser['user_id']]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$user || !password_verify($currentPassword, $user['pswrd'])) {
        header('Location: /biovarase/profile?error=' . urlencode('Password attuale non corretta') . $labIdParam);
        exit;
    }

    // Hash new password with bcrypt (compatible with Python)
    $hashedPassword = password_hash($newPassword, PASSWORD_BCRYPT, ['cost' => 12]);

    // Update password
    $stmt = $pdo->prepare("UPDATE users SET pswrd = ? WHERE user_id = ?");
    $stmt->execute([$hashedPassword, $currentUser['user_id']]);

    header('Location: /biovarase/profile?success=' . urlencode('Password aggiornata con successo') . $labIdParam);
    exit;

} catch (PDOException $e) {
    error_log("Biovarase Password Change Error: " . $e->getMessage());
    header('Location: /biovarase/profile?error=' . urlencode('Errore di sistema') . $labIdParam);
    exit;
}
