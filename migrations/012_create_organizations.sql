-- Migration 012: Create organizations table for flexible hierarchy
-- Date: 2026-01-10
-- Purpose: Replace countries/sites/labs/sections with single hierarchical table
--
-- Hierarchy example:
--   Italia (country)
--     └── Lazio (region)
--           └── Ospedale San Camillo (lab)
--                 └── Chimica Clinica (section)
--
-- Benefits:
--   - Flexible depth (can add levels without schema changes)
--   - Single org_id field for all scopes
--   - Easy recursive queries with CTEs

-- Step 1: Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    parent_id INT(11) UNSIGNED DEFAULT NULL COMMENT 'FK to parent org, NULL = root',
    org_type ENUM('country', 'region', 'lab', 'section') NOT NULL,
    code VARCHAR(20) DEFAULT NULL COMMENT 'Short code (ITA, LAZ, etc.)',
    description VARCHAR(255) NOT NULL,
    status TINYINT(1) UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (org_id),
    KEY idx_organizations_parent (parent_id),
    KEY idx_organizations_type (org_type),
    CONSTRAINT fk_organizations_parent
        FOREIGN KEY (parent_id) REFERENCES organizations(org_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Step 2: Insert default country (Italy) as root
INSERT INTO organizations (org_id, parent_id, org_type, code, description, status)
VALUES (1, NULL, 'country', 'ITA', 'Italia', 1);

-- Step 3: Migrate existing sites as regions under Italy
-- Note: sites.description comes from suppliers table via supplier_id
INSERT INTO organizations (org_id, parent_id, org_type, code, description, status)
SELECT
    s.site_id + 1000 AS org_id,  -- Offset to avoid PK conflicts
    1 AS parent_id,               -- Italy
    'region' AS org_type,
    NULL AS code,
    sup.description AS description,
    s.status
FROM sites s
JOIN suppliers sup ON s.supplier_id = sup.supplier_id;

-- Step 4: Migrate existing labs under their respective sites (now regions)
INSERT INTO organizations (org_id, parent_id, org_type, code, description, status)
SELECT
    lab_id + 2000 AS org_id,           -- Offset to avoid PK conflicts
    site_id + 1000 AS parent_id,       -- Points to migrated site
    'lab' AS org_type,
    NULL AS code,
    description,
    status
FROM labs;

-- Step 5: Migrate existing sections under their respective labs
INSERT INTO organizations (org_id, parent_id, org_type, code, description, status)
SELECT
    section_id + 3000 AS org_id,       -- Offset to avoid PK conflicts
    lab_id + 2000 AS parent_id,        -- Points to migrated lab
    'section' AS org_type,
    NULL AS code,
    description,
    status
FROM sections;

-- Step 6: Create mapping table for old_id -> new org_id (for FK migration)
CREATE TABLE IF NOT EXISTS _org_migration_map (
    old_table VARCHAR(20) NOT NULL,
    old_id INT(11) UNSIGNED NOT NULL,
    new_org_id INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (old_table, old_id),
    KEY idx_new_org_id (new_org_id)
) ENGINE=InnoDB;

-- Populate mapping
INSERT INTO _org_migration_map (old_table, old_id, new_org_id)
SELECT 'sites', site_id, site_id + 1000 FROM sites
UNION ALL
SELECT 'labs', lab_id, lab_id + 2000 FROM labs
UNION ALL
SELECT 'sections', section_id, section_id + 3000 FROM sections;

-- Verification:
-- SELECT * FROM organizations ORDER BY org_id;
-- SELECT o.*, p.description AS parent_name
-- FROM organizations o
-- LEFT JOIN organizations p ON o.parent_id = p.org_id
-- ORDER BY o.org_id;
