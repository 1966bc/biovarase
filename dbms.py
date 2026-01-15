#!/usr/bin/env python3
"""
Database Management System (DBMS) layer for Biovarase.

This module provides the DBMS class, which handles MariaDB database connections,
query execution, and connection management with automatic reconnection capabilities.

Architecture:
    - DBMS: Base database layer (this module)
    - Controller: Extends DBMS with SQL builders and domain logic
    - Engine: Main orchestrator combining all mixins including Controller

Key Features:
    - Automatic connection management with reconnection on failure
    - Dictionary-based result sets (no positional indexing)
    - Parameterized query support (SQL injection prevention)
    - Comprehensive error logging
    - Transaction support with rollback

Security:
    - All table/column names validated against SQL identifier regex
    - Mandatory use of parameterized queries (no string concatenation)
    - Credentials never logged or exposed

Classes:
    DBMS: Database connection and query execution layer

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import sys
import inspect
import re
import mariadb
from typing import Optional, Union, List, Dict, Tuple, Any


class BackgroundConnection:
    """
    Dedicated database connection for background thread operations.

    Provides the same read/write interface as DBMS but with its own
    independent connection. This allows background threads to execute
    queries without blocking the main thread's connection.

    Usage:
        bg_conn = engine.get_background_connection()
        try:
            rows = bg_conn.read(True, "SELECT * FROM tests", ())
            # ... do work ...
        finally:
            bg_conn.close()

    Note:
        Always close the connection when done to free resources.
    """

    def __init__(self, user, password, host, port, database, on_log=None):
        """Create a new background connection."""
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.on_log = on_log or (lambda *args: None)
        self.con = None
        self._connect()

    def _connect(self):
        """Establish the database connection."""
        try:
            self.con = mariadb.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
                autocommit=True
            )
        except Exception as e:
            self.on_log("BackgroundConnection._connect", e, type(e), __name__)
            self.con = None

    def read(self, fetch, sql, args=()):
        """Execute SELECT query. Same interface as DBMS.read()."""
        if self.con is None:
            return None

        cursor = None
        try:
            cursor = self.con.cursor(dictionary=True)
            cursor.execute(sql, args)
            if fetch:
                return cursor.fetchall()
            else:
                return cursor.fetchone()
        except Exception as e:
            self.on_log("BackgroundConnection.read", e, type(e), __name__)
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

    def write(self, sql, args=()):
        """Execute DML statement. Same interface as DBMS.write()."""
        if self.con is None:
            return None

        cursor = None
        try:
            cursor = self.con.cursor()
            cursor.execute(sql, args)
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        except Exception as e:
            self.on_log("BackgroundConnection.write", e, type(e), __name__)
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

    def close(self):
        """Close the connection and free resources."""
        if self.con:
            try:
                self.con.close()
            except Exception:
                pass
            self.con = None

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection on context exit."""
        self.close()
        return False


