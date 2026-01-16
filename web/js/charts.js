/**
 * Biovarase - Charts page JavaScript
 *
 * Handles test selection and multiple Levey-Jennings chart rendering.
 */

// Configuration from URL
const CONFIG = {
    apiBase: '/biovarase/api',
    labId: null,
    workstationId: null,
    date: null
};

// State
let currentTests = [];
let chartInstances = [];
let availableActions = [];
let currentSeriesData = {}; // Store series data by chart index for click handling
let isLoggedIn = false; // Will be set from page
let canModifyData = false; // Will be set from page

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
    let backUrl = `/biovarase/dashboard?lab_id=${CONFIG.labId}`;
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

    // Check if user is logged in and permissions (set by PHP in page)
    isLoggedIn = typeof window.USER_LOGGED_IN !== 'undefined' ? window.USER_LOGGED_IN : false;
    canModifyData = typeof window.USER_CAN_MODIFY !== 'undefined' ? window.USER_CAN_MODIFY : false;

    // Load actions for notes (only if logged in)
    if (isLoggedIn) {
        loadActions();
    }

    // Load tests
    loadTests();
});

/**
 * Load available actions for notes
 */
async function loadActions() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/actions.php`);
        const data = await response.json();
        if (data.actions) {
            availableActions = data.actions;
        }
    } catch (error) {
        console.error('Error loading actions:', error);
    }
}

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

        // Auto-select first test if available
        if (data.tests.length > 0) {
            selectTest(data.tests[0].test_method_id);
        }

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

    // Store series data for click handling
    const chartIndex = canvasId.replace('chart-', '');
    currentSeriesData[chartIndex] = series;

    const labels = series.map(s => {
        const date = new Date(s.received);
        return date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' });
    });

    const values = series.map(s => s.value);

    // Point colors based on z-score (gray for voided results)
    const pointColors = series.map(s => {
        // Voided results are always gray
        if (s.is_voided) return '#9e9e9e';

        const zscore = Math.abs(s.zscore || 0);
        if (zscore >= 3) return '#dc3545';
        if (zscore >= 2) return '#ffc107';
        return '#28a745';
    });

    // Point radius - larger for points with notes
    const pointRadii = series.map(s => s.has_notes ? 8 : 5);

    // Point border - thicker black border for points with notes, dashed effect for voided
    const pointBorderColors = series.map((s, idx) => {
        if (s.is_voided) return '#666';
        if (s.has_notes) return '#000';
        return pointColors[idx];
    });
    const pointBorderWidths = series.map(s => {
        if (s.is_voided) return 2;
        if (s.has_notes) return 3;
        return 1;
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
                pointBorderColor: pointBorderColors,
                pointBorderWidth: pointBorderWidths,
                pointRadius: pointRadii,
                pointHoverRadius: 9,
                fill: false,
                tension: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements, chart) => {
                if (elements.length > 0 && isLoggedIn) {
                    const idx = elements[0].index;
                    const chartIdx = canvasId.replace('chart-', '');
                    const point = currentSeriesData[chartIdx][idx];
                    openResultModal(point);
                }
            },
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
                            const noteIndicator = s.has_notes ? ' [N]' : '';
                            const voidedIndicator = s.is_voided ? ' [ANNULLATO]' : '';
                            const lines = [
                                `Valore: ${s.value.toFixed(2)}${noteIndicator}${voidedIndicator}`,
                                `Z-Score: ${zscore}`,
                                `${new Date(s.received).toLocaleString('it-IT')}`
                            ];
                            if (s.is_voided) {
                                const voidedBy = s.voided_by ? s.voided_by : 'N/A';
                                lines.push(`⚠️ Annullato da: ${voidedBy}`);
                            }
                            return lines;
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

// ============================================================================
// Result Modal - Notes and Edit
// ============================================================================

let currentResult = null;
let currentResultPermissions = { can_modify: false, can_void: false };

/**
 * Open modal for result actions (add note, edit value, void)
 */
async function openResultModal(point) {
    currentResult = point;

    // Create modal if it doesn't exist
    let modal = document.getElementById('resultModal');
    if (!modal) {
        modal = createResultModal();
        document.body.appendChild(modal);
    }

    // Populate basic info
    document.getElementById('resultInfo').innerHTML = `
        <p><strong>Data:</strong> ${new Date(point.received).toLocaleString('it-IT')}</p>
        <p><strong>Valore:</strong> ${point.value.toFixed(2)}</p>
        <p><strong>Z-Score:</strong> ${point.zscore !== null ? point.zscore.toFixed(2) : 'N/A'}</p>
    `;

    // Populate actions dropdown
    const actionSelect = document.getElementById('noteAction');
    actionSelect.innerHTML = '<option value="">-- Seleziona azione --</option>' +
        availableActions.map(a => `<option value="${a.action_id}">${escapeHtml(a.description)}</option>`).join('');

    // Clear previous values
    document.getElementById('noteDescription').value = '';
    document.getElementById('noteMessage').innerHTML = '';

    // Load existing notes
    loadResultNotes(point.result_id);

    // Fetch result permissions from API
    const editSection = document.getElementById('editValueSection');
    const voidSection = document.getElementById('voidResultSection');

    // Reset sections
    editSection.style.display = 'none';
    voidSection.style.display = 'none';

    if (isLoggedIn) {
        try {
            const response = await fetch(`${CONFIG.apiBase}/result.php?result_id=${point.result_id}`);
            const data = await response.json();

            if (data.result) {
                currentResultPermissions = {
                    can_modify: data.result.can_modify || false,
                    can_void: data.result.can_void || false
                };

                // Show edit section if user can modify this specific result
                if (currentResultPermissions.can_modify) {
                    editSection.style.display = 'block';
                    document.getElementById('newResultValue').value = point.value;
                    document.getElementById('editValueMessage').innerHTML = '';
                }

                // Show void section if user can void this specific result
                if (currentResultPermissions.can_void) {
                    voidSection.style.display = 'block';
                    document.getElementById('voidMessage').innerHTML = '';
                }

                // Show creator info if available
                if (data.result.created_by_name) {
                    document.getElementById('resultInfo').innerHTML += `
                        <p><strong>Inserito da:</strong> ${escapeHtml(data.result.created_by_name)}</p>
                    `;
                } else {
                    document.getElementById('resultInfo').innerHTML += `
                        <p><strong>Inserito da:</strong> <em>Strumento</em></p>
                    `;
                }
            }
        } catch (error) {
            console.error('Error fetching result permissions:', error);
        }
    }

    // Show modal
    modal.style.display = 'flex';
}

/**
 * Create the result modal HTML
 */
function createResultModal() {
    const modal = document.createElement('div');
    modal.id = 'resultModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal" style="max-width: 650px;">
            <div class="modal-header">
                <h2>Dettaglio Risultato</h2>
                <button class="modal-close" onclick="closeResultModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div id="resultInfo" style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; border-left: 4px solid #6c757d;"></div>

                <!-- Edit Value Section (only for users with modify permission) -->
                <div id="editValueSection" style="margin-bottom: 20px; padding: 15px; background: #e3f2fd; border-radius: 4px; border-left: 4px solid #2196f3; display: none;">
                    <h3 style="margin: 0 0 15px 0; font-size: 1rem; color: #1565c0;">
                        <span style="margin-right: 8px;">✏️</span>Modifica Valore
                    </h3>
                    <div style="display: flex; gap: 10px; align-items: flex-end;">
                        <div style="flex: 1;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 500;">Nuovo valore</label>
                            <input type="number" step="any" id="newResultValue" style="width: 100%; padding: 10px; border: 1px solid #90caf9; border-radius: 4px; background: #fff;">
                        </div>
                        <button onclick="updateResultValue()" style="padding: 10px 20px; background: #1976d2; color: #fff; border: none; border-radius: 4px; cursor: pointer;">Salva Valore</button>
                    </div>
                    <div id="editValueMessage" style="margin-top: 10px;"></div>
                </div>

                <!-- Void Result Section (only for users with void permission) -->
                <div id="voidResultSection" style="margin-bottom: 20px; padding: 15px; background: #ffebee; border-radius: 4px; border-left: 4px solid #d32f2f; display: none;">
                    <h3 style="margin: 0 0 15px 0; font-size: 1rem; color: #c62828;">
                        <span style="margin-right: 8px;">🚫</span>Annulla Risultato
                    </h3>
                    <p style="margin: 0 0 15px 0; color: #666; font-size: 0.9rem;">
                        Il risultato verrà annullato (status=0) e non comparirà più nei grafici e nelle statistiche.
                        L'operazione viene registrata nell'audit trail.
                    </p>
                    <button onclick="voidResult()" style="padding: 10px 20px; background: #d32f2f; color: #fff; border: none; border-radius: 4px; cursor: pointer;">Annulla Risultato</button>
                    <div id="voidMessage" style="margin-top: 10px;"></div>
                </div>

                <!-- Existing Notes -->
                <div id="existingNotes" style="margin-bottom: 20px;"></div>

                <!-- Add Note Section -->
                <div id="addNoteSection" style="padding: 15px; background: #fff8e1; border-radius: 4px; border-left: 4px solid #ff9800;">
                    <h3 style="margin: 0 0 15px 0; font-size: 1rem; color: #e65100;">
                        <span style="margin-right: 8px;">📝</span>Aggiungi Nota
                    </h3>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">Azione correttiva</label>
                        <select id="noteAction" style="width: 100%; padding: 10px; border: 1px solid #ffe0b2; border-radius: 4px; background: #fff;">
                            <option value="">-- Seleziona azione --</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500;">Descrizione</label>
                        <textarea id="noteDescription" rows="3" maxlength="200" placeholder="Descrizione della nota..." style="width: 100%; padding: 10px; border: 1px solid #ffe0b2; border-radius: 4px; resize: vertical; background: #fff;"></textarea>
                    </div>
                    <button onclick="saveNote()" style="padding: 10px 20px; background: #f57c00; color: #fff; border: none; border-radius: 4px; cursor: pointer;">Salva Nota</button>
                    <div id="noteMessage" style="margin-top: 10px;"></div>
                </div>

                <div style="margin-top: 20px; text-align: right;">
                    <button onclick="closeResultModal()" style="padding: 10px 25px; background: #6c757d; color: #fff; border: none; border-radius: 4px; cursor: pointer;">Chiudi</button>
                </div>
            </div>
        </div>
    `;

    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeResultModal();
    });

    return modal;
}

