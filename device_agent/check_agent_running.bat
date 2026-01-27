@echo off
REM Quick check if agent is running

echo.
echo ========================================
echo  Check Agent Status
echo ========================================
echo.

REM Check if Python process is running agent.py
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "python.exe" >nul
if errorlevel 1 (
    echo [STATUS] Agent is NOT running
    echo.
    echo To start agent:
    echo   1. Double-click: run_agent_silent.vbs
    echo   2. Or run: python agent.py
    echo.
) else (
    echo [STATUS] Python process found
    echo.
    echo Checking if agent is responding...
    echo.
    
    REM Try to access local discovery endpoint
    curl -s http://127.0.0.1:9123/device-info >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Agent process running but not responding
        echo           Local server may not be started
        echo.
        echo Check: device_agent/agent.log
    ) else (
        echo [OK] Agent is running and responding!
        echo.
        echo Device Info:
        curl -s http://127.0.0.1:9123/device-info
        echo.
    )
)

echo.
echo ========================================
echo  Log File (Last 10 lines)
echo ========================================
if exist agent.log (
    powershell -Command "Get-Content agent.log -Tail 10"
) else (
    echo [INFO] No log file found (agent may not have run yet)
)

echo.
pause
