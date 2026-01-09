@echo off
REM ============================================================================
REM  Biovarase - build_biovarase.cmd
REM  Build script for Nuitka compilation (STANDALONE mode)
REM  
REM  Updated: 2025-01-08
REM  Changes:
REM    - Security implementation (config.enc replaces config.txt)
REM    - File config nella ROOT (syntax: file=file invece di file=.)
REM    - Icona .exe aggiunta da biovarase.ico (root)
REM    - Rimossi riferimenti a directory/file inesistenti
REM  Target: Windows 10 / 11, Python 3.7+
REM ============================================================================

cd /d "%~dp0"

echo.
echo ============================================================================
echo  Biovarase Build System
echo ============================================================================
echo.

REM ============================================================================
REM  Pre-Build Checks
REM ============================================================================

echo [1/6] Checking Python installation...
py --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! Install Python 3.7+ first.
    pause
    goto :eof
)
py --version

echo.
echo [2/6] Checking Nuitka installation...
py -m nuitka --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Nuitka not found!
    echo Install with: py -m pip install nuitka
    pause
    goto :eof
)
py -m nuitka --version

echo.
echo [3/6] Checking cryptography library...
py -c "import cryptography" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] cryptography not found!
    echo Install: py -m pip install "cryptography>=3.4.8,<39.0.0"
    pause
    goto :eof
)
py -c "import cryptography; print('cryptography ' + cryptography.__version__)"

echo.
echo [4/6] Checking MinGW64 compiler...
where gcc >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] MinGW64 not found in PATH.
    echo Nuitka will download it automatically on first build.
    timeout /t 2 >nul
) ELSE (
    echo MinGW64 found
)

echo.
echo [5/6] Checking icon file...
IF NOT EXIST "biovarase.ico" (
    echo [WARNING] biovarase.ico not found!
    echo .exe will have default Windows icon.
    timeout /t 2 >nul
) ELSE (
    echo [OK] Icon found: biovarase.ico
)

echo.
echo [6/6] Checking required files...
IF NOT EXIST "biovarase.py" (
    echo [ERROR] biovarase.py not found!
    pause
    goto :eof
)
IF NOT EXIST "security.py" (
    echo [ERROR] security.py not found!
    pause
    goto :eof
)
IF NOT EXIST "setup_wizard.py" (
    echo [ERROR] setup_wizard.py not found!
    pause
    goto :eof
)
echo [OK] All required Python files found.

echo.
echo ============================================================================
echo  Starting Nuitka Compilation
echo ============================================================================
echo.
echo Mode: STANDALONE (creates dist\biovarase.dist\ folder)
echo Output: dist\biovarase.dist\biovarase.exe
echo Icon: biovarase.ico (embedded in .exe)
echo.
echo This may take 5-15 minutes depending on your system...
echo (First build will be slower - downloads MinGW64 if needed)
echo.

