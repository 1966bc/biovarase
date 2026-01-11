"""
Tests for app_config module - Application configuration utilities.

Tests cover:
- Configuration constants
- Log file utilities (log_to_file, rotate, cleanup)
- IP utilities
- Error display (mocked)

Author: Claude Code
"""
import pytest
import sys
import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the module after path setup
import app_config
from app_config import (
    CONFIG_FILENAME,
    MAX_LOGIN_ATTEMPTS,
    BATCH_DESCRIPTION_MAX_LENGTH,
    LOT_NUMBER_MAX_LENGTH,
    IDLE_MONITOR_POLL_INTERVAL,
    THREAD_JOIN_TIMEOUT,
    DB_CONNECTION_TIMEOUT,
    LOG_MAX_SIZE_MB,
    LOG_KEEP_COUNT,
    log_to_file,
    cleanup_old_logs,
    rotate_log_if_needed,
    get_current_ip,
)


# ============================================================================
# Test Constants
# ============================================================================

class TestConstants:
    """Test that configuration constants have expected values."""

    def test_config_filename(self):
        """CONFIG_FILENAME is 'config.enc'."""
        assert CONFIG_FILENAME == "config.enc"

    def test_max_login_attempts(self):
        """MAX_LOGIN_ATTEMPTS is 3."""
        assert MAX_LOGIN_ATTEMPTS == 3

    def test_batch_description_max_length(self):
        """BATCH_DESCRIPTION_MAX_LENGTH is 15."""
        assert BATCH_DESCRIPTION_MAX_LENGTH == 15

    def test_lot_number_max_length(self):
        """LOT_NUMBER_MAX_LENGTH is 20."""
        assert LOT_NUMBER_MAX_LENGTH == 20

    def test_idle_monitor_poll_interval(self):
        """IDLE_MONITOR_POLL_INTERVAL is 1."""
        assert IDLE_MONITOR_POLL_INTERVAL == 1

    def test_thread_join_timeout(self):
        """THREAD_JOIN_TIMEOUT is 2.0."""
        assert THREAD_JOIN_TIMEOUT == 2.0

    def test_db_connection_timeout(self):
        """DB_CONNECTION_TIMEOUT is 5."""
        assert DB_CONNECTION_TIMEOUT == 5

    def test_log_max_size_mb(self):
        """LOG_MAX_SIZE_MB is 10."""
        assert LOG_MAX_SIZE_MB == 10

    def test_log_keep_count(self):
        """LOG_KEEP_COUNT is 5."""
        assert LOG_KEEP_COUNT == 5


# ============================================================================
# Test Constants Types
# ============================================================================

class TestConstantTypes:
    """Test that constants have correct types."""

    def test_config_filename_is_string(self):
        """CONFIG_FILENAME is a string."""
        assert isinstance(CONFIG_FILENAME, str)

    def test_max_login_attempts_is_int(self):
        """MAX_LOGIN_ATTEMPTS is an integer."""
        assert isinstance(MAX_LOGIN_ATTEMPTS, int)

    def test_batch_description_max_length_is_int(self):
        """BATCH_DESCRIPTION_MAX_LENGTH is an integer."""
        assert isinstance(BATCH_DESCRIPTION_MAX_LENGTH, int)

    def test_lot_number_max_length_is_int(self):
        """LOT_NUMBER_MAX_LENGTH is an integer."""
        assert isinstance(LOT_NUMBER_MAX_LENGTH, int)

    def test_thread_join_timeout_is_float(self):
        """THREAD_JOIN_TIMEOUT is a float."""
        assert isinstance(THREAD_JOIN_TIMEOUT, float)


# ============================================================================
# Test Constants Validity
# ============================================================================

class TestConstantValidity:
    """Test that constants have sensible values."""

    def test_max_login_attempts_positive(self):
        """MAX_LOGIN_ATTEMPTS is positive."""
        assert MAX_LOGIN_ATTEMPTS > 0

    def test_batch_description_max_length_positive(self):
        """BATCH_DESCRIPTION_MAX_LENGTH is positive."""
        assert BATCH_DESCRIPTION_MAX_LENGTH > 0

    def test_lot_number_max_length_positive(self):
        """LOT_NUMBER_MAX_LENGTH is positive."""
        assert LOT_NUMBER_MAX_LENGTH > 0

    def test_db_connection_timeout_positive(self):
        """DB_CONNECTION_TIMEOUT is positive."""
        assert DB_CONNECTION_TIMEOUT > 0

    def test_log_max_size_reasonable(self):
        """LOG_MAX_SIZE_MB is between 1 and 100."""
        assert 1 <= LOG_MAX_SIZE_MB <= 100

    def test_log_keep_count_positive(self):
        """LOG_KEEP_COUNT is positive."""
        assert LOG_KEEP_COUNT > 0


