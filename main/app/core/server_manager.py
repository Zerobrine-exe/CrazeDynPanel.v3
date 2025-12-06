import json
import os
import subprocess
import psutil
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .server_store import get_server_store

class MinecraftServer:
    """Represents a single Minecraft server instance"""
    
    def __init__(self, name: str, path: str, jar: str, min_ram: str, max_ram: str, port: int = 25565, storage_limit: int = 10, rcon_port: int = 25575, rcon_password: str = "panel"):
        self.name = name
        self.path = Path(path)
        self.jar = jar
        self.min_ram = min_ram
        self.max_ram = max_ram
        self.port = port
        self.storage_limit = storage_limit  # Storage limit in GB
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.status = "stopped"
        self.console_lines = []
        self.cpu_usage = 0.0
        self.ram_usage = 0.0
        self.rcon_port = rcon_port
        self.rcon_password = rcon_password
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert server to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "path": str(self.path),
            "jar": self.jar,
            "min_ram": self.min_ram,
            "max_ram": self.max_ram,
            "port": self.port,
            "storage_limit": self.storage_limit,
            "pid": self.pid,
            "status": self.status,
            "rcon_port": self.rcon_port,
            "rcon_password": self.rcon_password
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MinecraftServer':
        """Create server from dictionary"""
        server = cls(
            name=data["name"],
            path=data["path"],
            jar=data["jar"],
            min_ram=data["min_ram"],
            max_ram=data["max_ram"],
            port=data.get("port", 25565),
            storage_limit=data.get("storage_limit", 10),
            rcon_port=data.get("rcon_port", 25575),
            rcon_password=data.get("rcon_password", "panel")
        )
        server.pid = data.get("pid")
        server.status = data.get("status", "stopped")
        return server

