-- Migration 018: Convert actions to English for international peer lab comparison
-- Date: 2026-01
--
-- This migration:
-- 1. Updates action descriptions from Italian to English
-- 2. Removes test/garbage data (status=0)
-- 3. Adds new standardized actions
--
-- The i18n.py file provides Italian translations for display

-- First, remove test data
DELETE FROM actions WHERE status = 0;

-- Update existing actions to English
UPDATE actions SET description = 'Calibration' WHERE action_id = 1;
UPDATE actions SET description = 'Replacement' WHERE action_id = 2;
UPDATE actions SET description = 'Reagent blank performed' WHERE action_id = 3;
UPDATE actions SET description = 'New calibration performed' WHERE action_id = 4;
UPDATE actions SET description = 'Reagents replaced' WHERE action_id = 5;
UPDATE actions SET description = 'Controls reconstituted and repeated' WHERE action_id = 6;
UPDATE actions SET description = 'Operating conditions check' WHERE action_id = 7;
UPDATE actions SET description = 'Detection system maintenance' WHERE action_id = 8;
UPDATE actions SET description = 'Target modified' WHERE action_id = 9;
UPDATE actions SET description = 'SD modified' WHERE action_id = 10;
UPDATE actions SET description = 'Target and SD modified' WHERE action_id = 11;
UPDATE actions SET description = 'Comment' WHERE action_id = 12;
UPDATE actions SET description = 'Controls replaced' WHERE action_id = 13;
UPDATE actions SET description = 'Electrode replaced' WHERE action_id = 14;

-- Add additional standardized actions for international use
INSERT IGNORE INTO actions (description, status) VALUES
('Repeat analysis', 1),
('Contact service', 1),
('New lot number', 1),
('Preventive maintenance', 1),
('Result excluded', 1),
('Instrument restart', 1);
