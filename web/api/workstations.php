<?php
/**
 * API: Get workstations status for TSLB Dashboard
 *
 * Returns all workstations for a lab with QC status summary.
 *
 * GET /api/workstations.php?lab_id=2002&date=2026-01-15
 *
 * Multi-tenant: Requires lab_id parameter.
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);
$labId = requireLabId();

// Date range: custom dates take priority over days
if (isset($_GET['date_from']) && isset($_GET['date_to'])) {
    $dateFrom = $_GET['date_from'];
    $dateTo = $_GET['date_to'];
} else {
    $days = isset($_GET['days']) ? min((int)$_GET['days'], 60) : 1;
    $dateFrom = date('Y-m-d', strtotime("-" . ($days - 1) . " days"));
    $dateTo = date('Y-m-d'); // today
}

try {
    $pdo = getDBConnection();

    // Get all workstations for this lab
    // Lab -> Sections -> Workstations
    // workstations.org_id points to section
    // We need sections that belong to this lab
    $sql = "
        SELECT
            w.workstation_id,
            w.description AS workstation_name,
            w.device_id,
            e.description AS equipment_name,
            sec.description AS section_name,
            sec.org_id AS section_id
        FROM workstations w
        JOIN organizations sec ON w.org_id = sec.org_id
        JOIN organizations lab ON sec.parent_id = lab.org_id
        JOIN equipments e ON w.equipment_id = e.equipment_id
        WHERE lab.org_id = :lab_id
          AND lab.org_type = 'lab'
          AND sec.org_type = 'section'
          AND w.status = 1
        ORDER BY sec.description, w.description
    ";

    $stmt = $pdo->prepare($sql);
    $stmt->execute(['lab_id' => $labId]);
    $workstations = $stmt->fetchAll();

    if (empty($workstations)) {
        jsonResponse([
            'date_from' => $dateFrom,
            'date_to' => $dateTo,
            'lab_id' => $labId,
            'workstations' => [],
            'message' => 'No workstations found for this lab'
        ]);
    }

    // For each workstation, get QC results summary for the date range
    $sqlResults = "
        SELECT
            r.workstation_id,
            COUNT(*) AS total,
            SUM(CASE
                WHEN b.sd > 0 AND ABS((r.result - b.target) / b.sd) >= 3 THEN 1
                ELSE 0
            END) AS violations,
            SUM(CASE
                WHEN b.sd > 0 AND ABS((r.result - b.target) / b.sd) >= 2
                     AND ABS((r.result - b.target) / b.sd) < 3 THEN 1
                ELSE 0
            END) AS warnings,
            MAX(r.received) AS last_result
        FROM results r
        JOIN batches b ON r.batch_id = b.batch_id
        WHERE r.org_id = :lab_id
          AND DATE(r.received) >= :date_from
          AND DATE(r.received) <= :date_to
          AND r.status = 1
          AND r.is_delete = 0
        GROUP BY r.workstation_id
    ";

    $stmtResults = $pdo->prepare($sqlResults);
    $stmtResults->execute(['lab_id' => $labId, 'date_from' => $dateFrom, 'date_to' => $dateTo]);
    $resultsMap = [];
    while ($row = $stmtResults->fetch()) {
        $resultsMap[$row['workstation_id']] = $row;
    }

    // Build response
    $response = [];
    foreach ($workstations as $ws) {
        $wsId = $ws['workstation_id'];
        $stats = $resultsMap[$wsId] ?? null;

        $total = $stats ? (int)$stats['total'] : 0;
        $violations = $stats ? (int)$stats['violations'] : 0;
        $warnings = $stats ? (int)$stats['warnings'] : 0;
        $ok = $total - $violations - $warnings;

        // Determine status
        if ($total === 0) {
            $status = 'gray';  // No data
        } elseif ($violations > 0) {
            $status = 'red';   // Has violations
        } elseif ($warnings > 0) {
            $status = 'yellow'; // Has warnings
        } else {
            $status = 'green';  // All OK
        }

        $response[] = [
            'workstation_id' => (int)$wsId,
            'workstation_name' => $ws['workstation_name'],
            'device_id' => $ws['device_id'],
            'equipment' => $ws['equipment_name'],
            'section' => $ws['section_name'],
            'total' => $total,
            'ok' => $ok,
            'warnings' => $warnings,
            'violations' => $violations,
            'status' => $status,
            'last_result' => $stats['last_result'] ?? null
        ];
    }

    jsonResponse([
        'date_from' => $dateFrom,
        'date_to' => $dateTo,
        'lab_id' => $labId,
        'workstations' => $response
    ]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
