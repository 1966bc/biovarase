<?php
/**
 * API: Get assays assigned to a workstation
 *
 * GET /api/workstation_assays.php?workstation_id=X
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);

if (!isset($_GET['workstation_id']) || !is_numeric($_GET['workstation_id'])) {
    jsonError('workstation_id required');
}

$workstationId = (int)$_GET['workstation_id'];

try {
    $pdo = getDBConnection();

    $stmt = $pdo->prepare("
        SELECT
            a.assay_id,
            t.description as test_name,
            m.description as method_name,
            wtm.external_code
        FROM workstation_test_methods wtm
        JOIN assays a ON wtm.test_method_id = a.assay_id
        JOIN tests t ON a.test_id = t.test_id
        JOIN methods m ON a.method_id = m.method_id
        WHERE wtm.workstation_id = ?
          AND a.status = 1
        ORDER BY t.description, m.description
    ");
    $stmt->execute([$workstationId]);
    $assays = $stmt->fetchAll(PDO::FETCH_ASSOC);

    jsonResponse(['assays' => $assays]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
