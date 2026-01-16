-- Migration 028: Create assays table (replaces test_methods + goals for web)
-- Date: 2026-01
--
-- This migration creates a new unified table for the web application.
-- The old test_methods and goals tables are kept for the Python desktop app.
--
-- Web app uses: assays
-- Desktop app uses: test_methods + goals (unchanged)

-- ============================================================================
-- 1. CREATE ASSAYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS assays (
    assay_id            MEDIUMINT(8) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    test_id             MEDIUMINT(8) UNSIGNED NOT NULL,
    method_id           TINYINT(3) UNSIGNED NOT NULL,
    unit_id             TINYINT(3) UNSIGNED NOT NULL,
    sample_id           TINYINT(3) UNSIGNED NOT NULL,
    category_id         TINYINT(3) UNSIGNED NULL,
    org_id              INT(11) UNSIGNED NULL COMMENT 'Section org_id',
    code                VARCHAR(10) NOT NULL,
    description         VARCHAR(100) NULL COMMENT 'Local lab name for the test',

    -- Goals (previously in separate goals table)
    cvw                 FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'CV within-subject',
    cvb                 FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'CV between-subject',
    imp                 FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Imprecision',
    bias                FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Bias',
    teap005             FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'TEa at p=0.05',
    teap001             FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'TEa at p=0.01',
    to_export           TINYINT(1) NOT NULL DEFAULT 0,

    is_mandatory        TINYINT(1) NOT NULL DEFAULT 1,
    status              TINYINT(1) NOT NULL DEFAULT 1,

    -- Audit fields
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by          INT UNSIGNED NULL,
    updated_by          INT UNSIGNED NULL,

    -- Indexes
    INDEX idx_assays_test (test_id),
    INDEX idx_assays_org (org_id),
    INDEX idx_assays_status (status),
    INDEX idx_assays_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add foreign keys separately (easier to debug)
ALTER TABLE assays
    ADD CONSTRAINT fk_assays_test FOREIGN KEY (test_id) REFERENCES tests(test_id),
    ADD CONSTRAINT fk_assays_method FOREIGN KEY (method_id) REFERENCES methods(method_id),
    ADD CONSTRAINT fk_assays_unit FOREIGN KEY (unit_id) REFERENCES units(unit_id),
    ADD CONSTRAINT fk_assays_sample FOREIGN KEY (sample_id) REFERENCES samples(sample_id);

ALTER TABLE assays
    ADD CONSTRAINT fk_assays_category FOREIGN KEY (category_id) REFERENCES categories(category_id);

ALTER TABLE assays
    ADD CONSTRAINT fk_assays_org FOREIGN KEY (org_id) REFERENCES organizations(org_id);

-- ============================================================================
-- 2. CREATE AUDIT_ASSAYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_assays (
    audit_id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    operation           ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    assay_id            MEDIUMINT(8) UNSIGNED NULL,
    test_id             MEDIUMINT(8) UNSIGNED NULL,
    method_id           TINYINT(3) UNSIGNED NULL,
    unit_id             TINYINT(3) UNSIGNED NULL,
    sample_id           TINYINT(3) UNSIGNED NULL,
    category_id         TINYINT(3) UNSIGNED NULL,
    org_id              INT(11) UNSIGNED NULL,
    code                VARCHAR(10) NULL,
    description         VARCHAR(100) NULL,
    cvw                 FLOAT UNSIGNED NULL,
    cvb                 FLOAT UNSIGNED NULL,
    imp                 FLOAT UNSIGNED NULL,
    bias                FLOAT UNSIGNED NULL,
    teap005             FLOAT UNSIGNED NULL,
    teap001             FLOAT UNSIGNED NULL,
    to_export           TINYINT(1) NULL,
    is_mandatory        TINYINT(1) NULL,
    status              TINYINT(1) NULL,
    log_time            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_id              INT UNSIGNED NULL COMMENT 'User who made the change',
    log_ip              VARCHAR(45) NULL,

    INDEX idx_audit_assays_assay (assay_id),
    INDEX idx_audit_assays_time (log_time),
    INDEX idx_audit_assays_user (log_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. CREATE TRIGGERS
-- ============================================================================

DELIMITER //

-- Trigger: AFTER INSERT
CREATE TRIGGER tr_assays_after_insert
AFTER INSERT ON assays
FOR EACH ROW
BEGIN
    INSERT INTO audit_assays (
        operation, assay_id, test_id, method_id, unit_id, sample_id,
        category_id, org_id, code, description,
        cvw, cvb, imp, bias, teap005, teap001, to_export,
        is_mandatory, status, log_id
    ) VALUES (
        'INSERT', NEW.assay_id, NEW.test_id, NEW.method_id, NEW.unit_id, NEW.sample_id,
        NEW.category_id, NEW.org_id, NEW.code, NEW.description,
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
        category_id, org_id, code, description,
        cvw, cvb, imp, bias, teap005, teap001, to_export,
        is_mandatory, status, log_id
    ) VALUES (
        'UPDATE', OLD.assay_id, OLD.test_id, OLD.method_id, OLD.unit_id, OLD.sample_id,
        OLD.category_id, OLD.org_id, OLD.code, OLD.description,
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
        category_id, org_id, code, description,
        cvw, cvb, imp, bias, teap005, teap001, to_export,
        is_mandatory, status
    ) VALUES (
        'DELETE', OLD.assay_id, OLD.test_id, OLD.method_id, OLD.unit_id, OLD.sample_id,
        OLD.category_id, OLD.org_id, OLD.code, OLD.description,
        OLD.cvw, OLD.cvb, OLD.imp, OLD.bias, OLD.teap005, OLD.teap001, OLD.to_export,
        OLD.is_mandatory, OLD.status
    );
END//

DELIMITER ;

-- ============================================================================
-- 4. POPULATE ASSAYS FROM TEST_METHODS + GOALS
-- ============================================================================

INSERT INTO assays (
    assay_id, test_id, method_id, unit_id, sample_id, category_id, org_id,
    code, description,
    cvw, cvb, imp, bias, teap005, teap001, to_export,
    is_mandatory, status
)
SELECT
    tm.test_method_id,
    tm.test_id,
    tm.method_id,
    tm.unit_id,
    tm.sample_id,
    NULLIF(tm.category_id, 0),  -- Convert 0 to NULL (no category with id=0)
    tm.org_id,
    tm.code,
    t.description,  -- Copy test description as initial local name
    COALESCE(g.cvw, 0),
    COALESCE(g.cvb, 0),
    COALESCE(g.imp, 0),
    COALESCE(g.bias, 0),
    COALESCE(g.teap005, 0),
    COALESCE(g.teap001, 0),
    COALESCE(g.to_export, 0),
    tm.is_mandatory,
    tm.status
FROM test_methods tm
JOIN tests t ON t.test_id = tm.test_id
LEFT JOIN goals g ON g.test_method_id = tm.test_method_id;

-- ============================================================================
-- 5. ADD ASSAY_ID TO BATCHES (for web app)
-- ============================================================================

ALTER TABLE batches
ADD COLUMN assay_id MEDIUMINT(8) UNSIGNED NULL AFTER test_method_id;

-- Populate assay_id from test_method_id
UPDATE batches SET assay_id = test_method_id WHERE test_method_id IS NOT NULL;

-- Create index and FK
CREATE INDEX idx_batches_assay ON batches(assay_id);
ALTER TABLE batches ADD CONSTRAINT fk_batches_assay FOREIGN KEY (assay_id) REFERENCES assays(assay_id);

-- ============================================================================
-- 6. UPDATE AUDIT_BATCHES (add assay_id column)
-- ============================================================================
-- Note: This may fail with "Duplicate column name" if already run - safe to ignore

ALTER TABLE audit_batches
ADD COLUMN IF NOT EXISTS assay_id MEDIUMINT(8) UNSIGNED NULL AFTER dict_test_id;

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- The old tables (test_methods, goals) are NOT modified or dropped.
-- The Python desktop app continues to use them.
--
-- The web app should use:
--   - assays instead of test_methods
--   - batches.assay_id instead of batches.test_method_id
--
-- Foreign key relationships:
--   results -> batches -> assays -> tests
--                                -> methods
--                                -> units
--                                -> samples
--                                -> categories
--                                -> organizations (section)
--
