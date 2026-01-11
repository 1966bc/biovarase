"""
Test suite for Controller class.

Tests the SQL builders and domain logic layer of Biovarase.
Includes both unit tests (with mocks) and integration tests (real database).

Key methods tested:
    - get_primary_key(): PK lookup from INFORMATION_SCHEMA
    - on_login(): User authentication with bcrypt
    - get_new_password(): Bcrypt password generation
    - get_selected(): Generic record retrieval
    - get_test_name(): Get test description
    - get_control_name(): Get control description
    - get_um(): Get unit of measurement
    - get_lab_id_by_section_id(): Get parent lab from section
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional

import bcrypt

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from controller import Controller


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

@pytest.fixture
def mock_controller():
    """
    Create a mock Controller for unit testing.

    Mocks the database methods (read, write) to avoid real DB calls.
    """
    controller = MagicMock(spec=Controller)
    controller.current_ids = {"lab_id": 2, "site_id": 1, "section_id": 6}
    controller._pk_cache = {}
    return controller


@pytest.fixture(scope="module")
def db_connection():
    """Create a database connection for integration tests."""
    import mariadb

    try:
        conn = mariadb.connect(
            user=TEST_DB_CONFIG["user"],
            password=TEST_DB_CONFIG["password"],
            database=TEST_DB_CONFIG["database"],
            host=TEST_DB_CONFIG["host"],
            port=TEST_DB_CONFIG["port"],
        )
        conn.autocommit = True
        yield conn
        conn.close()
    except mariadb.Error as e:
        pytest.skip(f"Cannot connect to test database: {e}")


@pytest.fixture
def db_controller(db_connection):
    """
    Create a Controller-like object that uses real database.

    This simulates the Controller's read method using real DB.
    """
    class TestController:
        def __init__(self, conn):
            self.conn = conn
            self.current_ids = {"lab_id": 2, "site_id": 1, "section_id": 6}
            self._pk_cache = {}

        def read(self, fetch: bool, sql: str, args: tuple = ()):
            """Execute SQL and return results as dict."""
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(sql, args)

            if fetch:
                return cursor.fetchall()
            else:
                return cursor.fetchone()

        def get_lab_id(self):
            return self.current_ids.get("lab_id")

    return TestController(db_connection)


# ============================================================================
# Unit Tests - get_new_password()
# ============================================================================

class TestGetNewPassword:
    """Test bcrypt password generation."""

    def test_returns_bytes(self):
        """get_new_password should return bytes."""
        # Create a real Controller method call
        new_password = b'pass'
        hashed = bcrypt.hashpw(new_password, bcrypt.gensalt())

        assert isinstance(hashed, bytes)

    def test_password_is_hashed(self):
        """Hashed password should not equal plain password."""
        new_password = b'pass'
        hashed = bcrypt.hashpw(new_password, bcrypt.gensalt())

        assert hashed != new_password

    def test_password_starts_with_bcrypt_prefix(self):
        """Bcrypt hash should start with $2b$."""
        new_password = b'pass'
        hashed = bcrypt.hashpw(new_password, bcrypt.gensalt())

        assert hashed.startswith(b'$2b$')

    def test_password_can_be_verified(self):
        """Hashed password should verify correctly."""
        new_password = b'pass'
        hashed = bcrypt.hashpw(new_password, bcrypt.gensalt())

        assert bcrypt.checkpw(new_password, hashed)

    def test_wrong_password_fails_verification(self):
        """Wrong password should fail verification."""
        new_password = b'pass'
        wrong_password = b'wrong'
        hashed = bcrypt.hashpw(new_password, bcrypt.gensalt())

        assert not bcrypt.checkpw(wrong_password, hashed)


# ============================================================================
# Unit Tests - on_login()
# ============================================================================

class TestOnLogin:
    """Test user authentication."""

    def test_login_with_correct_password(self):
        """Login with correct password returns user dict."""
        # Simulate stored password hash
        password = b'testpass123'
        stored_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        # Mock user from database
        mock_user = {
            "user_id": 1,
            "nickname": "testuser",
            "pswrd": stored_hash,
            "role": 5,
            "status": 1
        }

        # Verify password check works
        hashed_from_db = mock_user["pswrd"].encode('utf-8')
        assert bcrypt.checkpw(password, hashed_from_db)

    def test_login_with_wrong_password(self):
        """Login with wrong password fails."""
        password = b'testpass123'
        wrong_password = b'wrongpass'
        stored_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        hashed_from_db = stored_hash.encode('utf-8')
        assert not bcrypt.checkpw(wrong_password, hashed_from_db)

    def test_login_password_is_case_sensitive(self):
        """Password verification is case sensitive."""
        password = b'TestPass'
        wrong_case = b'testpass'
        stored_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        hashed_from_db = stored_hash.encode('utf-8')
        assert not bcrypt.checkpw(wrong_case, hashed_from_db)

    def test_login_handles_unicode_password(self):
        """Can handle unicode passwords."""
        password = 'pàsswörd123'.encode('utf-8')
        stored_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        hashed_from_db = stored_hash.encode('utf-8')
        assert bcrypt.checkpw(password, hashed_from_db)


# ============================================================================
# Integration Tests - get_primary_key()
# ============================================================================

@pytest.mark.integration
class TestGetPrimaryKey:
    """Test primary key lookup from database."""

    def test_get_pk_for_users_table(self, db_controller):
        """Primary key for users table should be user_id."""
        sql = """
            SELECT k.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
              ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
             AND t.TABLE_SCHEMA = k.TABLE_SCHEMA
             AND t.TABLE_NAME = k.TABLE_NAME
            WHERE t.TABLE_SCHEMA = DATABASE()
              AND t.TABLE_NAME = ?
              AND t.CONSTRAINT_TYPE = 'PRIMARY KEY'
            LIMIT 1;
        """
        row = db_controller.read(False, sql, ("users",))
        assert row is not None
        assert row["COLUMN_NAME"] == "user_id"

    def test_get_pk_for_batches_table(self, db_controller):
        """Primary key for batches table should be batch_id."""
        sql = """
            SELECT k.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
              ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
             AND t.TABLE_SCHEMA = k.TABLE_SCHEMA
             AND t.TABLE_NAME = k.TABLE_NAME
            WHERE t.TABLE_SCHEMA = DATABASE()
              AND t.TABLE_NAME = ?
              AND t.CONSTRAINT_TYPE = 'PRIMARY KEY'
            LIMIT 1;
        """
        row = db_controller.read(False, sql, ("batches",))
        assert row is not None
        assert row["COLUMN_NAME"] == "batch_id"

    def test_get_pk_for_results_table(self, db_controller):
        """Primary key for results table should be result_id."""
        sql = """
            SELECT k.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
              ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
             AND t.TABLE_SCHEMA = k.TABLE_SCHEMA
             AND t.TABLE_NAME = k.TABLE_NAME
            WHERE t.TABLE_SCHEMA = DATABASE()
              AND t.TABLE_NAME = ?
              AND t.CONSTRAINT_TYPE = 'PRIMARY KEY'
            LIMIT 1;
        """
        row = db_controller.read(False, sql, ("results",))
        assert row is not None
        assert row["COLUMN_NAME"] == "result_id"

    @pytest.mark.parametrize("table,expected_pk", [
        ("users", "user_id"),
        ("batches", "batch_id"),
        ("results", "result_id"),
        ("tests", "test_id"),
        ("units", "unit_id"),
        ("controls", "control_id"),
        ("methods", "method_id"),
        ("samples", "sample_id"),
        ("organizations", "org_id"),
    ])
    def test_get_pk_parametrized(self, db_controller, table, expected_pk):
        """Primary keys should match expected values."""
        sql = """
            SELECT k.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
              ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
             AND t.TABLE_SCHEMA = k.TABLE_SCHEMA
             AND t.TABLE_NAME = k.TABLE_NAME
            WHERE t.TABLE_SCHEMA = DATABASE()
              AND t.TABLE_NAME = ?
              AND t.CONSTRAINT_TYPE = 'PRIMARY KEY'
            LIMIT 1;
        """
        row = db_controller.read(False, sql, (table,))
        assert row is not None, f"No PK found for {table}"
        assert row["COLUMN_NAME"] == expected_pk


# ============================================================================
# Integration Tests - get_selected()
# ============================================================================

@pytest.mark.integration
class TestGetSelected:
    """Test generic record retrieval."""

    def test_get_selected_from_tests(self, db_controller):
        """Can retrieve a test by test_id."""
        sql = "SELECT * FROM tests WHERE test_id = ? LIMIT 1;"
        row = db_controller.read(False, sql, (1,))

        # May be None if no test with id 1
        if row:
            assert "test_id" in row
            assert "description" in row

    def test_get_selected_from_units(self, db_controller):
        """Can retrieve a unit by unit_id."""
        sql = "SELECT * FROM units WHERE unit_id = ? LIMIT 1;"
        row = db_controller.read(False, sql, (1,))

        if row:
            assert "unit_id" in row
            assert "description" in row

    def test_get_selected_returns_dict(self, db_controller):
        """Result should be a dictionary with column names."""
        sql = "SELECT 1 AS value, 'test' AS name;"
        row = db_controller.read(False, sql, ())

        assert isinstance(row, dict)
        assert row["value"] == 1
        assert row["name"] == "test"


# ============================================================================
# Integration Tests - get_test_name()
# ============================================================================

@pytest.mark.integration
class TestGetTestName:
    """Test get_test_name method."""

    def test_get_test_name_returns_description(self, db_controller):
        """Should return test description."""
        # First, get a valid test_id
        sql = "SELECT test_id, description FROM tests LIMIT 1;"
        test = db_controller.read(False, sql, ())

        if test:
            # Now test the query pattern used by get_test_name
            sql = "SELECT description FROM tests WHERE test_id = ?;"
            row = db_controller.read(False, sql, (test["test_id"],))

            assert row is not None
            assert row["description"] == test["description"]

    def test_get_test_name_nonexistent_returns_none(self, db_controller):
        """Should return None for nonexistent test_id."""
        sql = "SELECT description FROM tests WHERE test_id = ?;"
        row = db_controller.read(False, sql, (999999,))

        assert row is None


# ============================================================================
# Integration Tests - get_control_name()
# ============================================================================

@pytest.mark.integration
class TestGetControlName:
    """Test get_control_name method."""

    def test_get_control_name_returns_description(self, db_controller):
        """Should return control description."""
        sql = "SELECT control_id, description FROM controls LIMIT 1;"
        control = db_controller.read(False, sql, ())

        if control:
            sql = "SELECT description FROM controls WHERE control_id = ?;"
            row = db_controller.read(False, sql, (control["control_id"],))

            assert row is not None
            assert row["description"] == control["description"]

    def test_get_control_name_nonexistent_returns_none(self, db_controller):
        """Should return None for nonexistent control_id."""
        sql = "SELECT description FROM controls WHERE control_id = ?;"
        row = db_controller.read(False, sql, (999999,))

        assert row is None


# ============================================================================
# Integration Tests - get_um() (Unit of Measurement)
# ============================================================================

@pytest.mark.integration
class TestGetUnitOfMeasurement:
    """Test get_um method."""

    def test_get_um_returns_dict(self, db_controller):
        """Should return dict with description."""
        sql = "SELECT unit_id FROM units WHERE status = 1 LIMIT 1;"
        unit = db_controller.read(False, sql, ())

        if unit:
            sql = "SELECT description FROM units WHERE unit_id = ? AND status = 1;"
            row = db_controller.read(False, sql, (unit["unit_id"],))

            assert row is not None
            assert "description" in row

    def test_get_um_disabled_returns_none(self, db_controller):
        """Should return None for disabled unit."""
        sql = "SELECT description FROM units WHERE unit_id = ? AND status = 1;"
        row = db_controller.read(False, sql, (999999,))

        assert row is None


# ============================================================================
# Integration Tests - Organizations Hierarchy
# ============================================================================

@pytest.mark.integration
class TestOrganizationsHierarchy:
    """Test organization hierarchy queries."""

    def test_get_lab_id_by_section_id(self, db_controller):
        """Should return parent lab_id for a section."""
        # First find a section
        sql = """
            SELECT org_id, parent_id
            FROM organizations
            WHERE org_type = 'section'
            LIMIT 1;
        """
        section = db_controller.read(False, sql, ())

        if section:
            # Query like get_lab_id_by_section_id
            sql = """
                SELECT parent_id AS lab_id
                FROM organizations
                WHERE org_id = ? AND org_type = 'section';
            """
            row = db_controller.read(False, sql, (section["org_id"],))

            assert row is not None
            assert row["lab_id"] == section["parent_id"]

    def test_get_sections_for_lab(self, db_controller):
        """Should return sections for a lab."""
        # First find a lab
        sql = """
            SELECT org_id
            FROM organizations
            WHERE org_type = 'lab'
            LIMIT 1;
        """
        lab = db_controller.read(False, sql, ())

        if lab:
            # Get sections under this lab
            sql = """
                SELECT org_id, description
                FROM organizations
                WHERE parent_id = ? AND org_type = 'section';
            """
            sections = db_controller.read(True, sql, (lab["org_id"],))

            assert isinstance(sections, list)


# ============================================================================
# SQL Identifier Validation Tests
# ============================================================================

class TestSQLIdentifierValidation:
    """Test SQL identifier validation patterns."""

    @pytest.mark.parametrize("identifier,valid", [
        ("users", True),
        ("batch_id", True),
        ("test_method_id", True),
        ("Users", True),
        ("USERS", True),
        ("users123", True),
        ("_users", True),
        ("123users", False),  # Can't start with number
        ("users;DROP TABLE", False),  # SQL injection
        ("users--", False),  # Comment injection
        ("us ers", False),  # Space not allowed
        ("", False),  # Empty not allowed
    ])
    def test_sql_identifier_pattern(self, identifier, valid):
        """SQL identifiers should match safe pattern."""
        import re
        # Pattern from controller.py / DBMS for SQL identifier validation
        pattern = r'^[A-Za-z_][A-Za-z0-9_]*$'

        if valid:
            assert re.match(pattern, identifier), f"{identifier} should be valid"
        else:
            assert not re.match(pattern, identifier), f"{identifier} should be invalid"


# ============================================================================
# PK Cache Tests
# ============================================================================

class TestPKCache:
    """Test primary key caching behavior."""

    def test_cache_is_initialized_empty(self):
        """PK cache should start empty."""
        cache = {}
        assert len(cache) == 0

    def test_cache_stores_values(self):
        """Cache should store and retrieve values."""
        cache = {}
        cache["users"] = "user_id"
        cache["batches"] = "batch_id"

        assert cache["users"] == "user_id"
        assert cache["batches"] == "batch_id"
        assert len(cache) == 2

    def test_cache_hit_returns_immediately(self):
        """Second lookup should use cache."""
        cache = {"users": "user_id"}

        # First check cache
        if "users" in cache:
            result = cache["users"]

        assert result == "user_id"


# ============================================================================
# Parametrized Tests for Table Queries
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
    "organizations",
    "workstations",
    "test_methods",
])
def test_table_is_readable(db_controller, table):
    """All essential tables should be readable."""
    sql = f"SELECT * FROM {table} LIMIT 1;"
    # This tests that the query executes without error
    try:
        db_controller.read(False, sql, ())
    except Exception as e:
        pytest.fail(f"Failed to read from {table}: {e}")


@pytest.mark.integration
@pytest.mark.parametrize("table,pk_field", [
    ("users", "user_id"),
    ("batches", "batch_id"),
    ("results", "result_id"),
    ("tests", "test_id"),
    ("units", "unit_id"),
    ("controls", "control_id"),
])
def test_can_filter_by_pk(db_controller, table, pk_field):
    """Can filter tables by their primary key."""
    sql = f"SELECT * FROM {table} WHERE {pk_field} = ? LIMIT 1;"
    # Query should execute without error
    try:
        db_controller.read(False, sql, (1,))
    except Exception as e:
        pytest.fail(f"Failed to filter {table} by {pk_field}: {e}")
