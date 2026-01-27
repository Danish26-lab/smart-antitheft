@echo off
REM Easy Setup Script for Friend's Device
REM This script installs dependencies and starts the agent

echo.
echo ========================================
echo   Anti-Theft Agent - Easy Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available!
    echo Please reinstall Python and make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo [OK] pip is available
echo.

REM Install dependencies
echo Installing required packages...
echo This may take a few minutes...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!
echo.

REM Check if config.json exists
if not exist "config.json" (
    echo [INFO] First time setup - agent will auto-register
    echo.
)

echo ========================================
echo   Starting Agent...
echo ========================================
echo.
echo The agent will now start and register your device.
echo.
echo IMPORTANT: Keep this window open!
echo The agent must keep running for tracking to work.
echo.
echo You can minimize this window, but don't close it.
echo.
pause

REM Start the agent
python agent.py

REM If agent exits, show message
echo.
echo ========================================
echo   Agent Stopped
echo ========================================
echo.
echo The agent has stopped running.
echo.
echo To restart, run this script again or run: python agent.py
echo.
pause
