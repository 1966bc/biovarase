-- Migration 021: Add technical validation fields
-- Date: 2026-01-12
-- Purpose: Add fields for technical validation (technician) separate from
--          medical validation (supervisor). Also adds operator_code for
--          machine/instrument operator identification from import files.

-- ============================================================
-- ADD COLUMNS TO RESULTS TABLE
-- ============================================================

ALTER TABLE results
    ADD COLUMN tech_validated TINYINT(1) UNSIGNED NOT NULL DEFAULT 0
        COMMENT 'Technical validation flag: 0=pending, 1=validated'
        AFTER validated_at,
    ADD COLUMN tech_validated_by SMALLINT NULL
        COMMENT 'FK to users.user_id who technically validated'
        AFTER tech_validated,
    ADD COLUMN tech_validated_at TIMESTAMP NULL
        COMMENT 'Timestamp when technically validated'
        AFTER tech_validated_by,
    ADD COLUMN operator_code VARCHAR(50) NULL
        COMMENT 'Operator/machine code from instrument or import file'
        AFTER tech_validated_at;

-- Add index for tech_validated queries
ALTER TABLE results
    ADD INDEX idx_results_tech_validated (tech_validated, received),
    ADD INDEX idx_results_tech_validated_by (tech_validated_by),
    ADD INDEX idx_results_operator_code (operator_code);

-- ============================================================
-- ADD COLUMNS TO AUDIT_RESULTS TABLE
-- ============================================================

ALTER TABLE audit_results
    ADD COLUMN tech_validated TINYINT(1) UNSIGNED NULL
        COMMENT 'Technical validation flag'
        AFTER validated_at,
    ADD COLUMN tech_validated_by SMALLINT NULL
        COMMENT 'FK to users.user_id who technically validated'
        AFTER tech_validated,
    ADD COLUMN tech_validated_at TIMESTAMP NULL
        COMMENT 'Timestamp when technically validated'
        AFTER tech_validated_by,
    ADD COLUMN operator_code VARCHAR(50) NULL
        COMMENT 'Operator/machine code from instrument'
        AFTER tech_validated_at;

-- ============================================================
-- UPDATE TRIGGERS TO INCLUDE NEW FIELDS
-- ============================================================

DROP TRIGGER IF EXISTS on_insert_results;
DROP TRIGGER IF EXISTS on_update_results;

-- Recreate INSERT trigger for results
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
        tech_validated,
        tech_validated_by,
        tech_validated_at,
        operator_code,
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
        NEW.tech_validated,
        NEW.tech_validated_by,
        NEW.tech_validated_at,
        NEW.operator_code,
        NEW.is_delete,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END //
DELIMITER ;

-- Recreate UPDATE trigger for results
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
        tech_validated,
        tech_validated_by,
        tech_validated_at,
        operator_code,
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
        NEW.tech_validated,
        NEW.tech_validated_by,
        NEW.tech_validated_at,
        NEW.operator_code,
        NEW.is_delete,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END //
DELIMITER ;

-- ============================================================
-- VERIFICATION QUERIES (run manually after migration)
-- ============================================================
-- DESCRIBE results;
-- DESCRIBE audit_results;
-- SHOW TRIGGERS LIKE 'results';
