@echo off
REM ============================================================
REM Prey-Style Automatic Installer
REM One-click installation - No configuration needed!
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Anti-Theft Agent - Automatic Installer
echo   (Prey Project Style - Zero Configuration)
echo ============================================================
echo.

REM Get script directory
set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

REM Check for admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Not running as administrator.
    echo Some features may require admin rights.
    echo.
    echo Press any key to continue anyway, or Ctrl+C to cancel...
    pause >nul
)

echo [STEP 1/6] Checking Python installation...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo ============================================================
    echo   Python Installation Required
    echo ============================================================
    echo.
    echo Python 3.8+ is required for the agent to work.
    echo.
    echo Option 1: Download and install Python automatically
    echo Option 2: Install Python manually from python.org
    echo.
    set /p INSTALL_PYTHON="Do you want to open Python download page? (Y/N): "
    if /i "!INSTALL_PYTHON!"=="Y" (
        start https://www.python.org/downloads/
        echo.
        echo Please install Python and make sure to check "Add Python to PATH"
        echo Then run this installer again.
        pause
        exit /b 1
    ) else (
        echo.
        echo Please install Python 3.8+ from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python !PYTHON_VERSION! is installed
echo.

echo [STEP 2/6] Checking pip...
echo.
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available!
    echo Please reinstall Python and make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] pip is available
echo.

echo [STEP 3/6] Installing dependencies...
echo This may take a few minutes. Please wait...
echo.
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully
echo.

echo [STEP 4/6] Creating configuration...
echo.
if not exist "config.json" (
    echo [INFO] Creating default configuration...
    REM Agent will auto-register on first run
    echo {} > config.json
    echo [OK] Configuration file created
) else (
    echo [OK] Configuration file already exists
)
echo.

echo [STEP 5/6] Setting up auto-start...
echo.
REM Create startup task using Task Scheduler
set "TASK_NAME=AntiTheftAgent"
set "SCRIPT_PATH=%INSTALL_DIR%agent.py"
set "WORK_DIR=%INSTALL_DIR%"

REM Check if task already exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Creating Windows scheduled task for auto-start...
    
    REM Create task that runs on user logon
    schtasks /create /tn "%TASK_NAME%" /tr "pythonw \"%SCRIPT_PATH%\"" /sc onlogon /rl highest /f >nul 2>&1
    
    if errorlevel 1 (
        echo [WARNING] Could not create scheduled task (may need admin rights)
        echo Agent can still be started manually.
    ) else (
        echo [OK] Auto-start task created successfully
        echo       Agent will start automatically on login
    )
) else (
    echo [OK] Auto-start task already exists
)
echo.

echo [STEP 6/6] Starting agent...
echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo The agent will now start automatically.
echo.
echo IMPORTANT: The agent must keep running for tracking to work.
echo.
echo Options:
echo   1. Keep the agent window open (visible)
echo   2. Minimize the window (runs in background)
echo   3. Close this window - agent will auto-start on next login
echo.
pause

REM Start agent in background (minimized)
start /min pythonw agent.py

timeout /t 3 /nobreak >nul

REM Check if agent started
tasklist /FI "IMAGENAME eq pythonw.exe" 2>NUL | find /I /N "pythonw.exe">NUL
if errorlevel 1 (
    REM Try with python.exe if pythonw failed
    start /min python agent.py
    timeout /t 2 /nobreak >nul
)

echo.
echo ============================================================
echo   Agent Status
echo ============================================================
echo.
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if errorlevel 1 (
    tasklist /FI "IMAGENAME eq pythonw.exe" 2>NUL | find /I /N "pythonw.exe">NUL
    if errorlevel 1 (
        echo [WARNING] Agent may not have started.
        echo Try running manually: python agent.py
    ) else (
        echo [OK] Agent is running in background (pythonw.exe)
    )
) else (
    echo [OK] Agent is running (python.exe)
)
echo.

echo ============================================================
echo   Next Steps
echo ============================================================
echo.
echo 1. The agent is now running and will auto-register your device
echo 2. Open your browser and go to:
echo    https://frontend-wine-iota-46.vercel.app
echo 3. Sign up or log in
echo 4. Your device will automatically appear and link to your account
echo 5. Wait 1-2 minutes for the first location update
echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo The agent is now installed and running.
echo It will automatically start on every login.
echo.
echo To check if agent is running:
echo   - Open Task Manager
echo   - Look for "python.exe" or "pythonw.exe"
echo.
echo To view agent logs:
echo   - Open agent.log in this folder
echo.
pause