/**
 * Load existing notes for a result
 */
async function loadResultNotes(resultId) {
    const container = document.getElementById('existingNotes');
    container.innerHTML = '<p>Caricamento note...</p>';

    try {
        const response = await fetch(`${CONFIG.apiBase}/notes.php?result_id=${resultId}`);
        const data = await response.json();

        if (data.notes && data.notes.length > 0) {
            container.innerHTML = `
                <h3 style="margin-bottom: 10px; font-size: 1rem;">Note esistenti</h3>
                <div style="max-height: 150px; overflow-y: auto;">
                    ${data.notes.map(note => `
                        <div style="padding: 10px; background: #fff3cd; border-radius: 4px; margin-bottom: 8px; font-size: 0.9rem;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>${escapeHtml(note.action_name)}</strong>
                                <span style="color: #666; font-size: 0.8rem;">${escapeHtml(note.created_by_name || 'Sistema')}</span>
                            </div>
                            <div>${escapeHtml(note.description)}</div>
                            <div style="color: #666; font-size: 0.8rem; margin-top: 5px;">${new Date(note.created_at).toLocaleString('it-IT')}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            container.innerHTML = '<p style="color: #666; font-style: italic;">Nessuna nota esistente</p>';
        }
    } catch (error) {
        console.error('Error loading notes:', error);
        container.innerHTML = '<p style="color: #dc3545;">Errore caricamento note</p>';
    }
}

