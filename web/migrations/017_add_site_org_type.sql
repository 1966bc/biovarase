-- Migration 017: Add 'site' org_type for physical hospital locations
-- Date: 2026-01-11
-- Purpose: Add hospital/site level between region and lab
--
-- Updated hierarchy:
--   Italia (country)
--     └── Lazio (region)
--           └── Azienda Ospedaliera San Camillo (site)  <-- NEW
--                 └── Laboratorio Analisi (lab)
--                       └── Chimica Clinica (section)
--
-- Note: 'authority' (ASL) can be added later if needed

-- Step 1: Modify ENUM to include 'site'
ALTER TABLE organizations
MODIFY COLUMN org_type ENUM('country', 'region', 'site', 'lab', 'section') NOT NULL;

-- Step 2: Verification
-- Check the updated column definition:
-- SHOW COLUMNS FROM organizations LIKE 'org_type';

-- Example: Insert a site under a region
-- INSERT INTO organizations (parent_id, org_type, description, status)
-- VALUES (
--     (SELECT org_id FROM organizations WHERE org_type = 'region' AND description LIKE '%Lazio%'),
--     'site',
--     'Azienda Ospedaliera San Camillo',
--     1
-- );

-- Example: Move existing labs under the new site
-- UPDATE organizations
-- SET parent_id = (SELECT org_id FROM organizations WHERE org_type = 'site' AND description LIKE '%San Camillo%')
-- WHERE org_type = 'lab' AND parent_id = <old_region_id>;
