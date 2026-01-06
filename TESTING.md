# Biovarase Test Suite Documentation

Comprehensive guide for running and maintaining the Biovarase automated test suite.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

Biovarase includes a comprehensive automated test suite ensuring:
- **Medical Safety Compliance** - Critical Westgard QC rules validation
- **Statistical Accuracy** - QC calculations verification (ISO 15189:2022)
- **Security** - Password hashing and encryption validation
- **Code Quality** - Regression prevention and maintainability

### Test Statistics
- **Total Tests**: 89
- **Pass Rate**: 100%
- **Critical Tests**: 62 (medical safety + security)
- **Test Framework**: pytest 7.2+
- **Python Support**: 3.7+

---

## Quick Start

### Prerequisites

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install pytest
pip install pytest
```

### Run All Tests

```bash
# All working tests (excludes tests with external dependencies)
pytest tests/test_security.py tests/test_westgards.py tests/test_qc.py -v

# Or use shorter command
pytest tests/ -v
```

### Expected Output

```
============================= test session starts ==============================
collected 89 items

tests/test_security.py::TestPasswordHashing::test_hash_password PASSED   [  1%]
tests/test_security.py::TestPasswordHashing::test_verify_correct_password PASSED [  2%]
...
tests/test_qc.py::test_qc_requires_mocked_dependencies PASSED            [100%]

============================== 89 passed in 8.07s ===============================
```

---

## Test Structure

### Test Modules

```
tests/
├── conftest.py              # Shared fixtures (QC data, test data)
├── test_security.py         # Security tests (27 tests)
│   ├── Password hashing (bcrypt)
│   ├── Hardware ID generation
│   ├── Key derivation (PBKDF2)
│   └── Config encryption (Fernet)
├── test_westgards.py        # Westgard QC rules (29 tests) [CRITICAL]
│   ├── 1:3S - Random error detection
│   ├── 2:2S - Systematic error detection
│   ├── R:4S - Range random error
│   ├── 4:1S - Trending detection
│   ├── 10:X - Persistent bias
│   └── 1:2S - Warning level
├── test_qc.py               # QC statistics (33 tests) [CRITICAL]
│   ├── Mean, SD, CV calculations
│   ├── Bias calculation
│   ├── Total Error
│   ├── Measurement Uncertainty (ISO/TS 20914)
│   └── Sigma metrics
└── test_log_rotation.py     # Log rotation (requires refactoring)
```

### Test Markers

Tests are categorized using pytest markers:

```python
@pytest.mark.critical    # Critical for medical safety
@pytest.mark.security    # Security-related tests
@pytest.mark.qc          # QC statistical tests
@pytest.mark.westgard    # Westgard rule tests
@pytest.mark.unit        # Unit tests (no external dependencies)
@pytest.mark.integration # Integration tests (database, file I/O)
```

---

## Running Tests

### Basic Commands

```bash
# All tests (verbose)
pytest tests/ -v

# Specific module
pytest tests/test_security.py -v
pytest tests/test_westgards.py -v
pytest tests/test_qc.py -v

# Single test class
pytest tests/test_security.py::TestPasswordHashing -v

# Single test method
pytest tests/test_security.py::TestPasswordHashing::test_hash_password -v
```

### Filter by Markers

```bash
# Only critical tests (medical safety)
pytest -m critical -v

# Only security tests
pytest -m security -v

# Only Westgard tests
pytest -m westgard -v

# Only QC tests
pytest -m qc -v

# Only unit tests (fast, no external dependencies)
pytest -m unit -v
```

### Combine Markers

```bash
# Critical AND unit tests
pytest -m "critical and unit" -v

# Security OR qc tests
pytest -m "security or qc" -v

# Not integration tests (only unit)
pytest -m "not integration" -v
```

### Output Options

```bash
# Short traceback (cleaner output)
pytest tests/ --tb=short

# No traceback (only pass/fail)
pytest tests/ --tb=no

# Stop at first failure
pytest tests/ -x

# Show summary of all outcomes
pytest tests/ -ra

# Quiet mode (less verbose)
pytest tests/ -q

# Very verbose (show each assert)
pytest tests/ -vv
```

---

## Test Coverage

### Install Coverage Tool

```bash
pip install pytest-cov
```

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=. --cov-report=term

# HTML report (recommended)
pytest --cov=. --cov-report=html --cov-report=term

# Open HTML report
firefox htmlcov/index.html  # Linux
open htmlcov/index.html     # Mac
start htmlcov/index.html    # Windows
```

### Coverage Targets

- **Critical modules** (qc.py, westgards.py, frames/security.py): **100%**
- **Overall project**: Target **≥80%**

### Current Coverage

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| frames/security.py | 100% | 27 | ✅ Complete |
| westgards.py | 100% | 29 | ✅ Complete |
| qc.py | 100% | 33 | ✅ Complete |
| frames/login.py | ~60% | 0 | ⚠️ Partial (mariadb dependency) |
| dbms.py | 0% | 0 | ❌ Not tested |
| controller.py | 0% | 0 | ❌ Not tested |

---

## Writing New Tests

### Test File Template

