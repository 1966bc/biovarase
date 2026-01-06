# Biovarase - Best Practices & Design Principles

**Read this at session start alongside PROJECT_RULES.md**

**Version:** 1.0  
**Date:** 2025-12-03  
**Status:** ACTIVE REFERENCE

---

## 🎯 Core Programming Principles

### 1. SOLID Principles

#### S - Single Responsibility Principle
**"A class should have one, and only one, reason to change."**

- Ogni classe/metodo fa UNA cosa sola
- `DBMS` → solo database access
- `Controller` → solo SQL building + domain logic  
- `Engine` → solo orchestrazione
- `GUI` → solo presentazione

**Esempio:**
```python
# ✅ GOOD - Single responsibility
class DBMS:
    """Handles ONLY database connections and queries."""
    def read(self, fetch, sql, args):
        """Execute SELECT query."""
        pass
    
    def write(self, sql, args):
        """Execute INSERT/UPDATE/DELETE."""
        pass

# ❌ BAD - Multiple responsibilities
class DBMS:
    """Database + GUI + Business logic all mixed."""
    def read_and_show_dialog(self, sql):  # ❌ Too many concerns
        result = self.execute(sql)
        messagebox.showinfo("Result", result)  # ❌ GUI in DB layer!
        return self.calculate_statistics(result)  # ❌ Business logic in DB layer!
```

#### O - Open/Closed Principle
**"Open for extension, closed for modification."**

- Aperto a estensione (nuovi mixin), chiuso a modifica (core stabile)
- Aggiungi features via mixin, non modificare Engine core

**Esempio:**
```python
# ✅ GOOD - Extend via mixin
class NewFeatureMixin:
    def new_feature(self):
        pass

class Engine(DBMS, Controller, NewFeatureMixin):  # Extended!
    pass

# ❌ BAD - Modify existing class
class Engine(DBMS, Controller):
    def existing_method(self):
        # ❌ Modified existing method to add feature
        original_code()
        new_feature_code()  # ❌ Breaking existing functionality
```

#### L - Liskov Substitution Principle
**"Subclasses should be substitutable for their base classes."**

- Eredità usata solo dove ha senso (DBMS → Controller → Engine)
- No monkey-patching, no override strani

#### I - Interface Segregation Principle  
**"Many client-specific interfaces are better than one general-purpose interface."**

- GUI non dipende da dettagli database
- Mixin specifici per funzionalità specifiche

#### D - Dependency Inversion Principle
**"Depend on abstractions, not concretions."**

- GUI dipende da Engine (abstraction)
- Engine non dipende mai da GUI

---

### 2. KISS - Keep It Simple, Stupid

**Significato:**
- La soluzione più semplice che funziona è la migliore
- Se serve documentazione estesa per capire il codice → troppo complesso
- **Test:** "Can I understand this in 6 months?"

**Esempi:**

✅ **GOOD:**
```python
def get_user_role(self) -> int:
    """Get current user's role. Simple and clear."""
    return int(self.log_user.get("role", 2))
```

❌ **BAD (over-engineering):**
```python
class RoleResolver:
    def __init__(self, user_context):
        self.context = user_context
        self.factory = RoleFactory()
    
    def resolve(self):
        role_strategy = self.factory.create_strategy(self.context)
        return role_strategy.get_role()

# ❌ 4 classes for a simple int lookup!
```

**Regola d'oro:** Se non sai spiegarlo in 2 frasi, probabilmente è troppo complesso.

---

### 3. DRY - Don't Repeat Yourself

**Significato:**
- Ogni pezzo di conoscenza deve avere una rappresentazione unica
- Copia-incolla codice = debito tecnico
- **"Single Source of Truth"**

**Esempi:**

