@echo off
title AgriRoute Intelligence Launcher
echo ========================================================
echo        AGRIROUTE INTELLIGENCE - STARTING SERVICES
echo ========================================================
echo.
echo 1. Starting Python Backend Server on Port 8000...
start "AgriRoute Backend (Port 8000)" cmd /k "cd /d "%~dp0" && .\.python\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

echo 2. Starting Frontend Web Server on Port 8080...
start "AgriRoute Frontend (Port 8080)" cmd /k "cd /d "%~dp0" && powershell -ExecutionPolicy Bypass -File .\serve.ps1 -Port 8080"

echo 3. Waiting 3 seconds for servers to initialize...
timeout /t 3 /nobreak >nul

echo 4. Opening Dashboard in your Web Browser...
start http://localhost:8080

echo.
echo ========================================================
echo  AGRIROUTE INTELLIGENCE IS RUNNING!
echo  Dashboard: http://localhost:8080
echo  Backend API Docs: http://localhost:8000/docs
echo.
echo  Keep the two server windows open while using.
echo  To stop, simply close those two command windows.
echo ========================================================
pause
