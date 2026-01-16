-- Migration 026: Add created_by to results table for permission control
-- Date: 2026-01
--
-- This migration:
-- 1. Adds created_by field to track who entered the result
-- 2. For manual entries: created_by = user who entered
-- 3. For instrument data (Abbott): created_by = NULL (team can modify)
-- 4. Permission logic:
--    - Role 0-3 (Admin hierarchy): can modify any result in their org scope
--    - Role 4-5 (Superuser/Technician): can modify if:
--      a) created_by = current user (they created it), OR
--      b) created_by IS NULL AND same section (instrument data)

-- Add created_by column (FK to users)
ALTER TABLE results
ADD COLUMN created_by INT UNSIGNED NULL AFTER is_delete;

-- Add foreign key constraint
ALTER TABLE results
ADD CONSTRAINT fk_results_created_by
FOREIGN KEY (created_by) REFERENCES users(user_id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- Add index for efficient filtering by creator
CREATE INDEX idx_results_created_by ON results(created_by);

-- Note: Existing results will have created_by = NULL
-- This is correct for Abbott-imported data (instrument results)
-- Manual entries going forward will have created_by set

-- Also add created_by to audit_results for complete audit trail
ALTER TABLE audit_results
ADD COLUMN created_by INT UNSIGNED NULL AFTER is_delete;
