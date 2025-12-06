@echo off
echo ================================================
echo  CrazeDyn Panel - Portable Build Script
echo ================================================
echo.

REM This script creates a portable version that includes Python

echo [STEP 1] Checking requirements...
echo.

if not exist "app\__main__.py" (
    echo [ERROR] Must be run from Main directory
    pause
    exit /b 1
)

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [OK] Requirements met

echo.
echo [STEP 2] Creating portable directory structure...
echo.

if exist "portable" rmdir /s /q "portable"
mkdir "portable"
mkdir "portable\app"
mkdir "portable\servers"
mkdir "portable\python"

echo [OK] Directory structure created

echo.
echo [STEP 3] Copying application files...
echo.

xcopy "app" "portable\app" /E /I /Y
copy "servers.json" "portable\" >nul 2>&1
copy "paper_versions.json" "portable\" >nul 2>&1

echo [OK] Application files copied

echo.
echo [STEP 4] Building with PyInstaller (directory mode)...
echo.

pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name crazeDynPanel ^
    --add-data "app;app" ^
    --add-data "paper_versions.json;." ^
    --distpath="portable" ^
    app\__main__.py

if %errorLevel% neq 0 (
    echo [ERROR] PyInstaller failed
    pause
    exit /b 1
)

echo [OK] Portable build created

echo.
echo [STEP 5] Creating launcher scripts...
echo.

REM Create portable launcher
echo @echo off > portable\CrazeDynPanel.bat
echo cd /d "%%~dp0" >> portable\CrazeDynPanel.bat
echo echo Starting CrazeDyn Panel (Portable)... >> portable\CrazeDynPanel.bat
echo start "" "crazeDynPanel\crazeDynPanel.exe" >> portable\CrazeDynPanel.bat

REM Create installer
echo @echo off > portable\Install.bat
echo echo CrazeDyn Panel - Dependency Installer >> portable\Install.bat
echo echo. >> portable\Install.bat
echo echo This will install Java 17 and setup firewall rules >> portable\Install.bat
echo echo Administrator privileges required >> portable\Install.bat
echo echo. >> portable\Install.bat
echo pause >> portable\Install.bat
echo echo. >> portable\Install.bat
echo echo [1/2] Installing Java 17... >> portable\Install.bat
echo winget install -e --id Microsoft.OpenJDK.17 --accept-package-agreements >> portable\Install.bat
echo echo. >> portable\Install.bat
echo echo [2/2] Setting up firewall rules... >> portable\Install.bat
echo netsh advfirewall firewall add rule name="CrazeDyn Minecraft" dir=in action=allow protocol=TCP localport=25565 >> portable\Install.bat
echo netsh advfirewall firewall add rule name="CrazeDyn Minecraft Range" dir=in action=allow protocol=TCP localport=25560-25580 >> portable\Install.bat
echo echo. >> portable\Install.bat
echo echo Setup complete! You can now run CrazeDynPanel.bat >> portable\Install.bat
echo pause >> portable\Install.bat

echo [OK] Launcher scripts created

echo.
echo [STEP 6] Creating README...
echo.

echo # CrazeDyn Panel - Portable Edition > portable\README.txt
echo. >> portable\README.txt
echo ## Quick Start >> portable\README.txt
echo 1. Run Install.bat as Administrator (first time only) >> portable\README.txt
echo 2. Run CrazeDynPanel.bat to start the application >> portable\README.txt
echo. >> portable\README.txt
echo ## What's Included >> portable\README.txt
echo - CrazeDynPanel.exe and dependencies >> portable\README.txt
echo - Python runtime (embedded) >> portable\README.txt
echo - All required libraries >> portable\README.txt
echo. >> portable\README.txt
echo ## Features >> portable\README.txt
echo - Create and manage Minecraft servers >> portable\README.txt
echo - Auto-download PaperMC versions >> portable\README.txt
echo - Playit.gg plugin auto-install >> portable\README.txt
echo - System monitoring and console viewer >> portable\README.txt
echo - Port forwarding and network setup >> portable\README.txt
echo. >> portable\README.txt
echo ## Troubleshooting >> portable\README.txt
echo - Make sure Java 17+ is installed >> portable\README.txt
echo - Run as Administrator for firewall setup >> portable\README.txt
echo - Check Windows Defender exceptions if needed >> portable\README.txt
echo. >> portable\README.txt
echo ## Support >> portable\README.txt
echo Visit: https://github.com/crazeDyn/panel >> portable\README.txt

echo [OK] README created

echo.
echo [STEP 7] Build complete!
echo.
echo ================================================
echo           PORTABLE BUILD SUCCESSFUL!
echo ================================================
echo.
echo Created: portable\
echo ├── crazeDynPanel\          (Application directory)
echo ├── app\                    (Source code)
echo ├── servers\                (Server storage)
echo ├── CrazeDynPanel.bat       (Main launcher)
echo ├── Install.bat             (Dependency installer)
echo └── README.txt              (Instructions)
echo.
echo To distribute:
echo 1. Zip the entire 'portable' folder
echo 2. User extracts and runs Install.bat as admin
echo 3. User runs CrazeDynPanel.bat to use the application
echo.
echo Portable build is completely self-contained!
echo.
pause