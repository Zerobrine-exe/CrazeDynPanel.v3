import socket
import subprocess
import platform
import re
from typing import Dict, List, Optional, Tuple
import requests

class PortForwardingManager:
    """Manages port forwarding and network configuration"""
    
    def __init__(self):
        self.system = platform.system()
        self.active_rules = []
        
    def check_upnp_support(self) -> bool:
        """Check if UPnP is supported on the router"""
        try:
            import miniupnpc
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            devices = upnp.discover()
            return devices > 0
        except ImportError:
            return False
        except Exception:
            return False
            
    def add_upnp_port_mapping(self, internal_port: int, external_port: int, 
                             description: str = "Minecraft Server") -> bool:
        """Add UPnP port mapping"""
        try:
            import miniupnpc
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            
            if upnp.discover() > 0:
                upnp.selectigd()
                
                # Add TCP mapping
                result = upnp.addportmapping(
                    external_port, 'TCP', upnp.lanaddr, internal_port, 
                    description, ''
                )
                
                if result:
                    self.active_rules.append({
                        'type': 'upnp',
                        'internal_port': internal_port,
                        'external_port': external_port,
                        'protocol': 'TCP',
                        'description': description
                    })
                    return True
                    
        except ImportError:
            print("miniupnpc not available - install with: pip install miniupnpc")
        except Exception as e:
            print(f"UPnP mapping failed: {e}")
            
        return False
        
    def remove_upnp_port_mapping(self, external_port: int) -> bool:
        """Remove UPnP port mapping"""
        try:
            import miniupnpc
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            
            if upnp.discover() > 0:
                upnp.selectigd()
                result = upnp.deleteportmapping(external_port, 'TCP')
                
                if result:
                    # Remove from active rules
                    self.active_rules = [
                        rule for rule in self.active_rules 
                        if not (rule['type'] == 'upnp' and rule['external_port'] == external_port)
                    ]
                    return True
                    
        except Exception as e:
            print(f"UPnP removal failed: {e}")
            
        return False
        
    def add_windows_firewall_rule(self, port: int, name: str = "Minecraft Server") -> bool:
        """Add Windows Firewall rule"""
        if self.system != "Windows":
            return False
            
        try:
            # Add inbound rule for TCP
            cmd_tcp = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={name} - TCP", "dir=in", "action=allow", 
                "protocol=TCP", f"localport={port}"
            ]
            
            result_tcp = subprocess.run(cmd_tcp, capture_output=True, text=True)
            
            # Add inbound rule for UDP
            cmd_udp = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={name} - UDP", "dir=in", "action=allow",
                "protocol=UDP", f"localport={port}"
            ]
            
            result_udp = subprocess.run(cmd_udp, capture_output=True, text=True)
            
            if result_tcp.returncode == 0 and result_udp.returncode == 0:
                self.active_rules.append({
                    'type': 'firewall',
                    'port': port,
                    'name': name,
                    'protocols': ['TCP', 'UDP']
                })
                return True
                
        except Exception as e:
            print(f"Firewall rule creation failed: {e}")
            
        return False
        
    def remove_windows_firewall_rule(self, name: str) -> bool:
        """Remove Windows Firewall rule"""
        if self.system != "Windows":
            return False
            
        try:
            # Remove TCP rule
            cmd_tcp = [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={name} - TCP"
            ]
            
            # Remove UDP rule  
            cmd_udp = [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={name} - UDP"
            ]
            
            subprocess.run(cmd_tcp, capture_output=True)
            subprocess.run(cmd_udp, capture_output=True)
            
            # Remove from active rules
            self.active_rules = [
                rule for rule in self.active_rules 
                if not (rule['type'] == 'firewall' and rule['name'] == name)
            ]
            
            return True
            
        except Exception as e:
            print(f"Firewall rule removal failed: {e}")
            
        return False
        
    def get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
            
    def get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        services = [
            "https://api.ipify.org",
            "https://ipv4.icanhazip.com/",
            "https://ifconfig.me/ip"
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    return response.text.strip()
            except Exception:
                continue
                
        return None
        
    def test_port_accessibility(self, port: int, timeout: int = 10) -> Dict[str, any]:
        """Test if a port is accessible from outside"""
        result = {
            "port": port,
            "local_accessible": False,
            "external_accessible": False,
            "local_ip": self.get_local_ip(),
            "public_ip": self.get_public_ip(),
            "error": None
        }
        
        try:
            # Test local accessibility
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                local_result = s.connect_ex((result["local_ip"], port))
                result["local_accessible"] = local_result == 0
                
        except Exception as e:
            result["error"] = f"Local test failed: {e}"
            
        # Test external accessibility (simplified)
        # In a real scenario, this would need an external service
        # For now, just check if the port is bound locally
        try:
            connections = self._get_listening_ports()
            result["external_accessible"] = port in connections
        except Exception as e:
            if not result["error"]:
                result["error"] = f"External test failed: {e}"
                
        return result
        
    def _get_listening_ports(self) -> List[int]:
        """Get list of ports that are currently listening"""
        listening_ports = []
        
        try:
            if self.system == "Windows":
                # Use netstat on Windows
                if platform.system() == "Windows":
                    output = subprocess.check_output(
                        ["netstat", "-an"], 
                        text=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    output = subprocess.check_output(
                        ["netstat", "-an"], 
                        text=True
                    )
                
                for line in output.split('\n'):
                    if 'LISTENING' in line and 'TCP' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            addr = parts[1]
                            if ':' in addr:
                                port_str = addr.split(':')[-1]
                                try:
                                    port = int(port_str)
                                    listening_ports.append(port)
                                except ValueError:
                                    pass
            else:
                # Use netstat on Linux/Unix
                output = subprocess.check_output(
                    ["netstat", "-tlnp"], 
                    text=True
                )
                
                for line in output.split('\n'):
                    if 'LISTEN' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            addr = parts[3]
                            if ':' in addr:
                                port_str = addr.split(':')[-1]
                                try:
                                    port = int(port_str)
                                    listening_ports.append(port)
                                except ValueError:
                                    pass
                                    
        except Exception as e:
            print(f"Error getting listening ports: {e}")
            
        return listening_ports
        
    def get_router_info(self) -> Dict[str, any]:
        """Get router/gateway information"""
        info = {
            "gateway_ip": None,
            "router_model": None,
            "upnp_available": False
        }
        
        try:
            # Get default gateway
            if self.system == "Windows":
                if platform.system() == "Windows":
                    output = subprocess.check_output(
                        ["ipconfig"], 
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    output = subprocess.check_output(
                        ["ip", "route"], 
                        text=True
                    )
                
                for line in output.split('\n'):
                    if 'Default Gateway' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            gateway = parts[1].strip()
                            if gateway and gateway != "":
                                info["gateway_ip"] = gateway
                                break
            else:
                # Linux/Unix
                output = subprocess.check_output(["ip", "route"], text=True)
                for line in output.split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        if len(parts) > 2:
                            info["gateway_ip"] = parts[2]
                            break
                            
            # Check UPnP availability
            info["upnp_available"] = self.check_upnp_support()
            
        except Exception as e:
            print(f"Error getting router info: {e}")
            
        return info
        
    def generate_server_urls(self, port: int, server_name: str = "Minecraft Server") -> Dict[str, str]:
        """Generate connection URLs for the server"""
        local_ip = self.get_local_ip()
        public_ip = self.get_public_ip()
        
        urls = {
            "local": f"{local_ip}:{port}",
            "localhost": f"localhost:{port}"
        }
        
        if public_ip:
            urls["public"] = f"{public_ip}:{port}"
            
        return urls
        
    def setup_server_networking(self, port: int, server_name: str) -> Dict[str, any]:
        """Complete network setup for a Minecraft server"""
        result = {
            "success": False,
            "firewall_added": False,
            "upnp_added": False,
            "urls": {},
            "errors": []
        }
        
        try:
            # Add firewall rules
            if self.add_windows_firewall_rule(port, server_name):
                result["firewall_added"] = True
            else:
                result["errors"].append("Failed to add firewall rules")
                
            # Try UPnP port mapping
            if self.add_upnp_port_mapping(port, port, server_name):
                result["upnp_added"] = True
            else:
                result["errors"].append("UPnP port mapping failed")
                
            # Generate connection URLs
            result["urls"] = self.generate_server_urls(port, server_name)
            
            # Test accessibility
            test_result = self.test_port_accessibility(port)
            result["accessibility_test"] = test_result
            
            result["success"] = result["firewall_added"] or result["upnp_added"]
            
        except Exception as e:
            result["errors"].append(f"Setup failed: {e}")
            
        return result
        
    def cleanup_server_networking(self, port: int, server_name: str) -> bool:
        """Clean up network configuration for a server"""
        success = True
        
        try:
            # Remove firewall rules
            if not self.remove_windows_firewall_rule(server_name):
                success = False
                
            # Remove UPnP mapping
            if not self.remove_upnp_port_mapping(port):
                success = False
                
        except Exception as e:
            print(f"Cleanup failed: {e}")
            success = False
            
        return success