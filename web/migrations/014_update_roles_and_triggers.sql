-- Migration 014: Update user roles and audit triggers for organizations
-- Date: 2026-01-10
-- Purpose: Migrate to new role hierarchy and update triggers to use org_id

-- ============================================================
-- NEW ROLE HIERARCHY
-- ============================================================
-- OLD:                          NEW:
--   0 = Admin                     0 = App Admin (global)
--   1 = Superuser                 1 = Country Admin
--   2 = Technician                2 = Regional Admin
--   3 = Autologin                 3 = Lab Admin
--   5 = Viewer variant            4 = Superuser
--                                 5 = Technician
--                                 6 = Viewer

-- Step 1: Migrate roles (order matters - highest to lowest)
-- Note: Users with org_id=NULL and old role=0 become App Admin (role stays 0)
-- Users with org_id set become Lab Admin (role=3) initially

-- Old role=5 → New role=6 (Viewer)
UPDATE users SET role = 6 WHERE role = 5;

-- Old role=4 → New role=6 (Viewer)
UPDATE users SET role = 6 WHERE role = 4;

-- Old role=3 → New role=6 (Viewer)
UPDATE users SET role = 6 WHERE role = 3;

-- Old role=2 (Technician) → New role=5 (Technician)
UPDATE users SET role = 5 WHERE role = 2;

-- Old role=1 (Superuser) → New role=4 (Superuser)
UPDATE users SET role = 4 WHERE role = 1;

-- Old role=0 with org_id NOT NULL → New role=3 (Lab Admin)
UPDATE users SET role = 3 WHERE role = 0 AND org_id IS NOT NULL;

-- Old role=0 with org_id=NULL stays role=0 (App Admin)

-- ============================================================
-- UPDATE TRIGGERS TO USE org_id
-- ============================================================

-- Drop old triggers
DROP TRIGGER IF EXISTS on_insert_batch;
DROP TRIGGER IF EXISTS on_update_batch;
DROP TRIGGER IF EXISTS on_insert_results;
DROP TRIGGER IF EXISTS on_update_results;

-- Recreate INSERT trigger for batches
DELIMITER //
CREATE TRIGGER on_insert_batch
AFTER INSERT ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        lab_id,
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
        NEW.lab_id,
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

-- Recreate UPDATE trigger for batches
DELIMITER //
CREATE TRIGGER on_update_batch
AFTER UPDATE ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        lab_id,
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
        NEW.lab_id,
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

-- Recreate INSERT trigger for results
DELIMITER //
CREATE TRIGGER on_insert_results
AFTER INSERT ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        lab_id,
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
        NEW.lab_id,
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

-- Recreate UPDATE trigger for results
DELIMITER //
CREATE TRIGGER on_update_results
AFTER UPDATE ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        lab_id,
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
        NEW.lab_id,
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
-- SELECT user_id, nickname, role,
--   CASE role
--     WHEN 0 THEN 'App Admin'
--     WHEN 1 THEN 'Country Admin'
--     WHEN 2 THEN 'Regional Admin'
--     WHEN 3 THEN 'Lab Admin'
--     WHEN 4 THEN 'Superuser'
--     WHEN 5 THEN 'Technician'
--     WHEN 6 THEN 'Viewer'
--   END AS role_name,
--   org_id
-- FROM users ORDER BY role, user_id;
--
-- SHOW TRIGGERS;
