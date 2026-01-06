# Biovarase

**Professional Quality Control Management System for Medical Laboratories**

Biovarase is a comprehensive QC (Quality Control) management application designed for medical laboratories, implementing ISO 15189:2022 standards and Westgard multirule algorithms for analytical quality monitoring.

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-89%20passed-brightgreen)](./TESTING.md)
[![License](https://img.shields.io/badge/license-GNU%20GPL%20v3-blue)](./LICENSE)

---

## 🎯 Features

### Core Functionality
- **Westgard Multirule QC** - Statistical process control (1:3S, 2:2S, R:4S, 4:1S, 10:X)
- **QC Statistical Analysis** - Mean, SD, CV%, Bias, Total Error, Sigma metrics
- **Measurement Uncertainty** - ISO/TS 20914:2019 compliant calculations
- **Levey-Jennings Charts** - Visual QC trending and analysis
- **Batch Management** - QC material tracking and expiry monitoring

### Security & Compliance
- **Hardware-Locked Encryption** - AES-256-GCM config encryption tied to machine
- **Bcrypt Password Hashing** - Cost factor 12 for secure authentication
- **Role-Based Access Control** - Admin, Superuser, Technician, Viewer roles
- **Audit Logging** - Complete activity tracking
- **ISO 15189:2022 Compliance** - Medical laboratory quality standards

### Technical Features
- **Cross-Platform** - Linux and Windows 10/11 support
- **MariaDB Backend** - Robust relational database
- **Tkinter GUI** - Native desktop interface
- **Automated Testing** - 89 tests with 100% pass rate
- **Log Rotation** - Automatic log management (10MB limit, 5 file retention)

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.7 or higher
- **MariaDB**: 10.3 or higher
- **OS**: Linux (tested on Debian/Ubuntu) or Windows 10/11

### Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd biovarase
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Database**
   ```bash
   # Import database schema
   mysql -u root -p < biovarase.sql
   ```

5. **First Run**
   ```bash
   python3 frames/login.py
   ```

   On first run, the Setup Wizard will guide you through:
   - Database connection configuration
   - Admin user creation
   - Hardware-locked encryption setup

### Default Credentials

After initial setup, use the credentials you created during the wizard.

**Generic Viewer Account** (autologin):
- Username: `viewer`
- Password: `viewer`
- Role: Read-only access

---

## 🧪 Testing

Biovarase includes a comprehensive automated test suite with **89 tests** covering critical functionality.

### Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Install pytest
pip install pytest

# Run all tests
pytest tests/test_security.py tests/test_westgards.py tests/test_qc.py -v
```

### Test Coverage

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| Security (encryption, hashing) | 27 | 100% | ✅ |
| Westgard Rules (medical safety) | 29 | 100% | ✅ |
| QC Statistics (ISO 15189) | 33 | 100% | ✅ |
| **Total** | **89** | **100%** | ✅ |

For detailed testing documentation, see **[TESTING.md](./TESTING.md)**.

---

## 📖 Usage

### Launching the Application

```bash
# Standard launch
python3 frames/login.py

# With autologin (viewer account)
python3 frames/login.py --autologin
```

### Basic Workflow

1. **Login** - Authenticate with user credentials
2. **Select Site/Lab/Section** - Choose your working context
3. **Manage Batches** - Create/edit QC material batches
4. **Enter Results** - Input QC measurements
5. **Review QC Charts** - Analyze Levey-Jennings plots
6. **Validate Results** - Apply Westgard rules for run acceptance
7. **Generate Reports** - Export QC data and statistics

### User Roles

- **Admin (role=0)**: Full system access, configuration
- **Superuser (role=1)**: QC validation, data management
- **Technician (role=2)**: Data entry, result viewing
- **Viewer (role=3)**: Read-only access (autologin)

---

## 🏗️ Architecture

### Technology Stack

- **Language**: Python 3.7+
- **GUI Framework**: Tkinter (ttk themed widgets)
- **Database**: MariaDB 10.3+ (via mariadb connector)
- **Encryption**: Fernet (AES-128-CBC + HMAC-SHA256)
- **Password Hashing**: bcrypt (cost factor 12)
- **Testing**: pytest 6.0+

### Design Pattern

Biovarase uses a **Mixin Architecture** pattern:

```python
class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Launcher, Tools):
    """Main application engine combining all functionality via mixins."""
    pass
```

**Mixin Responsibilities**:
- `DBMS`: Database connection and query execution
- `Controller`: SQL builders and domain logic
- `QC`: Statistical calculations (mean, SD, CV, bias, etc.)
- `Westgards`: Westgard multirule algorithms
- `Exporter`: Data export functionality
- `Importer`: Data import functionality
- `Launcher`: Window management
- `Tools`: GUI utilities and helpers

For detailed architecture documentation, see **[CLAUDE.md](./CLAUDE.md)**.

---

## 📊 Standards Compliance

Biovarase implements the following international standards:

- **ISO 15189:2022** - Medical laboratories - Requirements for quality and competence
- **ISO/TS 20914:2019** - Medical laboratories - Practical guidance for estimation of measurement uncertainty
- **Westgard Multirule QC** - Statistical process control per Westgard JO. Basic QC Practices, 4th Edition. 2016

---

## 🔒 Security

### Encryption

- **Hardware-Locked Configuration**: Config files encrypted with hardware-specific key (MAC + machine-id)
- **Algorithm**: Fernet (AES-128-CBC + HMAC-SHA256)
- **Key Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations)
- **Non-Transferable**: Encrypted config only works on the machine that created it

### Password Security

- **Hashing**: bcrypt with cost factor 12
- **Salt**: Automatic random salt per password
- **Timing Attack Protection**: bcrypt's constant-time comparison

### Database Security

- **Parameterized Queries**: All SQL queries use placeholders (SQL injection prevention)
- **Input Validation**: SQL identifier validation with regex patterns
- **Connection Timeout**: 5-second timeout for database connections

---

## 🛠️ Development

### Project Structure

```
biovarase/
├── frames/           # GUI windows and dialogs
│   ├── login.py      # Application entry point
│   ├── main.py       # Main application window
│   ├── security.py   # Encryption/decryption utilities
│   └── ...
├── tests/            # Automated test suite
│   ├── conftest.py   # Shared pytest fixtures
│   ├── test_security.py
│   ├── test_westgards.py
│   └── test_qc.py
├── engine.py         # Main Engine class (mixin orchestrator)
├── dbms.py           # Database connection and queries
├── controller.py     # SQL builders and domain logic
├── qc.py             # QC statistical calculations
├── westgards.py      # Westgard rule algorithms
├── tools.py          # GUI utilities
├── pytest.ini        # Test configuration
├── TESTING.md        # Test suite documentation
├── CLAUDE.md         # Development guidelines
└── README.md         # This file
```

### Building Executable

```bash
# Compile with Nuitka (single-file executable)
python3 -m nuitka --standalone --onefile --enable-plugin=tk-inter frames/login.py

# Output: login.bin (Linux) or login.exe (Windows)
```

### Coding Standards

- **Python Version**: 3.7+ (maintain backward compatibility)
- **Style**: Follow PEP 8
- **Docstrings**: English, Google-style format
- **Comments**: English only
- **Type Hints**: Preferred but not required (Python 3.7 compatible)
- **Testing**: Pytest with fixtures and markers

For detailed coding guidelines, see **[CLAUDE.md](./CLAUDE.md)**.

---

## 📝 Documentation

- **[TESTING.md](./TESTING.md)** - Comprehensive test suite guide
- **[CLAUDE.md](./CLAUDE.md)** - Project architecture and development rules
- **[LOG_ROTATION.md](./LOG_ROTATION.md)** - Log management documentation

---

## 🤝 Contributing

Contributions are welcome! Please:

1. **Clone** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write tests** for new functionality
4. **Ensure** all tests pass (`pytest tests/ -v`)
5. **Commit** changes (`git commit -m 'Add amazing feature'`)
6. **Push** to branch (`git push origin feature/amazing-feature`)
7. **Submit** your changes following the project's contribution guidelines

See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for detailed guidelines.

### Before Submitting

- [ ] All tests pass locally
- [ ] New features have corresponding tests
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if needed)
- [ ] No security vulnerabilities introduced

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.

See [LICENSE](./LICENSE) file for details.

---

## 👤 Author

**Giuseppe Costanzi (1966bc)**
- Email: giuseppecostanzi@gmail.com
- Project: Biovarase Professional Edition v4.2

---

## 🙏 Acknowledgments

- **Westgard QC** - For statistical process control methodologies
- **ISO/TC 212** - For medical laboratory standards
- **Python Community** - For excellent tools and libraries

---

## 📞 Support

For issues, questions, or feature requests:
1. Check **[TESTING.md](./TESTING.md)** for test-related issues
2. Review **[CLAUDE.md](./CLAUDE.md)** for architecture questions
3. Review **[CONTRIBUTING.md](./CONTRIBUTING.md)** for contribution guidelines
4. Contact: giuseppecostanzi@gmail.com

---

**Made with ❤️ for Medical Laboratory Professionals**

*Ensuring analytical quality, one QC result at a time.*
