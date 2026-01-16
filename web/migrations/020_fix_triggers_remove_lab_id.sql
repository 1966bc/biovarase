-- Migration 020: Fix triggers to remove lab_id references
-- Date: 2026-01-12
-- Purpose: Remove lab_id from triggers since column was removed from batches/results

-- ============================================================
-- UPDATE TRIGGERS TO REMOVE lab_id
-- ============================================================

-- Drop old triggers
DROP TRIGGER IF EXISTS on_insert_batch;
DROP TRIGGER IF EXISTS on_update_batch;
DROP TRIGGER IF EXISTS on_insert_results;
DROP TRIGGER IF EXISTS on_update_results;

-- Recreate INSERT trigger for batches (without lab_id)
DELIMITER //
CREATE TRIGGER on_insert_batch
AFTER INSERT ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        org_id,
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
        NEW.org_id,
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

-- Recreate UPDATE trigger for batches (without lab_id)
DELIMITER //
CREATE TRIGGER on_update_batch
AFTER UPDATE ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        org_id,
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
        NEW.org_id,
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

-- Recreate INSERT trigger for results (without lab_id)
DELIMITER //
CREATE TRIGGER on_insert_results
AFTER INSERT ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        org_id,
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
        NEW.org_id,
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

-- Recreate UPDATE trigger for results (without lab_id)
DELIMITER //
CREATE TRIGGER on_update_results
AFTER UPDATE ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        org_id,
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
        NEW.org_id,
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

-- Verification:
-- SHOW TRIGGERS;
