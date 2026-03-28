@echo off
REM Multi-User Email Fetcher - Start Script

echo ============================================================
echo AI Employee - Multi-User Email Fetcher
echo ============================================================
echo.
echo This will fetch emails for ALL users who connected Gmail
echo Each user gets their own vault and isolated emails
echo.

REM Set Supabase credentials
set SUPABASE_URL=https://vzxlgdsaiunlhkcjseah.supabase.co
set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6eGxnZHNhaXVubGhrY2pzZWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyMjczODEsImV4cCI6MjA4OTgwMzM4MX0.inBPIjyqyRyDeTZKWP4aOhdhTza_zF1R7eXUU41HiT4
set SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6eGxnZHNhaXVubGhrY2pzZWFoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDIyNzM4MSwiZXhwIjoyMDg5ODAzMzgxfQ.Ucm35l7fxgN2wMYGox_Fse3E8je0SJg0vYrVjL7gjeo

echo Starting multi-user email fetcher...
echo.

cd /d "%~dp0"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\multi_user_email_fetcher.py

pause
