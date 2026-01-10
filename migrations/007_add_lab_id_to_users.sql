-- ============================================================================
-- Migration 007: Add lab_id to users table
-- ============================================================================
-- Purpose: Assign users to laboratories for automatic context loading at login
-- Priority: HIGH
-- Dependencies: None
-- ============================================================================

USE biovarase;

-- ============================================================================
-- Step 1: Add lab_id column to users
-- ============================================================================

SELECT 'Adding lab_id column to users table...' AS status;

ALTER TABLE users
  ADD COLUMN lab_id TINYINT(3) UNSIGNED DEFAULT NULL
  AFTER role;

-- ============================================================================
-- Step 2: Add foreign key constraint
-- ============================================================================

SELECT 'Adding foreign key constraint...' AS status;

ALTER TABLE users
  ADD CONSTRAINT fk_users_lab_id
  FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
  ON DELETE SET NULL
  ON UPDATE CASCADE;

-- ============================================================================
-- Step 3: Add index for performance
-- ============================================================================

SELECT 'Adding index on lab_id...' AS status;

ALTER TABLE users
  ADD INDEX idx_users_lab_id (lab_id);

-- ============================================================================
-- Step 4: Update existing users with default lab_id
-- ============================================================================
-- Assign all non-admin users to lab_id = 1 (adjust as needed)
-- Admin users (role = 0) keep lab_id = NULL for multi-lab access

SELECT 'Updating existing users with default lab_id...' AS status;

UPDATE users
SET lab_id = 1
WHERE role != 0 AND lab_id IS NULL;

-- ============================================================================
-- Verify changes
-- ============================================================================

SELECT 'Verifying users table structure...' AS status;

SELECT user_id, login, role, lab_id
FROM users
ORDER BY role, login;

SELECT 'Migration 007 completed successfully!' AS status;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
/*
USE biovarase;

ALTER TABLE users DROP FOREIGN KEY fk_users_lab_id;
ALTER TABLE users DROP INDEX idx_users_lab_id;
ALTER TABLE users DROP COLUMN lab_id;
*/
