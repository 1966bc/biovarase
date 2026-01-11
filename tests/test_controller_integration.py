"""
Integration tests for Controller class with real database.

These tests connect to the biovarase_test database and verify:
- SQL query builders
- User authentication
- Data retrieval methods
- Multi-site filtering
- Primary key detection

Prerequisites:
    Run: sudo bash sql/setup_test_db.sh

Usage:
    pytest tests/test_controller_integration.py -v
    pytest tests/test_controller_integration.py -v -m integration

Author: Claude Code
"""
import pytest
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test database credentials (same as test_integration.py)
TEST_DB_CONFIG = {
    "user": "biovarase_test",
    "password": "test_password_123",
    "database": "biovarase_test",
    "host": "localhost",
    "port": 3306,
}


# ============================================================================
# Database Connection Fixture
# ============================================================================

def get_connection():
    """Get a fresh database connection."""
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
        return conn
    except mariadb.Error as e:
        pytest.skip(f"Cannot connect to test database: {e}")
        return None


@pytest.fixture
def db_connection():
    """Create a fresh database connection for each test."""
    conn = get_connection()
    yield conn
    if conn:
        conn.close()


@pytest.fixture
def cursor(db_connection):
    """Create a dictionary cursor for each test."""
    cur = db_connection.cursor(dictionary=True, buffered=True)
    yield cur
    cur.close()


def create_test_controller(conn):
    """Create a Controller-like instance connected to test database."""
    from controller import Controller
    from dbms import DBMS

    class TestController(DBMS, Controller):
        """Minimal Controller for testing."""

        def __init__(self, connection):
            self.conn = connection
            self.current_ids = {"lab_id": None, "section_id": None}
            self._pk_cache = {}

        def read(self, fetch_all, sql, args=None):
            """Execute SELECT query."""
            cur = self.conn.cursor(dictionary=True, buffered=True)
            try:
                cur.execute(sql, args or ())
                if fetch_all:
                    return cur.fetchall()
                else:
                    return cur.fetchone()
            finally:
                cur.close()

        def write(self, sql, args=None):
            """Execute INSERT/UPDATE/DELETE query."""
            cur = self.conn.cursor()
            try:
                cur.execute(sql, args or ())
                return cur.lastrowid
            finally:
                cur.close()

        def on_log(self, *args, **kwargs):
            """Stub for logging."""
            pass

        def get_log_time(self):
            return datetime.now()

        def get_log_id(self):
            return 1

        def get_log_ip(self):
            return "127.0.0.1"

    return TestController(conn)


@pytest.fixture
def controller_instance(db_connection):
    """Create a Controller instance for each test."""
    return create_test_controller(db_connection)


# ============================================================================
# Test get_primary_key
# ============================================================================

@pytest.mark.integration
class TestGetPrimaryKey:
    """Test get_primary_key() method with real database."""

    def test_users_pk(self, controller_instance):
        """Primary key of users table is user_id."""
        pk = controller_instance.get_primary_key("users")
        assert pk == "user_id"

    def test_batches_pk(self, controller_instance):
        """Primary key of batches table is batch_id."""
        pk = controller_instance.get_primary_key("batches")
        assert pk == "batch_id"

    def test_results_pk(self, controller_instance):
        """Primary key of results table is result_id."""
        pk = controller_instance.get_primary_key("results")
        assert pk == "result_id"

    def test_tests_pk(self, controller_instance):
        """Primary key of tests table is test_id."""
        pk = controller_instance.get_primary_key("tests")
        assert pk == "test_id"

    def test_organizations_pk(self, controller_instance):
        """Primary key of organizations table is org_id."""
        pk = controller_instance.get_primary_key("organizations")
        assert pk == "org_id"

    def test_pk_caching(self, controller_instance):
        """Primary key is cached after first query."""
        # First call
        pk1 = controller_instance.get_primary_key("users")
        # Should be cached now
        assert "users" in controller_instance._pk_cache
        # Second call should use cache
        pk2 = controller_instance.get_primary_key("users")
        assert pk1 == pk2

    def test_invalid_table_raises(self, controller_instance):
        """Non-existent table raises RuntimeError."""
        with pytest.raises(RuntimeError):
            controller_instance.get_primary_key("nonexistent_table")


