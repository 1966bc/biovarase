<?php
/**
 * Lab Selector Page
 * App Admin selects which lab to work with
 */

$pageTitle = 'Seleziona Laboratorio - Biovarase';

require_once __DIR__ . '/../engine/auth.php';
require_once __DIR__ . '/../api/config.php';

// Must be logged in
requireAuth();

// Only App Admin needs this page
if (!isAppAdmin()) {
    header('Location: /biovarase/dashboard');
    exit;
}

// Handle POST - lab selection
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $labId = isset($_POST['lab_id']) ? intval($_POST['lab_id']) : 0;

    if ($labId > 0) {
        try {
            $pdo = getDbConnection();
            // Get lab and site info
            $stmt = $pdo->prepare("
                SELECT lab.org_id, lab.description as lab_name, site.description as site_name
                FROM organizations lab
                LEFT JOIN organizations site ON lab.parent_id = site.org_id AND site.org_type = 'site'
                WHERE lab.org_id = ? AND lab.org_type = 'lab' AND lab.status = 1
            ");
            $stmt->execute([$labId]);
            $lab = $stmt->fetch(PDO::FETCH_ASSOC);

            if ($lab) {
                setWorkingLabWithSite($lab['org_id'], $lab['lab_name'], $lab['site_name']);
                header('Location: /biovarase/dashboard');
                exit;
            }
        } catch (PDOException $e) {
            $error = 'Errore nel caricamento del laboratorio';
        }
    }
    $error = 'Seleziona un laboratorio valido';
}

// Fetch labs
try {
    $pdo = getDbConnection();
    $stmt = $pdo->query("
        SELECT o.org_id, o.description, p.description as site_name
        FROM organizations o
        LEFT JOIN organizations p ON o.parent_id = p.org_id
        WHERE o.org_type = 'lab' AND o.status = 1
        ORDER BY p.description, o.description
    ");
    $labs = $stmt->fetchAll(PDO::FETCH_ASSOC);
} catch (PDOException $e) {
    $labs = [];
    $error = 'Errore nel caricamento dei laboratori';
}
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($pageTitle) ?></title>
    <link rel="stylesheet" href="/biovarase/css/dashboard.css">
    <style>
        body {
            background: #ecf0f1;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .selector-container {
            background: #fff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 500px;
        }
        .selector-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .selector-header h1 {
            color: #2c3e50;
            margin: 0 0 10px 0;
            font-size: 1.5rem;
        }
        .selector-header p {
            color: #7f8c8d;
            margin: 0;
        }
        .user-info {
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            text-align: center;
        }
        .user-info strong {
            color: #2c3e50;
        }
        .user-info .badge {
            background: #e74c3c;
            color: #fff;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8rem;
            margin-left: 8px;
        }
        .lab-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .lab-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }
        .lab-item:last-child {
            border-bottom: none;
        }
        .lab-item:hover {
            background: #f8f9fa;
        }
        .lab-item input[type="radio"] {
            margin-right: 15px;
            transform: scale(1.3);
        }
        .lab-item label {
            flex: 1;
            cursor: pointer;
        }
        .lab-item .lab-name {
            font-weight: 500;
            color: #2c3e50;
            display: block;
        }
        .lab-item .site-name {
            font-size: 0.85rem;
            color: #7f8c8d;
        }
        .btn-select {
            width: 100%;
            padding: 14px;
            background: #3498db;
            color: #fff;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            margin-top: 20px;
            transition: background 0.2s;
        }
        .btn-select:hover {
            background: #2980b9;
        }
        .btn-select:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
        }
        .error-message {
            background: #fee;
            color: #c0392b;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
            text-align: center;
        }
        .empty-state {
            padding: 40px;
            text-align: center;
            color: #7f8c8d;
        }
        .logout-link {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: #e74c3c;
            text-decoration: none;
        }
        .logout-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="selector-container">
        <div class="selector-header">
            <h1>Seleziona Laboratorio</h1>
            <p>Scegli su quale laboratorio vuoi lavorare</p>
        </div>

        <div class="user-info">
            <?php $user = getCurrentUser(); ?>
            <strong><?= htmlspecialchars($user['last_name'] . ' ' . ($user['first_name'] ?? '')) ?></strong>
            <span class="badge">App Admin</span>
        </div>

        <?php if (!empty($error)): ?>
        <div class="error-message">
            <?= htmlspecialchars($error) ?>
        </div>
        <?php endif; ?>

        <?php if (empty($labs)): ?>
        <div class="empty-state">
            <p>Nessun laboratorio disponibile</p>
        </div>
        <?php else: ?>
        <form method="POST" id="labForm">
            <div class="lab-list">
                <?php foreach ($labs as $lab): ?>
                <div class="lab-item" onclick="selectLab(<?= $lab['org_id'] ?>)">
                    <input type="radio" name="lab_id" id="lab_<?= $lab['org_id'] ?>" value="<?= $lab['org_id'] ?>">
                    <label for="lab_<?= $lab['org_id'] ?>">
                        <span class="lab-name"><?= htmlspecialchars($lab['description']) ?></span>
                        <?php if ($lab['site_name']): ?>
                        <span class="site-name"><?= htmlspecialchars($lab['site_name']) ?></span>
                        <?php endif; ?>
                    </label>
                </div>
                <?php endforeach; ?>
            </div>

            <button type="submit" class="btn-select" id="btnSelect" disabled>Seleziona</button>
        </form>
        <?php endif; ?>

        <a href="/biovarase/logout" class="logout-link">Esci</a>
    </div>

    <script>
    function selectLab(labId) {
        document.getElementById('lab_' + labId).checked = true;
        document.getElementById('btnSelect').disabled = false;
    }

    // Enable button when radio is selected
    document.querySelectorAll('input[name="lab_id"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            document.getElementById('btnSelect').disabled = false;
        });
    });
    </script>
</body>
</html>
