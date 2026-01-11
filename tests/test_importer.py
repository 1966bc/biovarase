"""
Tests for Importer class - Mass spectrometry data import.

Tests cover:
- Device ID extraction from filenames
- Delimiter mapping
- Profile loading
- Header matching
- File parsing with profiles
- Result formatting
- Normalized output format

Author: Claude Code
"""
import pytest
import sys
import os
import tempfile
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from importer import Importer


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def importer():
    """Create an Importer instance for testing."""
    imp = Importer()
    # Mock methods that Importer expects from other mixins
    imp.on_log = MagicMock()
    return imp


@pytest.fixture
def sample_qc_file():
    """Create a temporary QC file for testing."""
    content = """Component Name\tBarcode\tMean\tReagent Lot
Glucose\tLOT-001\t5.50\tREAG-123
Creatinine\tLOT-001\t1.25\tREAG-456
Urea\tLOT-002\t7.80\tREAG-789
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def sample_qc_file_semicolon():
    """Create a temporary QC file with semicolon delimiter."""
    content = """Component Name;Barcode;Mean
Glucose;LOT-001;5.50
Creatinine;LOT-001;1.25
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


# ============================================================================
# Test Device ID Extraction
# ============================================================================

class TestExtractDeviceId:
    """Test _extract_device_id_from_filename() method."""

    def test_valid_uuid_in_filename(self, importer):
        """Extracts UUID from filename."""
        filename = "123e4567-e89b-12d3-a456-426614174001.txt"
        result = Importer._extract_device_id_from_filename(filename)
        assert result == "123e4567-e89b-12d3-a456-426614174001"

    def test_uuid_in_path(self, importer):
        """Extracts UUID from full path."""
        filepath = "/data/exports/123e4567-e89b-12d3-a456-426614174001.txt"
        result = Importer._extract_device_id_from_filename(filepath)
        assert result == "123e4567-e89b-12d3-a456-426614174001"

    def test_uuid_with_prefix(self, importer):
        """Extracts UUID even with prefix."""
        filename = "export_123e4567-e89b-12d3-a456-426614174001_data.txt"
        result = Importer._extract_device_id_from_filename(filename)
        assert result == "123e4567-e89b-12d3-a456-426614174001"

    def test_no_uuid_returns_none(self, importer):
        """Returns None if no UUID found."""
        filename = "simple_file.txt"
        result = Importer._extract_device_id_from_filename(filename)
        assert result is None

    def test_invalid_uuid_format_returns_none(self, importer):
        """Returns None for invalid UUID format."""
        filename = "12345-invalid-uuid.txt"
        result = Importer._extract_device_id_from_filename(filename)
        assert result is None

    def test_uppercase_uuid(self, importer):
        """Extracts uppercase UUID."""
        filename = "ABCDEF01-2345-6789-ABCD-EF0123456789.txt"
        result = Importer._extract_device_id_from_filename(filename)
        assert result == "ABCDEF01-2345-6789-ABCD-EF0123456789"


# ============================================================================
# Test Delimiter Mapping
# ============================================================================

class TestGetDelimiter:
    """Test _get_delimiter() method."""

    def test_tab_delimiter(self, importer):
        """'tab' maps to tab character."""
        assert importer._get_delimiter("tab") == "\t"

    def test_semicolon_delimiter(self, importer):
        """'semicolon' maps to semicolon."""
        assert importer._get_delimiter("semicolon") == ";"

    def test_comma_delimiter(self, importer):
        """'comma' maps to comma."""
        assert importer._get_delimiter("comma") == ","

    def test_default_is_tab(self, importer):
        """Unknown delimiter defaults to tab."""
        assert importer._get_delimiter("unknown") == "\t"

    def test_empty_string_is_tab(self, importer):
        """Empty string defaults to tab."""
        assert importer._get_delimiter("") == "\t"

    def test_none_is_tab(self, importer):
        """None defaults to tab."""
        assert importer._get_delimiter(None) == "\t"

    def test_case_insensitive(self, importer):
        """Delimiter names are case-insensitive."""
        assert importer._get_delimiter("TAB") == "\t"
        assert importer._get_delimiter("Tab") == "\t"
        assert importer._get_delimiter("SEMICOLON") == ";"


# ============================================================================
# Test Builtin Profiles
# ============================================================================

class TestBuiltinProfiles:
    """Test _builtin_profiles() method."""

    def test_returns_default_profile(self, importer):
        """Returns a default profile."""
        profiles = importer._builtin_profiles()
        assert "default" in profiles

    def test_default_has_required_fields(self, importer):
        """Default profile has all required fields."""
        profiles = importer._builtin_profiles()
        default = profiles["default"]

        assert "component_field" in default
        assert "id_field" in default
        assert "result_field" in default
        assert "delimiter" in default

    def test_default_extensions(self, importer):
        """Default profile has extensions."""
        profiles = importer._builtin_profiles()
        default = profiles["default"]

        assert ".txt" in default["extensions"]
        assert ".csv" in default["extensions"]


# ============================================================================
# Test Format Result
# ============================================================================

