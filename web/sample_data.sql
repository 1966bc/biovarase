-- Biovarase Web - Sample Data for Development
-- Run after biovarase.sql and all migrations
--
-- Usage:
--   mysql -u root -p biovarase < web/sample_data.sql

-- Clear existing sample data (careful in production!)
-- DELETE FROM results WHERE org_id = 9999;
-- DELETE FROM batches WHERE org_id = 9999;

-- ============================================================================
-- ORGANIZATIONS
-- ============================================================================

INSERT IGNORE INTO organizations (org_id, org_type, description, parent_id, status) VALUES
(9999, 'lab', 'Laboratorio Demo', NULL, 1),
(9998, 'section', 'Sezione Chimica Clinica', 9999, 1);

-- ============================================================================
-- USERS (password: 'demo123' - bcrypt hash)
-- ============================================================================

INSERT IGNORE INTO users (user_id, nickname, pswrd, first_name, last_name, role, org_id, status, elapsing_time, enable_time) VALUES
(9999, 'admin_demo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4aVkq3xCPbgIWIUi', 'Admin', 'Demo', 0, 9999, 1, 60, 1),
(9998, 'tecnico_demo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4aVkq3xCPbgIWIUi', 'Mario', 'Rossi', 5, 9999, 1, 30, 1),
(9997, 'viewer_demo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4aVkq3xCPbgIWIUi', 'Luigi', 'Verdi', 6, 9999, 1, 0, 0);

-- ============================================================================
-- MASTER DATA (if not already present)
-- ============================================================================

-- Units
INSERT IGNORE INTO units (unit_id, description, status) VALUES
(999, 'mg/dL', 1),
(998, 'mmol/L', 1),
(997, 'U/L', 1);

-- Methods
INSERT IGNORE INTO methods (method_id, description, status) VALUES
(999, 'Enzymatic', 1),
(998, 'Immunometric', 1);

-- Samples
INSERT IGNORE INTO samples (sample_id, description, status) VALUES
(999, 'Serum', 1),
(998, 'Plasma', 1);

-- Tests
INSERT IGNORE INTO tests (test_id, description, status) VALUES
(999, 'Glucose', 1),
(998, 'Cholesterol', 1),
(997, 'AST', 1),
(996, 'ALT', 1);

-- Controls
INSERT IGNORE INTO controls (control_id, description, status) VALUES
(999, 'Control Level 1', 1),
(998, 'Control Level 2', 1);

-- Actions (corrective actions)
INSERT IGNORE INTO actions (action_id, description, status) VALUES
(999, 'Repeated analysis', 1),
(998, 'New calibration', 1),
(997, 'Reagent replaced', 1),
(996, 'Maintenance performed', 1);

-- ============================================================================
-- WORKSTATIONS
-- ============================================================================

INSERT IGNORE INTO workstations (workstation_id, description, org_id, status) VALUES
(9999, 'Analyzer Demo 1', 9998, 1),
(9998, 'Analyzer Demo 2', 9998, 1);

-- ============================================================================
-- TEST METHODS (link test + method + unit)
-- ============================================================================

INSERT IGNORE INTO test_methods (test_method_id, test_id, method_id, unit_id, sample_id, org_id, status) VALUES
(9999, 999, 999, 999, 999, 9998, 1),  -- Glucose Enzymatic mg/dL
(9998, 998, 999, 999, 999, 9998, 1),  -- Cholesterol Enzymatic mg/dL
(9997, 997, 999, 997, 999, 9998, 1),  -- AST Enzymatic U/L
(9996, 996, 999, 997, 999, 9998, 1);  -- ALT Enzymatic U/L

-- ============================================================================
-- BATCHES (QC lots)
-- ============================================================================

