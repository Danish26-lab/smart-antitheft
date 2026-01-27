@echo off
REM ============================================================
REM Uninstall Anti-Theft Agent
REM ============================================================

echo.
echo ============================================================
echo   Anti-Theft Agent - Uninstaller
echo ============================================================
echo.

REM Check for admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Not running as administrator.
    echo Some cleanup may require admin rights.
    echo.
)

set "TASK_NAME=AntiTheftAgent"

echo [STEP 1/3] Stopping agent...
echo.
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Agent processes stopped
echo.

echo [STEP 2/3] Removing auto-start task...
echo.
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 (
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Could not remove scheduled task (may need admin rights)
    ) else (
        echo [OK] Auto-start task removed
    )
) else (
    echo [OK] No auto-start task found
)
echo.

echo [STEP 3/3] Cleanup options...
echo.
set /p DELETE_CONFIG="Delete configuration file? (Y/N): "
if /i "%DELETE_CONFIG%"=="Y" (
    if exist "config.json" (
        del "config.json"
        echo [OK] Configuration file deleted
    )
)

set /p DELETE_LOGS="Delete log files? (Y/N): "
if /i "%DELETE_LOGS%"=="Y" (
    if exist "agent.log" (
        del "agent.log"
        echo [OK] Log file deleted
    )
)

echo.
echo ============================================================
echo   Uninstallation Complete!
echo ============================================================
echo.
echo The agent has been removed from auto-start.
echo.
echo Note: Python and installed packages are NOT removed.
echo       You can reinstall by running INSTALL.bat again.
echo.
pause
