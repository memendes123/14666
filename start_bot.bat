@echo off
title STREAMZONE BOT PRO MAX
color 0B

echo ==============================================
echo        STREAMZONE BOT PRO MAX ULTRA
echo ==============================================
echo.

REM Go to this script folder
cd /d "%~dp0"
echo Current folder: %CD%
echo.

REM -------------------------------
REM Check Python
REM -------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found!
    echo Install Python 3.10 from:
    echo https://www.python.org/downloads/release/python-31011/
    pause
    exit /b
)

echo Python detected.
echo.

REM -------------------------------
REM Install dependencies
REM -------------------------------
echo Checking dependencies...
python -m pip install --upgrade pip

if exist requirements.txt (
    echo Installing from requirements.txt...
    python -m pip install -r requirements.txt
) else (
    echo Installing required packages...
    python -m pip install MetaTrader5==5.0.5430
    python -m pip install telethon==1.29.0
    python -m pip install psutil==6.0.0
    python -m pip install pytz==2024.1
)

echo Dependencies OK.
echo.

:runbot
cls
echo ==============================================
echo            Starting BOT...
echo ==============================================
echo.

python main.py

echo.
echo ==============================================
echo BOT stopped or crashed.
echo ==============================================
echo.

choice /c RS /m "R - Restart bot   S - Stop"
if errorlevel 2 goto end
if errorlevel 1 goto runbot

:end
echo Exiting...
pause