✅ **GOOD - Column widths centralized:**
```python
class UI(tk.Toplevel):
    # Single source of truth
    COL_TEST_WIDTH = 40
    COL_CODE_WIDTH = 10
    COL_SPACING = 2

    def _format_label(self, row):
        test = row["test"][:self.COL_TEST_WIDTH]
        code = row["code"][:self.COL_CODE_WIDTH]
        spacing = " " * self.COL_SPACING
        return f"{test:<{self.COL_TEST_WIDTH}}{spacing}{code:<{self.COL_CODE_WIDTH}}"

    def _parse_label(self, raw):
        pos = 0
        test = raw[pos:pos + self.COL_TEST_WIDTH].strip()
        pos += self.COL_TEST_WIDTH + self.COL_SPACING
        code = raw[pos:pos + self.COL_CODE_WIDTH].strip()
        return {"test": test, "code": code}
```

❌ **BAD - Hardcoded repetition:**
```python
def _format_label(self, row):
    return f"{test:<40}  {code:<10}"  # ❌ Magic numbers

def _parse_label(self, raw):
    test = raw[0:40].strip()   # ❌ Hardcoded again
    code = raw[42:52].strip()  # ❌ Different spacing (42 vs 40+2)!
```

**Regola d'oro:** Se lo scrivi 2 volte, refactor. Se lo scrivi 3 volte, è un bug.

---

### 4. YAGNI - You Aren't Gonna Need It

**Significato:**
- Non implementare features "che potrebbero servire in futuro"
- Implementa solo ciò che serve ADESSO
- Refactor quando serve davvero

**Esempi:**

✅ **GOOD - Implement what's needed:**
```python
def import_qc_file_auto(self, filepath, received_ts, workstation_id):
    """Import QC file for Abbott integration (needed NOW)."""
    # Implementation for current requirement
    pass
```

❌ **BAD - Speculative features:**
```python
def import_qc_file_auto_with_ml_validation_and_blockchain_and_ai_and_cloud(
    self, filepath, ml_model, blockchain_node, ai_endpoint, cloud_provider, ...
):
    """
    Import QC with ML validation, blockchain audit trail, AI prediction,
    cloud sync, quantum encryption, and time travel capability.
    
    ❌ None of this is needed! We just need to import a CSV file!
    """
    pass
```

**Regola d'oro:** Se non c'è un requisito concreto OGGI, non implementarlo OGGI.

---

### 5. Separation of Concerns

**Significato:**
- Ogni modulo/classe si occupa di UN aspetto del sistema
- GUI non fa business logic
- Business logic non fa rendering  
- Database layer non fa validazione

**Architettura Biovarase:**
```
┌─────────────────┐
│   GUI (frames)  │ ← Solo presentazione, raccolta input
└────────┬────────┘
         │ usa
┌────────▼────────┐
│     Engine      │ ← Orchestrazione, coordinamento
└────────┬────────┘
         │ eredita
┌────────▼────────┐
│   Controller    │ ← Business logic, SQL building
└────────┬────────┘
         │ eredita
┌────────▼────────┐
│      DBMS       │ ← Solo database access
└─────────────────┘
```

**Esempi:**

✅ **GOOD - Separated concerns:**
```python
# GUI layer (frames/users.py)
def on_add(self):
    """Button handler - just open editor."""
    self._open_editor(index=None)

# Business logic (controller.py)
def validate_user_data(self, user_data):
    """Validate user data before insert."""
    if not user_data.get("nickname"):
        raise ValueError("Nickname required")
    return True

# Database layer (dbms.py)
def write(self, sql, args):
    """Execute INSERT/UPDATE/DELETE."""
    cursor.execute(sql, args)
```

❌ **BAD - Mixed concerns:**
```python
# ❌ Everything in GUI!
def on_add(self):
    # ❌ Validation in GUI
    if not self.txtNickname.get():
        messagebox.showerror("Error", "Nickname required")
        return
    
    # ❌ SQL building in GUI
    sql = f"INSERT INTO users VALUES ('{nickname}')"  # ❌ SQL injection!
    
    # ❌ Direct database access in GUI
    cursor = self.connection.cursor()
    cursor.execute(sql)
```

---

### 6. Fail Fast / Fail Safe

**Significato:**
- Rileva errori il prima possibile
- Non nascondere errori (no `except: pass` silenzioso)
- Log SEMPRE gli errori

