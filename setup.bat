@echo off
setlocal enabledelayedexpansion
color 0e
title CrazeDynPanel v2.0 Setup

echo.
echo =========================================================================
echo                        🎮 CRAZEDYNPANEL V2.0 INSTALLER 🎮
echo =========================================================================
echo                   Made by Zerobrine - Professional Edition
echo                   Ultimate Minecraft Server Management Suite
echo =========================================================================
echo.
echo ✨ NEW IN V2.0:
echo    • Modern Icon-Based Interface       • Premium Plugin Management
echo    • Paper ^& Spigot Server Support      • Enhanced Search ^& Filtering  
echo    • Official Playit.gg Integration    • Professional Web Panel
echo    • Real-time Monitoring ^& Analytics  • Mobile-Responsive Design
echo =========================================================================
echo.
echo 🎯 ULTIMATE MINECRAFT SERVER MANAGER
echo 💼 Professional Control Panel with Premium Features  
echo 🌐 Desktop Application + Web Panel + Mobile Support
echo 🔗 Discord: https://dc.gg/zerocloud
echo 📺 YouTube: https://www.youtube.com/@Zerobrine_7
echo.

echo 📍 Installation Location:
set /p install_path=Enter path (or press Enter for C:\CrazeDynPanel): 
if "%install_path%"=="" set install_path=C:\CrazeDynPanel

echo.
echo 🎯 Mode Selection:
echo 1. Desktop GUI
echo 2. Web Panel  
echo 3. Both
set /p mode=Enter choice (1-3): 

REM Ask for email/password if web mode is selected
if "%mode%"=="2" goto ask_credentials
if "%mode%"=="3" goto ask_credentials
goto skip_credentials

:ask_credentials
echo.
echo 🔐 WEB PANEL ADMIN SETUP
echo =========================================================================
echo 📧 Admin credentials will be set up securely during installation
echo 🔒 Passwords are entered interactively (not visible in command line)
echo 🌐 You'll use these to login at http://localhost:5000
echo.
goto skip_credentials

:skip_credentials

echo.
echo 📁 Creating directory: %install_path%
mkdir "%install_path%" 2>nul
if errorlevel 1 (
    echo ⚠️ Failed to create directory "%install_path%". Please check permissions.
    pause
    exit /b 1
)

echo 📦 Copying files...
xcopy "Main" "%install_path%\Main\" /E /I /H /Y /Q
if errorlevel 1 (
    echo ⚠️ Failed to copy files from "Main". Make sure the folder exists.
    pause
    exit /b 1
)

echo 📋 Creating launchers...
if "%mode%"=="1" goto desktop
if "%mode%"=="2" goto web
if "%mode%"=="3" goto both
goto deps

:desktop
(
    echo @echo off
    echo title CrazeDynPanel v2.0 - Desktop
    echo cd /d "%install_path%\Main"
    echo python app\__main__.py
    echo pause
) > "%install_path%\Start_Desktop.bat"
echo ✅ Desktop launcher created
goto deps

:web
(
    echo @echo off
    echo title CrazeDynPanel v2.0 - Web Panel
    echo cd /d "%install_path%\Main"
    echo python launcher.py --web
    echo pause
) > "%install_path%\Start_Web.bat"
echo ✅ Web launcher created
goto deps

:both
(
    echo @echo off
    echo title CrazeDynPanel v2.0 - Desktop
    echo cd /d "%install_path%\Main"
    echo python app\__main__.py
    echo pause
) > "%install_path%\Start_Desktop.bat"

(
    echo @echo off
    echo title CrazeDynPanel v2.0 - Web Panel
    echo cd /d "%install_path%\Main"
    echo python launcher.py --web
    echo pause
) > "%install_path%\Start_Web.bat"
echo ✅ Both launchers created

:deps
echo.
echo 📦 Installing dependencies...
cd /d "%install_path%\Main"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo 💡 Please install Python 3.8+ from https://python.org
    echo 📘 Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if requirements.txt exists, if not create it
if not exist requirements.txt (
    echo 📝 Creating requirements.txt...
    (
        echo psutil
        echo requests
        echo flask
        echo flask-socketio
        echo gunicorn
        echo bcrypt
    ) > requirements.txt
)

REM Add PyQt6 for desktop mode
if "%mode%"=="1" (
    findstr /C:"pyqt6" requirements.txt >nul || echo pyqt6 >> requirements.txt
)
if "%mode%"=="3" (
    findstr /C:"pyqt6" requirements.txt >nul || echo pyqt6 >> requirements.txt
)

echo 📥 Installing Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    echo 💡 Try running: python -m pip install --upgrade pip
    pause
    exit /b 1
)

REM Setup admin credentials if web mode was selected
if "%mode%"=="2" goto setup_admin
if "%mode%"=="3" goto setup_admin
goto skip_admin

:setup_admin
echo.
echo 🔐 Setting up admin credentials...
echo 💡 For security, you'll enter credentials interactively
python setup_admin.py
if errorlevel 1 (
    echo ⚠️ Failed to setup admin credentials
    pause
    exit /b 1
)
echo ✅ Admin setup complete!

:skip_admin
echo.
echo =========================================================================
echo                          ✅ INSTALLATION COMPLETE! 
echo =========================================================================
echo.
echo 🎉 CrazeDynPanel v2.0 has been successfully installed!
echo.
echo 📍 Installation Directory: %install_path%
echo 🌐 Web Panel URL: http://localhost:5000
echo 📚 Documentation: README.md
echo.
echo ⚠️  IMPORTANT NOTES:
echo 📋 Java is required to run Minecraft servers
echo 💡 Download Java from: https://adoptium.net
echo 🔗 Playit.gg tunnels can be configured in the application
echo.
if "%mode%"=="1" echo 🚀 Start: %install_path%\Start_Desktop.bat
if "%mode%"=="2" echo 🚀 Start: %install_path%\Start_Web.bat
if "%mode%"=="3" (
    echo 🚀 Desktop: %install_path%\Start_Desktop.bat
    echo 🚀 Web: %install_path%\Start_Web.bat
)
echo.
echo 🎮 Ready to use! 🎮
echo.

set /p start_now=Start now? (Y/N): 
if /i "%start_now%"=="Y" (
    if "%mode%"=="1" start "" "%install_path%\Start_Desktop.bat"
    if "%mode%"=="2" start "" "%install_path%\Start_Web.bat"
    if "%mode%"=="3" (
        echo 1=Desktop, 2=Web
        set /p choice=Choose: 
        if "!choice!"=="1" start "" "%install_path%\Start_Desktop.bat"
        if "!choice!"=="2" start "" "%install_path%\Start_Web.bat"
    )
)

echo.
echo Thanks for using CrazeDynPanel v2.0! 🚀
echo.
pause
endlocal
exit /b