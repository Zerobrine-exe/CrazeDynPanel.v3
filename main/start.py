#!/usr/bin/env python3
"""
CrazeDynPanel v2.0 - Automated Installer & Launcher
Professional Minecraft Server Manager Setup
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Display the welcome banner"""
    print("\033[93m")  # Yellow text
    print("=" * 80)
    print()
    print("   ____                     ____              ____              __")
    print("  / ___|__ _ __ __ _ ____   |  _ \ _   _ _ __  |  _ \ __ _ _ __   ___| |")
    print(" | |   / _` |  __/ _` |_  /  | | | | | | | | | |_| |/ _` | '_ \ / _ \ |")
    print(" | |__| (_| | | | (_| |/ /   | |_| | |_| | | |  __/ (_| | | | |  __/ |")
    print("  \____\__,_|_|  \__,_/___|  |____/ \__, |_|  |_|  \__,_|_| |_|\___|_|")
    print("                                  |___/")
    print()
    print("              🎮 Professional Minecraft Server Manager 🎮")
    print("                        💼 Enterprise Edition v2.0 💼")
    print()
    print("=" * 80)
    print("\033[0m")  # Reset color

def get_install_location():
    """Ask user for installation location"""
    print("\n📍 CHOOSE INSTALLATION LOCATION")
    print("=" * 50)
    print()
    print("1. Default Location: C:/CrazeDynPanel")
    print("2. Program Files: C:/Program Files/CrazeDynPanel")
    print("3. Documents:", Path.home() / "Documents" / "CrazeDynPanel")
    print("4. Desktop:", Path.home() / "Desktop" / "CrazeDynPanel")
    print("5. Custom Location (specify your own path)")
    print()
    
    while True:
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            return Path("C:/CrazeDynPanel")
        elif choice == "2":
            return Path("C:/Program Files/CrazeDynPanel")
        elif choice == "3":
            return Path.home() / "Documents" / "CrazeDynPanel"
        elif choice == "4":
            return Path.home() / "Desktop" / "CrazeDynPanel"
        elif choice == "5":
            custom_path = input("Enter full path for installation: ").strip()
            return Path(custom_path)
        else:
            print("❌ Invalid choice! Please select 1-5.")

def get_install_mode():
    """Ask user for installation mode"""
    print("\n🎯 CHOOSE APPLICATION MODE")
    print("=" * 50)
    print()
    print("1. 🖥️  Desktop GUI Mode")
    print("   • Beautiful PyQt6 desktop application")
    print("   • Perfect for local server management")
    print("   • Full-featured GUI with real-time monitoring")
    print()
    print("2. 🌐 Web Panel Mode")
    print("   • Modern web-based control panel")
    print("   • Access from any device (phone, tablet, computer)")
    print("   • Professional authentication system")
    print()
    print("3. 🔗 Both Modes (Recommended)")
    print("   • Install both desktop and web versions")
    print("   • Complete flexibility")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            return "desktop", "Desktop GUI"
        elif choice == "2":
            return "web", "Web Panel"
        elif choice == "3":
            return "both", "Both Desktop & Web"
        else:
            print("❌ Invalid choice! Please select 1-3.")

def copy_files(source_dir, target_dir):
    """Copy all Main files to target directory"""
    print(f"\n📋 COPYING FILES")
    print("=" * 50)
    print()
    
    # Create target directory
    print(f"📁 Creating directory: {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all files
    print(f"📦 Copying files from: {source_dir}")
    print(f"📦 Copying files to: {target_dir}")
    
    for item in source_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, target_dir / item.name)
            print(f"✅ Copied: {item.name}")
        elif item.is_dir() and item.name not in ['.git', '__pycache__', '.pytest_cache']:
            shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
            print(f"✅ Copied folder: {item.name}")
    
    print("✅ All files copied successfully!")

