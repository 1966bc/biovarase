-- Migration 013: Add country_id and site_id to users for hierarchical access control
-- Date: 2026-01-10
-- Purpose: Enable Country Admin and Regional Admin roles

-- Step 1: Add country_id to users
ALTER TABLE users
ADD COLUMN country_id SMALLINT(5) UNSIGNED DEFAULT NULL
COMMENT 'FK to countries - for Country Admin scope'
AFTER role;

-- Step 2: Add site_id to users
ALTER TABLE users
ADD COLUMN site_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to sites - for Regional Admin scope'
AFTER country_id;

-- Step 3: Add indexes
CREATE INDEX idx_users_country_id ON users(country_id);
CREATE INDEX idx_users_site_id ON users(site_id);

-- Step 4: Add foreign key constraints
ALTER TABLE users
ADD CONSTRAINT fk_users_country
FOREIGN KEY (country_id) REFERENCES countries(country_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE users
ADD CONSTRAINT fk_users_site
FOREIGN KEY (site_id) REFERENCES sites(site_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- Note: lab_id FK already exists from migration 007

-- User scope logic:
-- role=0 (App Admin):      country_id=NULL, site_id=NULL, lab_id=NULL → sees everything
-- role=1 (Country Admin):  country_id=X,    site_id=NULL, lab_id=NULL → sees all in country X
-- role=2 (Regional Admin): country_id=NULL, site_id=X,    lab_id=NULL → sees all in site/region X
-- role=3 (Lab Admin):      country_id=NULL, site_id=NULL, lab_id=X    → sees only lab X
-- role=4,5,6:              country_id=NULL, site_id=NULL, lab_id=X    → sees only lab X

-- Verification:
-- SELECT user_id, nickname, role, country_id, site_id, lab_id FROM users;
