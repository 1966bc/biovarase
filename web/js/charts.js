/**
 * Biovarase - Charts page JavaScript
 *
 * Handles test selection and multiple Levey-Jennings chart rendering.
 */

// Configuration from URL
const CONFIG = {
    apiBase: 'api',
    labId: null,
    workstationId: null,
    date: null
};

// State
let currentTests = [];
let chartInstances = [];

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    CONFIG.labId = urlParams.get('lab_id');
    CONFIG.workstationId = urlParams.get('workstation_id');

    if (!CONFIG.labId || !CONFIG.workstationId) {
        showError('Parametri mancanti. Usa: ?lab_id=X&workstation_id=Y');
        return;
    }

    // Set date controls from URL params
    const daysParam = urlParams.get('days');
    const dateFromParam = urlParams.get('date_from');
    const dateToParam = urlParams.get('date_to');

    if (dateFromParam && dateToParam) {
        document.getElementById('dateFrom').value = dateFromParam;
        document.getElementById('dateTo').value = dateToParam;
        document.getElementById('daysSelect').disabled = true;
    } else if (daysParam) {
        document.getElementById('daysSelect').value = daysParam;
    }

    // Update back link with same params
    let backUrl = `dashboard.html?lab_id=${CONFIG.labId}`;
    if (dateFromParam && dateToParam) {
        backUrl += `&date_from=${dateFromParam}&date_to=${dateToParam}`;
    } else if (daysParam) {
        backUrl += `&days=${daysParam}`;
    }
    document.getElementById('backLink').href = backUrl;

    // Event listeners
    document.getElementById('refreshBtn').addEventListener('click', () => { loadTests(); refreshCharts(); });
    document.getElementById('limitSelect').addEventListener('change', refreshCharts);
    document.getElementById('daysSelect').addEventListener('change', () => { loadTests(); refreshCharts(); });
    document.getElementById('dateFrom').addEventListener('change', onDateRangeChange);
    document.getElementById('dateTo').addEventListener('change', onDateRangeChange);
    document.getElementById('clearDates').addEventListener('click', clearDateRange);

    // Load tests
    loadTests();
});

/**
 * Handle date range change - disable days dropdown when dates are set
 */
function onDateRangeChange() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const daysSelect = document.getElementById('daysSelect');

    // Disable days dropdown when custom dates are set
    daysSelect.disabled = !!(dateFrom || dateTo);

    // Reload tests and charts if both dates are set
    if (dateFrom && dateTo) {
        loadTests();
        refreshCharts();
    }
}

/**
 * Clear date range inputs
 */
function clearDateRange() {
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('daysSelect').disabled = false;
    loadTests();
    refreshCharts();
}

/**
 * Load tests for the workstation
 */
async function loadTests() {
    const testsList = document.getElementById('testsList');
    testsList.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    // Build URL with date params
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const days = document.getElementById('daysSelect').value;

    let url = `${CONFIG.apiBase}/workstation_tests.php?workstation_id=${CONFIG.workstationId}&lab_id=${CONFIG.labId}`;
    if (dateFrom && dateTo) {
        url += `&date_from=${dateFrom}&date_to=${dateTo}`;
    } else {
        url += `&days=${days}`;
    }

    try {
        const response = await fetch(url);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        // Update page title
        document.getElementById('pageTitle').textContent = `Grafici QC - ${data.workstation.name}`;

        currentTests = data.tests;
        renderTestsList(data.tests);

    } catch (error) {
        console.error('Error loading tests:', error);
        testsList.innerHTML = `<div class="error">Errore: ${error.message}</div>`;
    }
}

/**
 * Render tests list
 */
function renderTestsList(tests) {
    const testsList = document.getElementById('testsList');

    if (tests.length === 0) {
        testsList.innerHTML = '<div class="no-data">Nessun test configurato</div>';
        return;
    }

    testsList.innerHTML = tests.map(t => {
        // Status indicator
        let statusIndicator = '';
        if (t.status === 'red') {
            statusIndicator = `<span class="test-status status-red" title="${t.violations} violazioni">${t.violations}</span>`;
        } else if (t.status === 'yellow') {
            statusIndicator = `<span class="test-status status-yellow" title="${t.warnings} warning">${t.warnings}</span>`;
        }

        return `
            <div class="test-item test-status-${t.status}" data-test-method-id="${t.test_method_id}" onclick="selectTest(${t.test_method_id})">
                <div class="test-name">${escapeHtml(t.name)} ${statusIndicator}</div>
                <div class="test-info">${t.control_count} controlli</div>
            </div>
        `;
    }).join('');
}

/**
 * Select a test and load its charts
 */
async function selectTest(testMethodId) {
    // Update active state
    document.querySelectorAll('.test-item').forEach(el => {
        el.classList.toggle('active', parseInt(el.dataset.testMethodId) === testMethodId);
    });

    const chartsArea = document.getElementById('chartsArea');
    const limit = document.getElementById('limitSelect').value;
    const days = document.getElementById('daysSelect').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;

    chartsArea.innerHTML = `
        <div class="charts-loading">
            <div class="loading-spinner"></div>
            <p>Caricamento grafici...</p>
        </div>
    `;

    // Destroy previous charts
    destroyCharts();

    // Build URL with either date range or days
    let url = `${CONFIG.apiBase}/test_controls.php?test_method_id=${testMethodId}&workstation_id=${CONFIG.workstationId}&lab_id=${CONFIG.labId}&limit=${limit}`;
    if (dateFrom && dateTo) {
        url += `&date_from=${dateFrom}&date_to=${dateTo}`;
    } else {
        url += `&days=${days}`;
    }

    try {
        const response = await fetch(url);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        renderCharts(data);

    } catch (error) {
        console.error('Error loading charts:', error);
        chartsArea.innerHTML = `<div class="error">Errore: ${error.message}</div>`;
    }
}

