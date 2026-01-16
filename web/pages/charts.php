<?php
/**
 * Charts - Levey-Jennings QC Charts
 *
 * Shows QC charts for selected workstation and tests.
 * No authentication required for viewing.
 */

$pageTitle = 'Grafici QC - Biovarase';
$pageCSS = 'charts.css';
$pageJS = ['chart.min.js', 'chartjs-plugin-annotation.min.js', 'charts.js'];

require_once __DIR__ . '/../includes/header.php';
?>

    <header class="header">
        <div class="header-left">
            <a href="/biovarase/dashboard?lab_id=<?= htmlspecialchars($_GET['lab_id'] ?? '') ?>" class="back-link" id="backLink">&larr; Dashboard</a>
            <h1 id="pageTitle">Grafici QC</h1>
        </div>
        <div class="header-controls">
            <div>
                <label for="daysSelect">Periodo:</label>
                <select id="daysSelect">
                    <option value="30">30 giorni</option>
                    <option value="60" selected>60 giorni</option>
                    <option value="90">90 giorni</option>
                    <option value="180">180 giorni</option>
                </select>
            </div>
            <div class="date-range">
                <label>oppure</label>
                <input type="date" id="dateFrom" title="Data inizio">
                <span>-</span>
                <input type="date" id="dateTo" title="Data fine">
                <button class="btn-clear" id="clearDates" title="Cancella date">&times;</button>
            </div>
            <div>
                <label for="limitSelect">Max:</label>
                <select id="limitSelect">
                    <option value="50">50</option>
                    <option value="100" selected>100</option>
                    <option value="200">200</option>
                </select>
            </div>
            <button class="btn btn-primary" id="refreshBtn">Aggiorna</button>
        </div>
    </header>

    <main class="charts-layout">
        <!-- Test list sidebar -->
        <aside class="tests-sidebar">
            <h3>Test</h3>
            <div class="tests-list" id="testsList">
                <div class="loading">Caricamento...</div>
            </div>
        </aside>

        <!-- Charts area -->
        <section class="charts-area" id="chartsArea">
            <div class="no-selection">
                <p>Seleziona un test dalla lista per visualizzare i grafici</p>
            </div>
        </section>
    </main>

    <script>
        // Pass login status and permissions to JavaScript
        window.USER_LOGGED_IN = <?= isLoggedIn() ? 'true' : 'false' ?>;
        window.USER_CAN_MODIFY = <?= canModifyData() ? 'true' : 'false' ?>;
    </script>
<?php require_once __DIR__ . '/../includes/footer.php'; ?>
