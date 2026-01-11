"""
Tests for Exporter class - Excel export functionality.

Tests cover:
- Workbook creation
- Color conversion
- Date normalization
- Sheet setup
- Result coloring by SD bands
- Expiration highlighting
- Excel formula helpers

Author: Claude Code
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from exporter import Exporter


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def exporter():
    """Create an Exporter instance for testing."""
    exp = Exporter()
    # Mock methods that Exporter expects from other mixins
    exp.on_log = MagicMock()
    exp.launch = MagicMock(return_value=True)
    exp.get_zscore = MagicMock(return_value=1.65)
    return exp


# ============================================================================
# Test Workbook Creation
# ============================================================================

class TestCreateWorkbook:
    """Test create_workbook() method."""

    def test_create_workbook_returns_workbook_and_sheet(self, exporter):
        """create_workbook() returns a workbook and worksheet."""
        wb, ws = exporter.create_workbook("Test")

        assert wb is not None
        assert ws is not None

    def test_create_workbook_sets_title(self, exporter):
        """Worksheet title is set correctly."""
        wb, ws = exporter.create_workbook("MyTitle")

        assert ws.title == "MyTitle"

    def test_create_workbook_default_title(self, exporter):
        """Default title is 'Biovarase'."""
        wb, ws = exporter.create_workbook()

        assert ws.title == "Biovarase"


# ============================================================================
# Test Color Conversion
# ============================================================================

class TestColorConversion:
    """Test _color() method."""

    def test_color_red(self, exporter):
        """Red returns correct ARGB."""
        result = exporter._color("red")
        assert result == "FFFF0000"

    def test_color_yellow(self, exporter):
        """Yellow returns correct ARGB."""
        result = exporter._color("yellow")
        assert result == "FFFFFF00"

    def test_color_green(self, exporter):
        """Green returns correct ARGB."""
        result = exporter._color("green")
        assert result == "FF00FF00"

    def test_color_hex_6_digits(self, exporter):
        """6-digit hex is converted via _convert_color."""
        # Note: _color() delegates to _convert_color() when available
        # _convert_color returns white for unknown colors
        result = exporter._color("#FF5500")
        # Falls back to _convert_color which returns white for unknowns
        assert result == "FFFFFFFF"

    def test_color_hex_8_digits(self, exporter):
        """8-digit hex is handled via _convert_color."""
        # Note: _color() delegates to _convert_color() when available
        result = exporter._color("AABBCCDD")
        # Falls back to _convert_color which returns white for unknowns
        assert result == "FFFFFFFF"

    def test_color_unknown_returns_white(self, exporter):
        """Unknown color names return white via _convert_color."""
        # Note: _color() delegates to _convert_color() which returns white
        result = exporter._color("unknown")
        assert result == "FFFFFFFF"


class TestConvertColor:
    """Test _convert_color() method."""

    def test_convert_color_red(self, exporter):
        """Red returns ARGB."""
        result = exporter._convert_color("red")
        assert result == "FFFF0000"

    def test_convert_color_yellow(self, exporter):
        """Yellow returns ARGB."""
        result = exporter._convert_color("yellow")
        assert result == "FFFFFF00"

    def test_convert_color_blue(self, exporter):
        """Blue returns ARGB."""
        result = exporter._convert_color("blue")
        assert result == "FF0000FF"

    def test_convert_color_green(self, exporter):
        """Green returns ARGB."""
        result = exporter._convert_color("green")
        assert result == "FF00FF00"

    def test_convert_color_teal(self, exporter):
        """Teal returns ARGB."""
        result = exporter._convert_color("teal")
        assert result == "FF008080"

    def test_convert_color_unknown_returns_white(self, exporter):
        """Unknown color returns white."""
        result = exporter._convert_color("purple")
        assert result == "FFFFFFFF"


# ============================================================================
# Test Date Normalization
# ============================================================================

class TestNormalizeDate:
    """Test _normalize_date() method."""

    def test_normalize_date_object(self, exporter):
        """date object is normalized correctly."""
        d = date(2025, 1, 15)
        result_date, result_sql = exporter._normalize_date(d)

        assert result_date == d
        assert result_sql == "2025-01-15"

    def test_normalize_datetime_object(self, exporter):
        """datetime object is converted to date."""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        result_date, result_sql = exporter._normalize_date(dt)

        assert result_date == date(2025, 1, 15)
        assert result_sql == "2025-01-15"

    def test_normalize_tuple_with_date(self, exporter):
        """Tuple containing date is unpacked."""
        d = date(2025, 6, 20)
        result_date, result_sql = exporter._normalize_date((d,))

        assert result_date == d
        assert result_sql == "2025-06-20"

    def test_normalize_list_with_date(self, exporter):
        """List containing date is unpacked."""
        d = date(2025, 12, 31)
        result_date, result_sql = exporter._normalize_date([d])

        assert result_date == d
        assert result_sql == "2025-12-31"

    def test_normalize_invalid_raises_typeerror(self, exporter):
        """Non-date value raises TypeError."""
        with pytest.raises(TypeError):
            exporter._normalize_date("2025-01-15")

    def test_normalize_empty_tuple_raises(self, exporter):
        """Empty tuple raises TypeError."""
        with pytest.raises(TypeError):
            exporter._normalize_date(())


# ============================================================================
# Test Result Color by SD Bands
# ============================================================================

class TestResultColor:
    """Test _result_color() method."""

    def test_within_2sd_no_color(self, exporter):
        """Values within 2SD return None."""
        # target=100, sd=5, result=105 (1SD above)
        result = exporter._result_color(105, 100, 5)
        assert result is None

    def test_within_1sd_no_color(self, exporter):
        """Values within 1SD return None."""
        result = exporter._result_color(102, 100, 5)
        assert result is None

    def test_between_2sd_and_3sd_yellow(self, exporter):
        """Values between 2SD and 3SD return yellow."""
        # target=100, sd=5, 2SD=110, 3SD=115
        # result=112 is between 2SD and 3SD
        result = exporter._result_color(112, 100, 5)
        assert result == "yellow"

    def test_between_minus_2sd_and_minus_3sd_yellow(self, exporter):
        """Values between -2SD and -3SD return yellow."""
        # target=100, sd=5, -2SD=90, -3SD=85
        # result=88 is between -3SD and -2SD
        result = exporter._result_color(88, 100, 5)
        assert result == "yellow"

    def test_above_3sd_red(self, exporter):
        """Values >= 3SD return red."""
        # target=100, sd=5, 3SD=115
        result = exporter._result_color(116, 100, 5)
        assert result == "red"

    def test_below_minus_3sd_red(self, exporter):
        """Values <= -3SD return red."""
        # target=100, sd=5, -3SD=85
        result = exporter._result_color(84, 100, 5)
        assert result == "red"

    def test_exactly_at_2sd_yellow(self, exporter):
        """Value exactly at 2SD returns yellow."""
        # target=100, sd=5, 2SD=110
        result = exporter._result_color(110, 100, 5)
        assert result == "yellow"

    def test_exactly_at_3sd_red(self, exporter):
        """Value exactly at 3SD returns red."""
        # target=100, sd=5, 3SD=115
        result = exporter._result_color(115, 100, 5)
        assert result == "red"


# ============================================================================
# Test Excel Formula Helpers
# ============================================================================

class TestExcelFormulas:
    """Test Excel formula generation methods."""

    def test_get_excel_column_letter(self, exporter):
        """Column index to letter conversion."""
        assert exporter.get_excel_column_letter(0) == "A"
        assert exporter.get_excel_column_letter(1) == "B"
        assert exporter.get_excel_column_letter(25) == "Z"
        assert exporter.get_excel_column_letter(26) == "AA"

    def test_get_formula_imp(self, exporter):
        """Imp% formula generation."""
        result = exporter.get_formula_imp(5)
        assert "H5" in result
        assert "0.5" in result
        assert "ROUND" in result

    def test_get_formula_bias(self, exporter):
        """Bias% formula generation."""
        result = exporter.get_formula_bias(5)
        assert "H5" in result
        assert "I5" in result
        assert "SQRT" in result
        assert "POWER" in result

    def test_get_formula_eta(self, exporter):
        """TEa% formula generation."""
        result = exporter.get_formula_eta(5)
        assert "J5" in result
        assert "K5" in result
        assert "1.65" in result  # zscore

    def test_get_formula_cvt(self, exporter):
        """CVt formula generation."""
        result = exporter.get_formula_cvt(5)
        assert "G5" in result
        assert "H5" in result
        assert "SQRT" in result

    def test_get_formula_drc(self, exporter):
        """Drc% (Critical Difference) formula generation."""
        result = exporter.get_formula_drc(5)
        assert "G5" in result
        assert "H5" in result
        assert "2.77" in result


class TestFormulaKImp:
    """Test get_formula_k_imp() method."""

    def test_k_imp_green_low(self, exporter):
        """k between 0.25 and 0.50 returns green."""
        # cva=2, cvw=5 -> k=0.4
        result = exporter.get_formula_k_imp(2, 5, 3)
        assert result is not None
        formula, color = result
        assert color == "green"
        assert "G3" in formula

    def test_k_imp_yellow_medium(self, exporter):
        """k between 0.50 and 0.75 returns yellow."""
        # cva=3, cvw=5 -> k=0.6
        result = exporter.get_formula_k_imp(3, 5, 3)
        assert result is not None
        formula, color = result
        assert color == "yellow"

    def test_k_imp_red_high(self, exporter):
        """k > 0.75 returns red."""
        # cva=4, cvw=5 -> k=0.8
        result = exporter.get_formula_k_imp(4, 5, 3)
        assert result is not None
        formula, color = result
        assert color == "red"

    def test_k_imp_zero_division(self, exporter):
        """Zero division returns None."""
        result = exporter.get_formula_k_imp(2, 0, 3)
        assert result is None


class TestFormulaKBias:
    """Test get_formula_k_bias() method."""

    def test_k_bias_returns_formula_and_color(self, exporter):
        """Returns formula and color tuple."""
        exporter.get_bias = MagicMock(return_value=5)
        exporter.get_cvt = MagicMock(return_value=10)

        result = exporter.get_formula_k_bias(105, 100, 5, 3, 3)

        assert result is not None
        formula, color = result
        assert formula is not None
        assert color in ("green", "yellow", "red")

    def test_k_bias_zero_division(self, exporter):
        """Zero division returns (None, None)."""
        exporter.get_bias = MagicMock(return_value=5)
        exporter.get_cvt = MagicMock(return_value=0)

        result = exporter.get_formula_k_bias(105, 100, 5, 3, 3)

        assert result == (None, None)


# ============================================================================
# Test Setup Sheet
# ============================================================================

class TestSetupSheet:
    """Test _setup_sheet() method."""

    def test_setup_sheet_returns_worksheet_and_row(self, exporter):
        """Returns worksheet and next row number."""
        wb, _ = exporter.create_workbook()
        ws, row = exporter._setup_sheet(wb)

        assert ws is not None
        assert row == 2  # Header is row 1, data starts row 2

    def test_setup_sheet_sets_title(self, exporter):
        """Sheet title is set to 'Biovarase'."""
        wb, _ = exporter.create_workbook()
        ws, _ = exporter._setup_sheet(wb)

        assert ws.title == "Biovarase"

    def test_setup_sheet_has_frozen_panes(self, exporter):
        """Sheet has frozen panes at A2."""
        wb, _ = exporter.create_workbook()
        ws, _ = exporter._setup_sheet(wb)

        assert ws.freeze_panes == "A2"

    def test_setup_sheet_has_autofilter(self, exporter):
        """Sheet has autofilter enabled."""
        wb, _ = exporter.create_workbook()
        ws, _ = exporter._setup_sheet(wb)

        assert ws.auto_filter.ref is not None


# ============================================================================
# Test Highlight Expiration
# ============================================================================

class TestHighlightExpiration:
    """Test _highlight_expiration() method."""

    def test_highlight_expired_red(self, exporter):
        """Expired dates get red fill."""
        wb, ws = exporter.create_workbook()
        exp_date = date(2025, 1, 1)
        recv_date = date(2025, 1, 15)  # After expiration

        exporter._highlight_expiration(ws, 1, exp_date, recv_date, "01-01-2025")

        cell = ws.cell(row=1, column=4)
        assert cell.value == "01-01-2025"
        assert cell.fill.start_color.rgb == "FFFF0000"  # Red

    def test_highlight_near_expiry_yellow(self, exporter):
        """Dates within 15 days of expiry get yellow fill."""
        wb, ws = exporter.create_workbook()
        exp_date = date(2025, 1, 20)
        recv_date = date(2025, 1, 10)  # 10 days before expiration

        exporter._highlight_expiration(ws, 1, exp_date, recv_date, "20-01-2025")

        cell = ws.cell(row=1, column=4)
        assert cell.fill.start_color.rgb == "FFFFFF00"  # Yellow

    def test_highlight_far_expiry_no_fill(self, exporter):
        """Dates more than 15 days from expiry have no fill."""
        wb, ws = exporter.create_workbook()
        exp_date = date(2025, 2, 15)
        recv_date = date(2025, 1, 10)  # 36 days before expiration

        exporter._highlight_expiration(ws, 1, exp_date, recv_date, "15-02-2025")

        cell = ws.cell(row=1, column=4)
        # No fill applied (default)
        assert cell.fill.start_color.rgb == "00000000"

    def test_highlight_none_dates_no_error(self, exporter):
        """None dates don't cause errors."""
        wb, ws = exporter.create_workbook()

        # Should not raise
        exporter._highlight_expiration(ws, 1, None, None, "N/A")


