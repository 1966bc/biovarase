   SELECT 'assays' AS tabella, COUNT(*) AS righe FROM assays
  UNION ALL
  SELECT 'audit_assays', COUNT(*) FROM audit_assays
  UNION ALL
  SELECT 'batches con assay_id', COUNT(*) FROM batches WHERE assay_id IS NOT NULL;

 /*-- Pulisci le tabelle parzialmente create
  DROP TRIGGER IF EXISTS tr_assays_after_insert;
  DROP TRIGGER IF EXISTS tr_assays_after_update;
  DROP TRIGGER IF EXISTS tr_assays_after_delete;
  ALTER TABLE batches DROP FOREIGN KEY IF EXISTS fk_batches_assay;
  ALTER TABLE batches DROP INDEX IF EXISTS idx_batches_assay;
  ALTER TABLE batches DROP COLUMN IF EXISTS assay_id;
  DROP TABLE IF EXISTS audit_assays;
  DROP TABLE IF EXISTS assays;
