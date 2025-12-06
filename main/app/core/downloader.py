import requests
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import urllib.parse
import tempfile
import platform


class PaperMCDownloader:
    """Downloads PaperMC server jars and manages versions"""

    def __init__(self):
        self.versions_cache = None
# OLD PLAYIT PLUGIN SYSTEM REMOVED - Now using official MSI installer

        # Basic plugin pack URLs
        self.basic_plugin_pack = {
            "ServerNaptime":
            "https://github.com/gvk/MinecraftPluginServerHibernate/releases/download/v1.0/ServerNaptime.jar",
            "ViaBackwards":
            "https://github.com/ViaVersion/ViaBackwards/releases/download/5.4.2/ViaBackwards-5.4.2.jar",
            "ViaVersion":
            "https://github.com/ViaVersion/ViaVersion/releases/download/5.4.2/ViaVersion-5.4.2.jar",
            "EssentialsX":
            "https://github.com/EssentialsX/Essentials/releases/download/2.21.2/EssentialsX-2.21.2.jar",
            "Geyser":
            "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot",
            "Floodgate":
            "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot",
            "AuthMe":
            "https://github.com/AuthMe/AuthMeReloaded/releases/download/5.6.0/AuthMe-5.6.0.jar"
        }

    def get_paper_versions(self, use_cache: bool = True) -> Dict[str, str]:
        """Get available PaperMC versions"""
        if self.versions_cache and use_cache:
            return self.versions_cache

        try:
            # Try to load from local file first
            versions_file = Path(__file__).parent.parent / "paper_versions.json"
            if versions_file.exists():
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                    self.versions_cache = data.get("versions", {})
                    return self.versions_cache

            # Fallback to hardcoded versions if file not found
            fallback_versions = {
                "1.21.8":
                "https://api.papermc.io/v2/projects/paper/versions/1.21.8/builds/39/downloads/paper-1.21.8-39.jar",
                "1.21.7":
                "https://api.papermc.io/v2/projects/paper/versions/1.21.7/builds/32/downloads/paper-1.21.7-32.jar",
                "1.21.6":
                "https://api.papermc.io/v2/projects/paper/versions/1.21.6/builds/48/downloads/paper-1.21.6-48.jar",
                "1.21.5":
                "https://api.papermc.io/v2/projects/paper/versions/1.21.5/builds/114/downloads/paper-1.21.5-114.jar",
                "1.21.4":
                "https://api.papermc.io/v2/projects/paper/versions/1.21.4/builds/232/downloads/paper-1.21.4-232.jar",
                "1.20.6":
                "https://api.papermc.io/v2/projects/paper/versions/1.20.6/builds/151/downloads/paper-1.20.6-151.jar",
                "1.20.4":
                "https://api.papermc.io/v2/projects/paper/versions/1.20.4/builds/499/downloads/paper-1.20.4-499.jar",
                "1.19.4":
                "https://api.papermc.io/v2/projects/paper/versions/1.19.4/builds/550/downloads/paper-1.19.4-550.jar"
            }

            self.versions_cache = fallback_versions
            return self.versions_cache

        except Exception as e:
            print(f"Error loading PaperMC versions: {e}")
            return {}

    def get_latest_version(self) -> str:
        """Get the latest PaperMC version"""
        versions = self.get_paper_versions()
        if versions:
            # Return the first version (should be latest)
            return list(versions.keys())[0]
        return "1.21.8"  # Fallback

    def download_paper_jar(
        self,
        version: str,
        destination: Path,
        progress_callback: Optional[Callable[[int, int],
                                             None]] = None) -> bool:
        """Download PaperMC jar file"""
        try:
            versions = self.get_paper_versions()
            if version not in versions:
                print(f"Version {version} not found")
                return False

            url = versions[version]
            jar_name = f"paper-{version}.jar"
            jar_path = destination / jar_name

            print(f"Downloading {jar_name}...")

            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(jar_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

            print(f"Downloaded {jar_name} successfully")
            return True

        except Exception as e:
            print(f"Error downloading PaperMC jar: {e}")
            return False

# OLD PLAYIT PLUGIN DOWNLOAD METHOD REMOVED
    # Now using official Playit MSI installer integration

    def download_server_files(
        self,
        version: str,
        server_path: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """Download server jar (Playit integration now uses official MSI installer)"""
        # Create plugins directory for future plugin installations
        plugins_path = server_path / "plugins"
        plugins_path.mkdir(exist_ok=True)

        # Download server jar
        def jar_progress(downloaded, total):
            if progress_callback:
                progress_callback("server_jar", downloaded, total)

        return self.download_paper_jar(version, server_path, jar_progress)

    def download_basic_plugin_pack(
        self,
        plugins_path: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, bool]:
        """Download basic plugin pack to the plugins directory"""
        results = {}

        # Ensure plugins directory exists
        plugins_path.mkdir(parents=True, exist_ok=True)

        print("\n📦 Downloading Basic Plugin Pack...")
        print("─" * 50)

        for plugin_name, url in self.basic_plugin_pack.items():
            try:
                print(f"\n🔽 Downloading {plugin_name}...")

                # Determine filename
                if plugin_name in ["Geyser", "Floodgate"]:
                    filename = f"{plugin_name}-Spigot.jar"
                else:
                    filename = f"{plugin_name}.jar"

                plugin_path = plugins_path / filename

                # Download with progress
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                # Get file size
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(plugin_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if progress_callback:
                                progress_callback(plugin_name, downloaded,
                                                  total_size)
                            elif total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(
                                    f"\r  📊 Progress: {progress:.1f}% ({downloaded:,}/{total_size:,} bytes)",
                                    end="",
                                    flush=True)

                print(f"\r  ✅ {plugin_name} downloaded successfully!")
                results[plugin_name] = True

            except Exception as e:
                print(f"\r  ❌ Failed to download {plugin_name}: {str(e)}")
                results[plugin_name] = False

        print("\n" + "─" * 50)
        print("\n📋 Plugin Pack Download Summary:")
        for plugin_name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  • {plugin_name}: {status}")

        successful = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"\n🎯 Downloaded {successful}/{total} plugins successfully!")

        if "Geyser" in results or "Floodgate" in results:
            print(
                "\n⚠️  Note: GeyserMC and Floodgate may require manual setup if automatic configuration cannot be applied."
            )

        return results

    @staticmethod
    def ask_install_plugin_pack() -> bool:
        """Ask user if they want to install the basic plugin pack"""
        while True:
            print("\n" + "═" * 60)
            print("📦 BASIC PLUGIN PACK INSTALLATION")
            print("═" * 60)
            print("\nWould you like to install a basic plugin pack?")
            print("\nThis pack includes:")
            print("  🔧 ServerNaptime - Server hibernation when empty")
            print("  🔗 ViaVersion & ViaBackwards - Multi-version support")
            print("  ⚡ EssentialsX - Essential server commands")
            print("  🌐 Geyser & Floodgate - Bedrock Edition support")
            print("\n📝 Note: GeyserMC and Floodgate may require manual setup.")
            print("\nInstall basic plugin pack? (y/n): ", end="")

            try:
                choice = input().strip().lower()
                if choice in ['y', 'yes']:
                    return True
                elif choice in ['n', 'no']:
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no.")
            except (EOFError, KeyboardInterrupt):
                print("\n\n🚫 Installation cancelled by user.")
                return False


class DependencyChecker:
    """Checks and validates system dependencies"""

    @staticmethod
    def download_java_windows(
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[str]:
        """Download OpenJDK 21 MSI for Windows"""
        try:
            # OpenJDK 21 MSI URL
            java_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.8%2B9/OpenJDK21U-jdk_x64_windows_hotspot_21.0.8_9.msi"

            # Create temp directory for download
            temp_dir = Path(tempfile.gettempdir()) / "crazedyn_java"
            temp_dir.mkdir(exist_ok=True)

            msi_path = temp_dir / "OpenJDK21U-jdk_x64_windows_hotspot_21.0.8_9.msi"

            print("Downloading OpenJDK 21 for Windows...")

            response = requests.get(java_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(msi_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

            print(f"Downloaded OpenJDK 21 MSI to {msi_path}")
            return str(msi_path)

        except Exception as e:
            print(f"Error downloading Java: {e}")
            return None

    @staticmethod
    def install_java_windows(msi_path: str) -> bool:
        """Install Java MSI silently without desktop shortcut"""
        try:
            print("Installing OpenJDK 21...")

            # Verify MSI file exists and is valid
            msi_file = Path(msi_path)
            if not msi_file.exists():
                print(f"MSI file not found: {msi_path}")
                return False

            # Check file size (should be around 200MB for OpenJDK)
            file_size = msi_file.stat().st_size
            if file_size < 50 * 1024 * 1024:  # Less than 50MB is suspicious
                print(
                    f"MSI file seems too small ({file_size} bytes), may be corrupted"
                )
                return False

            print(f"MSI file verified: {file_size} bytes")

            # Try multiple installation approaches
            install_approaches = [
                # Approach 1: Simple installation with minimal parameters
                ["msiexec", "/i",
                 str(msi_path), "/quiet", "/norestart"],
                # Approach 2: Installation with specific features
                [
                    "msiexec",
                    "/i",
                    str(msi_path),
                    "/qn",  # Completely silent
                    "/norestart",
                    "ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith"
                ],
                # Approach 3: Basic installation with logging
                [
                    "msiexec", "/i",
                    str(msi_path), "/quiet", "/norestart", "/L*v",
                    str(Path(tempfile.gettempdir()) / "java_install.log")
                ]
            ]

            for i, cmd in enumerate(install_approaches, 1):
                print(f"Attempting installation method {i}/3...")

                try:
                    # Run the installer
                    result = subprocess.run(cmd,
                                            capture_output=True,
                                            text=True,
                                            timeout=600)

                    if result.returncode == 0:
                        print("Java installation completed successfully")

                        # Add Java to PATH if not already there
                        possible_java_paths = [
                            "C:\\Program Files\\Eclipse Adoptium\\jdk-21.0.8.9-hotspot\\bin",
                            "C:\\Program Files\\Eclipse Adoptium\\jre-21.0.8.9-hotspot\\bin",
                            "C:\\Program Files (x86)\\Eclipse Adoptium\\jdk-21.0.8.9-hotspot\\bin"
                        ]

                        java_added = False
                        for java_bin_path in possible_java_paths:
                            if Path(java_bin_path).exists():
                                current_path = os.environ.get('PATH', '')
                                if java_bin_path not in current_path:
                                    os.environ[
                                        'PATH'] = f"{java_bin_path};{current_path}"
                                    print(
                                        f"Added Java to PATH: {java_bin_path}")
                                java_added = True
                                break

                        if not java_added:
                            print(
                                "Warning: Could not automatically add Java to PATH"
                            )

                        # Clean up downloaded MSI
                        try:
                            os.remove(msi_path)
                            print("Cleaned up installation file")
                        except:
                            pass

                        return True

                    elif result.returncode == 1639:
                        print(
                            f"Installation method {i} failed: Invalid MSI package (error 1639)"
                        )
                        if i < len(install_approaches):
                            print("Trying alternative installation method...")
                            continue
                    elif result.returncode == 1618:
                        print(
                            f"Installation method {i} failed: Another installation in progress (error 1618)"
                        )
                        print(
                            "Please wait for other installations to complete and try again"
                        )
                        return False
                    elif result.returncode == 1602:
                        print(
                            f"Installation method {i} failed: User cancelled installation (error 1602)"
                        )
                        if i < len(install_approaches):
                            continue
                    else:
                        print(
                            f"Installation method {i} failed with code {result.returncode}"
                        )
                        if result.stderr:
                            print(f"Error details: {result.stderr}")
                        if i < len(install_approaches):
                            print("Trying alternative installation method...")
                            continue

                except subprocess.TimeoutExpired:
                    print(f"Installation method {i} timed out")
                    if i < len(install_approaches):
                        continue
                except Exception as e:
                    print(
                        f"Installation method {i} failed with exception: {e}")
                    if i < len(install_approaches):
                        continue

            # If all methods failed, provide user guidance
            print("All automatic installation methods failed.")
            print("Please try one of the following:")
            print(
                f"1. Run the installer manually as Administrator: {msi_path}")
            print(
                "2. Download and install Java manually from: https://adoptium.net/"
            )
            print("3. Ensure no other installations are running")
            return False

        except Exception as e:
            print(f"Error during Java installation: {e}")
            return False

    @staticmethod
    def check_java() -> Dict[str, Any]:
        """Check if Java is installed and get version info"""
        result = {
            "installed": False,
            "version": None,
            "path": None,
            "compatible": False
        }

        try:
            output = subprocess.check_output(["java", "-version"],
                                             stderr=subprocess.STDOUT,
                                             text=True)

            result["installed"] = True

            # Parse version from output
            lines = output.split('\n')
            for line in lines:
                if 'version' in line.lower():
                    # Extract version number
                    import re
                    version_match = re.search(r'"([^"]*)"', line)
                    if version_match:
                        version_str = version_match.group(1)
                        result["version"] = version_str

                        # Check if version is 17 or higher
                        try:
                            major_version = int(version_str.split('.')[0])
                            if major_version >= 17:
                                result["compatible"] = True
                        except:
                            # Try alternative version format
                            if version_str.startswith("1."):
                                try:
                                    minor_version = int(
                                        version_str.split('.')[1])
                                    if minor_version >= 17:
                                        result["compatible"] = True
                                except:
                                    pass
                    break

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # If Java not installed or not compatible on Windows, try to install it
        if (not result["installed"] or
                not result["compatible"]) and platform.system() == "Windows":
            print(
                "Java 17+ not found on Windows. Attempting to install OpenJDK 21..."
            )

            # Download Java MSI
            msi_path = DependencyChecker.download_java_windows()
            if msi_path:
                # Install Java
                if DependencyChecker.install_java_windows(msi_path):
                    print("Java installation successful. Rechecking...")
                    # Recheck Java after installation
                    return DependencyChecker.check_java()
                else:
                    print("Java installation failed")
            else:
                print("Failed to download Java installer")

        return result

    @staticmethod
    def check_python() -> Dict[str, Any]:
        """Check Python installation"""
        result = {
            "installed": True,  # We're running in Python
            "version": None,
            "compatible": True
        }

        try:
            import sys
            result[
                "version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            # Check if version is 3.8 or higher
            if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
                result["compatible"] = True
            else:
                result["compatible"] = False

        except:
            result["installed"] = False
            result["compatible"] = False

        return result

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information"""
        import platform
        import psutil

        return {
            "os":
            platform.system(),
            "os_version":
            platform.version(),
            "architecture":
            platform.architecture()[0],
            "processor":
            platform.processor(),
            "total_ram":
            round(psutil.virtual_memory().total / (1024**3), 2),  # GB
            "available_ram":
            round(psutil.virtual_memory().available / (1024**3), 2),  # GB
            "cpu_count":
            psutil.cpu_count()
        }
