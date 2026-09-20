-- ---------------------------------------------------------------------------
-- project:  biovarase
-- authors:  Giuseppe Costanzi (1966bc)
-- file:     sql/dql/lots_in_use.sql
-- ---------------------------------------------------------------------------
--
-- Every lot being controlled now, with its statistics and how far it sits
-- from its target: the state of the laboratory on one page.
--
-- The mean and the standard deviation are computed over the results; the
-- target and the sd of the lot are what the chart is drawn against. When the
-- two means drift apart the lot wants re-evaluating, which is the first
-- thing this query is asked.
-- ---------------------------------------------------------------------------

SELECT t.description AS analyte,
       b.description AS level,
       w.description AS bench,
       b.lot_number,
       b.expiration,
       COUNT(r.result_id) AS n,
       b.target,
       ROUND(AVG(r.result), 3) AS mean,
       b.sd,
       ROUND(100.0 * (AVG(r.result) - b.target) / b.target, 2) AS bias_percent

  FROM batches b
  JOIN test_methods tm ON tm.test_method_id = b.test_method_id
  JOIN tests t ON t.test_id = tm.test_id
  JOIN workstations w ON w.workstation_id = b.workstation_id
  LEFT JOIN results r ON r.batch_id = b.batch_id AND r.status = 1
 WHERE b.status = 1
 GROUP BY b.batch_id
 ORDER BY ABS(bias_percent) DESC;
