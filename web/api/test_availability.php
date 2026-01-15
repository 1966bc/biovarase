<?php
/**
 * API: Get test availability across workstations
 *
 * Shows where a specific test can be run and its current QC status.
 * Useful when a test fails on one workstation - shows alternatives.
 *
 * GET /api/test_availability.php?test_method_id=5&lab_id=2002&date=2026-01-15
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);
$labId = requireLabId();
$date = getDateParam();

// Test method ID is required
if (!isset($_GET['test_method_id']) || !is_numeric($_GET['test_method_id'])) {
    jsonError('test_method_id required');
}
$testMethodId = (int)$_GET['test_method_id'];

try {
    $pdo = getDBConnection();

    // Get test info
    $sqlTest = "
        SELECT
            tm.test_method_id,
            t.description AS test_name,
            t.test_id,
            m.description AS method_name,
            u.description AS unit
        FROM test_methods tm
        JOIN tests t ON tm.test_id = t.test_id
        JOIN methods m ON tm.method_id = m.method_id
        JOIN units u ON tm.unit_id = u.unit_id
        WHERE tm.test_method_id = :tm_id
          AND t.status = 1
          AND tm.status = 1
    ";

    $stmtTest = $pdo->prepare($sqlTest);
    $stmtTest->execute(['tm_id' => $testMethodId]);
    $testInfo = $stmtTest->fetch();

    if (!$testInfo) {
        jsonError('Test method not found', 404);
    }

    // Find all workstations that have this test configured (via batches)
    // and get latest QC status for each
    $sqlAvailability = "
        SELECT
            w.workstation_id,
            w.description AS workstation_name,
            e.description AS equipment_name,
            b.batch_id,
            b.target,
            b.sd,
            b.lot_number,
            c.description AS control_name,
            r.result_id,
            r.result,
            r.received,
            CASE
                WHEN b.sd = 0 OR b.sd IS NULL OR r.result IS NULL THEN 'unknown'
                WHEN ABS((r.result - b.target) / b.sd) >= 3 THEN 'violation'
                WHEN ABS((r.result - b.target) / b.sd) >= 2 THEN 'warning'
                ELSE 'ok'
            END AS status
        FROM batches b
        JOIN workstations w ON b.workstation_id = w.workstation_id
        JOIN organizations sec ON w.org_id = sec.org_id
        JOIN organizations lab ON sec.parent_id = lab.org_id
        JOIN equipments e ON w.equipment_id = e.equipment_id
        JOIN controls c ON b.control_id = c.control_id
        LEFT JOIN (
            SELECT r1.*
            FROM results r1
            INNER JOIN (
                SELECT batch_id, workstation_id, MAX(received) AS max_received
                FROM results
                WHERE DATE(received) = :date
                  AND status = 1
                  AND is_delete = 0
                GROUP BY batch_id, workstation_id
            ) r2 ON r1.batch_id = r2.batch_id
                AND r1.workstation_id = r2.workstation_id
                AND r1.received = r2.max_received
        ) r ON b.batch_id = r.batch_id AND r.workstation_id = w.workstation_id
        WHERE b.test_method_id = :tm_id
          AND lab.org_id = :lab_id
          AND b.status = 1
          AND w.status = 1
        ORDER BY
            CASE
                WHEN r.result IS NULL THEN 2
                WHEN ABS((r.result - b.target) / b.sd) >= 3 THEN 1
                ELSE 0
            END,
            w.description
    ";

    $stmtAvail = $pdo->prepare($sqlAvailability);
    $stmtAvail->execute([
        'tm_id' => $testMethodId,
        'lab_id' => $labId,
        'date' => $date
    ]);
    $availability = $stmtAvail->fetchAll();

    // Group by workstation (may have multiple controls)
    $workstationsMap = [];
    foreach ($availability as $row) {
        $wsId = $row['workstation_id'];
        if (!isset($workstationsMap[$wsId])) {
            $workstationsMap[$wsId] = [
                'workstation_id' => (int)$wsId,
                'workstation_name' => $row['workstation_name'],
                'equipment' => $row['equipment_name'],
                'status' => 'ok',  // Will be updated
                'controls' => []
            ];
        }

        // Add control info
        $controlStatus = $row['status'];
        $workstationsMap[$wsId]['controls'][] = [
            'control' => $row['control_name'],
            'lot_number' => $row['lot_number'],
            'value' => $row['result'] !== null ? (float)$row['result'] : null,
            'target' => (float)$row['target'],
            'sd' => (float)$row['sd'],
            'status' => $controlStatus,
            'received' => $row['received']
        ];

        // Update workstation status (worst case wins)
        $currentStatus = $workstationsMap[$wsId]['status'];
        if ($controlStatus === 'violation') {
            $workstationsMap[$wsId]['status'] = 'violation';
        } elseif ($controlStatus === 'warning' && $currentStatus !== 'violation') {
            $workstationsMap[$wsId]['status'] = 'warning';
        } elseif ($controlStatus === 'unknown' && $currentStatus === 'ok') {
            $workstationsMap[$wsId]['status'] = 'unknown';
        }
    }

    // Count available workstations
    $available = array_filter($workstationsMap, fn($ws) => $ws['status'] === 'ok');

    jsonResponse([
        'date' => $date,
        'test' => [
            'test_method_id' => (int)$testInfo['test_method_id'],
            'name' => $testInfo['test_name'],
            'method' => $testInfo['method_name'],
            'unit' => $testInfo['unit']
        ],
        'summary' => [
            'total_workstations' => count($workstationsMap),
            'available' => count($available),
            'with_problems' => count($workstationsMap) - count($available)
        ],
        'workstations' => array_values($workstationsMap)
    ]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
