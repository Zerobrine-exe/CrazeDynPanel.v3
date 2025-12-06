@echo off
title CrazeDyn Panel - Desktop App
echo.
echo =======================================================
echo          CrazeDyn Panel - Desktop Application
echo =======================================================
echo.
echo Starting Desktop GUI...
echo.

cd /d "%~dp0"
python app\__main__.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Failed to start desktop app!
    echo 💡 Make sure PyQt6 is installed: pip install PyQt6
    echo.
    pause
)