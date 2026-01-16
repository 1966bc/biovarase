-- Migration 018: Convert actions to English for international peer lab comparison
-- Date: 2026-01
--
-- This migration:
-- 1. Adds `code` column for unique English identifier (peer lab key)
-- 2. Updates action descriptions from Italian to English
-- 3. Removes test/garbage data (status=0)
-- 4. Adds new standardized actions
--
-- The i18n.py file provides Italian translations for display

-- First, remove test data
DELETE FROM actions WHERE status = 0;

-- Add code column if not exists
ALTER TABLE actions ADD COLUMN IF NOT EXISTS code VARCHAR(30) NULL AFTER action_id;

-- Update existing actions with English code and description
UPDATE actions SET code = 'CALIBRATION', description = 'Calibration' WHERE action_id = 1;
UPDATE actions SET code = 'REPLACEMENT', description = 'Replacement' WHERE action_id = 2;
UPDATE actions SET code = 'REAGENT_BLANK', description = 'Reagent blank performed' WHERE action_id = 3;
UPDATE actions SET code = 'NEW_CALIBRATION', description = 'New calibration performed' WHERE action_id = 4;
UPDATE actions SET code = 'REAGENTS_REPLACED', description = 'Reagents replaced' WHERE action_id = 5;
UPDATE actions SET code = 'CONTROLS_RECONSTITUTED', description = 'Controls reconstituted and repeated' WHERE action_id = 6;
UPDATE actions SET code = 'CONDITIONS_CHECK', description = 'Operating conditions check' WHERE action_id = 7;
UPDATE actions SET code = 'DETECTION_MAINTENANCE', description = 'Detection system maintenance' WHERE action_id = 8;
UPDATE actions SET code = 'TARGET_MODIFIED', description = 'Target modified' WHERE action_id = 9;
UPDATE actions SET code = 'SD_MODIFIED', description = 'SD modified' WHERE action_id = 10;
UPDATE actions SET code = 'TARGET_SD_MODIFIED', description = 'Target and SD modified' WHERE action_id = 11;
UPDATE actions SET code = 'COMMENT', description = 'Comment' WHERE action_id = 12;
UPDATE actions SET code = 'CONTROLS_REPLACED', description = 'Controls replaced' WHERE action_id = 13;
UPDATE actions SET code = 'ELECTRODE_REPLACED', description = 'Electrode replaced' WHERE action_id = 14;

-- Add additional standardized actions for international use
INSERT IGNORE INTO actions (code, description, status) VALUES
('REPEAT_ANALYSIS', 'Repeat analysis', 1),
('CONTACT_SERVICE', 'Contact service', 1),
('NEW_LOT', 'New lot number', 1),
('PREVENTIVE_MAINTENANCE', 'Preventive maintenance', 1),
('RESULT_EXCLUDED', 'Result excluded', 1),
('INSTRUMENT_RESTART', 'Instrument restart', 1);

-- Make code NOT NULL and UNIQUE after populating
-- (Run separately if needed to handle any NULL values first)
-- ALTER TABLE actions MODIFY COLUMN code VARCHAR(30) NOT NULL;
-- ALTER TABLE actions ADD UNIQUE INDEX idx_actions_code (code);
