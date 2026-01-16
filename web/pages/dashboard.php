<?php
/**
 * Dashboard - TSLB QC Overview
 *
 * Public page showing workstation QC status.
 * No authentication required for viewing.
 */

$pageTitle = 'TSLB Dashboard - Biovarase';
$pageJS = ['chart.min.js', 'chartjs-plugin-annotation.min.js', 'dashboard.js'];

require_once __DIR__ . '/../includes/header.php';
?>

    <header class="header">
        <h1>TSLB Dashboard</h1>
        <div class="header-controls">
            <div>
                <label for="daysSelect">Periodo:</label>
                <select id="daysSelect">
                    <option value="1" selected>Oggi</option>
                    <option value="7">7 giorni</option>
                    <option value="30">30 giorni</option>
                    <option value="60">60 giorni</option>
                </select>
            </div>
            <div class="date-range">
                <label>oppure</label>
                <input type="date" id="dateFrom" title="Data inizio">
                <span>-</span>
                <input type="date" id="dateTo" title="Data fine">
                <button class="btn-clear" id="clearDates" title="Cancella date">&times;</button>
            </div>
            <div class="date-display" id="dateDisplay"></div>
            <div>
                <label for="autoRefresh">Auto-refresh:</label>
                <select id="autoRefresh">
                    <option value="0">Disattivato</option>
                    <option value="30">30 secondi</option>
                    <option value="60" selected>1 minuto</option>
                    <option value="120">2 minuti</option>
                    <option value="300">5 minuti</option>
                </select>
            </div>
            <button class="btn btn-primary" id="refreshBtn">Aggiorna</button>
            <span class="status-time" id="lastRefresh"></span>
        </div>
    </header>

    <main>
        <div class="workstations-grid" id="workstationsGrid">
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>Caricamento...</p>
            </div>
        </div>
    </main>

    <!-- Workstation Detail Modal -->
    <div class="modal-overlay" id="detailModal">
        <div class="modal">
            <div class="modal-header">
                <h2 id="modalTitle">Dettaglio Workstation</h2>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <!-- Test Availability Modal -->
    <div class="modal-overlay" id="availabilityModal">
        <div class="modal">
            <div class="modal-header">
                <h2 id="availabilityTitle">Disponibilità Test</h2>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body" id="availabilityBody"></div>
        </div>
    </div>

    <!-- Levey-Jennings Chart Modal -->
    <div class="modal-overlay" id="chartModal">
        <div class="modal modal-large">
            <div class="modal-header">
                <h2 id="chartTitle">Levey-Jennings</h2>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body" id="chartBody">
                <div class="chart-info" id="chartInfo"></div>
                <div class="chart-container">
                    <canvas id="ljChart"></canvas>
                </div>
                <div class="chart-stats" id="chartStats"></div>
            </div>
        </div>
    </div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