/**
 * Save a new note
 */
async function saveNote() {
    const actionId = document.getElementById('noteAction').value;
    const description = document.getElementById('noteDescription').value.trim();
    const messageDiv = document.getElementById('noteMessage');

    if (!actionId) {
        messageDiv.innerHTML = '<p style="color: #dc3545;">Seleziona un\'azione</p>';
        return;
    }

    if (!description) {
        messageDiv.innerHTML = '<p style="color: #dc3545;">Inserisci una descrizione</p>';
        return;
    }

    messageDiv.innerHTML = '<p>Salvataggio...</p>';

    try {
        const response = await fetch(`${CONFIG.apiBase}/notes.php`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result_id: currentResult.result_id,
                action_id: parseInt(actionId),
                description: description
            })
        });

        const data = await response.json();

        if (data.success) {
            messageDiv.innerHTML = '<p style="color: #28a745;">Nota salvata!</p>';
            // Close modal and refresh charts after short delay
            setTimeout(() => {
                closeResultModal();
                refreshCharts();
            }, 800);
        } else {
            messageDiv.innerHTML = `<p style="color: #dc3545;">${escapeHtml(data.error || 'Errore')}</p>`;
        }
    } catch (error) {
        console.error('Error saving note:', error);
        messageDiv.innerHTML = '<p style="color: #dc3545;">Errore di connessione</p>';
    }
}

