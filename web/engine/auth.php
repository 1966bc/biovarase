<?php
/**
 * Auth - Session and authentication management
 *
 * Handles login, logout, session management, and role verification.
 * Compatible with bcrypt passwords created by Python/Biovarase desktop.
 */

// Start session if not already started
if (session_status() === PHP_SESSION_NONE) {
    session_start([
        'cookie_httponly' => true,
        'cookie_samesite' => 'Strict'
    ]);
}

// Check session timeout
checkSessionTimeout();

// Role constants (same as Biovarase desktop)
define('ROLE_APP_ADMIN', 0);
define('ROLE_COUNTRY_ADMIN', 1);
define('ROLE_REGIONAL_ADMIN', 2);
define('ROLE_LAB_ADMIN', 3);
define('ROLE_SUPERUSER', 4);
define('ROLE_TECHNICIAN', 5);
define('ROLE_VIEWER', 6);

/**
 * Check session timeout and logout if expired
 */
function checkSessionTimeout()
{
    if (!isset($_SESSION['user']) || !isset($_SESSION['last_activity'])) {
        return;
    }

    $user = $_SESSION['user'];

    // Check if timeout is enabled for this user
    if (empty($user['enable_time'])) {
        return;
    }

    $timeout = (int)$user['elapsing_time'] * 60; // Convert minutes to seconds
    if ($timeout <= 0) {
        return;
    }

    if (time() - $_SESSION['last_activity'] > $timeout) {
        logout();
        header('Location: /biovarase/login?error=' . urlencode('Sessione scaduta'));
        exit;
    }

    // Update last activity time
    $_SESSION['last_activity'] = time();
}

/**
 * Check if user is logged in
 */
function isLoggedIn()
{
    return isset($_SESSION['user']) && !empty($_SESSION['user']['user_id']);
}

/**
 * Get current logged user or null
 */
function getCurrentUser()
{
    return isLoggedIn() ? $_SESSION['user'] : null;
}

/**
 * Get current user's role (returns ROLE_VIEWER + 1 if not logged in)
 */
function getCurrentRole()
{
    return isLoggedIn() ? (int)$_SESSION['user']['role'] : 99;
}

/**
 * Get current user's org_id
 */
function getCurrentOrgId()
{
    return isLoggedIn() ? $_SESSION['user']['org_id'] : null;
}

/**
 * Get current user's user_id
 */
function getCurrentUserId()
{
    return isLoggedIn() ? $_SESSION['user']['user_id'] : null;
}

/**
 * Check if current user has at least the given role level
 * Lower role number = more permissions
 */
function hasRole($maxRole)
{
    return isLoggedIn() && getCurrentRole() <= $maxRole;
}

/**
 * Check if user is admin (role 0-3)
 */
function isAdmin()
{
    return hasRole(ROLE_LAB_ADMIN);
}

/**
 * Check if user can validate QC (role 0-4)
 */
function canValidateQC()
{
    return hasRole(ROLE_SUPERUSER);
}

/**
 * Check if user can modify data (role 0-5)
 */
function canModifyData()
{
    return hasRole(ROLE_TECHNICIAN);
}

/**
 * Check if user is read-only (role 6)
 */
function isReadOnly()
{
    return getCurrentRole() === ROLE_VIEWER;
}

/**
 * Attempt to login user
 * Returns: ['success' => bool, 'message' => string, 'user' => array|null]
 */
