"""
Embedded Agent Files for Vercel Deployment
Contains essential agent files as strings for serverless deployment
"""

# Essential agent files embedded as strings
# These will be included in the ZIP download on Vercel

AGENT_FILES = {
    'INSTALL.bat': '''@echo off
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
echo    https://antitheft.vercel.app
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
''',
    
    'requirements.txt': '''requests>=2.31.0
psutil>=5.9.0
opencv-python>=4.8.0
pyzbar>=0.1.9
''',
    
    'README_INSTALLER.md': '''# 🚀 Prey-Style Automatic Installer

## Overview

This installer follows the **Prey Project approach** - **zero configuration, fully automatic setup**. Your friend just needs to double-click `INSTALL.bat` and everything is done automatically.

## How It Works (Like Prey)

### Prey Project Method:
1. ✅ User downloads installer
2. ✅ Double-clicks installer
3. ✅ Everything installs automatically
4. ✅ Agent auto-registers device
5. ✅ Agent auto-starts on boot
6. ✅ **No user configuration needed**

### Our Implementation:
1. ✅ Friend copies `device_agent` folder
2. ✅ Double-clicks `INSTALL.bat`
3. ✅ Installer checks Python (prompts if missing)
4. ✅ Auto-installs dependencies
5. ✅ Auto-creates configuration
6. ✅ Auto-sets up Windows scheduled task
7. ✅ Auto-starts agent
8. ✅ **No user configuration needed**

## Installation Steps

### For Your Friend (Super Simple):

1. **Copy the `device_agent` folder** to their laptop
2. **Double-click `INSTALL.bat`**
3. **Wait for installation to complete** (2-3 minutes)
4. **Done!** Agent is running and will auto-start on login

### What Happens Automatically:

1. **Python Check**: Verifies Python is installed (prompts if missing)
2. **Dependencies**: Installs all required packages automatically
3. **Configuration**: Creates `config.json` automatically
4. **Auto-Start**: Sets up Windows scheduled task for auto-start
5. **Agent Start**: Starts the agent immediately
6. **Registration**: Agent auto-registers device (no user input)

## Features (Like Prey)

### ✅ Automatic Registration
- Agent registers itself on first run
- Creates "unowned" device in database
- Links to user account when friend logs in
- **No manual registration needed**

### ✅ Auto-Start on Boot
- Windows scheduled task created automatically
- Agent starts on every login
- Runs in background (minimized)
- **No manual startup needed**

### ✅ Zero Configuration
- All settings auto-detected
- Hardware fingerprinting automatic
- Backend URL pre-configured
- **No config file editing needed**

### ✅ Background Operation
- Runs silently in background
- No console window needed
- Can check status via Task Manager
- **No user interaction needed**

## File Structure

```
device_agent/
├── INSTALL.bat          ← Double-click this (main installer)
├── UNINSTALL.bat        ← Remove agent (optional)
├── agent.py            ← Main agent (auto-started)
├── config.json         ← Auto-created (no editing needed)
├── requirements.txt    ← Dependencies (auto-installed)
└── README_INSTALLER.md ← This file
```

## Usage

### Installation:
```batch
Double-click: INSTALL.bat
```

### Uninstallation:
```batch
Double-click: UNINSTALL.bat
```

### Manual Start (if needed):
```batch
python agent.py
```

### Check Status:
- Open Task Manager
- Look for `python.exe` or `pythonw.exe`
- Or check `agent.log` file

## What Friend Needs to Do

### Minimum (Recommended):
1. Copy `device_agent` folder
2. Double-click `INSTALL.bat`
3. Wait for completion
4. **Done!**

### If Python Not Installed:
1. Installer will prompt
2. Click "Y" to open Python download page
3. Download and install Python
4. **Important**: Check "Add Python to PATH"
5. Run `INSTALL.bat` again

## After Installation

1. **Agent is running** (check Task Manager)
2. **Friend logs in** to frontend
3. **Device auto-appears** in dashboard
4. **Device auto-links** to friend's account
5. **Location updates** start within 1-2 minutes

## Troubleshooting

### Agent Not Starting:
- Check Task Manager for `python.exe`
- Check `agent.log` for errors
- Try running `python agent.py` manually

### Python Not Found:
- Reinstall Python
- Make sure "Add Python to PATH" is checked
- Restart computer after installation

### Dependencies Failed:
- Check internet connection
- Try: `pip install -r requirements.txt` manually

### Auto-Start Not Working:
- May need admin rights
- Check Task Scheduler for "AntiTheftAgent" task
- Can start manually: `python agent.py`

## Comparison with Prey

| Feature | Prey Project | Our System |
|---------|--------------|------------|
| Installation | One-click installer | One-click `INSTALL.bat` |
| Configuration | Automatic | Automatic |
| Registration | Auto-register | Auto-register |
| Auto-Start | Windows Service | Scheduled Task |
| Background | Yes | Yes |
| User Input | None | None (except Python if missing) |

## Advantages

1. **Zero Configuration**: Everything automatic
2. **User-Friendly**: Just double-click and done
3. **Prey-Style**: Follows proven Prey approach
4. **Reliable**: Auto-start ensures agent always runs
5. **Simple**: No technical knowledge needed

## Notes

- Agent must keep running for tracking to work
- Auto-start ensures it runs on every login
- Configuration is auto-created and managed
- No manual editing of config files needed
- Agent auto-registers on first run

---

**Just like Prey - install once, forget about it!** 🎉
'''
}

# Note: Full agent.py and other Python files are too large to embed
# They will be read from device_agent folder if available, or downloaded from GitHub
