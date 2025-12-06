@echo off
echo ===============================================
echo    CrazeDyn Panel - Windows Build Script
echo ===============================================
echo.

REM Check if we're in the correct directory
if not exist "app\__main__.py" (
    echo [ERROR] Build script must be run from the Main directory
    echo Current directory should contain app\__main__.py
    pause
    exit /b 1
)

echo [STEP 1] Checking Python installation...
echo.

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and ensure it's in your PATH
    pause
    exit /b 1
)

echo [OK] Python found

echo.
echo [STEP 2] Installing/updating required packages...
echo.

python -m pip install --upgrade pip
python -m pip install PyQt6 requests psutil pyinstaller

if %errorLevel% neq 0 (
    echo [ERROR] Failed to install required packages
    echo Please check your internet connection and Python installation
    pause
    exit /b 1
)

echo [OK] Packages installed

echo.
echo [STEP 3] Cleaning previous build...
echo.

if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [OK] Cleaned previous build files

echo.
echo [STEP 4] Building executable with PyInstaller...
echo.

REM Build the main executable
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name crazeDynPanel ^
    --add-data "app;app" ^
    --add-data "paper_versions.json;." ^
    --icon="icon.ico" ^
    --distpath="." ^
    app\__main__.py

if %errorLevel% neq 0 (
    echo [ERROR] PyInstaller build failed
    echo Check the output above for details
    pause
    exit /b 1
)

echo [OK] Executable built successfully

echo.
echo [STEP 5] Verifying build...
echo.

if exist "crazeDynPanel.exe" (
    echo [OK] crazeDynPanel.exe created successfully
    
    REM Get file size
    for %%A in (crazeDynPanel.exe) do set size=%%~zA
    set /a size_mb=size/1024/1024
    echo [INFO] Executable size: %size_mb% MB
    
) else (
    echo [ERROR] crazeDynPanel.exe was not created
    pause
    exit /b 1
)

echo.
echo [STEP 6] Creating additional files...
echo.

REM Create run.bat launcher
echo @echo off > run.bat
echo echo Starting CrazeDyn Panel... >> run.bat
echo start "" "crazeDynPanel.exe" >> run.bat

REM Create install.bat for dependencies
echo @echo off > install.bat
echo echo Installing dependencies for CrazeDyn Panel... >> install.bat
echo echo. >> install.bat
echo echo [INFO] Installing Java 17... >> install.bat
echo winget install -e --id Microsoft.OpenJDK.17 --accept-package-agreements --accept-source-agreements >> install.bat
echo echo. >> install.bat
echo echo [INFO] Adding firewall rules... >> install.bat
echo netsh advfirewall firewall add rule name="Minecraft Server Default" dir=in action=allow protocol=TCP localport=25565 >> install.bat
echo netsh advfirewall firewall add rule name="Minecraft Server Range" dir=in action=allow protocol=TCP localport=25560-25580 >> install.bat
echo echo. >> install.bat
echo echo Dependencies installed successfully! >> install.bat
echo pause >> install.bat

echo [OK] Additional files created

echo.
echo [STEP 7] Build complete!
echo.
echo ===============================================
echo              BUILD SUCCESSFUL!
echo ===============================================
echo.
echo Created files:
echo - crazeDynPanel.exe (Main executable)
echo - run.bat (Quick launcher)  
echo - install.bat (Install dependencies)
echo - CDPanel.bat (Alternative launcher)
echo.
echo Distribution contents:
if exist "crazeDynPanel.exe" dir "crazeDynPanel.exe"
echo.
echo To distribute:
echo 1. Copy crazeDynPanel.exe to target computer
echo 2. Run install.bat as Administrator (first time only)
echo 3. Run crazeDynPanel.exe or use run.bat
echo.
echo For development:
echo - Use CDPanel.bat to run Python version
echo - Use crazeDynPanel.exe for release version
echo.
pause