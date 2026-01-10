"""
Test suite for Log Rotation functionality (frames/login.py).

Tests log file rotation and cleanup mechanisms to prevent disk full.
"""
import pytest
import os
import glob
from app_config import rotate_log_if_needed, cleanup_old_logs, LOG_MAX_SIZE_MB, LOG_KEEP_COUNT


@pytest.mark.unit
class TestLogRotation:
    """Test log rotation and cleanup mechanisms."""

    def test_rotate_log_when_oversized(self, tmp_path, monkeypatch):
        """Test log rotation when file exceeds LOG_MAX_SIZE_MB."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create large log file (>10 MB)
        log_file = tmp_path / "log.txt"
        size_bytes = int((LOG_MAX_SIZE_MB + 1) * 1024 * 1024)
        log_file.write_bytes(b"X" * size_bytes)

        # Verify file is large
        assert os.path.getsize(log_file) / (1024 * 1024) > LOG_MAX_SIZE_MB

        # Rotate
        rotate_log_if_needed()

        # log.txt should not exist (or be new/small)
        if os.path.exists("log.txt"):
            size_mb = os.path.getsize("log.txt") / (1024 * 1024)
            assert size_mb < 1, "log.txt should be new/small after rotation"

        # Rotated file should exist
        rotated_files = glob.glob("log_*.txt")
        assert len(rotated_files) >= 1, "Rotated log file should exist"

    def test_no_rotate_when_small(self, tmp_path, monkeypatch):
        """Test no rotation when file < LOG_MAX_SIZE_MB."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create small log file (<10 MB)
        log_file = tmp_path / "log.txt"
        size_bytes = int((LOG_MAX_SIZE_MB - 1) * 1024 * 1024)
        log_file.write_bytes(b"X" * size_bytes)

        original_content = log_file.read_bytes()

        # Rotate
        rotate_log_if_needed()

        # log.txt should still exist with same content
        assert os.path.exists("log.txt"), "log.txt should still exist"
        assert log_file.read_bytes() == original_content, "Content should be unchanged"

        # No rotated files should exist
        rotated_files = glob.glob("log_*.txt")
        assert len(rotated_files) == 0, "No rotated files should be created"

    def test_cleanup_keeps_only_n_logs(self, tmp_path, monkeypatch):
        """Test cleanup_old_logs keeps only LOG_KEEP_COUNT files."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create 10 old rotated log files
        for i in range(10):
            filename = f"log_2025120{i}_120000.txt"
            (tmp_path / filename).write_text(f"Old log {i}\n")

        # Verify 10 files created
        rotated_files = glob.glob("log_*.txt")
        assert len(rotated_files) == 10

        # Cleanup
        cleanup_old_logs(keep=LOG_KEEP_COUNT)

        # Only LOG_KEEP_COUNT should remain
        rotated_files = glob.glob("log_*.txt")
        assert len(rotated_files) <= LOG_KEEP_COUNT, \
            f"Should keep only {LOG_KEEP_COUNT} files, found {len(rotated_files)}"

    def test_cleanup_does_nothing_if_few_logs(self, tmp_path, monkeypatch):
        """Test cleanup does nothing if fewer than keep count."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create only 2 old logs
        for i in range(2):
            filename = f"log_2025120{i}_120000.txt"
            (tmp_path / filename).write_text(f"Old log {i}\n")

        # Cleanup
        cleanup_old_logs(keep=LOG_KEEP_COUNT)

        # All 2 should remain
        rotated_files = glob.glob("log_*.txt")
        assert len(rotated_files) == 2, "All files should remain (< keep count)"

    def test_rotate_creates_timestamped_filename(self, tmp_path, monkeypatch):
        """Test rotated file has correct timestamp format."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create large log
        log_file = tmp_path / "log.txt"
        size_bytes = int((LOG_MAX_SIZE_MB + 1) * 1024 * 1024)
        log_file.write_bytes(b"X" * size_bytes)

        # Rotate
        rotate_log_if_needed()

        # Check rotated filename format: log_YYYYMMDD_HHMMSS.txt
        rotated_files = glob.glob("log_*.txt")
        assert len(rotated_files) >= 1

        filename = rotated_files[0]
        # Extract timestamp part
        timestamp_part = filename.replace("log_", "").replace(".txt", "")

        # Verify format: 15 characters (YYYYMMDD_HHMMSS)
        assert len(timestamp_part) == 15, f"Timestamp format incorrect: {timestamp_part}"
        assert "_" in timestamp_part, "Timestamp should contain underscore"

    def test_rotate_safe_if_no_log_file(self, tmp_path, monkeypatch):
        """Test rotation does nothing if log.txt doesn't exist."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # No log.txt exists

        # Should not raise exception
        rotate_log_if_needed()

        # Still no files
        assert not os.path.exists("log.txt")
        assert len(glob.glob("log_*.txt")) == 0


@pytest.mark.unit
def test_log_max_size_constant():
    """Test LOG_MAX_SIZE_MB constant is reasonable."""
    assert LOG_MAX_SIZE_MB > 0, "LOG_MAX_SIZE_MB must be positive"
    assert LOG_MAX_SIZE_MB <= 100, "LOG_MAX_SIZE_MB should be reasonable (≤100 MB)"


@pytest.mark.unit
def test_log_keep_count_constant():
    """Test LOG_KEEP_COUNT constant is reasonable."""
    assert LOG_KEEP_COUNT > 0, "LOG_KEEP_COUNT must be positive"
    assert LOG_KEEP_COUNT <= 20, "LOG_KEEP_COUNT should be reasonable (≤20)"
