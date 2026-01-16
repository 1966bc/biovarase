<?php
/**
 * Logout - End user session
 */

require_once __DIR__ . '/../engine/auth.php';

logout();

header('Location: /biovarase/dashboard');
exit;
