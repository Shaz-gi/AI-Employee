@echo off
REM Simple Email Fetcher - Start Script (FIXED)

echo ============================================================
echo AI Employee - Simple Real-Time Email Fetcher
echo ============================================================
echo.

REM Set Supabase credentials
REM Get these from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api
set SUPABASE_URL=https://vzxlgdsaiunlhkcjseah.supabase.co
set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6eGxnZHNhaXVubGhrY2pzZWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyMjczODEsImV4cCI6MjA4OTgwMzM4MX0.inBPIjyqyRyDeTZKWP4aOhdhTza_zF1R7eXUU41HiT4
set SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6eGxnZHNhaXVubGhrY2pzZWFoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDIyNzM4MSwiZXhwIjoyMDg5ODAzMzgxfQ.Ucm35l7fxgN2wMYGox_Fse3E8je0SJg0vYrVjL7gjeo

echo Starting email fetcher...
echo Using service role key: %SUPABASE_SERVICE_KEY:~0,10%...
echo.

cd /d "%~dp0"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\simple_email_fetcher.py

pause
