-- Migration 015: Cleanup old hierarchy columns and tables
-- Date: 2026-01-10
-- Purpose: Remove old site_id/lab_id/section_id columns after org_id migration
--
-- WARNING: Run this ONLY after:
--   1. Verifying all org_id values are correctly populated
--   2. Updating all application code to use org_id
--   3. Testing thoroughly in development
--
-- This migration is DESTRUCTIVE and cannot be easily rolled back!

-- ============================================================
-- PHASE 1: DROP FOREIGN KEYS (must do before dropping columns)
-- ============================================================

-- Users: drop old lab_id FK
ALTER TABLE users DROP FOREIGN KEY IF EXISTS fk_users_lab;

-- Batches: drop old lab_id FK
ALTER TABLE batches DROP FOREIGN KEY IF EXISTS fk_batches_lab;

-- Results: drop old lab_id FK
ALTER TABLE results DROP FOREIGN KEY IF EXISTS fk_results_lab;

-- Test_methods: drop old lab_id FK and section_id FK
ALTER TABLE test_methods DROP FOREIGN KEY IF EXISTS fk_test_methods_lab;
ALTER TABLE test_methods DROP FOREIGN KEY IF EXISTS fk_test_methods_section;

-- Categories: drop old lab_id FK
ALTER TABLE categories DROP FOREIGN KEY IF EXISTS fk_categories_lab;

-- Workstations: drop old section_id FK
ALTER TABLE workstations DROP FOREIGN KEY IF EXISTS fk_workstations_section;

-- Labs: drop site_id FK
ALTER TABLE labs DROP FOREIGN KEY IF EXISTS fk_labs_site;

-- Sections: drop lab_id FK
ALTER TABLE sections DROP FOREIGN KEY IF EXISTS fk_sections_lab;

-- Sites: (no FK to drop, but will drop the table)

-- ============================================================
-- PHASE 2: DROP OLD COLUMNS
-- ============================================================

-- Users: drop lab_id
ALTER TABLE users DROP COLUMN IF EXISTS lab_id;

-- Workstations: drop section_id
ALTER TABLE workstations DROP COLUMN IF EXISTS section_id;

-- Batches: drop lab_id
ALTER TABLE batches DROP COLUMN IF EXISTS lab_id;

-- Results: drop lab_id
ALTER TABLE results DROP COLUMN IF EXISTS lab_id;

-- Test_methods: drop section_id and lab_id
ALTER TABLE test_methods DROP COLUMN IF EXISTS section_id;
ALTER TABLE test_methods DROP COLUMN IF EXISTS lab_id;

-- Categories: drop lab_id
ALTER TABLE categories DROP COLUMN IF EXISTS lab_id;

-- Audit tables: drop lab_id (keep for historical reference? or drop?)
-- ALTER TABLE audit_batches DROP COLUMN IF EXISTS lab_id;
-- ALTER TABLE audit_results DROP COLUMN IF EXISTS lab_id;

-- ============================================================
-- PHASE 3: DROP OLD TABLES
-- ============================================================

-- Drop migration mapping table (no longer needed)
DROP TABLE IF EXISTS _org_migration_map;

-- Drop old hierarchy tables (IN REVERSE ORDER due to FK dependencies)
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS labs;
DROP TABLE IF EXISTS sites;

-- Note: countries table was never created (we went straight to organizations)

-- ============================================================
-- PHASE 4: RENAME org_id INDEXES (optional, for clarity)
-- ============================================================

-- These are optional cosmetic changes
-- ALTER TABLE users RENAME INDEX idx_users_org_id TO idx_users_scope;

-- ============================================================
-- VERIFICATION
-- ============================================================
-- Run these queries to verify cleanup:
--
-- SHOW TABLES LIKE 'sites';      -- Should return empty
-- SHOW TABLES LIKE 'labs';       -- Should return empty
-- SHOW TABLES LIKE 'sections';   -- Should return empty
--
-- DESCRIBE users;                -- Should NOT have lab_id
-- DESCRIBE batches;              -- Should NOT have lab_id
-- DESCRIBE results;              -- Should NOT have lab_id
-- DESCRIBE workstations;         -- Should NOT have section_id
-- DESCRIBE test_methods;         -- Should NOT have section_id, lab_id
--
-- SELECT * FROM organizations;   -- Should have all hierarchy data
