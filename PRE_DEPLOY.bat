@echo off
REM ============================================================
REM Pre-Deploy Script
REM Copies agent files to backend for Vercel deployment
REM ============================================================

echo.
echo ============================================================
echo   Preparing for Vercel Deployment
echo ============================================================
echo.

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo [STEP 1/2] Copying agent files to backend...
echo.
cd backend
python utils/copy_agent_files.py

if errorlevel 1 (
    echo [ERROR] Failed to copy agent files!
    pause
    exit /b 1
)

echo.
echo [STEP 2/2] Ready for deployment!
echo.
echo Agent files have been copied to backend/device_agent
echo You can now deploy to Vercel:
echo   vercel --prod
echo.
pause