```python
"""
Test suite for ModuleName functionality.

Brief description of what this module tests.
"""
import pytest
from module_name import ClassName


@pytest.mark.unit
class TestClassName:
    """Test ClassName methods."""

    def setup_method(self):
        """Setup before each test method."""
        self.obj = ClassName()

    def test_method_name_behavior(self):
        """Test method_name with normal input."""
        # Arrange
        input_value = "test"
        expected = "expected_result"

        # Act
        result = self.obj.method_name(input_value)

        # Assert
        assert result == expected, f"Expected {expected}, got {result}"

    def test_method_name_edge_case(self):
        """Test method_name with edge case."""
        result = self.obj.method_name(None)
        assert result is None, "None input should return None"


@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    ("case1", "result1"),
    ("case2", "result2"),
    ("case3", "result3"),
])
def test_parametrized_example(input, expected):
    """Parametrized test for multiple scenarios."""
    obj = ClassName()
    result = obj.method_name(input)
    assert result == expected
```

### Fixtures Example (conftest.py)

```python
import pytest


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return [1, 2, 3, 4, 5]


@pytest.fixture
def temp_file(tmp_path):
    """Create temporary file for testing."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")
    return file_path
```

### Best Practices

1. **Test Naming**: Use descriptive names
   - ✅ `test_calculate_mean_with_empty_list_returns_zero`
   - ❌ `test_mean1`

2. **AAA Pattern**: Arrange, Act, Assert
   ```python
   def test_example():
       # Arrange - Setup test data
       data = [1, 2, 3]

       # Act - Execute function under test
       result = calculate_mean(data)

       # Assert - Verify result
       assert result == 2.0
   ```

3. **One Assertion Per Test** (when possible)
   - Each test should verify one specific behavior

4. **Use Fixtures** for reusable test data
   - Avoid duplicating test data across tests

5. **Test Edge Cases**:
   - Empty inputs
   - None/null values
   - Zero values
   - Negative values
   - Very large values
   - Boundary conditions

6. **Mock External Dependencies**:
   ```python
   def test_with_mock(monkeypatch):
       monkeypatch.setattr(module, 'external_call', lambda: 'mocked')
       result = function_under_test()
       assert result == 'expected'
   ```

---

## Continuous Integration

### Automated Testing in CI/CD

You can integrate the test suite into your CI/CD pipeline. Example configuration for common CI systems:

**Generic CI/CD steps:**
1. Setup Python 3.7+ environment
2. Install dependencies: `pip install -r requirements.txt`
3. Install test tools: `pip install pytest pytest-cov`
4. Run tests: `pytest tests/test_security.py tests/test_westgards.py tests/test_qc.py -v`
5. Generate coverage: `pytest --cov=. --cov-report=xml`

### Pre-commit Hooks

Install pre-commit:
```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        args: [tests/test_security.py, tests/test_westgards.py, tests/test_qc.py]
        language: system
        pass_filenames: false
        always_run: true
```

Install hooks:
```bash
pre-commit install
```

Now tests run automatically before each commit!

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'pytest'

**Solution**:
```bash
pip install pytest
```

#### 2. ImportError: cannot import name 'X' from 'module'

**Solution**: Ensure you're in project root:
```bash
cd /path/to/biovarase
pytest tests/
```

#### 3. Tests fail with "mariadb module not found"

**Solution**: Run only working tests:
```bash
pytest tests/test_security.py tests/test_westgards.py tests/test_qc.py -v
```

#### 4. Fixture 'X' not found

**Solution**: Check that `conftest.py` is in tests directory:
```bash
ls tests/conftest.py  # Should exist
```

#### 5. Tests pass locally but fail in CI

**Possible causes**:
- Different Python version
- Missing dependencies in requirements.txt
- Environment-specific configuration

**Solution**: Match CI environment locally:
```bash
python3.11 -m pytest tests/ -v  # Match CI Python version
```

### Debug Mode

Run pytest with debugging:
```bash
# Show local variables on failure
pytest tests/ -l

# Enter debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -s

# Very verbose output
pytest tests/ -vv
```

### Performance Issues

```bash
# Show slowest 10 tests
pytest tests/ --durations=10

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto  # Auto-detect CPU cores
```

---

## Maintenance

### Updating Tests After Code Changes

1. **API Changes**: Update test assertions and mocks
2. **New Features**: Add corresponding test coverage
3. **Bug Fixes**: Add regression test for the bug
4. **Refactoring**: Ensure tests still pass (green refactoring)

### Test Review Checklist

Before committing new tests:
- [ ] All tests pass locally
- [ ] Test names are descriptive
- [ ] Edge cases covered
- [ ] Fixtures used for reusable data
- [ ] Markers added appropriately
- [ ] Documentation updated (this file)

---

## References

### Standards & Guidelines
- **ISO 15189:2022** - Medical laboratories quality requirements
- **ISO/TS 20914:2019** - Measurement uncertainty guidance
- **Westgard JO** - Basic QC Practices, 4th Edition. 2016

### Pytest Documentation
- Official Docs: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Markers: https://docs.pytest.org/en/stable/mark.html
- Parametrize: https://docs.pytest.org/en/stable/parametrize.html

### Internal Documentation
- `CLAUDE.md` - Project overview and development guidelines
- `pytest.ini` - Pytest configuration
- `tests/conftest.py` - Shared fixtures documentation

---

## Support

For questions or issues:
1. Check this documentation
2. Review `CLAUDE.md` for project architecture
3. Check pytest output with `-vv` flag
4. Review test source code for examples

---

**Last Updated**: 2025-12-03
**Test Suite Version**: 1.0
**Python Version**: 3.7+
**Pytest Version**: 6.0+