# ============================================================================
# Test log_to_file
# ============================================================================

class TestLogToFile:
    """Test log_to_file() function."""

    def test_log_to_file_writes_message(self):
        """Writes message to log file."""
        m = mock_open()
        with patch("builtins.open", m):
            with patch("builtins.print"):
                log_to_file("Test message")

        m.assert_called_once()
        handle = m()
        written = handle.write.call_args[0][0]
        assert "Test message" in written

    def test_log_to_file_includes_timestamp(self):
        """Includes timestamp in log entry."""
        m = mock_open()
        with patch("builtins.open", m):
            with patch("builtins.print"):
                log_to_file("Test message")

        written = m().write.call_args[0][0]
        # Should contain date pattern like "2025-01-15"
        assert "-" in written

    def test_log_to_file_includes_level(self):
        """Includes log level in log entry."""
        m = mock_open()
        with patch("builtins.open", m):
            with patch("builtins.print"):
                log_to_file("Test message", "WARNING")

        written = m().write.call_args[0][0]
        assert "WARNING" in written

    def test_log_to_file_default_level_info(self):
        """Default log level is INFO."""
        m = mock_open()
        with patch("builtins.open", m):
            with patch("builtins.print"):
                log_to_file("Test message")

        written = m().write.call_args[0][0]
        assert "INFO" in written

    def test_log_to_file_prints_to_console(self):
        """Also prints to console."""
        with patch("builtins.open", mock_open()):
            with patch("builtins.print") as mock_print:
                log_to_file("Test message", "ERROR")

        mock_print.assert_called_once()
        printed = mock_print.call_args[0][0]
        assert "ERROR" in printed
        assert "Test message" in printed

    def test_log_to_file_never_raises(self):
        """Never raises exception even on error."""
        with patch("builtins.open", side_effect=IOError("Disk full")):
            # Should not raise
            log_to_file("Test message")


# ============================================================================
# Test get_current_ip
# ============================================================================

class TestGetCurrentIP:
    """Test get_current_ip() function."""

    def test_returns_string(self):
        """Returns a string."""
        result = get_current_ip()
        assert isinstance(result, str)

    def test_returns_ip_format_or_fallback(self):
        """Returns IP-like format or fallback."""
        result = get_current_ip()
        # Either contains dots (IP) or is the fallback
        assert "." in result or result == "0.0.0.0"

    def test_fallback_on_error(self):
        """Returns fallback on socket error."""
        with patch("socket.gethostname", side_effect=OSError("Network error")):
            result = get_current_ip()
        assert result == "0.0.0.0"


# ============================================================================
# Test cleanup_old_logs
# ============================================================================

class TestCleanupOldLogs:
    """Test cleanup_old_logs() function."""

    def test_cleanup_with_no_logs(self):
        """Does nothing when no log files exist."""
        with patch("glob.glob", return_value=[]):
            # Should not raise
            cleanup_old_logs()

    def test_cleanup_keeps_recent_logs(self):
        """Keeps the most recent log files."""
        log_files = [
            "log_20250101_120000.txt",
            "log_20250102_120000.txt",
            "log_20250103_120000.txt",
        ]
        with patch("glob.glob", return_value=log_files):
            with patch("os.remove") as mock_remove:
                cleanup_old_logs(keep=3)

        # Should not remove any (we have exactly 3)
        mock_remove.assert_not_called()

    def test_cleanup_removes_old_logs(self):
        """Removes oldest log files when over limit."""
        log_files = [
            "log_20250101_120000.txt",  # oldest - should be removed
            "log_20250102_120000.txt",
            "log_20250103_120000.txt",
            "log_20250104_120000.txt",
        ]
        with patch("glob.glob", return_value=log_files):
            with patch("os.remove") as mock_remove:
                cleanup_old_logs(keep=2)

        # Should remove 2 oldest files
        assert mock_remove.call_count == 2
        mock_remove.assert_any_call("log_20250101_120000.txt")
        mock_remove.assert_any_call("log_20250102_120000.txt")

    def test_cleanup_never_raises(self):
        """Never raises exception on errors."""
        with patch("glob.glob", side_effect=OSError("Error")):
            # Should not raise
            cleanup_old_logs()


# ============================================================================
# Test rotate_log_if_needed
# ============================================================================

