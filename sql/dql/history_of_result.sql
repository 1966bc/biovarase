-- ---------------------------------------------------------------------------
-- project:  biovarase
-- authors:  Giuseppe Costanzi (1966bc)
-- file:     sql/dql/history_of_result.sql
-- args:     result_id
-- ---------------------------------------------------------------------------
--
-- Everything that happened to one result, oldest first: entered, corrected,
-- excluded, deleted - with the values as they were each time and who did it.
--
-- The rows come from audit_results, written by the triggers on the table, so
-- they are there whether the change was made by a window, by a script, or by
-- somebody at the sqlite3 shell. A deleted result has no row in results any
-- more and still has its history here, which is the point of keeping one.
-- ---------------------------------------------------------------------------

SELECT a.log_time,
       a.operation,
       a.result,
       a.status,
       u.last_name AS by_whom

  FROM audit_results a
  LEFT JOIN users u ON u.user_id = a.log_id
 WHERE a.result_id = ?
 ORDER BY a.audit_id;
