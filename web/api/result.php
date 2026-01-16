<?php
/**
 * Result API - Get/Update/Void a single result
 *
 * GET: Get result details
 * PUT: Update result value (requires login + permission)
 * PATCH: Void result (set status=0) (requires login + permission)
 *
 * Permission logic (for PUT/PATCH):
 * - Role 0-3 (Admin hierarchy): can modify any result in their org scope
 * - Role 4-5 (Superuser/Technician): can modify if:
 *   a) created_by = current user (they created it), OR
 *   b) created_by IS NULL (instrument data, team can modify)
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/../engine/auth.php';

requireMethod(['GET', 'PUT', 'POST']);

try {
    $pdo = getDBConnection();

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        // Get result details
        $resultId = isset($_GET['result_id']) ? (int)$_GET['result_id'] : 0;

        if (!$resultId) {
            jsonError('result_id required');
        }

        $stmt = $pdo->prepare("
            SELECT r.result_id, r.result, r.received, r.status, r.is_delete,
                   r.validated, r.validated_by, r.validated_at,
                   r.workstation_id, r.batch_id, r.org_id, r.created_by,
                   b.description as batch_description,
                   w.description as workstation_name,
                   t.description as test_name,
                   CONCAT(u.last_name, ' ', u.first_name) as created_by_name
            FROM results r
            JOIN batches b ON b.batch_id = r.batch_id
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            JOIN tests t ON t.test_id = tm.test_id
            JOIN workstations w ON w.workstation_id = r.workstation_id
            LEFT JOIN users u ON u.user_id = r.created_by
            WHERE r.result_id = ?
        ");
        $stmt->execute([$resultId]);
        $result = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$result) {
            jsonError('Result not found', 404);
        }

        // Check if current user can modify this result (for frontend)
        $canModify = false;
        $canVoid = false;
        if (isLoggedIn()) {
            $canModify = canModifyResult($result);
            $canVoid = canVoidResult($result);
        }

        $result['can_modify'] = $canModify;
        $result['can_void'] = $canVoid;

        jsonResponse(['result' => $result]);

    } elseif ($_SERVER['REQUEST_METHOD'] === 'PUT') {
        // PUT - Update result value
        if (!isLoggedIn()) {
            jsonError('Login required', 401);
        }

        // Get JSON body
        $input = json_decode(file_get_contents('php://input'), true);

        $resultId = isset($input['result_id']) ? (int)$input['result_id'] : 0;
        $newValue = isset($input['value']) ? $input['value'] : null;

        if (!$resultId) {
            jsonError('result_id required');
        }

        if ($newValue === null || !is_numeric($newValue)) {
            jsonError('Valid numeric value required');
        }

        $newValue = (float)$newValue;

        // Verify result exists and get current data for permission check and audit
        $stmt = $pdo->prepare("
            SELECT r.*, b.org_id as batch_org_id, tm.org_id as section_org_id
            FROM results r
            JOIN batches b ON b.batch_id = r.batch_id
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            WHERE r.result_id = ?
        ");
        $stmt->execute([$resultId]);
        $current = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$current) {
            jsonError('Result not found', 404);
        }

        // Check org_id permission (user can only modify their lab's data)
        $currentUser = getCurrentUser();
        if ($currentUser['org_id'] && $current['org_id'] != $currentUser['org_id']) {
            jsonError('Permission denied - wrong organization', 403);
        }

        // Check specific result permission
        if (!canModifyResult($current)) {
            jsonError('Permission denied - cannot modify this result', 403);
        }

        // Begin transaction
        $pdo->beginTransaction();

        try {
            // Insert audit record BEFORE update
            $stmt = $pdo->prepare("
                INSERT INTO audit_results (
                    operation, result_id, org_id, batch_id, run_number,
                    workstation_id, reagent_lot, result, received, status,
                    validated, validated_by, validated_at,
                    tech_validated, tech_validated_by, tech_validated_at,
                    operator_code, is_delete, created_by, log_id, log_ip
                ) VALUES (
                    'UPDATE', ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            ");
            $stmt->execute([
                $resultId, $current['org_id'], $current['batch_id'], $current['run_number'],
                $current['workstation_id'], $current['reagent_lot'], $current['result'],
                $current['received'], $current['status'],
                $current['validated'], $current['validated_by'], $current['validated_at'],
                $current['tech_validated'], $current['tech_validated_by'], $current['tech_validated_at'],
                $current['operator_code'], $current['is_delete'], $current['created_by'],
                $currentUser['user_id'], $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1'
            ]);

            // Update result
            $stmt = $pdo->prepare("
                UPDATE results
                SET result = ?, log_time = NOW(), log_id = ?, log_ip = ?
                WHERE result_id = ?
            ");
            $stmt->execute([
                $newValue,
                $currentUser['user_id'],
                $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1',
                $resultId
            ]);

            $pdo->commit();

            jsonResponse([
                'success' => true,
                'message' => 'Risultato aggiornato',
                'old_value' => (float)$current['result'],
                'new_value' => $newValue
            ]);

        } catch (Exception $e) {
            $pdo->rollBack();
            throw $e;
        }

    } else {
        // POST - Void result (set status=0)
        // Use POST with action=void since PATCH may be blocked by Apache
        if (!isLoggedIn()) {
            jsonError('Login required', 401);
        }

        // Get JSON body
        $input = json_decode(file_get_contents('php://input'), true);

        // Check action
        $action = isset($input['action']) ? $input['action'] : '';
        if ($action !== 'void') {
            jsonError('Invalid action. Use action=void', 400);
        }

        $resultId = isset($input['result_id']) ? (int)$input['result_id'] : 0;

        if (!$resultId) {
            jsonError('result_id required');
        }

        // Verify result exists and get current data
        $stmt = $pdo->prepare("
            SELECT r.*, b.org_id as batch_org_id, tm.org_id as section_org_id
            FROM results r
            JOIN batches b ON b.batch_id = r.batch_id
            JOIN test_methods tm ON tm.test_method_id = b.test_method_id
            WHERE r.result_id = ?
        ");
        $stmt->execute([$resultId]);
        $current = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$current) {
            jsonError('Result not found', 404);
        }

        // Check if already voided
        if ($current['status'] == 0) {
            jsonError('Result already voided', 400);
        }

        // Check org_id permission
        $currentUser = getCurrentUser();
        if ($currentUser['org_id'] && $current['org_id'] != $currentUser['org_id']) {
            jsonError('Permission denied - wrong organization', 403);
        }

        // Check specific result permission
        if (!canVoidResult($current)) {
            jsonError('Permission denied - cannot void this result', 403);
        }

        // Begin transaction
        $pdo->beginTransaction();

        try {
            // Insert audit record BEFORE void
            $stmt = $pdo->prepare("
                INSERT INTO audit_results (
                    operation, result_id, org_id, batch_id, run_number,
                    workstation_id, reagent_lot, result, received, status,
                    validated, validated_by, validated_at,
                    tech_validated, tech_validated_by, tech_validated_at,
                    operator_code, is_delete, created_by, log_id, log_ip
                ) VALUES (
                    'VOID', ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            ");
            $stmt->execute([
                $resultId, $current['org_id'], $current['batch_id'], $current['run_number'],
                $current['workstation_id'], $current['reagent_lot'], $current['result'],
                $current['received'], $current['status'],
                $current['validated'], $current['validated_by'], $current['validated_at'],
                $current['tech_validated'], $current['tech_validated_by'], $current['tech_validated_at'],
                $current['operator_code'], $current['is_delete'], $current['created_by'],
                $currentUser['user_id'], $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1'
            ]);

            // Void result (set status=0)
            $stmt = $pdo->prepare("
                UPDATE results
                SET status = 0, log_time = NOW(), log_id = ?, log_ip = ?
                WHERE result_id = ?
            ");
            $stmt->execute([
                $currentUser['user_id'],
                $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1',
                $resultId
            ]);

            $pdo->commit();

            jsonResponse([
                'success' => true,
                'message' => 'Risultato annullato',
                'result_id' => $resultId
            ]);

        } catch (Exception $e) {
            $pdo->rollBack();
            throw $e;
        }
    }

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error: ' . $e->getMessage(), 500);
}
