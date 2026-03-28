@echo off
REM AI Employee Web UI - Start Script
echo ========================================
echo  AI Employee Web Dashboard
echo ========================================
echo.
echo Starting web server...
echo Open http://localhost:5000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe app.py

pause
