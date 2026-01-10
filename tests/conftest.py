"""
Pytest configuration and shared fixtures for Biovarase test suite.

This file provides common fixtures used across all test modules.
"""
import os
import sys
import pytest
from typing import List, Dict, Any

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# ============================================================================
# QC Test Data Fixtures
# ============================================================================

@pytest.fixture
def qc_normal_series() -> List[float]:
    """
    Normal QC series - all values within 1SD.

    Returns:
        List of QC results centered around 100.0 with SD=5.0
    """
    return [100.0, 102.0, 98.0, 101.0, 99.0, 103.0, 97.0, 100.5]


@pytest.fixture
def qc_target_sd() -> tuple:
    """
    Standard target and SD for QC tests.

    Returns:
        Tuple of (target, sd) = (100.0, 5.0)
    """
    return (100.0, 5.0)


@pytest.fixture
def qc_violation_1_3s() -> List[float]:
    """
    QC series with 1:3S violation (last value > 3SD).

    Returns:
        Series ending with value at 116.0 (3.2 SD above mean)
    """
    return [100.0, 102.0, 98.0, 116.0]


@pytest.fixture
def qc_violation_2_2s() -> List[float]:
    """
    QC series with 2:2S violation (two consecutive > 2SD same side).

    Returns:
        Series with last two values > 2SD above mean
    """
    return [100.0, 98.0, 111.0, 112.0]


@pytest.fixture
def qc_violation_r_4s() -> List[float]:
    """
    QC series with R:4S violation (range of 2 consecutive ≥ 4SD).

    Returns:
        Series with two consecutive values spanning > 4SD
    """
    return [100.0, 90.0, 110.5]  # Last two span 20.5 (4.1 SD)


@pytest.fixture
def qc_violation_4_1s() -> List[float]:
    """
    QC series with 4:1S violation (four consecutive > 1SD same side).

    Returns:
        Series with last four values all > 1SD above mean
    """
    return [100.0, 98.0, 106.0, 107.0, 106.5, 108.0]


@pytest.fixture
def qc_violation_10_x() -> List[float]:
    """
    QC series with 10:X violation (ten consecutive same side of mean).

    Returns:
        Series with last ten values all above mean
    """
    return [100.0, 98.0] + [101.0 + i*0.5 for i in range(10)]


# ============================================================================
# Statistical Test Data Fixtures
# ============================================================================

@pytest.fixture
def stats_simple_series() -> List[float]:
    """
    Simple series for statistical calculations.

    Returns:
        List [10, 20, 30, 40, 50]
    """
    return [10.0, 20.0, 30.0, 40.0, 50.0]


@pytest.fixture
def stats_known_values() -> Dict[str, float]:
    """
    Known statistical values for stats_simple_series.

    Returns:
        Dictionary with mean, sd, cv, etc.
    """
    return {
        "mean": 30.0,
        "sd_sample": 15.811388300841896,  # ddof=1
        "sd_population": 14.142135623730951,  # ddof=0
        "cv_sample": 52.704,  # Approx
        "cv_population": 47.140,  # Approx
        "variance_sample": 250.0,
        "variance_population": 200.0,
    }


# ============================================================================
# Database Test Fixtures (for integration tests)
# ============================================================================

@pytest.fixture
def mock_db_credentials() -> Dict[str, str]:
    """
    Mock database credentials for testing.

    Returns:
        Dictionary with user, password, database, host
    """
    return {
        "user": "test_user",
        "password": "test_password",
        "database": "test_biovarase",
        "host": "localhost",
    }


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_log_file(tmp_path):
    """
    Create temporary log file for testing.

    Args:
        tmp_path: pytest built-in fixture for temporary directory

    Returns:
        Path to temporary log.txt file
    """
    log_file = tmp_path / "log.txt"
    log_file.write_text("Initial log content\n")
    return log_file


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Create temporary configuration file for testing.

    Args:
        tmp_path: pytest built-in fixture for temporary directory

    Returns:
        Path to temporary config file
    """
    config_file = tmp_path / "test_config.txt"
    config_file.write_text("test_value\n")
    return config_file


# ============================================================================
# Test Markers Documentation
# ============================================================================

def pytest_configure(config):
    """
    Register custom markers with pytest.

    This provides documentation for custom markers used in the test suite.
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (database, file I/O)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "critical: Critical tests for medical safety"
    )
    config.addinivalue_line(
        "markers", "westgard: Westgard QC rule tests"
    )
    config.addinivalue_line(
        "markers", "qc: Quality control statistical tests"
    )
    config.addinivalue_line(
        "markers", "security: Security and encryption tests"
    )
