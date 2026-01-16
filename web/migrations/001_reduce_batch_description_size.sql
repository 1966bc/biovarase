-- Migration: Reduce batches.description from VARCHAR(255) to VARCHAR(15)
-- Date: 2026-01-08
-- Reason: Field only stores level indicators (L1, L2, Normal, Positive, etc.)
--         VARCHAR(255) is excessive for this purpose.
--
-- Before running, verify no data will be truncated:
--   SELECT description, LENGTH(description) FROM batches WHERE LENGTH(description) > 15;

ALTER TABLE batches
    MODIFY description VARCHAR(15) NOT NULL DEFAULT 'NOT ASSIGNED';
