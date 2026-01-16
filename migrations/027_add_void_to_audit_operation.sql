-- Migration 027: Add VOID to audit_results operation enum
-- Date: 2026-01
--
-- Adds VOID operation type for voided results tracking

ALTER TABLE audit_results
MODIFY COLUMN operation ENUM('INSERT','UPDATE','DELETE','VOID') NOT NULL;