**Esempi:**

✅ **GOOD - Fail fast with logging:**
```python
def load_data(self):
    try:
        result = self.engine.read(False, sql, args)
        if not result:
            raise ValueError("No data found for query")
        return result
    except Exception as exc:
        # Log the error
        self.engine.on_log("load_data", exc, type(exc), sys.modules[__name__])
        # Show user-friendly message
        messagebox.showerror("Error", f"Failed to load data: {exc}", parent=self)
        return None
```

❌ **BAD - Silent failures:**
```python
def load_data(self):
    try:
        result = self.engine.read(False, sql, args)
        return result
    except:
        pass  # ❌ Error hidden! Who will debug this?
    
    return None  # ❌ User has no idea what went wrong
```

**Regola d'oro:** Se qualcosa va male, DILLO SUBITO. Non fingere che va tutto bene.

---

### 7. Code for Readability

**Significato:**
- Il codice si scrive 1 volta, si legge 100 volte
- Nomi variabili/metodi autodocumentanti
- Commenti spiegano il "perché", non il "cosa"

**Esempi:**

✅ **GOOD - Self-documenting:**
```python
# Extract company name (may be None for legacy records without supplier)
company = (row.get("company") or "").strip()

# Only Admin/Superuser/Technician can change section
# Autologin users (role=3) are read-only guests
if role == 3:
    messagebox.showwarning("Permission Denied", "Read-only users cannot change section.")
    return
```

❌ **BAD - Cryptic:**
```python
c = r.get("c") or ""  # ❌ What is "c"?
c = c.strip()         # ❌ Why strip?

if r >= 3:  # ❌ Why 3? What does this mean?
    return
```

**Guidelines:**
- Variable names: `user_id` not `uid`, `company_name` not `cn`
- Method names: `get_user_role()` not `gur()`
- Constants: `ROLE_ADMIN = 0` not just `0` everywhere
- Comments: Explain "why" not "what"

---

## 🏗️ Architectural Patterns (Biovarase-specific)

### 1. Singleton Pattern (Master Windows)

**Quando usare:**
- Finestre master (list/tree view)
- Una sola istanza logica (main, batches, users, sites, etc.)

**Perché:**
- Evita duplicazione window state
- Garantisce single source of truth
- Migliore gestione risorse

**Come implementare:**
```python
class UI(tk.Toplevel):
    """Master window - Singleton pattern."""
    
    _instance = None
    
    def __new__(cls, parent):
        """Ensure only one instance exists."""
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    # Instance exists - bring to front
                    cls._instance.deiconify()
                    cls._instance.lift()
                    cls._instance.after_idle(cls._instance.focus_set)
                    return cls._instance
            except Exception:
                # Instance was destroyed - create new
                cls._instance = None
        
        # Create new instance
        obj = super().__new__(cls)
        cls._instance = obj
        return obj
    
    def __init__(self, parent):
        """Initialize only once."""
        if getattr(self, "_is_init", False):
            self.parent = parent
            return
        
        super().__init__(name="unique_window_name")
        self._is_init = True
        # ... rest of init
```

---

### 2. Non-Singleton Pattern (Editor Windows)

**Quando usare:**
- Finestre editor/dettaglio
- Possono esserci istanze multiple (edit multiple records)

**Come implementare:**
```python
class UI(tk.Toplevel):
    """Editor window - Non-singleton pattern."""
    
    def __init__(self, parent, index=None):
        """Create new instance every time."""
        super().__init__(name="editor")
        self.parent = parent
        self.index = index  # Primary key or None for INSERT
        # ... rest of init
```

---

### 3. Mixin Pattern

**Quando usare:**
- Funzionalità condivisa tra classi
- Comportamenti composable
- Evitare deep inheritance hierarchies

