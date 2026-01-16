<?php
/**
 * Admin - Methods Management
 */
$pageTitle = 'Methods - Admin - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

$config = [
    'table' => 'methods',
    'pk' => 'method_id',
    'title' => 'Methods',
    'title_singular' => 'Method',
    'description_maxlen' => 30,
    'description_unique' => true,
    'check_fk_tables' => ['assays', 'test_methods'],
    'fk_field' => 'method_id',
    'role_required' => 0,
];

include __DIR__ . '/../../includes/crud_simple.php';
