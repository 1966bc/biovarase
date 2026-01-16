<?php
/**
 * Dashboard - Workstations QC Overview
 *
 * Public page showing workstation QC status.
 * No authentication required for viewing.
 */

$pageJS = ['chart.min.js', 'chartjs-plugin-annotation.min.js', 'dashboard.js'];

require_once __DIR__ . '/../includes/header.php';

$pageTitle = t('Workstations') . ' - Biovarase';
?>

    <header class="header">
        <h1><?= t('Workstations') ?></h1>
        <div class="header-controls">
            <div>
                <label for="daysSelect"><?= t('Period') ?>:</label>
                <select id="daysSelect">
                    <option value="1" selected><?= t('Today') ?></option>
                    <option value="7"><?= t('7 days') ?></option>
                    <option value="30"><?= t('30 days') ?></option>
                    <option value="60"><?= t('60 days') ?></option>
                </select>
            </div>
            <div class="date-range">
                <label><?= t('or') ?></label>
                <input type="date" id="dateFrom" title="<?= t('Start date') ?>">
                <span>-</span>
                <input type="date" id="dateTo" title="<?= t('End date') ?>">
                <button class="btn-clear" id="clearDates" title="<?= t('Clear dates') ?>">&times;</button>
            </div>
            <div class="date-display" id="dateDisplay"></div>
            <div>
                <label for="autoRefresh"><?= t('Auto-refresh') ?>:</label>
                <select id="autoRefresh">
                    <option value="0"><?= t('Disabled') ?></option>
                    <option value="30"><?= t('30 seconds') ?></option>
                    <option value="60" selected><?= t('1 minute') ?></option>
                    <option value="120"><?= t('2 minutes') ?></option>
                    <option value="300"><?= t('5 minutes') ?></option>
                </select>
            </div>
            <button class="btn btn-primary" id="refreshBtn"><?= t('Refresh') ?></button>
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
