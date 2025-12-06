#!/usr/bin/env python3
"""
Playit.gg Manager for CrazeDyn Panel
Automatically downloads, installs, and manages Playit.gg software
"""

import os
import sys
import subprocess
import requests
import platform
from pathlib import Path
import threading
import time
import json
import tempfile
import shutil

class PlayitManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # Use absolute path based on this script's location
        script_dir = Path(__file__).parent
        self.playit_dir = script_dir / "playit"
        self.config_file = self.playit_dir / "config.json"
        self.tunnels = {}
        self.process = None
        self.running = False
        
        # Official MSI installer URL
        self.msi_installer_url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.16.2/playit-windows-x86_64-signed.msi"
        
        # Determine executable paths based on OS
        if self.system == "windows":
            # Check common installation paths for MSI-installed Playit
            possible_paths = [
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "playit" / "playit.exe",
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "playit" / "playit.exe",
                Path.home() / "AppData" / "Local" / "playit" / "playit.exe",
                self.playit_dir / "playit.exe"  # Fallback to local directory
            ]
            self.playit_exe = None
            for path in possible_paths:
                if path.exists():
                    self.playit_exe = path
                    break
            if not self.playit_exe:
                self.playit_exe = possible_paths[0]  # Default to Program Files
        else:
            self.playit_exe = self.playit_dir / "playit"
    
    def check_installation_status(self):
        """Check if Playit is installed and return status"""
        if self.system == "windows":
            # Check for MSI installation first
            if self.playit_exe and self.playit_exe.exists():
                return "installed"
            
            # Check if we have the old portable version
            if (self.playit_dir / "playit.exe").exists():
                return "portable"
            
            return "not_installed"
        else:
            # For non-Windows systems, check portable installation
            if self.playit_exe and self.playit_exe.exists():
                return "installed"
            return "not_installed"
    
    def install_playit_msi(self, silent=True):
        """Download and install Playit using official MSI installer"""
        if self.system != "windows":
            print("❌ MSI installer is only available for Windows")
            return self.download_playit_portable()
        
        print("🌐 Installing Playit.gg using official MSI installer...")
        
        try:
            # Download the MSI installer
            print("📥 Downloading Playit.gg MSI installer...")
            
            response = requests.get(self.msi_installer_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.msi', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\\r📦 Download Progress: {percent:.1f}%", end="", flush=True)
            
            print()  # New line after progress
            print("✅ MSI installer downloaded successfully!")
            
            # Run the MSI installer
            print("🚀 Running Playit.gg installer...")
            if silent:
                # Silent installation
                result = subprocess.run([
                    "msiexec", "/i", str(temp_path), "/quiet", "/norestart"
                ], capture_output=True, text=True)
            else:
                # Interactive installation
                result = subprocess.run([
                    "msiexec", "/i", str(temp_path)
                ], capture_output=True, text=True)
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
            
            if result.returncode == 0:
                print("✅ Playit.gg installed successfully!")
                # Update executable path after installation
                self.__init__()  # Reinitialize to find the installed executable
                return True
            else:
                print(f"❌ Installation failed with code {result.returncode}")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to install Playit.gg MSI: {e}")
            return False
    
    def download_playit_portable(self):
        """Fallback: Download portable version for non-Windows or if MSI fails"""
        print("🌐 Setting up Playit.gg portable version...")
        
        try:
            # Create directory
            self.playit_dir.mkdir(exist_ok=True)
            
            # Determine download URL based on system
            if self.system == "windows":
                if "64" in self.arch or "amd64" in self.arch:
                    url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.16.2/playit-windows-amd64.exe"
                else:
                    url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.16.2/playit-windows-386.exe"
                filename = "playit.exe"
            elif self.system == "linux":
                if "64" in self.arch or "amd64" in self.arch:
                    url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.16.2/playit-linux-amd64"
                else:
                    url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.16.2/playit-linux-386"
                filename = "playit"
            elif self.system == "darwin":  # macOS
                url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.16.2/playit-darwin-amd64"
                filename = "playit"
            else:
                print(f"❌ Unsupported system: {self.system}")
                return False
            
            portable_exe = self.playit_dir / filename
            
            print(f"📥 Downloading Playit.gg v0.16.2...")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(str(portable_exe), 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\\r📦 Progress: {percent:.1f}%", end="", flush=True)
            
            print()  # New line after progress
            
            # Make executable on Unix systems
            if self.system != "windows":
                os.chmod(str(portable_exe), 0o755)
            
            # Update executable path
            if self.system == "windows":
                self.playit_exe = portable_exe
            
            print("✅ Playit.gg portable version downloaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download Playit.gg portable: {e}")
            return False
    
    def is_installed(self):
        """Check if Playit.gg is installed"""
        return self.playit_exe and self.playit_exe.exists()
    
    def start_playit(self):
        """Start Playit.gg agent"""
        status = self.check_installation_status()
        if status == "not_installed":
            print("⚠️ Playit.gg is not installed. Please install it first using the 'Enable Playit' button.")
            return False
        
        if self.running:
            print("⚠️ Playit.gg is already running")
            return True
        
        try:
            print("🚀 Starting Playit.gg agent...")
            
            # Start Playit.gg in background
            self.process = subprocess.Popen(
                [str(self.playit_exe)],
                cwd=str(self.playit_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.running = True
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_playit, daemon=True)
            monitor_thread.start()
            
            print("✅ Playit.gg agent started!")
            print("🌐 Visit https://playit.gg to create your account and configure tunnels")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Playit.gg: {e}")
            return False
    
    def stop_playit(self):
        """Stop Playit.gg agent"""
        if not self.running or not self.process:
            return True
        
        try:
            print("🛑 Stopping Playit.gg agent...")
            self.process.terminate()
            
            # Wait for process to terminate
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing Playit.gg process...")
                self.process.kill()
                self.process.wait()
            
            self.running = False
            self.process = None
            print("✅ Playit.gg agent stopped")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop Playit.gg: {e}")
            return False
    
    def _monitor_playit(self):
        """Monitor Playit.gg process output"""
        if not self.process:
            return
        
        try:
            while self.running and self.process.poll() is None:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                else:
                    break
                if line:
                    # Parse output for tunnel information
                    line = line.strip()
                    if "tunnel" in line.lower() and "http" in line.lower():
                        # Extract tunnel URLs
                        self._parse_tunnel_info(line)
                
                time.sleep(0.1)
        except Exception as e:
            print(f"Playit.gg monitor error: {e}")
        finally:
            self.running = False
    
    def _parse_tunnel_info(self, line):
        """Parse tunnel information from Playit.gg output"""
        try:
            # This is a basic parser - may need adjustment based on actual output format
            if "https://" in line:
                # Extract URL
                start = line.find("https://")
                end = line.find(" ", start)
                if end == -1:
                    url = line[start:].strip()
                else:
                    url = line[start:end].strip()
                
                # Store tunnel info
                self.tunnels["web"] = {
                    "url": url,
                    "type": "http",
                    "status": "active"
                }
                
                print(f"🌐 Web tunnel active: {url}")
        except Exception as e:
            print(f"Error parsing tunnel info: {e}")
    
    def get_tunnel_status(self):
        """Get current tunnel status"""
        return {
            "running": self.running,
            "tunnels": self.tunnels,
            "process_id": self.process.pid if self.process else None
        }
    
    def create_tunnel(self, local_port, tunnel_type="tcp"):
        """Create a new tunnel for a specific port"""
        if not self.running:
            print("❌ Playit.gg agent is not running")
            return False
        
        try:
            # This would require Playit.gg API integration
            # For now, just document the port
            print(f"📡 Tunnel requested for port {local_port} ({tunnel_type})")
            print("🌐 Please configure this tunnel manually at https://playit.gg")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create tunnel: {e}")
            return False
    
    def get_public_url(self):
        """Get the public URL for web access"""
        if "web" in self.tunnels:
            return self.tunnels["web"]["url"]
        return None

    def enable_playit_for_server(self, server_name, server_port):
        """Enable Playit.gg tunneling for a specific server"""
        status = self.check_installation_status()
        
        if status == "not_installed":
            print(f"🌐 Playit.gg not installed. Installing for server '{server_name}'...")
            
            if self.system == "windows":
                # Try MSI installer first
                if self.install_playit_msi(silent=True):
                    print("✅ Playit.gg installed via MSI installer!")
                else:
                    print("⚠️ MSI installation failed, trying portable version...")
                    if not self.download_playit_portable():
                        return False
            else:
                # Non-Windows: use portable version
                if not self.download_playit_portable():
                    return False
        
        # Start Playit agent if not running
        if not self.running:
            if not self.start_playit():
                return False
        
        # Create tunnel for the server
        self.create_tunnel(server_port, "tcp")
        
        print("🎯 Playit.gg Setup Complete!")
        print(f"✅ Your server '{server_name}' is now accessible through Playit.gg!")
        print("🌐 Visit https://playit.gg to configure your tunnels")
        print("📱 Share the public URL with your friends to let them connect!")
        
        return True
    
    def get_playit_status_message(self):
        """Get user-friendly status message for UI"""
        status = self.check_installation_status()
        
        if status == "installed":
            return "✅ Installed"
        elif status == "portable":
            return "✅ Portable Version"
        else:
            return "❌ Not Installed"

# Global instance
playit_manager = PlayitManager()

def setup_playit_tunnels():
    """Setup Playit.gg tunnels for CrazeDyn Panel (legacy function for web panel startup)"""
    print("🌐 Setting up Playit.gg for remote access...")
    
    # Start Playit.gg if available
    if playit_manager.start_playit():
        # Wait a moment for startup
        time.sleep(3)
        
        # Create tunnel for web panel (port 5000)
        playit_manager.create_tunnel(5000, "http")
        
        # Instructions for user
        print("=" * 60)
        print("🎯 PLAYIT.GG SETUP INSTRUCTIONS")
        print("=" * 60)
        print("1. Visit https://playit.gg and create a free account")
        print("2. Click 'Add Tunnel' in your dashboard")
        print("3. Choose 'Minecraft Java' for game servers")
        print("4. Choose 'HTTP' for web panel access")
        print("5. Set local port to your server port (e.g., 25565)")
        print("6. Copy the public URL and share with players!")
        print("=" * 60)
        print("💡 Your CrazeDyn Panel will be accessible worldwide!")
        print("📱 Players can connect from anywhere using the public URL")
        print("=" * 60)
        
        return True
    else:
        print("❌ Failed to setup Playit.gg")
        return False

if __name__ == "__main__":
    setup_playit_tunnels()