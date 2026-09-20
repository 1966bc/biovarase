-- ---------------------------------------------------------------------------
-- project:  biovarase
-- authors:  Giuseppe Costanzi (1966bc)
-- file:     sql/console.sql
-- ---------------------------------------------------------------------------
--
-- The sqlite3 shell, opened the way the program opens the database. Read at
-- start-up and not by hand:
--
--     sqlite3 -init sql/console.sql sql/biovarase.sl3
--
-- -init takes the place of ~/.sqliterc for that session, so what is here is
-- the whole configuration: nothing is inherited from the machine, and the
-- shell behaves the same everywhere.
--
-- Nothing in this file is part of the program and nothing here writes. The
-- scratch pad is sql/statement.sql, run with .read once this is up.
-- ---------------------------------------------------------------------------

-- Foreign keys are OFF in every new SQLite connection, this shell included.
-- dbms.set_connection turns them on, so a shell without this line lets
-- through what the program would refuse.
PRAGMA foreign_keys = ON;

.headers on
.mode column
.nullvalue .
.timer on

SELECT 'biovarase' AS database,
       (SELECT COUNT(*) FROM tests) AS analytes,
       (SELECT COUNT(*) FROM batches) AS lots,
       (SELECT COUNT(*) FROM results) AS results,
       (SELECT COUNT(*) FROM notes) AS notes;
