-- Migration 011: Add lab_id to test_methods table for direct multi-tenant filtering
-- Date: 2026-01-10
-- Purpose: Denormalize lab_id for explicit tenant isolation
--
-- Before: test_methods → section_id → sections.lab_id (requires join)
-- After:  test_methods.lab_id (direct filtering)

-- Step 1: Add lab_id column (nullable initially for safe migration)
ALTER TABLE test_methods
ADD COLUMN lab_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to labs.lab_id for multi-tenant isolation'
AFTER section_id;

-- Step 2: Populate lab_id from sections table
UPDATE test_methods tm
INNER JOIN sections s ON tm.section_id = s.section_id
SET tm.lab_id = s.lab_id
WHERE tm.lab_id IS NULL;

-- Step 3: Add index for filtering performance
CREATE INDEX idx_test_methods_lab_id ON test_methods(lab_id);

-- Step 4: Add composite index for common queries
CREATE INDEX idx_test_methods_lab_status ON test_methods(lab_id, status);

-- Step 5: Add foreign key constraint
ALTER TABLE test_methods
ADD CONSTRAINT fk_test_methods_lab
FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- Step 6: Make NOT NULL after data is populated
-- IMPORTANT: Run this only after verifying all rows have lab_id set
-- ALTER TABLE test_methods MODIFY COLUMN lab_id INT(11) UNSIGNED NOT NULL;

-- Verification query (run manually):
-- SELECT COUNT(*) AS orphan_test_methods FROM test_methods WHERE lab_id IS NULL;
-- Should return 0 before making NOT NULL
