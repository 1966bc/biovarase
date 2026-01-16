<?php
/**
 * Settings API - Handle user preferences
 *
 * POST /api/settings
 * Body: {action: 'setLanguage', language: 'it'|'en'}
 */

require_once __DIR__ . '/../engine/i18n.php';

// Only accept POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Content-Type: application/json');
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get JSON body
$input = json_decode(file_get_contents('php://input'), true);

if (!$input || !isset($input['action'])) {
    header('Content-Type: application/json');
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request']);
    exit;
}

$action = $input['action'];

switch ($action) {
    case 'setLanguage':
        $lang = isset($input['language']) ? $input['language'] : null;
        if ($lang && setLanguage($lang)) {
            // Cookie is set by setLanguage(), now send JSON response
            header('Content-Type: application/json');
            echo json_encode(['success' => true, 'language' => $lang]);
        } else {
            header('Content-Type: application/json');
            http_response_code(400);
            echo json_encode(['error' => 'Invalid language']);
        }
        break;

    default:
        header('Content-Type: application/json');
        http_response_code(400);
        echo json_encode(['error' => 'Unknown action']);
}
