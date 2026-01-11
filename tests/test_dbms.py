"""
Test suite for DBMS class - the database layer of Biovarase.

This is the foundation layer that handles all database operations.
Tests cover both unit tests (with mocks) and integration tests (real database).

Key methods tested:
    - _validate_sql_identifier(): SQL injection prevention
    - _set_connection(): Connection establishment
    - _ensure_connection(): Connection verification/reconnection
    - read(): SELECT queries with fetch/fetchone
    - write(): INSERT/UPDATE/DELETE with lastrowid/rowcount
    - _get_columns(): Get column names from table
    - build_sql(): Generate INSERT/UPDATE SQL
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dbms import DBMS


# ============================================================================
# Test Database Configuration
# ============================================================================

TEST_DB_CONFIG = {
    "user": "biovarase_test",
    "password": "test_password_123",
    "database": "biovarase_test",
    "host": "localhost",
    "port": 3306,
}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def db_connection():
    """Create a real DBMS connection for integration tests."""
    import mariadb

    try:
        # Test raw connection first
        conn = mariadb.connect(
            user=TEST_DB_CONFIG["user"],
            password=TEST_DB_CONFIG["password"],
            database=TEST_DB_CONFIG["database"],
            host=TEST_DB_CONFIG["host"],
            port=TEST_DB_CONFIG["port"],
        )
        conn.close()
    except mariadb.Error as e:
        pytest.skip(f"Cannot connect to test database: {e}")

    # Now create DBMS instance
    dbms = DBMS(
        user=TEST_DB_CONFIG["user"],
        password=TEST_DB_CONFIG["password"],
        database=TEST_DB_CONFIG["database"],
        host=TEST_DB_CONFIG["host"],
        port=TEST_DB_CONFIG["port"],
    )

    # Add mock on_log to prevent errors
    dbms.on_log = MagicMock()

    yield dbms

    # Cleanup
    if dbms.con:
        try:
            dbms.con.close()
        except Exception:
            pass


@pytest.fixture
def mock_dbms():
    """Create a mock DBMS for unit testing without real DB."""
    dbms = MagicMock(spec=DBMS)
    dbms.on_log = MagicMock()
    return dbms


# ============================================================================
# Unit Tests - _validate_sql_identifier()
# ============================================================================

class TestValidateSQLIdentifier:
    """Test SQL identifier validation for injection prevention."""

    def test_valid_simple_name(self):
        """Simple table name should pass."""
        dbms = MagicMock()
        dbms.on_log = MagicMock()
        # Call the real method
        DBMS._validate_sql_identifier(dbms, "users", "table")
        # Should not raise

    def test_valid_with_underscore(self):
        """Name with underscore should pass."""
        dbms = MagicMock()
        DBMS._validate_sql_identifier(dbms, "test_methods", "table")

    def test_valid_with_numbers(self):
        """Name with numbers (not first) should pass."""
        dbms = MagicMock()
        DBMS._validate_sql_identifier(dbms, "users123", "table")

    def test_valid_starting_with_underscore(self):
        """Name starting with underscore should pass."""
        dbms = MagicMock()
        DBMS._validate_sql_identifier(dbms, "_private_table", "table")

    def test_invalid_starts_with_number(self):
        """Name starting with number should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError) as exc_info:
            DBMS._validate_sql_identifier(dbms, "123users", "table")
        assert "Invalid SQL table name" in str(exc_info.value)

    def test_invalid_with_semicolon(self):
        """Name with semicolon (SQL injection) should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError):
            DBMS._validate_sql_identifier(dbms, "users;DROP TABLE", "table")

    def test_invalid_with_dash(self):
        """Name with dash should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError):
            DBMS._validate_sql_identifier(dbms, "user-table", "table")

    def test_invalid_with_space(self):
        """Name with space should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError):
            DBMS._validate_sql_identifier(dbms, "user table", "table")

    def test_invalid_empty_string(self):
        """Empty string should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError):
            DBMS._validate_sql_identifier(dbms, "", "table")

    def test_invalid_sql_comment(self):
        """SQL comment injection should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError):
            DBMS._validate_sql_identifier(dbms, "users--", "table")

    def test_invalid_quotes(self):
        """Quotes should fail."""
        dbms = MagicMock()
        with pytest.raises(ValueError):
            DBMS._validate_sql_identifier(dbms, "users'", "table")

    @pytest.mark.parametrize("identifier,valid", [
        ("users", True),
        ("Users", True),
        ("USERS", True),
        ("_users", True),
        ("users_table", True),
        ("users123", True),
        ("u", True),
        ("123users", False),
        ("users;", False),
        ("users--", False),
        ("users/*", False),
        ("", False),
        ("user table", False),
        ("user-table", False),
        ("user.table", False),
        ("user'table", False),
    ])
    def test_identifier_validation_parametrized(self, identifier, valid):
        """Parametrized test for SQL identifier validation."""
        dbms = MagicMock()
        if valid:
            # Should not raise
            DBMS._validate_sql_identifier(dbms, identifier, "table")
        else:
            with pytest.raises(ValueError):
                DBMS._validate_sql_identifier(dbms, identifier, "table")


# ============================================================================
# Integration Tests - Connection
# ============================================================================

@pytest.mark.integration
class TestConnection:
    """Test database connection management."""

    def test_connection_is_established(self, db_connection):
        """DBMS should have active connection after init."""
        assert db_connection.con is not None

    def test_connection_is_open(self, db_connection):
        """Connection should be open."""
        # mariadb connector doesn't have .open attribute, verify with query
        cursor = db_connection.con.cursor(dictionary=True)
        cursor.execute("SELECT 1")
        cursor.close()

    def test_connection_uses_correct_database(self, db_connection):
        """Should be connected to test database."""
        cursor = db_connection.con.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE() AS db_name")
        row = cursor.fetchone()
        cursor.close()
        assert row["db_name"] == "biovarase_test"

    def test_ensure_connection_when_connected(self, db_connection):
        """_ensure_connection should work when already connected."""
        db_connection._ensure_connection()
        assert db_connection.con is not None
        # Verify connection works
        cursor = db_connection.con.cursor(dictionary=True)
        cursor.execute("SELECT 1")
        cursor.close()


# ============================================================================
# Integration Tests - read()
# ============================================================================

@pytest.mark.integration
class TestRead:
    """Test read() method for SELECT queries."""

    def test_read_fetch_true_returns_list(self, db_connection):
        """read(True, ...) should return a list."""
        result = db_connection.read(True, "SELECT 1 AS value", ())
        assert isinstance(result, list)

    def test_read_fetch_false_returns_dict(self, db_connection):
        """read(False, ...) should return a dict."""
        result = db_connection.read(False, "SELECT 1 AS value", ())
        assert isinstance(result, dict)

    def test_read_fetch_true_empty_returns_empty_list(self, db_connection):
        """read(True, ...) with no results returns empty list."""
        result = db_connection.read(
            True,
            "SELECT * FROM users WHERE user_id = ?",
            (999999,)
        )
        assert result == []

    def test_read_fetch_false_no_result_returns_none(self, db_connection):
        """read(False, ...) with no results returns None."""
        result = db_connection.read(
            False,
            "SELECT * FROM users WHERE user_id = ?",
            (999999,)
        )
        assert result is None

    def test_read_returns_dict_with_column_names(self, db_connection):
        """Results should have column names as keys."""
        result = db_connection.read(
            False,
            "SELECT 1 AS col_a, 2 AS col_b, 'test' AS col_c",
            ()
        )
        assert "col_a" in result
        assert "col_b" in result
        assert "col_c" in result
        assert result["col_a"] == 1
        assert result["col_b"] == 2
        assert result["col_c"] == "test"

    def test_read_with_parameters(self, db_connection):
        """read() should handle parameterized queries."""
        result = db_connection.read(
            False,
            "SELECT ? AS param1, ? AS param2",
            ("value1", 42)
        )
        assert result["param1"] == "value1"
        assert result["param2"] == 42

    def test_read_multiple_rows(self, db_connection):
        """read(True, ...) should return multiple rows."""
        result = db_connection.read(
            True,
            "SELECT 1 AS n UNION SELECT 2 UNION SELECT 3",
            ()
        )
        assert len(result) == 3
        values = [row["n"] for row in result]
        assert 1 in values
        assert 2 in values
        assert 3 in values

    def test_read_from_real_table(self, db_connection):
        """Can read from actual tables."""
        result = db_connection.read(True, "SELECT * FROM tests LIMIT 5", ())
        assert isinstance(result, list)
        if result:
            assert "test_id" in result[0]
            assert "description" in result[0]

    def test_read_with_where_clause(self, db_connection):
        """Can filter with WHERE clause."""
        result = db_connection.read(
            True,
            "SELECT * FROM units WHERE status = ?",
            (1,)
        )
        assert isinstance(result, list)
        for row in result:
            assert row["status"] == 1


# ============================================================================
# Integration Tests - write()
# ============================================================================

@pytest.mark.integration
class TestWrite:
    """Test write() method for INSERT/UPDATE/DELETE."""

    def test_write_insert_returns_lastrowid(self, db_connection):
        """INSERT should return lastrowid."""
        # Insert a test action
        result = db_connection.write(
            "INSERT INTO actions (description, status) VALUES (?, ?)",
            ("TEST_ACTION_DBMS", 1)
        )
        assert result is not None
        assert result > 0

        # Cleanup
        db_connection.write(
            "DELETE FROM actions WHERE description = ?",
            ("TEST_ACTION_DBMS",)
        )

    def test_write_update_returns_rowcount(self, db_connection):
        """UPDATE should return rowcount."""
        # First insert
        insert_id = db_connection.write(
            "INSERT INTO actions (description, status) VALUES (?, ?)",
            ("TEST_UPDATE_DBMS", 1)
        )

        # Update it
        result = db_connection.write(
            "UPDATE actions SET status = ? WHERE action_id = ?",
            (0, insert_id)
        )
        # rowcount should be 1
        assert result == 1

        # Cleanup
        db_connection.write(
            "DELETE FROM actions WHERE action_id = ?",
            (insert_id,)
        )

    def test_write_delete_returns_rowcount(self, db_connection):
        """DELETE should return rowcount."""
        # First insert
        db_connection.write(
            "INSERT INTO actions (description, status) VALUES (?, ?)",
            ("TEST_DELETE_DBMS", 1)
        )

        # Delete it
        result = db_connection.write(
            "DELETE FROM actions WHERE description = ?",
            ("TEST_DELETE_DBMS",)
        )
        assert result >= 1

    def test_write_with_no_rows_affected(self, db_connection):
        """UPDATE/DELETE with no matching rows returns 0."""
        result = db_connection.write(
            "UPDATE actions SET status = ? WHERE action_id = ?",
            (1, 999999)
        )
        assert result == 0

    def test_write_invalid_sql_returns_none(self, db_connection):
        """Invalid SQL should return None and set last_write_error."""
        result = db_connection.write(
            "INSERT INTO nonexistent_table (col) VALUES (?)",
            ("test",)
        )
        assert result is None
        assert db_connection.last_write_error is not None


# ============================================================================
# Integration Tests - _get_columns()
# ============================================================================

@pytest.mark.integration
class TestGetColumns:
    """Test _get_columns() method."""

    def test_get_columns_returns_tuple(self, db_connection):
        """Should return tuple of column names."""
        columns = db_connection._get_columns("users")
        assert isinstance(columns, tuple)

    def test_get_columns_includes_pk_first(self, db_connection):
        """First column should be the primary key."""
        columns = db_connection._get_columns("users")
        assert columns[0] == "user_id"

    def test_get_columns_for_batches(self, db_connection):
        """Should get columns for batches table."""
        columns = db_connection._get_columns("batches")
        assert "batch_id" in columns
        assert "lot_number" in columns
        assert "target" in columns
        assert "sd" in columns

    def test_get_columns_invalid_table_returns_empty(self, db_connection):
        """Invalid table should return empty tuple."""
        columns = db_connection._get_columns("nonexistent_table_xyz")
        assert columns == ()

    @pytest.mark.parametrize("table,expected_pk", [
        ("users", "user_id"),
        ("batches", "batch_id"),
        ("results", "result_id"),
        ("tests", "test_id"),
        ("units", "unit_id"),
    ])
    def test_get_columns_pk_is_first(self, db_connection, table, expected_pk):
        """Primary key should be the first column."""
        columns = db_connection._get_columns(table)
        assert len(columns) > 0
        assert columns[0] == expected_pk


# ============================================================================
# Integration Tests - build_sql()
# ============================================================================

@pytest.mark.integration
class TestBuildSQL:
    """Test build_sql() method for generating INSERT/UPDATE."""

    def test_build_sql_insert(self, db_connection):
        """build_sql('insert') should generate INSERT statement."""
        sql = db_connection.build_sql("actions", "insert")
        assert sql is not None
        assert sql.startswith("INSERT INTO actions")
        assert "VALUES" in sql
        assert "?" in sql
        # Should not include PK (action_id)
        assert "action_id" not in sql.split("(")[1].split(")")[0]

    def test_build_sql_update(self, db_connection):
        """build_sql('update') should generate UPDATE statement."""
        sql = db_connection.build_sql("actions", "update")
        assert sql is not None
        assert sql.startswith("UPDATE actions SET")
        assert "WHERE" in sql
        assert "action_id = ?" in sql

    def test_build_sql_invalid_op_returns_none(self, db_connection):
        """Invalid operation should return None."""
        sql = db_connection.build_sql("actions", "delete")
        assert sql is None

    def test_build_sql_insert_has_correct_placeholders(self, db_connection):
        """INSERT should have correct number of placeholders."""
        sql = db_connection.build_sql("actions", "insert")
        columns = db_connection._get_columns("actions")
        # Number of ? should be len(columns) - 1 (excluding PK)
        placeholder_count = sql.count("?")
        assert placeholder_count == len(columns) - 1

    def test_build_sql_update_has_correct_placeholders(self, db_connection):
        """UPDATE should have correct number of placeholders."""
        sql = db_connection.build_sql("actions", "update")
        columns = db_connection._get_columns("actions")
        # Number of ? should be len(columns) - 1 (SET) + 1 (WHERE) = len(columns)
        placeholder_count = sql.count("?")
        assert placeholder_count == len(columns)

    def test_build_sql_prevents_injection(self, db_connection):
        """build_sql should reject malicious table names."""
        sql = db_connection.build_sql("users; DROP TABLE users", "insert")
        assert sql is None


# ============================================================================
# Integration Tests - Transaction Behavior
# ============================================================================

@pytest.mark.integration
class TestTransactions:
    """Test transaction and autocommit behavior."""

    def test_autocommit_is_true_by_default(self, db_connection):
        """Autocommit should be True by default."""
        assert db_connection.autocommit is True

    def test_write_persists_with_autocommit(self, db_connection):
        """Write should persist immediately with autocommit."""
        # Insert
        insert_id = db_connection.write(
            "INSERT INTO actions (description, status) VALUES (?, ?)",
            ("TEST_AUTOCOMMIT", 1)
        )

        # Read it back in new cursor
        result = db_connection.read(
            False,
            "SELECT * FROM actions WHERE action_id = ?",
            (insert_id,)
        )
        assert result is not None
        assert result["description"] == "TEST_AUTOCOMMIT"

        # Cleanup
        db_connection.write(
            "DELETE FROM actions WHERE action_id = ?",
            (insert_id,)
        )


# ============================================================================
# Integration Tests - Error Handling
# ============================================================================

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in DBMS operations."""

    def test_read_invalid_sql_returns_none(self, db_connection):
        """Invalid SQL in read should return None."""
        result = db_connection.read(True, "INVALID SQL SYNTAX", ())
        assert result is None

    def test_write_invalid_sql_returns_none(self, db_connection):
        """Invalid SQL in write should return None."""
        result = db_connection.write("INVALID SQL SYNTAX", ())
        assert result is None

    def test_write_sets_last_write_error(self, db_connection):
        """Failed write should set last_write_error."""
        db_connection.write("INVALID SQL", ())
        assert db_connection.last_write_error is not None

    def test_write_clears_last_write_error_on_success(self, db_connection):
        """Successful write should clear last_write_error."""
        # First, cause an error
        db_connection.write("INVALID SQL", ())
        assert db_connection.last_write_error is not None

        # Now succeed
        insert_id = db_connection.write(
            "INSERT INTO actions (description, status) VALUES (?, ?)",
            ("TEST_CLEAR_ERROR", 1)
        )
        assert db_connection.last_write_error is None

        # Cleanup
        db_connection.write(
            "DELETE FROM actions WHERE action_id = ?",
            (insert_id,)
        )

    def test_on_log_called_on_error(self, db_connection):
        """on_log should be called when error occurs."""
        db_connection.on_log.reset_mock()
        db_connection.read(True, "INVALID SQL", ())
        assert db_connection.on_log.called


