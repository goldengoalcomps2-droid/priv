@echo off
REM Video Downloader - Windows Setup & Launch
title Video Downloader Setup

echo.
echo   ==================================
echo     Video Downloader - Setup
echo   ==================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo   [ERROR] Python not found.
    echo   Install Python from: https://python.org/downloads
    echo   Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo   Found Python:
python --version

REM Create virtual environment if needed
if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo   Installing dependencies...
pip install -q -r requirements.txt

REM Create downloads folder
if not exist "downloads" mkdir downloads

echo.
echo   ==================================
echo     Setup Complete!
echo   ==================================
echo.
echo   Starting Video Downloader...
echo   Open your browser to: http://localhost:5000
echo.

python app.py
pause
