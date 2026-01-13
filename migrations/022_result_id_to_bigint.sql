-- Migration 022: Change result_id to BIGINT UNSIGNED
-- Date: 2026-01-13
-- Purpose: Maximum capacity for result_id (18 quintillion vs 4 billion)
--
-- Current: INT(11) UNSIGNED - max 4,294,967,295
-- New: BIGINT UNSIGNED - max 18,446,744,073,709,551,615
--
-- Also update audit_results.result_id to match

-- Step 1: Modify results table
ALTER TABLE results
MODIFY COLUMN result_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT;

-- Step 2: Modify audit_results table to match
ALTER TABLE audit_results
MODIFY COLUMN result_id BIGINT UNSIGNED NOT NULL;

-- Verification:
-- DESCRIBE results;
-- DESCRIBE audit_results;