INSERT IGNORE INTO batches (batch_id, test_method_id, workstation_id, control_id, description, lot_number, target, sd, expiration, org_id, status) VALUES
-- Glucose L1 and L2 on Analyzer 1
(9999, 9999, 9999, 999, 'L1', 'LOT-2026-001', 85.0, 4.2, '2027-12-31', 9999, 1),
(9998, 9999, 9999, 998, 'L2', 'LOT-2026-002', 250.0, 12.5, '2027-12-31', 9999, 1),
-- Cholesterol L1 and L2 on Analyzer 1
(9997, 9998, 9999, 999, 'L1', 'LOT-2026-003', 120.0, 6.0, '2027-12-31', 9999, 1),
(9996, 9998, 9999, 998, 'L2', 'LOT-2026-004', 280.0, 14.0, '2027-12-31', 9999, 1),
-- AST L1 on Analyzer 2
(9995, 9997, 9998, 999, 'L1', 'LOT-2026-005', 35.0, 3.5, '2027-12-31', 9999, 1),
(9994, 9997, 9998, 998, 'L2', 'LOT-2026-006', 120.0, 12.0, '2027-12-31', 9999, 1);

-- ============================================================================
-- RESULTS (sample QC data - last 30 days)
-- ============================================================================

-- Generate sample results for Glucose L1 (batch 9999)
-- Values around target 85.0 with SD 4.2
INSERT IGNORE INTO results (result_id, batch_id, workstation_id, result, received, org_id, status, is_delete) VALUES
(99990001, 9999, 9999, 84.2, DATE_SUB(NOW(), INTERVAL 30 DAY), 9999, 1, 0),
(99990002, 9999, 9999, 86.1, DATE_SUB(NOW(), INTERVAL 29 DAY), 9999, 1, 0),
(99990003, 9999, 9999, 83.5, DATE_SUB(NOW(), INTERVAL 28 DAY), 9999, 1, 0),
(99990004, 9999, 9999, 87.3, DATE_SUB(NOW(), INTERVAL 27 DAY), 9999, 1, 0),
(99990005, 9999, 9999, 85.0, DATE_SUB(NOW(), INTERVAL 26 DAY), 9999, 1, 0),
(99990006, 9999, 9999, 82.8, DATE_SUB(NOW(), INTERVAL 25 DAY), 9999, 1, 0),
(99990007, 9999, 9999, 88.5, DATE_SUB(NOW(), INTERVAL 24 DAY), 9999, 1, 0),
(99990008, 9999, 9999, 84.9, DATE_SUB(NOW(), INTERVAL 23 DAY), 9999, 1, 0),
(99990009, 9999, 9999, 86.7, DATE_SUB(NOW(), INTERVAL 22 DAY), 9999, 1, 0),
(99990010, 9999, 9999, 83.2, DATE_SUB(NOW(), INTERVAL 21 DAY), 9999, 1, 0),
(99990011, 9999, 9999, 85.8, DATE_SUB(NOW(), INTERVAL 20 DAY), 9999, 1, 0),
(99990012, 9999, 9999, 84.1, DATE_SUB(NOW(), INTERVAL 19 DAY), 9999, 1, 0),
(99990013, 9999, 9999, 91.5, DATE_SUB(NOW(), INTERVAL 18 DAY), 9999, 1, 0),  -- Warning (+1.5 SD)
(99990014, 9999, 9999, 85.3, DATE_SUB(NOW(), INTERVAL 17 DAY), 9999, 1, 0),
(99990015, 9999, 9999, 84.6, DATE_SUB(NOW(), INTERVAL 16 DAY), 9999, 1, 0),
(99990016, 9999, 9999, 86.2, DATE_SUB(NOW(), INTERVAL 15 DAY), 9999, 1, 0),
(99990017, 9999, 9999, 83.9, DATE_SUB(NOW(), INTERVAL 14 DAY), 9999, 1, 0),
(99990018, 9999, 9999, 85.5, DATE_SUB(NOW(), INTERVAL 13 DAY), 9999, 1, 0),
(99990019, 9999, 9999, 97.0, DATE_SUB(NOW(), INTERVAL 12 DAY), 9999, 1, 0),  -- Violation (+2.9 SD)
(99990020, 9999, 9999, 84.8, DATE_SUB(NOW(), INTERVAL 11 DAY), 9999, 1, 0),
(99990021, 9999, 9999, 85.2, DATE_SUB(NOW(), INTERVAL 10 DAY), 9999, 1, 0),
(99990022, 9999, 9999, 86.0, DATE_SUB(NOW(), INTERVAL 9 DAY), 9999, 1, 0),
(99990023, 9999, 9999, 84.3, DATE_SUB(NOW(), INTERVAL 8 DAY), 9999, 1, 0),
(99990024, 9999, 9999, 85.7, DATE_SUB(NOW(), INTERVAL 7 DAY), 9999, 1, 0),
(99990025, 9999, 9999, 83.6, DATE_SUB(NOW(), INTERVAL 6 DAY), 9999, 1, 0),
(99990026, 9999, 9999, 86.4, DATE_SUB(NOW(), INTERVAL 5 DAY), 9999, 1, 0),
(99990027, 9999, 9999, 84.5, DATE_SUB(NOW(), INTERVAL 4 DAY), 9999, 1, 0),
(99990028, 9999, 9999, 85.9, DATE_SUB(NOW(), INTERVAL 3 DAY), 9999, 1, 0),
(99990029, 9999, 9999, 84.0, DATE_SUB(NOW(), INTERVAL 2 DAY), 9999, 1, 0),
(99990030, 9999, 9999, 85.4, DATE_SUB(NOW(), INTERVAL 1 DAY), 9999, 1, 0);

