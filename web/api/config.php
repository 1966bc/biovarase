<?php
/**
 * Biovarase Web Dashboard - Configuration
 *
 * Database connection and common utilities for multi-tenant API.
 *
 * IMPORTANT: This file contains sensitive credentials.
 * - Never commit to version control
 * - Restrict access via .htaccess
 * - In production, consider using environment variables
 */

// Error reporting (disable in production)
error_reporting(E_ALL);
ini_set('display_errors', 0); // Log errors, don't display
ini_set('log_errors', 1);

// Database configuration - EDIT FOR YOUR ENVIRONMENT
define('DB_HOST', 'localhost');           // Production: use actual DB server IP
define('DB_NAME', 'biovarase');
define('DB_USER', 'biovarase');           // Change for production
define('DB_PASS', 'CHANGE_THIS_PASSWORD'); // IMPORTANT: Set actual password
define('DB_CHARSET', 'utf8mb4');

/**
 * Get PDO database connection
 *
 * @return PDO
 * @throws PDOException
 */
function getDBConnection(): PDO {
    static $pdo = null;

    if ($pdo === null) {
        $dsn = sprintf(
            "mysql:host=%s;dbname=%s;charset=%s",
            DB_HOST, DB_NAME, DB_CHARSET
        );

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];

        $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
    }

    return $pdo;
}

/**
 * Send JSON response
 *
 * @param mixed $data Data to encode
 * @param int $status HTTP status code
 */
function jsonResponse($data, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

/**
 * Send error response
 *
 * @param string $message Error message
 * @param int $status HTTP status code
 */
function jsonError(string $message, int $status = 400): void {
    jsonResponse(['error' => $message], $status);
}

/**
 * Get current lab_id from request
 *
 * Multi-tenant: Every API call must be scoped to a lab.
 * The lab_id can come from:
 * 1. Session (after login)
 * 2. Header X-Lab-Id (for API clients)
 * 3. Query parameter lab_id (for development/testing)
 *
 * In production, should use session or authenticated token.
 *
 * @return int|null
 */
function getLabId(): ?int {
    // Priority 1: Session
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
    if (isset($_SESSION['lab_id'])) {
        return (int)$_SESSION['lab_id'];
    }

    // Priority 2: Header
    $headers = getallheaders();
    if (isset($headers['X-Lab-Id'])) {
        return (int)$headers['X-Lab-Id'];
    }

    // Priority 3: Query parameter (development only!)
    if (isset($_GET['lab_id'])) {
        return (int)$_GET['lab_id'];
    }

    return null;
}

/**
 * Require lab_id or fail
 *
 * @return int
 */
function requireLabId(): int {
    $labId = getLabId();
    if ($labId === null) {
        jsonError('lab_id required (multi-tenant)', 401);
    }
    return $labId;
}

/**
 * Get date parameter or default to today
 *
 * @return string Date in Y-m-d format
 */
function getDateParam(): string {
    $date = $_GET['date'] ?? date('Y-m-d');

    // Validate date format
    $d = DateTime::createFromFormat('Y-m-d', $date);
    if (!$d || $d->format('Y-m-d') !== $date) {
        jsonError('Invalid date format. Use YYYY-MM-DD');
    }

    return $date;
}

/**
 * Validate that request method is allowed
 *
 * @param array $allowed Allowed methods
 */
function requireMethod(array $allowed): void {
    if (!in_array($_SERVER['REQUEST_METHOD'], $allowed)) {
        jsonError('Method not allowed', 405);
    }
}
