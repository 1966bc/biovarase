-- ---------------------------------------------------------------------------
-- project:  biovarase
-- authors:  Giuseppe Costanzi (1966bc)
-- file:     sql/dql/series_of_lot.sql
-- args:     batch_id, how many
-- ---------------------------------------------------------------------------
--
-- The results of one lot, newest first: the series a Levey-Jennings chart is
-- drawn on, turned round by whoever draws it.
--
-- status = 1 only. A result with status 0 is a point excluded from the
-- statistics on purpose - a run repeated, a sample that was not the control -
-- and it is left out here rather than in every window that asks.
-- ---------------------------------------------------------------------------

SELECT r.result_id,
       r.result,
       r.received,
       r.reagent_lot,
       u.last_name AS entered_by

  FROM results r
  LEFT JOIN users u ON u.user_id = r.created_by
 WHERE r.batch_id = ?
   AND r.status = 1
 ORDER BY r.received DESC
 LIMIT ?;