REM ============================================================================
REM  Nuitka Compilation Command
REM  
REM  IMPORTANT: Nuitka syntax for files in root:
REM    --include-data-files=SOURCE=DEST
REM    SOURCE = file in project root
REM    DEST   = file name (NOT "." - that's illegal!)
REM    
REM  Example: --include-data-files=icon=icon (copies "icon" to "icon")
REM ============================================================================

py -m nuitka biovarase.py ^
    --standalone ^
    --output-dir=dist ^
    --output-filename=biovarase ^
    --windows-icon-from-ico=biovarase.ico ^
    --enable-plugin=tk-inter ^
    --follow-imports ^
    --mingw64 ^
    ^
    --include-package=cryptography ^
    --include-package=security ^
    --nofollow-import-to=tkinter.test ^
    ^
    --include-data-dir=documents=documents ^
    --include-data-dir=sql=sql ^
    ^
    --include-data-files=autologin=autologin ^
    --include-data-files=correlation_coefficient=correlation_coefficient ^
    --include-data-files=date_format=date_format ^
    --include-data-files=ddof=ddof ^
    --include-data-files=dimensions=dimensions ^
    --include-data-files=elements=elements ^
    --include-data-files=icon=icon ^
    --include-data-files=language=language ^
    --include-data-files=LICENSE=LICENSE ^
    --include-data-files=observations=observations ^
    --include-data-files=records=records ^
    --include-data-files=remember_batch=remember_batch ^
    --include-data-files=section_id=section_id ^
    --include-data-files=zscore=zscore ^
    --include-data-files=documents.json=documents.json

REM Note: NO line continuation after last file

REM ============================================================================
REM  Post-Build Check
REM ============================================================================

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================================
    echo  BUILD FAILED (ERRORLEVEL=%ERRORLEVEL%)
    echo ============================================================================
    echo.
    echo Common issues:
    echo  - MinGW64 not found (let Nuitka download it automatically)
    echo  - Missing dependencies (check imports)
    echo  - Syntax errors in Python code
    echo  - Icon file not found (build continues but without icon)
    echo  - cryptography version incompatible (use 38.x for Python 3.7)
    echo  - Illegal path syntax (use file=file, NOT file=.)
    echo.
    echo Check error messages above for details.
    echo.
    pause
    goto :eof
)

echo.
echo ============================================================================
echo  BUILD SUCCESSFUL!
echo ============================================================================
echo.
echo Output folder: dist\biovarase.dist\
echo Executable:    dist\biovarase.dist\biovarase.exe
echo Icon:          Embedded in .exe (biovarase.ico)
echo.

REM ============================================================================
REM  Post-Build Verification
REM ============================================================================

echo ============================================================================
echo  Verifying Build Contents
echo ============================================================================
echo.

IF EXIST "dist\biovarase.dist\biovarase.exe" (
    echo [OK] biovarase.exe created
) ELSE (
    echo [ERROR] biovarase.exe NOT found!
)

IF EXIST "dist\biovarase.dist\security.py" (
    echo [OK] security.py included
) ELSE (
    echo [WARNING] security.py NOT found
)

IF EXIST "dist\biovarase.dist\setup_wizard.py" (
    echo [OK] setup_wizard.py included
) ELSE (
    echo [WARNING] setup_wizard.py NOT found
)

echo.
echo Checking config files in ROOT:

IF EXIST "dist\biovarase.dist\icon" (
    echo [OK] icon file in root
) ELSE (
    echo [WARNING] icon file NOT in root
)

IF EXIST "dist\biovarase.dist\section_id" (
    echo [OK] section_id file in root
) ELSE (
    echo [WARNING] section_id file NOT in root
)

IF EXIST "dist\biovarase.dist\dimensions" (
    echo [OK] dimensions file in root
) ELSE (
    echo [WARNING] dimensions file NOT in root
)

IF EXIST "dist\biovarase.dist\date_format" (
    echo [OK] date_format file in root
) ELSE (
    echo [WARNING] date_format file NOT in root
)

IF EXIST "dist\biovarase.dist\ddof" (
    echo [OK] ddof file in root
) ELSE (
    echo [WARNING] ddof file NOT in root
)

IF EXIST "dist\biovarase.dist\zscore" (
    echo [OK] zscore file in root
) ELSE (
    echo [WARNING] zscore file NOT in root
)

echo.
echo Checking directories:

IF EXIST "dist\biovarase.dist\documents" (
    echo [OK] documents\ directory
) ELSE (
    echo [ERROR] documents\ directory NOT found
)

IF EXIST "dist\biovarase.dist\cryptography" (
    echo [OK] cryptography\ library
) ELSE (
    echo [ERROR] cryptography\ library NOT found
)

echo.
echo ============================================================================
echo  Build Summary
echo ============================================================================
echo.
echo What's inside dist\biovarase.dist\:
echo  - biovarase.exe          (main executable WITH ICON)
echo  - security.py            (encryption module)
echo  - setup_wizard.py        (first-time setup GUI)
echo  - cryptography\          (security library)
echo  - icon, section_id, dimensions, ddof, etc. (config files in ROOT)
echo  - documents\, sql\ (application data)
echo.
echo SECURITY NOTE: 
echo  - config.txt is NOT included (replaced by config.enc)
echo  - config.enc is NOT included (created at first run, hardware-locked)
echo.

REM ============================================================================
REM  Testing Instructions
REM ============================================================================

echo ============================================================================
echo  Next Steps - Testing the Build
echo ============================================================================
echo.
echo 1. TEST LOCALLY (Development PC):
echo    cd dist\biovarase.dist
echo    biovarase.exe
echo.
echo 2. FIRST RUN (ANY PC):
echo    - Setup wizard appears (config.enc doesn't exist)
echo    - Enter database credentials:
echo      * User: biovarase
echo      * Password: [your DB password]
echo      * Database: biovarase
echo      * Host: localhost (or IP)
echo    - Click "Save and Continue"
echo    - config.enc created (hardware-locked to THIS PC)
echo    - Login window appears
echo.
echo 3. SUBSEQUENT RUNS (SAME PC):
echo    - biovarase.exe
echo    - config.enc decrypted automatically (silent)
echo    - Login window appears directly
echo    - No database credential prompts
echo.
echo 4. VERIFY APPLICATION:
echo    - Login with user credentials (nickname/password)
echo    - Main window opens
echo    - Test QC operations:
echo      * Open Batches window
echo      * Add/view QC results
echo      * Generate Levey-Jennings chart
echo      * Test Westgard rules validation
echo.

REM ============================================================================
REM  Distribution Instructions
REM ============================================================================

echo ============================================================================
echo  Distribution to Sant'Andrea / Other PCs
echo ============================================================================
echo.
echo IMPORTANT: Hardware-Locked Security Model
echo.
echo 1. COPY ENTIRE FOLDER to target PC:
echo    - Copy: dist\biovarase.dist\
echo    - Do NOT include config.enc from this PC
echo    - Each PC creates its own config.enc
echo.
echo 2. ON TARGET PC - FIRST RUN:
echo    - Navigate to copied folder
echo    - Run biovarase.exe
echo    - Setup wizard appears (config.enc missing)
echo    - User enters database credentials
echo    - config.enc created (locked to THAT PC's hardware)
echo.
echo 3. HARDWARE LOCK BEHAVIOR:
echo    - config.enc is tied to specific PC (MAC + machine-id)
echo    - Copying config.enc to different PC = decryption FAILS
echo    - This is a SECURITY FEATURE (not a bug)
echo    - If PC hardware changes: re-run setup wizard
echo.
echo 4. DISTRIBUTION OPTIONS:
echo    Option A - USB stick:
echo      - Copy dist\biovarase.dist\ to USB
echo      - Copy to C:\Biovarase\ on target PC
echo      - Run biovarase.exe (setup wizard appears)
echo.
echo    Option B - Network share:
echo      - Copy to \\server\software\biovarase\
echo      - Users copy to local PC
echo      - Each runs setup wizard (own config.enc)
echo.
echo    Option C - Multiple PCs (Sant'Andrea):
echo      - Copy to each workstation: C:\Biovarase\
echo      - Each runs setup wizard
echo      - Each creates unique config.enc (hardware-locked)
echo      - All connect to SAME database (localhost or server IP)
echo.
echo 5. IT DOCUMENTATION:
echo    - Document database credentials (secure location)
echo    - If PC reinstalled: re-enter credentials in wizard
echo    - If PC upgraded: re-run setup wizard
echo    - No backup of config.enc needed (regenerated on demand)
echo.
echo ============================================================================
echo.

echo BUILD COMPLETE! Ready for testing and distribution.
echo.
pause