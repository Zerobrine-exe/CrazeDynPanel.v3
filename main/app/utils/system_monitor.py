import psutil
import time
import threading
import socket
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

@dataclass
class SystemStats:
    """System statistics data class"""
    cpu_percent: float
    ram_percent: float
    ram_used_mb: float
    ram_total_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float

@dataclass
class ProcessStats:
    """Process statistics data class"""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    status: str
    create_time: float

class SystemMonitor:
    """Monitor system and process statistics"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks: List[Callable[[SystemStats], None]] = []
        self.process_callbacks: List[Callable[[int, ProcessStats], None]] = []
        self.monitored_processes: Dict[int, psutil.Process] = {}
        
        # For network monitoring
        self.last_network_io = psutil.net_io_counters()
        self.last_network_time = time.time()
        
    def add_system_callback(self, callback: Callable[[SystemStats], None]):
        """Add callback for system stats updates"""
        self.callbacks.append(callback)
        
    def add_process_callback(self, callback: Callable[[int, ProcessStats], None]):
        """Add callback for process stats updates"""
        self.process_callbacks.append(callback)
        
    def monitor_process(self, pid: int):
        """Start monitoring a specific process"""
        try:
            process = psutil.Process(pid)
            self.monitored_processes[pid] = process
        except psutil.NoSuchProcess:
            pass
            
    def stop_monitoring_process(self, pid: int):
        """Stop monitoring a specific process"""
        if pid in self.monitored_processes:
            del self.monitored_processes[pid]
            
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Get system stats
                system_stats = self._get_system_stats()
                
                # Notify system callbacks
                for callback in self.callbacks:
                    try:
                        callback(system_stats)
                    except Exception as e:
                        print(f"Error in system callback: {e}")
                
                # Get process stats
                for pid, process in list(self.monitored_processes.items()):
                    try:
                        if process.is_running():
                            process_stats = self._get_process_stats(process)
                            
                            # Notify process callbacks
                            for callback in self.process_callbacks:
                                try:
                                    callback(pid, process_stats)
                                except Exception as e:
                                    print(f"Error in process callback: {e}")
                        else:
                            # Process no longer running
                            del self.monitored_processes[pid]
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process no longer exists
                        if pid in self.monitored_processes:
                            del self.monitored_processes[pid]
                            
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                
            time.sleep(self.update_interval)
            
    def _get_system_stats(self) -> SystemStats:
        """Get current system statistics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        ram_used_mb = memory.used / 1024 / 1024
        ram_total_mb = memory.total / 1024 / 1024
        
        # Disk usage (root partition)
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Network usage (calculate rate)
        current_network_io = psutil.net_io_counters()
        current_time = time.time()
        
        time_delta = current_time - self.last_network_time
        if time_delta > 0:
            sent_rate = (current_network_io.bytes_sent - self.last_network_io.bytes_sent) / time_delta
            recv_rate = (current_network_io.bytes_recv - self.last_network_io.bytes_recv) / time_delta
            
            network_sent_mb = sent_rate / 1024 / 1024  # MB/s
            network_recv_mb = recv_rate / 1024 / 1024  # MB/s
        else:
            network_sent_mb = 0.0
            network_recv_mb = 0.0
            
        self.last_network_io = current_network_io
        self.last_network_time = current_time
        
        return SystemStats(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_used_mb=ram_used_mb,
            ram_total_mb=ram_total_mb,
            disk_usage_percent=disk_usage_percent,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb
        )
        
    def _get_process_stats(self, process: psutil.Process) -> ProcessStats:
        """Get statistics for a specific process"""
        try:
            # Basic info
            pid = process.pid
            name = process.name()
            status = process.status()
            create_time = process.create_time()
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            return ProcessStats(
                pid=pid,
                name=name,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                status=status,
                create_time=create_time
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Return default stats for dead process
            return ProcessStats(
                pid=process.pid,
                name="Unknown",
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                status="dead",
                create_time=0.0
            )

class PortChecker:
    """Check port availability and usage"""
    
    @staticmethod
    def is_port_open(port: int, host: str = "localhost") -> bool:
        """Check if a port is open"""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
            
    @staticmethod
    def get_open_ports(start_port: int = 25565, count: int = 10) -> List[int]:
        """Get a list of available ports starting from start_port"""
        open_ports = []
        port = start_port
        
        while len(open_ports) < count and port <= 65535:
            if not PortChecker.is_port_open(port):
                open_ports.append(port)
            port += 1
            
        return open_ports
        
    @staticmethod
    def get_port_info(port: int) -> Dict[str, any]:
        """Get information about what's using a specific port"""
        info = {
            "port": port,
            "in_use": False,
            "process": None,
            "pid": None,
            "connections": []
        }
        
        try:
            # Check network connections
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.laddr.port == port:
                    info["in_use"] = True
                    info["connections"].append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status,
                        "family": conn.family.name,
                        "type": conn.type.name
                    })
                    
                    # Get process info
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            info["process"] = process.name()
                            info["pid"] = conn.pid
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                            
        except Exception as e:
            print(f"Error getting port info: {e}")
            
        return info

class NetworkForwarder:
    """Handle port forwarding and network configuration"""
    
    def __init__(self):
        self.active_forwards = {}
        
    def get_local_ip(self) -> str:
        """Get the local IP address"""
        import socket
        
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                local_ip = sock.getsockname()[0]
            return local_ip
        except Exception:
            return "127.0.0.1"
            
    def get_public_ip(self) -> Optional[str]:
        """Get the public IP address"""
        try:
            import requests
            response = requests.get("https://ipv4.icanhazip.com/", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            pass
            
        try:
            import requests
            response = requests.get("https://api.ipify.org", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            pass
            
        return None
        
    def check_port_forwarding(self, port: int, timeout: int = 5) -> bool:
        """Check if a port is accessible from outside"""
        import socket
        import threading
        
        result = {"success": False}
        
        def check_external():
            try:
                public_ip = self.get_public_ip()
                if public_ip:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(timeout)
                        if sock.connect_ex((public_ip, port)) == 0:
                            result["success"] = True
            except Exception:
                pass
                
        thread = threading.Thread(target=check_external, daemon=True)
        thread.start()
        thread.join(timeout=timeout + 1)
        
        return result["success"]
        
    def get_network_info(self) -> Dict[str, any]:
        """Get comprehensive network information"""
        return {
            "local_ip": self.get_local_ip(),
            "public_ip": self.get_public_ip(),
            "interfaces": self._get_network_interfaces(),
            "active_connections": len(psutil.net_connections()),
            "network_stats": psutil.net_io_counters()._asdict()
        }
        
    def _get_network_interfaces(self) -> List[Dict[str, any]]:
        """Get network interface information"""
        interfaces = []
        
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for interface_name, addresses in addrs.items():
                interface_info = {
                    "name": interface_name,
                    "addresses": [],
                    "is_up": stats.get(interface_name, psutil._common.snicstats(False, 0, 0, 0, 0, False)).isup
                }
                
                for addr in addresses:
                    if addr.family == 2:  # AF_INET (IPv4)
                        interface_info["addresses"].append({
                            "family": "IPv4",
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        })
                    elif addr.family == 23:  # AF_INET6 (IPv6)
                        interface_info["addresses"].append({
                            "family": "IPv6", 
                            "address": addr.address,
                            "netmask": addr.netmask
                        })
                        
                interfaces.append(interface_info)
                
        except Exception as e:
            print(f"Error getting network interfaces: {e}")
            
        return interfaces