@echo off
REM AI Employee - Quick Start Script
REM Run this to start all AI Employee services

echo ========================================
echo  AI Employee - Silver Tier
echo ========================================
echo.

cd /d "%~dp0"

echo Starting AI Employee Orchestrator...
echo Press Ctrl+C to stop
echo.

REM Start orchestrator (runs continuously)
python src\orchestrator.py AI_Employee_Vault

pause
