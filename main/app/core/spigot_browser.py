#!/usr/bin/env python3
"""
SpigotMC Plugin Browser
Searches and downloads plugins from SpigotMC using Spiget API
"""

import requests
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class PluginInfo:
    """Plugin information from SpigotMC"""
    id: str
    name: str
    description: str = ""
    author: str = ""
    version: str = ""
    downloads: int = 0
    rating: float = 0.0
    category: str = ""
    premium: bool = False
    updated: str = ""
    download_url: str = ""
    url: str = ""

class SpigotMCBrowser:
    """Browser for SpigotMC plugins using Spiget API"""
    
    def __init__(self):
        self.base_url = "https://api.spiget.org/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CrazeDyn Panel Plugin Browser 1.0'
        })
    
    def search_plugins(self, query: str = "", category: str = None, sort: str = "downloads", size: int = 20) -> Tuple[List[PluginInfo], int]:
        """Search plugins on SpigotMC"""
        try:
            # Build search URL
            url = f"{self.base_url}/resources"
            params = {
                'size': min(size, 100),  # Limit to reasonable size
                'sort': f"-{sort}" if sort in ['downloads', 'rating', 'updated'] else "-downloads"
            }
            
            if query:
                params['search'] = query
            
            if category:
                params['category'] = category
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            plugins = []
            
            for item in data:
                try:
                    plugin = PluginInfo(
                        id=str(item.get('id', '')),
                        name=item.get('name', 'Unknown'),
                        description=item.get('tag', ''),
                        author=item.get('author', {}).get('name', 'Unknown'),
                        version=item.get('version', {}).get('name', 'Unknown'),
                        downloads=item.get('downloads', 0),
                        rating=float(item.get('rating', {}).get('average', 0)),
                        category=item.get('category', {}).get('name', 'General'),
                        premium=item.get('premium', False),
                        updated=self._format_date(item.get('updateDate', 0)),
                        download_url=f"https://api.spiget.org/v2/resources/{item.get('id')}/download",
                        url=f"https://www.spigotmc.org/resources/{item.get('id')}"
                    )
                    plugins.append(plugin)
                except Exception as e:
                    continue  # Skip malformed entries
            
            return plugins, len(plugins)
            
        except Exception as e:
            print(f"Error searching plugins: {e}")
            return [], 0
    
    def get_popular_plugins(self, count: int = 20) -> List[PluginInfo]:
        """Get popular plugins"""
        plugins, _ = self.search_plugins(sort="downloads", size=count)
        return plugins
    
    def get_plugin_details(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get detailed information about a plugin"""
        try:
            url = f"{self.base_url}/resources/{plugin_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            item = response.json()
            
            plugin = PluginInfo(
                id=str(item.get('id', '')),
                name=item.get('name', 'Unknown'),
                description=item.get('description', ''),
                author=item.get('author', {}).get('name', 'Unknown'),
                version=item.get('version', {}).get('name', 'Unknown'),
                downloads=item.get('downloads', 0),
                rating=float(item.get('rating', {}).get('average', 0)),
                category=item.get('category', {}).get('name', 'General'),
                premium=item.get('premium', False),
                updated=self._format_date(item.get('updateDate', 0)),
                download_url=f"https://api.spiget.org/v2/resources/{plugin_id}/download",
                url=f"https://www.spigotmc.org/resources/{plugin_id}"
            )
            
            return plugin
            
        except Exception as e:
            print(f"Error getting plugin details: {e}")
            return None
    
    def download_plugin(self, plugin: PluginInfo, destination: Path) -> bool:
        """Download a plugin to the specified destination"""
        try:
            if plugin.premium:
                print(f"❌ {plugin.name} is a premium plugin and requires manual purchase")
                return False
            
            print(f"📥 Downloading {plugin.name}...")
            
            # Download the plugin
            response = self.session.get(plugin.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get filename from Content-Disposition header or use plugin name
            filename = f"{plugin.name}.jar"
            if 'content-disposition' in response.headers:
                import re
                cd = response.headers['content-disposition']
                match = re.findall('filename=(.+)', cd)
                if match:
                    filename = match[0].strip('"')
            
            # Ensure .jar extension
            if not filename.endswith('.jar'):
                filename += '.jar'
            
            file_path = destination / filename
            
            # Write file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✅ Downloaded {plugin.name} to {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {plugin.name}: {e}")
            return False
    
    def _format_date(self, timestamp: int) -> str:
        """Format timestamp to readable date"""
        try:
            if timestamp > 0:
                return time.strftime('%Y-%m-%d', time.localtime(timestamp / 1000))
            return "Unknown"
        except:
            return "Unknown"
    
    def get_categories(self) -> List[str]:
        """Get available plugin categories"""
        try:
            url = f"{self.base_url}/categories"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return [cat.get('name', '') for cat in data if cat.get('name')]
            
        except Exception as e:
            print(f"Error getting categories: {e}")
            return [
                "Admin Tools", "Anti-Griefing Tools", "Chat Related", 
                "Developer Tools", "Economy", "Fun", "General", 
                "Mechanics", "Miscellaneous", "Transportation", "World Management"
            ]