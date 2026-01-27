@echo off
REM Install Agent as Windows Startup Service
REM This will make the agent run automatically when Windows starts

echo.
echo ========================================
echo  Install Anti-Theft Agent as Startup
echo ========================================
echo.

REM Get the script directory
set "AGENT_DIR=%~dp0"
set "PROJECT_ROOT=%AGENT_DIR%.."

echo Agent Directory: %AGENT_DIR%
echo Project Root: %PROJECT_ROOT%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Create startup shortcut
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=Anti-Theft Agent.lnk"

echo Creating startup shortcut...
echo Target: %AGENT_DIR%run_agent_silent.vbs
echo.

REM Create VBScript to create shortcut
set "VBS_FILE=%TEMP%\create_shortcut.vbs"
(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo sLinkFile = "%STARTUP_FOLDER%\%SHORTCUT_NAME%"
echo Set oLink = oWS.CreateShortcut(sLinkFile^)
echo oLink.TargetPath = "%AGENT_DIR%run_agent_silent.vbs"
echo oLink.WorkingDirectory = "%AGENT_DIR%"
echo oLink.Description = "Anti-Theft Device Agent - Runs on Windows startup"
echo oLink.Save
) > "%VBS_FILE%"

cscript //nologo "%VBS_FILE%"
del "%VBS_FILE%"

if exist "%STARTUP_FOLDER%\%SHORTCUT_NAME%" (
    echo [OK] Startup shortcut created successfully!
    echo.
    echo The agent will now start automatically when Windows boots.
    echo.
    echo To test: Restart your computer or run the agent manually:
    echo   Double-click: run_agent_silent.vbs
    echo.
) else (
    echo [ERROR] Failed to create startup shortcut
    echo.
    echo Manual setup:
    echo 1. Press Win+R, type: shell:startup
    echo 2. Create shortcut to: %AGENT_DIR%run_agent_silent.vbs
    echo.
)

pause
