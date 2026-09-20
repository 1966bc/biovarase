-- project: Biovarase
-- authors: Giuseppe Costanzi (1966bc)
-- licence: GPL-3.0-or-later, see LICENSE
--
-- Internal quality control for one laboratory.
--
-- One laboratory, one file. There is no tenant column anywhere: the database
-- is the laboratory. Results are entered, never validated; what happened to
-- them is kept by the audit trail at the bottom of this file.
--
--     sqlite3 biovarase.sl3 < schema.sql

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- master data

CREATE TABLE units (
    unit_id     INTEGER PRIMARY KEY,
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE TABLE samples (
    sample_id   INTEGER PRIMARY KEY,
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE TABLE methods (
    method_id   INTEGER PRIMARY KEY,
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE TABLE tests (
    test_id     INTEGER PRIMARY KEY,
    description TEXT    NOT NULL UNIQUE,
    loinc       TEXT,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY,
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE TABLE equipments (
    equipment_id INTEGER PRIMARY KEY,
    supplier_id  INTEGER REFERENCES suppliers (supplier_id),
    description  TEXT    NOT NULL,
    status       INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

-- The control material, as the manufacturer sells it. A lot of it is a batch.
CREATE TABLE controls (
    control_id  INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers (supplier_id),
    description TEXT    NOT NULL,
    reference   TEXT,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

-- What was done about an out of control result: calibration, new reagent lot...
CREATE TABLE actions (
    action_id   INTEGER PRIMARY KEY,
    code        TEXT,
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

-- ------------------------------------------------------------------ the staff

-- role 0 manages the laboratory, role 1 enters results.
CREATE TABLE users (
    user_id    INTEGER PRIMARY KEY,
    last_name  TEXT    NOT NULL,
    first_name TEXT,
    nickname   TEXT    NOT NULL UNIQUE,
    pswrd      TEXT    NOT NULL,
    role       INTEGER NOT NULL DEFAULT 1 CHECK (role IN (0, 1)),
    status     INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

-- One row, always. The login writes it, the audit triggers read it: SQLite has
-- no CURRENT_USER and no way to ask which machine is connected, so both are
-- kept here, in the open.
--
-- host matters when the database file lives on a shared folder, which is how
-- a section with four benches works: the user says who, the host says from
-- which computer, and when an account has been shared - which it should not
-- be and is - the host is the only thing left that distinguishes two people.
CREATE TABLE session (
    session_id INTEGER PRIMARY KEY CHECK (session_id = 1),
    user_id    INTEGER REFERENCES users (user_id),
    host       TEXT
);

INSERT INTO session (session_id, user_id, host) VALUES (1, NULL, NULL);

-- ------------------------------------------------------------- the laboratory

-- An instrument on the bench: which model it is, and which one of them.
CREATE TABLE workstations (
    workstation_id INTEGER PRIMARY KEY,
    equipment_id   INTEGER NOT NULL REFERENCES equipments (equipment_id),
    description    TEXT    NOT NULL,
    serial         TEXT,
    rank           INTEGER NOT NULL DEFAULT 1,
    status         INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

-- An analyte as this laboratory measures it: sample, method, unit, and the
-- analytical goals it is held to (biological variation, total error).
CREATE TABLE test_methods (
    test_method_id INTEGER PRIMARY KEY,
    test_id        INTEGER NOT NULL REFERENCES tests (test_id),
    category_id    INTEGER REFERENCES categories (category_id),
    sample_id      INTEGER NOT NULL REFERENCES samples (sample_id),
    method_id      INTEGER NOT NULL REFERENCES methods (method_id),
    unit_id        INTEGER NOT NULL REFERENCES units (unit_id),
    code           TEXT    NOT NULL,
    -- Whether this method is controlled every working day. What is run in
    -- batches - the steroids, the vitamins - is controlled on the days it is
    -- run, and a report of what was not done today must not ask after it.
    is_mandatory   INTEGER NOT NULL DEFAULT 1 CHECK (is_mandatory IN (0, 1)),
    cvw            REAL    NOT NULL DEFAULT 0,
    cvb            REAL    NOT NULL DEFAULT 0,
    imp            REAL    NOT NULL DEFAULT 0,
    bias           REAL    NOT NULL DEFAULT 0,
    teap005        REAL    NOT NULL DEFAULT 0,
    teap001        REAL    NOT NULL DEFAULT 0,
    status         INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE INDEX idx_test_methods_test ON test_methods (test_id);

-- ------------------------------------------------------------------------- qc

-- A lot of control material, on one analyte, on one instrument: the series.
-- target and sd are this laboratory's own, computed on its results; lower and
-- upper are the manufacturer's, off the insert in the box.
CREATE TABLE batches (
    batch_id       INTEGER PRIMARY KEY,
    control_id     INTEGER NOT NULL REFERENCES controls (control_id),
    test_method_id INTEGER NOT NULL REFERENCES test_methods (test_method_id),
    workstation_id INTEGER NOT NULL REFERENCES workstations (workstation_id),
    lot_number     TEXT    NOT NULL,
    description    TEXT    NOT NULL,
    expiration     DATE,
    target         REAL    NOT NULL DEFAULT 0,
    sd             REAL    NOT NULL DEFAULT 0,
    lower          REAL    NOT NULL DEFAULT 0,
    upper          REAL    NOT NULL DEFAULT 0,
    rank           INTEGER NOT NULL DEFAULT 1,
    status         INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE INDEX idx_batches_series ON batches (test_method_id, workstation_id, status);
CREATE INDEX idx_batches_expiration ON batches (expiration, status);

-- One measurement of a control.
--
-- status 0 leaves the point on the chart, in grey and with the line broken
-- around it, and out of the statistics. It is the only way a result is ever
-- withdrawn: there is no logical deletion and no delete in the program.
--
-- A wrong value is corrected and the old one stays in audit_results; a result
-- entered on the wrong lot is moved to the right one; a duplicate is excluded
-- with the action "Entered twice". Every one of those leaves a trace of what
-- happened, which is what a record is for - and a point in grey with a note
-- saying why tells the truth, where a row made to disappear would say that
-- nobody ever typed it.
CREATE TABLE results (
    result_id   INTEGER   PRIMARY KEY,
    batch_id    INTEGER   NOT NULL REFERENCES batches (batch_id),
    result      REAL      NOT NULL,
    received    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reagent_lot TEXT,
    status      INTEGER   NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
    created_by  INTEGER   REFERENCES users (user_id),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_results_batch ON results (batch_id, status);
CREATE INDEX idx_results_received ON results (received);

-- What was seen and what was done about it. With no validation step, this is
-- where a non conformity is written down: it carries the whole weight.
CREATE TABLE notes (
    note_id     INTEGER   PRIMARY KEY,
    result_id   INTEGER   NOT NULL REFERENCES results (result_id) ON DELETE CASCADE,
    action_id   INTEGER   NOT NULL REFERENCES actions (action_id),
    description TEXT      NOT NULL,
    modified    DATE      NOT NULL,
    created_by  INTEGER   REFERENCES users (user_id),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status      INTEGER   NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

CREATE INDEX idx_notes_result ON notes (result_id, status);

-- ------------------------------------------- external quality assessment

-- Internal control answers whether the method is doing today what it did
-- yesterday. It cannot answer whether what it does is right, because the
-- target it is judged against is the laboratory's own: a method can sit
-- perfectly on a mean that has been wrong for six months, and the chart will
-- never say so.
--
-- A proficiency scheme is the other half. The same sample goes to everybody,
-- the value comes from outside, and what comes back is how far this
-- laboratory fell from it. ISO 15189 asks for both, and ISO 13528 says how
-- the arithmetic is done.

CREATE TABLE eqa_schemes (
    scheme_id   INTEGER PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers (supplier_id),
    description TEXT    NOT NULL UNIQUE,
    status      INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1))
);

-- One distribution of a scheme: the sample that arrived, was run, and came
-- back with a report. received is the day it was measured, which is the day
-- the performance belongs to; reported is the day the report came, which is
-- usually weeks later and is why the two are not one column.
CREATE TABLE eqa_rounds (
    round_id    INTEGER   PRIMARY KEY,
    scheme_id   INTEGER   NOT NULL REFERENCES eqa_schemes (scheme_id),
    description TEXT      NOT NULL,
    received    DATE      NOT NULL,
    reported    DATE,
    status      INTEGER   NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
    created_by  INTEGER   REFERENCES users (user_id),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (scheme_id, description)
);

-- What this laboratory reported for one analyte of one round, beside what the
-- scheme said it should have been.
--
-- assigned is the value the scheme assigned: a consensus of the participants,
-- a reference method, or the way the material was made. sd is the standard
-- deviation the scheme judges by - sigma-pt in ISO 13528, the target spread,
-- which is a decision about fitness for purpose and not the spread the
-- participants happened to have.
--
-- The z score is not a column. It is (result - assigned) / sd, and storing it
-- would allow a row in which those three numbers do not give the fourth.
CREATE TABLE eqa_results (
    eqa_id         INTEGER   PRIMARY KEY,
    round_id       INTEGER   NOT NULL REFERENCES eqa_rounds (round_id),
    test_method_id INTEGER   NOT NULL REFERENCES test_methods (test_method_id),
    result         REAL      NOT NULL,
    assigned       REAL      NOT NULL,
    sd             REAL      NOT NULL CHECK (sd > 0),
    status         INTEGER   NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
    created_by     INTEGER   REFERENCES users (user_id),
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (round_id, test_method_id)
);

CREATE INDEX idx_eqa_results_round ON eqa_results (round_id, status);
CREATE INDEX idx_eqa_results_method ON eqa_results (test_method_id);

-- ---------------------------------------------------------------- audit trail

-- Nothing is deleted quietly and nothing is changed quietly: every insert,
-- update and delete on results and batches lands here, with the values as they
-- were, who did it and when. This is what replaces the validation workflow.

CREATE TABLE audit_results (
    audit_id    INTEGER   PRIMARY KEY,
    operation   TEXT      NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    result_id   INTEGER   NOT NULL,
    batch_id    INTEGER,
    result      REAL,
    received    TIMESTAMP,
    reagent_lot TEXT,
    status      INTEGER,
    log_time    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_id      INTEGER,
    log_host    TEXT
);

CREATE INDEX idx_audit_results_result ON audit_results (result_id, log_time);

CREATE TABLE audit_batches (
    audit_id   INTEGER   PRIMARY KEY,
    operation  TEXT      NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    batch_id   INTEGER   NOT NULL,
    lot_number TEXT,
    target     REAL,
    sd         REAL,
    lower      REAL,
    upper      REAL,
    status     INTEGER,
    log_time   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_id     INTEGER,
    log_host   TEXT
);

CREATE INDEX idx_audit_batches_batch ON audit_batches (batch_id, log_time);

-- A result sent to a proficiency scheme is a result, and the same promise
-- covers it: what it was before a correction is kept here.
CREATE TABLE audit_eqa_results (
    audit_id       INTEGER   PRIMARY KEY,
    operation      TEXT      NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    eqa_id         INTEGER   NOT NULL,
    round_id       INTEGER,
    test_method_id INTEGER,
    result         REAL,
    assigned       REAL,
    sd             REAL,
    status         INTEGER,
    log_time       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_id         INTEGER,
    log_host       TEXT
);

CREATE INDEX idx_audit_eqa_results_eqa ON audit_eqa_results (eqa_id, log_time);

-- On insert the new row is kept, on update and delete the row as it was.

CREATE TRIGGER tr_results_insert AFTER INSERT ON results
BEGIN
    INSERT INTO audit_results (operation, result_id, batch_id, result, received,
                               reagent_lot, status, log_id, log_host)
    VALUES ('INSERT', NEW.result_id, NEW.batch_id, NEW.result, NEW.received,
            NEW.reagent_lot, NEW.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_results_update AFTER UPDATE ON results
BEGIN
    INSERT INTO audit_results (operation, result_id, batch_id, result, received,
                               reagent_lot, status, log_id, log_host)
    VALUES ('UPDATE', OLD.result_id, OLD.batch_id, OLD.result, OLD.received,
            OLD.reagent_lot, OLD.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_results_delete AFTER DELETE ON results
BEGIN
    INSERT INTO audit_results (operation, result_id, batch_id, result, received,
                               reagent_lot, status, log_id, log_host)
    VALUES ('DELETE', OLD.result_id, OLD.batch_id, OLD.result, OLD.received,
            OLD.reagent_lot, OLD.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_batches_insert AFTER INSERT ON batches
BEGIN
    INSERT INTO audit_batches (operation, batch_id, lot_number, target, sd,
                               lower, upper, status, log_id, log_host)
    VALUES ('INSERT', NEW.batch_id, NEW.lot_number, NEW.target, NEW.sd,
            NEW.lower, NEW.upper, NEW.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_batches_update AFTER UPDATE ON batches
BEGIN
    INSERT INTO audit_batches (operation, batch_id, lot_number, target, sd,
                               lower, upper, status, log_id, log_host)
    VALUES ('UPDATE', OLD.batch_id, OLD.lot_number, OLD.target, OLD.sd,
            OLD.lower, OLD.upper, OLD.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_batches_delete AFTER DELETE ON batches
BEGIN
    INSERT INTO audit_batches (operation, batch_id, lot_number, target, sd,
                               lower, upper, status, log_id, log_host)
    VALUES ('DELETE', OLD.batch_id, OLD.lot_number, OLD.target, OLD.sd,
            OLD.lower, OLD.upper, OLD.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_eqa_results_insert AFTER INSERT ON eqa_results
BEGIN
    INSERT INTO audit_eqa_results (operation, eqa_id, round_id, test_method_id,
                                   result, assigned, sd, status, log_id, log_host)
    VALUES ('INSERT', NEW.eqa_id, NEW.round_id, NEW.test_method_id,
            NEW.result, NEW.assigned, NEW.sd, NEW.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_eqa_results_update AFTER UPDATE ON eqa_results
BEGIN
    INSERT INTO audit_eqa_results (operation, eqa_id, round_id, test_method_id,
                                   result, assigned, sd, status, log_id, log_host)
    VALUES ('UPDATE', OLD.eqa_id, OLD.round_id, OLD.test_method_id,
            OLD.result, OLD.assigned, OLD.sd, OLD.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;

CREATE TRIGGER tr_eqa_results_delete AFTER DELETE ON eqa_results
BEGIN
    INSERT INTO audit_eqa_results (operation, eqa_id, round_id, test_method_id,
                                   result, assigned, sd, status, log_id, log_host)
    VALUES ('DELETE', OLD.eqa_id, OLD.round_id, OLD.test_method_id,
            OLD.result, OLD.assigned, OLD.sd, OLD.status,
            (SELECT user_id FROM session WHERE session_id = 1),
            (SELECT host FROM session WHERE session_id = 1));
END;
