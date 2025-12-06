#!/usr/bin/env python3
"""
Unified Server Storage System for CrazeDynPanel
Ensures both Python and Web versions use the same servers.json file
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import tempfile
import shutil

class ServerStore:
    """Centralized server data storage that both Python and Web panels can use"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._data_dir = self._get_data_dir()
        self._servers_path = self._data_dir / "servers.json"
        self._ensure_data_dir()
        
    def _get_data_dir(self) -> Path:
        """Get the unified data directory for all CrazeDyn Panel data"""
        # Priority order:
        # 1. Environment variable (for production deployments)
        # 2. OS-specific user data dir
        # 3. Fallback to Main directory (for development)
        
        env_dir = os.getenv('CRAZEDYN_DATA_DIR')
        if env_dir:
            return Path(env_dir)
        
        # Get the Main directory (where this script's parent's parent is)
        main_dir = Path(__file__).parent.parent
        
        # For development/portable mode, use Main directory
        # For production, we could use OS-specific directories
        return main_dir
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists"""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self._data_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            print(f"⚠️ Warning: Cannot write to data directory {self._data_dir}: {e}")
            # Fallback to temp directory if needed
            self._data_dir = Path(tempfile.gettempdir()) / "crazedyn_panel"
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._servers_path = self._data_dir / "servers.json"
    
    def get_servers_path(self) -> Path:
        """Get the absolute path to servers.json"""
        return self._servers_path
    
    def load_servers(self) -> Dict[str, Any]:
        """Load servers from JSON file with proper error handling and validation"""
        with self._lock:
            try:
                if not self._servers_path.exists():
                    # Initialize with empty data if file doesn't exist
                    self._save_servers_atomic({})
                    return {}
                
                with open(self._servers_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate and normalize the data
                return self._validate_and_normalize(data)
                
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ Warning: Error loading servers.json: {e}")
                print("🔄 Initializing with empty server list")
                # Backup corrupted file and start fresh
                if self._servers_path.exists():
                    backup_path = self._servers_path.with_suffix('.json.backup')
                    shutil.copy2(self._servers_path, backup_path)
                    print(f"📝 Corrupted file backed up to: {backup_path}")
                
                empty_data = {}
                self._save_servers_atomic(empty_data)
                return empty_data
                
            except Exception as e:
                print(f"❌ Unexpected error loading servers: {e}")
                return {}
    
    def save_servers(self, servers_data: Dict[str, Any]) -> bool:
        """Save servers to JSON file atomically"""
        with self._lock:
            return self._save_servers_atomic(servers_data)
    
    def _save_servers_atomic(self, data: Dict[str, Any]) -> bool:
        """Atomically save servers data to prevent corruption"""
        try:
            # Validate data before saving
            validated_data = self._validate_and_normalize(data)
            
            # Write to temporary file first
            temp_path = self._servers_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(validated_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic replace
            if os.name == 'nt':  # Windows
                # Windows doesn't support atomic replace if target exists
                if self._servers_path.exists():
                    backup_path = self._servers_path.with_suffix('.bak')
                    shutil.move(str(self._servers_path), str(backup_path))
                shutil.move(str(temp_path), str(self._servers_path))
                # Clean up backup
                backup_path = self._servers_path.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.unlink()
            else:  # Unix-like systems
                shutil.move(str(temp_path), str(self._servers_path))
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving servers: {e}")
            # Clean up temp file if it exists
            temp_path = self._servers_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def _validate_and_normalize(self, data: Any) -> Dict[str, Any]:
        """Validate and normalize server data structure"""
        if not isinstance(data, dict):
            print(f"⚠️ Warning: Server data is not a dictionary, converting...")
            return {}
        
        normalized = {}
        for server_name, server_data in data.items():
            if not isinstance(server_data, dict):
                print(f"⚠️ Warning: Skipping invalid server data for '{server_name}'")
                continue
            
            # Ensure required fields exist with defaults
            normalized_server = {
                "name": server_data.get("name", server_name),
                "path": server_data.get("path", f"servers/{server_name}"),
                "jar": server_data.get("jar", "paper-1.20.1.jar"),
                "min_ram": server_data.get("min_ram", "512M"),
                "max_ram": server_data.get("max_ram", "1024M"),
                "port": server_data.get("port", 25565),
                "storage_limit": server_data.get("storage_limit", 10),
                "pid": server_data.get("pid"),
                "status": server_data.get("status", "stopped"),
                # Add any custom fields that exist
                **{k: v for k, v in server_data.items() 
                   if k not in ["name", "path", "jar", "min_ram", "max_ram", "port", "storage_limit", "pid", "status"]}
            }
            
            normalized[server_name] = normalized_server
        
        return normalized
    
    def add_server(self, server_name: str, server_data: Dict[str, Any]) -> bool:
        """Add a new server to the store"""
        with self._lock:
            servers = self.load_servers()
            servers[server_name] = server_data
            return self.save_servers(servers)
    
    def update_server(self, server_name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing server in the store"""
        with self._lock:
            servers = self.load_servers()
            if server_name not in servers:
                return False
            
            servers[server_name].update(updates)
            return self.save_servers(servers)
    
    def remove_server(self, server_name: str) -> bool:
        """Remove a server from the store"""
        with self._lock:
            servers = self.load_servers()
            if server_name in servers:
                del servers[server_name]
                return self.save_servers(servers)
            return False
    
    def get_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific server's data"""
        servers = self.load_servers()
        return servers.get(server_name)
    
    def list_servers(self) -> List[str]:
        """Get list of all server names"""
        servers = self.load_servers()
        return list(servers.keys())
    
    def backup_servers(self) -> bool:
        """Create a backup of the servers file"""
        try:
            if not self._servers_path.exists():
                return False
            
            timestamp = int(time.time())
            backup_path = self._servers_path.with_suffix(f'.backup.{timestamp}.json')
            shutil.copy2(self._servers_path, backup_path)
            print(f"📝 Servers backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False

# Global instance for use throughout the application
server_store = ServerStore()

def get_server_store() -> ServerStore:
    """Get the global server store instance"""
    return server_store

if __name__ == "__main__":
    # Test the ServerStore
    store = ServerStore()
    print(f"📁 Data directory: {store._data_dir}")
    print(f"📄 Servers file: {store.get_servers_path()}")
    
    # Test load/save
    servers = store.load_servers()
    print(f"📊 Loaded {len(servers)} servers")
    for name in servers:
        print(f"  - {name}")