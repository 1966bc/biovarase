<?php
/**
 * Admin - Units Management
 */
$pageTitle = 'Units - Admin - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

$config = [
    'table' => 'units',
    'pk' => 'unit_id',
    'title' => 'Units',
    'title_singular' => 'Unit',
    'description_maxlen' => 10,
    'check_fk_tables' => ['assays', 'test_methods'],
    'fk_field' => 'unit_id',
    'role_required' => 0,
];

include __DIR__ . '/../../includes/crud_simple.php';