-- Glucose L2 (batch 9998) - target 250.0, SD 12.5
INSERT IGNORE INTO results (result_id, batch_id, workstation_id, result, received, org_id, status, is_delete) VALUES
(99980001, 9998, 9999, 248.5, DATE_SUB(NOW(), INTERVAL 30 DAY), 9999, 1, 0),
(99980002, 9998, 9999, 252.3, DATE_SUB(NOW(), INTERVAL 29 DAY), 9999, 1, 0),
(99980003, 9998, 9999, 246.8, DATE_SUB(NOW(), INTERVAL 28 DAY), 9999, 1, 0),
(99980004, 9998, 9999, 254.1, DATE_SUB(NOW(), INTERVAL 27 DAY), 9999, 1, 0),
(99980005, 9998, 9999, 249.7, DATE_SUB(NOW(), INTERVAL 26 DAY), 9999, 1, 0),
(99980006, 9998, 9999, 251.2, DATE_SUB(NOW(), INTERVAL 25 DAY), 9999, 1, 0),
(99980007, 9998, 9999, 247.5, DATE_SUB(NOW(), INTERVAL 24 DAY), 9999, 1, 0),
(99980008, 9998, 9999, 253.0, DATE_SUB(NOW(), INTERVAL 23 DAY), 9999, 1, 0),
(99980009, 9998, 9999, 250.5, DATE_SUB(NOW(), INTERVAL 22 DAY), 9999, 1, 0),
(99980010, 9998, 9999, 248.9, DATE_SUB(NOW(), INTERVAL 21 DAY), 9999, 1, 0),
(99980011, 9998, 9999, 251.8, DATE_SUB(NOW(), INTERVAL 20 DAY), 9999, 1, 0),
(99980012, 9998, 9999, 249.2, DATE_SUB(NOW(), INTERVAL 19 DAY), 9999, 1, 0),
(99980013, 9998, 9999, 252.6, DATE_SUB(NOW(), INTERVAL 18 DAY), 9999, 1, 0),
(99980014, 9998, 9999, 247.8, DATE_SUB(NOW(), INTERVAL 17 DAY), 9999, 1, 0),
(99980015, 9998, 9999, 250.1, DATE_SUB(NOW(), INTERVAL 16 DAY), 9999, 1, 0);

