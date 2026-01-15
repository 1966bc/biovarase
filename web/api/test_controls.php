<?php
/**
 * API: Get all controls for a test on a workstation
 *
 * Returns all batches (controls) for a specific test on a workstation,
 * including the result series for each and drift analysis.
 *
 * GET /api/test_controls.php?test_method_id=5&workstation_id=1&lab_id=2002&limit=30
 */

require_once __DIR__ . '/config.php';

requireMethod(['GET']);
$labId = requireLabId();

if (!isset($_GET['test_method_id']) || !is_numeric($_GET['test_method_id'])) {
    jsonError('test_method_id required');
}
if (!isset($_GET['workstation_id']) || !is_numeric($_GET['workstation_id'])) {
    jsonError('workstation_id required');
}

$testMethodId = (int)$_GET['test_method_id'];
$workstationId = (int)$_GET['workstation_id'];
$limit = isset($_GET['limit']) ? min((int)$_GET['limit'], 200) : 100;

// Date range: custom dates take priority over days
if (isset($_GET['date_from']) && isset($_GET['date_to'])) {
    $dateFrom = $_GET['date_from'];
    $dateTo = $_GET['date_to'];
} else {
    $days = isset($_GET['days']) ? min((int)$_GET['days'], 180) : 60;
    $dateFrom = date('Y-m-d', strtotime("-{$days} days"));
    $dateTo = date('Y-m-d'); // today
}

try {
    $pdo = getDBConnection();

    // Get test info
    $sqlTest = "
        SELECT
            t.description AS test_name,
            m.description AS method_name,
            u.description AS unit
        FROM test_methods tm
        JOIN tests t ON tm.test_id = t.test_id
        JOIN methods m ON tm.method_id = m.method_id
        JOIN units u ON tm.unit_id = u.unit_id
        WHERE tm.test_method_id = :tm_id
    ";
    $stmtTest = $pdo->prepare($sqlTest);
    $stmtTest->execute(['tm_id' => $testMethodId]);
    $testInfo = $stmtTest->fetch();

    if (!$testInfo) {
        jsonError('Test method not found', 404);
    }

    // Get all batches (controls) for this test on this workstation
    // Include inactive batches if they have results in the date range
    $sqlBatches = "
        SELECT
            b.batch_id,
            b.target,
            b.sd,
            b.lot_number,
            b.description AS batch_description,
            b.status AS batch_status,
            b.expiration,
            c.description AS control_name,
            c.control_id
        FROM batches b
        JOIN controls c ON b.control_id = c.control_id
        WHERE b.test_method_id = ?
          AND b.workstation_id = ?
          AND b.org_id = ?
          AND EXISTS (
              SELECT 1 FROM results r
              WHERE r.batch_id = b.batch_id
                AND r.org_id = ?
                AND DATE(r.received) >= ?
                AND DATE(r.received) <= ?
                AND r.status = 1
                AND r.is_delete = 0
          )
        ORDER BY c.description, b.lot_number
    ";

    $stmtBatches = $pdo->prepare($sqlBatches);
    $stmtBatches->execute([$testMethodId, $workstationId, $labId, $labId, $dateFrom, $dateTo]);
    $batches = $stmtBatches->fetchAll();

    if (empty($batches)) {
        jsonResponse([
            'test' => [
                'test_method_id' => $testMethodId,
                'name' => $testInfo['test_name'],
                'method' => $testInfo['method_name'],
                'unit' => $testInfo['unit']
            ],
            'controls' => []
        ]);
    }

    // For each batch, get the result series and calculate drift
    $controls = [];
    foreach ($batches as $batch) {
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
              AND DATE(r.received) >= :date_from
              AND DATE(r.received) <= :date_to
            ORDER BY r.received DESC
            LIMIT :limit
        ";

        $stmtResults = $pdo->prepare($sqlResults);
        $stmtResults->bindValue(':batch_id', $batch['batch_id'], PDO::PARAM_INT);
        $stmtResults->bindValue(':lab_id', $labId, PDO::PARAM_INT);
        $stmtResults->bindValue(':date_from', $dateFrom, PDO::PARAM_STR);
        $stmtResults->bindValue(':date_to', $dateTo, PDO::PARAM_STR);
        $stmtResults->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmtResults->execute();
        $results = $stmtResults->fetchAll();

        // Reverse for chronological order
        $results = array_reverse($results);

        // Calculate zscore for each result
        $target = (float)$batch['target'];
        $sd = (float)$batch['sd'];
        $series = [];
        foreach ($results as $r) {
            $zscore = null;
            if ($sd > 0) {
                $zscore = round(($r['result'] - $target) / $sd, 2);
            }
            $series[] = [
                'result_id' => (int)$r['result_id'],
                'value' => (float)$r['result'],
                'zscore' => $zscore,
                'received' => $r['received'],
                'validated' => (bool)$r['validated']
            ];
        }

        // Calculate statistics
        $values = array_column($series, 'value');
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

        // Drift analysis
        $drift = analyzeDrift($series, $target);

        // Get first and last result dates from series
        $firstResult = !empty($series) ? $series[0]['received'] : null;
        $lastResult = !empty($series) ? $series[count($series) - 1]['received'] : null;

        // Check if lot is expired
        $isExpired = false;
        if ($batch['expiration']) {
            $isExpired = strtotime($batch['expiration']) < strtotime('today');
        }

        $controls[] = [
            'batch_id' => (int)$batch['batch_id'],
            'control' => $batch['control_name'],
            'lot_number' => $batch['lot_number'],
            'target' => $target,
            'sd' => $sd,
            'is_active' => (bool)$batch['batch_status'],
            'is_expired' => $isExpired,
            'expiration' => $batch['expiration'],
            'first_result' => $firstResult,
            'last_result' => $lastResult,
            'statistics' => [
                'count' => $count,
                'mean' => round($mean, 4),
                'sd' => round($calculatedSd, 4),
                'cv' => round($cv, 2),
                'bias' => $target > 0 ? round((($mean - $target) / $target) * 100, 2) : 0
            ],
            'drift' => $drift,
            'series' => $series
        ];
    }

    jsonResponse([
        'test' => [
            'test_method_id' => $testMethodId,
            'name' => $testInfo['test_name'],
            'method' => $testInfo['method_name'],
            'unit' => $testInfo['unit']
        ],
        'controls' => $controls
    ]);

} catch (PDOException $e) {
    error_log("Biovarase API Error: " . $e->getMessage());
    jsonError('Database error', 500);
}

