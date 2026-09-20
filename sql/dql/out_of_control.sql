-- ---------------------------------------------------------------------------
-- project:  biovarase
-- authors:  Giuseppe Costanzi (1966bc)
-- file:     sql/dql/out_of_control.sql
-- args:     how many standard deviations
-- ---------------------------------------------------------------------------
--
-- The results further from their target than the given number of standard
-- deviations, newest first, with what was written about them.
--
-- This is the 1:3S rule read in SQL, and it is only the first of the Westgard
-- rules: the others are about runs of results, not about one, and are read in
-- westgards.py where a series can be walked. A query that finds single points
-- cannot see four results drifting on the same side of the mean.
-- ---------------------------------------------------------------------------

SELECT r.received,
       t.description AS analyte,
       b.description AS level,
       w.description AS bench,
       r.result,
       b.target,
       ROUND((r.result - b.target) / b.sd, 2) AS z,
       a.description AS action,
       n.description AS note

  FROM results r
  JOIN batches b ON b.batch_id = r.batch_id
  JOIN test_methods tm ON tm.test_method_id = b.test_method_id
  JOIN tests t ON t.test_id = tm.test_id
  JOIN workstations w ON w.workstation_id = b.workstation_id
  LEFT JOIN notes n ON n.result_id = r.result_id AND n.status = 1
  LEFT JOIN actions a ON a.action_id = n.action_id
 WHERE r.status = 1
   AND ABS(r.result - b.target) > ? * b.sd
 ORDER BY r.received DESC;
