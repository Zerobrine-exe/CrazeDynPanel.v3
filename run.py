#!/usr/bin/env python3
"""
CrazeDyn Panel - Replit Startup Script
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'main'))

os.chdir(Path(__file__).parent / 'main')

from web_panel.app import app, socketio

if __name__ == "__main__":
    print("Starting CrazeDyn Web Panel on 0.0.0.0:5000...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )
