#!/usr/bin/env python3
"""
CrazeDyn Panel - Production Launcher
Optimized for production deployment with Gunicorn
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start CrazeDyn Panel in production mode"""
    print("🚀 Starting CrazeDyn Panel (Production Mode)")
    print("=" * 50)
    
    # Set environment variables
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('PORT', '5000')
    
    # Start with Gunicorn
    try:
        cmd = [
            sys.executable, '-m', 'gunicorn',
            '--worker-class', 'gevent',
            '--workers', '4',
            '--bind', '0.0.0.0:5000',
            '--timeout', '120',
            '--keep-alive', '5',
            '--max-requests', '1000',
            '--access-logfile', './logs/access.log',
            '--error-logfile', './logs/error.log',
            '--log-level', 'info',
            '--preload',
            'web_panel.app:app'
        ]
        
        # Create logs directory
        Path('./logs').mkdir(exist_ok=True)
        
        print("🌐 Starting production server with Gunicorn...")
        print("📡 Server will be available at: http://0.0.0.0:5000")
        print("📝 Logs: ./logs/access.log, ./logs/error.log")
        print("=" * 50)
        
        subprocess.run(cmd, cwd=Path(__file__).parent)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down production server...")
    except Exception as e:
        print(f"❌ Production server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())