# ============================================================================
# Test Apply Fill Color
# ============================================================================

class TestApplyFillColor:
    """Test _apply_fill_color() method."""

    def test_apply_fill_with_color(self, exporter):
        """Applies fill color from result tuple."""
        wb, ws = exporter.create_workbook()

        exporter._apply_fill_color(ws, 1, 1, ("formula", "red"))

        cell = ws.cell(row=1, column=1)
        assert cell.fill.start_color.rgb == "FFFF0000"

    def test_apply_fill_none_tuple(self, exporter):
        """None tuple doesn't apply fill."""
        wb, ws = exporter.create_workbook()

        # Should not raise
        exporter._apply_fill_color(ws, 1, 1, None)

    def test_apply_fill_empty_color(self, exporter):
        """Empty color string doesn't apply fill."""
        wb, ws = exporter.create_workbook()

        # Should not raise
        exporter._apply_fill_color(ws, 1, 1, ("formula", ""))


# ============================================================================
# Test Save and Launch
# ============================================================================

class TestSaveAndLaunch:
    """Test save_and_launch() method."""

    def test_save_and_launch_creates_file(self, exporter):
        """Creates a temporary file."""
        wb, ws = exporter.create_workbook()

        path = exporter.save_and_launch(wb)

        assert path is not None
        assert path.endswith(".xlsx")
        assert os.path.exists(path)

        # Cleanup
        os.remove(path)

    def test_save_and_launch_calls_launch(self, exporter):
        """Calls launch() with file path."""
        wb, ws = exporter.create_workbook()

        path = exporter.save_and_launch(wb)

        exporter.launch.assert_called_once_with(path)

        # Cleanup
        os.remove(path)


# ============================================================================
# Test String Representation
# ============================================================================

class TestStringRepresentation:
    """Test __str__ method."""

    def test_str_contains_class_name(self, exporter):
        """String representation contains class name."""
        s = str(exporter)
        assert "Exporter" in s
        assert "MRO" in s