# ============================================================================
# Test get_selected
# ============================================================================

@pytest.mark.integration
class TestGetSelected:
    """Test get_selected() method with real database."""

    def test_get_user_by_id(self, controller_instance, cursor):
        """Can retrieve user by user_id."""
        # First check if any users exist
        cursor.execute("SELECT user_id FROM users LIMIT 1")
        row = cursor.fetchone()

        if not row:
            pytest.skip("No users in test database")

        user_id = row["user_id"]
        result = controller_instance.get_selected("users", "user_id", user_id)

        assert result is not None
        # Check both access patterns
        assert result["user_id"] == user_id
        assert result[0] == user_id  # Numeric index

    def test_get_nonexistent_record(self, controller_instance):
        """Returns None for non-existent record."""
        result = controller_instance.get_selected("users", "user_id", 999999)
        assert result is None

    def test_invalid_table_name_raises(self, controller_instance):
        """Invalid table name raises ValueError."""
        with pytest.raises(ValueError):
            controller_instance.get_selected("users; DROP TABLE", "user_id", 1)

    def test_invalid_field_name_raises(self, controller_instance):
        """Invalid field name raises ValueError."""
        with pytest.raises(ValueError):
            controller_instance.get_selected("users", "id; DROP", 1)

    def test_hybrid_dict_access(self, controller_instance, cursor):
        """Result allows both string and numeric access."""
        cursor.execute("SELECT user_id, nickname FROM users LIMIT 1")
        row = cursor.fetchone()

        if not row:
            pytest.skip("No users in test database")

        user_id = row["user_id"]
        result = controller_instance.get_selected("users", "user_id", user_id)

        # String access
        assert "user_id" in result
        assert "nickname" in result

        # Numeric access
        assert 0 in result
        assert 1 in result


# ============================================================================
# Test get_autologin_user
# ============================================================================

@pytest.mark.integration
class TestGetAutologinUser:
    """Test get_autologin_user() method."""

    def test_returns_none_if_no_viewer(self, controller_instance, cursor):
        """Returns None if no 'viewer' user exists."""
        # Check if viewer exists
        cursor.execute("SELECT user_id FROM users WHERE nickname = 'viewer' AND status = 1")
        row = cursor.fetchone()

        result = controller_instance.get_autologin_user()

        if row:
            assert result is not None
            assert result["nickname"] == "viewer"
        else:
            assert result is None


# ============================================================================
# Test get_test_name
# ============================================================================

@pytest.mark.integration
class TestGetTestName:
    """Test get_test_name() method."""

    def test_returns_description(self, controller_instance, cursor):
        """Returns test description for valid test_id."""
        cursor.execute("SELECT test_id, description FROM tests LIMIT 1")
        row = cursor.fetchone()

        if not row:
            pytest.skip("No tests in test database")

        result = controller_instance.get_test_name(row["test_id"])
        assert result == row["description"]

    def test_returns_none_for_invalid(self, controller_instance):
        """Returns None for non-existent test_id."""
        result = controller_instance.get_test_name(999999)
        assert result is None


# ============================================================================
# Test get_control_name
# ============================================================================

@pytest.mark.integration
class TestGetControlName:
    """Test get_control_name() method."""

    def test_returns_description(self, controller_instance, cursor):
        """Returns control description for valid control_id."""
        cursor.execute("SELECT control_id, description FROM controls LIMIT 1")
        row = cursor.fetchone()

        if not row:
            pytest.skip("No controls in test database")

        result = controller_instance.get_control_name(row["control_id"])
        assert result == row["description"]

    def test_returns_none_for_invalid(self, controller_instance):
        """Returns None for non-existent control_id."""
        result = controller_instance.get_control_name(999999)
        assert result is None


# ============================================================================
# Test get_um
# ============================================================================