/**
 * Render all charts for a test
 */
function renderCharts(data) {
    const chartsArea = document.getElementById('chartsArea');
    const { test, controls } = data;

    if (controls.length === 0) {
        chartsArea.innerHTML = '<div class="no-selection"><p>Nessun controllo configurato per questo test</p></div>';
        return;
    }

    // Create HTML structure
    let html = `
        <div class="target-info">
            <span><span class="target-line"></span> Target</span>
            <span><span class="sd-line sd1"></span> ±1 SD</span>
            <span><span class="sd-line sd2"></span> ±2 SD</span>
            <span><span class="sd-line sd3"></span> ±3 SD</span>
        </div>
    `;

    controls.forEach((ctrl, idx) => {
        // Build status badges
        let badges = '';
        if (ctrl.is_expired) {
            badges += '<span class="badge badge-expired">SCADUTO</span>';
        }
        if (!ctrl.is_active) {
            badges += '<span class="badge badge-inactive">NON ATTIVO</span>';
        }

        // Format dates
        const firstDate = ctrl.first_result ? new Date(ctrl.first_result).toLocaleDateString('it-IT') : '-';
        const lastDate = ctrl.last_result ? new Date(ctrl.last_result).toLocaleDateString('it-IT') : '-';
        const expirationDate = ctrl.expiration ? new Date(ctrl.expiration).toLocaleDateString('it-IT') : '-';

        html += `
            <div class="chart-card ${ctrl.is_expired ? 'expired' : ''} ${!ctrl.is_active ? 'inactive' : ''}">
                <div class="chart-card-header">
                    <div>
                        <h4>${escapeHtml(ctrl.control)} ${badges}</h4>
                        <span class="lot-number">Lotto: ${escapeHtml(ctrl.lot_number)} - Scad: ${expirationDate}</span>
                        <span class="date-range-info">Dati dal ${firstDate} al ${lastDate}</span>
                    </div>
                    <div class="target-info">
                        Target: ${ctrl.target.toFixed(2)} ± ${ctrl.sd.toFixed(2)} ${escapeHtml(test.unit)}
                    </div>
                </div>
                <div class="chart-card-body">
                    <div class="chart-wrapper">
                        <canvas id="chart-${idx}"></canvas>
                    </div>
                    <div class="chart-stats-row">
                        <div class="chart-stat">
                            <div class="value">${ctrl.statistics.count}</div>
                            <div class="label">N</div>
                        </div>
                        <div class="chart-stat">
                            <div class="value">${ctrl.statistics.mean.toFixed(2)}</div>
                            <div class="label">Media</div>
                        </div>
                        <div class="chart-stat">
                            <div class="value">${ctrl.statistics.sd.toFixed(2)}</div>
                            <div class="label">DS</div>
                        </div>
                        <div class="chart-stat">
                            <div class="value">${ctrl.statistics.cv.toFixed(1)}%</div>
                            <div class="label">CV%</div>
                        </div>
                        <div class="chart-stat">
                            <div class="value" style="color: ${Math.abs(ctrl.statistics.bias) > 5 ? '#dc3545' : 'inherit'}">${ctrl.statistics.bias.toFixed(1)}%</div>
                            <div class="label">Bias</div>
                        </div>
                    </div>
                    ${renderDriftAlerts(ctrl.drift)}
                </div>
            </div>
        `;
    });

    chartsArea.innerHTML = html;

    // Create charts after DOM is ready
    setTimeout(() => {
        controls.forEach((ctrl, idx) => {
            createChart(`chart-${idx}`, ctrl, test.unit);
        });
    }, 0);
}

/**
 * Render drift alerts
 */
function renderDriftAlerts(drift) {
    if (!drift.has_drift || drift.alerts.length === 0) {
        return '';
    }

    let html = '<div class="drift-alerts">';
    drift.alerts.forEach(alert => {
        const icon = alert.severity === 'violation' ? '⚠️' : '⚡';
        html += `
            <div class="drift-alert ${alert.severity}">
                <span class="drift-alert-icon">${icon}</span>
                <span>${escapeHtml(alert.message)}</span>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

/**
 * Create a single Levey-Jennings chart
 */
function createChart(canvasId, control, unit) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const { target, sd, series } = control;

    const labels = series.map(s => {
        const date = new Date(s.received);
        return date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' });
    });

    const values = series.map(s => s.value);

    // Point colors based on z-score
    const pointColors = series.map(s => {
        const zscore = Math.abs(s.zscore || 0);
        if (zscore >= 3) return '#dc3545';
        if (zscore >= 2) return '#ffc107';
        return '#28a745';
    });

    // Y axis range
    const yMin = target - 4 * sd;
    const yMax = target + 4 * sd;

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                borderColor: '#007bff',
                backgroundColor: 'transparent',
                pointBackgroundColor: pointColors,
                pointBorderColor: pointColors,
                pointRadius: 5,
                pointHoverRadius: 7,
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
                        text: unit
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
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
                                `${new Date(s.received).toLocaleString('it-IT')}`
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
                            borderWidth: 2
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

    chartInstances.push(chart);
}

/**
 * Refresh current charts
 */
function refreshCharts() {
    const activeTest = document.querySelector('.test-item.active');
    if (activeTest) {
        selectTest(parseInt(activeTest.dataset.testMethodId));
    }
}

/**
 * Destroy all chart instances
 */
function destroyCharts() {
    chartInstances.forEach(chart => {
        if (chart) chart.destroy();
    });
    chartInstances = [];
}

/**
 * Show error message
 */
function showError(message) {
    document.getElementById('testsList').innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
    document.getElementById('chartsArea').innerHTML = '';
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
