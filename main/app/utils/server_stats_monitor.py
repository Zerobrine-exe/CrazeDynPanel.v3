"""
Server Statistics Monitor - Real-time server resource monitoring
"""

import psutil
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class ServerStatsMonitor(QObject):
    """Monitor server statistics in real-time"""
    
    # Signals for updating UI
    stats_updated = pyqtSignal(dict)
    
    def __init__(self, server_process_pid: Optional[int] = None, server_path: Optional[Path] = None, storage_limit: int = 10):
        super().__init__()
        self.server_pid = server_process_pid
        self.server_path = Path(server_path) if server_path else None
        self.storage_limit = storage_limit  # Storage limit in GB
        self.server_process = None
        self.start_time = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.last_cpu_times = None
        
        # Cache folder size to reduce CPU usage
        self.cached_folder_size = 0
        self.last_size_check = 0
        self.size_check_interval = 30  # Only check folder size every 30 seconds
        
        # Initialize process reference if PID provided
        if self.server_pid:
            self.connect_to_process(self.server_pid)
    
    def connect_to_process(self, pid: int):
        """Connect to a running server process"""
        try:
            self.server_pid = pid
            self.server_process = psutil.Process(pid)
            if self.server_process.is_running():
                # Get process start time
                self.start_time = self.server_process.create_time()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.server_process = None
            self.server_pid = None
            self.start_time = None
        return False
    
    def start_monitoring(self, update_interval: int = 5000):
        """Start real-time monitoring with specified interval in milliseconds (reduced for performance)"""
        self.update_timer.start(update_interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.update_timer.stop()
    
    def update_stats(self):
        """Update server statistics and emit signal"""
        try:
            stats = self.get_current_stats()
            self.stats_updated.emit(stats)
        except Exception as e:
            # Emit offline stats on error
            self.stats_updated.emit(self._get_offline_stats())
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current server statistics"""
        if not self.server_process or not self.server_process.is_running():
            return self._get_offline_stats()
        
        try:
            stats = {
                'online': True,
                'cpu_percent': self._get_cpu_percent(),
                'memory_info': self._get_memory_info(),
                'disk_usage': self._get_disk_usage(),
                'uptime': self._get_uptime(),
                'players': self._get_player_info(),
                'tps': self._get_tps()
            }
            return stats
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.server_process = None
            self.server_pid = None
            return self._get_offline_stats()
    
    def _get_offline_stats(self) -> Dict[str, Any]:
        """Return offline server stats"""
        return {
            'online': False,
            'cpu_percent': 0.0,
            'memory_info': {'used': 0, 'available': 0, 'percent': 0.0},
            'disk_usage': {'used': 0, 'total': 0, 'percent': 0.0},
            'uptime': "Server offline",
            'players': {'online': 0, 'max': 0},
            'tps': 0.0
        }
    
    def _get_cpu_percent(self) -> float:
        """Get CPU usage percentage for the server process"""
        try:
            return self.server_process.cpu_percent()
        except:
            return 0.0
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            memory_info = self.server_process.memory_info()
            # Get system memory for context
            system_memory = psutil.virtual_memory()
            
            return {
                'used': memory_info.rss,  # Resident set size in bytes
                'available': system_memory.available,
                'percent': (memory_info.rss / system_memory.total) * 100
            }
        except:
            return {'used': 0, 'available': 0, 'percent': 0.0}
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage for server directory vs allocated limit (cached for performance)"""
        try:
            if self.server_path and self.server_path.exists():
                import time
                current_time = time.time()
                
                # Only recalculate folder size every 30 seconds to reduce CPU usage
                if current_time - self.last_size_check > self.size_check_interval:
                    self.cached_folder_size = self._calculate_folder_size(self.server_path)
                    self.last_size_check = current_time
                
                # Convert storage limit from GB to bytes
                limit_bytes = self.storage_limit * 1024 * 1024 * 1024
                
                return {
                    'used': self.cached_folder_size,
                    'total': limit_bytes,
                    'percent': (self.cached_folder_size / limit_bytes) * 100 if limit_bytes > 0 else 0.0
                }
        except:
            pass
        
        return {'used': 0, 'total': 0, 'percent': 0.0}
    
    def _calculate_folder_size(self, folder_path: Path) -> int:
        """Calculate total size of folder and all its contents"""
        total_size = 0
        try:
            for path in folder_path.rglob('*'):
                if path.is_file():
                    try:
                        total_size += path.stat().st_size
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        except (OSError, PermissionError):
            # Skip if we can't access the folder
            pass
        
        return total_size
    
    def _get_uptime(self) -> str:
        """Get server uptime as formatted string"""
        try:
            if self.start_time:
                uptime_seconds = time.time() - self.start_time
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                
                if days > 0:
                    return f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"
        except:
            pass
        
        return "Unknown"
    
    def _get_player_info(self) -> Dict[str, int]:
        """Get player information from server logs if available"""
        # This would need to parse server logs for player count
        # For now, return placeholder that can be enhanced later
        try:
            if self.server_path:
                logs_path = self.server_path / "logs" / "latest.log"
                if logs_path.exists():
                    # Parse latest log for player count - simplified implementation
                    return self._parse_player_count_from_logs(logs_path)
        except:
            pass
        
        return {'online': 0, 'max': 20}  # Default max players
    
    def _parse_player_count_from_logs(self, log_path: Path) -> Dict[str, int]:
        """Parse player count from server logs"""
        try:
            # Read last few lines of log file for player join/leave events
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read last 1000 characters to get recent activity
                f.seek(0, 2)  # Go to end
                file_size = f.tell()
                f.seek(max(0, file_size - 1000))
                recent_logs = f.read()
            
            # Count player join/leave events (simplified)
            # This is a basic implementation - could be enhanced with better parsing
            online_count = recent_logs.count("joined the game") - recent_logs.count("left the game")
            online_count = max(0, online_count)  # Ensure non-negative
            
            return {'online': online_count, 'max': 20}
        except:
            return {'online': 0, 'max': 20}
    
    def _get_tps(self) -> float:
        """Get TPS (Ticks Per Second) from server logs if available"""
        # This would need to parse server performance data
        # For now, return estimated TPS based on CPU usage
        try:
            cpu = self._get_cpu_percent()
            if cpu < 50:
                return 20.0  # Perfect TPS
            elif cpu < 80:
                return max(15.0, 20.0 - (cpu - 50) * 0.17)  # Degraded TPS
            else:
                return max(5.0, 20.0 - (cpu - 50) * 0.3)  # Poor TPS
        except:
            return 0.0
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    @staticmethod
    def get_usage_color(percentage: float) -> str:
        """Get color code based on usage percentage"""
        if percentage < 50:
            return "#00ff88"  # Green
        elif percentage < 80:
            return "#ffaa00"  # Yellow/Orange
        else:
            return "#ff4444"  # Red