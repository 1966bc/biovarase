-- Migration 030: Add LOINC code to assays table
-- Date: 2026-01
--
-- LOINC (Logical Observation Identifiers Names and Codes) is the international
-- standard for identifying laboratory observations. The code is specific to
-- the combination of test + method + sample + unit, which is why it belongs
-- in assays rather than tests.
--
-- LOINC format: numeric with hyphen and check digit (e.g., "2345-7")
-- Max length: 10 characters (current LOINC codes are 3-7 chars + hyphen + check)

-- Add loinc_code to assays
ALTER TABLE assays
ADD COLUMN loinc_code VARCHAR(20) NULL COMMENT 'LOINC code for interoperability' AFTER description;

-- Add index for LOINC lookups
CREATE INDEX idx_assays_loinc ON assays(loinc_code);

-- Add loinc_code to audit_assays
ALTER TABLE audit_assays
ADD COLUMN loinc_code VARCHAR(20) NULL AFTER description;

-- Update triggers to include loinc_code
DROP TRIGGER IF EXISTS tr_assays_after_insert;
DROP TRIGGER IF EXISTS tr_assays_after_update;
DROP TRIGGER IF EXISTS tr_assays_after_delete;

DELIMITER //

-- Trigger: AFTER INSERT
CREATE TRIGGER tr_assays_after_insert
AFTER INSERT ON assays
FOR EACH ROW
BEGIN
    INSERT INTO audit_assays (
        operation, assay_id, test_id, method_id, unit_id, sample_id,
        category_id, org_id, code, description, loinc_code,
        cvw, cvb, imp, bias, teap005, teap001, to_export,
        is_mandatory, status, log_id
    ) VALUES (
        'INSERT', NEW.assay_id, NEW.test_id, NEW.method_id, NEW.unit_id, NEW.sample_id,
        NEW.category_id, NEW.org_id, NEW.code, NEW.description, NEW.loinc_code,
        NEW.cvw, NEW.cvb, NEW.imp, NEW.bias, NEW.teap005, NEW.teap001, NEW.to_export,
        NEW.is_mandatory, NEW.status, NEW.created_by
    );
END//

-- Trigger: AFTER UPDATE
CREATE TRIGGER tr_assays_after_update
AFTER UPDATE ON assays
FOR EACH ROW
BEGIN
    INSERT INTO audit_assays (
        operation, assay_id, test_id, method_id, unit_id, sample_id,
        category_id, org_id, code, description, loinc_code,
        cvw, cvb, imp, bias, teap005, teap001, to_export,
        is_mandatory, status, log_id
    ) VALUES (
        'UPDATE', OLD.assay_id, OLD.test_id, OLD.method_id, OLD.unit_id, OLD.sample_id,
        OLD.category_id, OLD.org_id, OLD.code, OLD.description, OLD.loinc_code,
        OLD.cvw, OLD.cvb, OLD.imp, OLD.bias, OLD.teap005, OLD.teap001, OLD.to_export,
        OLD.is_mandatory, OLD.status, NEW.updated_by
    );
END//

-- Trigger: AFTER DELETE
CREATE TRIGGER tr_assays_after_delete
AFTER DELETE ON assays
FOR EACH ROW
BEGIN
    INSERT INTO audit_assays (
        operation, assay_id, test_id, method_id, unit_id, sample_id,
        category_id, org_id, code, description, loinc_code,
        cvw, cvb, imp, bias, teap005, teap001, to_export,
        is_mandatory, status
    ) VALUES (
        'DELETE', OLD.assay_id, OLD.test_id, OLD.method_id, OLD.unit_id, OLD.sample_id,
        OLD.category_id, OLD.org_id, OLD.code, OLD.description, OLD.loinc_code,
        OLD.cvw, OLD.cvb, OLD.imp, OLD.bias, OLD.teap005, OLD.teap001, OLD.to_export,
        OLD.is_mandatory, OLD.status
    );
END//

DELIMITER ;
