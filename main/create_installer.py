#!/usr/bin/env python3
"""
CrazeDyn Panel - Installer Creator
Creates a self-contained installer executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_installer():
    """Create a self-contained installer executable"""
    print("🔧 Creating CrazeDyn Panel Installer...")
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Create installer script
    installer_script = """
import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

# Embedded project files would go here in a real installer
# For now, we'll assume the files are in the same directory

def extract_and_run():
    '''Extract project files and run setup'''
    # This would extract embedded files in a real installer
    # For demonstration, we'll use the current directory
    current_dir = Path(__file__).parent
    
    # Run the setup batch file
    setup_bat = current_dir / "setup_windows.bat"
    if setup_bat.exists():
        subprocess.run([str(setup_bat)], shell=True)
    else:
        print("Setup file not found!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    extract_and_run()
"""
    
    # Write installer script
    with open("installer_main.py", "w") as f:
        f.write(installer_script)
    
    # Create the installer executable
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console", 
        "--name", "CrazeDynPanel_Installer",
        "--distpath", ".",
        "installer_main.py"
    ]
    
    print("Building installer executable...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Installer created: CrazeDynPanel_Installer.exe")
        
        # Cleanup
        if os.path.exists("installer_main.py"):
            os.remove("installer_main.py")
        if os.path.exists("CrazeDynPanel_Installer.spec"):
            os.remove("CrazeDynPanel_Installer.spec")
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
            
        print("\n🎯 Usage:")
        print("1. Copy CrazeDynPanel_Installer.exe and setup_windows.bat to target machine")
        print("2. Run CrazeDynPanel_Installer.exe")
        print("3. Follow the installation prompts")
        
    else:
        print("❌ Error creating installer:")
        print(result.stderr)
        return False
    
    return True

if __name__ == "__main__":
    create_installer()