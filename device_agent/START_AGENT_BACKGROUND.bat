@echo off
REM Start Agent in Background (No Window)
REM Use this to run agent silently without showing a window

echo Starting agent in background...
start /min pythonw agent.py
timeout /t 2 /nobreak >nul

REM Check if agent started
tasklist /FI "IMAGENAME eq pythonw.exe" 2>NUL | find /I /N "pythonw.exe">NUL
if errorlevel 1 (
    echo [ERROR] Agent failed to start. Trying with python.exe instead...
    start /min python agent.py
)

echo.
echo [OK] Agent started in background!
echo.
echo To check if agent is running:
echo   - Open Task Manager
echo   - Look for "python.exe" or "pythonw.exe"
echo.
echo To stop the agent:
echo   - Open Task Manager
echo   - End "python.exe" or "pythonw.exe" process
echo.
pause
