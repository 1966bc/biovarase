-- Migration: Reduce batches.lot_number from VARCHAR(30) to VARCHAR(20)
-- Date: 2026-01-08
-- Reason: Lot numbers rarely exceed 20 characters.
--
-- Before running, verify no data will be truncated:
--   SELECT lot_number, LENGTH(lot_number) FROM batches WHERE LENGTH(lot_number) > 20;

ALTER TABLE batches
    MODIFY lot_number VARCHAR(20) NOT NULL;