# ============================================================================
# Integration Tests - SQL Injection Prevention
# ============================================================================

@pytest.mark.integration
@pytest.mark.security
class TestSQLInjectionPrevention:
    """Test that SQL injection is prevented."""

    def test_parameterized_query_prevents_injection(self, db_connection):
        """Parameterized queries should prevent SQL injection."""
        # This malicious input should be treated as a literal string
        malicious_input = "'; DROP TABLE users; --"
        result = db_connection.read(
            True,
            "SELECT * FROM users WHERE nickname = ?",
            (malicious_input,)
        )
        # Should return empty list, not cause an error
        assert result == []

        # Verify users table still exists
        result = db_connection.read(True, "SELECT COUNT(*) AS cnt FROM users", ())
        assert result is not None

    def test_build_sql_rejects_injection_in_table_name(self, db_connection):
        """build_sql should reject SQL injection in table name."""
        sql = db_connection.build_sql("users; DROP TABLE users", "insert")
        assert sql is None

    def test_get_columns_rejects_injection(self, db_connection):
        """_get_columns should reject SQL injection."""
        columns = db_connection._get_columns("users; DROP TABLE users")
        assert columns == ()


# ============================================================================
# Parametrized Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.parametrize("table", [
    "users",
    "batches",
    "results",
    "tests",
    "units",
    "controls",
    "methods",
    "samples",
    "actions",
    "organizations",
])
def test_can_read_from_table(db_connection, table):
    """All essential tables should be readable."""
    result = db_connection.read(True, f"SELECT * FROM {table} LIMIT 1", ())
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.parametrize("table", [
    "users",
    "batches",
    "results",
    "tests",
    "units",
    "controls",
])
def test_can_build_insert_for_table(db_connection, table):
    """Should generate INSERT SQL for essential tables."""
    sql = db_connection.build_sql(table, "insert")
    assert sql is not None
    assert sql.startswith(f"INSERT INTO {table}")


@pytest.mark.integration
@pytest.mark.parametrize("table", [
    "users",
    "batches",
    "results",
    "tests",
    "units",
    "controls",
])
def test_can_build_update_for_table(db_connection, table):
    """Should generate UPDATE SQL for essential tables."""
    sql = db_connection.build_sql(table, "update")
    assert sql is not None
    assert sql.startswith(f"UPDATE {table} SET")