function attemptLogin($username, $password, $pdo)
{
    // Sanitize username
    $username = trim($username);

    if (empty($username) || empty($password)) {
        return ['success' => false, 'message' => 'Username e password richiesti'];
    }

    try {
        // Fetch user by nickname (including timeout settings)
        $stmt = $pdo->prepare("
            SELECT u.user_id, u.nickname as username, u.pswrd, u.role, u.status as enable, u.org_id,
                   u.elapsing_time, u.enable_time,
                   u.last_name, u.first_name,
                   o.description as org_name
            FROM users u
            LEFT JOIN organizations o ON o.org_id = u.org_id
            WHERE u.nickname = ?
            LIMIT 1
        ");
        $stmt->execute([$username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$user) {
            return ['success' => false, 'message' => 'Credenziali non valide'];
        }

        // Check if user is enabled
        if (!$user['enable']) {
            return ['success' => false, 'message' => 'Utente disabilitato'];
        }

        // Verify password (works with bcrypt from Python)
        if (!password_verify($password, $user['pswrd'])) {
            return ['success' => false, 'message' => 'Credenziali non valide'];
        }

        // Login successful - store user in session (without password hash)
        unset($user['pswrd']);
        $_SESSION['user'] = $user;
        $_SESSION['login_time'] = time();
        $_SESSION['last_activity'] = time();

        // Get lab_id for redirect (for lab users, org_id is the lab_id)
        $labId = $user['org_id'];

        return ['success' => true, 'message' => 'Login effettuato', 'user' => $user, 'lab_id' => $labId];

    } catch (PDOException $e) {
        error_log("Biovarase Auth Error: " . $e->getMessage());
        return ['success' => false, 'message' => 'Errore di sistema'];
    }
}

/**
 * Logout current user
 */
function logout()
{
    $_SESSION = [];

    if (ini_get("session.use_cookies")) {
        $params = session_get_cookie_params();
        setcookie(session_name(), '', time() - 42000,
            $params["path"], $params["domain"],
            $params["secure"], $params["httponly"]
        );
    }

    session_destroy();
}

/**
 * Require authentication - redirect to login if not logged in
 */
function requireAuth()
{
    if (!isLoggedIn()) {
        header('Location: /biovarase/login');
        exit;
    }
}

/**
 * Require specific role - show 403 if insufficient permissions
 */
function requireRole($maxRole)
{
    requireAuth();

    if (!hasRole($maxRole)) {
        http_response_code(403);
        echo "Accesso negato. Permessi insufficienti.";
        exit;
    }
}

/**
 * Get role name in Italian
 */
function getRoleName($role)
{
    $roles = [
        ROLE_APP_ADMIN => 'App Admin',
        ROLE_COUNTRY_ADMIN => 'Country Admin',
        ROLE_REGIONAL_ADMIN => 'Regional Admin',
        ROLE_LAB_ADMIN => 'Lab Admin',
        ROLE_SUPERUSER => 'Superuser',
        ROLE_TECHNICIAN => 'Tecnico',
        ROLE_VIEWER => 'Viewer'
    ];

    return isset($roles[$role]) ? $roles[$role] : 'Sconosciuto';
}

/**
 * Check if user can modify a specific result
 *
 * Permission logic:
 * - Role 0-3 (Admin hierarchy): can modify any result in their org scope
 * - Role 4-5 (Superuser/Technician): can modify if:
 *   a) created_by = current user (they created it), OR
 *   b) created_by IS NULL (instrument data, team can modify)
 *
 * @param array $result The result record with created_by and org_id
 * @param int|null $userSectionId The user's section org_id (for instrument data check)
 * @return bool
 */
function canModifyResult($result, $userSectionId = null)
{
    if (!isLoggedIn()) {
        return false;
    }

    $currentUser = getCurrentUser();
    $currentRole = getCurrentRole();
    $currentUserId = $currentUser['user_id'];

    // Role 0-3 (Admin hierarchy): can modify any result in their org scope
    if ($currentRole <= ROLE_LAB_ADMIN) {
        return true;
    }

    // Role 4-5 (Superuser/Technician)
    if ($currentRole <= ROLE_TECHNICIAN) {
        // Case a) They created this result
        if (!empty($result['created_by']) && $result['created_by'] == $currentUserId) {
            return true;
        }

        // Case b) Instrument data (created_by IS NULL) - team can modify
        if (empty($result['created_by'])) {
            return true;
        }
    }

    // Role 6 (Viewer) or not matching any condition
    return false;
}

/**
 * Check if user can void (annullare) a result
 * Same logic as canModifyResult - if you can modify, you can void
 */
function canVoidResult($result, $userSectionId = null)
{
    return canModifyResult($result, $userSectionId);
}

/**
 * Check if user is App Admin (role 0)
 */
function isAppAdmin()
{
    return getCurrentRole() === ROLE_APP_ADMIN;
}

/**
 * Get working lab ID
 * - For App Admin: returns selected working_lab_id from session
 * - For other users: returns their org_id (their assigned lab)
 */
function getWorkingLabId()
{
    if (!isLoggedIn()) {
        return null;
    }

    // App Admin uses working_lab_id from session
    if (isAppAdmin()) {
        return isset($_SESSION['working_lab_id']) ? $_SESSION['working_lab_id'] : null;
    }

    // Other users use their org_id
    return getCurrentOrgId();
}

/**
 * Set working lab ID (for App Admin)
 */
function setWorkingLabId($labId)
{
    if (!isLoggedIn() || !isAppAdmin()) {
        return false;
    }

    $_SESSION['working_lab_id'] = $labId ? (int)$labId : null;
    return true;
}

/**
 * Get working lab name
 */
function getWorkingLabName()
{
    if (!isLoggedIn()) {
        return null;
    }

    // App Admin with working lab
    if (isAppAdmin() && isset($_SESSION['working_lab_name'])) {
        return $_SESSION['working_lab_name'];
    }

    // Other users - org_name from session
    $user = getCurrentUser();
    return $user['org_name'] ?? null;
}

/**
 * Set working lab (ID and name)
 */
function setWorkingLab($labId, $labName)
{
    if (!isLoggedIn() || !isAppAdmin()) {
        return false;
    }

    $_SESSION['working_lab_id'] = $labId ? (int)$labId : null;
    $_SESSION['working_lab_name'] = $labName;
    return true;
}

/**
 * Check if user needs to select a lab before proceeding
 * Returns true for App Admin who hasn't selected a working lab
 */
function needsLabSelection()
{
    if (!isLoggedIn()) {
        return false;
    }

    // Only App Admin needs to select a lab
    if (!isAppAdmin()) {
        return false;
    }

    // Check if working lab is set
    return empty($_SESSION['working_lab_id']);
}

/**
 * Require working lab - redirect to lab selector if needed
 */
function requireWorkingLab()
{
    requireAuth();

    if (needsLabSelection()) {
        header('Location: /biovarase/select-lab');
        exit;
    }
}

/**
 * Get site name (hospital) for the working lab
 * Site is the parent of the lab in the organization hierarchy
 */
function getWorkingSiteName()
{
    if (!isLoggedIn()) {
        return null;
    }

    // Check if already cached in session
    if (isset($_SESSION['working_site_name'])) {
        return $_SESSION['working_site_name'];
    }

    $workingLabId = getWorkingLabId();
    if (!$workingLabId) {
        return null;
    }

    // Query to get site (parent of lab)
    try {
        require_once __DIR__ . '/../api/config.php';
        $pdo = getDbConnection();
        $stmt = $pdo->prepare("
            SELECT site.description as site_name
            FROM organizations lab
            JOIN organizations site ON lab.parent_id = site.org_id
            WHERE lab.org_id = ? AND site.org_type = 'site'
        ");
        $stmt->execute([$workingLabId]);
        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($result) {
            $_SESSION['working_site_name'] = $result['site_name'];
            return $result['site_name'];
        }
    } catch (PDOException $e) {
        // Silently fail
    }

    return null;
}

/**
 * Set working lab with site info
 */
function setWorkingLabWithSite($labId, $labName, $siteName = null)
{
    if (!isLoggedIn() || !isAppAdmin()) {
        return false;
    }

    $_SESSION['working_lab_id'] = $labId ? (int)$labId : null;
    $_SESSION['working_lab_name'] = $labName;
    $_SESSION['working_site_name'] = $siteName;
    return true;
}
