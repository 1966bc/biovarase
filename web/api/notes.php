<?php
/**
 * Notes API - Get/Create notes for a result
 *
 * GET: Get notes for a result
 * POST: Create a new note (requires login)
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/../engine/auth.php';

requireMethod(['GET', 'POST']);

try {
    $pdo = getDBConnection();

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        // Get notes for a result
        $resultId = isset($_GET['result_id']) ? (int)$_GET['result_id'] : 0;

        if (!$resultId) {
            jsonError('result_id required');
        }

        $stmt = $pdo->prepare("
            SELECT n.note_id, n.result_id, n.action_id, n.description, n.modified,
                   n.created_by, n.created_at,
                   a.description as action_name,
                   CONCAT(u.last_name, ' ', u.first_name) as created_by_name
            FROM notes n
            JOIN actions a ON a.action_id = n.action_id
            LEFT JOIN users u ON u.user_id = n.created_by
            WHERE n.result_id = ? AND n.status = 1
            ORDER BY n.created_at DESC
        ");
        $stmt->execute([$resultId]);
        $notes = $stmt->fetchAll(PDO::FETCH_ASSOC);

        jsonResponse(['notes' => $notes]);

    } else {
        // POST - Create new note
        if (!isLoggedIn()) {
            jsonError('Login required', 401);
        }

        // Get JSON body
        $input = json_decode(file_get_contents('php://input'), true);

        $resultId = isset($input['result_id']) ? (int)$input['result_id'] : 0;
        $actionId = isset($input['action_id']) ? (int)$input['action_id'] : 0;
        $description = isset($input['description']) ? trim($input['description']) : '';

        if (!$resultId || !$actionId) {
            jsonError('result_id and action_id required');
        }

        if (empty($description)) {
            jsonError('description required');
        }

        if (strlen($description) > 200) {
            jsonError('description max 200 characters');
        }

        $currentUser = getCurrentUser();

        $stmt = $pdo->prepare("
            INSERT INTO notes (result_id, action_id, description, modified, status, created_by, created_at)
            VALUES (?, ?, ?, CURDATE(), 1, ?, NOW())
        ");
        $stmt->execute([$resultId, $actionId, $description, $currentUser['user_id']]);

        $noteId = $pdo->lastInsertId();

        jsonResponse([
            'success' => true,
            'note_id' => $noteId,
            'message' => 'Nota salvata'
        ]);
    }

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
