-- Migration 013: Add org_id to tables that reference the hierarchy
-- Date: 2026-01-10
-- Purpose: Replace site_id/lab_id/section_id with unified org_id
--
-- Tables to update:
--   - users (replace lab_id with org_id)
--   - workstations (replace section_id with org_id)
--   - batches (replace lab_id with org_id)
--   - results (replace lab_id with org_id)
--   - test_methods (replace section_id, lab_id with org_id)
--   - categories (replace lab_id with org_id)
--   - audit_batches (replace lab_id with org_id)
--   - audit_results (replace lab_id with org_id)

-- ============================================================
-- USERS
-- ============================================================
ALTER TABLE users
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to organizations - defines user scope'
AFTER role;

-- Migrate: users.lab_id -> org_id (lab level)
UPDATE users u
JOIN _org_migration_map m ON m.old_table = 'labs' AND m.old_id = u.lab_id
SET u.org_id = m.new_org_id
WHERE u.lab_id IS NOT NULL;

-- Users with lab_id=NULL remain org_id=NULL (app admins)

CREATE INDEX idx_users_org_id ON users(org_id);

ALTER TABLE users
ADD CONSTRAINT fk_users_org
FOREIGN KEY (org_id) REFERENCES organizations(org_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================
-- WORKSTATIONS
-- ============================================================
ALTER TABLE workstations
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to organizations (section level)'
AFTER section_id;

-- Migrate: workstations.section_id -> org_id
UPDATE workstations w
JOIN _org_migration_map m ON m.old_table = 'sections' AND m.old_id = w.section_id
SET w.org_id = m.new_org_id;

CREATE INDEX idx_workstations_org_id ON workstations(org_id);

ALTER TABLE workstations
ADD CONSTRAINT fk_workstations_org
FOREIGN KEY (org_id) REFERENCES organizations(org_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================
-- BATCHES
-- ============================================================
ALTER TABLE batches
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to organizations (lab level)'
AFTER lab_id;

-- Migrate: batches.lab_id -> org_id
UPDATE batches b
JOIN _org_migration_map m ON m.old_table = 'labs' AND m.old_id = b.lab_id
SET b.org_id = m.new_org_id;

CREATE INDEX idx_batches_org_id ON batches(org_id);

ALTER TABLE batches
ADD CONSTRAINT fk_batches_org
FOREIGN KEY (org_id) REFERENCES organizations(org_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================
-- RESULTS
-- ============================================================
ALTER TABLE results
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to organizations (lab level)'
AFTER lab_id;

-- Migrate: results.lab_id -> org_id
UPDATE results r
JOIN _org_migration_map m ON m.old_table = 'labs' AND m.old_id = r.lab_id
SET r.org_id = m.new_org_id;

CREATE INDEX idx_results_org_id ON results(org_id);

ALTER TABLE results
ADD CONSTRAINT fk_results_org
FOREIGN KEY (org_id) REFERENCES organizations(org_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================
-- TEST_METHODS
-- ============================================================
ALTER TABLE test_methods
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to organizations (section level)'
AFTER lab_id;

-- Migrate: test_methods.section_id -> org_id (section level is more specific)
UPDATE test_methods tm
JOIN _org_migration_map m ON m.old_table = 'sections' AND m.old_id = tm.section_id
SET tm.org_id = m.new_org_id;

CREATE INDEX idx_test_methods_org_id ON test_methods(org_id);

ALTER TABLE test_methods
ADD CONSTRAINT fk_test_methods_org
FOREIGN KEY (org_id) REFERENCES organizations(org_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================
-- CATEGORIES
-- ============================================================
ALTER TABLE categories
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to organizations (lab level)'
AFTER lab_id;

-- Migrate: categories.lab_id -> org_id
UPDATE categories c
JOIN _org_migration_map m ON m.old_table = 'labs' AND m.old_id = c.lab_id
SET c.org_id = m.new_org_id
WHERE c.lab_id IS NOT NULL;

CREATE INDEX idx_categories_org_id ON categories(org_id);

ALTER TABLE categories
ADD CONSTRAINT fk_categories_org
FOREIGN KEY (org_id) REFERENCES organizations(org_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================
-- AUDIT_BATCHES
-- ============================================================
ALTER TABLE audit_batches
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'Organization ID for audit filtering'
AFTER lab_id;

-- Migrate: audit_batches.lab_id -> org_id
UPDATE audit_batches ab
JOIN _org_migration_map m ON m.old_table = 'labs' AND m.old_id = ab.lab_id
SET ab.org_id = m.new_org_id
WHERE ab.lab_id IS NOT NULL;

CREATE INDEX idx_audit_batches_org_id ON audit_batches(org_id);

-- ============================================================
-- AUDIT_RESULTS
-- ============================================================
ALTER TABLE audit_results
ADD COLUMN org_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'Organization ID for audit filtering'
AFTER lab_id;

-- Migrate: audit_results.lab_id -> org_id
UPDATE audit_results ar
JOIN _org_migration_map m ON m.old_table = 'labs' AND m.old_id = ar.lab_id
SET ar.org_id = m.new_org_id
WHERE ar.lab_id IS NOT NULL;

CREATE INDEX idx_audit_results_org_id ON audit_results(org_id);

-- Verification:
-- SELECT 'users' AS tbl, COUNT(*) AS total, SUM(org_id IS NULL) AS nulls FROM users
-- UNION ALL SELECT 'workstations', COUNT(*), SUM(org_id IS NULL) FROM workstations
-- UNION ALL SELECT 'batches', COUNT(*), SUM(org_id IS NULL) FROM batches
-- UNION ALL SELECT 'results', COUNT(*), SUM(org_id IS NULL) FROM results
-- UNION ALL SELECT 'test_methods', COUNT(*), SUM(org_id IS NULL) FROM test_methods;
