#!/usr/bin/env python3
"""
CrazeDynPanel v2.0 - Icon Management System
Professional icon handling for both GUI and Web interfaces
"""

import os
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

class IconManager:
    """
    Centralized icon management system for CrazeDynPanel v2.0
    Provides consistent icon access across GUI and web interfaces
    """
    
    def __init__(self):
        # Base paths
        self.base_path = Path(__file__).parent.parent.parent
        self.icon_path = self.base_path / "icon"
        
        # Icon categories
        self.categories = {
            'menu': self.icon_path / "menu",
            'buttons': self.icon_path / "buttons", 
            'status': self.icon_path / "status",
            'server': self.icon_path / "server",
            'misc': self.icon_path / "misc"
        }
        
        # Icon registry - maps logical names to files (only existing icons)
        self.icons = {
            # Menu icons (available)
            'dashboard': 'menu/dashboard.png',
            'server_management': 'menu/server_management.png',
            'plugins': 'menu/plugins.png',
            'console': 'menu/console.png',
            'settings': 'menu/settings.png',
            
            # Button icons (available)
            'create_server': 'buttons/create_server.png',
            'start_server': 'buttons/start.png',
            'stop_server': 'buttons/stop.png',
            'restart_server': 'buttons/restart.png',
            
            # Status icons (available)
            'status_online': 'status/online.png',
            'status_offline': 'status/offline.png', 
            'status_starting': 'status/starting.png',
        }
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create icon directories if they don't exist"""
        for category_path in self.categories.values():
            category_path.mkdir(parents=True, exist_ok=True)
    
    def get_icon_path(self, icon_name: str) -> Path:
        """Get the full path to an icon file"""
        if icon_name not in self.icons:
            # Return a default icon or empty path
            return self.icon_path / "misc" / "default.png"
        
        return self.icon_path / self.icons[icon_name]
    
    def get_qicon(self, icon_name: str, size: tuple = None) -> QIcon:
        """
        Get a QIcon for PyQt6 GUI use
        
        Args:
            icon_name: Logical name of the icon
            size: Optional (width, height) tuple for scaling
        
        Returns:
            QIcon object for use in PyQt6 widgets
        """
        icon_path = self.get_icon_path(icon_name)
        
        if not icon_path.exists():
            # Return empty icon if file doesn't exist
            return QIcon()
        
        if size:
            # Create scaled pixmap
            pixmap = QPixmap(str(icon_path))
            scaled_pixmap = pixmap.scaled(
                size[0], size[1], 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            return QIcon(scaled_pixmap)
        
        return QIcon(str(icon_path))
    
    def get_web_icon_url(self, icon_name: str) -> str:
        """
        Get a web-accessible URL for an icon
        
        Args:
            icon_name: Logical name of the icon
        
        Returns:
            Relative URL path for web use
        """
        if icon_name not in self.icons:
            return "/static/icons/misc/default.png"
        
        # Convert to web path format
        return f"/static/icons/{self.icons[icon_name]}"
    
    def get_base64_icon(self, icon_name: str) -> str:
        """
        Get an icon as base64 encoded string for embedding
        
        Args:
            icon_name: Logical name of the icon
            
        Returns:
            Base64 encoded image data
        """
        import base64
        
        icon_path = self.get_icon_path(icon_name)
        
        if not icon_path.exists():
            return ""
        
        try:
            with open(icon_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                file_ext = icon_path.suffix.lower()
                mime_type = 'image/png' if file_ext == '.png' else 'image/jpeg'
                return f"data:{mime_type};base64,{encoded}"
        except Exception:
            return ""
    
    def list_available_icons(self) -> dict:
        """List all available icons by category"""
        available = {}
        
        for icon_name, path in self.icons.items():
            category = path.split('/')[0]
            if category not in available:
                available[category] = []
            
            icon_path = self.get_icon_path(icon_name)
            available[category].append({
                'name': icon_name,
                'path': str(icon_path),
                'exists': icon_path.exists()
            })
        
        return available
    
    def register_icon(self, icon_name: str, relative_path: str):
        """
        Register a new icon in the system
        
        Args:
            icon_name: Logical name for the icon
            relative_path: Path relative to icon directory
        """
        self.icons[icon_name] = relative_path
    
    def get_fallback_emoji(self, icon_name: str) -> str:
        """
        Get emoji fallback for when icons aren't available
        
        Args:
            icon_name: Logical name of the icon
            
        Returns:
            Appropriate emoji character
        """
        emoji_map = {
            'dashboard': '📊',
            'server_management': '🖥️',
            'plugins': '🧩', 
            'console': '💻',
            'settings': '⚙️',
            'create_server': '➕',
            'start_server': '▶️',
            'stop_server': '⏹️',
            'restart_server': '🔄',
            'status_online': '🟢',
            'status_offline': '🔴',
            'status_starting': '🟡',
            'status_error': '🔸',
            'paper_server': '📄',
            'spigot_server': '🔧',
            'vanilla_server': '🍦'
        }
        
        return emoji_map.get(icon_name, '📁')

# Global icon manager instance
icon_manager = IconManager()

def get_icon(name: str) -> QIcon:
    """Convenience function to get QIcon"""
    return icon_manager.get_qicon(name)

def get_icon_path(name: str) -> str:
    """Convenience function to get icon file path"""
    return str(icon_manager.get_icon_path(name))

def get_web_icon(name: str) -> str:
    """Convenience function to get web icon URL"""
    return icon_manager.get_web_icon_url(name)