def create_launchers(install_path, mode):
    """Create launcher scripts"""
    print(f"\n📋 CREATING LAUNCHERS")
    print("=" * 50)
    
    if mode in ["desktop", "both"]:
        # Desktop launcher
        if platform.system() == "Windows":
            desktop_bat = install_path / "Start_Desktop.bat"
            with open(desktop_bat, 'w') as f:
                f.write(f"""@echo off
title CrazeDynPanel v2.0 - Desktop Mode
cd /d "{install_path}"
python launcher.py
pause""")
            print("✅ Desktop launcher created: Start_Desktop.bat")
        else:
            desktop_sh = install_path / "start_desktop.sh"
            with open(desktop_sh, 'w') as f:
                f.write(f"""#!/bin/bash
cd "{install_path}"
python3 launcher.py
read -p "Press Enter to exit..."
""")
            desktop_sh.chmod(0o755)
            print("✅ Desktop launcher created: start_desktop.sh")
    
    if mode in ["web", "both"]:
        # Web launcher
        if platform.system() == "Windows":
            web_bat = install_path / "Start_Web.bat"
            with open(web_bat, 'w') as f:
                f.write(f"""@echo off
title CrazeDynPanel v2.0 - Web Panel
cd /d "{install_path}"
python launcher.py --web
pause""")
            print("✅ Web launcher created: Start_Web.bat")
        else:
            web_sh = install_path / "start_web.sh"
            with open(web_sh, 'w') as f:
                f.write(f"""#!/bin/bash
cd "{install_path}"
python3 launcher.py --web
read -p "Press Enter to exit..."
""")
            web_sh.chmod(0o755)
            print("✅ Web launcher created: start_web.sh")

