/**
 * Biovarase TSLB Dashboard - JavaScript
 *
 * Handles API calls, rendering, and user interactions.
 */

// Configuration
const CONFIG = {
    apiBase: '/biovarase/api',
    autoRefreshInterval: 60000, // 60 seconds, 0 to disable
    labId: null, // Set from URL or selection
};

// Chart instance (for cleanup)
let ljChartInstance = null;

// State
let autoRefreshTimer = null;
let currentWorkstations = [];

/**
 * Initialize dashboard
 */
document.addEventListener('DOMContentLoaded', () => {
    // Get lab_id from URL parameter or prompt
    const urlParams = new URLSearchParams(window.location.search);
    CONFIG.labId = urlParams.get('lab_id');

    // Set days/date range from URL or default
    const daysSelect = document.getElementById('daysSelect');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');

    const daysParam = urlParams.get('days');
    const dateFromParam = urlParams.get('date_from');
    const dateToParam = urlParams.get('date_to');

    if (dateFromParam && dateToParam) {
        dateFrom.value = dateFromParam;
        dateTo.value = dateToParam;
        daysSelect.disabled = true;
    } else if (daysParam) {
        daysSelect.value = daysParam;
    }

    // Set auto-refresh from URL or default
    const refreshSelect = document.getElementById('autoRefresh');
    const refreshParam = urlParams.get('refresh');
    if (refreshParam) {
        refreshSelect.value = refreshParam;
        CONFIG.autoRefreshInterval = parseInt(refreshParam) * 1000;
    }

    // Event listeners
    document.getElementById('refreshBtn').addEventListener('click', loadWorkstations);
    daysSelect.addEventListener('change', () => { loadWorkstations(); updateDateDisplay(); });
    dateFrom.addEventListener('change', onDateRangeChange);
    dateTo.addEventListener('change', onDateRangeChange);
    document.getElementById('clearDates').addEventListener('click', clearDateRange);
    refreshSelect.addEventListener('change', handleAutoRefreshChange);

    // Modal close handlers
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeAllModals();
        });
    });

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeAllModals);
    });

    // Keyboard handler
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAllModals();
    });

    // Initial load
    if (CONFIG.labId) {
        loadWorkstations();
        startAutoRefresh();
        updateDateDisplay();
    } else {
        showError('lab_id parameter required. Example: ?lab_id=2002');
    }
});

/**
 * Handle date range change
 */
function onDateRangeChange() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const daysSelect = document.getElementById('daysSelect');

    daysSelect.disabled = !!(dateFrom || dateTo);

    if (dateFrom && dateTo) {
        loadWorkstations();
    }
    updateDateDisplay();
}

/**
 * Update the date display in Italian format
 */
function updateDateDisplay() {
    const display = document.getElementById('dateDisplay');
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const days = document.getElementById('daysSelect').value;

    if (dateFrom && dateTo) {
        const fromDate = new Date(dateFrom).toLocaleDateString('it-IT');
        const toDate = new Date(dateTo).toLocaleDateString('it-IT');
        display.textContent = `📅 ${fromDate} - ${toDate}`;
    } else if (days === '1') {
        display.textContent = `📅 Oggi: ${new Date().toLocaleDateString('it-IT')}`;
    } else {
        const fromDate = new Date();
        fromDate.setDate(fromDate.getDate() - (days - 1));
        display.textContent = `📅 ${fromDate.toLocaleDateString('it-IT')} - ${new Date().toLocaleDateString('it-IT')}`;
    }
}

/**
 * Clear date range
 */
function clearDateRange() {
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('daysSelect').disabled = false;
    loadWorkstations();
    updateDateDisplay();
}

/**
 * Get current date parameters for API calls
 */
function getDateParams() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const days = document.getElementById('daysSelect').value;

    if (dateFrom && dateTo) {
        return { date_from: dateFrom, date_to: dateTo };
    } else {
        return { days: days };
    }
}

