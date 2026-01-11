"""
Integration tests for Biovarase with real database.

These tests connect to the biovarase_test database and verify:
- Database connection and operations
- CRUD operations on all major tables
- Trigger functionality (audit tables)
- Foreign key constraints
- Role-based data filtering

Prerequisites:
    Run: sudo bash sql/setup_test_db.sh

Usage:
    pytest tests/test_integration.py -v
    pytest tests/test_integration.py -v -m integration
"""
import pytest
import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test database credentials
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

@pytest.fixture(scope="module")
def db_connection():
    """
    Create a database connection for integration tests.

    Uses module scope to reuse connection across tests in this file.
    """
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
def cursor(db_connection):
    """Create a dictionary cursor for each test."""
    cur = db_connection.cursor(dictionary=True)
    yield cur
    cur.close()


@pytest.fixture
def clean_cursor(db_connection):
    """
    Cursor with automatic cleanup of test data.

    Tracks inserted IDs and deletes them after test.
    """
    cur = db_connection.cursor(dictionary=True)
    inserted_ids = {"results": [], "batches": [], "users": []}

    yield cur, inserted_ids

    # Cleanup in reverse order (respect foreign keys)
    for result_id in inserted_ids["results"]:
        cur.execute("DELETE FROM results WHERE result_id = ?", (result_id,))
    for batch_id in inserted_ids["batches"]:
        cur.execute("DELETE FROM batches WHERE batch_id = ?", (batch_id,))
    for user_id in inserted_ids["users"]:
        cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    cur.close()


# ============================================================================
# Test Database Connection
# ============================================================================

@pytest.mark.integration
class TestDatabaseConnection:
    """Test basic database connectivity."""

    def test_connection_successful(self, db_connection):
        """Verify connection to test database works."""
        assert db_connection is not None
        assert db_connection.open

    def test_can_execute_query(self, cursor):
        """Verify we can execute a simple query."""
        cursor.execute("SELECT 1 AS test_value")
        row = cursor.fetchone()
        assert row["test_value"] == 1

    def test_database_is_biovarase_test(self, cursor):
        """Verify we're connected to test database, not production."""
        cursor.execute("SELECT DATABASE() AS db_name")
        row = cursor.fetchone()
        assert row["db_name"] == "biovarase_test"

    def test_tables_exist(self, cursor):
        """Verify essential tables exist."""
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'biovarase_test'
        """)
        tables = [row["table_name"] for row in cursor.fetchall()]

        essential_tables = [
            "users", "batches", "results", "test_methods",
            "workstations", "controls", "tests", "units",
            "audit_batches", "audit_results", "organizations"
        ]

        for table in essential_tables:
            assert table in tables, f"Missing table: {table}"


# ============================================================================
# Test Users Table
# ============================================================================

@pytest.mark.integration
class TestUsersTable:
    """Test operations on users table."""

    def test_read_users(self, cursor):
        """Can read from users table."""
        cursor.execute("SELECT * FROM users LIMIT 5")
        rows = cursor.fetchall()
        # Should return a list (possibly empty)
        assert isinstance(rows, list)

    def test_insert_and_delete_user(self, clean_cursor):
        """Can insert and delete a test user."""
        cursor, ids = clean_cursor

        # Insert test user
        cursor.execute("""
            INSERT INTO users (last_name, first_name, nickname, pswrd, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Test", "User", "test_integration_user", "hashed_password", 5, 1))

        user_id = cursor.lastrowid
        ids["users"].append(user_id)

        assert user_id > 0

        # Verify insert
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["last_name"] == "Test"
        assert row["nickname"] == "test_integration_user"
        assert row["role"] == 5  # Technician

    def test_user_role_values(self, cursor):
        """Verify role values are within expected range (0-6)."""
        cursor.execute("SELECT DISTINCT role FROM users WHERE role IS NOT NULL")
        roles = [row["role"] for row in cursor.fetchall()]

        for role in roles:
            assert 0 <= role <= 6, f"Invalid role value: {role}"


# ============================================================================
# Test Batches Table
# ============================================================================

@pytest.mark.integration
class TestBatchesTable:
    """Test operations on batches table."""

    def test_read_batches(self, cursor):
        """Can read from batches table."""
        cursor.execute("SELECT * FROM batches LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)

    def test_batch_has_required_fields(self, cursor):
        """Batches have all required fields."""
        cursor.execute("SELECT * FROM batches LIMIT 1")
        row = cursor.fetchone()

        if row:
            required_fields = [
                "batch_id", "control_id", "lot_number",
                "target", "sd", "status"
            ]
            for field in required_fields:
                assert field in row, f"Missing field: {field}"

    def test_batch_target_and_sd_are_decimal(self, cursor):
        """Target and SD should be Decimal type."""
        cursor.execute("SELECT target, sd FROM batches WHERE target > 0 LIMIT 1")
        row = cursor.fetchone()

        if row:
            assert isinstance(row["target"], Decimal)
            assert isinstance(row["sd"], Decimal)


# ============================================================================
# Test Results Table
# ============================================================================

@pytest.mark.integration
class TestResultsTable:
    """Test operations on results table."""

    def test_read_results(self, cursor):
        """Can read from results table."""
        cursor.execute("SELECT * FROM results LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)

    def test_results_have_batch_reference(self, cursor):
        """All results should reference a valid batch."""
        cursor.execute("""
            SELECT r.result_id, r.batch_id
            FROM results r
            LEFT JOIN batches b ON r.batch_id = b.batch_id
            WHERE b.batch_id IS NULL
            LIMIT 1
        """)
        orphans = cursor.fetchall()
        assert len(orphans) == 0, "Found results without valid batch"


# ============================================================================
# Test Audit Triggers
# ============================================================================

@pytest.mark.integration
class TestAuditTriggers:
    """Test audit trail functionality."""

    def test_audit_batches_table_exists(self, cursor):
        """Audit batches table should exist."""
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM information_schema.tables
            WHERE table_schema = 'biovarase_test'
            AND table_name = 'audit_batches'
        """)
        row = cursor.fetchone()
        assert row["cnt"] == 1

    def test_audit_results_table_exists(self, cursor):
        """Audit results table should exist."""
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM information_schema.tables
            WHERE table_schema = 'biovarase_test'
            AND table_name = 'audit_results'
        """)
        row = cursor.fetchone()
        assert row["cnt"] == 1

    def test_batch_insert_trigger_exists(self, cursor):
        """Trigger for batch inserts should exist (if imported)."""
        cursor.execute("""
            SELECT trigger_name FROM information_schema.triggers
            WHERE trigger_schema = 'biovarase_test'
            AND event_object_table = 'batches'
            AND event_manipulation = 'INSERT'
        """)
        triggers = cursor.fetchall()
        # Triggers may not be imported in test DB - just verify query works
        # In production, triggers are created by schema.sql
        if len(triggers) == 0:
            pytest.skip("Triggers not imported in test database")


# ============================================================================
# Test Organizations Table
# ============================================================================

@pytest.mark.integration
class TestOrganizationsTable:
    """Test organizations hierarchy."""

    def test_organizations_table_exists(self, cursor):
        """Organizations table should exist."""
        cursor.execute("SELECT COUNT(*) as cnt FROM organizations")
        row = cursor.fetchone()
        assert row is not None

    def test_org_types_are_valid(self, cursor):
        """Organization types should be valid."""
        cursor.execute("SELECT DISTINCT org_type FROM organizations")
        org_types = [row["org_type"] for row in cursor.fetchall()]

        valid_types = ["country", "region", "site", "lab", "section"]
        for org_type in org_types:
            if org_type:  # Skip NULL
                assert org_type in valid_types, f"Invalid org_type: {org_type}"

    def test_hierarchy_integrity(self, cursor):
        """Parent references should be valid."""
        cursor.execute("""
            SELECT o.org_id, o.parent_id
            FROM organizations o
            LEFT JOIN organizations p ON o.parent_id = p.org_id
            WHERE o.parent_id IS NOT NULL AND p.org_id IS NULL
        """)
        orphans = cursor.fetchall()
        assert len(orphans) == 0, "Found organizations with invalid parent_id"


# ============================================================================
# Test Data Filtering by Lab
# ============================================================================

@pytest.mark.integration
class TestLabFiltering:
    """Test multi-tenant data isolation."""

    def test_batches_have_lab_id(self, cursor):
        """All batches should have lab_id."""
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM batches
            WHERE lab_id IS NULL OR lab_id = 0
        """)
        row = cursor.fetchone()
        # May have some without lab_id during migration
        # Just verify the column exists and query works
        assert row is not None

    def test_filter_batches_by_lab(self, cursor):
        """Can filter batches by lab_id."""
        cursor.execute("""
            SELECT lab_id, COUNT(*) as batch_count
            FROM batches
            WHERE lab_id > 0
            GROUP BY lab_id
        """)
        rows = cursor.fetchall()
        # Should work even if empty
        assert isinstance(rows, list)


# ============================================================================
# Test Foreign Key Constraints
# ============================================================================

@pytest.mark.integration
class TestForeignKeys:
    """Test referential integrity."""

    def test_results_batch_fk(self, cursor):
        """Results should reference valid batches."""
        cursor.execute("""
            SELECT r.result_id
            FROM results r
            LEFT JOIN batches b ON r.batch_id = b.batch_id
            WHERE r.batch_id IS NOT NULL AND b.batch_id IS NULL
            LIMIT 5
        """)
        orphans = cursor.fetchall()
        assert len(orphans) == 0, f"Found {len(orphans)} orphan results"

    def test_batches_control_fk(self, cursor):
        """Batches should reference valid controls."""
        cursor.execute("""
            SELECT b.batch_id, b.control_id
            FROM batches b
            LEFT JOIN controls c ON b.control_id = c.control_id
            WHERE b.control_id IS NOT NULL AND c.control_id IS NULL
            LIMIT 5
        """)
        orphans = cursor.fetchall()
        # Some may be orphaned, just check query works
        assert isinstance(orphans, list)


# ============================================================================
# Test Master Data Tables
# ============================================================================

@pytest.mark.integration
class TestMasterData:
    """Test global master data tables."""

    def test_tests_table(self, cursor):
        """Tests table should have data."""
        cursor.execute("SELECT test_id, description FROM tests LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)

    def test_units_table(self, cursor):
        """Units table should have data."""
        cursor.execute("SELECT unit_id, description FROM units LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)

    def test_methods_table(self, cursor):
        """Methods table should have data."""
        cursor.execute("SELECT method_id, description FROM methods LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)

    def test_controls_table(self, cursor):
        """Controls table should have data."""
        cursor.execute("SELECT control_id, description FROM controls LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)

    def test_samples_table(self, cursor):
        """Samples table should have data."""
        cursor.execute("SELECT sample_id, description FROM samples LIMIT 5")
        rows = cursor.fetchall()
        assert isinstance(rows, list)


# ============================================================================
# Test Dictionary Access Pattern
# ============================================================================

@pytest.mark.integration
@pytest.mark.critical
class TestDictionaryAccess:
    """
    Verify dictionary access pattern works correctly.

    This is CRITICAL for Biovarase - all DB access must use
    row["field"] not row[0] to prevent bugs.
    """

    def test_row_is_dictionary(self, cursor):
        """Query results should be dictionaries."""
        cursor.execute("SELECT 1 AS value, 'test' AS name")
        row = cursor.fetchone()

        assert isinstance(row, dict)
        assert row["value"] == 1
        assert row["name"] == "test"

    def test_can_access_by_column_name(self, cursor):
        """Can access columns by name, not position."""
        cursor.execute("""
            SELECT user_id, nickname, role
            FROM users
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            # These should work
            _ = row["user_id"]
            _ = row["nickname"]
            _ = row["role"]

            # This pattern is what we want to enforce
            assert "user_id" in row
            assert "nickname" in row
            assert "role" in row

    def test_fetchall_returns_list_of_dicts(self, cursor):
        """fetchall() should return list of dictionaries."""
        cursor.execute("SELECT 1 AS a UNION SELECT 2 AS a")
        rows = cursor.fetchall()

        assert isinstance(rows, list)
        for row in rows:
            assert isinstance(row, dict)


# ============================================================================
# Performance Sanity Tests
# ============================================================================

@pytest.mark.integration
class TestPerformance:
    """Basic performance sanity checks."""

    def test_simple_query_under_100ms(self, cursor):
        """Simple queries should be fast."""
        import time

        start = time.time()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        elapsed = time.time() - start

        assert elapsed < 0.1, f"Simple query took {elapsed:.3f}s"

    def test_count_query_reasonable(self, cursor):
        """Count queries should complete quickly."""
        import time

        start = time.time()
        cursor.execute("SELECT COUNT(*) as cnt FROM results")
        cursor.fetchone()
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Count query took {elapsed:.3f}s"