**Come implementare:**
```python
# Mixin classes (no __init__, stateless)
class QCMixin:
    """Quality control calculations."""
    def get_mean(self, values):
        pass

class WestgardsMixin:
    """Westgard rules evaluation."""
    def get_rule_13S(self, series, limits):
        pass

# Main class combines all mixins
class Engine(DBMS, Controller, QCMixin, WestgardsMixin, ToolsMixin):
    """
    Main orchestrator combining all mixins.
    
    MRO (Method Resolution Order):
        Engine → DBMS → Controller → QCMixin → WestgardsMixin → ToolsMixin
    """
    def __init__(self, user, password, database, host):
        # Initialize base classes
        DBMS.__init__(self, user, password, database, host)
        # Mixins have no __init__
```

**Rules for Mixins:**
- No `__init__` in mixin classes
- Stateless (no instance variables)
- Pure functions that operate on parameters
- Document dependencies clearly

---

### 4. Registry Pattern (Window Management)

**Quando usare:**
- Tracciare finestre aperte
- Cross-window communication
- Update windows from other windows

**Come implementare:**
```python
# In window __init__:
self.engine.dict_instances[self.winfo_name()] = self

# In window close:
self.engine.dict_instances.pop(self.winfo_name(), None)
self.engine.safe_close(self)

# To update another window:
win = self.engine.dict_instances.get("batches")
if win and win.winfo_exists():
    win._load_tree()
    win._set_index(batch_id)
```

**Benefits:**
- No parent-chain traversal (`self.parent.parent.parent`)
- Loose coupling between windows
- Windows can be opened/closed independently

---

## 🔒 Security Best Practices

### 1. SQL Injection Prevention

**ALWAYS use parameterized queries:**

✅ **GOOD:**
```python
sql = "SELECT * FROM users WHERE nickname = ?"
result = self.engine.read(False, sql, (nickname,))
```

❌ **BAD:**
```python
sql = f"SELECT * FROM users WHERE nickname = '{nickname}'"  # ❌ CRITICAL VULNERABILITY!
result = self.engine.read(False, sql, ())
```

**Why it matters:**
```python
# Attacker input:
nickname = "admin' OR '1'='1"

# Vulnerable query becomes:
"SELECT * FROM users WHERE nickname = 'admin' OR '1'='1'"
# ❌ Returns ALL users!

# Parameterized query:
"SELECT * FROM users WHERE nickname = ?"
# ✅ Safely escapes to: "SELECT * FROM users WHERE nickname = 'admin'' OR ''1''=''1'"
# Returns nothing (no user with that literal nickname)
```

---

### 2. Password Hashing

**NEVER store plaintext passwords:**

✅ **GOOD (already implemented):**
```python
import bcrypt

# Hashing (on registration/password change)
password_bytes = password.encode('utf-8')
hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))

# Verification (on login)
stored_hash = user["pswrd"].encode('utf-8')
password_bytes = password.encode('utf-8')
if bcrypt.checkpw(password_bytes, stored_hash):
    # Login successful
```

❌ **BAD:**
```python
# ❌ Plaintext password in database
sql = "INSERT INTO users (nickname, password) VALUES (?, ?)"
self.engine.write(sql, (nickname, password))  # ❌ CRITICAL!
```

---

### 3. Input Validation

**Validate before use:**

```python
def _validate_sql_identifier(self, identifier, name):
    """Validate table/column names to prevent SQL injection."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(
            f"Invalid {name}: '{identifier}'. "
            f"Only alphanumeric and underscore allowed."
        )
```

---

### 4. Least Privilege Principle

**Give minimum permissions necessary:**

```python
ROLE_ADMIN = 0       # Full access
ROLE_SUPERUSER = 1   # QC validation, lab-wide
ROLE_TECHNICIAN = 2  # Data entry, section-only
ROLE_AUTOLOGIN = 3   # Read-only

def on_configure_system(self):
    """Admin-only operation."""
    if self.engine.get_user_role() != ROLE_ADMIN:
        messagebox.showwarning("Permission Denied", "Admin access required.")
        return
```

---

## 🧪 Testing Philosophy

**"If it's not tested, it's broken."**

### 1. Manual Testing (Current Approach)

**Process:**
1. Make change
2. Test feature manually with real data
3. Test edge cases (empty data, wrong input, etc.)
4. Test integration with other features
5. Deploy to Sant'Andrea (production validation)

**Checklist:**
- [ ] Feature works as expected
- [ ] Error handling tested
- [ ] Edge cases covered
- [ ] No regression (existing features still work)
- [ ] Performance acceptable

---

### 2. Automated Testing (Future Goal)

**Unit Tests (pytest):**
```python
def test_westgard_13S():
    """Test 1:3s rejection rule."""
    westgard = Westgards()
    target = 100.0
    sd = 5.0
    
    # Series with one value > 3SD
    series = [100, 101, 102, 116]  # 116 is 3.2 SD above target
    
    limits = westgard._calculate_control_limits(target, sd)
    result = westgard.get_rule_13S(series, limits)
    
    assert result == True, "Should detect 1:3s violation"
```

**Integration Tests:**
```python
def test_qc_import_workflow():
    """Test complete QC import workflow."""
    # 1. Import file
    imported = engine.import_qc_file_auto(filepath, received_ts, workstation_id)
    assert imported > 0
    
    # 2. Verify results in database
    results = engine.read(True, "SELECT * FROM results WHERE received = ?", (received_ts,))
    assert len(results) == imported
    
    # 3. Verify Westgard validation triggered
    # ...
```

---

### 3. Regression Testing

**After every change:**
- Test the changed feature
- Test 2-3 related features
- Test 1-2 unrelated features (random smoke test)

**Why:** Changes can have unexpected side effects.

---

## 📝 Documentation Standards

### 1. Code Comments

**Good comments explain WHY, not WHAT:**

✅ **GOOD:**
```python
# Technicians are mobile workers who can work in different sections
# Only autologin users (guests) are restricted to single section
if role == 3:
    return

# Database returns Decimal type which breaks arithmetic with float
# Must convert both operands to float before calculation
avg_float = float(avg)
target_float = float(target)
bias = ((avg_float - target_float) / target_float) * 100.0
```

❌ **BAD:**
```python
# Check if role is 3
if role == 3:  # ❌ Yes, I can read the code
    return

# Convert to float
avg_float = float(avg)  # ❌ Yes, I see you're converting to float
```

---

### 2. Docstrings (Google Style)

**Template:**
```python
def method_name(self, param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description (one line).
    
    Longer description if needed. Explain what the method does,
    when to use it, any important behavior or side effects.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
        TypeError: When param2 is wrong type
    
    Example:
        >>> obj.method_name("test", 42)
        "result"
    
    Note:
        Any important notes, warnings, or caveats.
    """
    pass
```

---

### 3. CHANGELOG.md

**ALWAYS document changes:**

```markdown
### [2025-12-03] - Feature: Change User/Section Menu Items

#### Added
- **main.py**: New menu items "Change User" (Ctrl+U) and "Change Section" (Ctrl+E)
  - **Reason**: Allow switching user/section without restarting application
  - **Impact**: Better UX, faster workflow for multi-user environments

#### Changed
- **main.py**: Menu structure updated
  - Added separator before Change Password
  - Grouped user management functions together

#### Technical Details
- `on_change_user()`: Closes all windows, resets context, shows login
- `on_change_section()`: Updates section_id, reloads main window
- Permission: Change Section blocked for autologin (role=3) only

#### Benefits
- ✅ No application restart needed
- ✅ Faster user switching
- ✅ Better for shared workstations
```

---

## 🚫 Anti-Patterns (Cosa NON fare)

### 1. God Object
**Problem:** Una classe che fa tutto.

❌ **BAD:**
```python
class God:
    """Does everything: GUI, DB, business logic, validation, etc."""
    def show_window(self): pass
    def connect_db(self): pass
    def validate_data(self): pass
    def calculate_qc(self): pass
    def send_email(self): pass
    def backup_database(self): pass
    # ❌ 50 more methods doing unrelated things
```

✅ **GOOD:** Separate responsibilities into focused classes.

---

### 2. Magic Numbers
**Problem:** Hardcoded numbers with no meaning.

❌ **BAD:**
```python
if role <= 1:  # ❌ What does 1 mean?
    allow_access()

if len(series) >= 10:  # ❌ Why 10?
    calculate_westgard()
```

✅ **GOOD:**
```python
ROLE_SUPERUSER = 1
WESTGARD_MIN_SERIES = 10

if role <= ROLE_SUPERUSER:
    allow_access()

if len(series) >= WESTGARD_MIN_SERIES:
    calculate_westgard()
```

---

### 3. Copy-Paste Programming
**Problem:** Duplicare codice invece di refactor.

❌ **BAD:**
```python
# In file1.py
def format_date(dt):
    return dt.strftime("%d-%m-%Y")

# In file2.py  
def format_date(dt):  # ❌ Copy-pasted!
    return dt.strftime("%d-%m-%Y")

# In file3.py
def format_date(dt):  # ❌ Copy-pasted again!
    return dt.strftime("%d-%m-%Y")
```

✅ **GOOD:**
```python
# In engine.py (centralized)
def format_date(self, dt):
    """Format date according to user preference."""
    date_format = self.get_date_format()  # From config
    if date_format == "mm-dd-yyyy":
        return dt.strftime("%m-%d-%Y")
    else:  # dd-mm-yyyy
        return dt.strftime("%d-%m-%Y")

# In all other files
formatted = self.engine.format_date(dt)  # ✅ Reuse!
```

---

### 4. Premature Optimization
**Problem:** Ottimizzare prima che serva.

❌ **BAD:**
```python
# ❌ Spending 2 days optimizing this:
def get_mean(values):
    # Ultra-optimized with Cython, SIMD, GPU acceleration...
    pass

# When this works fine:
def get_mean(values):
    return sum(values) / len(values)  # ✅ Fast enough!
```

**Rule:** Make it work, then make it right, then make it fast (if needed).

---

### 5. Not Invented Here Syndrome
**Problem:** Riscrivere tutto invece di usare librerie esistenti.

❌ **BAD:**
```python
# ❌ Writing custom JSON parser
def my_json_parser(text):
    # 500 lines of buggy JSON parsing code
    pass
```

✅ **GOOD:**
```python
import json  # ✅ Use standard library!
data = json.loads(text)
```

---

### 6. Golden Hammer
**Problem:** "Ho un martello, quindi tutto è un chiodo."

❌ **BAD:**
```python
# Using Singleton pattern for EVERYTHING
class User(Singleton): pass  # ❌ Why singleton?
class Result(Singleton): pass  # ❌ Makes no sense
class TempData(Singleton): pass  # ❌ Wrong pattern
```

✅ **GOOD:** Use right pattern for right problem.

---

## 🎓 Learning Resources

### Python
- **PEP 8 Style Guide** - https://pep8.org
- **"Fluent Python"** by Luciano Ramalho (advanced)
- **"Clean Code"** by Robert Martin (principles apply to all languages)

### Design Patterns
- **"Design Patterns"** by Gang of Four (classic)
- **"Head First Design Patterns"** (easier introduction)
- **refactoring.guru** - Great visual explanations

### Database
- **"SQL Antipatterns"** by Bill Karwin
- **"Use The Index, Luke"** - use-the-index-luke.com (SQL performance)

### Tkinter
- **effbot.org/tkinterbook** - Classic Tkinter reference
- **TkDocs** - tkdocs.com (modern Tk documentation)

### Quality Control
- **"Basic QC Practices"** by Westgard JO (4th Edition, 2016)
- **ISO 15189:2022** - Medical laboratories standard

---

## 💡 Biovarase-Specific Wisdom

### "The Three Questions" (before any change)

Ask yourself:

1. **Does it violate PROJECT_RULES.md?**
   - If yes → STOP, rethink approach

2. **Can it be simpler?**
   - If yes → Simplify before implementing

3. **Will I understand this in 6 months?**
   - If no → Add comments/documentation

### Decision Matrix

| Question | Yes → | No → |
|----------|-------|------|
| Is it a master window? | Singleton pattern | Non-singleton |
| Does it access database? | Use `engine.read()` | Don't access DB directly |
| Is it business logic? | Put in Controller | Keep out of GUI |
| Is it reusable code? | Make a mixin/helper | Keep it local |
| Does it modify data? | Log the change | No logging needed |
| Can user break it? | Add validation | Trust the input |
| Will it fail? | Add error handling | Let it fail fast |

### Code Review Checklist

Before committing code, check:

- [ ] No PROJECT_RULES.md violations
- [ ] No positional indexing (`row[0]`)
- [ ] SQL uses placeholders (no concatenation)
- [ ] All exceptions logged
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] No magic numbers
- [ ] No hardcoded paths
- [ ] CHANGELOG.md updated
- [ ] Manual testing done

---

## 🔄 Refactoring Checklist

### Before Refactoring

- [ ] Create timestamped backup (`.bak_YYYYMMDD_HHMMSS`)
- [ ] Document current behavior completely
- [ ] Write down what you want to change and why
- [ ] Check if it affects other code

### During Refactoring

- [ ] One change at a time (atomic commits)
- [ ] Test after each small change
- [ ] Keep git commits small and focused
- [ ] Don't refactor and add features simultaneously

### After Refactoring

- [ ] Compare before/after behavior
- [ ] Run through test cases
- [ ] Update CHANGELOG.md
- [ ] Update relevant documentation
- [ ] Test edge cases
- [ ] Deploy to test environment first

---

## 🎯 Quality Gates

### Code is ready when:

**Compilation:**
- [ ] Python compiles without syntax errors
- [ ] All imports resolve correctly

**Standards:**
- [ ] No PROJECT_RULES.md violations
- [ ] PEP 8 compliant (mostly)
- [ ] English-only comments and docstrings

**Documentation:**
- [ ] All public methods have docstrings
- [ ] Type hints on all methods
- [ ] CHANGELOG.md entry exists
- [ ] Architecture changes documented

**Testing:**
- [ ] Manual testing passed
- [ ] Edge cases tested
- [ ] Error handling verified
- [ ] No regressions detected

**Code Quality:**
- [ ] No TODO comments (or in backlog)
- [ ] No commented-out code blocks
- [ ] No debug print statements
- [ ] No magic numbers

---

## 📊 Metrics for Success

### Code Quality Metrics

**Good indicators:**
- Lines of code decreasing (refactoring working)
- Documentation coverage increasing
- Bug reports decreasing
- Code review time decreasing (code is clearer)

**Bad indicators:**
- File size growing rapidly (God object warning)
- Copy-paste code appearing
- Exception handlers with `pass`
- TODO comments accumulating

### Project Health

**Green flags:** ✅
- Features shipping on time
- Users happy (positive feedback)
- Code easy to change
- Bugs rare and easy to fix

**Red flags:** 🚩
- Fear of changing code ("might break something")
- Copy-paste to add features ("safer than modifying")
- Long debugging sessions ("what does this do?")
- Avoiding certain files ("too complex")

---

## 🚀 Continuous Improvement

### Weekly Practice

**Monday:**
- Review last week's code
- Identify one thing to improve

**During Week:**
- Apply improvement to new code
- Refactor one old file/method

**Friday:**
- Document what you learned
- Update best practices if needed

### Monthly Review

- [ ] Review CHANGELOG.md
- [ ] Identify patterns (good and bad)
- [ ] Update PROJECT_RULES.md if needed
- [ ] Plan refactoring for next month

---

## 🎓 Remember

> "Code quality is not a sprint, it's a marathon."

> "Small, consistent improvements beat big rewrites."

> "The best code is code that doesn't need to be written."

> "Make it work, then make it right, then make it fast."

> "Simplicity is the ultimate sophistication." - Leonardo da Vinci

---

**END OF BEST_PRACTICES.md**

**Next steps:**
1. Read this document at start of each session
2. Reference specific sections when making design decisions
3. Update as we learn new patterns
4. Share with team members when project grows

**Questions? Doubts? Ask!** It's better to ask than to guess. 😊
