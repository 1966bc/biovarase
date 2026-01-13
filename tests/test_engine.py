"""
Tests for Engine class - the main orchestrator of Biovarase.

Tests cover:
- Singleton pattern (_EngineMeta metaclass)
- Observer pattern (subscribe, unsubscribe, notify)
- Permission methods (role-based access control)
- Configuration management (language, ddof, zscore, etc.)
- Context management (current_ids, section_id, lab_id)
- User session management
- Error logging
- Utility methods

Author: Claude Code
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, date
import tempfile

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_engine():
    """
    Create a mock Engine instance for testing.

    Mocks database connection to avoid needing real DB.
    """
    with patch('mariadb.connect'):
        # Import after patching to avoid connection attempt
        from engine import Engine

        # Reset singleton for each test
        Engine._EngineMeta__instance = None
        type(Engine)._instance = None

        engine = Engine(
            user="test_user",
            password="test_pass",
            database="test_db"
        )

        yield engine

        # Cleanup singleton
        type(Engine)._instance = None


@pytest.fixture
def engine_with_user(mock_engine):
    """Engine with a logged-in user."""
    mock_engine.log_user = {
        "user_id": 1,
        "nickname": "testuser",
        "role": 5,  # Technician
        "org_id": 2002,
        "lab_id": 2,
    }
    return mock_engine


# ============================================================================
# Test Singleton Pattern
# ============================================================================

class TestSingletonPattern:
    """Test Engine singleton implementation."""

    def test_singleton_returns_same_instance(self, mock_engine):
        """Multiple Engine() calls return the same instance."""
        with patch('mariadb.connect'):
            from engine import Engine
            engine2 = Engine("other", "other", "other")
            assert engine2 is mock_engine

    def test_singleton_str_representation(self, mock_engine):
        """Engine __str__ shows class name and MRO."""
        s = str(mock_engine)
        assert "Engine" in s
        assert "MRO" in s


# ============================================================================
# Test Observer Pattern
# ============================================================================

class TestObserverPattern:
    """Test Engine's event system."""

    def test_subscribe_adds_callback(self, mock_engine):
        """subscribe() adds callback to event list."""
        callback = MagicMock()
        mock_engine.subscribe("batch_changed", callback)

        assert "batch_changed" in mock_engine._subscribers
        assert callback in mock_engine._subscribers["batch_changed"]

    def test_subscribe_same_callback_once(self, mock_engine):
        """Same callback is not added twice."""
        callback = MagicMock()
        mock_engine.subscribe("batch_changed", callback)
        mock_engine.subscribe("batch_changed", callback)

        assert mock_engine._subscribers["batch_changed"].count(callback) == 1

    def test_unsubscribe_removes_callback(self, mock_engine):
        """unsubscribe() removes callback from event list."""
        callback = MagicMock()
        mock_engine.subscribe("batch_changed", callback)
        mock_engine.unsubscribe("batch_changed", callback)

        assert callback not in mock_engine._subscribers.get("batch_changed", [])

    def test_unsubscribe_nonexistent_no_error(self, mock_engine):
        """unsubscribe() doesn't raise for nonexistent callback."""
        callback = MagicMock()
        # Should not raise
        mock_engine.unsubscribe("nonexistent_event", callback)

    def test_notify_calls_all_subscribers(self, mock_engine):
        """notify() calls all registered callbacks."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        mock_engine.subscribe("result_changed", callback1)
        mock_engine.subscribe("result_changed", callback2)

        mock_engine.notify("result_changed", {"id": 123})

        callback1.assert_called_once_with({"id": 123})
        callback2.assert_called_once_with({"id": 123})

    def test_notify_no_subscribers_no_error(self, mock_engine):
        """notify() works even with no subscribers."""
        # Should not raise
        mock_engine.notify("unknown_event", "data")

    def test_notify_exception_in_callback_continues(self, mock_engine):
        """notify() continues even if callback raises exception."""
        bad_callback = MagicMock(side_effect=RuntimeError("Oops"))
        good_callback = MagicMock()

        mock_engine.subscribe("test_event", bad_callback)
        mock_engine.subscribe("test_event", good_callback)

        # Should not raise
        mock_engine.notify("test_event", "data")

        # Good callback should still be called
        good_callback.assert_called_once()


# ============================================================================
# Test Permission Methods
# ============================================================================

class TestPermissionMethods:
    """Test role-based access control methods."""

    @pytest.mark.parametrize("role,expected", [
        (0, True),   # App Admin
        (1, True),   # Country Admin
        (2, True),   # Regional Admin
        (3, True),   # Lab Admin
        (4, True),   # Superuser
        (5, False),  # Technician
        (6, False),  # Viewer
    ])
    def test_can_validate_qc(self, mock_engine, role, expected):
        """can_validate_qc() returns True for roles 0-4."""
        mock_engine.log_user = {"role": role}
        assert mock_engine.can_validate_qc() == expected

    @pytest.mark.parametrize("role,expected", [
        (0, True),   # App Admin - only one who can
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (6, False),
    ])
    def test_can_configure_system(self, mock_engine, role, expected):
        """can_configure_system() returns True only for App Admin (0)."""
        mock_engine.log_user = {"role": role}
        assert mock_engine.can_configure_system() == expected

    @pytest.mark.parametrize("role,expected", [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),   # Technician can modify
        (6, False),  # Viewer cannot
    ])
    def test_can_modify_data(self, mock_engine, role, expected):
        """can_modify_data() returns True for roles 0-5."""
        mock_engine.log_user = {"role": role}
        assert mock_engine.can_modify_data() == expected

    @pytest.mark.parametrize("role,expected", [
        (0, False),
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (6, True),  # Only Viewer is read-only
    ])
    def test_is_read_only(self, mock_engine, role, expected):
        """is_read_only() returns True only for Viewer (6)."""
        mock_engine.log_user = {"role": role}
        assert mock_engine.is_read_only() == expected

    @pytest.mark.parametrize("role,expected", [
        (0, True),
        (1, True),
        (2, True),
        (3, True),   # Lab Admin and above
        (4, False),
        (5, False),
        (6, False),
    ])
    def test_can_manage_local_config(self, mock_engine, role, expected):
        """can_manage_local_config() returns True for roles 0-3."""
        mock_engine.log_user = {"role": role}
        assert mock_engine.can_manage_local_config() == expected

    @pytest.mark.parametrize("role,expected", [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),   # Superuser can delete
        (5, False),  # Technician cannot
        (6, False),
    ])
    def test_can_delete_results(self, mock_engine, role, expected):
        """can_delete_results() returns True for roles 0-4."""
        mock_engine.log_user = {"role": role}
        assert mock_engine.can_delete_results() == expected


# ============================================================================
# Test Role Check Methods
# ============================================================================

class TestRoleCheckMethods:
    """Test specific role check methods."""

    def test_is_admin_true_for_role_0(self, mock_engine):
        """is_admin() returns True for role 0."""
        mock_engine.log_user = {"role": 0}
        assert mock_engine.is_admin() is True

    def test_is_admin_false_for_other_roles(self, mock_engine):
        """is_admin() returns False for roles other than 0."""
        for role in [1, 2, 3, 4, 5, 6]:
            mock_engine.log_user = {"role": role}
            assert mock_engine.is_admin() is False

    def test_is_superuser_true_for_role_4(self, mock_engine):
        """is_superuser() returns True for role 4."""
        mock_engine.log_user = {"role": 4}
        assert mock_engine.is_superuser() is True

    def test_is_user_true_for_role_5(self, mock_engine):
        """is_user() returns True for role 5 (Technician)."""
        mock_engine.log_user = {"role": 5}
        assert mock_engine.is_user() is True

    def test_is_lab_admin_true_for_role_3(self, mock_engine):
        """is_lab_admin() returns True for role 3."""
        mock_engine.log_user = {"role": 3}
        assert mock_engine.is_lab_admin() is True

    def test_get_user_role_returns_role(self, mock_engine):
        """get_user_role() returns the user's role."""
        mock_engine.log_user = {"role": 5}
        assert mock_engine.get_user_role() == 5

    def test_get_user_role_missing_returns_99(self, mock_engine):
        """get_user_role() returns 99 if role is not set."""
        mock_engine.log_user = {}
        assert mock_engine.get_user_role() == 99

    def test_get_user_org_id_returns_org_id(self, mock_engine):
        """get_user_org_id() returns the user's org_id."""
        mock_engine.log_user = {"org_id": 2002}
        assert mock_engine.get_user_org_id() == 2002

    def test_get_user_org_id_none_if_not_set(self, mock_engine):
        """get_user_org_id() returns None if org_id not set."""
        mock_engine.log_user = {}
        assert mock_engine.get_user_org_id() is None


