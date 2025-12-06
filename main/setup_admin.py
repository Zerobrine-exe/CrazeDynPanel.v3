#!/usr/bin/env python3
"""
Script to create admin credentials during setup
"""

import sys
import json
import bcrypt
import time
from pathlib import Path

def save_admin_credentials(email, password, data_dir=None):
    """Save admin credentials securely"""
    try:
        if not data_dir:
            data_dir = Path(__file__).parent
        
        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        config = {
            'email': email,
            'password_hash': hashed_password.decode('utf-8'),
            'created_at': time.time()
        }
        
        config_path = Path(data_dir) / 'admin_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Secure the file permissions (owner read/write only)
        try:
            config_path.chmod(0o600)
        except:
            pass  # Windows doesn't support chmod
        
        print(f"✅ Admin credentials saved successfully!")
        print(f"📧 Email: {email}")
        print(f"📁 Config saved to: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving admin credentials: {e}")
        return False

if __name__ == "__main__":
    # Interactive mode for security - don't accept passwords via command line
    if len(sys.argv) > 1:
        print("❌ For security, passwords cannot be passed via command line")
        print("💡 Run this script interactively instead")
        sys.exit(1)
    
    print("🔐 CrazeDynPanel v2.0 - Admin Setup")
    print("=" * 40)
    
    email = input("📧 Enter admin email: ").strip().lower()
    
    import getpass
    password = getpass.getpass("🔑 Enter admin password (hidden): ")
    
    # Validate inputs
    if not email or '@' not in email:
        print("❌ Invalid email address")
        sys.exit(1)
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        sys.exit(1)
    
    success = save_admin_credentials(email, password)
    if success:
        print("🎉 Admin setup complete! You can now login to the web panel.")
        sys.exit(0)
    else:
        sys.exit(1)