/**
 * Analyze drift/trend in the series
 *
 * Detects:
 * - Shift: N consecutive points above or below target (Westgard 10:X rule)
 * - Trend: N consecutive points going up or down
 *
 * @param array $series Result series
 * @param float $target Target value
 * @return array Drift analysis results
 */
function analyzeDrift(array $series, float $target): array {
    $drift = [
        'has_drift' => false,
        'alerts' => []
    ];

    if (count($series) < 7) {
        return $drift;
    }

    // Check for shift (consecutive points on same side of target)
    $aboveCount = 0;
    $belowCount = 0;
    $maxAbove = 0;
    $maxBelow = 0;

    foreach ($series as $point) {
        if ($point['value'] > $target) {
            $aboveCount++;
            $belowCount = 0;
            $maxAbove = max($maxAbove, $aboveCount);
        } elseif ($point['value'] < $target) {
            $belowCount++;
            $aboveCount = 0;
            $maxBelow = max($maxBelow, $belowCount);
        } else {
            $aboveCount = 0;
            $belowCount = 0;
        }
    }

    // 7+ consecutive points = warning, 10+ = Westgard violation
    if ($maxAbove >= 10 || $maxBelow >= 10) {
        $drift['has_drift'] = true;
        $side = $maxAbove >= 10 ? 'sopra' : 'sotto';
        $drift['alerts'][] = [
            'type' => 'shift',
            'severity' => 'violation',
            'message' => "10:X - " . max($maxAbove, $maxBelow) . " punti consecutivi $side il target"
        ];
    } elseif ($maxAbove >= 7 || $maxBelow >= 7) {
        $drift['has_drift'] = true;
        $side = $maxAbove >= 7 ? 'sopra' : 'sotto';
        $drift['alerts'][] = [
            'type' => 'shift',
            'severity' => 'warning',
            'message' => max($maxAbove, $maxBelow) . " punti consecutivi $side il target"
        ];
    }

    // Check for trend (consecutive increases or decreases)
    $upCount = 0;
    $downCount = 0;
    $maxUp = 0;
    $maxDown = 0;

    for ($i = 1; $i < count($series); $i++) {
        if ($series[$i]['value'] > $series[$i-1]['value']) {
            $upCount++;
            $downCount = 0;
            $maxUp = max($maxUp, $upCount);
        } elseif ($series[$i]['value'] < $series[$i-1]['value']) {
            $downCount++;
            $upCount = 0;
            $maxDown = max($maxDown, $downCount);
        } else {
            $upCount = 0;
            $downCount = 0;
        }
    }

    // 6+ consecutive increases/decreases = trend warning
    if ($maxUp >= 6 || $maxDown >= 6) {
        $drift['has_drift'] = true;
        $direction = $maxUp >= 6 ? 'crescente' : 'decrescente';
        $drift['alerts'][] = [
            'type' => 'trend',
            'severity' => 'warning',
            'message' => "Trend $direction: " . (max($maxUp, $maxDown) + 1) . " punti consecutivi"
        ];
    }

    return $drift;
}
