-- ---------------------------------------------------------------------------
-- project:  biovarase
-- authors:  Giuseppe Costanzi (1966bc)
-- file:     sql/statement.sql
-- ---------------------------------------------------------------------------
--
-- Scratch pad. Write the statement you are working on here and run it with
--
--     .read sql/statement.sql
--
-- Nothing in this file is part of the program. When a query earns its keep,
-- move it to sql/dql/ and give it a name.
-- ---------------------------------------------------------------------------

SELECT t.description AS analyte,
       b.description AS level,
       w.description AS bench,
       COUNT(r.result_id) AS n,
       ROUND(AVG(r.result), 2) AS mean,
       b.target

  FROM batches b
  JOIN test_methods tm ON tm.test_method_id = b.test_method_id
  JOIN tests t ON t.test_id = tm.test_id
  JOIN workstations w ON w.workstation_id = b.workstation_id
  LEFT JOIN results r ON r.batch_id = b.batch_id AND r.status = 1
 WHERE b.status = 1
 GROUP BY b.batch_id
 ORDER BY t.description, b.rank
 LIMIT 10;