-- Cholesterol L1 (batch 9997) - target 120.0, SD 6.0
INSERT IGNORE INTO results (result_id, batch_id, workstation_id, result, received, org_id, status, is_delete) VALUES
(99970001, 9997, 9999, 119.2, DATE_SUB(NOW(), INTERVAL 30 DAY), 9999, 1, 0),
(99970002, 9997, 9999, 121.5, DATE_SUB(NOW(), INTERVAL 28 DAY), 9999, 1, 0),
(99970003, 9997, 9999, 118.3, DATE_SUB(NOW(), INTERVAL 26 DAY), 9999, 1, 0),
(99970004, 9997, 9999, 122.1, DATE_SUB(NOW(), INTERVAL 24 DAY), 9999, 1, 0),
(99970005, 9997, 9999, 119.8, DATE_SUB(NOW(), INTERVAL 22 DAY), 9999, 1, 0),
(99970006, 9997, 9999, 120.5, DATE_SUB(NOW(), INTERVAL 20 DAY), 9999, 1, 0),
(99970007, 9997, 9999, 117.9, DATE_SUB(NOW(), INTERVAL 18 DAY), 9999, 1, 0),
(99970008, 9997, 9999, 121.2, DATE_SUB(NOW(), INTERVAL 16 DAY), 9999, 1, 0),
(99970009, 9997, 9999, 119.5, DATE_SUB(NOW(), INTERVAL 14 DAY), 9999, 1, 0),
(99970010, 9997, 9999, 120.8, DATE_SUB(NOW(), INTERVAL 12 DAY), 9999, 1, 0),
(99970011, 9997, 9999, 118.6, DATE_SUB(NOW(), INTERVAL 10 DAY), 9999, 1, 0),
(99970012, 9997, 9999, 121.9, DATE_SUB(NOW(), INTERVAL 8 DAY), 9999, 1, 0),
(99970013, 9997, 9999, 119.1, DATE_SUB(NOW(), INTERVAL 6 DAY), 9999, 1, 0),
(99970014, 9997, 9999, 120.3, DATE_SUB(NOW(), INTERVAL 4 DAY), 9999, 1, 0),
(99970015, 9997, 9999, 118.8, DATE_SUB(NOW(), INTERVAL 2 DAY), 9999, 1, 0);

-- AST L1 on Analyzer 2 (batch 9995) - target 35.0, SD 3.5
INSERT IGNORE INTO results (result_id, batch_id, workstation_id, result, received, org_id, status, is_delete) VALUES
(99950001, 9995, 9998, 34.5, DATE_SUB(NOW(), INTERVAL 30 DAY), 9999, 1, 0),
(99950002, 9995, 9998, 36.2, DATE_SUB(NOW(), INTERVAL 27 DAY), 9999, 1, 0),
(99950003, 9995, 9998, 33.8, DATE_SUB(NOW(), INTERVAL 24 DAY), 9999, 1, 0),
(99950004, 9995, 9998, 35.5, DATE_SUB(NOW(), INTERVAL 21 DAY), 9999, 1, 0),
(99950005, 9995, 9998, 34.2, DATE_SUB(NOW(), INTERVAL 18 DAY), 9999, 1, 0),
(99950006, 9995, 9998, 36.0, DATE_SUB(NOW(), INTERVAL 15 DAY), 9999, 1, 0),
(99950007, 9995, 9998, 34.8, DATE_SUB(NOW(), INTERVAL 12 DAY), 9999, 1, 0),
(99950008, 9995, 9998, 35.3, DATE_SUB(NOW(), INTERVAL 9 DAY), 9999, 1, 0),
(99950009, 9995, 9998, 33.9, DATE_SUB(NOW(), INTERVAL 6 DAY), 9999, 1, 0),
(99950010, 9995, 9998, 35.7, DATE_SUB(NOW(), INTERVAL 3 DAY), 9999, 1, 0);

-- ============================================================================
-- SAMPLE NOTE
-- ============================================================================

INSERT IGNORE INTO notes (note_id, result_id, action_id, description, status, created_by, created_at) VALUES
(9999, 99990019, 999, 'Valore ripetuto dopo manutenzione', 1, 9999, DATE_SUB(NOW(), INTERVAL 12 DAY));

-- ============================================================================
-- SUMMARY
-- ============================================================================
--
-- Utenti creati:
--   - admin_demo / demo123  (role 0 - Admin)
--   - tecnico_demo / demo123 (role 5 - Technician)
--   - viewer_demo / demo123  (role 6 - Viewer)
--
-- Lab: Laboratorio Demo (org_id 9999)
--
-- Workstations:
--   - Analyzer Demo 1 (9999) - Glucose, Cholesterol
--   - Analyzer Demo 2 (9998) - AST, ALT
--
-- URL di test:
--   http://localhost/biovarase/dashboard?lab_id=9999
--   http://localhost/biovarase/charts?lab_id=9999&workstation_id=9999
--
