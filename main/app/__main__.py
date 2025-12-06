#!/usr/bin/env python3
"""
CrazeDyn Panel - Minecraft Server Manager
Main application entry point
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Change to the Main directory for proper file paths
main_dir = app_dir.parent
os.chdir(main_dir)

if __name__ == "__main__":
    try:
        from gui.main_window import main
        main()
    except ImportError as e:
        print(f"Error importing GUI modules: {e}")
        print("Make sure PyQt6 is installed: pip install PyQt6")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)