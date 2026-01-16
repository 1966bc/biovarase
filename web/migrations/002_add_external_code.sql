-- Migration: 002_add_external_code
-- Date: 2026-01-06
-- Description: Add external_code column to workstation_test_methods
--              for vendor-agnostic workstation integration (Abbott, Siemens, etc.)
--
-- Usage:
--   mysql -u biovarase -p biovarase < sql/migrations/002_add_external_code.sql
--
-- Rollback:
--   ALTER TABLE workstation_test_methods DROP COLUMN external_code;
--   ALTER TABLE workstation_test_methods DROP INDEX uk_wtm_external;

-- Add external_code column
-- This stores the test code as named by the workstation/vendor
-- e.g., "BHCG" for Abbott, "HCG" for Siemens, etc.
ALTER TABLE workstation_test_methods
ADD COLUMN external_code VARCHAR(50) DEFAULT NULL
COMMENT 'Test code from workstation export (e.g., BHCG, FT4)';

-- Add unique constraint: same external_code cannot be mapped twice on same workstation
-- This prevents duplicate mappings and ensures unambiguous import
ALTER TABLE workstation_test_methods
ADD UNIQUE INDEX uk_wtm_external (workstation_id, external_code);

-- Verification
SELECT
    'Migration 002_add_external_code completed successfully' AS status,
    COUNT(*) AS existing_mappings
FROM workstation_test_methods;
