@echo off
REM Multi-User AI Orchestrator - Start Script

echo ============================================================
echo AI Employee - Multi-User AI Orchestrator
echo ============================================================
echo.
echo This will process emails for ALL users with AI
echo Each user gets personalized AI analysis and draft responses
echo.

REM Set environment variables
set SUPABASE_URL=https://vzxlgdsaiunlhkcjseah.supabase.co
set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6eGxnZHNhaXVubGhrY2pzZWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyMjczODEsImV4cCI6MjA4OTgwMzM4MX0.inBPIjyqyRyDeTZKWP4aOhdhTza_zF1R7eXUU41HiT4
set SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6eGxnZHNhaXVubGhrY2pzZWFoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDIyNzM4MSwiZXhwIjoyMDg5ODAzMzgxfQ.Ucm35l7fxgN2wMYGox_Fse3E8je0SJg0vYrVjL7gjeo
Set OPENROUTER_API_KEY=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
Set OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free

echo Starting multi-user orchestrator...
echo.

cd /d "%~dp0"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\multi_user_orchestrator.py

pause