def install_dependencies(install_path, mode):
    """Install required dependencies"""
    print(f"\n📦 INSTALLING DEPENDENCIES")
    print("=" * 50)
    print()
    
    # Check Python
    print("🔍 Checking Python installation...")
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✅ Python found: {result.stdout.strip()}")
    except Exception:
        print("❌ Python not found!")
        return False
    
    # Create requirements based on mode
    requirements = [
        "psutil",
        "requests", 
        "flask",
        "flask-socketio",
        "gunicorn",
        "bcrypt"
    ]
    
    if mode in ["desktop", "both"]:
        requirements.append("pyqt6")
    
    # Install packages
    print("📦 Installing required packages...")
    print("This may take a few minutes...")
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=False, capture_output=True)
        
        # Install each package
        for package in requirements:
            print(f"📦 Installing {package}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"⚠️ {package} installation failed, but continuing...")
        
        print("✅ Dependencies installation completed!")
        return True
        
    except Exception as e:
        print(f"⚠️ Some dependencies may have failed: {e}")
        print("The application may still work with limited features.")
        return False

def show_completion_info(install_path, mode, mode_name):
    """Show completion information"""
    print("\n🎉 INSTALLATION COMPLETE!")
    print("=" * 50)
    print()
    print(f"📍 Installation Location: {install_path}")
    print(f"🎯 Mode: {mode_name}")
    print()
    print("🚀 HOW TO START:")
    print("=" * 30)
    
    if mode == "desktop":
        if platform.system() == "Windows":
            print(f"• Double-click: {install_path}/Start_Desktop.bat")
        else:
            print(f"• Run: {install_path}/start_desktop.sh")
        print(f"• Or run: python launcher.py (from {install_path})")
    
    elif mode == "web":
        if platform.system() == "Windows":
            print(f"• Double-click: {install_path}/Start_Web.bat")
        else:
            print(f"• Run: {install_path}/start_web.sh")
        print(f"• Or run: python launcher.py --web (from {install_path})")
        print("• Then visit: http://localhost:5000 in your browser")
    
    elif mode == "both":
        print("Desktop Mode:")
        if platform.system() == "Windows":
            print(f"  • Double-click: {install_path}/Start_Desktop.bat")
        else:
            print(f"  • Run: {install_path}/start_desktop.sh")
        print()
        print("Web Panel Mode:")
        if platform.system() == "Windows":
            print(f"  • Double-click: {install_path}/Start_Web.bat")
        else:
            print(f"  • Run: {install_path}/start_web.sh")
        print("  • Then visit: http://localhost:5000 in your browser")
    
    print()
    print("🎮 FEATURES:")
    print("=" * 30)
    print("• Create and manage Minecraft servers")
    print("• Playit.gg integration for worldwide access")
    print("• Modern UI with professional authentication")
    print("• Real-time monitoring and console access")
    print()
    print("🔗 SUPPORT:")
    print("=" * 30)
    print("💬 Discord: https://dc.gg/zerocloud")
    print("📺 YouTube: https://www.youtube.com/@Zerobrine_7")
    print()

def main():
    """Main installer function"""
    # Check if we're running from the right directory
    current_dir = Path.cwd()
    if not (current_dir / "launcher.py").exists():
        print("❌ Please run this installer from the Main directory!")
        print(f"Current directory: {current_dir}")
        print("Expected file: launcher.py")
        input("Press Enter to exit...")
        return
    
    print_banner()
    
    print("🚀 AUTOMATED INSTALLER")
    print("=" * 50)
    print()
    print("This installer will:")
    print("• Ask for your preferred installation location")
    print("• Let you choose between Desktop GUI or Web Panel mode")
    print("• Copy all necessary files to your chosen location")
    print("• Automatically download and install all dependencies")
    print("• Set up everything ready to use!")
    print()
    input("Press Enter to continue...")
    
    # Get installation preferences
    install_path = get_install_location()
    mode, mode_name = get_install_mode()
    
    print(f"\n📂 Selected installation path: {install_path}")
    print(f"🎯 Selected mode: {mode_name}")
    confirm = input("\nIs this correct? (Y/N): ").strip().lower()
    if confirm != 'y':
        print("Installation cancelled.")
        return
    
    # Handle existing installation
    if install_path.exists():
        print(f"\n⚠️ Directory already exists: {install_path}")
        overwrite = input("Overwrite existing installation? (Y/N): ").strip().lower()
        if overwrite != 'y':
            print("Installation cancelled.")
            return
        print("🗑️ Removing existing files...")
        shutil.rmtree(install_path, ignore_errors=True)
    
    try:
        # Copy files
        copy_files(current_dir, install_path)
        
        # Create launchers
        create_launchers(install_path, mode)
        
        # Install dependencies
        install_dependencies(install_path, mode)
        
        # Show completion info
        show_completion_info(install_path, mode, mode_name)
        
        # Offer to start immediately
        start_now = input("Would you like to start CrazeDynPanel now? (Y/N): ").strip().lower()
        if start_now == 'y':
            if mode == "desktop":
                if platform.system() == "Windows":
                    subprocess.Popen([str(install_path / "Start_Desktop.bat")], shell=True)
                else:
                    subprocess.Popen([str(install_path / "start_desktop.sh")])
            elif mode == "web":
                if platform.system() == "Windows":
                    subprocess.Popen([str(install_path / "Start_Web.bat")], shell=True)
                else:
                    subprocess.Popen([str(install_path / "start_web.sh")])
                # Open browser
                import webbrowser
                webbrowser.open("http://localhost:5000")
            else:  # both
                choice = input("Start Desktop (1) or Web Panel (2)? Enter choice: ").strip()
                if choice == "1":
                    if platform.system() == "Windows":
                        subprocess.Popen([str(install_path / "Start_Desktop.bat")], shell=True)
                    else:
                        subprocess.Popen([str(install_path / "start_desktop.sh")])
                elif choice == "2":
                    if platform.system() == "Windows":
                        subprocess.Popen([str(install_path / "Start_Web.bat")], shell=True)
                    else:
                        subprocess.Popen([str(install_path / "start_web.sh")])
                    import webbrowser
                    webbrowser.open("http://localhost:5000")
        
        print("\n🎯 Thank you for choosing CrazeDynPanel v2.0! 🎮")
        
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        print("Please check permissions and try again.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()