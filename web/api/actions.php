<?php
/**
 * Actions API - Get available corrective actions
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);

try {
    $pdo = getDBConnection();

    $stmt = $pdo->prepare("
        SELECT action_id, code, description
        FROM actions
        WHERE status = 1
        ORDER BY description
    ");
    $stmt->execute();
    $actions = $stmt->fetchAll(PDO::FETCH_ASSOC);

    jsonResponse(['actions' => $actions]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
