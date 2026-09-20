# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The database, and what can be asked of it.

One SQLite file beside the program. There is no host, no port, no user and no
password: the laboratory is the file, and whoever can open the file is in.

A failed statement is written to the log and raised again. It never comes back
as an empty result: a read that fails must not look like a table with no rows
in it.
"""
import datetime
import os
import socket
import sqlite3 as lite


class DBMS:
    """Connection to the database, and the statements built from its schema."""

    def __init__(self, database, log):
        # Both are given by whoever creates the object: the application passes
        # the file beside the program and its Log, a test passes ":memory:"
        # and a log of its own.
        self.database = database
        self.log = log
        #: table -> its columns as get_table_info returns them, remembered
        #: after the first time they are asked of the schema.
        self.dict_tables = {}
        self.set_types()
        self.set_connection()

    def __str__(self):
        return "class: {0}\nMRO: {1}".format(self.__class__.__name__,
                                             [x.__name__ for x in DBMS.__mro__],)

    def set_types(self):
        """Teach sqlite3 the two conversions it is handing back.

        SQLite has no type for a date: a date is text in a column that says
        DATE, and sqlite3 turned that text into a datetime.date on the way
        out and back into text on the way in. Both default conversions are
        deprecated as of Python 3.12 and will be removed, and the day they go
        every date this program reads comes back a string. That does not fail
        where it happens. It fails later, in a comparison that answers a
        question about a period and answers it wrongly.

        These are the same conversions, written down here where they can be
        read. The database holds ISO throughout - 2027-07-12 for a day,
        2026-03-24 07:05:00 for a moment - which is what isoformat() writes
        and fromisoformat() reads back. A registration is for the module and
        not for one connection; doing it again does no harm.
        """
        lite.register_adapter(datetime.date, self.adapt_date)
        lite.register_adapter(datetime.datetime, self.adapt_datetime)
        lite.register_converter("DATE", self.convert_date)
        lite.register_converter("TIMESTAMP", self.convert_timestamp)

    def adapt_date(self, value):
        """A day on its way into the database: 2027-07-12."""
        return value.isoformat()

    def adapt_datetime(self, value):
        """A moment on its way in: 2026-03-24 07:05:00.

        A space between the day and the hour, which is what SQLite's own
        CURRENT_TIMESTAMP writes in the columns that have a default, and so
        what the rest of the table already looks like.
        """
        return value.isoformat(" ")

    def convert_date(self, value):
        """A DATE column on its way out, as a datetime.date."""
        return datetime.date.fromisoformat(value.decode())

    def convert_timestamp(self, value):
        """A TIMESTAMP column on its way out, as a datetime.datetime."""
        return datetime.datetime.fromisoformat(value.decode())

    def set_connection(self):
        """Open the database and say how rows come back.

        Foreign keys are off by default in SQLite and have to be asked for on
        every connection: without this a result could point at a lot that is
        not there.
        """
        self.con = lite.connect(self.database,
                                detect_types=lite.PARSE_DECLTYPES | lite.PARSE_COLNAMES,
                                isolation_level='IMMEDIATE')
        # Every row can be read by column name, row["target"], and not only by
        # position, row[6], which silently changes meaning the day a column is
        # added.
        self.con.row_factory = lite.Row
        self.con.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Close the connection. The file stays where it is."""
        self.con.close()

    def __enter__(self):
        """Enter a with block: the connection is already open."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Leave a with block closing the connection, error or not."""
        self.close()

    def read(self, fetch, sql, args=()):
        """Run a SELECT and return its rows.

        fetch True returns a list, empty when no row matched, so it is tested
        with 'if rows'. fetch False returns one row or None, tested with
        'if row is not None'.

        A failed query is written to the log, with the statement, and raised
        again: it never turns into an empty result.

        @param name: fetch, sql, args
        @return: rows
        @rtype: list or row
        """
        cur = self.con.cursor()
        try:
            cur.execute(sql, args)
            if fetch is True:
                rs = cur.fetchall()
            else:
                rs = cur.fetchone()
        except lite.Error:
            self.log.error("read failed: {0}".format(sql))
            raise
        finally:
            cur.close()

        return rs

    def write(self, sql, args=()):
        """Run one statement and commit it; return the id of the new row.

        A failed statement is rolled back, written to the log with the
        statement, and raised again. On an UPDATE or a DELETE there is no new
        row: lastrowid is meaningless and the number of rows touched is what
        the caller wants, so that is what comes back.

        @param name: sql, args
        @return: lastrowid on an insert, rows touched otherwise
        @rtype: integer
        """
        cur = self.con.cursor()
        try:
            cur.execute(sql, args)
            self.con.commit()
            if sql.lstrip()[:6].upper() == "INSERT":
                written = cur.lastrowid
            else:
                written = cur.rowcount
        except lite.Error:
            self.con.rollback()
            self.log.error("write failed, rolled back: {0}".format(sql))
            raise
        finally:
            cur.close()

        return written

    def set_session_user(self, user_id):
        """Say who is working and from which machine, for the triggers to write.

        SQLite has no CURRENT_USER and no way to ask which computer is
        connected. The triggers read this one row, so the login writes it
        here: the name and the host in the audit trail come from the session,
        not from whatever the window happened to know.

        The host is the machine the program is running on. It is worth
        recording because the database file can live on a shared folder, and
        then the same row can be written from any of four benches.

        @param name: user_id
        """
        self.write("UPDATE session SET user_id = ?, host = ? WHERE session_id = 1",
                   (user_id, socket.gethostname()))

    def get_dict(self, row):
        """A row as a dictionary; None stays None.

        @param name: row
        @return: the row as a dictionary
        @rtype: dictionary
        """
        found = None
        if row is not None:
            found = dict(row)
        return found

    def get_table_info(self, table):
        """What a table is made of, asked of the schema once and then remembered.

        PRAGMA table_info says, for every column, its name and whether it is
        the primary key: nothing is guessed from the order of the columns.

        The answer is kept in dict_tables - memoization, by hand; the standard
        library would do it with functools.lru_cache. It is safe because the
        program changes the data and never the structure of a table while it
        runs.

        @param name: table
        @return: (name, is primary key) per column, in table order
        @rtype: list
        """
        if table not in self.dict_tables:
            rows = self.read(True, "PRAGMA table_info({0})".format(table))
            if not rows:
                raise ValueError("no table {0}".format(table))
            self.dict_tables[table] = [(row["name"], bool(row["pk"])) for row in rows]

        return self.dict_tables[table]

    def get_primary_key(self, table):
        """The primary key column of a table, asked of the schema.

        @param name: table
        @return: column name
        @rtype: string
        """
        keys = [name for name, is_key in self.get_table_info(table) if is_key]

        if len(keys) != 1:
            raise ValueError("{0} has {1} primary key columns, not one".format(table,
                                                                               len(keys)))

        return keys[0]

    def get_fields(self, table):
        """Column names of a table, primary key excluded, in table order.

        The key is left out because the schema says it is the key, not because
        it happens to be the first column.

        @param name: table
        @return: fields
        @rtype: tuple
        """
        return tuple(name for name, is_key in self.get_table_info(table) if not is_key)

    def get_args(self, table, values):
        """The values of a row as a list, in the order the schema declares.

        values is a dictionary keyed by column name, so no window has to know
        the order of the columns. A missing column and an unknown one are both
        refused, naming the table: a value written one column further along is
        the kind of error that is found months later, in the data.

        @param name: table, values
        @return: args
        @rtype: list
        """
        fields = self.get_fields(table)
        missing = [name for name in fields if name not in values]
        unknown = [name for name in values if name not in fields]

        if missing or unknown:
            raise ValueError("{0}: missing {1}, not a column {2}".format(table,
                                                                        missing,
                                                                        unknown))

        return [values[name] for name in fields]

    def get_insert(self, table, values):
        """An INSERT and its args, with the values given by column name.

        @param name: table, values
        @return: sql, args
        @rtype: tuple
        """
        fields = self.get_fields(table)
        sql = "INSERT INTO {0} ({1}) VALUES ({2})".format(table,
                                                          ", ".join(fields),
                                                          ", ".join("?" * len(fields)))

        return (sql, self.get_args(table, values))

    def get_update(self, table, key_value, values):
        """An UPDATE and its args, with the values given by column name.

        The primary key is asked of the schema and its value goes last.

        @param name: table, key_value, values
        @return: sql, args
        @rtype: tuple
        """
        assignments = ", ".join("{0} = ?".format(name) for name in self.get_fields(table))
        sql = "UPDATE {0} SET {1} WHERE {2} = ?".format(table,
                                                        assignments,
                                                        self.get_primary_key(table))
        args = self.get_args(table, values)
        args.append(key_value)

        return (sql, args)

    def get_selected(self, table, field, *args):
        """One row, by any column, as a dictionary keyed by column name.

        @param name: table, field, args
        @return: the row
        @rtype: dictionary
        """
        sql = "SELECT * FROM {0} WHERE {1} = ?".format(table, field)

        return self.get_dict(self.read(False, sql, args))

    def check(self):
        """Ask SQLite whether the file is still sound, page by page.

        PRAGMA integrity_check reads the whole database and reports what it
        finds: "ok", or a list of what is wrong with it. On a file kept on a
        shared folder this is the question worth asking now and then, because
        corruption there is silent until something reads the damaged page.

        @return: what SQLite answered
        @rtype: string
        """
        rows = self.read(True, "PRAGMA integrity_check")

        return "\n".join(row[0] for row in rows)

    def vacuum(self):
        """Rebuild the file, leaving out the space deleted rows left behind.

        SQLite does not give pages back when rows go: it keeps them for the
        next insert. After a cleanup that is a file larger than its contents,
        and vacuum writes it again from scratch, in order.

        It cannot run inside a transaction, so the connection is committed
        first; it needs room for a second copy of the database while it works.

        @return: how many bytes the file lost
        @rtype: integer
        """
        before = os.path.getsize(self.database)

        self.con.commit()
        # isolation_level None for the duration: VACUUM is refused inside the
        # transaction the driver would otherwise open for it.
        level = self.con.isolation_level
        self.con.isolation_level = None
        self.con.execute("VACUUM")
        self.con.isolation_level = level

        return before - os.path.getsize(self.database)

    def dump(self, folder):
        """Write the whole database as SQL into folder; return the file's path.

        The file is named after the moment, YYYYMMDDHHMMSS.sql, so dumps sort
        by date and never overwrite each other. The folder is created the
        first time.

        @param name: folder
        @return: path of the file written
        @rtype: string
        """
        name = "{0}.sql".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        path = os.path.join(folder, name)

        os.makedirs(folder, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for line in self.con.iterdump():
                f.write("{0}\n".format(line))

        return path
