<?php
/**
 * CRUD for Corrective Actions
 * Global table (App Admin only) - QC corrective actions for peer lab comparison
 */

$pageTitle = 'Corrective Actions - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

$config = [
    'table' => 'actions',
    'pk' => 'action_id',
    'title' => 'Corrective Actions',
    'title_singular' => 'Action',
    'description_maxlen' => 50,
    'description_unique' => true,
    'extra_fields' => [
        'code' => ['label' => 'Code', 'maxlen' => 30]
    ],
    'check_fk_tables' => ['result_actions'],
    'fk_field' => 'action_id',
    'role_required' => 0,
];

include __DIR__ . '/../../includes/crud_simple.php';