class ServerManager:
    """Manages all Minecraft servers"""
    
    def __init__(self, servers_file: str = "servers.json"):
        # Use the unified server store instead of direct file access
        self.server_store = get_server_store()
        self.servers_file = self.server_store.get_servers_path()
        self.servers: Dict[str, MinecraftServer] = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        self.load_servers()
        
    def load_servers(self):
        """Load servers from unified server store"""
        try:
            # Use the server store to load data
            data = self.server_store.load_servers()
            
            # Convert to MinecraftServer objects
            for server_name, server_data in data.items():
                server = MinecraftServer.from_dict(server_data)
                self.servers[server.name] = server
                
                # Check if server is still running
                if server.pid and self.is_process_running(server.pid):
                    server.status = "running"
                    try:
                        server.process = psutil.Process(server.pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        server.status = "stopped"
                        server.pid = None
                else:
                    server.status = "stopped"
                    server.pid = None
            
            print(f"✅ Loaded {len(self.servers)} servers from unified store")
            
        except Exception as e:
            print(f"❌ Error loading servers from unified store: {e}")
            self.servers = {}
    
    def save_servers(self):
        """Save servers to unified server store"""
        try:
            # Convert MinecraftServer objects to dictionary format
            data = {server.name: server.to_dict() for server in self.servers.values()}
            
            # Use the server store to save data atomically
            if self.server_store.save_servers(data):
                print(f"✅ Saved {len(self.servers)} servers to unified store")
                return True
            else:
                print("❌ Failed to save servers to unified store")
                return False
        except Exception as e:
            print(f"❌ Error preparing servers for save: {e}")
            return False
    
    def create_server(self, name: str, version: str, min_ram: str, max_ram: str, 
                     storage_path: str, port: int = 25565, storage_limit: int = 10) -> bool:
        """Create a new Minecraft server"""
        try:
            # Auto-detect storage path if not provided properly
            if not storage_path or storage_path == "servers":
                storage_path = Path.cwd() / "servers"
            else:
                storage_path = Path(storage_path)
            
            server_path = storage_path / name
            server_path.mkdir(parents=True, exist_ok=True)
            
            print(f"Creating server at: {server_path.absolute()}")
            
            # Create plugins directory
            plugins_path = server_path / "plugins"
            plugins_path.mkdir(exist_ok=True)
            
            # Create logs directory
            logs_path = server_path / "logs"
            logs_path.mkdir(exist_ok=True)
            
            # Determine jar filename from version
            jar_name = f"paper-{version}.jar"
            
            # Create server instance with path (handle relative/absolute path safely)
            try:
                # Try to create relative path if possible
                relative_path = server_path.relative_to(Path.cwd())
                server_path_str = str(relative_path)
            except ValueError:
                # If relative path fails, use absolute path
                server_path_str = str(server_path.absolute())
                
            # Determine RCON port (prefer 25575, fallback to free 20000–26000)
            rcon_port = 25575 if self._is_port_free(25575) else self._find_free_port(20000, 26000)
            server = MinecraftServer(
                name=name,
                path=server_path_str,
                jar=jar_name,
                min_ram=min_ram,
                max_ram=max_ram,
                port=port,
                storage_limit=storage_limit,
                rcon_port=rcon_port,
                rcon_password="panel"
            )
            
            # Create start.bat file
            self._create_start_batch(server)
            
            # Create server.properties with custom port and RCON enabled
            self._create_server_properties(server)
            
            # Accept EULA
            self._create_eula_file(server)
            
            self.servers[name] = server
            self.save_servers()
            return True
            
        except Exception as e:
            print(f"Error creating server: {e}")
            return False
    
    def _download_server_jar(self, server: MinecraftServer) -> bool:
        """Download server jar if missing"""
        try:
            print(f"🔄 Downloading {server.jar}...")
            
            # Import downloader and extract version from jar name
            from .downloader import PaperMCDownloader
            downloader = PaperMCDownloader()
            
            # Extract version from jar filename (e.g., "paper-1.20.6.jar" -> "1.20.6")
            jar_name = server.jar
            if jar_name.startswith("paper-") and jar_name.endswith(".jar"):
                version = jar_name[6:-4]  # Remove "paper-" prefix and ".jar" suffix
            else:
                # Default to latest stable version if we can't parse
                version = "1.20.6"
                print(f"⚠️ Could not parse version from {jar_name}, using default: {version}")
            
            # Download server files to server directory
            server_path = Path(server.path)
            success = downloader.download_server_files(version, server_path)
            
            if success:
                # Check if the jar file now exists
                jar_path = server_path / server.jar
                if jar_path.exists() and jar_path.stat().st_size > 0:
                    print(f"✅ Successfully downloaded {server.jar}")
                    return True
                else:
                    print(f"⚠️ Download completed but jar file is missing or empty")
                    # Try to find any paper jar in the directory and rename it
                    for jar_file in server_path.glob("paper*.jar"):
                        if jar_file.stat().st_size > 0:
                            jar_file.rename(jar_path)
                            print(f"✅ Renamed {jar_file.name} to {server.jar}")
                            return True
                    return False
            else:
                print(f"❌ Failed to download server files for version {version}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to download server jar: {e}")
            print("💡 Ensure you have internet connection and the version is valid")
            return False
    
    def _create_start_batch(self, server: MinecraftServer):
        """Create start.bat file for the server"""
        batch_content = f"""@echo off
title {server.name} - Minecraft Server
echo Starting {server.name}...
echo.
java -Xms{server.min_ram} -Xmx{server.max_ram} -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true -jar {server.jar} nogui
echo.
echo Server stopped. Press any key to close...
pause
"""
        batch_path = Path(server.path) / "start.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_content)
    
    def _create_server_properties(self, server: MinecraftServer):
        """Create server.properties file with custom port and external access support"""
        properties_content = f"""# Minecraft server properties
# Generated by CrazeDyn Panel - {time.strftime('%Y-%m-%d %H:%M:%S')}
# Optimized for low ping and high performance
server-port={server.port}
server-ip=
gamemode=survival
difficulty=easy
spawn-protection=16
max-players=20
level-name=world
level-type=minecraft:normal
enable-command-block=true
online-mode=true
pvp=true
white-list=false
allow-nether=true
generate-structures=true
enforce-whitelist=false
enable-query=true
enable-rcon=true
rcon.port={server.rcon_port}
rcon.password={server.rcon_password}
# Performance optimizations for reduced ping
view-distance=8
simulation-distance=6
network-compression-threshold=256
max-tick-time=60000
sync-chunk-writes=false
prevent-proxy-connections=false
use-native-transport=true
motd=§6{server.name} §f- §bPowered by CrazeDyn Panel
"""
        properties_path = Path(server.path) / "server.properties"
        with open(properties_path, 'w', encoding='utf-8') as f:
            f.write(properties_content)

    def _is_port_free(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    def _find_free_port(self, start: int, end: int) -> int:
        for p in range(start, end + 1):
            if self._is_port_free(p):
                return p
        return 25575
    
    def _create_eula_file(self, server: MinecraftServer):
        """Create eula.txt file (automatically accept EULA)"""
        eula_content = """# By running the server you are agreeing to the Minecraft EULA
# https://account.mojang.com/documents/minecraft_eula
eula=true
"""
        eula_path = Path(server.path) / "eula.txt"
        with open(eula_path, 'w') as f:
            f.write(eula_content)
    
    def start_server(self, name: str) -> bool:
        """Start a Minecraft server using .bat file"""
        if name not in self.servers:
            return False
            
        server = self.servers[name]
        if server.status == "running":
            return True
        
        # Check Java availability before starting
        try:
            from .downloader import DependencyChecker
            java_info = DependencyChecker.check_java()
            if not java_info['installed']:
                print(f"❌ Java not found. Cannot start server '{name}'")
                print("💡 Please install Java 17 or higher to run Minecraft servers")
                return False
            elif not java_info['compatible']:
                print(f"❌ Java version {java_info.get('version', 'unknown')} is not compatible")
                print("💡 Minecraft servers require Java 17 or higher")
                return False
            else:
                print(f"✅ Java {java_info.get('version', 'unknown')} detected")
        except Exception as e:
            print(f"⚠️ Could not check Java installation: {e}")
            print("🔄 Attempting to start server anyway...")
            
        try:
            # Get absolute path to server directory
            server_path = Path(server.path)
            if not server_path.is_absolute():
                server_path = Path.cwd() / server_path
            
            # Ensure server directory exists
            if not server_path.exists():
                print(f"Server directory not found: {server_path}")
                return False
            
            # Ensure RCON is enabled in server.properties before start
            props_path = server_path / "server.properties"
            if props_path.exists():
                try:
                    lines = []
                    with open(props_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                    has_enable = False
                    has_port = False
                    has_pass = False
                    updated = []
                    for line in lines:
                        if line.strip().startswith('enable-rcon='):
                            updated.append(f"enable-rcon=true\n")
                            has_enable = True
                        elif line.strip().startswith('rcon.port='):
                            updated.append(f"rcon.port={server.rcon_port}\n")
                            has_port = True
                        elif line.strip().startswith('rcon.password='):
                            updated.append(f"rcon.password={server.rcon_password}\n")
                            has_pass = True
                        else:
                            updated.append(line)
                    if not has_enable:
                        updated.append("enable-rcon=true\n")
                    if not has_port:
                        updated.append(f"rcon.port={server.rcon_port}\n")
                    if not has_pass:
                        updated.append(f"rcon.password={server.rcon_password}\n")
                    with open(props_path, 'w', encoding='utf-8', errors='replace') as f:
                        f.writelines(updated)
                except Exception:
                    pass

            # Create start.bat if it doesn't exist
            bat_file = server_path / "start.bat"
            if not bat_file.exists():
                self._create_start_batch(server)
            
            # Download server jar if it doesn't exist
            jar_file = server_path / server.jar
            if not jar_file.exists():
                print(f"Server jar not found: {jar_file}")
                # Try to download it
                if not self._download_server_jar(server):
                    return False
            
            # Start the server using optimized Java command
            java_cmd = f'java -Xms{server.min_ram} -Xmx{server.max_ram} -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true -jar {server.jar} nogui'
            
            if os.name == 'nt':  # Windows
                cmd = f'cd /d "{server_path}" && {java_cmd}'
            else:  # Linux/Mac 
                cmd = java_cmd
            
            print(f"Starting server with command: {cmd}")
            print(f"Working directory: {server_path}")
            
            # Initialize console lines
            server.console_lines = []
            
            # Start process in background with better output handling
            server.process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # Unbuffered for real-time output
                universal_newlines=True,
                cwd=str(server_path),
                env=dict(os.environ, PYTHONUNBUFFERED='1')  # Force unbuffered output
            )
            
            server.pid = server.process.pid
            server.status = "starting"
            
            # Wait a moment for process to fully start
            time.sleep(0.5)
            
            # Check if process is actually running and update status
            if self.is_process_running(server.pid):
                server.status = "running"
            else:
                server.status = "stopped"
            
            # Start monitoring thread for this server
            monitor_thread = threading.Thread(
                target=self._monitor_server_output,
                args=(server,),
                daemon=True
            )
            monitor_thread.start()
            
            self.save_servers()
            return True
            
        except Exception as e:
            print(f"Error starting server {name}: {e}")
            server.status = "stopped"
            return False
    
    def stop_server(self, name: str) -> bool:
        """Stop a Minecraft server gracefully"""
        if name not in self.servers:
            return False
            
        server = self.servers[name]
        if server.status == "stopped":
            return True
            
        try:
            if server.process and server.process.poll() is None:
                # Send stop command to server
                server.process.stdin.write("stop\n")
                server.process.stdin.flush()
                
                # Wait for graceful shutdown
                try:
                    server.process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    # Force kill if not responding
                    server.process.kill()
                    server.process.wait()
            
            server.status = "stopped"
            server.pid = None
            server.process = None
            self.save_servers()
            return True
            
        except Exception as e:
            print(f"Error stopping server {name}: {e}")
            return False
    
    def restart_server(self, name: str) -> bool:
        """Restart a Minecraft server"""
        if self.stop_server(name):
            time.sleep(2)  # Brief pause
            return self.start_server(name)
        return False
    
    def delete_server(self, name: str) -> bool:
        """Delete a Minecraft server (removes from management, not files)"""
        if name in self.servers:
            # Stop server first if running
            self.stop_server(name)
            del self.servers[name]
            self.save_servers()
            return True
        return False
    
    def get_server_status(self, name: str) -> str:
        """Get current status of a server"""
        if name in self.servers:
            server = self.servers[name]
            if server.pid and self.is_process_running(server.pid):
                return "running"
            else:
                return "stopped"
        return "unknown"
    
    def get_server_stats(self, name: str) -> Dict[str, float]:
        """Get CPU and RAM usage for a server"""
        stats = {"cpu": 0.0, "ram": 0.0, "ram_mb": 0.0}
        
        if name in self.servers:
            server = self.servers[name]
            if server.process and server.status == "running":
                try:
                    # Use psutil.Process for monitoring stats
                    psutil_process = psutil.Process(server.pid)
                    stats["cpu"] = psutil_process.cpu_percent()
                    memory_info = psutil_process.memory_info()
                    stats["ram_mb"] = memory_info.rss / 1024 / 1024  # MB
                    stats["ram"] = (memory_info.rss / psutil.virtual_memory().total) * 100
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        return stats
    
    def _monitor_server_output(self, server: MinecraftServer):
        """Monitor server console output in a separate thread"""
        if not server.process:
            print(f"No process found for server {server.name}")
            return
            
        print(f"Starting output monitoring for server {server.name}")
        
        try:
            while server.process and server.process.poll() is None:
                try:
                    line = server.process.stdout.readline()
                    if line:
                        # Decode the line properly to handle any encoding issues
                        if isinstance(line, bytes):
                            try:
                                line = line.decode('utf-8', errors='replace')
                            except:
                                line = line.decode('latin-1', errors='replace')
                        
                        # Clean the line but preserve meaningful content
                        line = line.rstrip('\n\r').strip()
                        
                        if line:  # Only append non-empty lines
                            formatted_line = f"[{time.strftime('%H:%M:%S')}] {line}"
                            server.console_lines.append(formatted_line)
                            print(f"Console: {formatted_line}")  # Debug output
                            
                            # Keep only last 1000 lines
                            if len(server.console_lines) > 1000:
                                server.console_lines = server.console_lines[-1000:]
                            
                            # Update status based on output
                            if "Done (" in line and "For help, type" in line:
                                server.status = "running"
                                self.save_servers()
                    else:
                        # No output available, sleep briefly to avoid busy waiting
                        time.sleep(0.1)
                        
                except Exception as read_error:
                    print(f"Error reading output: {read_error}")
                    time.sleep(0.1)
                        
        except Exception as e:
            print(f"Error monitoring server output: {e}")
        finally:
            print(f"Output monitoring ended for server {server.name}")
            if server.status != "stopped":
                server.status = "stopped"
                server.pid = None
                self.save_servers()
    
    def send_command(self, name: str, command: str) -> bool:
        """Send a command to a running server"""
        if name in self.servers:
            server = self.servers[name]
            if server.process and server.process.poll() is None:
                try:
                    server.process.stdin.write(f"{command}\n")
                    server.process.stdin.flush()
                    return True
                except Exception as e:
                    print(f"Error sending command: {e}")
        return False
    
    def get_console_output(self, name: str, lines: int = 50) -> List[str]:
        """Get recent console output for a server"""
        if name in self.servers:
            server = self.servers[name]
            return server.console_lines[-lines:] if server.console_lines else []
        return []
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            return psutil.pid_exists(pid)
        except:
            return False
    
    def start_monitoring(self):
        """Start the monitoring thread for all servers"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_all_servers, daemon=True)
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
    
    def _monitor_all_servers(self):
        """Monitor all servers in a loop"""
        while self.monitoring_active:
            for server in self.servers.values():
                if server.status == "running" and server.process:
                    try:
                        # Update CPU and RAM usage using psutil
                        psutil_process = psutil.Process(server.pid)
                        server.cpu_usage = psutil_process.cpu_percent()
                        memory_info = psutil_process.memory_info()
                        server.ram_usage = memory_info.rss / 1024 / 1024  # MB
                        
                        # Check if process is still alive
                        if server.process and server.process.poll() is not None:
                            server.status = "stopped"
                            server.pid = None
                            server.process = None
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        server.status = "stopped"
                        server.pid = None
                        server.process = None
            
            time.sleep(1)  # Update every second