@pytest.mark.integration
class TestGetUm:
    """Test get_um() method."""

    def test_returns_unit_dict(self, controller_instance, cursor):
        """Returns unit dict for valid unit_id."""
        cursor.execute("SELECT unit_id, description FROM units WHERE status = 1 LIMIT 1")
        row = cursor.fetchone()

        if not row:
            pytest.skip("No units in test database")

        result = controller_instance.get_um(row["unit_id"])
        assert result is not None
        assert result["description"] == row["description"]

    def test_returns_none_for_invalid(self, controller_instance):
        """Returns None for non-existent unit_id."""
        result = controller_instance.get_um(999999)
        assert result is None


# ============================================================================
# Test get_series
# ============================================================================

@pytest.mark.integration
class TestGetSeries:
    """Test get_series() method."""

    def test_returns_list(self, controller_instance, cursor):
        """Returns list of floats."""
        # Find a batch with results
        cursor.execute("""
            SELECT r.batch_id, r.workstation_id
            FROM results r
            WHERE r.is_delete = 0
            GROUP BY r.batch_id, r.workstation_id
            HAVING COUNT(*) > 1
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            pytest.skip("No results with series in test database")

        result = controller_instance.get_series(
            row["batch_id"],
            row["workstation_id"],
            limit=10
        )

        assert isinstance(result, list)
        # Results can be float or Decimal from database
        from decimal import Decimal
        assert all(isinstance(x, (float, Decimal)) for x in result)

    def test_empty_series_returns_empty_list(self, controller_instance):
        """Returns empty list for non-existent batch."""
        result = controller_instance.get_series(
            batch_id=999999,
            workstation_id=999999,
            limit=10
        )
        assert result == []


# ============================================================================
# Test get_lab_id_by_section_id
# ============================================================================

@pytest.mark.integration
class TestGetLabIdBySectionId:
    """Test get_lab_id_by_section_id() method."""

    def test_returns_lab_id(self, controller_instance, cursor):
        """Returns lab_id for valid section."""
        cursor.execute("""
            SELECT org_id, parent_id
            FROM organizations
            WHERE org_type = 'section' AND status = 1
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            pytest.skip("No sections in test database")

        result = controller_instance.get_lab_id_by_section_id(row["org_id"])
        assert result == row["parent_id"]

    def test_returns_none_for_invalid(self, controller_instance):
        """Returns None for non-existent section."""
        result = controller_instance.get_lab_id_by_section_id(999999)
        assert result is None


# ============================================================================
# Test get_first_section_by_lab
# ============================================================================

@pytest.mark.integration
class TestGetFirstSectionByLab:
    """Test get_first_section_by_lab() method."""

    def test_returns_section_dict(self, controller_instance, cursor):
        """Returns section dict for valid lab."""
        # Find a lab with sections
        cursor.execute("""
            SELECT parent_id AS lab_id
            FROM organizations
            WHERE org_type = 'section' AND status = 1
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            pytest.skip("No labs with sections in test database")

        result = controller_instance.get_first_section_by_lab(row["lab_id"])
        assert result is not None
        assert "section_id" in result

    def test_returns_none_for_invalid(self, controller_instance):
        """Returns None for lab without sections."""
        result = controller_instance.get_first_section_by_lab(999999)
        assert result is None


# ============================================================================
# Test get_idd_by_lab_id
# ============================================================================

@pytest.mark.integration
class TestGetIddByLabId:
    """Test get_idd_by_lab_id() method."""

    def test_returns_hierarchy_dict(self, controller_instance, cursor):
        """Returns hierarchy dict for valid lab_id."""
        cursor.execute("""
            SELECT org_id
            FROM organizations
            WHERE org_type = 'lab' AND status = 1
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            pytest.skip("No labs in test database")

        result = controller_instance.get_idd_by_lab_id(row["org_id"])
        assert result is not None
        assert "lab_id" in result

    def test_returns_none_for_invalid(self, controller_instance):
        """Returns None for non-existent lab."""
        result = controller_instance.get_idd_by_lab_id(999999)
        assert result is None


# ============================================================================
# Test get_mandatory
# ============================================================================

@pytest.mark.integration
class TestGetMandatory:
    """Test get_mandatory() method."""

    def test_returns_list(self, controller_instance, cursor):
        """Returns list of test descriptions."""
        # Set a lab_id context
        cursor.execute("""
            SELECT org_id AS lab_id
            FROM organizations
            WHERE org_type = 'lab' AND status = 1
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            pytest.skip("No labs in test database")

        controller_instance.current_ids["lab_id"] = row["lab_id"]

        result = controller_instance.get_mandatory()
        assert isinstance(result, list)
        # All elements should be strings
        assert all(isinstance(x, str) for x in result)


# ============================================================================
# Test SQL Identifier Validation
# ============================================================================

@pytest.mark.integration
class TestSQLIdentifierValidation:
    """Test that SQL injection is prevented in get_selected."""

    def test_sql_injection_in_table_blocked(self, controller_instance):
        """SQL injection in table name is blocked."""
        with pytest.raises(ValueError):
            controller_instance.get_selected(
                "users; DELETE FROM users; --",
                "user_id",
                1
            )

    def test_sql_injection_in_field_blocked(self, controller_instance):
        """SQL injection in field name is blocked."""
        with pytest.raises(ValueError):
            controller_instance.get_selected(
                "users",
                "user_id = 1 OR 1=1; --",
                1
            )

    def test_valid_table_names_pass(self, controller_instance):
        """Valid table names pass validation."""
        # These should not raise ValueError (only DB errors are ok)
        for table in ["users", "batches", "results", "test_methods"]:
            try:
                # Use actual PK field to avoid DB errors
                pk_field = controller_instance.get_primary_key(table)
                controller_instance.get_selected(table, pk_field, 999999)
            except ValueError:
                # This would mean injection protection failed - not ok
                pytest.fail(f"Valid table name '{table}' was rejected")
            except Exception:
                # Any other exception (like no data) is fine
                pass


# ============================================================================
# Test on_login
# ============================================================================

@pytest.mark.integration
class TestOnLogin:
    """Test on_login() method."""

    def test_valid_credentials(self, controller_instance, cursor):
        """Valid credentials return user dict."""
        # Create a test user with known password
        import bcrypt

        test_password = b"test_password_123"
        hashed = bcrypt.hashpw(test_password, bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO users (last_name, first_name, nickname, pswrd, role, org_id, status)
            VALUES ('Test', 'Login', 'test_login_user', ?, 5, NULL, 1)
        """, (hashed.decode('utf-8'),))

        user_id = cursor.lastrowid

        try:
            result = controller_instance.on_login(("test_login_user", test_password))

            assert result is not None
            assert result["nickname"] == "test_login_user"
        finally:
            # Cleanup
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def test_invalid_password(self, controller_instance, cursor):
        """Invalid password returns None."""
        # Create a test user
        import bcrypt

        test_password = b"correct_password"
        hashed = bcrypt.hashpw(test_password, bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO users (last_name, first_name, nickname, pswrd, role, org_id, status)
            VALUES ('Test', 'Wrong', 'test_wrong_user', ?, 5, NULL, 1)
        """, (hashed.decode('utf-8'),))

        user_id = cursor.lastrowid

        try:
            result = controller_instance.on_login(("test_wrong_user", b"wrong_password"))
            assert result is None
        finally:
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def test_nonexistent_user(self, controller_instance):
        """Non-existent user returns None."""
        result = controller_instance.on_login(("nonexistent_user_xyz", b"any_password"))
        assert result is None


# ============================================================================
# Test get_new_password
# ============================================================================

@pytest.mark.integration
class TestGetNewPassword:
    """Test get_new_password() method."""

    def test_returns_hashed_string(self, controller_instance):
        """Returns bcrypt hashed password as string (for DB storage)."""
        result = controller_instance.get_new_password()

        assert isinstance(result, str)
        # Bcrypt hashes start with $2b$
        assert result.startswith("$2")

    def test_can_verify_password(self, controller_instance):
        """Generated hash can verify original password."""
        import bcrypt

        hashed = controller_instance.get_new_password()

        # Default password is 'pass', hash is str so encode it
        assert bcrypt.checkpw(b"pass", hashed.encode('utf-8'))
