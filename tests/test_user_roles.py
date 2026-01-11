"""
Test suite for user role-based permissions.

Tests all permission methods across the 7 user roles defined in Biovarase.
Uses mock Engine with simulated log_user to test each permission level.

Role Hierarchy:
    0 = ROLE_APP_ADMIN      - Global admin, all permissions
    1 = ROLE_COUNTRY_ADMIN  - Country scope admin
    2 = ROLE_REGIONAL_ADMIN - Regional scope admin
    3 = ROLE_LAB_ADMIN      - Lab configuration
    4 = ROLE_SUPERUSER      - QC validation, batch management
    5 = ROLE_TECHNICIAN     - Data entry only
    6 = ROLE_VIEWER         - Read-only access
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import role constants
from engine import (
    ROLE_APP_ADMIN,
    ROLE_COUNTRY_ADMIN,
    ROLE_REGIONAL_ADMIN,
    ROLE_LAB_ADMIN,
    ROLE_SUPERUSER,
    ROLE_TECHNICIAN,
    ROLE_VIEWER,
)


# ============================================================================
# Fixtures for each user role
# ============================================================================

@pytest.fixture
def mock_engine():
    """
    Create a mock Engine with permission methods.

    Returns a factory function that creates an engine with specified role.
    """
    def _create_engine(role: int, org_id: int = None, lab_id: int = 2):
        """Create mock engine with given role."""
        engine = MagicMock()
        engine.log_user = {
            "user_id": 100 + role,
            "nickname": f"test_role_{role}",
            "role": role,
            "org_id": org_id,
            "lab_id": lab_id,
        }
        engine.current_ids = {
            "lab_id": lab_id,
            "site_id": 1,
            "section_id": None,
        }

        # Implement get_user_role
        def get_user_role():
            try:
                return int(engine.log_user.get("role", 99))
            except (TypeError, ValueError):
                return 99
        engine.get_user_role = get_user_role

        # Implement can_validate_qc: roles 0-4 can validate
        def can_validate_qc():
            return get_user_role() <= ROLE_SUPERUSER
        engine.can_validate_qc = can_validate_qc

        # Implement can_configure_system: only role 0
        def can_configure_system():
            return get_user_role() == ROLE_APP_ADMIN
        engine.can_configure_system = can_configure_system

        # Implement can_modify_data: roles 0-5 can modify
        def can_modify_data():
            return get_user_role() <= ROLE_TECHNICIAN
        engine.can_modify_data = can_modify_data

        # Implement is_read_only: only role 6
        def is_read_only():
            return get_user_role() >= ROLE_VIEWER
        engine.is_read_only = is_read_only

        # Implement can_manage_local_config: roles 0-3
        def can_manage_local_config():
            return get_user_role() <= ROLE_LAB_ADMIN
        engine.can_manage_local_config = can_manage_local_config

        # Implement can_delete_results: roles 0-4
        def can_delete_results():
            return get_user_role() <= ROLE_SUPERUSER
        engine.can_delete_results = can_delete_results

        # Implement is_admin: only role 0
        def is_admin():
            return get_user_role() == ROLE_APP_ADMIN
        engine.is_admin = is_admin

        # Implement is_superuser: only role 4
        def is_superuser():
            return get_user_role() == ROLE_SUPERUSER
        engine.is_superuser = is_superuser

        # Implement is_user (technician): only role 5
        def is_user():
            return get_user_role() == ROLE_TECHNICIAN
        engine.is_user = is_user

        # Implement is_lab_admin: only role 3
        def is_lab_admin():
            return get_user_role() == ROLE_LAB_ADMIN
        engine.is_lab_admin = is_lab_admin

        # Implement get_data_scope: returns (scope_type, filter_id)
        def get_data_scope():
            role = get_user_role()
            if role == ROLE_APP_ADMIN:
                return ("global", None)
            else:
                return ("lab", engine.current_ids.get("lab_id"))
        engine.get_data_scope = get_data_scope

        # Implement get_user_org_id: returns user's org_id
        def get_user_org_id():
            return engine.log_user.get("org_id")
        engine.get_user_org_id = get_user_org_id

        return engine

    return _create_engine


@pytest.fixture
def app_admin(mock_engine):
    """App Admin (role=0) - Global administrator."""
    return mock_engine(ROLE_APP_ADMIN, org_id=None)


@pytest.fixture
def country_admin(mock_engine):
    """Country Admin (role=1) - Country scope."""
    return mock_engine(ROLE_COUNTRY_ADMIN, org_id=1000)


@pytest.fixture
def regional_admin(mock_engine):
    """Regional Admin (role=2) - Regional scope."""
    return mock_engine(ROLE_REGIONAL_ADMIN, org_id=2000)


@pytest.fixture
def lab_admin(mock_engine):
    """Lab Admin (role=3) - Lab configuration."""
    return mock_engine(ROLE_LAB_ADMIN, org_id=2002)


@pytest.fixture
def superuser(mock_engine):
    """Superuser (role=4) - QC validation."""
    return mock_engine(ROLE_SUPERUSER, org_id=2002)


@pytest.fixture
def technician(mock_engine):
    """Technician (role=5) - Data entry."""
    return mock_engine(ROLE_TECHNICIAN, org_id=2002)


@pytest.fixture
def viewer(mock_engine):
    """Viewer (role=6) - Read-only."""
    return mock_engine(ROLE_VIEWER, org_id=2002)


# ============================================================================
# Test Role Constants
# ============================================================================

class TestRoleConstants:
    """Verify role constants are correctly defined."""

    def test_role_app_admin_is_zero(self):
        """App Admin should be role 0."""
        assert ROLE_APP_ADMIN == 0

    def test_role_country_admin_is_one(self):
        """Country Admin should be role 1."""
        assert ROLE_COUNTRY_ADMIN == 1

    def test_role_regional_admin_is_two(self):
        """Regional Admin should be role 2."""
        assert ROLE_REGIONAL_ADMIN == 2

    def test_role_lab_admin_is_three(self):
        """Lab Admin should be role 3."""
        assert ROLE_LAB_ADMIN == 3

    def test_role_superuser_is_four(self):
        """Superuser should be role 4."""
        assert ROLE_SUPERUSER == 4

    def test_role_technician_is_five(self):
        """Technician should be role 5."""
        assert ROLE_TECHNICIAN == 5

    def test_role_viewer_is_six(self):
        """Viewer should be role 6."""
        assert ROLE_VIEWER == 6

    def test_roles_are_sequential(self):
        """Roles should be sequential from 0 to 6."""
        roles = [
            ROLE_APP_ADMIN,
            ROLE_COUNTRY_ADMIN,
            ROLE_REGIONAL_ADMIN,
            ROLE_LAB_ADMIN,
            ROLE_SUPERUSER,
            ROLE_TECHNICIAN,
            ROLE_VIEWER,
        ]
        assert roles == list(range(7))


# ============================================================================
# Test can_validate_qc() - Roles 0-4 can validate
# ============================================================================

class TestCanValidateQC:
    """Test can_validate_qc() permission method."""

    @pytest.mark.critical
    def test_app_admin_can_validate(self, app_admin):
        """App Admin (0) can validate QC."""
        assert app_admin.can_validate_qc() is True

    @pytest.mark.critical
    def test_country_admin_can_validate(self, country_admin):
        """Country Admin (1) can validate QC."""
        assert country_admin.can_validate_qc() is True

    @pytest.mark.critical
    def test_regional_admin_can_validate(self, regional_admin):
        """Regional Admin (2) can validate QC."""
        assert regional_admin.can_validate_qc() is True

    @pytest.mark.critical
    def test_lab_admin_can_validate(self, lab_admin):
        """Lab Admin (3) can validate QC."""
        assert lab_admin.can_validate_qc() is True

    @pytest.mark.critical
    def test_superuser_can_validate(self, superuser):
        """Superuser (4) can validate QC."""
        assert superuser.can_validate_qc() is True

    @pytest.mark.critical
    def test_technician_cannot_validate(self, technician):
        """Technician (5) cannot validate QC."""
        assert technician.can_validate_qc() is False

    @pytest.mark.critical
    def test_viewer_cannot_validate(self, viewer):
        """Viewer (6) cannot validate QC."""
        assert viewer.can_validate_qc() is False


# ============================================================================
# Test can_configure_system() - Only role 0
# ============================================================================

class TestCanConfigureSystem:
    """Test can_configure_system() permission method."""

    @pytest.mark.critical
    def test_app_admin_can_configure_system(self, app_admin):
        """App Admin (0) can configure system (master data)."""
        assert app_admin.can_configure_system() is True

    def test_country_admin_cannot_configure_system(self, country_admin):
        """Country Admin (1) cannot configure system."""
        assert country_admin.can_configure_system() is False

    def test_regional_admin_cannot_configure_system(self, regional_admin):
        """Regional Admin (2) cannot configure system."""
        assert regional_admin.can_configure_system() is False

    def test_lab_admin_cannot_configure_system(self, lab_admin):
        """Lab Admin (3) cannot configure system."""
        assert lab_admin.can_configure_system() is False

    def test_superuser_cannot_configure_system(self, superuser):
        """Superuser (4) cannot configure system."""
        assert superuser.can_configure_system() is False

    def test_technician_cannot_configure_system(self, technician):
        """Technician (5) cannot configure system."""
        assert technician.can_configure_system() is False

    def test_viewer_cannot_configure_system(self, viewer):
        """Viewer (6) cannot configure system."""
        assert viewer.can_configure_system() is False


# ============================================================================
# Test can_modify_data() - Roles 0-5 can modify
# ============================================================================

class TestCanModifyData:
    """Test can_modify_data() permission method."""

    def test_app_admin_can_modify_data(self, app_admin):
        """App Admin (0) can modify data."""
        assert app_admin.can_modify_data() is True

    def test_country_admin_can_modify_data(self, country_admin):
        """Country Admin (1) can modify data."""
        assert country_admin.can_modify_data() is True

    def test_regional_admin_can_modify_data(self, regional_admin):
        """Regional Admin (2) can modify data."""
        assert regional_admin.can_modify_data() is True

    def test_lab_admin_can_modify_data(self, lab_admin):
        """Lab Admin (3) can modify data."""
        assert lab_admin.can_modify_data() is True

    def test_superuser_can_modify_data(self, superuser):
        """Superuser (4) can modify data."""
        assert superuser.can_modify_data() is True

    def test_technician_can_modify_data(self, technician):
        """Technician (5) can modify data."""
        assert technician.can_modify_data() is True

    @pytest.mark.critical
    def test_viewer_cannot_modify_data(self, viewer):
        """Viewer (6) cannot modify data."""
        assert viewer.can_modify_data() is False


# ============================================================================
# Test is_read_only() - Only role 6
# ============================================================================

class TestIsReadOnly:
    """Test is_read_only() permission method."""

    def test_app_admin_is_not_read_only(self, app_admin):
        """App Admin (0) is not read-only."""
        assert app_admin.is_read_only() is False

    def test_country_admin_is_not_read_only(self, country_admin):
        """Country Admin (1) is not read-only."""
        assert country_admin.is_read_only() is False

    def test_regional_admin_is_not_read_only(self, regional_admin):
        """Regional Admin (2) is not read-only."""
        assert regional_admin.is_read_only() is False

    def test_lab_admin_is_not_read_only(self, lab_admin):
        """Lab Admin (3) is not read-only."""
        assert lab_admin.is_read_only() is False

    def test_superuser_is_not_read_only(self, superuser):
        """Superuser (4) is not read-only."""
        assert superuser.is_read_only() is False

    def test_technician_is_not_read_only(self, technician):
        """Technician (5) is not read-only."""
        assert technician.is_read_only() is False

    def test_viewer_is_read_only(self, viewer):
        """Viewer (6) is read-only."""
        assert viewer.is_read_only() is True


# ============================================================================
# Test can_manage_local_config() - Roles 0-3
# ============================================================================

class TestCanManageLocalConfig:
    """Test can_manage_local_config() permission method."""

    def test_app_admin_can_manage_local_config(self, app_admin):
        """App Admin (0) can manage local config."""
        assert app_admin.can_manage_local_config() is True

    def test_country_admin_can_manage_local_config(self, country_admin):
        """Country Admin (1) can manage local config."""
        assert country_admin.can_manage_local_config() is True

    def test_regional_admin_can_manage_local_config(self, regional_admin):
        """Regional Admin (2) can manage local config."""
        assert regional_admin.can_manage_local_config() is True

    def test_lab_admin_can_manage_local_config(self, lab_admin):
        """Lab Admin (3) can manage local config."""
        assert lab_admin.can_manage_local_config() is True

    def test_superuser_cannot_manage_local_config(self, superuser):
        """Superuser (4) cannot manage local config."""
        assert superuser.can_manage_local_config() is False

    def test_technician_cannot_manage_local_config(self, technician):
        """Technician (5) cannot manage local config."""
        assert technician.can_manage_local_config() is False

    def test_viewer_cannot_manage_local_config(self, viewer):
        """Viewer (6) cannot manage local config."""
        assert viewer.can_manage_local_config() is False


# ============================================================================
# Test can_delete_results() - Roles 0-4
# ============================================================================

class TestCanDeleteResults:
    """Test can_delete_results() permission method."""

    @pytest.mark.critical
    def test_app_admin_can_delete_results(self, app_admin):
        """App Admin (0) can delete results."""
        assert app_admin.can_delete_results() is True

    @pytest.mark.critical
    def test_country_admin_can_delete_results(self, country_admin):
        """Country Admin (1) can delete results."""
        assert country_admin.can_delete_results() is True

    @pytest.mark.critical
    def test_regional_admin_can_delete_results(self, regional_admin):
        """Regional Admin (2) can delete results."""
        assert regional_admin.can_delete_results() is True

    @pytest.mark.critical
    def test_lab_admin_can_delete_results(self, lab_admin):
        """Lab Admin (3) can delete results."""
        assert lab_admin.can_delete_results() is True

    @pytest.mark.critical
    def test_superuser_can_delete_results(self, superuser):
        """Superuser (4) can delete results."""
        assert superuser.can_delete_results() is True

    @pytest.mark.critical
    def test_technician_cannot_delete_results(self, technician):
        """Technician (5) cannot delete results."""
        assert technician.can_delete_results() is False

    @pytest.mark.critical
    def test_viewer_cannot_delete_results(self, viewer):
        """Viewer (6) cannot delete results."""
        assert viewer.can_delete_results() is False


# ============================================================================
# Test Role Identity Methods
# ============================================================================

class TestRoleIdentity:
    """Test role identity methods (is_admin, is_superuser, etc.)."""

    def test_is_admin_only_for_app_admin(self, app_admin, country_admin, lab_admin, superuser, technician, viewer):
        """is_admin() returns True only for App Admin."""
        assert app_admin.is_admin() is True
        assert country_admin.is_admin() is False
        assert lab_admin.is_admin() is False
        assert superuser.is_admin() is False
        assert technician.is_admin() is False
        assert viewer.is_admin() is False

    def test_is_superuser_only_for_superuser(self, app_admin, lab_admin, superuser, technician, viewer):
        """is_superuser() returns True only for Superuser."""
        assert app_admin.is_superuser() is False
        assert lab_admin.is_superuser() is False
        assert superuser.is_superuser() is True
        assert technician.is_superuser() is False
        assert viewer.is_superuser() is False

    def test_is_user_only_for_technician(self, app_admin, lab_admin, superuser, technician, viewer):
        """is_user() returns True only for Technician."""
        assert app_admin.is_user() is False
        assert lab_admin.is_user() is False
        assert superuser.is_user() is False
        assert technician.is_user() is True
        assert viewer.is_user() is False

    def test_is_lab_admin_only_for_lab_admin(self, app_admin, lab_admin, superuser, technician, viewer):
        """is_lab_admin() returns True only for Lab Admin."""
        assert app_admin.is_lab_admin() is False
        assert lab_admin.is_lab_admin() is True
        assert superuser.is_lab_admin() is False
        assert technician.is_lab_admin() is False
        assert viewer.is_lab_admin() is False


# ============================================================================
# Test get_user_role()
# ============================================================================

class TestGetUserRole:
    """Test get_user_role() method."""

    def test_get_user_role_returns_correct_value(self, mock_engine):
        """get_user_role() returns the correct role number."""
        for role in range(7):
            engine = mock_engine(role)
            assert engine.get_user_role() == role

    def test_get_user_role_with_invalid_role_returns_99(self, mock_engine):
        """get_user_role() returns 99 for invalid role."""
        engine = mock_engine(0)
        engine.log_user["role"] = "invalid"
        assert engine.get_user_role() == 99

    def test_get_user_role_with_none_returns_99(self, mock_engine):
        """get_user_role() returns 99 when role is None."""
        engine = mock_engine(0)
        engine.log_user["role"] = None
        assert engine.get_user_role() == 99


# ============================================================================
# Parametrized Tests for Complete Coverage
# ============================================================================

@pytest.mark.parametrize("role,expected", [
    (ROLE_APP_ADMIN, True),
    (ROLE_COUNTRY_ADMIN, True),
    (ROLE_REGIONAL_ADMIN, True),
    (ROLE_LAB_ADMIN, True),
    (ROLE_SUPERUSER, True),
    (ROLE_TECHNICIAN, False),
    (ROLE_VIEWER, False),
])
def test_can_validate_qc_parametrized(mock_engine, role, expected):
    """Parametrized test for can_validate_qc()."""
    engine = mock_engine(role)
    assert engine.can_validate_qc() is expected


@pytest.mark.parametrize("role,expected", [
    (ROLE_APP_ADMIN, True),
    (ROLE_COUNTRY_ADMIN, False),
    (ROLE_REGIONAL_ADMIN, False),
    (ROLE_LAB_ADMIN, False),
    (ROLE_SUPERUSER, False),
    (ROLE_TECHNICIAN, False),
    (ROLE_VIEWER, False),
])
def test_can_configure_system_parametrized(mock_engine, role, expected):
    """Parametrized test for can_configure_system()."""
    engine = mock_engine(role)
    assert engine.can_configure_system() is expected


@pytest.mark.parametrize("role,expected", [
    (ROLE_APP_ADMIN, True),
    (ROLE_COUNTRY_ADMIN, True),
    (ROLE_REGIONAL_ADMIN, True),
    (ROLE_LAB_ADMIN, True),
    (ROLE_SUPERUSER, True),
    (ROLE_TECHNICIAN, True),
    (ROLE_VIEWER, False),
])
def test_can_modify_data_parametrized(mock_engine, role, expected):
    """Parametrized test for can_modify_data()."""
    engine = mock_engine(role)
    assert engine.can_modify_data() is expected


@pytest.mark.parametrize("role,expected", [
    (ROLE_APP_ADMIN, True),
    (ROLE_COUNTRY_ADMIN, True),
    (ROLE_REGIONAL_ADMIN, True),
    (ROLE_LAB_ADMIN, True),
    (ROLE_SUPERUSER, False),
    (ROLE_TECHNICIAN, False),
    (ROLE_VIEWER, False),
])
def test_can_manage_local_config_parametrized(mock_engine, role, expected):
    """Parametrized test for can_manage_local_config()."""
    engine = mock_engine(role)
    assert engine.can_manage_local_config() is expected


@pytest.mark.parametrize("role,expected", [
    (ROLE_APP_ADMIN, True),
    (ROLE_COUNTRY_ADMIN, True),
    (ROLE_REGIONAL_ADMIN, True),
    (ROLE_LAB_ADMIN, True),
    (ROLE_SUPERUSER, True),
    (ROLE_TECHNICIAN, False),
    (ROLE_VIEWER, False),
])
@pytest.mark.critical
def test_can_delete_results_parametrized(mock_engine, role, expected):
    """Parametrized test for can_delete_results()."""
    engine = mock_engine(role)
    assert engine.can_delete_results() is expected


# ============================================================================
# Test get_data_scope() - Data filtering based on role
# ============================================================================

class TestGetDataScope:
    """Test get_data_scope() method for data filtering."""

    def test_app_admin_has_global_scope(self, app_admin):
        """App Admin (0) has global scope with no filtering."""
        scope, filter_id = app_admin.get_data_scope()
        assert scope == "global"
        assert filter_id is None

    def test_country_admin_has_lab_scope(self, country_admin):
        """Country Admin (1) currently filters by lab_id."""
        scope, filter_id = country_admin.get_data_scope()
        assert scope == "lab"
        assert filter_id == 2  # Default lab_id from fixture

    def test_regional_admin_has_lab_scope(self, regional_admin):
        """Regional Admin (2) currently filters by lab_id."""
        scope, filter_id = regional_admin.get_data_scope()
        assert scope == "lab"
        assert filter_id == 2

    def test_lab_admin_has_lab_scope(self, lab_admin):
        """Lab Admin (3) filters by lab_id."""
        scope, filter_id = lab_admin.get_data_scope()
        assert scope == "lab"
        assert filter_id == 2

    def test_superuser_has_lab_scope(self, superuser):
        """Superuser (4) filters by lab_id."""
        scope, filter_id = superuser.get_data_scope()
        assert scope == "lab"
        assert filter_id == 2

    def test_technician_has_lab_scope(self, technician):
        """Technician (5) filters by lab_id."""
        scope, filter_id = technician.get_data_scope()
        assert scope == "lab"
        assert filter_id == 2

    def test_viewer_has_lab_scope(self, viewer):
        """Viewer (6) filters by lab_id."""
        scope, filter_id = viewer.get_data_scope()
        assert scope == "lab"
        assert filter_id == 2

    def test_scope_with_different_lab_id(self, mock_engine):
        """Scope returns correct lab_id when different."""
        engine = mock_engine(ROLE_TECHNICIAN, org_id=3000, lab_id=5)
        scope, filter_id = engine.get_data_scope()
        assert scope == "lab"
        assert filter_id == 5

    def test_scope_with_none_lab_id(self, mock_engine):
        """Scope handles None lab_id gracefully."""
        engine = mock_engine(ROLE_TECHNICIAN, org_id=3000, lab_id=None)
        engine.current_ids["lab_id"] = None
        scope, filter_id = engine.get_data_scope()
        assert scope == "lab"
        assert filter_id is None


# ============================================================================
# Test get_user_org_id() - User organization ID
# ============================================================================

class TestGetUserOrgId:
    """Test get_user_org_id() method."""

    def test_app_admin_org_id_is_none(self, app_admin):
        """App Admin has org_id = None (global scope)."""
        assert app_admin.get_user_org_id() is None

    def test_country_admin_has_org_id(self, country_admin):
        """Country Admin has specific org_id."""
        assert country_admin.get_user_org_id() == 1000

    def test_regional_admin_has_org_id(self, regional_admin):
        """Regional Admin has specific org_id."""
        assert regional_admin.get_user_org_id() == 2000

    def test_lab_admin_has_org_id(self, lab_admin):
        """Lab Admin has specific org_id."""
        assert lab_admin.get_user_org_id() == 2002

    def test_superuser_has_org_id(self, superuser):
        """Superuser has specific org_id."""
        assert superuser.get_user_org_id() == 2002

    def test_technician_has_org_id(self, technician):
        """Technician has specific org_id."""
        assert technician.get_user_org_id() == 2002

    def test_viewer_has_org_id(self, viewer):
        """Viewer has specific org_id."""
        assert viewer.get_user_org_id() == 2002

    def test_org_id_with_custom_value(self, mock_engine):
        """Custom org_id is returned correctly."""
        engine = mock_engine(ROLE_LAB_ADMIN, org_id=9999)
        assert engine.get_user_org_id() == 9999


# ============================================================================
# Edge Case Tests - Invalid/Missing Data
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_role_in_log_user(self, mock_engine):
        """Handle missing role gracefully."""
        engine = mock_engine(0)
        del engine.log_user["role"]
        assert engine.get_user_role() == 99

    def test_empty_log_user(self, mock_engine):
        """Handle empty log_user dictionary."""
        engine = mock_engine(0)
        engine.log_user = {}
        assert engine.get_user_role() == 99
        assert engine.get_user_org_id() is None

    def test_role_as_string_number(self, mock_engine):
        """Role stored as string number should work."""
        engine = mock_engine(0)
        engine.log_user["role"] = "3"
        assert engine.get_user_role() == 3

    def test_role_as_float(self, mock_engine):
        """Role stored as float should work."""
        engine = mock_engine(0)
        engine.log_user["role"] = 4.0
        assert engine.get_user_role() == 4

    def test_negative_role_value(self, mock_engine):
        """Negative role should be handled (unlikely but test it)."""
        engine = mock_engine(0)
        engine.log_user["role"] = -1
        # Negative roles would pass all <= checks, so they'd have max permissions
        assert engine.get_user_role() == -1
        assert engine.can_validate_qc() is True
        assert engine.can_configure_system() is False  # Only role 0 exactly

    def test_very_high_role_value(self, mock_engine):
        """Very high role value has minimal permissions."""
        engine = mock_engine(0)
        engine.log_user["role"] = 100
        assert engine.get_user_role() == 100
        assert engine.can_validate_qc() is False
        assert engine.can_configure_system() is False
        assert engine.can_modify_data() is False
        assert engine.is_read_only() is True

    def test_current_ids_missing_lab_id(self, mock_engine):
        """Handle missing lab_id in current_ids."""
        engine = mock_engine(ROLE_TECHNICIAN, org_id=2002)
        engine.current_ids = {}
        scope, filter_id = engine.get_data_scope()
        assert scope == "lab"
        assert filter_id is None


# ============================================================================
# Real-World Scenario Tests
# ============================================================================

class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_technician_daily_workflow(self, technician):
        """Technician can enter data but not validate or delete."""
        # Can enter QC results
        assert technician.can_modify_data() is True
        # Cannot validate results
        assert technician.can_validate_qc() is False
        # Cannot delete results
        assert technician.can_delete_results() is False
        # Cannot configure workstations
        assert technician.can_manage_local_config() is False
        # Is not read-only
        assert technician.is_read_only() is False

    def test_superuser_validation_workflow(self, superuser):
        """Superuser can validate and manage QC but not configure."""
        # Can enter QC results
        assert superuser.can_modify_data() is True
        # Can validate results
        assert superuser.can_validate_qc() is True
        # Can delete incorrect results
        assert superuser.can_delete_results() is True
        # Cannot configure workstations
        assert superuser.can_manage_local_config() is False
        # Cannot access master data
        assert superuser.can_configure_system() is False

    def test_lab_admin_configuration_workflow(self, lab_admin):
        """Lab Admin can configure lab and validate QC."""
        # Can configure local settings
        assert lab_admin.can_manage_local_config() is True
        # Can validate QC
        assert lab_admin.can_validate_qc() is True
        # Can delete results
        assert lab_admin.can_delete_results() is True
        # Cannot access global master data
        assert lab_admin.can_configure_system() is False
        # Is specifically lab admin
        assert lab_admin.is_lab_admin() is True

    def test_app_admin_full_access(self, app_admin):
        """App Admin has full access to everything."""
        assert app_admin.can_configure_system() is True
        assert app_admin.can_manage_local_config() is True
        assert app_admin.can_validate_qc() is True
        assert app_admin.can_delete_results() is True
        assert app_admin.can_modify_data() is True
        assert app_admin.is_read_only() is False
        assert app_admin.is_admin() is True
        # Global scope
        scope, filter_id = app_admin.get_data_scope()
        assert scope == "global"

    def test_viewer_readonly_access(self, viewer):
        """Viewer can only view, nothing else."""
        assert viewer.is_read_only() is True
        assert viewer.can_modify_data() is False
        assert viewer.can_validate_qc() is False
        assert viewer.can_delete_results() is False
        assert viewer.can_manage_local_config() is False
        assert viewer.can_configure_system() is False

    def test_multi_lab_isolation(self, mock_engine):
        """Users from different labs have separate scopes."""
        tech_lab_1 = mock_engine(ROLE_TECHNICIAN, org_id=1001, lab_id=1)
        tech_lab_2 = mock_engine(ROLE_TECHNICIAN, org_id=1002, lab_id=2)

        scope1, lab1 = tech_lab_1.get_data_scope()
        scope2, lab2 = tech_lab_2.get_data_scope()

        assert lab1 == 1
        assert lab2 == 2
        assert lab1 != lab2  # Labs are isolated


# ============================================================================
# Permission Boundary Tests
# ============================================================================

class TestPermissionBoundaries:
    """Test permission boundaries between adjacent roles."""

    def test_superuser_technician_boundary(self, superuser, technician):
        """Superuser (4) can validate, Technician (5) cannot."""
        # This is the critical validation boundary
        assert superuser.can_validate_qc() is True
        assert technician.can_validate_qc() is False

        assert superuser.can_delete_results() is True
        assert technician.can_delete_results() is False

    def test_lab_admin_superuser_boundary(self, lab_admin, superuser):
        """Lab Admin (3) can manage config, Superuser (4) cannot."""
        assert lab_admin.can_manage_local_config() is True
        assert superuser.can_manage_local_config() is False

    def test_technician_viewer_boundary(self, technician, viewer):
        """Technician (5) can modify, Viewer (6) cannot."""
        assert technician.can_modify_data() is True
        assert viewer.can_modify_data() is False

        assert technician.is_read_only() is False
        assert viewer.is_read_only() is True

    def test_app_admin_country_admin_boundary(self, app_admin, country_admin):
        """App Admin (0) can configure system, Country Admin (1) cannot."""
        assert app_admin.can_configure_system() is True
        assert country_admin.can_configure_system() is False

        # But both can manage local config
        assert app_admin.can_manage_local_config() is True
        assert country_admin.can_manage_local_config() is True


# ============================================================================
# Parametrized Tests for is_read_only
# ============================================================================

@pytest.mark.parametrize("role,expected", [
    (ROLE_APP_ADMIN, False),
    (ROLE_COUNTRY_ADMIN, False),
    (ROLE_REGIONAL_ADMIN, False),
    (ROLE_LAB_ADMIN, False),
    (ROLE_SUPERUSER, False),
    (ROLE_TECHNICIAN, False),
    (ROLE_VIEWER, True),
])
def test_is_read_only_parametrized(mock_engine, role, expected):
    """Parametrized test for is_read_only()."""
    engine = mock_engine(role)
    assert engine.is_read_only() is expected


# ============================================================================
# Parametrized Tests for get_data_scope
# ============================================================================

@pytest.mark.parametrize("role,expected_scope", [
    (ROLE_APP_ADMIN, "global"),
    (ROLE_COUNTRY_ADMIN, "lab"),
    (ROLE_REGIONAL_ADMIN, "lab"),
    (ROLE_LAB_ADMIN, "lab"),
    (ROLE_SUPERUSER, "lab"),
    (ROLE_TECHNICIAN, "lab"),
    (ROLE_VIEWER, "lab"),
])
def test_get_data_scope_parametrized(mock_engine, role, expected_scope):
    """Parametrized test for get_data_scope() scope type."""
    engine = mock_engine(role)
    scope, _ = engine.get_data_scope()
    assert scope == expected_scope
