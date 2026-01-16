-- Migration 029: Sync batch assay_id with test_method_id
-- Date: 2026-01
--
-- This trigger keeps assay_id in sync with test_method_id for batches.
-- When Abbott import (or Python desktop) sets test_method_id,
-- the trigger automatically sets assay_id to the same value.
--
-- This allows:
-- - Desktop Python to continue using test_method_id (unchanged)
-- - Web PHP to read assay_id (always in sync)

DELIMITER //

-- Trigger: BEFORE INSERT on batches
DROP TRIGGER IF EXISTS tr_batches_sync_assay_insert//
CREATE TRIGGER tr_batches_sync_assay_insert
BEFORE INSERT ON batches
FOR EACH ROW
BEGIN
    -- If test_method_id is set but assay_id is not, sync them
    IF NEW.test_method_id IS NOT NULL AND NEW.assay_id IS NULL THEN
        SET NEW.assay_id = NEW.test_method_id;
    END IF;
    -- If assay_id is set but test_method_id is not, sync the other way
    IF NEW.assay_id IS NOT NULL AND NEW.test_method_id IS NULL THEN
        SET NEW.test_method_id = NEW.assay_id;
    END IF;
END//

-- Trigger: BEFORE UPDATE on batches
DROP TRIGGER IF EXISTS tr_batches_sync_assay_update//
CREATE TRIGGER tr_batches_sync_assay_update
BEFORE UPDATE ON batches
FOR EACH ROW
BEGIN
    -- If test_method_id changed, sync assay_id
    IF NEW.test_method_id != OLD.test_method_id OR
       (NEW.test_method_id IS NOT NULL AND OLD.test_method_id IS NULL) THEN
        SET NEW.assay_id = NEW.test_method_id;
    END IF;
    -- If assay_id changed, sync test_method_id
    IF NEW.assay_id != OLD.assay_id OR
       (NEW.assay_id IS NOT NULL AND OLD.assay_id IS NULL) THEN
        SET NEW.test_method_id = NEW.assay_id;
    END IF;
END//

DELIMITER ;
