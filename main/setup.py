#!/usr/bin/env python3
"""
CrazeDyn Panel Setup Script
Interactive installer to choose between Web and Desktop versions
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🎮 CrazeDyn Panel - Minecraft Server Manager")
    print("=" * 60)
    print("🚀 Interactive Setup & Launcher")
    print()

def print_options():
    """Print available options"""
    print("📋 Choose your installation type:")
    print()
    print("1. 🌐 Web Panel Only")
    print("   • Access from any device on your network")
    print("   • Modern responsive interface")
    print("   • Works on phones, tablets, computers")
    print("   • Lightweight installation")
    print()
    print("2. 🖥️  Desktop GUI Only") 
    print("   • Traditional desktop application")
    print("   • Full PyQt6 interface")
    print("   • Local Windows application")
    print("   • Complete offline functionality")
    print()
    print("3. 🔧 Full Installation")
    print("   • Both Web and Desktop versions")
    print("   • Maximum flexibility")
    print("   • All features available")
    print()
    print("4. ▶️  Quick Launch (skip setup)")
    print("   • Launch with existing installation")
    print("   • Choose Web or Desktop mode")
    print()

def install_dependencies(dep_type):
    """Install dependencies based on type"""
    print(f"📦 Installing {dep_type} dependencies...")
    
    # Base requirements for all installations
    base_reqs = [
        "psutil>=5.9.0",
        "requests>=2.31.0"
    ]
    
    # Web-specific requirements
    web_reqs = [
        "flask>=3.0.0", 
        "flask-socketio>=5.3.0",
        "gunicorn>=21.0.0",
        "gevent>=23.0.0"
    ]
    
    # Desktop-specific requirements  
    desktop_reqs = [
        "pyqt6>=6.9.1"
    ]
    
    # Optional requirements
    optional_reqs = [
        "miniupnpc>=2.2.2"
    ]
    
    # Build requirements
    build_reqs = [
        "pyinstaller>=6.15.0"
    ]
    
    # Select requirements based on type
    requirements = base_reqs.copy()
    
    if dep_type in ["web", "full"]:
        requirements.extend(web_reqs)
        
    if dep_type in ["desktop", "full"]:
        requirements.extend(desktop_reqs)
        
    if dep_type == "full":
        requirements.extend(optional_reqs)
        requirements.extend(build_reqs)
    
    # Install each requirement
    for req in requirements:
        try:
            print(f"  Installing {req}...")
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                          check=True, capture_output=True)
            print(f"  ✅ {req}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install {req}: {e}")
            return False
    
    print(f"✅ {dep_type.title()} dependencies installed successfully!")
    return True

def quick_launch():
    """Quick launch existing installation"""
    print("⚡ Quick Launch Mode")
    print()
    print("Choose launch mode:")
    print("1. 🌐 Web Panel")
    print("2. 🖥️  Desktop GUI")
    print()
    
    while True:
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == "1":
            print("🌐 Starting Web Panel...")
            os.system(f"{sys.executable} launcher.py --web")
            break
        elif choice == "2":
            print("🖥️ Starting Desktop GUI...")
            os.system(f"{sys.executable} launcher.py --desktop")
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

def main():
    """Main setup function"""
    print_banner()
    print_options()
    
    while True:
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            # Web Panel Only
            print("\n🌐 Setting up Web Panel...")
            if install_dependencies("web"):
                print("\n✅ Web Panel setup complete!")
                print("\n🚀 To start the web panel, run:")
                print(f"   {sys.executable} launcher.py --web")
                print("\n🌐 Then open your browser to: http://localhost:5000")
            break
            
        elif choice == "2":
            # Desktop GUI Only
            print("\n🖥️ Setting up Desktop GUI...")
            if install_dependencies("desktop"):
                print("\n✅ Desktop GUI setup complete!")
                print("\n🚀 To start the desktop app, run:")
                print(f"   {sys.executable} launcher.py --desktop")
                print(f"   or: {sys.executable} app/__main__.py")
            break
            
        elif choice == "3":
            # Full Installation
            print("\n🔧 Setting up Full Installation...")
            if install_dependencies("full"):
                print("\n✅ Full installation complete!")
                print("\n🚀 Launch options:")
                print(f"   Web Panel:   {sys.executable} launcher.py --web")
                print(f"   Desktop GUI: {sys.executable} launcher.py --desktop")
                print("\n🌐 Web Panel: http://localhost:5000")
            break
            
        elif choice == "4":
            # Quick Launch
            quick_launch()
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
    
    print("\n" + "=" * 60)
    print("🎮 CrazeDyn Panel Setup Complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)