/**
 * Update result value
 */
async function updateResultValue() {
    const newValue = document.getElementById('newResultValue').value;
    const messageDiv = document.getElementById('editValueMessage');

    if (!newValue || isNaN(parseFloat(newValue))) {
        messageDiv.innerHTML = '<p style="color: #dc3545;">Inserisci un valore numerico valido</p>';
        return;
    }

    messageDiv.innerHTML = '<p>Aggiornamento...</p>';

    try {
        const response = await fetch(`${CONFIG.apiBase}/result.php`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result_id: currentResult.result_id,
                value: parseFloat(newValue)
            })
        });

        const data = await response.json();

        if (data.success) {
            messageDiv.innerHTML = `<p style="color: #28a745;">Valore aggiornato: ${data.old_value.toFixed(2)} → ${data.new_value.toFixed(2)}</p>`;
            // Close modal and refresh charts after short delay
            setTimeout(() => {
                closeResultModal();
                refreshCharts();
            }, 800);
        } else {
            messageDiv.innerHTML = `<p style="color: #dc3545;">${escapeHtml(data.error || 'Errore')}</p>`;
        }
    } catch (error) {
        console.error('Error updating result:', error);
        messageDiv.innerHTML = '<p style="color: #dc3545;">Errore di connessione</p>';
    }
}

/**
 * Void (annulla) result - sets status=0
 */
async function voidResult() {
    const messageDiv = document.getElementById('voidMessage');

    // Confirm before voiding
    if (!confirm('Sei sicuro di voler annullare questo risultato?\n\nIl risultato non verrà eliminato ma non comparirà più nei grafici e nelle statistiche.')) {
        return;
    }

    messageDiv.innerHTML = '<p>Annullamento in corso...</p>';

    try {
        console.log('Voiding result:', currentResult.result_id);

        const response = await fetch(`${CONFIG.apiBase}/result.php`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'void',
                result_id: currentResult.result_id
            })
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const text = await response.text();
            console.error('Error response:', text);
            messageDiv.innerHTML = `<p style="color: #dc3545;">Errore ${response.status}: ${text.substring(0, 100)}</p>`;
            return;
        }

        const data = await response.json();
        console.log('Response data:', data);

        if (data.success) {
            messageDiv.innerHTML = '<p style="color: #28a745;">Risultato annullato!</p>';
            // Close modal and refresh charts after short delay
            setTimeout(() => {
                closeResultModal();
                refreshCharts();
            }, 800);
        } else {
            messageDiv.innerHTML = `<p style="color: #dc3545;">${escapeHtml(data.error || 'Errore')}</p>`;
        }
    } catch (error) {
        console.error('Error voiding result:', error);
        messageDiv.innerHTML = `<p style="color: #dc3545;">Errore: ${error.message}</p>`;
    }
}

/**
 * Close result modal
 */
function closeResultModal() {
    const modal = document.getElementById('resultModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentResult = null;
}
