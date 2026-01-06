# Contributing to Biovarase

Thank you for your interest in contributing to Biovarase! This document provides guidelines and instructions for contributing to this medical laboratory QC management system.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Communication Guidelines](#communication-guidelines)
- [Documentation](#documentation)
- [Code Review Criteria](#code-review-criteria)
- [Important References](#important-references)

---

## Code of Conduct

### Our Commitment

Biovarase is a **production medical system** used in active medical laboratories. Code quality, data integrity, and patient safety are paramount.

### Core Principles

1. **Patient Safety First** - QC data impacts patient care decisions
2. **Data Integrity** - Never compromise database consistency
3. **Backward Compatibility** - Changes must not break existing installations
4. **ISO 15189:2022 Compliance** - Follow medical laboratory standards
5. **Test Coverage** - All critical code must have automated tests

---

## Getting Started

### Prerequisites

- **Python**: 3.7 or higher
- **MariaDB**: 10.3 or higher
- **OS**: Linux (tested on Debian/Ubuntu) or Windows 10/11
- **Git**: For version control

### Clone and Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd biovarase
   ```

2. **Add upstream remote (if working on a fork):**
   ```bash
   git remote add upstream <upstream-repository-url>
   ```

### Development Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install development tools:**
   ```bash
   pip install pytest pytest-cov pylint
   ```

4. **Setup database:**
   ```bash
   mysql -u root -p < biovarase.sql
   ```

5. **Run tests to verify setup:**
   ```bash
   pytest tests/ -v
   ```

   Expected: `89 passed` (100% pass rate)

---

## Development Workflow

### Branch Strategy

1. **Create feature branch from main:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Branch naming conventions:**
   - `feature/` - New features (e.g., `feature/add-sigma-metrics`)
   - `fix/` - Bug fixes (e.g., `fix/westgard-1-3s-boundary`)
   - `docs/` - Documentation updates (e.g., `docs/update-testing-guide`)
   - `refactor/` - Code refactoring (e.g., `refactor/extract-qc-mixin`)
   - `test/` - Test additions (e.g., `test/add-bias-edge-cases`)

### Commit Messages

**Format:** English, imperative mood, clear and descriptive

**Good examples:**
```
Add measurement uncertainty calculation per ISO/TS 20914

Fix 1:3S Westgard rule boundary condition
- Exactly 3SD should trigger 1:2S, not 1:3S
- Implementation uses > not >= for comparison

Update TESTING.md with parametrized test examples

Refactor QC.get_mean() to handle empty series
```

**Bad examples:**
```
Updated stuff          # Too vague
Fixed bug              # Not descriptive
WIP                    # Never commit WIP
aggiornato file        # Wrong language (must be English)
```

### Commit Best Practices

- **One logical change per commit**
- **Run tests before committing:** `pytest tests/ -v`
- **Keep commits atomic** - each should be a working state
- **Reference issue numbers** if applicable: `Fix #42: Handle zero SD in CV calculation`

---

## Code Standards

### Language Policy

**CRITICAL - Strictly enforced:**

- ✅ **Code**: English (variables, functions, comments, docstrings, commits)
- ✅ **Communication**: Italian (discussions, issue descriptions, PR descriptions)

**Example:**
```python
# ✅ CORRECT
def calculate_bias(avg: float, target: float) -> float:
    """
    Calculate bias percentage between average and target.

    Args:
        avg: Mean value from QC results
        target: Expected target value

    Returns:
        Bias percentage
    """
    if target == 0:
        return 0.0
    return ((avg - target) / target) * 100

# ❌ WRONG - Italian in code
def calcola_bias(media: float, obiettivo: float) -> float:
    """Calcola la percentuale di bias."""  # Italian docstring
    pass
```

### Python Style Guide (PEP 8)

**Indentation:** 4 spaces (no tabs)

**Line length:** 100 characters maximum

**Encoding:** UTF-8 with BOM
```python
# -*- coding: utf-8 -*-
```

**Naming conventions:**
- Classes: `PascalCase` (e.g., `QualityControl`)
- Functions/methods: `snake_case` (e.g., `get_mean`, `calculate_sigma`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RESULTS`, `DEFAULT_ZSCORE`)
- Private: `_leading_underscore` (e.g., `_validate_input`)

### Type Hints (Required for New Code)

```python
from typing import List, Dict, Optional, Tuple, Any

def get_westgard_violation_rule(
    self,
    target: float,
    sd: float,
    series: List[float]
) -> str:
    """Evaluate QC series against Westgard multirule algorithm."""
    pass
```

### Docstrings (Required for All Public Methods)

**Format:** Google-style docstrings in English

```python
def get_bias(self, avg: float, target: float) -> float:
    """
    Calculate bias percentage between average and target value.

    Bias represents systematic error in QC results per ISO 15189:2022.

    Args:
        avg: Mean value calculated from QC results
        target: Expected target value for the QC material

    Returns:
        Bias percentage. Returns 0.0 if target is zero (avoid division by zero).

    Raises:
        TypeError: If avg or target are not numeric types

    Example:
        >>> qc = QC()
        >>> qc.get_bias(105.0, 100.0)
        5.0
    """
    pass
```

### Comments

**Explain WHY, not WHAT:**

```python
# ✅ GOOD - Explains reasoning
# Use ddof=1 for sample SD (unbiased estimator per ISO 15189)
stdev = statistics.stdev(values, ddof=1)

# ✅ GOOD - Explains non-obvious logic
# Check 1:3S before 2:2S - rule evaluation order matters per Westgard
if abs(z_score) > 3:
    return "1:3S"

# ❌ BAD - Restates code mechanically
# Calculate standard deviation
stdev = statistics.stdev(values)

# ❌ BAD - Obvious from code
# Loop through results
for result in results:
    pass
```

### Database Access Rules

**MANDATORY patterns - strictly enforced:**

```python
# ✅ CORRECT - Dictionary access, parameterized query
rows = self.engine.read(True, "SELECT * FROM tests WHERE enable = ?", (1,))
for row in rows:
    print(row["description"])  # Dictionary key access

# ✅ CORRECT - Parameterized INSERT
new_id = self.engine.write(
    True,
    "INSERT INTO batches (control_id, target, sd) VALUES (?, ?, ?)",
    (control_id, target, sd)
)

# ❌ FORBIDDEN - Positional indexing
print(row[0])  # NEVER use positional indexing

# ❌ FORBIDDEN - String concatenation (SQL injection risk!)
sql = f"SELECT * FROM tests WHERE id = {test_id}"
rows = self.engine.read(True, sql)
```

### Error Handling

**All exceptions must be logged:**

```python
import inspect
import sys

try:
    # database operation
    result = self.engine.write(True, sql, args)
except Exception as e:
    self.on_log(
        inspect.stack()[0][3],      # function name
        sys.exc_info()[1],           # exception value
        sys.exc_info()[0],           # exception type
        sys.modules[__name__]        # module
    )
    raise  # Re-raise after logging
```

**Never use bare except:**
```python
# ❌ FORBIDDEN
try:
    something()
except:  # Catches ALL exceptions, including KeyboardInterrupt
    pass

# ✅ CORRECT
try:
    something()
except ValueError as e:
    self.on_log(...)
    return default_value
```

---

## Testing Requirements

### Test Coverage Requirements

**All new code must have tests**, especially:
- QC statistical calculations
- Westgard rule implementations
- Security features (encryption, password hashing)
- Database operations

**Current coverage:**
- Critical modules (qc.py, westgards.py, frames/security.py): **100%** ✅
- Overall project target: **≥80%**

### Running Tests

**Before committing, all tests must pass:**

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_qc.py -v

# Run by marker (critical tests only)
pytest -m critical -v

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term
```

**Expected output:** `89 passed` (100% pass rate)

### Writing New Tests

**1. Create test file in tests/ directory:**

```python
"""
Test suite for NewFeature functionality.

Tests cover XYZ according to ISO 15189:2022.
"""
import pytest
from module import NewFeature


@pytest.mark.unit
@pytest.mark.qc
class TestNewFeature:
    """Test NewFeature methods."""

    def setup_method(self):
        """Setup before each test method."""
        self.feature = NewFeature()

    def test_method_with_normal_input(self):
        """Test method with normal input values."""
        # Arrange
        input_value = 100.0
        expected = 200.0

        # Act
        result = self.feature.method(input_value)

        # Assert
        assert result == pytest.approx(expected, abs=0.01), \
            f"Expected {expected}, got {result}"

    def test_method_with_empty_input_returns_zero(self):
        """Test method with empty input returns zero."""
        result = self.feature.method([])
        assert result == 0.0, "Empty input should return 0.0"
```

**2. Use pytest markers:**
- `@pytest.mark.critical` - Critical for medical safety
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.qc` - QC statistical tests
- `@pytest.mark.westgard` - Westgard rule tests
- `@pytest.mark.unit` - Unit tests (no external dependencies)

**3. Follow AAA pattern:**
- **Arrange** - Setup test data
- **Act** - Execute function under test
- **Assert** - Verify result

**4. Test edge cases:**
- Empty inputs
- None/null values
- Zero values
- Negative values
- Boundary conditions
- Very large values

**For detailed testing guidelines, see:** [TESTING.md](./TESTING.md)

---

## Pull Request Process

### Before Submitting PR

**Complete this checklist:**

- [ ] All tests pass locally (`pytest tests/ -v`)
- [ ] New features have corresponding tests
- [ ] Test coverage ≥80% for new code
- [ ] Code follows PEP 8 style guide
- [ ] Docstrings added for all public methods
- [ ] Comments explain WHY, not WHAT
- [ ] No bare exceptions (`except:`)
- [ ] Database queries use parameterized statements
- [ ] Dictionary access only (no `row[0]`)
- [ ] Commit messages are clear and in English
- [ ] Documentation updated (if needed)
- [ ] No security vulnerabilities introduced
- [ ] Backward compatibility maintained

### Submitting Changes

**1. Push your branch:**
```bash
git push origin feature/your-feature-name
```

**2. Create Merge/Pull Request on your version control platform**

**3. Change Request Description (Italian):**

```markdown
## Descrizione

Breve descrizione delle modifiche (1-2 frasi).

## Tipo di modifica

- [ ] Bug fix (modifica non-breaking che risolve un issue)
- [ ] Nuova funzionalità (modifica non-breaking che aggiunge funzionalità)
- [ ] Breaking change (fix o feature che causerebbe malfunzionamenti alle funzionalità esistenti)
- [ ] Documentazione

## Motivazione e contesto

Perché questa modifica è necessaria? Quale problema risolve?
Riferimento issue: #numero_issue (se applicabile)

## Come è stato testato?

- [ ] Test suite esistente passa (89/89)
- [ ] Aggiunti nuovi test per la funzionalità
- [ ] Test manuali eseguiti (descrivere)

## Checklist

- [ ] Il codice segue le linee guida PEP 8
- [ ] Ho commentato il codice dove necessario (in inglese)
- [ ] Ho aggiornato la documentazione di conseguenza
- [ ] Le mie modifiche non generano nuovi warning
- [ ] Ho aggiunto test che dimostrano che il mio fix/feature funziona
- [ ] Tutti i test (nuovi ed esistenti) passano
- [ ] Ho verificato la retrocompatibilità

## Screenshot (se applicabile)

[Aggiungi screenshot per modifiche UI]
```

### PR Review Process

**Reviewers will check:**
1. Code quality and style compliance
2. Test coverage and test quality
3. Documentation completeness
4. Backward compatibility
5. Security considerations
6. Database integrity
7. ISO 15189:2022 compliance (for QC features)

**Be responsive to feedback** - Reviews may require changes before merge.

---

## Issue Reporting

### Bug Reports

**Use this template:**

```markdown
**Descrizione del bug**
Descrizione chiara e concisa del bug.

**Per riprodurre**
Passi per riprodurre il comportamento:
1. Vai a '...'
2. Clicca su '...'
3. Scrolla fino a '...'
4. Vedi errore

**Comportamento atteso**
Descrizione chiara di cosa ti aspettavi che succedesse.

**Screenshot**
Se applicabile, aggiungi screenshot per spiegare il problema.

**Ambiente (completa le seguenti informazioni):**
 - OS: [es. Linux Ubuntu 22.04, Windows 11]
 - Python Version: [es. 3.11.2]
 - MariaDB Version: [es. 10.11.3]
 - Biovarase Version: [es. 4.2]

**Log di errore**
Contenuto del file `log.txt` (se rilevante)

**Contesto aggiuntivo**
Qualsiasi altra informazione sul problema.
```

### Feature Requests

**Use this template:**

```markdown
**La tua richiesta è correlata a un problema? Descrivi.**
Descrizione chiara e concisa del problema. Es. Sono sempre frustrato quando [...]

**Descrivi la soluzione che vorresti**
Descrizione chiara e concisa di cosa vorresti che succedesse.

**Descrivi alternative che hai considerato**
Descrizione chiara e concisa di soluzioni o feature alternative che hai considerato.

**Conformità agli standard**
Questa feature è richiesta da ISO 15189:2022 o altri standard? Specificare.

**Contesto aggiuntivo**
Aggiungi qualsiasi altro contesto o screenshot sulla feature request.
```

---

## Communication Guidelines

### Discussion Language

**Italian** for:
- Issue descriptions
- PR descriptions
- Code review comments
- Questions and discussions

**English** for:
- Code (variables, functions, classes)
- Comments in code
- Docstrings
- Commit messages
- Technical documentation

### Respectful Communication

- Be constructive and respectful
- Focus on the code, not the person
- Assume good intentions
- Ask questions to clarify, don't assume
- Medical laboratory professionals may contribute - respect domain expertise

### Reporting Issues

For bugs, feature requests, or questions:
- Use the project's issue tracking system (if available)
- Contact the maintainer directly: giuseppecostanzi@gmail.com
- Follow the templates provided in the Issue Reporting section above

---

## Documentation

### When to Update Documentation

Update documentation when:
- Adding new features
- Changing existing behavior
- Adding new dependencies
- Modifying database schema
- Changing configuration options
- Adding new test categories

### Documentation Files

- **README.md** - Project overview, quick start, features
- **TESTING.md** - Test suite documentation and guidelines
- **CLAUDE.md** - Architecture and development guidelines
- **CONTRIBUTING.md** - This file
- **PROJECT_RULES.md** - Authoritative development rules
- **BEST_PRACTICES.md** - SOLID principles and design patterns

### Docstring Requirements

All public methods, classes, and modules must have docstrings:
- Clear description of purpose
- Args with types
- Returns with type
- Raises (exceptions)
- Example usage (for complex methods)

---

## Code Review Criteria

### What Reviewers Look For

**1. Correctness**
- Does the code do what it claims?
- Are edge cases handled?
- Is error handling appropriate?

**2. Testing**
- Are there adequate tests?
- Do tests cover edge cases?
- Do all tests pass?

**3. Code Quality**
- Is code readable and maintainable?
- Are variables/functions well-named?
- Is complexity reasonable?
- Are there code smells?

**4. Security**
- SQL injection prevention (parameterized queries)
- No hardcoded credentials
- Input validation where needed
- Proper error handling

**5. Standards Compliance**
- PEP 8 style guide
- Language policy (English code, Italian communication)
- ISO 15189:2022 (for QC features)
- Database access rules

**6. Documentation**
- Docstrings present and clear
- Comments explain WHY
- README/docs updated if needed

**7. Backward Compatibility**
- Existing functionality preserved
- Database schema changes handled properly
- Configuration changes documented

---

## Important References

### Project Documentation

- **[README.md](./README.md)** - Project overview and quick start
- **[TESTING.md](./TESTING.md)** - Comprehensive test suite guide
- **[CLAUDE.md](./CLAUDE.md)** - Architecture and development guidelines
- **[PROJECT_RULES.md](./PROJECT_RULES.md)** - Authoritative development rules
- **[BEST_PRACTICES.md](./BEST_PRACTICES.md)** - SOLID principles and patterns

### External Standards

- **ISO 15189:2022** - Medical laboratories - Requirements for quality and competence
- **ISO/TS 20914:2019** - Medical laboratories - Practical guidance for estimation of measurement uncertainty
- **Westgard QC Rules** - Statistical process control methodologies
- **PEP 8** - Python Style Guide
- **pytest Documentation** - https://docs.pytest.org/

### Tools and Libraries

- **Python**: https://www.python.org/
- **MariaDB**: https://mariadb.org/
- **pytest**: https://docs.pytest.org/
- **bcrypt**: https://github.com/pyca/bcrypt/
- **Tkinter**: https://docs.python.org/3/library/tkinter.html

---

## Questions?

If you have questions:

1. Check this documentation first
2. Review [CLAUDE.md](./CLAUDE.md) for architecture details
3. Check [TESTING.md](./TESTING.md) for test-related questions
4. Contact the maintainer: giuseppecostanzi@gmail.com

---

## Thank You!

Thank you for contributing to Biovarase! Your contributions help improve quality control in medical laboratories worldwide.

**Remember:**
- Patient safety depends on code quality
- Test everything thoroughly
- Follow standards strictly
- Communicate clearly
- Be respectful and constructive

**Made with ❤️ for Medical Laboratory Professionals**

*Ensuring analytical quality, one contribution at a time.*