# ============================================================================
# Test Data Scope
# ============================================================================

class TestDataScope:
    """Test get_data_scope() method."""

    def test_admin_gets_global_scope(self, mock_engine):
        """App Admin (role 0) gets global scope."""
        mock_engine.log_user = {"role": 0}
        scope, filter_id = mock_engine.get_data_scope()
        assert scope == "global"
        assert filter_id is None

    def test_other_roles_get_lab_scope(self, mock_engine):
        """Non-admin users get lab scope."""
        mock_engine.log_user = {"role": 5}
        mock_engine.current_ids = {"lab_id": 2002}

        scope, filter_id = mock_engine.get_data_scope()

        assert scope == "lab"
        assert filter_id == 2002


# ============================================================================
# Test Context Management
# ============================================================================

class TestContextManagement:
    """Test current_ids and context methods."""

    def test_get_section_id_from_context(self, mock_engine):
        """get_section_id() returns value from current_ids."""
        mock_engine.current_ids = {"section_id": 6}
        assert mock_engine.get_section_id() == 6

    def test_get_section_id_none_if_not_set(self, mock_engine):
        """get_section_id() returns None if not in current_ids."""
        mock_engine.current_ids = {}
        assert mock_engine.get_section_id() is None

    def test_get_lab_id_from_context(self, mock_engine):
        """get_lab_id() returns value from current_ids."""
        mock_engine.current_ids = {"lab_id": 2002}
        assert mock_engine.get_lab_id() == 2002

    def test_set_section_id_updates_context(self, mock_engine):
        """set_section_id() updates current_ids."""
        mock_engine.current_ids = {}
        mock_engine.set_section_id(6)
        assert mock_engine.current_ids["section_id"] == 6

    def test_set_section_id_converts_to_int(self, mock_engine):
        """set_section_id() converts value to int."""
        mock_engine.current_ids = {}
        mock_engine.set_section_id("6")
        assert mock_engine.current_ids["section_id"] == 6

    def test_set_section_id_none_does_nothing(self, mock_engine):
        """set_section_id(None) doesn't update context."""
        mock_engine.current_ids = {}
        mock_engine.set_section_id(None)
        assert "section_id" not in mock_engine.current_ids


# ============================================================================
# Test Configuration Methods
# ============================================================================

class TestConfigurationMethods:
    """Test configuration file read/write methods."""

    def test_get_file_returns_full_path(self, mock_engine):
        """get_file() returns full path to file."""
        path = mock_engine.get_file("test.txt")
        assert path.endswith("test.txt")
        assert os.path.isabs(path)

    def test_get_python_version(self, mock_engine):
        """get_python_version() returns version string."""
        version = mock_engine.get_python_version()
        assert "Python version:" in version
        assert "." in version

    def test_get_date_returns_iso_format(self, mock_engine):
        """get_date() returns YYYY-MM-DD format."""
        date_str = mock_engine.get_date()
        assert len(date_str) == 10
        assert date_str.count("-") == 2
        # Should be parseable as date
        datetime.strptime(date_str, "%Y-%m-%d")

    def test_get_today_returns_european_format(self, mock_engine):
        """get_today() returns DD-MM-YYYY format."""
        today_str = mock_engine.get_today()
        assert len(today_str) == 10
        assert today_str.count("-") == 2
        # Should be parseable
        datetime.strptime(today_str, "%d-%m-%Y")

    def test_get_time_returns_time(self, mock_engine):
        """get_time() returns current time."""
        t = mock_engine.get_time()
        assert hasattr(t, 'hour')
        assert hasattr(t, 'minute')


class TestLanguageConfiguration:
    """Test language configuration methods."""

    def test_get_language_reads_from_file(self, mock_engine):
        """get_language() reads language from file."""
        with patch("builtins.open", mock_open(read_data="it\n")):
            lang = mock_engine.get_language()
        assert lang == "it"

    def test_get_language_defaults_to_en(self, mock_engine):
        """get_language() returns 'en' if file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            lang = mock_engine.get_language()
        assert lang == "en"

    def test_get_language_validates_value(self, mock_engine):
        """get_language() returns 'en' for invalid values."""
        with patch("builtins.open", mock_open(read_data="fr\n")):
            lang = mock_engine.get_language()
        assert lang == "en"

    def test_set_language_writes_to_file(self, mock_engine):
        """set_language() writes language to file."""
        m = mock_open()
        with patch("builtins.open", m):
            result = mock_engine.set_language("it")
        assert result is True
        m().write.assert_called_once_with("it")

    def test_set_language_rejects_invalid(self, mock_engine):
        """set_language() rejects invalid language codes."""
        result = mock_engine.set_language("fr")
        assert result is False


class TestDateFormatConfiguration:
    """Test date format configuration."""

    def test_get_date_format_european(self, mock_engine):
        """get_date_format() reads European format."""
        with patch("builtins.open", mock_open(read_data="dd-mm-yyyy\n")):
            fmt = mock_engine.get_date_format()
        assert fmt == "dd-mm-yyyy"

    def test_get_date_format_american(self, mock_engine):
        """get_date_format() reads American format."""
        with patch("builtins.open", mock_open(read_data="mm-dd-yyyy\n")):
            fmt = mock_engine.get_date_format()
        assert fmt == "mm-dd-yyyy"

    def test_get_date_format_defaults_to_european(self, mock_engine):
        """get_date_format() defaults to European on error."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            fmt = mock_engine.get_date_format()
        assert fmt == "dd-mm-yyyy"

    def test_format_date_european(self, mock_engine):
        """format_date() formats as DD-MM-YYYY."""
        with patch("builtins.open", mock_open(read_data="dd-mm-yyyy\n")):
            dt = datetime(2025, 1, 29)
            result = mock_engine.format_date(dt)
        assert result == "29-01-2025"

    def test_format_date_american(self, mock_engine):
        """format_date() formats as MM-DD-YYYY."""
        with patch("builtins.open", mock_open(read_data="mm-dd-yyyy\n")):
            dt = datetime(2025, 1, 29)
            result = mock_engine.format_date(dt)
        assert result == "01-29-2025"

    def test_format_date_none_returns_empty(self, mock_engine):
        """format_date(None) returns empty string."""
        result = mock_engine.format_date(None)
        assert result == ""

    def test_format_datetime_includes_time(self, mock_engine):
        """format_datetime() includes time."""
        with patch("builtins.open", mock_open(read_data="dd-mm-yyyy\n")):
            dt = datetime(2025, 1, 29, 14, 35, 22)
            result = mock_engine.format_datetime(dt)
        assert result == "29-01-2025 14:35:22"


class TestRememberBatchConfiguration:
    """Test remember_batch configuration."""

    def test_get_remember_batch_true(self, mock_engine):
        """get_remember_batch() returns True for '1'."""
        with patch("builtins.open", mock_open(read_data="1\n")):
            result = mock_engine.get_remember_batch()
        assert result is True

    def test_get_remember_batch_false(self, mock_engine):
        """get_remember_batch() returns False for '0'."""
        with patch("builtins.open", mock_open(read_data="0\n")):
            result = mock_engine.get_remember_batch()
        assert result is False

    def test_get_remember_batch_true_variants(self, mock_engine):
        """get_remember_batch() accepts 'true', 'yes', 'on'."""
        for val in ["true", "TRUE", "yes", "YES", "on", "ON"]:
            with patch("builtins.open", mock_open(read_data=f"{val}\n")):
                result = mock_engine.get_remember_batch()
            assert result is True, f"Failed for '{val}'"

    def test_get_remember_batch_file_not_found(self, mock_engine):
        """get_remember_batch() returns False if file missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = mock_engine.get_remember_batch()
        assert result is False

    def test_set_remember_batch_true(self, mock_engine):
        """set_remember_batch(True) writes '1'."""
        m = mock_open()
        with patch("builtins.open", m):
            result = mock_engine.set_remember_batch(True)
        assert result is True
        m().write.assert_called_once_with("1")

    def test_set_remember_batch_false(self, mock_engine):
        """set_remember_batch(False) writes '0'."""
        m = mock_open()
        with patch("builtins.open", m):
            result = mock_engine.set_remember_batch(False)
        assert result is True
        m().write.assert_called_once_with("0")


class TestAutologinConfiguration:
    """Test autologin configuration."""

    def test_get_autologin_flag_true(self, mock_engine):
        """get_autologin_flag() returns True for '1'."""
        with patch.object(mock_engine, 'get_file', return_value="/fake/autologin"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="1")):
                    result = mock_engine.get_autologin_flag()
        assert result is True

    def test_get_autologin_flag_false(self, mock_engine):
        """get_autologin_flag() returns False for '0'."""
        with patch.object(mock_engine, 'get_file', return_value="/fake/autologin"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="0")):
                    result = mock_engine.get_autologin_flag()
        assert result is False

    def test_get_autologin_flag_file_missing(self, mock_engine):
        """get_autologin_flag() returns False if file missing."""
        with patch.object(mock_engine, 'get_file', return_value="/fake/autologin"):
            with patch("os.path.exists", return_value=False):
                result = mock_engine.get_autologin_flag()
        assert result is False


# ============================================================================
# Test User Session
# ============================================================================

class TestUserSession:
    """Test user session management."""

    def test_set_log_user_stores_user_data(self, mock_engine):
        """set_log_user() stores user dictionary."""
        user_data = {
            "user_id": 1,
            "last_name": "Test",
            "first_name": "User",
            "nickname": "testuser",
            "pswrd": "hashed",
            "role": 5,
            "org_id": 2002,
            "lab_id": 2,
            "elapsing_time": None,
            "enable_time": None,
            "status": 1,
        }

        mock_engine.set_log_user(user_data)

        # Check string keys
        assert mock_engine.log_user["user_id"] == 1
        assert mock_engine.log_user["nickname"] == "testuser"
        assert mock_engine.log_user["role"] == 5

        # Check numeric keys for backward compatibility
        assert mock_engine.log_user[0] == 1  # user_id
        assert mock_engine.log_user[3] == "testuser"  # nickname
        assert mock_engine.log_user[5] == 5  # role

    def test_get_log_id_returns_user_id(self, engine_with_user):
        """get_log_id() returns user_id."""
        assert engine_with_user.get_log_id() == 1

    def test_get_log_ip_returns_ip(self, mock_engine):
        """get_log_ip() returns IP address."""
        ip = mock_engine.get_log_ip()
        assert ip is not None
        # Either a valid IP or error message
        assert "." in ip or "No IP" in ip

    def test_get_log_time_returns_datetime(self, mock_engine):
        """get_log_time() returns current datetime."""
        t = mock_engine.get_log_time()
        assert isinstance(t, datetime)


# ============================================================================
# Test Error Logging
# ============================================================================

class TestErrorLogging:
    """Test on_log() error logging method."""

    def test_on_log_writes_to_file(self, mock_engine):
        """on_log() writes error to log file."""
        m = mock_open()
        with patch.object(mock_engine, 'get_file', return_value="/fake/log.txt"):
            with patch("builtins.open", m):
                mock_engine.on_log(
                    "test_function",
                    ValueError("Test error"),
                    ValueError,
                    sys.modules[__name__]
                )

        # Verify file was opened for append
        m.assert_called_once_with("/fake/log.txt", "a", encoding="utf-8", errors="backslashreplace")

    def test_on_log_includes_timestamp(self, mock_engine):
        """on_log() includes timestamp in log."""
        written_content = []
        m = mock_open()
        m.return_value.write = lambda x: written_content.append(x)

        with patch.object(mock_engine, 'get_file', return_value="/fake/log.txt"):
            with patch("builtins.open", m):
                mock_engine.on_log(
                    "test_function",
                    ValueError("Test error"),
                    ValueError,
                    sys.modules[__name__]
                )

        log_text = "".join(written_content)
        # Should contain date-like pattern
        assert "202" in log_text  # Year

    def test_on_log_includes_function_name(self, mock_engine):
        """on_log() includes function name in log."""
        written_content = []
        m = mock_open()
        m.return_value.write = lambda x: written_content.append(x)

        with patch.object(mock_engine, 'get_file', return_value="/fake/log.txt"):
            with patch("builtins.open", m):
                mock_engine.on_log(
                    "my_function",
                    ValueError("Test error"),
                    ValueError,
                    sys.modules[__name__]
                )

        log_text = "".join(written_content)
        assert "my_function" in log_text

    def test_on_log_never_raises(self, mock_engine):
        """on_log() never raises exceptions."""
        with patch.object(mock_engine, 'get_file', side_effect=RuntimeError("Oops")):
            # Should not raise
            mock_engine.on_log(
                "test",
                ValueError("err"),
                ValueError,
                sys.modules[__name__]
            )


# ============================================================================
# Test Utility Methods
# ============================================================================

class TestUtilityMethods:
    """Test various utility methods."""

    def test_get_observations_reads_file(self, mock_engine):
        """get_observations() reads from file."""
        with patch("builtins.open", mock_open(read_data="10\n")):
            result = mock_engine.get_observations()
        assert result == "10"

    def test_get_observations_file_not_found(self, mock_engine):
        """get_observations() returns None if file missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch.object(mock_engine, 'on_log'):
                result = mock_engine.get_observations()
        assert result is None

    def test_get_correlation_coefficient_returns_float(self, mock_engine):
        """get_correlation_coefficient() returns float."""
        with patch("builtins.open", mock_open(read_data="0.95\n")):
            result = mock_engine.get_correlation_coefficient()
        assert result == 0.95
        assert isinstance(result, float)

    def test_get_icon_returns_embedded_data(self, mock_engine):
        """get_icon() returns embedded base64 PNG data."""
        result = mock_engine.get_icon()
        assert result is not None
        assert result.startswith("iVBORw0KGgo")  # PNG base64 header
        assert len(result) > 100  # Reasonable icon size

    def test_get_expiration_date_positive(self, mock_engine):
        """get_expiration_date() returns positive for future dates."""
        from datetime import timedelta
        future = (date.today() + timedelta(days=30)).strftime("%d-%m-%Y")
        result = mock_engine.get_expiration_date(future)
        assert result == 30

    def test_get_expiration_date_negative(self, mock_engine):
        """get_expiration_date() returns negative for past dates."""
        from datetime import timedelta
        past = (date.today() - timedelta(days=10)).strftime("%d-%m-%Y")
        result = mock_engine.get_expiration_date(past)
        assert result == -10

    def test_get_expiration_date_invalid(self, mock_engine):
        """get_expiration_date() returns None for invalid dates."""
        with patch.object(mock_engine, 'on_log'):
            result = mock_engine.get_expiration_date("invalid")
        assert result is None

    def test_get_dimensions_returns_dict(self, mock_engine):
        """get_dimensions() returns dictionary from file."""
        content = "width,800\nheight,600\n"
        with patch("builtins.open", mock_open(read_data=content)):
            result = mock_engine.get_dimensions()
        assert result == {"width": "800", "height": "600"}

    def test_get_dimensions_file_not_found(self, mock_engine):
        """get_dimensions() returns empty dict if file missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch.object(mock_engine, 'on_log'):
                result = mock_engine.get_dimensions()
        assert result == {}


# ============================================================================
# Test Cursor Control
# ============================================================================

class TestCursorControl:
    """Test busy/not_busy cursor control."""

    def test_busy_sets_watch_cursor(self, mock_engine):
        """busy() sets cursor to 'watch'."""
        caller = MagicMock()
        mock_engine.busy(caller)
        caller.config.assert_called_once_with(cursor="watch")

    def test_not_busy_resets_cursor(self, mock_engine):
        """not_busy() resets cursor to default."""
        caller = MagicMock()
        mock_engine.not_busy(caller)
        caller.config.assert_called_once_with(cursor="")


# ============================================================================
# Test Init Current IDs
# ============================================================================

class TestInitCurrentIds:
    """Test init_current_ids_from_user() method."""

    def test_init_from_user_org_id(self, mock_engine):
        """init_current_ids_from_user() uses user's org_id."""
        mock_engine.log_user = {"org_id": 2002}
        mock_engine._get_org_type = MagicMock(return_value="lab")
        mock_engine.get_idd_by_lab_id = MagicMock(return_value={
            "site_id": 2001,
            "lab_id": 2002,
        })
        mock_engine.get_first_section_by_lab = MagicMock(return_value={"section_id": 6})

        result = mock_engine.init_current_ids_from_user()

        assert result is True
        assert mock_engine.current_ids["lab_id"] == 2002
        assert mock_engine.current_ids["site_id"] == 2001
        assert mock_engine.current_ids["section_id"] == 6

    def test_init_with_override_lab_id(self, mock_engine):
        """init_current_ids_from_user(lab_id) uses provided lab_id."""
        mock_engine.log_user = {"org_id": 2002}
        mock_engine._get_org_type = MagicMock(return_value="lab")
        mock_engine.get_idd_by_lab_id = MagicMock(return_value={
            "site_id": 3001,
            "lab_id": 3002,
        })
        mock_engine.get_first_section_by_lab = MagicMock(return_value=None)

        result = mock_engine.init_current_ids_from_user(lab_id=3002)

        mock_engine.get_idd_by_lab_id.assert_called_with(3002)
        assert result is True

    def test_init_no_org_id_returns_false(self, mock_engine):
        """init_current_ids_from_user() returns False if no org_id."""
        mock_engine.log_user = {}

        result = mock_engine.init_current_ids_from_user()

        assert result is False
        assert mock_engine.current_ids == {}

    def test_init_db_error_returns_false(self, mock_engine):
        """init_current_ids_from_user() returns False on DB error."""
        mock_engine.log_user = {"org_id": 2002}
        mock_engine.get_idd_by_lab_id = MagicMock(return_value=None)

        result = mock_engine.init_current_ids_from_user()

        assert result is False


# ============================================================================
# Test Standard Messages
# ============================================================================

class TestStandardMessages:
    """Test standard message attributes."""

    def test_no_selected_message(self, mock_engine):
        """no_selected attribute is set."""
        assert "No record selected" in mock_engine.no_selected

    def test_mandatory_message(self, mock_engine):
        """mandatory attribute has placeholder."""
        assert "%s" in mock_engine.mandatory

    def test_delete_message(self, mock_engine):
        """delete attribute is set."""
        assert "Delete" in mock_engine.delete

    def test_abort_message(self, mock_engine):
        """abort attribute is set."""
        assert "aborted" in mock_engine.abort


# ============================================================================
# Test App Title
# ============================================================================

class TestAppTitle:
    """Test application title."""

    def test_app_title_is_biovarase(self, mock_engine):
        """App title is 'Biovarase'."""
        assert mock_engine.app_title == "Biovarase"
        assert mock_engine.title == "Biovarase"


# ============================================================================
# Test Role Constants Import
# ============================================================================

class TestRoleConstants:
    """Test role constants are accessible."""

    def test_role_constants_exist(self):
        """Role constants are defined in engine module."""
        from engine import (
            ROLE_APP_ADMIN,
            ROLE_COUNTRY_ADMIN,
            ROLE_REGIONAL_ADMIN,
            ROLE_LAB_ADMIN,
            ROLE_SUPERUSER,
            ROLE_TECHNICIAN,
            ROLE_VIEWER,
        )

        assert ROLE_APP_ADMIN == 0
        assert ROLE_COUNTRY_ADMIN == 1
        assert ROLE_REGIONAL_ADMIN == 2
        assert ROLE_LAB_ADMIN == 3
        assert ROLE_SUPERUSER == 4
        assert ROLE_TECHNICIAN == 5
        assert ROLE_VIEWER == 6

    def test_legacy_role_aliases(self):
        """Legacy role aliases exist for backward compatibility."""
        from engine import ROLE_ADMIN, ROLE_AUTOLOGIN

        assert ROLE_ADMIN == 0
        assert ROLE_AUTOLOGIN == 6
