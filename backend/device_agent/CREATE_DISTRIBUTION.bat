@echo off
REM ============================================================
REM Create Distribution Package for Agent
REM This creates a ZIP file ready for sharing/download
REM ============================================================

echo.
echo ============================================================
echo   Creating Agent Distribution Package
echo ============================================================
echo.

REM Get script directory
set "AGENT_DIR=%~dp0"
set "PARENT_DIR=%AGENT_DIR%.."
cd /d "%AGENT_DIR%"

echo [STEP 1/3] Checking files...
echo.

REM Check if INSTALL.bat exists
if not exist "INSTALL.bat" (
    echo [ERROR] INSTALL.bat not found!
    echo Please make sure you're running this from the device_agent folder.
    pause
    exit /b 1
)

if not exist "agent.py" (
    echo [ERROR] agent.py not found!
    echo Please make sure you're running this from the device_agent folder.
    pause
    exit /b 1
)

echo [OK] All required files found
echo.

echo [STEP 2/3] Creating ZIP package...
echo.

REM Create ZIP file in parent directory
set "ZIP_NAME=antitheft-agent-installer.zip"
set "ZIP_PATH=%PARENT_DIR%\%ZIP_NAME%"

REM Remove old ZIP if exists
if exist "%ZIP_PATH%" (
    del "%ZIP_PATH%"
    echo [INFO] Removed old ZIP file
)

REM Create ZIP using PowerShell (works on Windows 7+)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%AGENT_DIR%*' -DestinationPath '%ZIP_PATH%' -Force"

if errorlevel 1 (
    echo [ERROR] Failed to create ZIP file!
    echo.
    echo Alternative: Manually create ZIP of the device_agent folder
    pause
    exit /b 1
)

echo [OK] ZIP package created successfully!
echo.

echo [STEP 3/3] Package Information...
echo.
echo ============================================================
echo   Distribution Package Created!
echo ============================================================
echo.
echo File: %ZIP_NAME%
echo Location: %PARENT_DIR%
echo Size: 
for %%A in ("%ZIP_PATH%") do echo    %%~zA bytes
echo.
echo ============================================================
echo   Next Steps
echo ============================================================
echo.
echo 1. Upload %ZIP_NAME% to one of these services:
echo    - Google Drive (drive.google.com)
echo    - OneDrive (onedrive.live.com)
echo    - Dropbox (dropbox.com)
echo    - GitHub Releases (github.com)
echo    - WeTransfer (wetransfer.com)
echo.
echo 2. Get the download link
echo.
echo 3. Send the link to your friend
echo.
echo 4. Friend downloads, extracts, and runs INSTALL.bat
echo.
echo ============================================================
echo.
pause
