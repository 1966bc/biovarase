-- Migration 009: Add lab_id to audit_batches table for multi-tenant audit filtering
-- Date: 2026-01-10
-- Purpose: Enable lab-specific audit trail filtering (ISO 15189 compliance)

-- Step 1: Add lab_id column
ALTER TABLE audit_batches
ADD COLUMN lab_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to labs.lab_id for multi-tenant audit filtering'
AFTER batch_id;

-- Step 2: Populate lab_id from batches table (for existing audit records)
UPDATE audit_batches ab
INNER JOIN batches b ON ab.batch_id = b.batch_id
SET ab.lab_id = b.lab_id
WHERE ab.lab_id IS NULL;

-- Step 3: For deleted batches, try to get lab_id from other audit records
UPDATE audit_batches ab1
INNER JOIN (
    SELECT batch_id, lab_id
    FROM audit_batches
    WHERE lab_id IS NOT NULL
    GROUP BY batch_id
) ab2 ON ab1.batch_id = ab2.batch_id
SET ab1.lab_id = ab2.lab_id
WHERE ab1.lab_id IS NULL;

-- Step 4: Add index for filtering
CREATE INDEX idx_audit_batches_lab_id ON audit_batches(lab_id);
CREATE INDEX idx_audit_batches_lab_time ON audit_batches(lab_id, log_time);

-- Note: No FK constraint on audit tables - they must preserve history even if lab is deleted
-- lab_id can remain NULL for very old records where batch no longer exists

-- Step 6: Update triggers to include lab_id in audit records

-- Drop and recreate INSERT trigger
DROP TRIGGER IF EXISTS on_insert_batch;

DELIMITER //
CREATE TRIGGER on_insert_batch
AFTER INSERT ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        lab_id,
        control_id,
        dict_test_id,
        workstation_id,
        lot_number,
        expiration,
        target,
        sd,
        description,
        `lower`,
        `upper`,
        `rank`,
        status,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'INSERT',
        NEW.batch_id,
        NEW.lab_id,
        NEW.control_id,
        NEW.test_method_id,
        NEW.workstation_id,
        NEW.lot_number,
        NEW.expiration,
        NEW.target,
        NEW.sd,
        NEW.description,
        NEW.lower,
        NEW.upper,
        NEW.rank,
        NEW.status,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END //
DELIMITER ;

-- Drop and recreate UPDATE trigger
DROP TRIGGER IF EXISTS on_update_batch;

DELIMITER //
CREATE TRIGGER on_update_batch
AFTER UPDATE ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        lab_id,
        control_id,
        dict_test_id,
        workstation_id,
        lot_number,
        expiration,
        target,
        sd,
        description,
        `lower`,
        `upper`,
        `rank`,
        status,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'UPDATE',
        NEW.batch_id,
        NEW.lab_id,
        NEW.control_id,
        NEW.test_method_id,
        NEW.workstation_id,
        NEW.lot_number,
        NEW.expiration,
        NEW.target,
        NEW.sd,
        NEW.description,
        NEW.lower,
        NEW.upper,
        NEW.rank,
        NEW.status,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END //
DELIMITER ;