class TestFormatResult:
    """Test _format_result() method."""

    def test_raw_format(self, importer):
        """'raw' format returns value as-is."""
        result = importer._format_result("  5.50  ", "raw")
        assert result == "5.50"

    def test_float_format_default(self, importer):
        """'float' format with default decimals."""
        result = importer._format_result("5.5", "float")
        assert result == "5.50"

    def test_float3_format(self, importer):
        """'float3' format with 3 decimals."""
        result = importer._format_result("5.5", "float3")
        assert result == "5.500"

    def test_float0_format(self, importer):
        """'float0' format with 0 decimals."""
        result = importer._format_result("5.5", "float0")
        assert result == "6"

    def test_float_invalid_returns_none(self, importer):
        """Invalid float value returns None."""
        result = importer._format_result("invalid", "float")
        assert result is None

    def test_empty_value(self, importer):
        """Empty value returns empty string."""
        result = importer._format_result("", "raw")
        assert result == ""

    def test_none_value(self, importer):
        """None value returns empty string."""
        result = importer._format_result(None, "raw")
        assert result == ""


# ============================================================================
# Test Header Matching
# ============================================================================

class TestHeaderMatches:
    """Test _header_matches() method."""

    def test_matching_header(self, importer, sample_qc_file):
        """Returns True for matching header."""
        profile = {
            "component_field": "Component Name",
            "id_field": "Barcode",
            "result_field": "Mean",
            "delimiter": "tab",
        }

        result = importer._header_matches(sample_qc_file, profile)
        assert result is True

    def test_missing_field(self, importer, sample_qc_file):
        """Returns False for missing field."""
        profile = {
            "component_field": "Component Name",
            "id_field": "Missing Field",
            "result_field": "Mean",
            "delimiter": "tab",
        }

        result = importer._header_matches(sample_qc_file, profile)
        assert result is False

    def test_empty_profile_fields(self, importer, sample_qc_file):
        """Returns False for empty profile fields."""
        profile = {
            "component_field": "",
            "id_field": "",
            "result_field": "",
            "delimiter": "tab",
        }

        result = importer._header_matches(sample_qc_file, profile)
        assert result is False

    def test_nonexistent_file(self, importer):
        """Returns False for nonexistent file."""
        profile = {
            "component_field": "Component Name",
            "id_field": "Barcode",
            "result_field": "Mean",
            "delimiter": "tab",
        }

        result = importer._header_matches("/nonexistent/file.txt", profile)
        assert result is False


# ============================================================================
# Test File Parsing
# ============================================================================

class TestParseFileWithProfile:
    """Test _parse_file_with_profile_normalized() method."""

    def test_parse_valid_file(self, importer, sample_qc_file):
        """Parses valid file and returns normalized rows."""
        profile = {
            "component_field": "Component Name",
            "id_field": "Barcode",
            "result_field": "Mean",
            "reagent_lot_field": "Reagent Lot",
            "sample_type_field": "",
            "sample_type_value": "",
            "exclude_suffix": [],
            "exclude_prefix": [],
            "result_format": "raw",
            "delimiter": "tab",
        }

        rows = importer._parse_file_with_profile_normalized(sample_qc_file, profile)

        assert len(rows) == 3
        assert rows[0]["analyte"] == "Glucose"
        assert rows[0]["lot_number"] == "LOT-001"
        assert rows[0]["result"] == 5.50
        assert rows[0]["reagent_lot"] == "REAG-123"

    def test_parse_with_exclude_suffix(self, importer):
        """Excludes rows with matching suffix."""
        content = """Component Name\tBarcode\tMean
Glucose\tLOT-001\t5.50
Glucose_qual\tLOT-001\t0.95
Creatinine\tLOT-001\t1.25
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            filepath = f.name

        try:
            profile = {
                "component_field": "Component Name",
                "id_field": "Barcode",
                "result_field": "Mean",
                "reagent_lot_field": "",
                "sample_type_field": "",
                "sample_type_value": "",
                "exclude_suffix": ["_qual"],
                "exclude_prefix": [],
                "result_format": "raw",
                "delimiter": "tab",
            }

            rows = importer._parse_file_with_profile_normalized(filepath, profile)

            assert len(rows) == 2
            assert all("_qual" not in r["analyte"] for r in rows)
        finally:
            os.unlink(filepath)

    def test_parse_with_exclude_prefix(self, importer):
        """Excludes rows with matching prefix."""
        content = """Component Name\tBarcode\tMean
Glucose\tLOT-001\t5.50
IS_Glucose\tLOT-001\t1.00
Creatinine\tLOT-001\t1.25
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            filepath = f.name

        try:
            profile = {
                "component_field": "Component Name",
                "id_field": "Barcode",
                "result_field": "Mean",
                "reagent_lot_field": "",
                "sample_type_field": "",
                "sample_type_value": "",
                "exclude_suffix": [],
                "exclude_prefix": ["IS_"],
                "result_format": "raw",
                "delimiter": "tab",
            }

            rows = importer._parse_file_with_profile_normalized(filepath, profile)

            assert len(rows) == 2
            assert all(not r["analyte"].startswith("IS_") for r in rows)
        finally:
            os.unlink(filepath)

    def test_parse_empty_file(self, importer):
        """Returns empty list for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            f.flush()
            filepath = f.name

        try:
            profile = {
                "component_field": "Component Name",
                "id_field": "Barcode",
                "result_field": "Mean",
                "reagent_lot_field": "",
                "sample_type_field": "",
                "sample_type_value": "",
                "exclude_suffix": [],
                "exclude_prefix": [],
                "result_format": "raw",
                "delimiter": "tab",
            }

            rows = importer._parse_file_with_profile_normalized(filepath, profile)
            assert rows == []
        finally:
            os.unlink(filepath)


# ============================================================================
# Test Get Generic File Auto
# ============================================================================

class TestGetGenericFileAuto:
    """Test get_generic_file_auto() method."""

    def test_valid_file_and_device_id(self, importer, sample_qc_file):
        """Returns rows, device_id, and profile_name."""
        device_id = "123e4567-e89b-12d3-a456-426614174001"

        # Use builtin profile
        with patch.object(importer, '_load_profiles', return_value={}):
            rows, returned_device_id, profile_name = importer.get_generic_file_auto(
                sample_qc_file, device_id
            )

        assert rows is not None
        assert len(rows) == 3
        assert returned_device_id == device_id
        assert profile_name == "default"

    def test_empty_filepath_returns_none(self, importer):
        """Returns (None, None, None) for empty filepath."""
        rows, device_id, profile = importer.get_generic_file_auto("", "device123")
        assert rows is None
        assert device_id is None
        assert profile is None

    def test_empty_device_id_returns_none(self, importer, sample_qc_file):
        """Returns (None, None, None) for empty device_id."""
        rows, device_id, profile = importer.get_generic_file_auto(sample_qc_file, "")
        assert rows is None
        assert device_id is None
        assert profile is None

    def test_nonexistent_file_returns_none(self, importer):
        """Returns (None, None, None) for nonexistent file."""
        rows, device_id, profile = importer.get_generic_file_auto(
            "/nonexistent/file.txt", "device123"
        )
        assert rows is None
        assert device_id is None
        assert profile is None


# ============================================================================
# Test Get Generic File (Backward Compatible)
# ============================================================================

class TestGetGenericFile:
    """Test get_generic_file() method (backward compatible)."""

    def test_extracts_device_id_from_filename(self, importer):
        """Extracts device_id from filename and calls get_generic_file_auto."""
        content = """Component Name\tBarcode\tMean
Glucose\tLOT-001\t5.50
"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            prefix='123e4567-e89b-12d3-a456-426614174001_',
            delete=False
        ) as f:
            f.write(content)
            f.flush()
            filepath = f.name

        try:
            with patch.object(importer, '_load_profiles', return_value={}):
                rows = importer.get_generic_file(filepath)

            assert rows is not None
            assert len(rows) == 1
        finally:
            os.unlink(filepath)

    def test_no_device_id_returns_none(self, importer, sample_qc_file):
        """Returns None if no device_id in filename."""
        rows = importer.get_generic_file(sample_qc_file)
        assert rows is None


# ============================================================================
# Test String Representation
# ============================================================================

class TestStringRepresentation:
    """Test __str__ method."""

    def test_str_contains_class_name(self, importer):
        """String representation contains class name."""
        s = str(importer)
        assert "Importer" in s


# ============================================================================
# Test Profile Loading
# ============================================================================

class TestLoadProfiles:
    """Test _load_profiles() method."""

    def test_no_file_returns_empty(self, importer):
        """Returns empty dict if profiles file doesn't exist."""
        with patch.object(importer, '_profiles_file_path', return_value='/nonexistent/path.ini'):
            profiles = importer._load_profiles()
        assert profiles == {}

    def test_valid_ini_file(self, importer):
        """Loads profiles from valid INI file."""
        ini_content = """[device_test-uuid]
description = Test Device
extensions = .txt, .csv
delimiter = tab
component_field = Component Name
id_field = Barcode
result_field = Mean
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(ini_content)
            f.flush()
            ini_path = f.name

        try:
            with patch.object(importer, '_profiles_file_path', return_value=ini_path):
                profiles = importer._load_profiles()

            assert "device_test-uuid" in profiles
            profile = profiles["device_test-uuid"]
            assert profile["description"] == "Test Device"
            assert profile["component_field"] == "Component Name"
            assert ".txt" in profile["extensions"]
        finally:
            os.unlink(ini_path)


# ============================================================================
# Test Log Warning
# ============================================================================

class TestLogWarning:
    """Test _log_warning() method."""

    def test_log_warning_calls_on_log(self, importer):
        """_log_warning calls on_log with RuntimeError."""
        importer._log_warning("test_function", "Test message")

        importer.on_log.assert_called_once()
        call_args = importer.on_log.call_args[0]
        assert call_args[0] == "test_function"
        assert isinstance(call_args[1], RuntimeError)
        assert "Test message" in str(call_args[1])

    def test_log_warning_never_raises(self, importer):
        """_log_warning never raises even if on_log fails."""
        importer.on_log = MagicMock(side_effect=RuntimeError("Oops"))

        # Should not raise
        importer._log_warning("test", "message")
