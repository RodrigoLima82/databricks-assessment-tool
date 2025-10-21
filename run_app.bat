@echo off
REM ============================================================================
REM Databricks Assessment Tool - Windows Batch Starter
REM ============================================================================
REM
REM This script starts the Databricks Assessment Tool on Windows
REM For more control, use: python run_app.py
REM
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo    DATABRICKS ASSESSMENT TOOL - Windows Startup
echo ============================================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Install from: https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

echo [OK] Python found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Install from: https://nodejs.org/en/download/
    pause
    exit /b 1
)

echo [OK] Node.js found

REM Check .env file
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Create .env based on .env.example
    pause
    exit /b 1
)

echo [OK] .env file found

echo.
echo Starting application via Python script...
echo.
echo Press Ctrl+C to stop
echo.

REM Run the Python starter script
python run_app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start
    pause
    exit /b 1
)

pause

