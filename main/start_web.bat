@echo off
title CrazeDyn Panel - Web Interface
echo.
echo =======================================================
echo          CrazeDyn Panel - Web Interface
echo =======================================================
echo.
echo Starting Web Panel...
echo 🌐 Web interface will be available at: http://localhost:5000
echo 📱 Default login: admin / crazedyn123
echo.

cd /d "%~dp0"
python launcher.py --web

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Failed to start web panel!
    echo 💡 Try installing dependencies: python setup.py
    echo.
    pause
)