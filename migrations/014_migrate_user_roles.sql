-- Migration 014: Migrate existing user roles to new hierarchy
-- Date: 2026-01-10
-- Purpose: Convert old role numbers to new international hierarchy
--
-- OLD ROLES:
--   0 = Admin (with lab_id=NULL was "regional", with lab_id=X was "local")
--   1 = Superuser
--   2 = Technician
--   3,4,5 = Various viewer/guest roles
--
-- NEW ROLES:
--   0 = App Admin (global)
--   1 = Country Admin
--   2 = Regional Admin
--   3 = Lab Admin
--   4 = Superuser
--   5 = Technician
--   6 = Viewer

-- Step 1: Migrate roles (MUST be done in correct order to avoid conflicts)
-- Process from highest to lowest old role number

-- Old role=5 (viewer variant) → New role=6 (Viewer)
UPDATE users SET role = 6 WHERE role = 5;

-- Old role=4 (viewer variant) → New role=6 (Viewer)
UPDATE users SET role = 6 WHERE role = 4;

-- Old role=3 (autologin/guest) → New role=6 (Viewer)
UPDATE users SET role = 6 WHERE role = 3;

-- Old role=2 (Technician) → New role=5 (Technician)
UPDATE users SET role = 5 WHERE role = 2;

-- Old role=1 (Superuser) → New role=4 (Superuser)
UPDATE users SET role = 4 WHERE role = 1;

-- Old role=0 with lab_id IS NOT NULL → New role=3 (Lab Admin)
UPDATE users SET role = 3 WHERE role = 0 AND lab_id IS NOT NULL;

-- Old role=0 with lab_id IS NULL → New role=0 (App Admin) - stays the same
-- These are the global admins, they keep role=0

-- Verification:
-- SELECT user_id, nickname, role, country_id, site_id, lab_id,
--   CASE role
--     WHEN 0 THEN 'App Admin'
--     WHEN 1 THEN 'Country Admin'
--     WHEN 2 THEN 'Regional Admin'
--     WHEN 3 THEN 'Lab Admin'
--     WHEN 4 THEN 'Superuser'
--     WHEN 5 THEN 'Technician'
--     WHEN 6 THEN 'Viewer'
--   END AS role_name
-- FROM users ORDER BY role;
