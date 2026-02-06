@echo off
REM Run Locust performance test (headless) - generates report.html
REM Ensure backend is running first (start_all.bat or python backend/app.py)

echo.
echo ========================================
echo  Performance Test - Locust Load Test
echo ========================================
echo.
echo Make sure the backend is running (http://localhost:5000)
echo.
pause

pip install locust --quiet 2>nul
python -m locust -f locustfile.py AntiTheftAPIUser --headless -u 5 -r 1 -t 30s --html report.html

echo.
echo Report saved to: report.html
echo Open in browser to view results.
echo.
pause