/**
 * Load workstations from API
 */
async function loadWorkstations() {
    const grid = document.getElementById('workstationsGrid');
    const dateParams = getDateParams();

    showLoading(grid);
    updateLastRefresh();

    // Build URL
    let url = `${CONFIG.apiBase}/workstations.php?lab_id=${CONFIG.labId}`;
    if (dateParams.date_from) {
        url += `&date_from=${dateParams.date_from}&date_to=${dateParams.date_to}`;
    } else {
        url += `&days=${dateParams.days}`;
    }

    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        currentWorkstations = data.workstations;
        renderWorkstations(data.workstations, grid);

    } catch (error) {
        console.error('Error loading workstations:', error);
        showError(`Errore caricamento dati: ${error.message}`, grid);
    }
}

/**
 * Render workstation cards
 */
function renderWorkstations(workstations, container) {
    if (!workstations || workstations.length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <p>Nessuna workstation trovata per questo laboratorio.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = workstations.map(ws => `
        <div class="workstation-card status-${ws.status}"
             onclick="openWorkstationDetail(${ws.workstation_id})"
             title="Click per dettagli">
            <div class="workstation-name">${escapeHtml(ws.workstation_name)}</div>
            <div class="workstation-equipment">${escapeHtml(ws.equipment)}</div>
            <div class="semaforo ${ws.status}">
                ${getSemaforoIcon(ws.status)}
            </div>
            <div class="workstation-stats">
                ${ws.total > 0 ? `
                    <span class="count-ok">${ws.ok}</span> /
                    <span class="count-warn">${ws.warnings}</span> /
                    <span class="count-fail">${ws.violations}</span>
                ` : 'Nessun dato'}
            </div>
            ${ws.last_result ? `
                <div class="workstation-time">
                    Ultimo: ${formatTime(ws.last_result)}
                </div>
            ` : ''}
            <button class="btn-charts" onclick="openChartsPage(${ws.workstation_id}, event)" title="Grafici Levey-Jennings">
                📈 Grafici
            </button>
        </div>
    `).join('');
}

/**
 * Get semaforo icon based on status
 */
function getSemaforoIcon(status) {
    switch (status) {
        case 'green': return '✓';
        case 'yellow': return '!';
        case 'red': return '✗';
        default: return '?';
    }
}

/**
 * Open charts page for a workstation
 */
function openChartsPage(workstationId, event) {
    event.stopPropagation(); // Prevent card click
    const dateParams = getDateParams();
    let url = `/biovarase/charts?lab_id=${CONFIG.labId}&workstation_id=${workstationId}`;
    if (dateParams.date_from) {
        url += `&date_from=${dateParams.date_from}&date_to=${dateParams.date_to}`;
    } else {
        url += `&days=${dateParams.days}`;
    }
    window.location.href = url;
}

/**
 * Open workstation detail modal
 */
async function openWorkstationDetail(workstationId) {
    const date = document.getElementById('dateInput').value;
    const modal = document.getElementById('detailModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');

    // Find workstation info
    const ws = currentWorkstations.find(w => w.workstation_id === workstationId);
    title.textContent = ws ? ws.workstation_name : `Workstation ${workstationId}`;

    body.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Caricamento...</p></div>';
    modal.classList.add('active');

    try {
        const response = await fetch(
            `${CONFIG.apiBase}/workstation_detail.php?id=${workstationId}&lab_id=${CONFIG.labId}&date=${date}`
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        renderWorkstationDetail(data, body);

    } catch (error) {
        console.error('Error loading detail:', error);
        body.innerHTML = `<div class="error">Errore: ${error.message}</div>`;
    }
}

/**
 * Render workstation detail in modal
 */
function renderWorkstationDetail(data, container) {
    const { summary, results, workstation } = data;

    let html = `
        <div class="results-summary">
            <div class="summary-item">
                <div class="value">${summary.total}</div>
                <div class="label">Totale</div>
            </div>
            <div class="summary-item">
                <div class="value" style="color: var(--color-green)">${summary.ok}</div>
                <div class="label">OK</div>
            </div>
            <div class="summary-item">
                <div class="value" style="color: var(--color-yellow)">${summary.warnings}</div>
                <div class="label">Warning</div>
            </div>
            <div class="summary-item">
                <div class="value" style="color: var(--color-red)">${summary.violations}</div>
                <div class="label">Violazioni</div>
            </div>
        </div>
    `;

    if (results.length === 0) {
        html += '<div class="no-data">Nessun risultato per questa data.</div>';
    } else {
        html += `
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Test</th>
                        <th>Controllo</th>
                        <th>Valore</th>
                        <th>Target</th>
                        <th>SD</th>
                        <th>Z-Score</th>
                        <th>Stato</th>
                        <th>Ora</th>
                        <th>Grafico</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map(r => `
                        <tr class="status-${r.status}">
                            <td>
                                <a class="test-link" onclick="openTestAvailability(${r.test_method_id}, '${escapeHtml(r.test)}')">
                                    ${escapeHtml(r.test)}
                                </a>
                            </td>
                            <td>${escapeHtml(r.control)}</td>
                            <td>${r.value.toFixed(2)}</td>
                            <td>${r.target.toFixed(2)}</td>
                            <td>${r.sd.toFixed(2)}</td>
                            <td class="zscore status-${r.status}">
                                ${r.zscore !== null ? r.zscore.toFixed(2) : '-'}
                            </td>
                            <td class="status-${r.status}">
                                ${getStatusText(r.status)}
                            </td>
                            <td>${formatTime(r.received)}</td>
                            <td>
                                <button class="btn-chart" onclick="openLJChart(${r.batch_id}, '${escapeHtml(r.test)}')" title="Grafico Levey-Jennings">
                                    📈
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    container.innerHTML = html;
}

/**
 * Open test availability modal
 */
async function openTestAvailability(testMethodId, testName) {
    const date = document.getElementById('dateInput').value;
    const modal = document.getElementById('availabilityModal');
    const title = document.getElementById('availabilityTitle');
    const body = document.getElementById('availabilityBody');

    title.textContent = `${testName} - Disponibilità`;
    body.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Caricamento...</p></div>';
    modal.classList.add('active');

    try {
        const response = await fetch(
            `${CONFIG.apiBase}/test_availability.php?test_method_id=${testMethodId}&lab_id=${CONFIG.labId}&date=${date}`
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        renderTestAvailability(data, body);

    } catch (error) {
        console.error('Error loading availability:', error);
        body.innerHTML = `<div class="error">Errore: ${error.message}</div>`;
    }
}

/**
 * Render test availability
 */
function renderTestAvailability(data, container) {
    const { test, summary, workstations } = data;

    let html = `
        <div class="results-summary">
            <div class="summary-item">
                <div class="value">${summary.total_workstations}</div>
                <div class="label">Workstation</div>
            </div>
            <div class="summary-item">
                <div class="value" style="color: var(--color-green)">${summary.available}</div>
                <div class="label">Disponibili</div>
            </div>
            <div class="summary-item">
                <div class="value" style="color: var(--color-red)">${summary.with_problems}</div>
                <div class="label">Con problemi</div>
            </div>
        </div>
        <p style="margin-bottom: 16px; color: var(--color-text-muted);">
            ${test.name} può essere refertato sulle workstation evidenziate in verde.
        </p>
        <div class="availability-list">
    `;

    if (workstations.length === 0) {
        html += '<div class="no-data">Nessuna workstation configurata per questo test.</div>';
    } else {
        workstations.forEach(ws => {
            html += `
                <div class="availability-item status-${ws.status}">
                    <div class="ws-name">${escapeHtml(ws.workstation_name)}</div>
                    <div class="ws-status">
                        ${getStatusText(ws.status)}
                        ${ws.status === 'ok' ? '- DISPONIBILE' : ''}
                    </div>
                </div>
            `;
        });
    }

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Get human-readable status text
 */
function getStatusText(status) {
    switch (status) {
        case 'ok': return 'OK';
        case 'warning': return 'Warning';
        case 'violation': return 'Violazione';
        case 'unknown': return 'Nessun dato';
        default: return status;
    }
}

/**
 * Close all modals
 */
function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.remove('active');
    });
}

/**
 * Handle auto-refresh change
 */
function handleAutoRefreshChange() {
    const value = parseInt(document.getElementById('autoRefresh').value);
    CONFIG.autoRefreshInterval = value * 1000;

    stopAutoRefresh();
    if (value > 0) {
        startAutoRefresh();
    }
}

/**
 * Start auto-refresh timer
 */
function startAutoRefresh() {
    if (CONFIG.autoRefreshInterval > 0) {
        autoRefreshTimer = setInterval(loadWorkstations, CONFIG.autoRefreshInterval);
    }
}

/**
 * Stop auto-refresh timer
 */
function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
}

/**
 * Update last refresh timestamp
 */
function updateLastRefresh() {
    const el = document.getElementById('lastRefresh');
    el.textContent = `Ultimo aggiornamento: ${new Date().toLocaleTimeString('it-IT')}`;
}

/**
 * Show loading state
 */
function showLoading(container) {
    container.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>Caricamento...</p>
        </div>
    `;
}

/**
 * Show error message
 */
function showError(message, container = null) {
    const html = `<div class="error">${escapeHtml(message)}</div>`;
    if (container) {
        container.innerHTML = html;
    } else {
        document.getElementById('workstationsGrid').innerHTML = html;
    }
}

/**
 * Format time from datetime string
 */
function formatTime(datetime) {
    if (!datetime) return '-';
    const date = new Date(datetime);
    return date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Format date in Italian format (dd/mm/yyyy)
 */
function formatDate(datetime) {
    if (!datetime) return '-';
    const date = new Date(datetime);
    return date.toLocaleDateString('it-IT');
}

/**
 * Format datetime in Italian format (dd/mm/yyyy HH:mm)
 */
function formatDateTime(datetime) {
    if (!datetime) return '-';
    const date = new Date(datetime);
    return date.toLocaleDateString('it-IT') + ' ' + date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Open Levey-Jennings chart modal
 */
async function openLJChart(batchId, testName) {
    const modal = document.getElementById('chartModal');
    const title = document.getElementById('chartTitle');
    const info = document.getElementById('chartInfo');
    const stats = document.getElementById('chartStats');

    title.textContent = `${testName} - Levey-Jennings`;
    info.innerHTML = '<div class="loading">Caricamento...</div>';
    stats.innerHTML = '';
    modal.classList.add('active');

    // Destroy previous chart instance
    if (ljChartInstance) {
        ljChartInstance.destroy();
        ljChartInstance = null;
    }

    try {
        const response = await fetch(
            `${CONFIG.apiBase}/series.php?batch_id=${batchId}&lab_id=${CONFIG.labId}&limit=50`
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        renderLJChart(data);

    } catch (error) {
        console.error('Error loading chart data:', error);
        info.innerHTML = `<div class="error">Errore: ${error.message}</div>`;
    }
}

/**
 * Render Levey-Jennings chart
 */
function renderLJChart(data) {
    const { batch, statistics, series } = data;
    const info = document.getElementById('chartInfo');
    const stats = document.getElementById('chartStats');

    // Show batch info
    info.innerHTML = `
        <div class="chart-info-item">
            <span class="label">Controllo:</span>
            <span class="value">${escapeHtml(batch.control)}</span>
        </div>
        <div class="chart-info-item">
            <span class="label">Lotto:</span>
            <span class="value">${escapeHtml(batch.lot_number)}</span>
        </div>
        <div class="chart-info-item">
            <span class="label">Workstation:</span>
            <span class="value">${escapeHtml(batch.workstation)}</span>
        </div>
        <div class="chart-info-item">
            <span class="label">Target:</span>
            <span class="value">${batch.target.toFixed(2)} ± ${batch.sd.toFixed(2)} ${escapeHtml(batch.unit)}</span>
        </div>
    `;

    // Show statistics
    stats.innerHTML = `
        <div class="stat">
            <div class="stat-value">${statistics.count}</div>
            <div class="stat-label">N</div>
        </div>
        <div class="stat">
            <div class="stat-value">${statistics.mean.toFixed(2)}</div>
            <div class="stat-label">Media</div>
        </div>
        <div class="stat">
            <div class="stat-value">${statistics.sd.toFixed(2)}</div>
            <div class="stat-label">DS</div>
        </div>
        <div class="stat">
            <div class="stat-value">${statistics.cv.toFixed(1)}%</div>
            <div class="stat-label">CV%</div>
        </div>
    `;

    // Prepare chart data
    const target = batch.target;
    const sd = batch.sd;

    const labels = series.map((s, i) => {
        const date = new Date(s.received);
        return date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' });
    });

    const values = series.map(s => s.value);

    // Determine point colors based on z-score
    const pointColors = series.map(s => {
        const zscore = Math.abs(s.zscore || 0);
        if (zscore >= 3) return '#dc3545'; // Red
        if (zscore >= 2) return '#ffc107'; // Yellow
        return '#28a745'; // Green
    });

    const pointBorderColors = pointColors;

    // Calculate Y axis range (target ± 4SD)
    const yMin = target - 4 * sd;
    const yMax = target + 4 * sd;

    // Create chart
    const ctx = document.getElementById('ljChart').getContext('2d');

    ljChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: batch.test,
                data: values,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                pointBackgroundColor: pointColors,
                pointBorderColor: pointBorderColors,
                pointRadius: 6,
                pointHoverRadius: 8,
                fill: false,
                tension: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: yMin,
                    max: yMax,
                    title: {
                        display: true,
                        text: batch.unit
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Data'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const idx = context.dataIndex;
                            const s = series[idx];
                            const zscore = s.zscore !== null ? s.zscore.toFixed(2) : 'N/A';
                            return [
                                `Valore: ${s.value.toFixed(2)}`,
                                `Z-Score: ${zscore}`,
                                `Ora: ${new Date(s.received).toLocaleTimeString('it-IT')}`
                            ];
                        }
                    }
                },
                annotation: {
                    annotations: {
                        targetLine: {
                            type: 'line',
                            yMin: target,
                            yMax: target,
                            borderColor: '#000',
                            borderWidth: 2,
                            label: {
                                display: true,
                                content: 'Target',
                                position: 'start'
                            }
                        },
                        plus1sd: {
                            type: 'line',
                            yMin: target + sd,
                            yMax: target + sd,
                            borderColor: '#28a745',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        minus1sd: {
                            type: 'line',
                            yMin: target - sd,
                            yMax: target - sd,
                            borderColor: '#28a745',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        plus2sd: {
                            type: 'line',
                            yMin: target + 2 * sd,
                            yMax: target + 2 * sd,
                            borderColor: '#ffc107',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        minus2sd: {
                            type: 'line',
                            yMin: target - 2 * sd,
                            yMax: target - 2 * sd,
                            borderColor: '#ffc107',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        plus3sd: {
                            type: 'line',
                            yMin: target + 3 * sd,
                            yMax: target + 3 * sd,
                            borderColor: '#dc3545',
                            borderWidth: 2,
                            borderDash: [5, 5]
                        },
                        minus3sd: {
                            type: 'line',
                            yMin: target - 3 * sd,
                            yMax: target - 3 * sd,
                            borderColor: '#dc3545',
                            borderWidth: 2,
                            borderDash: [5, 5]
                        }
                    }
                }
            }
        }
    });
}
