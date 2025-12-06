#!/usr/bin/env python3
"""
CrazeDyn Panel - Unified Launcher
One command to rule them all!
"""

import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def install_requirements():
    """Install required packages if not available"""
    required_packages = [
        'flask',
        'flask-socketio',
        'psutil',
        'requests',
        'pyqt6'  # Keep for fallback compatibility
    ]
    
    print("🔍 Checking dependencies...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    
    print("✅ All dependencies ready!")
    return True

def get_local_ip():
    """Get local IP address"""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except:
        return '127.0.0.1'

def check_port_available(port):
    """Check if port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False

def start_web_panel():
    """Start the web panel"""
    try:
        # Import after ensuring dependencies are installed
        from web_panel.app import app, socketio, perf_monitor
        
        # Start performance monitoring
        perf_monitor.start()
        
        # Use fixed port 5000 (required for Replit webview)
        port = 5000
        if not check_port_available(port):
            print(f"⚠️ Port {port} is busy, attempting to start anyway...")
            print("💡 If startup fails, another service may be using this port")
        
        local_ip = get_local_ip()
        
        print("\n" + "🚀" * 25)
        print("🌐 CrazeDynPanel v2.0 - Web Interface")
        print("🚀" * 60)
        print(f"📱 Local Access:     http://localhost:{port}")
        print(f"🌐 Network Access:   http://{local_ip}:{port}")
        print(f"📡 LAN Access:       http://{local_ip}:{port}")
        print("🚀" * 60)
        print("✨ Premium Features Available:")
        print("   • Real-time server monitoring & analytics")
        print("   • Remote server management with console")
        print("   • Advanced plugin management system")
        print("   • Paper & Spigot server support")
        print("   • Modern responsive UI with icons")
        print("   • Multi-device optimized interface")
        print("   • Premium themes & customization")
        print("🚀" * 60)
        print("🎯 Access from ANY device on your network!")
        print("📱 Works perfectly on phones, tablets, and computers")
        print("🔗 Discord: https://dc.gg/zerocloud")
        print("📺 YouTube: https://www.youtube.com/@Zerobrine_7") 
        print("🚀" * 60)
        
        # Disable Flask access logging to prevent console spam
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # Run the web server
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=port, 
            debug=False, 
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error starting web panel: {e}")
        return False

def start_legacy_gui():
    """Start the legacy PyQt6 GUI as fallback"""
    try:
        print("🔄 Starting legacy desktop interface...")
        from app.__main__ import main
        main()
    except Exception as e:
        print(f"❌ Error starting legacy GUI: {e}")
        return False

def print_v2_header():
    """Print the stylish v2.0 header with branding"""
    print("\n" + "🌟" * 25)
    print("🎮 CrazeDynPanel v2.0 – Made by Zerobrine")
    print("🌟" * 60) 
    print("🎯 Ultimate Minecraft Server Manager & Control Panel")
    print("💼 Professional Edition with Premium Features")
    print("🌟" * 60)
    print("🔗 Join our Discord: https://dc.gg/zerocloud")
    print("📺 Subscribe on YouTube: https://www.youtube.com/@Zerobrine_7")
    print("🌟" * 60)
    print("✨ New in v2.0:")
    print("   • Modern Icon-Based Interface")
    print("   • Paper & Spigot Server Support")
    print("   • Premium Plugin Management")
    print("   • Enhanced Search & Filtering")
    print("   • Custom Themes & UI")
    print("🌟" * 60 + "\n")

def main():
    """Main launcher function"""
    print_v2_header()
    
    # Check command line arguments first
    mode = None
    production = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--desktop', '-d']:
            mode = "desktop"
        elif sys.argv[1] in ['--web', '-w']:
            mode = "web"
        elif sys.argv[1] in ['--production', '-p']:
            mode = "web"
            production = True
        elif sys.argv[1] in ['--setup', '-s']:
            print("🔧 Running interactive setup...")
            os.system(f"{sys.executable} setup.py")
            return 0
        elif sys.argv[1] in ['--help', '-h']:
            print("\nUsage:")
            print("  python launcher.py              # Interactive mode selection")
            print("  python launcher.py --web        # Start web panel (development)")
            print("  python launcher.py --desktop    # Start desktop app")
            print("  python launcher.py --production # Start web panel (production)")
            print("  python launcher.py --setup      # Run interactive setup")
            print("  python launcher.py --help       # Show this help")
            return 0
    
    # Interactive mode selection if no arguments provided
    if mode is None:
        print("\n📋 Choose launch mode:")
        print("1. 🌐 Web Panel (recommended)")
        print("2. 🖥️  Desktop GUI") 
        print("3. 🔧 Run Setup")
        print()
        
        while True:
            try:
                choice = input("Enter choice (1-3): ").strip()
                if choice == "1":
                    mode = "web"
                    break
                elif choice == "2":
                    mode = "desktop"
                    break
                elif choice == "3":
                    print("🔧 Running interactive setup...")
                    os.system(f"{sys.executable} setup.py")
                    return 0
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
            except KeyboardInterrupt:
                print("\n🛑 Cancelled by user.")
                return 0
    
    # Install dependencies
    if not install_requirements():
        print("❌ Failed to install dependencies")
        print("💡 Try running: python setup.py")
        return 1
    
    # Setup signal handling for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down CrazeDyn Panel...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if mode == "web":
            if production:
                print("🌐 Starting in PRODUCTION WEB mode...")
                # Start production server
                from start_production import main as start_production
                return start_production()
            else:
                print("🌐 Starting in WEB mode...")
                
                # Setup Playit.gg for remote access (optional)
                try:
                    from playit_manager import setup_playit_tunnels
                    setup_thread = threading.Thread(target=setup_playit_tunnels, daemon=True)
                    setup_thread.start()
                except Exception as e:
                    print(f"⚠️ Playit.gg setup failed: {e}")
                    print("📝 Playit.gg is optional - continuing without remote tunneling")
                
                start_web_panel()
        else:
            print("🖥️  Starting in DESKTOP mode...")
            start_legacy_gui()
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())