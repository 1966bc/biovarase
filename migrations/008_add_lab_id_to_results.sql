-- Migration 008: Add lab_id to results table for direct multi-tenant filtering
-- Date: 2026-01-10
-- Purpose: Denormalize lab_id for explicit tenant isolation and audit performance
--
-- Before: results → batch_id → batches.lab_id (requires join)
-- After:  results.lab_id (direct filtering)

-- Step 1: Add lab_id column (nullable initially for safe migration)
ALTER TABLE results
ADD COLUMN lab_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to labs.lab_id for multi-tenant isolation'
AFTER batch_id;

-- Step 2: Populate lab_id from batches table
UPDATE results r
INNER JOIN batches b ON r.batch_id = b.batch_id
SET r.lab_id = b.lab_id
WHERE r.lab_id IS NULL;

-- Step 3: Add index for filtering performance
CREATE INDEX idx_results_lab_id ON results(lab_id);

-- Step 4: Add composite index for common queries
CREATE INDEX idx_results_lab_status ON results(lab_id, status, is_delete);

-- Step 5: Add foreign key constraint
ALTER TABLE results
ADD CONSTRAINT fk_results_lab
FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- Step 6: Make NOT NULL after data is populated
-- IMPORTANT: Run this only after verifying all rows have lab_id set
-- ALTER TABLE results MODIFY COLUMN lab_id INT(11) UNSIGNED NOT NULL;

-- Verification query (run manually):
-- SELECT COUNT(*) AS orphan_results FROM results WHERE lab_id IS NULL;
-- Should return 0 before making NOT NULL
