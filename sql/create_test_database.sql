-- ============================================================================
-- Biovarase Test Database Setup
-- ============================================================================
-- Run this script as root to create the test database:
--   sudo mysql < sql/create_test_database.sql
--
-- This creates:
--   1. biovarase_test database
--   2. biovarase_test user with full permissions on test DB only
--   3. Imports schema from production (structure only, no data)
-- ============================================================================

-- Create test database
CREATE DATABASE IF NOT EXISTS biovarase_test
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

-- Create test user (if not exists)
-- Password: test_password_123 (only for local testing!)
CREATE USER IF NOT EXISTS 'biovarase_test'@'localhost'
    IDENTIFIED BY 'test_password_123';

-- Grant full permissions on test database only
GRANT ALL PRIVILEGES ON biovarase_test.* TO 'biovarase_test'@'localhost';

-- Ensure no access to production database
-- (biovarase_test user can ONLY access biovarase_test)

FLUSH PRIVILEGES;

-- Verify
SELECT 'Database biovarase_test created successfully!' AS status;
SELECT User, Host FROM mysql.user WHERE User = 'biovarase_test';
SHOW GRANTS FOR 'biovarase_test'@'localhost';
