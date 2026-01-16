-- Migration: Add lab_id to categories table for multi-tenant support
-- Date: 2026-01-09
-- Description: Categories should be lab-specific, not global

-- Step 1: Add lab_id column (nullable initially for existing data)
ALTER TABLE categories
ADD COLUMN lab_id INT(11) DEFAULT NULL AFTER category_id;

-- Step 2: Add foreign key constraint
ALTER TABLE categories
ADD CONSTRAINT fk_categories_lab
FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- Step 3: Add index for performance
ALTER TABLE categories
ADD INDEX idx_categories_lab (lab_id);

-- Step 4: Update existing categories to belong to a default lab
-- NOTE: Run this manually after identifying the correct lab_id for each category
-- UPDATE categories SET lab_id = ? WHERE lab_id IS NULL;

-- Step 5: After updating all categories, make lab_id NOT NULL
-- ALTER TABLE categories MODIFY COLUMN lab_id INT(11) NOT NULL;