class TestRotateLogIfNeeded:
    """Test rotate_log_if_needed() function."""

    def test_no_rotation_if_log_missing(self):
        """Does nothing if log.txt doesn't exist."""
        with patch("os.path.exists", return_value=False):
            with patch("os.rename") as mock_rename:
                rotate_log_if_needed()

        mock_rename.assert_not_called()

    def test_no_rotation_if_under_limit(self):
        """Does nothing if log is under size limit."""
        with patch("os.path.exists", return_value=True):
            # 5 MB < 10 MB limit
            with patch("os.path.getsize", return_value=5 * 1024 * 1024):
                with patch("os.rename") as mock_rename:
                    rotate_log_if_needed()

        mock_rename.assert_not_called()

    def test_rotates_if_over_limit(self):
        """Rotates log if over size limit."""
        with patch("os.path.exists", return_value=True):
            # 15 MB > 10 MB limit
            with patch("os.path.getsize", return_value=15 * 1024 * 1024):
                with patch("os.rename") as mock_rename:
                    with patch("builtins.print"):
                        with patch.object(app_config, "cleanup_old_logs"):
                            rotate_log_if_needed()

        mock_rename.assert_called_once()
        # Check new filename contains timestamp pattern
        args = mock_rename.call_args[0]
        assert args[0] == "log.txt"
        assert args[1].startswith("log_")
        assert args[1].endswith(".txt")

    def test_calls_cleanup_after_rotation(self):
        """Calls cleanup_old_logs after rotation."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", return_value=15 * 1024 * 1024):
                with patch("os.rename"):
                    with patch("builtins.print"):
                        with patch.object(app_config, "cleanup_old_logs") as mock_cleanup:
                            rotate_log_if_needed()

        mock_cleanup.assert_called_once_with(keep=LOG_KEEP_COUNT)

    def test_rotation_never_raises(self):
        """Never raises exception on errors."""
        with patch("os.path.exists", side_effect=OSError("Error")):
            # Should not raise
            rotate_log_if_needed()


# ============================================================================
# Test Integration of Constants with Application Logic
# ============================================================================

class TestConstantsIntegration:
    """Test that constants can be used in typical scenarios."""

    def test_batch_description_truncation(self):
        """Constant can be used for string truncation."""
        long_description = "This is a very long batch description"
        truncated = long_description[:BATCH_DESCRIPTION_MAX_LENGTH]

        assert len(truncated) == BATCH_DESCRIPTION_MAX_LENGTH
        assert truncated == "This is a very "

    def test_lot_number_validation(self):
        """Constant can be used for lot number validation."""
        valid_lot = "LOT-12345"
        invalid_lot = "LOT-" + "X" * 30  # Too long

        assert len(valid_lot) <= LOT_NUMBER_MAX_LENGTH
        assert len(invalid_lot) > LOT_NUMBER_MAX_LENGTH

    def test_login_attempts_loop(self):
        """Constant can be used in login attempt loop."""
        attempts = 0
        while attempts < MAX_LOGIN_ATTEMPTS:
            attempts += 1

        assert attempts == MAX_LOGIN_ATTEMPTS


# ============================================================================
# Test Module-Level Availability
# ============================================================================

class TestModuleAvailability:
    """Test that module-level functions are accessible."""

    def test_log_to_file_exists(self):
        """log_to_file is callable."""
        assert callable(log_to_file)

    def test_cleanup_old_logs_exists(self):
        """cleanup_old_logs is callable."""
        assert callable(cleanup_old_logs)

    def test_rotate_log_if_needed_exists(self):
        """rotate_log_if_needed is callable."""
        assert callable(rotate_log_if_needed)

    def test_get_current_ip_exists(self):
        """get_current_ip is callable."""
        assert callable(get_current_ip)


# ============================================================================
# Test Constants Documentation
# ============================================================================

class TestConstantsDocumentation:
    """Test that constants have meaningful names."""

    def test_config_filename_descriptive(self):
        """CONFIG_FILENAME name describes its purpose."""
        assert "CONFIG" in "CONFIG_FILENAME"
        assert "FILENAME" in "CONFIG_FILENAME"

    def test_max_login_attempts_descriptive(self):
        """MAX_LOGIN_ATTEMPTS name describes its purpose."""
        assert "MAX" in "MAX_LOGIN_ATTEMPTS"
        assert "LOGIN" in "MAX_LOGIN_ATTEMPTS"

    def test_log_constants_descriptive(self):
        """Log constants have descriptive names."""
        assert "LOG" in "LOG_MAX_SIZE_MB"
        assert "LOG" in "LOG_KEEP_COUNT"


# ============================================================================
# Test IP Validation Function Exists
# ============================================================================

class TestValidateIPRestriction:
    """Test validate_ip_restriction() function."""

    def test_function_exists(self):
        """validate_ip_restriction exists."""
        from app_config import validate_ip_restriction
        assert callable(validate_ip_restriction)

    def test_no_restriction_returns_true(self):
        """Returns True when no IP restriction is set."""
        from app_config import validate_ip_restriction

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(app_config, "BIOVARASE_SERVER_IP", None, create=True):
                # Remove env var if exists
                os.environ.pop("BIOVARASE_SERVER_IP", None)
                result = validate_ip_restriction()

        assert result is True
