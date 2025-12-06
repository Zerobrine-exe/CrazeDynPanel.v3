#!/usr/bin/env python3
"""
CrazeDyn Panel - Production Server
Uses Gunicorn with Gevent for production deployment
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def get_bind_address():
    """Get the bind address and port"""
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    return f"{host}:{port}"

def get_workers():
    """Calculate optimal number of workers"""
    import multiprocessing
    workers = multiprocessing.cpu_count() * 2 + 1
    return min(workers, 8)  # Cap at 8 workers

def setup_logging():
    """Setup production logging"""
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    return {
        'access_log': str(log_dir / "access.log"),
        'error_log': str(log_dir / "error.log"),
        'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    }

# Gunicorn configuration
bind = get_bind_address()
workers = get_workers()
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5

# Logging
logs = setup_logging()
accesslog = logs['access_log']
errorlog = logs['error_log']
access_log_format = logs['access_log_format']
loglevel = "info"

# Process naming
proc_name = "crazedyn-panel"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

print("🚀 CrazeDyn Panel - Production Server")
print(f"📡 Bind: {bind}")
print(f"👥 Workers: {workers}")
print(f"📝 Logs: {logs['access_log']}, {logs['error_log']}")

if __name__ == "__main__":
    # Import the app
    from web_panel.app import app, socketio
    
    print("🌐 Starting production server...")
    
    # Run with SocketIO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )