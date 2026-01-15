<?php
/**
 * API: Get detailed QC results for a single workstation
 *
 * Returns all QC results for a workstation on a given date.
 *
 * GET /api/workstation_detail.php?id=1&lab_id=2002&date=2026-01-15
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);
$labId = requireLabId();
$date = getDateParam();

// Workstation ID is required
if (!isset($_GET['id']) || !is_numeric($_GET['id'])) {
    jsonError('Workstation ID required');
}
$workstationId = (int)$_GET['id'];

try {
    $pdo = getDBConnection();

    // Get workstation info
    $sqlWs = "
        SELECT
            w.workstation_id,
            w.description AS workstation_name,
            w.device_id,
            e.description AS equipment_name,
            sec.description AS section_name
        FROM workstations w
        JOIN organizations sec ON w.org_id = sec.org_id
        JOIN organizations lab ON sec.parent_id = lab.org_id
        JOIN equipments e ON w.equipment_id = e.equipment_id
        WHERE w.workstation_id = :ws_id
          AND lab.org_id = :lab_id
          AND w.status = 1
    ";

    $stmtWs = $pdo->prepare($sqlWs);
    $stmtWs->execute(['ws_id' => $workstationId, 'lab_id' => $labId]);
    $workstation = $stmtWs->fetch();

    if (!$workstation) {
        jsonError('Workstation not found or not accessible', 404);
    }

    // Get all results for this workstation on the given date
    $sqlResults = "
        SELECT
            r.result_id,
            r.result,
            r.received,
            r.validated,
            r.run_number,
            b.batch_id,
            b.target,
            b.sd,
            b.lot_number,
            b.description AS batch_description,
            t.description AS test_name,
            tm.test_method_id,
            c.description AS control_name,
            CASE
                WHEN b.sd > 0 THEN ROUND((r.result - b.target) / b.sd, 2)
                ELSE NULL
            END AS zscore,
            CASE
                WHEN b.sd = 0 OR b.sd IS NULL THEN 'unknown'
                WHEN ABS((r.result - b.target) / b.sd) >= 3 THEN 'violation'
                WHEN ABS((r.result - b.target) / b.sd) >= 2 THEN 'warning'
                ELSE 'ok'
            END AS status
        FROM results r
        JOIN batches b ON r.batch_id = b.batch_id
        JOIN test_methods tm ON b.test_method_id = tm.test_method_id
        JOIN tests t ON tm.test_id = t.test_id
        JOIN controls c ON b.control_id = c.control_id
        WHERE r.workstation_id = :ws_id
          AND r.org_id = :lab_id
          AND DATE(r.received) = :date
          AND r.status = 1
          AND r.is_delete = 0
          AND t.status = 1
          AND tm.status = 1
        ORDER BY
            CASE
                WHEN ABS((r.result - b.target) / b.sd) >= 3 THEN 0
                WHEN ABS((r.result - b.target) / b.sd) >= 2 THEN 1
                ELSE 2
            END,
            t.description,
            r.received DESC
    ";

    $stmtResults = $pdo->prepare($sqlResults);
    $stmtResults->execute([
        'ws_id' => $workstationId,
        'lab_id' => $labId,
        'date' => $date
    ]);
    $results = $stmtResults->fetchAll();

    // Count summary
    $total = count($results);
    $violations = 0;
    $warnings = 0;
    foreach ($results as $r) {
        if ($r['status'] === 'violation') $violations++;
        elseif ($r['status'] === 'warning') $warnings++;
    }

    jsonResponse([
        'date' => $date,
        'workstation' => [
            'id' => (int)$workstation['workstation_id'],
            'name' => $workstation['workstation_name'],
            'device_id' => $workstation['device_id'],
            'equipment' => $workstation['equipment_name'],
            'section' => $workstation['section_name']
        ],
        'summary' => [
            'total' => $total,
            'ok' => $total - $violations - $warnings,
            'warnings' => $warnings,
            'violations' => $violations
        ],
        'results' => array_map(function($r) {
            return [
                'result_id' => (int)$r['result_id'],
                'test' => $r['test_name'],
                'test_method_id' => (int)$r['test_method_id'],
                'control' => $r['control_name'],
                'batch_id' => (int)$r['batch_id'],
                'lot_number' => $r['lot_number'],
                'value' => (float)$r['result'],
                'target' => (float)$r['target'],
                'sd' => (float)$r['sd'],
                'zscore' => $r['zscore'] !== null ? (float)$r['zscore'] : null,
                'status' => $r['status'],
                'received' => $r['received'],
                'validated' => (bool)$r['validated']
            ];
        }, $results)
    ]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
