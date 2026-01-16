-- Migration 031: Recalculate SD for batches with lower/upper values
-- Formula: SD = (upper - lower) / 4 (assuming ±2SD limits)
-- Only updates batches where both lower and upper are set and upper > lower
--
-- Run: mysql -u root -p biovarase < migrations/031_recalculate_batch_sd.sql

-- Show current values before update
SELECT
    batch_id,
    lot_number,
    target,
    sd AS old_sd,
    `lower`,
    `upper`,
    ROUND((`upper` - `lower`) / 4, 3) AS new_sd
FROM batches
WHERE `lower` IS NOT NULL
  AND `upper` IS NOT NULL
  AND `upper` > `lower`
ORDER BY batch_id;

-- Update SD values
UPDATE batches
SET sd = ROUND((`upper` - `lower`) / 4, 3)
WHERE `lower` IS NOT NULL
  AND `upper` IS NOT NULL
  AND `upper` > `lower`;

-- Show affected rows
SELECT ROW_COUNT() AS rows_updated;

-- Verify update
SELECT
    batch_id,
    lot_number,
    target,
    sd,
    `lower`,
    `upper`
FROM batches
WHERE `lower` IS NOT NULL
  AND `upper` IS NOT NULL
ORDER BY batch_id;
