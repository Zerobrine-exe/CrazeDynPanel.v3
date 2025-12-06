#!/usr/bin/env python3
"""
CrazeDyn Panel - Command Line Installer
Minecraft Server Manager Installation with Plugin Pack Support
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add the app directory to Python path
installer_dir = Path(__file__).parent
app_dir = installer_dir / "app"
sys.path.insert(0, str(app_dir))

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the installer banner"""
    print("=" * 70)
    print("🎮 CrazeDyn Panel - Minecraft Server Manager Installer")
    print("=" * 70)
    print()

def get_server_config() -> dict:
    """Get server configuration from user input"""
    config = {}
    
    print("📋 Server Configuration")
    print("-" * 30)
    
    # Server name
    while True:
        name = input("🏷️  Server name: ").strip()
        if name:
            config['name'] = name
            break
        print("❌ Server name cannot be empty!")
    
    # Minecraft version
    print("\n🔧 Available Minecraft versions:")
    versions = ["1.21.8", "1.21.7", "1.21.6", "1.21.5", "1.21.4", "1.20.6", "1.20.4", "1.19.4"]
    for i, version in enumerate(versions, 1):
        print(f"   {i}. {version}")
    
    while True:
        try:
            choice = input(f"\n📦 Select version (1-{len(versions)}) [1]: ").strip()
            if not choice:
                choice = "1"
            index = int(choice) - 1
            if 0 <= index < len(versions):
                config['version'] = versions[index]
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(versions)}")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # RAM configuration
    print("\n💾 Memory Configuration")
    while True:
        try:
            min_ram = input("📉 Minimum RAM (GB) [2]: ").strip()
            if not min_ram:
                min_ram = "2"
            min_ram_val = int(min_ram)
            if min_ram_val > 0:
                config['min_ram'] = f"{min_ram_val}G"
                break
            else:
                print("❌ RAM must be greater than 0")
        except ValueError:
            print("❌ Please enter a valid number")
    
    while True:
        try:
            max_ram = input("📈 Maximum RAM (GB) [4]: ").strip()
            if not max_ram:
                max_ram = "4"
            max_ram_val = int(max_ram)
            min_ram_val = int(config['min_ram'][:-1])  # Remove 'G'
            if max_ram_val >= min_ram_val:
                config['max_ram'] = f"{max_ram_val}G"
                break
            else:
                print(f"❌ Maximum RAM must be >= {min_ram_val}G")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Server port
    while True:
        try:
            port = input("🔌 Server port [25565]: ").strip()
            if not port:
                port = "25565"
            port_val = int(port)
            if 1024 <= port_val <= 65535:
                config['port'] = port_val
                break
            else:
                print("❌ Port must be between 1024 and 65535")
        except ValueError:
            print("❌ Please enter a valid port number")
    
    # Storage path
    default_path = str(installer_dir / "servers")
    storage_path = input(f"📁 Storage path [{default_path}]: ").strip()
    if not storage_path:
        storage_path = default_path
    config['path'] = storage_path
    
    return config

def main():
    """Main installer function"""
    try:
        clear_screen()
        print_banner()
        
        print("🔍 Checking dependencies...")
        
        # Import and initialize downloader
        try:
            from core.downloader import PaperMCDownloader, DependencyChecker
            from core.server_manager import ServerManager
        except ImportError:
            print("❌ Failed to import core modules. Make sure you're running from the correct directory.")
            sys.exit(1)
        
        downloader = PaperMCDownloader()
        
        # Check Java
        print("☕ Checking Java installation...")
        java_check = DependencyChecker.check_java()
        if not java_check['installed'] or not java_check['compatible']:
            print("❌ Java 17+ is required but not found!")
            print("   Please install Java 17+ from: https://adoptium.net/")
            sys.exit(1)
        else:
            print(f"✅ Java {java_check['version']} found")
        
        print("\n" + "=" * 70)
        print("📦 CREATE NEW MINECRAFT SERVER")
        print("=" * 70)
        
        # Get server configuration
        config = get_server_config()
        
        print("\n" + "=" * 50)
        print("📋 Configuration Summary")
        print("=" * 50)
        print(f"🏷️  Name: {config['name']}")
        print(f"📦 Version: {config['version']}")
        print(f"💾 RAM: {config['min_ram']} - {config['max_ram']}")
        print(f"🔌 Port: {config['port']}")
        print(f"📁 Path: {config['path']}")
        
        # Confirm creation
        print("\n❓ Create server with these settings? (y/n): ", end="")
        if input().strip().lower() not in ['y', 'yes']:
            print("❌ Server creation cancelled.")
            return
        
        # Create server manager and server
        print("\n🏗️  Creating server...")
        server_manager = ServerManager()
        
        success = server_manager.create_server(
            name=config['name'],
            version=config['version'],
            min_ram=config['min_ram'],
            max_ram=config['max_ram'],
            storage_path=config['path'],
            port=config['port']
        )
        
        if not success:
            print("❌ Failed to create server!")
            return
        
        print("✅ Server created successfully!")
        
        # Download server files
        print("\n📥 Downloading server files...")
        server = server_manager.servers[config['name']]
        server_path = Path(server.path)
        
        if not downloader.download_server_files(config['version'], server_path):
            print("❌ Failed to download server files!")
            return
        
        print("✅ Server files downloaded!")
        
        # Ask about plugin pack installation
        install_plugins = PaperMCDownloader.ask_install_plugin_pack()
        
        if install_plugins:
            plugins_path = server_path / "plugins"
            print("\n🔄 Starting plugin pack download...")
            
            plugin_results = downloader.download_basic_plugin_pack(plugins_path)
            
            # Check results
            successful_plugins = sum(1 for success in plugin_results.values() if success)
            total_plugins = len(plugin_results)
            
            if successful_plugins == total_plugins:
                print("\n🎉 All plugins downloaded successfully!")
            elif successful_plugins > 0:
                print(f"\n⚠️  {successful_plugins}/{total_plugins} plugins downloaded successfully.")
                print("   Some plugins failed to download - check your internet connection.")
            else:
                print("\n❌ Plugin pack download failed!")
                print("   You can manually download plugins later from the management interface.")
        else:
            print("\n⏭️  Plugin installation skipped.")
        
        # Final message
        print("\n" + "🎉" * 25)
        print("SERVER INSTALLATION COMPLETE!")
        print("🎉" * 25)
        print(f"\n📍 Server location: {server_path}")
        print(f"🔗 Connection: localhost:{config['port']}")
        print("\n🚀 To start your server:")
        print("   1. Run the CrazeDyn Panel application")
        print("   2. Click the 'Start' button on your server")
        print("   3. Wait for startup to complete")
        print("   4. Connect with your Minecraft client!")
        
        if install_plugins:
            print("\n📝 Plugin Pack Notes:")
            print("   • GeyserMC enables Bedrock Edition clients to connect")
            print("   • Floodgate removes the need for Bedrock players to have Java accounts")
            print("   • EssentialsX provides essential server commands like /home, /warp")
            print("   • ViaVersion enables newer clients to connect to older servers")
            print("   • ServerNaptime hibernates the server when no players are online")
            print("\n⚠️  Note: GeyserMC and Floodgate may require manual setup if automatic configuration cannot be applied.")
        
        print(f"\n🎮 Happy gaming with {config['name']}!")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Installation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {str(e)}")
        print("   Please check your internet connection and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()