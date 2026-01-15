<?php
/**
 * API: Get result series for Levey-Jennings chart
 *
 * Returns historical QC results for a specific batch.
 *
 * GET /api/series.php?batch_id=123&lab_id=2002&limit=50
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);
$labId = requireLabId();

// Batch ID is required
if (!isset($_GET['batch_id']) || !is_numeric($_GET['batch_id'])) {
    jsonError('batch_id required');
}
$batchId = (int)$_GET['batch_id'];

// Optional limit (default 50, max 100)
$limit = isset($_GET['limit']) ? min((int)$_GET['limit'], 100) : 50;

try {
    $pdo = getDBConnection();

    // Get batch info (target, SD, test name, etc.)
    $sqlBatch = "
        SELECT
            b.batch_id,
            b.target,
            b.sd,
            b.lot_number,
            b.description AS batch_description,
            t.description AS test_name,
            c.description AS control_name,
            u.description AS unit,
            w.description AS workstation_name
        FROM batches b
        JOIN test_methods tm ON b.test_method_id = tm.test_method_id
        JOIN tests t ON tm.test_id = t.test_id
        JOIN controls c ON b.control_id = c.control_id
        JOIN units u ON tm.unit_id = u.unit_id
        JOIN workstations w ON b.workstation_id = w.workstation_id
        WHERE b.batch_id = :batch_id
          AND b.org_id = :lab_id
    ";

    $stmtBatch = $pdo->prepare($sqlBatch);
    $stmtBatch->execute(['batch_id' => $batchId, 'lab_id' => $labId]);
    $batch = $stmtBatch->fetch();

    if (!$batch) {
        jsonError('Batch not found or not accessible', 404);
    }

    // Get results series (most recent first, then reverse for chart)
    $sqlResults = "
        SELECT
            r.result_id,
            r.result,
            r.received,
            r.validated
        FROM results r
        WHERE r.batch_id = :batch_id
          AND r.org_id = :lab_id
          AND r.status = 1
          AND r.is_delete = 0
        ORDER BY r.received DESC
        LIMIT :limit
    ";

    $stmtResults = $pdo->prepare($sqlResults);
    $stmtResults->bindValue(':batch_id', $batchId, PDO::PARAM_INT);
    $stmtResults->bindValue(':lab_id', $labId, PDO::PARAM_INT);
    $stmtResults->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmtResults->execute();
    $results = $stmtResults->fetchAll();

    // Calculate zscore in PHP
    $target = (float)$batch['target'];
    $sd = (float)$batch['sd'];
    foreach ($results as &$r) {
        if ($sd > 0) {
            $r['zscore'] = round(($r['result'] - $target) / $sd, 2);
        } else {
            $r['zscore'] = null;
        }
    }
    unset($r); // Break reference

    // Reverse to get chronological order (oldest first)
    $results = array_reverse($results);

    // Calculate statistics
    $values = array_column($results, 'result');
    $count = count($values);
    $mean = $count > 0 ? array_sum($values) / $count : 0;
    $variance = 0;
    if ($count > 1) {
        foreach ($values as $v) {
            $variance += pow($v - $mean, 2);
        }
        $variance /= ($count - 1);
    }
    $calculatedSd = sqrt($variance);
    $cv = $mean > 0 ? ($calculatedSd / $mean) * 100 : 0;

    jsonResponse([
        'batch' => [
            'batch_id' => (int)$batch['batch_id'],
            'test' => $batch['test_name'],
            'control' => $batch['control_name'],
            'lot_number' => $batch['lot_number'],
            'workstation' => $batch['workstation_name'],
            'unit' => $batch['unit'],
            'target' => (float)$batch['target'],
            'sd' => (float)$batch['sd']
        ],
        'statistics' => [
            'count' => $count,
            'mean' => round($mean, 4),
            'sd' => round($calculatedSd, 4),
            'cv' => round($cv, 2)
        ],
        'series' => array_map(function($r) {
            return [
                'result_id' => (int)$r['result_id'],
                'value' => (float)$r['result'],
                'zscore' => $r['zscore'] !== null ? (float)$r['zscore'] : null,
                'received' => $r['received'],
                'validated' => (bool)$r['validated']
            ];
        }, $results)
    ]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}