class DBMS:
    """
    Database Management System base layer for MariaDB operations.

    Provides connection management, query execution, and database operations
    with automatic reconnection, error handling, and comprehensive logging.

    This is the foundation layer of Biovarase's data access architecture.
    Controller extends this class with SQL builders and domain logic.

    Attributes:
        user (str): Database username
        password (str): Database password
        database (str): Database name
        host (str): Database server hostname (default: localhost)
        port (int): Database server port (default: 3306)
        autocommit (bool): Enable autocommit mode (default: True)
        con: MariaDB connection object (managed internally)

    Connection Management:
        - Automatic connection on initialization
        - Auto-reconnection via _ensure_connection()
        - Proper cleanup and cursor management
        - Connection validation before each query

    Query Execution:
        - read(): Execute SELECT queries, return dict results
        - write(): Execute INSERT/UPDATE/DELETE with auto-commit or rollback
        - Parameterized queries only (SQL injection prevention)
        - Dictionary cursor for named-key access (no positional indexing)

    Error Handling:
        - All database errors logged via on_log()
        - Graceful degradation (returns None on failure)
        - Automatic rollback on write failures
        - Comprehensive error context in logs

    Security:
        - SQL identifier validation (table/column names)
        - Mandatory parameterized queries
        - No credentials in logs or exceptions
        - Connection encryption support

    Example:
        >>> dbms = DBMS("user", "password", "biovarase")
        >>> rows = dbms.read(True, "SELECT * FROM tests WHERE enable = ?", (1,))
        >>> for row in rows:
        ...     print(row["description"])  # Named-key access
    """
    def __init__(
        self,
        user: str,
        password: str,
        database: str,
        host: str = 'localhost',
        port: int = 3306,
        autocommit: bool = True
    ) -> None:

        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.autocommit = autocommit
        self.last_write_error = None
        self.con = self._set_connection()

    def __str__(self) -> str:
        return "class: {0}\nMRO: {1}".format(self.__class__.__name__,
                                             [x.__name__ for x in DBMS.__mro__],)

    def _validate_sql_identifier(self, identifier: str, identifier_type: str = "identifier") -> None:
        """
        Validate SQL identifier (table/column name) to prevent SQL injection.

        Args:
            identifier: Table or column name to validate
            identifier_type: Type description for error message (e.g., "table", "column")

        Raises:
            ValueError: If identifier contains invalid characters

        Note:
            Valid SQL identifiers must match: ^[a-zA-Z_][a-zA-Z0-9_]*$
            This prevents SQL injection via table/column name manipulation.
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(
                f"Invalid SQL {identifier_type} name: '{identifier}'. "
                f"Must match pattern: ^[a-zA-Z_][a-zA-Z0-9_]*$"
            )

    def _set_connection(self) -> Optional[Any]:
        try:
            return mariadb.connect(
                user=self.user, password=self.password,
                host=self.host, port=self.port,
                database=self.database, autocommit=self.autocommit
            )
        except Exception as e:
            f = inspect.currentframe()
            function = f.f_code.co_name
            caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
            self.on_log(function, e, type(e), sys.modules[__name__], caller)
            return None

    def get_background_connection(self) -> BackgroundConnection:
        """
        Create a new independent database connection for background operations.

        Returns a BackgroundConnection instance with the same credentials as
        the main connection. Use this for long-running operations in worker
        threads to avoid blocking the main thread.

        Returns:
            BackgroundConnection: New connection instance

        Example:
            def worker():
                with self.engine.get_background_connection() as bg:
                    rows = bg.read(True, "SELECT * FROM results", ())
                    # ... process data ...
        """
        return BackgroundConnection(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            on_log=self.on_log
        )

    def _ensure_connection(self) -> None:
        """
        Ensure there is an active DB connection.
        - If no connection, open a new one.
        - If connection exists, ping it; if ping fails, reopen it.
        This keeps the API KISS and resilient to idle timeouts.
        """
        # no connection yet → open
        if self.con is None:
            self.con = self._set_connection()
            return

        # try to ping; if not available, run a lightweight SELECT 1
        try:
            ping = getattr(self.con, "ping", None)
            if callable(ping):
                try:
                    ping(reconnect=True)  # works for many connectors
                except TypeError:
                    ping()               # fallback if reconnect kw not supported
            else:
                cur = None
                try:
                    cur = self.con.cursor()
                    cur.execute("SELECT 1")
                finally:
                    if cur:
                        cur.close()
        except Exception:
            # ping failed → reconnect
            self.con = self._set_connection()


    def read(
        self,
        fetch: bool,
        sql: str,
        args: Tuple = ()
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Execute a SELECT query and return results as dictionaries.

        Args:
            fetch (bool):
                - True  → return a list of dictionaries (possibly empty)
                - False → return a single dictionary or None when no rows
            sql (str): SQL query string
            args (tuple): parameters for the query (default: ())

        Returns:
            list[dict] | dict | None
                Example (fetch=True):
                    [{'id': 1, 'description': 'Chemistry'},
                     {'id': 2, 'description': 'Hematology'}]
                Example (fetch=False):
                    {'id': 1, 'description': 'Chemistry'}
                Returns None on error.
        """
        cursor = None
        try:
            self._ensure_connection()
            if self.con is None:
                raise RuntimeError("No active DB connection")

            # use dictionary cursor
            cursor = self.con.cursor(dictionary=True)
            cursor.execute(sql, args)

            if fetch:
                return cursor.fetchall()  # → list of dicts (possibly empty)
            else:
                return cursor.fetchone()  # → single dict or None

        except Exception as e:
            f = inspect.currentframe()
            function = f.f_code.co_name
            caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
            self.on_log(function, e, type(e), sys.modules[__name__], caller)
            return None

        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as e:
                    f = inspect.currentframe()
                    function = f.f_code.co_name + ".close"
                    caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
                    self.on_log(function, e, type(e), sys.modules[__name__], caller)

    def write(self, sql: str, args: Tuple = ()) -> Optional[int]:
        """
        Execute a DML statement (INSERT/UPDATE/DELETE).
        Returns:
          - lastrowid when available and non-zero,
          - otherwise the affected rowcount,
          - None on error (error stored in last_write_error).
        Commits only if autocommit is disabled.
        """
        cursor = None
        self.last_write_error = None
        try:

            self._ensure_connection()
            
            if self.con is None:
                raise RuntimeError("No active DB connection")

            cursor = self.con.cursor()
            cursor.execute(sql, args)

            # Commit only when autocommit is disabled
            if not getattr(self, "autocommit", True):
                self.con.commit()

            # Prefer lastrowid; fallback to rowcount if not meaningful
            last_id = getattr(cursor, "lastrowid", None)
            return last_id if last_id not in (None, 0) else cursor.rowcount

        except Exception as e:
            # Rollback only if autocommit is disabled
            try:
                if cursor and not getattr(self, "autocommit", True):
                    self.con.rollback()
            except Exception:
                pass

            self.last_write_error = e
            f = inspect.currentframe()
            function = f.f_code.co_name
            caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
            self.on_log(function, e, type(e), sys.modules[__name__], caller)
            return None

        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as e:
                    f = inspect.currentframe()
                    function = f.f_code.co_name + ".close"
                    caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
                    self.on_log(function, e, type(e), sys.modules[__name__], caller)

    def _get_columns(self, table: str) -> Tuple[str, ...]:
        """
        Internal helper.
        Return all column names in declaration order (PK included as the first column).
        Uses LIMIT 0 to fetch only metadata from the cursor.
        """
        cursor = None
        try:
            # Validate table name to prevent SQL injection
            self._validate_sql_identifier(table, "table")

            self._ensure_connection()
            if self.con is None:
                raise RuntimeError("No active DB connection")

            sql = f"SELECT * FROM {table} LIMIT 0"
            cursor = self.con.cursor()
            cursor.execute(sql)
            return tuple(desc[0] for desc in (cursor.description or ()))
        except Exception as e:
                f = inspect.currentframe()
                function = f.f_code.co_name
                caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
                self.on_log(function, e, type(e), sys.modules[__name__], caller)
                return tuple()
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as e:
                    f = inspect.currentframe()
                    function = f.f_code.co_name + ".close"
                    caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
                    self.on_log(function, e, type(e), sys.modules[__name__], caller)

    def build_sql(self, table: str, op: str) -> Optional[str]:
        """
        Generate SQL for INSERT or UPDATE using project conventions:
        - PK is the first column
        - placeholders use '?'
        """
        try:
            # Validate table name to prevent SQL injection
            self._validate_sql_identifier(table, "table")

            all_cols = list(self._get_columns(table))  # includes PK as first column
        
            if op == "insert":
                fields = all_cols[1:]  # skip PK
                cols_list = ",".join(fields)
                placeholders = ",".join(["?"] * len(fields))
                return f"INSERT INTO {table}({cols_list}) VALUES({placeholders})"

            elif op == "update":
                primary_key = all_cols[0]
                set_cols = [c for c in all_cols if c != primary_key]
                set_clause = ", ".join(f"{c} = ?" for c in set_cols)
                return f"UPDATE {table} SET {set_clause} WHERE {primary_key} = ?"

            else:
                raise ValueError("op must be 'insert' or 'update'")

        except Exception as e:
            f = inspect.currentframe()
            function = f.f_code.co_name
            caller = f.f_back.f_code.co_name if f and f.f_back else "<top>"
            self.on_log(function, e, type(e), sys.modules[__name__], caller)
            return None

