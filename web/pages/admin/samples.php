<?php
/**
 * Admin - Samples Management
 */
$pageTitle = 'Samples - Admin - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

$config = [
    'table' => 'samples',
    'pk' => 'sample_id',
    'title' => 'Samples',
    'title_singular' => 'Sample',
    'description_maxlen' => 8,
    'description_unique' => true,
    'extra_fields' => [
        'sample' => ['label' => 'Symbol', 'maxlen' => 1],
    ],
    'check_fk_tables' => ['assays', 'test_methods'],
    'fk_field' => 'sample_id',
    'role_required' => 0,
];

include __DIR__ . '/../../includes/crud_simple.php';
