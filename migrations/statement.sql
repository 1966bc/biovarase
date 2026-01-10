 -- Stato finale
  SELECT 'results' AS tbl, COUNT(*) AS total FROM results
  UNION ALL SELECT 'batches', COUNT(*) FROM batches
  UNION ALL SELECT 'test_methods', COUNT(*) FROM test_methods;

  -- Nessun NULL in lab_id
  SELECT 'results' AS tbl, COUNT(*) AS nulls FROM results WHERE lab_id IS NULL
  UNION ALL SELECT 'test_methods', COUNT(*) FROM test_methods WHERE lab_id IS NULL;
