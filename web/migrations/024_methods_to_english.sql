-- Migration 024: Translate methods descriptions to English
-- Date: 2026-01-13
-- Author: Claude

UPDATE methods SET description = 'Photometry' WHERE method_id = 1;
UPDATE methods SET description = 'Turbidimetry' WHERE method_id = 2;
UPDATE methods SET description = 'Nephelometry' WHERE method_id = 3;
-- LC-MS (4) already English
-- Dummy (5) already English
-- LC-MS/MS (6) already English
UPDATE methods SET description = 'Potentiometry' WHERE method_id = 7;
UPDATE methods SET description = 'HPLC Fluorimetry' WHERE method_id = 8;
UPDATE methods SET description = 'Chemiluminescence' WHERE method_id = 9;
UPDATE methods SET description = 'ELISA' WHERE method_id = 10;
-- GC-MS (11) already English
-- 1132123 (17) test data, skipped
-- Not assigned (18) already English
UPDATE methods SET description = 'Immunoturbidimetry' WHERE method_id = 19;
