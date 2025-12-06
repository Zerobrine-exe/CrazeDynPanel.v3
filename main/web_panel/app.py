#!/usr/bin/env python3
"""
CrazeDyn Web Panel - Modern Web-Based Server Management
Fast, responsive, and accessible from anywhere
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit, join_room
from functools import wraps
import secrets
import hashlib
import threading
import time
import os
import sys
from pathlib import Path
import json
import psutil
import socket

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
try:
    from app.core.server_manager import ServerManager
    from app.core.downloader import PaperMCDownloader
    from app.core.server_store import get_server_store
    print("✅ Core modules imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import core modules: {e}")
    # Create dummy classes for development
    from app.core.server_store import get_server_store
    
    class ServerManager:
        def __init__(self):
            self.server_store = get_server_store()
            self.servers = {}
            self.load_servers()
        def load_servers(self): 
            # Use unified server store
            try:
                data = self.server_store.load_servers()
                for name, server_data in data.items():
                    self.servers[name] = type('Server', (), server_data)()
            except Exception as e:
                print(f"Error loading servers in web panel: {e}")
        def get_console_output(self, name): return "Console not available - server manager not loaded"
        def send_command(self, name, command): return False
        def start_server(self, name): return False
        def stop_server(self, name): return False
        def restart_server(self, name): return False
        def get_server_status(self, name): return "unknown"
    
    class PaperMCDownloader:
        def __init__(self): pass

app = Flask(__name__)
# Use stable secret key from environment, generate if not set
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = os.getenv('HTTPS_ENABLED', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize SocketIO with secure CORS for Replit proxy access
def get_allowed_origins():
    """Get allowed origins including localhost and Replit domains"""
    origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://localhost:5000",
        "https://127.0.0.1:5000"
    ]
    
    replit_domains = os.getenv('REPLIT_DOMAINS', '')
    if replit_domains:
        for domain in replit_domains.split(','):
            domain = domain.strip()
            if domain:
                origins.append(f"https://{domain}")
                origins.append(f"http://{domain}")
    
    try:
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        origins.extend([
            f"http://{host_ip}:5000",
            f"http://{hostname}:5000",
            f"https://{host_ip}:5000",
            f"https://{hostname}:5000"
        ])
    except:
        pass
    
    return origins

socketio = SocketIO(app, cors_allowed_origins=get_allowed_origins(), async_mode='threading')

# Secure SocketIO connections
@socketio.on('connect')
def on_connect():
    if 'authenticated' not in session or not session['authenticated']:
        return False  # Reject connection

# Authentication system with email/password setup
import bcrypt
import json
from pathlib import Path

def get_admin_config_path():
    """Get path to admin config file"""
    data_dir = os.getenv('CRAZEDYN_DATA_DIR', str(Path(__file__).parent.parent))
    return Path(data_dir) / 'admin_config.json'

def save_admin_credentials(email, password):
    """Save admin credentials securely"""
    try:
        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        config = {
            'email': email,
            'password_hash': hashed_password.decode('utf-8'),
            'created_at': time.time()
        }
        
        config_path = get_admin_config_path()
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Secure the file permissions (owner read/write only)
        config_path.chmod(0o600)
        return True
    except Exception as e:
        print(f"Error saving admin credentials: {e}")
        return False

def load_admin_credentials():
    """Load admin credentials"""
    try:
        config_path = get_admin_config_path()
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading admin credentials: {e}")
        return None

def verify_admin_credentials(email, password):
    """Verify admin email and password"""
    config = load_admin_credentials()
    if not config:
        return False
    
    if config['email'] != email:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), config['password_hash'].encode('utf-8'))
    except Exception:
        return False

# Check if admin setup is complete
admin_config = load_admin_credentials()
if admin_config:
    print(f"🔐 Authentication enabled - Admin: {admin_config['email'][:3]}***@{admin_config['email'].split('@')[1] if '@' in admin_config['email'] else 'hidden'}")
else:
    print("⚡ First-time setup required - Admin credentials not configured")

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Authentication required'})
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_server_name(name):
    """Validate server name to prevent injection attacks"""
    import re
    if not re.match(r'^[A-Za-z0-9_-]+$', name):
        return False
    return name in server_manager.servers

# Authentication routes
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial admin setup page"""
    # Check if setup is already complete
    if load_admin_credentials():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            # Save credentials and login
            if save_admin_credentials(email, password):
                session['authenticated'] = True
                session['admin_email'] = email
                session.permanent = True
                flash('🎉 Welcome to CrazeDynPanel v2.0! Setup complete.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Failed to save credentials. Please try again.', 'error')
    
    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    # Redirect to setup if not configured
    if not load_admin_credentials():
        return redirect(url_for('setup'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if verify_admin_credentials(email, password):
            session['authenticated'] = True
            session['admin_email'] = email
            session.permanent = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('login'))

# Global instances
server_manager = ServerManager()
downloader = PaperMCDownloader()

def secure_path_join(base_path: Path, user_path: str) -> Path:
    """Securely join user-provided path with base path, preventing path traversal attacks"""
    import os
    
    # Normalize inputs
    user_path = user_path.strip() if user_path else ''
    if not user_path or user_path == '/':
        return base_path
    
    # Remove leading slashes and normalize
    user_path = user_path.lstrip('/')
    
    # Reject dangerous path components immediately
    if '..' in user_path or user_path.startswith('/') or any(c in user_path for c in ['\\', '\0']):
        raise ValueError(f"Invalid path detected: {user_path}")
    
    try:
        # Create the full path and resolve
        full_path = (base_path / user_path).resolve()
        base_resolved = base_path.resolve()
        
        # Use proper containment check
        try:
            # Python 3.9+ method (preferred)
            if not full_path.is_relative_to(base_resolved):
                raise ValueError(f"Path outside base directory: {user_path}")
        except AttributeError:
            # Fallback for older Python versions
            common_path = os.path.commonpath([str(full_path), str(base_resolved)])
            if common_path != str(base_resolved):
                raise ValueError(f"Path outside base directory: {user_path}")
        
        return full_path
        
    except (ValueError, OSError) as e:
        print(f"Security: Blocked path traversal attempt - {user_path}: {e}")
        raise ValueError(f"Invalid or unsafe path: {user_path}")

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.stats = {}
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.running = False
    
    def _monitor_loop(self):
        while self.running:
            try:
                # Get system stats
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Get server stats
                server_stats = {}
                for name, server in server_manager.servers.items():
                    status = server_manager.get_server_status(name)
                    player_count = 0
                    
                    # Try to get player count if server is running
                    if status == "running" and server.process:
                        try:
                            # This would need to be implemented based on server query
                            player_count = 0  # Placeholder
                        except:
                            pass
                    
                    server_stats[name] = {
                        'status': status,
                        'players': player_count,
                        'cpu': 0,  # Individual server CPU usage
                        'memory': 0  # Individual server memory usage
                    }
                
                # Update global stats
                self.stats = {
                    'system': {
                        'cpu': cpu_percent,
                        'memory': {
                            'used': memory.used,
                            'total': memory.total,
                            'percent': memory.percent
                        }
                    },
                    'servers': server_stats,
                    'timestamp': time.time()
                }
                
                # Emit to all connected clients
                socketio.emit('stats_update', self.stats)
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
            
            time.sleep(2)  # Update every 2 seconds

# Initialize performance monitor
perf_monitor = PerformanceMonitor()

# Record server start time for uptime calculation
start_time = time.time()

def create_startup_scripts(server_path: Path, jar_name: str, min_ram: str, max_ram: str):
    """Create startup scripts for the server"""
    server_path.mkdir(parents=True, exist_ok=True)
    
    start_sh = server_path / 'start.sh'
    with open(start_sh, 'w') as f:
        f.write(f'''#!/bin/bash
java -Xms{min_ram} -Xmx{max_ram} -jar {jar_name} nogui
''')
    start_sh.chmod(0o755)
    
    start_bat = server_path / 'start.bat'
    with open(start_bat, 'w') as f:
        f.write(f'''@echo off
java -Xms{min_ram} -Xmx{max_ram} -jar {jar_name} nogui
pause
''')

def create_eula_file(server_path: Path):
    """Create EULA file accepting Minecraft's EULA"""
    eula_path = server_path / 'eula.txt'
    with open(eula_path, 'w') as f:
        f.write('eula=true\n')

@app.route('/')
def index():
    """Main route - redirect to setup or login as needed"""
    if not load_admin_credentials():
        return redirect(url_for('setup'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')  
@login_required
def dashboard():
    """Main dashboard"""
    servers = server_manager.servers
    return render_template('dashboard.html', servers=servers)

@app.route('/api/servers')
@login_required
def api_servers():
    """Get all servers"""
    servers_data = []
    for name, server in server_manager.servers.items():
        status = server_manager.get_server_status(name)
        servers_data.append({
            'name': name,
            'status': status,
            'port': server.port,
            'path': server.path,
            'min_ram': server.min_ram,
            'max_ram': server.max_ram
        })
    return jsonify(servers_data)

@app.route('/api/server/<name>/start', methods=['POST'])
@login_required
def api_start_server(name):
    """Start a server"""
    try:
        success = server_manager.start_server(name)
        return jsonify({'success': success, 'message': f'Server {name} started' if success else 'Failed to start server'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/stop', methods=['POST'])
@login_required
def api_stop_server(name):
    """Stop a server"""
    try:
        success = server_manager.stop_server(name)
        return jsonify({'success': success, 'message': f'Server {name} stopped' if success else 'Failed to stop server'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/restart', methods=['POST'])
@login_required
def api_restart_server(name):
    """Restart a server"""
    try:
        success = server_manager.restart_server(name)
        return jsonify({'success': success, 'message': f'Server {name} restarted' if success else 'Failed to restart server'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/create', methods=['POST'])
@login_required
def api_create_server():
    """Create a new server"""
    try:
        data = request.json
        
        required_fields = ['name', 'version', 'min_ram', 'max_ram', 'storage_path', 'port', 'storage_limit']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing field: {field}'})
        
        # Check if server already exists
        if data['name'] in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server already exists'})
        
        # Create server
        success = server_manager.create_server(
            name=data['name'],
            version=data['version'],
            min_ram=data['min_ram'],
            max_ram=data['max_ram'],
            storage_path=data['storage_path'],
            port=data['port'],
            storage_limit=data['storage_limit']
        )
        
        if success:
            # Download files in background
            server = server_manager.servers[data['name']]
            server_path = Path(server.path)
            software_type = data.get('software_type', 'paper')
            
            # Start background download and setup
            def download_and_setup_files():
                try:
                    import requests
                    version = data['version']
                    jar_name = 'server.jar'
                    download_url = None
                    
                    if software_type == 'paper':
                        try:
                            builds_resp = requests.get(f'https://api.papermc.io/v2/projects/paper/versions/{version}/builds', timeout=10)
                            if builds_resp.status_code == 200:
                                builds = builds_resp.json().get('builds', [])
                                if builds:
                                    latest_build = builds[-1]
                                    build_num = latest_build['build']
                                    jar_name = latest_build['downloads']['application']['name']
                                    download_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{build_num}/downloads/{jar_name}"
                        except Exception as e:
                            print(f"Paper API error: {e}")
                            
                    elif software_type == 'vanilla':
                        if version in VANILLA_URLS:
                            download_url = VANILLA_URLS[version]
                            jar_name = f'minecraft_server.{version}.jar'
                            
                    elif software_type == 'fabric':
                        try:
                            loader_resp = requests.get('https://meta.fabricmc.net/v2/versions/loader', timeout=10)
                            installer_resp = requests.get('https://meta.fabricmc.net/v2/versions/installer', timeout=10)
                            if loader_resp.status_code == 200 and installer_resp.status_code == 200:
                                loaders = loader_resp.json()
                                installers = installer_resp.json()
                                latest_loader = loaders[0]['version'] if loaders else '0.16.10'
                                latest_installer = installers[0]['version'] if installers else '1.1.0'
                                download_url = f'https://meta.fabricmc.net/v2/versions/loader/{version}/{latest_loader}/{latest_installer}/server/jar'
                                jar_name = f'fabric-server-mc.{version}-loader.{latest_loader}-launcher.{latest_installer}.jar'
                        except Exception as e:
                            print(f"Fabric API error: {e}")
                            
                    elif software_type == 'purpur':
                        try:
                            builds_resp = requests.get(f'https://api.purpurmc.org/v2/purpur/{version}', timeout=10)
                            if builds_resp.status_code == 200:
                                builds_data = builds_resp.json()
                                latest_build = builds_data.get('builds', {}).get('latest', 'latest')
                                download_url = f"https://api.purpurmc.org/v2/purpur/{version}/{latest_build}/download"
                                jar_name = f'purpur-{version}-{latest_build}.jar'
                        except Exception as e:
                            print(f"Purpur API error: {e}")
                            
                    elif software_type == 'quilt':
                        try:
                            loader_resp = requests.get('https://meta.quiltmc.org/v3/versions/loader', timeout=10)
                            if loader_resp.status_code == 200:
                                loaders = loader_resp.json()
                                latest_loader = loaders[0]['version'] if loaders else '0.27.1'
                                download_url = f'https://meta.quiltmc.org/v3/versions/loader/{version}/{latest_loader}/server/jar'
                                jar_name = f'quilt-server-{version}-{latest_loader}.jar'
                        except Exception as e:
                            print(f"Quilt API error: {e}")
                    
                    if download_url:
                        print(f"Downloading {software_type} server JAR for {version}...")
                        jar_path = server_path / jar_name
                        resp = requests.get(download_url, timeout=300, stream=True)
                        if resp.status_code == 200:
                            with open(jar_path, 'wb') as f:
                                for chunk in resp.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            print(f"Downloaded: {jar_name}")
                            
                            create_startup_scripts(server_path, jar_name, data['min_ram'], data['max_ram'])
                            create_eula_file(server_path)
                        else:
                            print(f"Download failed: HTTP {resp.status_code}")
                    else:
                        downloader.download_server_files(data['version'], server_path)
                    
                    if data.get('install_plugins', False) and software_type in ['paper', 'purpur']:
                        plugins_path = server_path / 'plugins'
                        downloader.download_basic_plugin_pack(plugins_path)
                    
                    if data.get('enable_playit', False):
                        try:
                            from playit_manager import playit_manager
                            print(f"Enabling Playit.gg for server '{data['name']}'...")
                            playit_success = playit_manager.enable_playit_for_server(data['name'], data['port'])
                            if playit_success:
                                print(f"Playit.gg enabled for server '{data['name']}'!")
                            else:
                                print(f"Failed to enable Playit.gg for server '{data['name']}'")
                        except Exception as e:
                            print(f"Playit integration error: {e}")
                            
                except Exception as e:
                    print(f"Download/setup error: {e}")
            
            thread = threading.Thread(target=download_and_setup_files, daemon=True)
            thread.start()
            
            return jsonify({'success': True, 'message': f'Server {data["name"]} created successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to create server'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/server/<name>')
@login_required
def server_management(name):
    """Server management page with all tabs"""
    if name not in server_manager.servers:
        return redirect(url_for('dashboard'))
    
    server = server_manager.servers[name]
    status = server_manager.get_server_status(name)
    return render_template('server.html', server=server, server_name=name, status=status)

@app.route('/api/server/<name>/console')
@login_required
def api_server_console(name):
    """Get server console output"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        # Get console output from server
        try:
            console_output = server_manager.get_console_output(name) or "No console output available"
        except:
            console_output = "Console output temporarily unavailable"
        
        # Join list of strings into single string for frontend
        if isinstance(console_output, list):
            console_string = '\n'.join(console_output)
        else:
            console_string = str(console_output) if console_output else "No console output available"
            
        return jsonify({
            'success': True,
            'output': console_string
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/command', methods=['POST'])
@login_required
def api_server_command(name):
    """Send command to server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'message': 'No command provided'})
        
        success = server_manager.send_command(name, command)
        return jsonify({
            'success': success,
            'message': f'Command sent: {command}' if success else 'Failed to send command'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/delete', methods=['DELETE'])
@login_required
def api_server_delete(name):
    """Delete a server"""
    try:
        
        # Validate server name
        if not validate_server_name(name):
            return jsonify({'success': False, 'message': 'Invalid server name or server not found'}), 400
        
        # Check if server is running and stop it first
        server_status = server_manager.get_server_status(name)
        if server_status == "running":
            server_manager.stop_server(name)
            # Wait a bit for server to stop
            import time
            time.sleep(2)
        
        # Delete server
        success = server_manager.delete_server(name)
        
        if success:
            return jsonify({'success': True, 'message': f'Server {name} deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete server'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server deletion failed: {str(e)}'}), 500

# File Management API
def calculate_folder_size(path):
    """Calculate total size of a folder recursively"""
    total_size = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return total_size

@app.route('/api/server/<name>/files')
@login_required
def api_server_files(name):
    """Get server files list with actual folder sizes"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        path = request.args.get('path', '/')
        
        # Securely resolve full path
        server_base = Path(server.path)
        full_path = secure_path_join(server_base, path)
        
        if not full_path.exists():
            return jsonify({'success': False, 'message': 'Path not found'})
        
        files = []
        for item in full_path.iterdir():
            try:
                stat = item.stat()
                if item.is_dir():
                    size = calculate_folder_size(item)
                else:
                    size = stat.st_size
                files.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': size,
                    'modified': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                })
            except (OSError, PermissionError):
                continue
        
        # Sort: directories first, then files
        files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/upload', methods=['POST'])
@login_required
def api_server_upload(name):
    """Upload file to server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        file = request.files.get('file')
        path = request.form.get('path', '/')
        
        if not file:
            return jsonify({'success': False, 'message': 'No file provided'})
        
        # Securely resolve upload path and filename
        from werkzeug.utils import secure_filename
        
        server_base = Path(server.path)
        upload_path = secure_path_join(server_base, path)
        
        # Sanitize filename to prevent path traversal
        safe_filename = secure_filename(file.filename)
        if not safe_filename or '/' in safe_filename or '\\' in safe_filename:
            return jsonify({'success': False, 'message': 'Invalid filename'})
        
        upload_path.mkdir(parents=True, exist_ok=True)
        file_path = upload_path / safe_filename
        
        file.save(str(file_path))
        
        return jsonify({'success': True, 'message': f'Uploaded {file.filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/download')
@login_required
def api_server_download(name):
    """Download file from server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        file_path = request.args.get('path', '')
        
        # Securely resolve file path
        try:
            server_base = Path(server.path)
            full_path = secure_path_join(server_base, file_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid file path'})
        
        if not full_path.exists() or not full_path.is_file():
            return jsonify({'success': False, 'message': 'File not found'})
        
        from flask import send_file
        return send_file(str(full_path), as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/content')
@login_required
def api_server_file_content(name):
    """Get file content for editing"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        file_path = request.args.get('path', '')
        
        # Securely resolve file path
        try:
            server_base = Path(server.path)
            full_path = secure_path_join(server_base, file_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid file path'})
        
        if not full_path.exists() or not full_path.is_file():
            return jsonify({'success': False, 'message': 'File not found'})
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return jsonify({'success': False, 'message': 'File is not text-readable'})
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/save', methods=['POST'])
@login_required
def api_server_file_save(name):
    """Save file content"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        file_path = data.get('path', '')
        content = data.get('content', '')
        
        # Securely resolve file path
        try:
            server_base = Path(server.path)
            full_path = secure_path_join(server_base, file_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid file path'})
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True, 'message': 'File saved'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/delete', methods=['POST'])
@login_required
def api_server_file_delete(name):
    """Delete file or directory"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        file_path = data.get('path', '')
        
        # Securely resolve file path
        try:
            server_base = Path(server.path)
            full_path = secure_path_join(server_base, file_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid file path'})
        
        if not full_path.exists():
            return jsonify({'success': False, 'message': 'File not found'})
        
        if full_path.is_dir():
            import shutil
            shutil.rmtree(full_path)
        else:
            full_path.unlink()
        
        return jsonify({'success': True, 'message': 'Deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/rename', methods=['POST'])
@login_required
def api_server_file_rename(name):
    """Rename file or directory"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        old_path = data.get('oldPath', '')
        new_name = data.get('newName', '')
        
        if old_path.startswith('/'):
            full_old_path = Path(server.path) / old_path.lstrip('/')
        else:
            full_old_path = Path(server.path) / old_path
        
        if not full_old_path.exists():
            return jsonify({'success': False, 'message': 'File not found'})
        
        new_path = full_old_path.parent / new_name
        full_old_path.rename(new_path)
        
        return jsonify({'success': True, 'message': 'Renamed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/mkdir', methods=['POST'])
@login_required
def api_server_file_mkdir(name):
    """Create directory"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        dir_path = data.get('path', '')
        
        # Securely resolve directory path
        try:
            server_base = Path(server.path)
            full_path = secure_path_join(server_base, dir_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid directory path'})
        
        full_path.mkdir(parents=True, exist_ok=True)
        
        return jsonify({'success': True, 'message': 'Directory created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/copy', methods=['POST'])
@login_required
def api_server_file_copy(name):
    """Copy file or directory with proper handling for existing destinations"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        source_path = data.get('sourcePath', '')
        dest_path = data.get('destPath', '')
        
        server_base = Path(server.path)
        try:
            full_source = secure_path_join(server_base, source_path)
            full_dest = secure_path_join(server_base, dest_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid path'})
        
        if not full_source.exists():
            return jsonify({'success': False, 'message': 'Source not found'})
        
        import shutil
        
        # If destination is an existing directory, copy into it
        if full_dest.is_dir():
            full_dest = full_dest / full_source.name
        
        # Handle name collisions by appending suffix
        original_dest = full_dest
        counter = 1
        while full_dest.exists():
            if full_source.is_dir():
                full_dest = original_dest.parent / f"{original_dest.name}_copy{counter}"
            else:
                stem = original_dest.stem
                suffix = original_dest.suffix
                full_dest = original_dest.parent / f"{stem}_copy{counter}{suffix}"
            counter += 1
        
        if full_source.is_dir():
            shutil.copytree(full_source, full_dest)
        else:
            shutil.copy2(full_source, full_dest)
        
        return jsonify({'success': True, 'message': f'Copied to {full_dest.name}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/file/move', methods=['POST'])
@login_required
def api_server_file_move(name):
    """Move file or directory"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        source_path = data.get('sourcePath', '')
        dest_path = data.get('destPath', '')
        
        server_base = Path(server.path)
        try:
            full_source = secure_path_join(server_base, source_path)
            full_dest = secure_path_join(server_base, dest_path)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid path'})
        
        if not full_source.exists():
            return jsonify({'success': False, 'message': 'Source not found'})
        
        import shutil
        shutil.move(str(full_source), str(full_dest))
        
        return jsonify({'success': True, 'message': 'Moved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to CrazeDyn Panel'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    print('Client disconnected')

@socketio.on('subscribe_server')
def handle_subscribe_server(data):
    """Subscribe to server updates"""
    server_name = data.get('server_name')
    if server_name in server_manager.servers:
        # Join room for this server
        join_room(server_name)
        emit('subscribed', {'server': server_name})

# Plugin Management API
@app.route('/api/paper/versions')
def api_paper_versions():
    """Get all available PaperMC versions with download links"""
    try:
        versions = downloader.get_paper_versions()
        # Convert to list with version and download URL
        version_list = []
        for version, download_url in versions.items():
            version_list.append({
                'version': version,
                'download_url': download_url,
                'display_name': f"Paper {version}"
            })
        
        return jsonify({
            'success': True,
            'versions': version_list,
            'latest': version_list[0]['version'] if version_list else '1.21.8'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'versions': []})

# Vanilla Minecraft Server URLs
VANILLA_SERVER_URLS = {
    '1.21.10': 'https://piston-data.mojang.com/v1/objects/95495a7f485eedd84ce928cef5e223b757d2f764/server.jar',
    '1.21.9': 'https://piston-data.mojang.com/v1/objects/11e54c2081420a4d49db3007e66c80a22579ff2a/server.jar',
    '1.21.8': 'https://piston-data.mojang.com/v1/objects/6bce4ef400e4efaa63a13d5e6f6b500be969ef81/server.jar',
    '1.21.7': 'https://piston-data.mojang.com/v1/objects/05e4b48fbc01f0385adb74bcff9751d34552486c/server.jar',
    '1.21.6': 'https://piston-data.mojang.com/v1/objects/6e64dcabba3c01a7271b4fa6bd898483b794c59b/server.jar',
    '1.21.5': 'https://piston-data.mojang.com/v1/objects/e6ec2f64e6080b9b5d9b471b291c33cc7f509733/server.jar',
    '1.21.4': 'https://piston-data.mojang.com/v1/objects/4707d00eb834b446575d89a61a11b5d548d8c001/server.jar',
    '1.21.3': 'https://piston-data.mojang.com/v1/objects/45810d238246d90e811d896f87b14695b7fb6839/server.jar',
    '1.21.2': 'https://piston-data.mojang.com/v1/objects/7bf95409b0d9b5388bfea3704ec92012d273c14c/server.jar',
    '1.21.1': 'https://piston-data.mojang.com/v1/objects/59353fb40c36d304f2035d51e7d6e6baa98dc05c/server.jar',
    '1.21': 'https://piston-data.mojang.com/v1/objects/450698d1863ab5180c25d7c804ef0fe6369dd1ba/server.jar',
    '1.20.6': 'https://piston-data.mojang.com/v1/objects/145ff0858209bcfc164859ba735d4199aafa1eea/server.jar',
    '1.20.5': 'https://piston-data.mojang.com/v1/objects/79493072f65e17243fd36a699c9a96b4381feb91/server.jar',
    '1.20.4': 'https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar',
    '1.20.3': 'https://piston-data.mojang.com/v1/objects/4fb536bfd4a83d61cdbaf684b8d311e66e7d4c49/server.jar',
    '1.20.2': 'https://piston-data.mojang.com/v1/objects/5b868151bd02b41319f54c8d4061b8cae84e665c/server.jar',
    '1.20.1': 'https://piston-data.mojang.com/v1/objects/84194a2f286ef7c14ed7ce0090dba59902951553/server.jar',
    '1.20': 'https://piston-data.mojang.com/v1/objects/15c777e2cfe0556eef19aab534b186c0c6f277e1/server.jar',
    '1.19.4': 'https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar',
    '1.19.3': 'https://piston-data.mojang.com/v1/objects/c9df48efed58511cdd0213c56b9013a7b5c9ac1f/server.jar',
    '1.19.2': 'https://piston-data.mojang.com/v1/objects/f69c284232d7c7580bd89a5a4931c3581eae1378/server.jar',
    '1.19.1': 'https://piston-data.mojang.com/v1/objects/8399e1211e95faa421c1507b322dbeae86d604df/server.jar',
    '1.19': 'https://piston-data.mojang.com/v1/objects/e00c4052dac1d59a1188b2aa9d5a87113aaf1122/server.jar',
    '1.18.2': 'https://piston-data.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar',
    '1.18.1': 'https://piston-data.mojang.com/v1/objects/125e5adf40c659fd3bce3e66e67a16bb49ecc1b9/server.jar',
    '1.18': 'https://piston-data.mojang.com/v1/objects/3cf24a8694aca6267883b17d934efacc5e44440d/server.jar',
    '1.17.1': 'https://piston-data.mojang.com/v1/objects/a16d67e5807f57fc4e550299cf20226194497dc2/server.jar',
    '1.17': 'https://piston-data.mojang.com/v1/objects/0a269b5f2c5b93b1712d0f5dc43b6182b9ab254e/server.jar',
    '1.16.5': 'https://piston-data.mojang.com/v1/objects/1b557e7b033b583cd9f66746b7a9ab1ec1673ced/server.jar',
    '1.16.4': 'https://piston-data.mojang.com/v1/objects/35139deedbd5182953cf1caa23835da59ca3d7cd/server.jar',
}

@app.route('/api/vanilla/versions')
def api_vanilla_versions():
    """Get all available Vanilla Minecraft server versions"""
    try:
        version_list = []
        for version, download_url in VANILLA_SERVER_URLS.items():
            version_list.append({
                'version': version,
                'download_url': download_url,
                'display_name': f"Vanilla {version}"
            })
        
        return jsonify({
            'success': True,
            'versions': version_list,
            'latest': list(VANILLA_SERVER_URLS.keys())[0] if VANILLA_SERVER_URLS else '1.21.10'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'versions': []})

@app.route('/api/fabric/versions')
def api_fabric_versions():
    """Get all available Fabric loader versions for Minecraft"""
    try:
        import requests
        
        # Get latest Fabric loader and installer versions
        loader_response = requests.get('https://meta.fabricmc.net/v2/versions/loader', timeout=10)
        installer_response = requests.get('https://meta.fabricmc.net/v2/versions/installer', timeout=10)
        game_response = requests.get('https://meta.fabricmc.net/v2/versions/game', timeout=10)
        
        loaders = loader_response.json() if loader_response.status_code == 200 else []
        installers = installer_response.json() if installer_response.status_code == 200 else []
        games = game_response.json() if game_response.status_code == 200 else []
        
        latest_loader = loaders[0]['version'] if loaders else '0.16.10'
        latest_installer = installers[0]['version'] if installers else '1.1.0'
        
        # Get stable game versions only
        game_versions = [g['version'] for g in games if g.get('stable', False)][:20]
        
        version_list = []
        for mc_version in game_versions:
            version_list.append({
                'version': mc_version,
                'loader': latest_loader,
                'installer': latest_installer,
                'download_url': f'https://meta.fabricmc.net/v2/versions/loader/{mc_version}/{latest_loader}/{latest_installer}/server/jar',
                'display_name': f"Fabric {mc_version}"
            })
        
        return jsonify({
            'success': True,
            'versions': version_list,
            'latest_loader': latest_loader,
            'latest_installer': latest_installer,
            'latest': game_versions[0] if game_versions else '1.21.4'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'versions': []})

@app.route('/api/purpur/versions')
def api_purpur_versions():
    """Get available Purpur versions"""
    try:
        import requests
        response = requests.get('https://api.purpurmc.org/v2/purpur', timeout=10)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to fetch Purpur versions', 'versions': []})
        
        data = response.json()
        versions = data.get('versions', [])
        versions.reverse()
        
        version_list = []
        for version in versions[:20]:
            version_list.append({
                'version': version,
                'display_name': f"Purpur {version}"
            })
        
        latest = versions[0] if versions else '1.21.4'
        return jsonify({
            'success': True,
            'versions': version_list,
            'latest': latest
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'versions': []})

@app.route('/api/quilt/versions')
def api_quilt_versions():
    """Get available Quilt versions"""
    try:
        import requests
        loader_response = requests.get('https://meta.quiltmc.org/v3/versions/loader', timeout=10)
        game_response = requests.get('https://meta.quiltmc.org/v3/versions/game', timeout=10)
        
        loaders = loader_response.json() if loader_response.status_code == 200 else []
        games = game_response.json() if game_response.status_code == 200 else []
        
        latest_loader = loaders[0]['version'] if loaders else '0.27.1'
        
        game_versions = [g['version'] for g in games if g.get('stable', False)][:20]
        
        version_list = []
        for mc_version in game_versions:
            version_list.append({
                'version': mc_version,
                'loader': latest_loader,
                'display_name': f"Quilt {mc_version}"
            })
        
        return jsonify({
            'success': True,
            'versions': version_list,
            'latest_loader': latest_loader,
            'latest': game_versions[0] if game_versions else '1.21.4'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'versions': []})

@app.route('/api/server/software-types')
def api_software_types():
    """Get all available server software types"""
    return jsonify({
        'success': True,
        'types': [
            {'id': 'paper', 'name': 'PaperMC', 'description': 'High performance fork of Spigot with optimizations and plugins support', 'icon': 'scroll'},
            {'id': 'vanilla', 'name': 'Vanilla', 'description': 'Official Minecraft server from Mojang', 'icon': 'cube'},
            {'id': 'fabric', 'name': 'Fabric', 'description': 'Lightweight modding platform for Minecraft', 'icon': 'feather'},
            {'id': 'purpur', 'name': 'Purpur', 'description': 'Fork of Paper with additional features and customization', 'icon': 'cube'},
            {'id': 'quilt', 'name': 'Quilt', 'description': 'Modern mod loader focused on being open and community-driven', 'icon': 'layer-group'}
        ]
    })

# Modrinth API
@app.route('/api/modrinth/search')
def api_modrinth_search():
    """Search mods on Modrinth"""
    try:
        import requests
        query = request.args.get('query', '')
        loader = request.args.get('loader', 'fabric')
        mc_version = request.args.get('mc_version', '1.21.4')
        
        if not query:
            return jsonify({'success': False, 'message': 'Query required', 'mods': []})
        
        # Build facets for filtering
        facets = f'[["categories:{loader}"],["versions:{mc_version}"],["project_type:mod"]]'
        
        response = requests.get(
            f'https://api.modrinth.com/v2/search',
            params={
                'query': query,
                'limit': 20,
                'facets': facets
            },
            headers={'User-Agent': 'CrazeDynPanel/3.0'},
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Modrinth API error', 'mods': []})
        
        data = response.json()
        mods = [{
            'project_id': hit['project_id'],
            'slug': hit['slug'],
            'title': hit['title'],
            'description': hit.get('description', ''),
            'icon_url': hit.get('icon_url', ''),
            'downloads': hit.get('downloads', 0),
            'author': hit.get('author', 'Unknown')
        } for hit in data.get('hits', [])]
        
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'mods': []})

@app.route('/api/modrinth/project/<project_id>/versions')
def api_modrinth_versions(project_id):
    """Get versions for a Modrinth project"""
    try:
        import requests
        loader = request.args.get('loader', 'fabric')
        mc_version = request.args.get('mc_version', '')
        
        response = requests.get(
            f'https://api.modrinth.com/v2/project/{project_id}/version',
            headers={'User-Agent': 'CrazeDynPanel/3.0'},
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Version fetch failed', 'versions': []})
        
        versions = response.json()
        
        # Filter by loader and MC version
        filtered = []
        for v in versions:
            if loader in v.get('loaders', []):
                if not mc_version or mc_version in v.get('game_versions', []):
                    if v.get('files'):
                        filtered.append({
                            'id': v['id'],
                            'name': v['name'],
                            'version_number': v['version_number'],
                            'download_url': v['files'][0]['url'],
                            'filename': v['files'][0]['filename'],
                            'size': v['files'][0]['size']
                        })
        
        return jsonify({'success': True, 'versions': filtered[:5]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'versions': []})

@app.route('/api/server/<name>/mods')
@login_required
def api_server_mods(name):
    """Get installed mods list"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        mods_path = Path(server.path) / 'mods'
        
        if not mods_path.exists():
            return jsonify({'success': True, 'mods': []})
        
        mods = []
        for mod_file in mods_path.glob('*.jar'):
            try:
                stat = mod_file.stat()
                mods.append({
                    'name': mod_file.name,
                    'size': stat.st_size
                })
            except (OSError, PermissionError):
                continue
        
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/mods/install', methods=['POST'])
@login_required
def api_server_mods_install(name):
    """Install a mod from Modrinth"""
    try:
        import requests
        
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        project_id = data.get('project_id')
        loader = data.get('loader', 'fabric')
        mc_version = data.get('mc_version', '1.21.4')
        
        if not project_id:
            return jsonify({'success': False, 'message': 'Project ID required'})
        
        # Get the latest compatible version
        response = requests.get(
            f'https://api.modrinth.com/v2/project/{project_id}/version',
            headers={'User-Agent': 'CrazeDynPanel/3.0'},
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to fetch mod versions'})
        
        versions = response.json()
        
        # Find compatible version
        download_url = None
        filename = None
        for v in versions:
            if loader in v.get('loaders', []) and mc_version in v.get('game_versions', []):
                if v.get('files'):
                    download_url = v['files'][0]['url']
                    filename = v['files'][0]['filename']
                    break
        
        if not download_url:
            return jsonify({'success': False, 'message': f'No compatible version found for {loader} {mc_version}'})
        
        # Create mods directory if needed
        mods_path = Path(server.path) / 'mods'
        mods_path.mkdir(parents=True, exist_ok=True)
        
        # Download the mod
        mod_response = requests.get(download_url, headers={'User-Agent': 'CrazeDynPanel/3.0'}, timeout=60)
        if mod_response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to download mod'})
        
        mod_path = mods_path / filename
        with open(mod_path, 'wb') as f:
            f.write(mod_response.content)
        
        return jsonify({'success': True, 'message': f'Installed {filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/mods/delete', methods=['POST'])
@login_required
def api_server_mods_delete(name):
    """Delete a mod"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        mod_name = data.get('name')
        
        if not mod_name:
            return jsonify({'success': False, 'message': 'Mod name required'})
        
        mod_path = secure_path_join(Path(server.path) / 'mods', mod_name)
        
        if not mod_path.exists():
            return jsonify({'success': False, 'message': 'Mod not found'})
        
        mod_path.unlink()
        return jsonify({'success': True, 'message': f'Deleted {mod_name}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/version')
@login_required
def api_server_version(name):
    """Get current server version info"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        
        # Detect server software and version
        software = 'Unknown'
        mc_version = '--'
        jar_name = '--'
        
        # Look for server JAR
        for jar in server_path.glob('*.jar'):
            jar_name = jar.name
            name_lower = jar_name.lower()
            if 'paper' in name_lower:
                software = 'PaperMC'
            elif 'fabric' in name_lower:
                software = 'Fabric'
            elif 'forge' in name_lower:
                software = 'Forge'
            elif 'spigot' in name_lower:
                software = 'Spigot'
            elif 'vanilla' in name_lower or 'server' in name_lower:
                software = 'Vanilla'
            
            # Try to extract version from filename
            import re
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', jar_name)
            if version_match:
                mc_version = version_match.group(1)
            break
        
        # Try to get Java version
        java_version = '--'
        try:
            import subprocess
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
            output = result.stderr or result.stdout
            if 'version' in output:
                java_match = re.search(r'"(\d+(?:\.\d+)*)"', output)
                if java_match:
                    java_version = java_match.group(1)
        except:
            pass
        
        return jsonify({
            'success': True,
            'software': software,
            'mc_version': mc_version,
            'java_version': java_version,
            'jar_name': jar_name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/version/install', methods=['POST'])
@login_required
def api_server_version_install(name):
    """Download and install a new server version"""
    try:
        import requests
        
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        software = data.get('software')
        version = data.get('version')
        download_url = data.get('download_url')
        
        if not all([software, version, download_url]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        server_path = Path(server.path)
        
        old_jars = []
        jar_patterns = ['*.jar']
        exclude_patterns = ['plugins', 'mods', 'libraries']
        
        for jar_file in server_path.glob('*.jar'):
            if jar_file.is_file() and not any(excl in str(jar_file) for excl in exclude_patterns):
                old_jars.append(jar_file)
        
        response = requests.get(download_url, headers={'User-Agent': 'CrazeDynPanel/3.0'}, timeout=300, stream=True)
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to download server JAR'})
        
        jar_name = f'{software}-{version}.jar'
        jar_path = server_path / jar_name
        
        with open(jar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        for old_jar in old_jars:
            if old_jar != jar_path:
                try:
                    old_jar.unlink()
                    print(f"Removed old JAR: {old_jar.name}")
                except Exception as e:
                    print(f"Failed to remove old JAR {old_jar.name}: {e}")
        
        create_startup_scripts(server_path, jar_name, server.min_ram, server.max_ram)
        
        return jsonify({'success': True, 'message': f'Installed {jar_name} and updated startup scripts'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/plugins')
@login_required
def api_server_plugins(name):
    """Get installed plugins list"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        plugins_path = Path(server.path) / 'plugins'
        
        if not plugins_path.exists():
            return jsonify({'success': True, 'plugins': []})
        
        plugins = []
        for plugin_file in plugins_path.glob('*.jar'):
            try:
                stat = plugin_file.stat()
                size = stat.st_size
                size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
                
                plugins.append({
                    'name': plugin_file.stem,
                    'filename': plugin_file.name,
                    'size': size_str,
                    'status': 'Enabled',
                    'version': 'Unknown'  # Could be extracted from plugin.yml if needed
                })
            except (OSError, PermissionError):
                continue
        
        return jsonify({'success': True, 'plugins': plugins})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/plugins/upload', methods=['POST'])
@login_required
def api_server_plugin_upload(name):
    """Upload plugin to server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        plugin_file = request.files.get('plugin')
        
        if not plugin_file:
            return jsonify({'success': False, 'message': 'No plugin file provided'})
        
        if not plugin_file.filename.endswith('.jar'):
            return jsonify({'success': False, 'message': 'Only .jar files are allowed'})
        
        plugins_path = Path(server.path) / 'plugins'
        plugins_path.mkdir(exist_ok=True)
        
        file_path = plugins_path / plugin_file.filename
        plugin_file.save(str(file_path))
        
        return jsonify({'success': True, 'message': f'Uploaded {plugin_file.filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/plugins/delete', methods=['POST'])
@login_required
def api_server_plugin_delete(name):
    """Delete plugin from server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        plugin_name = data.get('plugin_name', '')
        
        plugins_path = Path(server.path) / 'plugins'
        plugin_file = plugins_path / f'{plugin_name}.jar'
        
        if not plugin_file.exists():
            # Try to find by exact filename
            for jar_file in plugins_path.glob('*.jar'):
                if jar_file.stem == plugin_name:
                    plugin_file = jar_file
                    break
        
        if plugin_file.exists():
            plugin_file.unlink()
            return jsonify({'success': True, 'message': f'Deleted {plugin_name}'})
        else:
            return jsonify({'success': False, 'message': 'Plugin not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/plugins/rename', methods=['POST'])
@login_required
def api_server_plugin_rename(name):
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        server = server_manager.servers[name]
        data = request.json
        old_name = data.get('plugin_name', '')
        new_name = data.get('new_name', '')
        plugins_path = Path(server.path) / 'plugins'
        if not new_name:
            return jsonify({'success': False, 'message': 'New name required'})
        old_file = plugins_path / f'{old_name}.jar'
        if not old_file.exists():
            for jar_file in plugins_path.glob('*.jar'):
                if jar_file.stem == old_name or jar_file.name == old_name:
                    old_file = jar_file
                    break
        if not old_file.exists():
            return jsonify({'success': False, 'message': 'Plugin not found'})
        dest_file = plugins_path / (new_name if new_name.endswith('.jar') else f'{new_name}.jar')
        if dest_file.exists():
            return jsonify({'success': False, 'message': 'A file with the new name already exists'})
        old_file.rename(dest_file)
        return jsonify({'success': True, 'message': 'Renamed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/plugins/install', methods=['POST'])
@login_required
def api_server_plugin_install(name):
    """Install plugin from SpigotMC"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        plugin_id = data.get('plugin_id', '')
        plugin_name = data.get('plugin_name', '')
        
        plugins_path = Path(server.path) / 'plugins'
        plugins_path.mkdir(exist_ok=True)
        
        # Use the existing spigot browser to download
        try:
            from app.core.spigot_browser import PluginInfo
            plugin_info = PluginInfo(
                id=plugin_id,
                name=plugin_name,
                download_url=f'https://api.spiget.org/v2/resources/{plugin_id}/download',
                premium=False
            )
            
            success = downloader.spigot_browser.download_plugin(plugin_info, plugins_path)
            
            if success:
                return jsonify({'success': True, 'message': f'Installed {plugin_name}'})
            else:
                return jsonify({'success': False, 'message': f'Failed to download {plugin_name}'})
        except Exception as download_error:
            return jsonify({'success': False, 'message': f'Download error: {str(download_error)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Plugin Browser API
@app.route('/api/plugins/search')
@login_required
def api_plugins_search():
    """Search plugins on SpigotMC"""
    try:
        query = request.args.get('query', '')
        category = request.args.get('category', '')
        sort = request.args.get('sort', 'downloads')
        
        # Use existing spigot browser
        plugins, _ = downloader.spigot_browser.search_plugins(
            query=query,
            category=category if category else None,
            sort=sort,
            size=30
        )
        
        return jsonify({'success': True, 'plugins': [plugin.__dict__ for plugin in plugins]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/plugins/popular')
@login_required
def api_plugins_popular():
    """Get popular plugins"""
    try:
        plugins = downloader.spigot_browser.get_popular_plugins(20)
        return jsonify({'success': True, 'plugins': [plugin.__dict__ for plugin in plugins]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/plugins/details/<plugin_id>')
@login_required
def api_plugin_details(plugin_id):
    """Get plugin details"""
    try:
        plugin = downloader.spigot_browser.get_plugin_details(plugin_id)
        if plugin:
            return jsonify({'success': True, 'plugin': plugin.__dict__})
        else:
            return jsonify({'success': False, 'message': 'Plugin not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# World Management API
@app.route('/api/server/<name>/worlds')
@login_required
def api_server_worlds(name):
    """Get all worlds for a server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        worlds = []
        
        for item in server_path.iterdir():
            if item.is_dir():
                level_dat = item / 'level.dat'
                if level_dat.exists():
                    stat = item.stat()
                    worlds.append({
                        'name': item.name,
                        'size': sum(f.stat().st_size for f in item.rglob('*') if f.is_file()),
                        'modified': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                    })
        
        return jsonify({'success': True, 'worlds': worlds})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/worlds', methods=['POST'])
@login_required
def api_create_world(name):
    """Create a new world"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        world_name = data.get('name', '').strip()
        world_type = data.get('type', 'normal')
        seed = data.get('seed', '')
        
        if not world_name:
            return jsonify({'success': False, 'message': 'World name is required'})
        
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', world_name):
            return jsonify({'success': False, 'message': 'Invalid world name. Use only letters, numbers, underscores, and hyphens.'})
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        world_path = secure_path_join(server_path, world_name)
        
        if world_path.exists():
            return jsonify({'success': False, 'message': 'World already exists'})
        
        world_path.mkdir(parents=True)
        return jsonify({'success': True, 'message': f'World {world_name} created'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/worlds/<world_name>', methods=['DELETE'])
@login_required
def api_delete_world(name, world_name):
    """Delete a world"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        world_path = secure_path_join(server_path, world_name)
        
        if not world_path.exists():
            return jsonify({'success': False, 'message': 'World not found'})
        
        import shutil
        shutil.rmtree(world_path)
        return jsonify({'success': True, 'message': f'World {world_name} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Backup Management API
@app.route('/api/server/<name>/backups')
@login_required
def api_server_backups(name):
    """Get all backups for a server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        backup_dir = Path(server.path) / 'backups'
        
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True)
            return jsonify({'success': True, 'backups': []})
        
        backups = []
        for item in backup_dir.iterdir():
            if item.is_file() and item.suffix in ['.zip', '.tar', '.gz']:
                stat = item.stat()
                backups.append({
                    'name': item.name,
                    'size': stat.st_size,
                    'created': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime)),
                    'type': 'full' if 'full' in item.name.lower() else 'world' if 'world' in item.name.lower() else 'config'
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        return jsonify({'success': True, 'backups': backups})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def auto_cleanup_backups(backup_dir, retention_days=30):
    """Automatically cleanup old backups based on retention policy"""
    if retention_days <= 0:
        return 0
    
    cutoff_time = time.time() - (retention_days * 86400)
    deleted_count = 0
    
    try:
        for backup in backup_dir.iterdir():
            if backup.is_file() and backup.suffix in ['.zip', '.tar', '.gz']:
                if backup.stat().st_mtime < cutoff_time:
                    backup.unlink()
                    deleted_count += 1
    except Exception:
        pass
    
    return deleted_count

@app.route('/api/server/<name>/backups', methods=['POST'])
@login_required
def api_create_backup(name):
    """Create a backup with automatic cleanup of old backups"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        backup_type = data.get('type', 'full')
        retention_days = data.get('retention_days', 30)  # Default 30 days retention
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        backup_dir = server_path / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_name = f"{name}_{backup_type}_{timestamp}.zip"
        backup_path = backup_dir / backup_name
        
        import zipfile
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if backup_type == 'full':
                for item in server_path.rglob('*'):
                    if item.is_file() and 'backups' not in str(item):
                        arcname = item.relative_to(server_path)
                        zipf.write(item, arcname)
            elif backup_type == 'world':
                for world_dir in server_path.iterdir():
                    if world_dir.is_dir() and (world_dir / 'level.dat').exists():
                        for item in world_dir.rglob('*'):
                            if item.is_file():
                                arcname = item.relative_to(server_path)
                                zipf.write(item, arcname)
            elif backup_type == 'config':
                for item in server_path.glob('*.yml'):
                    zipf.write(item, item.name)
                for item in server_path.glob('*.properties'):
                    zipf.write(item, item.name)
                for item in server_path.glob('*.json'):
                    zipf.write(item, item.name)
        
        # Auto-cleanup old backups based on retention policy
        deleted_count = 0
        if retention_days > 0:
            deleted_count = auto_cleanup_backups(backup_dir, retention_days)
        
        message = f'Backup {backup_name} created'
        if deleted_count > 0:
            message += f' ({deleted_count} old backup(s) auto-removed)'
        
        return jsonify({'success': True, 'message': message, 'deleted_old': deleted_count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/backups/<backup_name>', methods=['DELETE'])
@login_required
def api_delete_backup(name, backup_name):
    """Delete a backup"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        backup_path = secure_path_join(Path(server.path) / 'backups', backup_name)
        
        if not backup_path.exists():
            return jsonify({'success': False, 'message': 'Backup not found'})
        
        backup_path.unlink()
        return jsonify({'success': True, 'message': f'Backup {backup_name} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/backups/<backup_name>/download')
@login_required
def api_download_backup(name, backup_name):
    """Download a backup file"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        backup_path = secure_path_join(Path(server.path) / 'backups', backup_name)
        
        if not backup_path.exists():
            return jsonify({'success': False, 'message': 'Backup not found'})
        
        from flask import send_file
        return send_file(str(backup_path), as_attachment=True, download_name=backup_name)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/backups/auto-cleanup', methods=['POST'])
@login_required
def api_cleanup_old_backups(name):
    """Clean up old backups based on retention settings"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        retention_days = data.get('days', 30)
        
        if retention_days == 'never':
            return jsonify({'success': True, 'message': 'Auto-cleanup disabled', 'deleted': 0})
        
        server = server_manager.servers[name]
        backup_dir = Path(server.path) / 'backups'
        
        if not backup_dir.exists():
            return jsonify({'success': True, 'message': 'No backups to clean', 'deleted': 0})
        
        cutoff_time = time.time() - (int(retention_days) * 86400)
        deleted_count = 0
        
        for backup in backup_dir.iterdir():
            if backup.is_file() and backup.suffix in ['.zip', '.tar', '.gz']:
                if backup.stat().st_mtime < cutoff_time:
                    backup.unlink()
                    deleted_count += 1
        
        return jsonify({'success': True, 'message': f'Deleted {deleted_count} old backups', 'deleted': deleted_count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/backups/<backup_name>/restore', methods=['POST'])
@login_required
def api_restore_backup(name, backup_name):
    """Restore a backup"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        backup_path = secure_path_join(server_path / 'backups', backup_name)
        
        if not backup_path.exists():
            return jsonify({'success': False, 'message': 'Backup not found'})
        
        import zipfile
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(server_path)
        
        return jsonify({'success': True, 'message': f'Backup {backup_name} restored'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Task Scheduler API
tasks_store = {}

@app.route('/api/server/<name>/tasks')
@login_required
def api_server_tasks(name):
    """Get all scheduled tasks for a server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server_tasks = tasks_store.get(name, [])
        return jsonify({'success': True, 'tasks': server_tasks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/tasks', methods=['POST'])
@login_required
def api_create_task(name):
    """Create a scheduled task"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        task = {
            'id': secrets.token_hex(8),
            'name': data.get('name', 'Unnamed Task'),
            'type': data.get('type', 'command'),
            'action': data.get('action', ''),
            'schedule': data.get('schedule', 'daily'),
            'time': data.get('time', '00:00'),
            'enabled': data.get('enabled', True),
            'created': time.strftime('%Y-%m-%d %H:%M')
        }
        
        if name not in tasks_store:
            tasks_store[name] = []
        tasks_store[name].append(task)
        
        return jsonify({'success': True, 'message': 'Task created', 'task': task})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/tasks/<task_id>', methods=['DELETE'])
@login_required
def api_delete_task(name, task_id):
    """Delete a scheduled task"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        if name in tasks_store:
            tasks_store[name] = [t for t in tasks_store[name] if t['id'] != task_id]
        
        return jsonify({'success': True, 'message': 'Task deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/tasks/<task_id>/toggle', methods=['POST'])
@login_required
def api_toggle_task(name, task_id):
    """Toggle task enabled state"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        if name in tasks_store:
            for task in tasks_store[name]:
                if task['id'] == task_id:
                    task['enabled'] = not task['enabled']
                    return jsonify({'success': True, 'enabled': task['enabled']})
        
        return jsonify({'success': False, 'message': 'Task not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Notification API
notifications_store = {}

@app.route('/api/server/<name>/notifications')
@login_required
def api_server_notifications(name):
    """Get notifications for a server"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server_notifications = notifications_store.get(name, [])
        return jsonify({'success': True, 'notifications': server_notifications})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/notifications/mark-read', methods=['POST'])
@login_required
def api_mark_notifications_read(name):
    """Mark all notifications as read"""
    try:
        if name in notifications_store:
            for notif in notifications_store[name]:
                notif['read'] = True
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Template API
@app.route('/api/server/<name>/templates/clone', methods=['POST'])
@login_required
def api_clone_template(name):
    """Clone a template from GitHub"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        repo_url = data.get('url', '')
        
        if not repo_url:
            return jsonify({'success': False, 'message': 'Repository URL is required'})
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        
        import subprocess
        result = subprocess.run(
            ['git', 'clone', repo_url, str(server_path / 'templates' / 'imported')],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'Template cloned successfully'})
        else:
            return jsonify({'success': False, 'message': f'Clone failed: {result.stderr}'})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Clone timed out'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/templates/save', methods=['POST'])
@login_required
def api_save_template(name):
    """Save current server as template"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        data = request.json
        template_name = data.get('name', 'unnamed_template')
        
        server = server_manager.servers[name]
        server_path = Path(server.path)
        templates_dir = server_path / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_path = templates_dir / f"{template_name}.zip"
        
        import zipfile
        with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in ['server.properties', 'bukkit.yml', 'spigot.yml', 'paper.yml']:
                file_path = server_path / item
                if file_path.exists():
                    zipf.write(file_path, item)
            
            plugins_dir = server_path / 'plugins'
            if plugins_dir.exists():
                for plugin in plugins_dir.glob('*.jar'):
                    zipf.write(plugin, f'plugins/{plugin.name}')
        
        return jsonify({'success': True, 'message': f'Template {template_name} saved'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/templates')
@login_required
def api_server_templates(name):
    """Get saved templates"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        templates_dir = Path(server.path) / 'templates'
        
        if not templates_dir.exists():
            return jsonify({'success': True, 'templates': []})
        
        templates = []
        for item in templates_dir.glob('*.zip'):
            stat = item.stat()
            templates.append({
                'name': item.stem,
                'size': stat.st_size,
                'created': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
            })
        
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Log Viewer API
@app.route('/api/server/<name>/logs')
@login_required
def api_server_logs(name):
    """Get list of log files"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        logs_dir = Path(server.path) / 'logs'
        
        if not logs_dir.exists():
            return jsonify({'success': True, 'logs': []})
        
        logs = []
        for item in logs_dir.iterdir():
            if item.is_file() and item.suffix in ['.log', '.txt', '.gz']:
                stat = item.stat()
                logs.append({
                    'name': item.name,
                    'size': stat.st_size,
                    'modified': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                })
        
        logs.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/logs/<logfile>')
@login_required
def api_server_log_content(name, logfile):
    """Get log file content"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        log_path = secure_path_join(Path(server.path) / 'logs', logfile)
        
        if not log_path.exists():
            return jsonify({'success': False, 'message': 'Log file not found'})
        
        if log_path.suffix == '.gz':
            import gzip
            with gzip.open(log_path, 'rt', encoding='utf-8', errors='replace') as f:
                content = f.read()
        else:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        
        lines = content.split('\n')[-1000:]
        
        return jsonify({'success': True, 'content': '\n'.join(lines)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Server Properties API
@app.route('/api/server/<name>/properties')
@login_required
def api_server_properties(name):
    """Get server.properties content"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        props_path = Path(server.path) / 'server.properties'
        
        if not props_path.exists():
            return jsonify({'success': True, 'properties': {}})
        
        properties = {}
        with open(props_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
        
        return jsonify({'success': True, 'properties': properties})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/properties', methods=['POST'])
@login_required
def api_server_properties_save(name):
    """Save server.properties content"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        data = request.json
        properties = data.get('properties', {})
        
        props_path = Path(server.path) / 'server.properties'
        
        existing_lines = []
        if props_path.exists():
            with open(props_path, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
        
        updated_keys = set()
        new_lines = []
        for line in existing_lines:
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                new_lines.append(line)
            elif '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in properties:
                    new_lines.append(f"{key}={properties[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        for key, value in properties.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")
        
        with open(props_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return jsonify({'success': True, 'message': 'Server properties saved'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Change Password API
@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change admin password"""
    try:
        data = request.json
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'})
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'})
        
        config = load_admin_credentials()
        if not config:
            return jsonify({'success': False, 'message': 'No admin account found'})
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), config['password_hash'].encode('utf-8')):
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        if save_admin_credentials(config['email'], new_password):
            return jsonify({'success': True, 'message': 'Password changed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save new password'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Server Status API
@app.route('/api/server/<name>/status')
@login_required
def api_server_status(name):
    """Get detailed server status"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        status = server_manager.get_server_status(name)
        
        return jsonify({
            'success': True,
            'status': status,
            'name': name,
            'port': server.port,
            'min_ram': server.min_ram,
            'max_ram': server.max_ram,
            'path': server.path
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Server Stats API (for real-time monitoring)
@app.route('/api/server/<name>/stats')
@login_required
def api_server_stats(name):
    """Get real-time server stats (CPU, RAM, TPS, Players)"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        
        server = server_manager.servers[name]
        status = server_manager.get_server_status(name)
        
        cpu_usage = 0
        ram_usage = 0
        ram_max = 0
        tps = 20.0
        players_online = 0
        players_max = 20
        uptime = 0
        
        if status == 'running':
            try:
                if hasattr(server, 'process') and server.process:
                    proc = psutil.Process(server.process.pid)
                    cpu_usage = proc.cpu_percent(interval=0.1)
                    mem_info = proc.memory_info()
                    ram_usage = mem_info.rss // (1024 * 1024)
                    ram_max = int(server.max_ram.replace('G', '')) * 1024 if 'G' in str(server.max_ram) else int(server.max_ram.replace('M', ''))
                    uptime = int(time.time() - proc.create_time())
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                pass
            
            server_props_path = Path(server.path) / 'server.properties'
            if server_props_path.exists():
                try:
                    with open(server_props_path, 'r') as f:
                        for line in f:
                            if line.startswith('max-players='):
                                players_max = int(line.split('=')[1].strip())
                                break
                except:
                    pass
        
        return jsonify({
            'success': True,
            'status': status,
            'cpu': round(cpu_usage, 1),
            'ram': ram_usage,
            'ram_max': ram_max,
            'tps': tps,
            'players_online': players_online,
            'players_max': players_max,
            'uptime': uptime
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Player Management API
@app.route('/api/server/<name>/players')
@login_required
def api_server_players(name):
    """Get online players via RCON with log fallback"""
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        server = server_manager.servers[name]
        host = '127.0.0.1'
        port = getattr(server, 'rcon_port', 25575)
        password = getattr(server, 'rcon_password', 'panel')
        # Try console 'list' to populate logs/console
        try:
            server_manager.send_command(name, 'list')
            time.sleep(0.3)
        except Exception:
            pass
        response = send_rcon_command(host, port, password, 'list')
        names: list[str] = []
        if response:
            try:
                after_colon = response.split(':', 1)[1].strip()
                names = [p.strip() for p in after_colon.split(',') if p.strip()]
            except Exception:
                names = []
        if not names:
            try:
                logs_dir = Path(server.path) / 'logs'
                latest = logs_dir / 'latest.log'
                if latest.exists():
                    import re
                    with open(latest, 'rb') as f:
                        size = latest.stat().st_size
                        start = max(0, size - 200000)
                        f.seek(start)
                        content = f.read().decode('utf-8', errors='ignore')
                    matches = re.findall(r'There are\s+\d+/\d+\s+players online:\s*(.*)', content)
                    if matches:
                        last = matches[-1]
                        names = [p.strip() for p in last.split(',') if p.strip()]
                    else:
                        join_events = re.findall(r'[\d:]+\s\[Server thread/INFO\]:\s(\w+)\sjoined the game', content)
                        leave_events = re.findall(r'[\d:]+\s\[Server thread/INFO\]:\s(\w+)\sleft the game', content)
                        recent = join_events[-10:]
                        for p in recent:
                            if p not in leave_events[-10:]:
                                names.append(p)
                        names = list(dict.fromkeys(names))
            except Exception:
                names = []
        if not names:
            try:
                lines = server_manager.get_console_output(name, 300)
                import re
                join_re = re.compile(r"\b(\w+)\b\sjoined the game")
                leave_re = re.compile(r"\b(\w+)\b\sleft the game")
                lost_re = re.compile(r"\b(\w+)\b\s(lost connection|Disconnected|timed out)")
                list_re = re.compile(r"players online:\s*(.*)")
                current = []
                # Prefer latest 'list' line
                for ln in reversed(lines):
                    mlist = list_re.search(ln)
                    if mlist:
                        payload = mlist.group(1)
                        names = [p.strip() for p in payload.split(',') if p.strip()]
                        break
                for ln in lines:
                    m = join_re.search(ln)
                    if m:
                        p = m.group(1)
                        current.append(p)
                    m2 = leave_re.search(ln)
                    if m2:
                        p2 = m2.group(1)
                        current = [x for x in current if x != p2]
                    m3 = lost_re.search(ln)
                    if m3:
                        p3 = m3.group(1)
                        current = [x for x in current if x != p3]
                # Keep order and uniqueness
                seen = set()
                names = [x for x in current if not (x in seen or seen.add(x))]
            except Exception:
                names = []
        return jsonify({'success': True, 'players': [{'name': n, 'status': 'Online'} for n in names], 'online': len(names)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/server/<name>/player/action', methods=['POST'])
@login_required
def api_player_action(name):
    try:
        if name not in server_manager.servers:
            return jsonify({'success': False, 'message': 'Server not found'})
        data = request.json
        player = data.get('player', '')
        action = data.get('action', '')
        reason = data.get('reason', '')
        if not player or not action:
            return jsonify({'success': False, 'message': 'Missing player or action'})
        cmd = ''
        if action == 'kick':
            cmd = f'kick {player} {reason or "Removed by panel"}'
        elif action == 'ban':
            cmd = f'ban {player}'
        elif action == 'unban':
            cmd = f'pardon {player}'
        elif action == 'op':
            cmd = f'op {player}'
        elif action == 'deop':
            cmd = f'deop {player}'
        elif action == 'whitelist_add':
            cmd = f'whitelist add {player}'
        elif action == 'whitelist_remove':
            cmd = f'whitelist remove {player}'
        else:
            return jsonify({'success': False, 'message': 'Unknown action'})
        success = server_manager.send_command(name, cmd)
        if success:
            return jsonify({'success': True, 'response': 'ok'})
        server = server_manager.servers[name]
        host = '127.0.0.1'
        port = getattr(server, 'rcon_port', 25575)
        password = getattr(server, 'rcon_password', 'panel')
        resp = send_rcon_command(host, port, password, cmd)
        return jsonify({'success': bool(resp), 'response': resp or ''})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_local_ip():
    """Get local IP address for external access"""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except:
        return '127.0.0.1'

if __name__ == '__main__':
    # Start performance monitoring
    perf_monitor.start()
    
    # Get local IP for external access
    local_ip = get_local_ip()
    port = 5000
    
    print("=" * 50)
    print("🚀 CrazeDyn Web Panel Starting")
    print("=" * 50)
    print(f"📱 Local Access:    http://localhost:{port}")
    print(f"🌐 Network Access:  http://{local_ip}:{port}")
    print("=" * 50)
    print("✨ Features:")
    print("   • Real-time server monitoring")
    print("   • Remote server management")
    print("   • Live console access")
    print("   • Responsive modern UI")
    print("=" * 50)
    
    # Run the web server
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down CrazeDyn Panel...")
        perf_monitor.stop()
    except Exception as e:
        print(f"❌ Error starting server: {e}")

# Initialize SpigotMC browser for downloader
if not hasattr(downloader, 'spigot_browser'):
    try:
        from app.core.spigot_browser import SpigotMCBrowser
        downloader.spigot_browser = SpigotMCBrowser()
        print("✅ SpigotMC browser initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize SpigotMC browser: {e}")
        # Create a dummy browser for development
        class DummyBrowser:
            def search_plugins(self, **kwargs):
                return [], 0
            def get_popular_plugins(self, count):
                return []
            def get_plugin_details(self, plugin_id):
                return None
            def download_plugin(self, plugin, destination):
                return False
        downloader.spigot_browser = DummyBrowser()
        
# Update routes for new file management interface
@app.route('/server/<name>/files')
@login_required
def server_files(name):
    """Server file management page"""
    if name not in server_manager.servers:
        return redirect(url_for('dashboard'))
    
    server = server_manager.servers[name]
    return render_template('files.html', server=server)

@app.route('/server/<name>/plugins')
@login_required
def server_plugins(name):
    """Server plugin management page"""
    if name not in server_manager.servers:
        return redirect(url_for('dashboard'))
    
    server = server_manager.servers[name]
    return render_template('plugins.html', server=server)

@app.route('/servers')
@login_required
def servers_list():
    """Servers list page"""
    servers = server_manager.servers
    return render_template('dashboard.html', servers=servers)

@app.route('/plugins')
@login_required
def global_plugins():
    """Global plugins management page"""
    return render_template('global_plugins.html')

@app.route('/settings')
@login_required
def settings_page():
    """Settings page"""
    return render_template('settings.html')
from .rcon_client import send_rcon_command
