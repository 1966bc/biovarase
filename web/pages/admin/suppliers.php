<?php
/**
 * CRUD for Suppliers
 * Global table (App Admin only) - Control/reagent manufacturers
 */

$pageTitle = 'Suppliers - Biovarase';
require_once __DIR__ . '/../../includes/header.php';
require_once __DIR__ . '/../../api/config.php';

$config = [
    'table' => 'suppliers',
    'pk' => 'supplier_id',
    'title' => 'Suppliers',
    'title_singular' => 'Supplier',
    'description_maxlen' => 255,
    'description_unique' => true,
    'check_fk_tables' => ['controls', 'equipments'],
    'fk_field' => 'supplier_id',
    'role_required' => 0,
];

include __DIR__ . '/../../includes/crud_simple.php';
