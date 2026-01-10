-- Migration 012: Create countries table for international hierarchy
-- Date: 2026-01-10
-- Purpose: Add top-level geographic entity for multi-country deployment

-- Step 1: Create countries table
CREATE TABLE IF NOT EXISTS countries (
    country_id SMALLINT(5) UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(3) NOT NULL COMMENT 'ISO 3166-1 alpha-3 code (ITA, FRA, ESP)',
    description VARCHAR(100) NOT NULL COMMENT 'Country name',
    status TINYINT(1) UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (country_id),
    UNIQUE KEY uk_countries_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Step 2: Insert default country (Italy)
INSERT INTO countries (code, description, status) VALUES ('ITA', 'Italia', 1);

-- Step 3: Add country_id to sites table
ALTER TABLE sites
ADD COLUMN country_id SMALLINT(5) UNSIGNED DEFAULT NULL
COMMENT 'FK to countries.country_id'
AFTER site_id;

-- Step 4: Set existing sites to Italy
UPDATE sites SET country_id = 1 WHERE country_id IS NULL;

-- Step 5: Add index
CREATE INDEX idx_sites_country_id ON sites(country_id);

-- Step 6: Add foreign key constraint
ALTER TABLE sites
ADD CONSTRAINT fk_sites_country
FOREIGN KEY (country_id) REFERENCES countries(country_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- Verification:
-- SELECT s.site_id, c.description AS country, s.description AS site FROM sites s JOIN countries c ON s.country_id = c.country_id;
