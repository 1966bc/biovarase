-- Migration 016: Create App Admin user
-- Date: 2026-01-10
-- Purpose: Create a global administrator user for the application
--
-- This user has:
--   - role = 0 (App Admin)
--   - org_id = NULL (global scope, sees all organizations)
--   - lab_id = NULL (no lab restriction)
--
-- Default password: 'admin123' (bcrypt hashed)
-- IMPORTANT: Change this password immediately after first login!

-- Check if admin user already exists
SET @admin_exists = (SELECT COUNT(*) FROM users WHERE nickname = 'admin');

-- Only insert if admin doesn't exist
INSERT INTO users (
    last_name,
    first_name,
    nickname,
    pswrd,
    role,
    org_id,
    lab_id,
    elapsing_time,
    enable_time,
    status
)
SELECT
    'Administrator',
    'System',
    'admin',
    -- bcrypt hash of 'admin123' with cost 12
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4mOQKj6xJ2nKEOyK',
    0,      -- App Admin role
    NULL,   -- Global scope (no org restriction)
    NULL,   -- No lab restriction
    30,     -- 30 minutes logout time
    1,      -- Enable timeout
    1       -- Active status
FROM DUAL
WHERE @admin_exists = 0;

-- If admin already exists, update to ensure correct role and scope
UPDATE users
SET role = 0,
    org_id = NULL,
    lab_id = NULL,
    status = 1
WHERE nickname = 'admin';

-- Verification
SELECT
    user_id,
    last_name,
    first_name,
    nickname,
    role,
    CASE role
        WHEN 0 THEN 'App Admin'
        WHEN 1 THEN 'Country Admin'
        WHEN 2 THEN 'Regional Admin'
        WHEN 3 THEN 'Lab Admin'
        WHEN 4 THEN 'Superuser'
        WHEN 5 THEN 'Technician'
        WHEN 6 THEN 'Viewer'
    END AS role_name,
    org_id,
    lab_id,
    status
FROM users
WHERE nickname = 'admin';

-- Note: To reset password to 'admin123', run:
-- UPDATE users SET pswrd = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4mOQKj6xJ2nKEOyK'
-- WHERE nickname = 'admin';
