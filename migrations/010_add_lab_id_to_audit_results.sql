-- Migration 010: Add lab_id to audit_results table for multi-tenant audit filtering
-- Date: 2026-01-10
-- Purpose: Enable lab-specific audit trail filtering (ISO 15189 compliance)

-- Step 1: Add lab_id column
ALTER TABLE audit_results
ADD COLUMN lab_id INT(11) UNSIGNED DEFAULT NULL
COMMENT 'FK to labs.lab_id for multi-tenant audit filtering'
AFTER result_id;

-- Step 2: Populate lab_id from batches table via batch_id
UPDATE audit_results ar
INNER JOIN batches b ON ar.batch_id = b.batch_id
SET ar.lab_id = b.lab_id
WHERE ar.lab_id IS NULL;

-- Step 3: For records where batch was deleted, try results table
UPDATE audit_results ar
INNER JOIN results r ON ar.result_id = r.result_id
SET ar.lab_id = r.lab_id
WHERE ar.lab_id IS NULL AND r.lab_id IS NOT NULL;

-- Step 4: For remaining orphans, try other audit_results with same batch_id
UPDATE audit_results ar1
INNER JOIN (
    SELECT batch_id, lab_id
    FROM audit_results
    WHERE lab_id IS NOT NULL
    GROUP BY batch_id
) ar2 ON ar1.batch_id = ar2.batch_id
SET ar1.lab_id = ar2.lab_id
WHERE ar1.lab_id IS NULL;

-- Step 5: Add indexes for filtering
CREATE INDEX idx_audit_results_lab_id ON audit_results(lab_id);
CREATE INDEX idx_audit_results_lab_time ON audit_results(lab_id, log_time);

-- Note: No FK constraint on audit tables - they must preserve history even if lab is deleted
-- lab_id can remain NULL for very old records where batch no longer exists

-- Step 6: Update triggers to include lab_id in audit records

-- Drop and recreate INSERT trigger
DROP TRIGGER IF EXISTS on_insert_results;

DELIMITER //
CREATE TRIGGER on_insert_results
AFTER INSERT ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        lab_id,
        batch_id,
        run_number,
        workstation_id,
        result,
        received,
        status,
        validated,
        validated_by,
        validated_at,
        is_delete,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'INSERT',
        NEW.result_id,
        NEW.lab_id,
        NEW.batch_id,
        NEW.run_number,
        NEW.workstation_id,
        NEW.result,
        NEW.received,
        NEW.status,
        NEW.validated,
        NEW.validated_by,
        NEW.validated_at,
        NEW.is_delete,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END //
DELIMITER ;

-- Drop and recreate UPDATE trigger
DROP TRIGGER IF EXISTS on_update_results;

DELIMITER //
CREATE TRIGGER on_update_results
AFTER UPDATE ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        lab_id,
        batch_id,
        run_number,
        workstation_id,
        result,
        received,
        status,
        validated,
        validated_by,
        validated_at,
        is_delete,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'UPDATE',
        NEW.result_id,
        NEW.lab_id,
        NEW.batch_id,
        NEW.run_number,
        NEW.workstation_id,
        NEW.result,
        NEW.received,
        NEW.status,
        NEW.validated,
        NEW.validated_by,
        NEW.validated_at,
        NEW.is_delete,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END //
DELIMITER ;
