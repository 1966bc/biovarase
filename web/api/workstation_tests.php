<?php
/**
 * API: Get tests for a workstation
 *
 * Returns all tests configured on a workstation (via batches).
 *
 * GET /api/workstation_tests.php?workstation_id=1&lab_id=2002
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);
$labId = requireLabId();

if (!isset($_GET['workstation_id']) || !is_numeric($_GET['workstation_id'])) {
    jsonError('workstation_id required');
}
$workstationId = (int)$_GET['workstation_id'];

// Date range for QC status calculation
if (isset($_GET['date_from']) && isset($_GET['date_to'])) {
    $dateFrom = $_GET['date_from'];
    $dateTo = $_GET['date_to'];
} else {
    $days = isset($_GET['days']) ? min((int)$_GET['days'], 180) : 60;
    $dateFrom = date('Y-m-d', strtotime("-" . ($days - 1) . " days"));
    $dateTo = date('Y-m-d');
}

try {
    $pdo = getDBConnection();

    // Get workstation info
    $sqlWs = "
        SELECT w.description AS workstation_name, e.description AS equipment
        FROM workstations w
        JOIN equipments e ON w.equipment_id = e.equipment_id
        WHERE w.workstation_id = :ws_id AND w.status = 1
    ";
    $stmtWs = $pdo->prepare($sqlWs);
    $stmtWs->execute(['ws_id' => $workstationId]);
    $workstation = $stmtWs->fetch();

    if (!$workstation) {
        jsonError('Workstation not found', 404);
    }

    // Get all tests on this workstation (distinct tests from active batches)
    $sql = "
        SELECT DISTINCT
            t.test_id,
            t.description AS test_name,
            tm.test_method_id,
            m.description AS method_name,
            u.description AS unit,
            COUNT(DISTINCT b.batch_id) AS control_count
        FROM batches b
        JOIN test_methods tm ON b.test_method_id = tm.test_method_id
        JOIN tests t ON tm.test_id = t.test_id
        JOIN methods m ON tm.method_id = m.method_id
        JOIN units u ON tm.unit_id = u.unit_id
        WHERE b.workstation_id = :ws_id
          AND b.org_id = :lab_id
          AND b.status = 1
          AND t.status = 1
          AND tm.status = 1
        GROUP BY t.test_id, t.description, tm.test_method_id, m.description, u.description
        ORDER BY t.description
    ";

    $stmt = $pdo->prepare($sql);
    $stmt->execute(['ws_id' => $workstationId, 'lab_id' => $labId]);
    $tests = $stmt->fetchAll();

    // Get QC status for each test in the date range
    $sqlStatus = "
        SELECT
            b.test_method_id,
            SUM(CASE WHEN b.sd > 0 AND ABS((r.result - b.target) / b.sd) >= 3 THEN 1 ELSE 0 END) AS violations,
            SUM(CASE WHEN b.sd > 0 AND ABS((r.result - b.target) / b.sd) >= 2 AND ABS((r.result - b.target) / b.sd) < 3 THEN 1 ELSE 0 END) AS warnings
        FROM results r
        JOIN batches b ON r.batch_id = b.batch_id
        WHERE r.workstation_id = ?
          AND r.org_id = ?
          AND DATE(r.received) >= ?
          AND DATE(r.received) <= ?
          AND r.status = 1
          AND r.is_delete = 0
        GROUP BY b.test_method_id
    ";
    $stmtStatus = $pdo->prepare($sqlStatus);
    $stmtStatus->execute([$workstationId, $labId, $dateFrom, $dateTo]);
    $statusMap = [];
    while ($row = $stmtStatus->fetch()) {
        $statusMap[$row['test_method_id']] = [
            'violations' => (int)$row['violations'],
            'warnings' => (int)$row['warnings']
        ];
    }

    jsonResponse([
        'workstation' => [
            'id' => $workstationId,
            'name' => $workstation['workstation_name'],
            'equipment' => $workstation['equipment']
        ],
        'tests' => array_map(function($t) use ($statusMap) {
            $tmId = (int)$t['test_method_id'];
            $status = $statusMap[$tmId] ?? ['violations' => 0, 'warnings' => 0];

            // Determine status color
            if ($status['violations'] > 0) {
                $qcStatus = 'red';
            } elseif ($status['warnings'] > 0) {
                $qcStatus = 'yellow';
            } else {
                $qcStatus = 'green';
            }

            return [
                'test_id' => (int)$t['test_id'],
                'test_method_id' => $tmId,
                'name' => $t['test_name'],
                'method' => $t['method_name'],
                'unit' => $t['unit'],
                'control_count' => (int)$t['control_count'],
                'violations' => $status['violations'],
                'warnings' => $status['warnings'],
                'status' => $qcStatus
            ];
        }, $tests)
    ]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
