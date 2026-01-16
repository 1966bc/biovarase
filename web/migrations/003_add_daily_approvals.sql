-- Migration: 003_add_daily_approvals
-- Description: Add daily workstation approval tracking for QC workflow
-- Date: 2026-01-06
-- Author: Claude Code

-- Table to track daily workstation approvals
-- One row per workstation per day = explicit "OK to start routine" decision
CREATE TABLE IF NOT EXISTS daily_approvals (
    approval_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    approval_date DATE NOT NULL,
    workstation_id SMALLINT(5) UNSIGNED NOT NULL,
    approved_by TINYINT(3) UNSIGNED NOT NULL,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes VARCHAR(255) NULL,

    UNIQUE KEY uk_daily_ws (approval_date, workstation_id),
    KEY idx_approval_date (approval_date),
    KEY idx_workstation (workstation_id),
    KEY idx_approved_by (approved_by),

    CONSTRAINT fk_daily_approvals_workstation
        FOREIGN KEY (workstation_id) REFERENCES workstations(workstation_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_daily_approvals_user
        FOREIGN KEY (approved_by) REFERENCES users(user_id)
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
