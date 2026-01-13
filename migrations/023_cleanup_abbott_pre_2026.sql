-- Migration 023: Cleanup Abbott data before 2026-01-01
-- Date: 2026-01-13
-- Purpose: Remove old Abbott data and reset autoincrement
--
-- WARNING: This deletes data! Make a backup first:
--   mysqldump -u root -p biovarase > backup_before_cleanup_$(date +%Y%m%d_%H%M%S).sql
--
-- Manual results (operator_code IS NULL) are PRESERVED.

-- Step 1: Check what will be deleted (DRY RUN - just SELECT)
SELECT 'Results Abbott to delete' AS action, COUNT(*) AS cnt
FROM results WHERE operator_code IS NOT NULL AND received < '2026-01-01';

SELECT 'Batches to delete (only pre-2026 Abbott data)' AS action, COUNT(*) AS cnt
FROM batches b
WHERE EXISTS (SELECT 1 FROM results r WHERE r.batch_id = b.batch_id AND r.operator_code IS NOT NULL AND r.received < '2026-01-01')
AND NOT EXISTS (SELECT 1 FROM results r WHERE r.batch_id = b.batch_id AND (r.received >= '2026-01-01' OR r.operator_code IS NULL));

-- Step 2: Delete old Abbott results (preserves manual results!)
DELETE FROM results
WHERE operator_code IS NOT NULL
AND received < '2026-01-01';

-- Step 3: Delete orphan batches (batches with no remaining results)
DELETE FROM batches
WHERE batch_id NOT IN (SELECT DISTINCT batch_id FROM results);

-- Step 4: Optimize tables and reset autoincrement
-- Note: AUTO_INCREMENT can only be set >= current max,
-- so we set it to max+1 to clean up gaps
SET @max_result := (SELECT COALESCE(MAX(result_id), 0) + 1 FROM results);
SET @max_batch := (SELECT COALESCE(MAX(batch_id), 0) + 1 FROM batches);

-- Use prepared statements for dynamic ALTER
SET @sql_r = CONCAT('ALTER TABLE results AUTO_INCREMENT = ', @max_result);
SET @sql_b = CONCAT('ALTER TABLE batches AUTO_INCREMENT = ', @max_batch);
PREPARE stmt FROM @sql_r; EXECUTE stmt; DEALLOCATE PREPARE stmt;
PREPARE stmt FROM @sql_b; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Step 5: Verify
SELECT 'Remaining results' AS info, COUNT(*) AS cnt, MIN(result_id) AS min_id, MAX(result_id) AS max_id FROM results
UNION ALL
SELECT 'Remaining batches', COUNT(*), MIN(batch_id), MAX(batch_id) FROM batches;
