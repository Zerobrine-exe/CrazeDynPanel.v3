# CrazeDyn Panel - Installation Guide

Welcome to CrazeDyn Panel! This guide will help you install and set up everything you need to run your Minecraft server management panel.

## 📋 Prerequisites

Before running CrazeDyn Panel, you need to install two essential components:

### 1. Java (OpenJDK)
- **Required for**: Running Minecraft servers
- **File**: `openjdk-install.msi` (included in installation folder)
- **Version**: Java 17 or newer recommended

### 2. Python
- **Required for**: Running the CrazeDyn Panel application
- **File**: `python-install.msi` (included in installation folder)
- **Version**: Python 3.8 or newer

---

## 🚀 Installation Steps

### Step 1: Install Java
1. Navigate to your installation folder
2. Double-click `openjdk-install.msi`
3. Follow the installation wizard
4. Accept default settings
5. Click "Install" and wait for completion
6. Restart your computer when prompted

### Step 2: Install Python
1. Double-click `python-install.msi`
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Choose "Install Now"
4. Wait for installation to complete
5. Click "Close"

### Step 3: Verify Installation
1. Open Command Prompt (Windows + R, type `cmd`, press Enter)
2. Type `java -version` and press Enter
   - Should show Java version information
3. Type `python --version` and press Enter
   - Should show Python version information

If both commands show version numbers, you're ready to proceed!

---

## 🎮 Running CrazeDyn Panel

### Option 1: Using the Executable (Recommended)
1. Navigate to the `Main` folder
2. Double-click `CrazeDyn Panel.exe`
3. The application will start automatically

### Option 2: Using Python (For Developers)
1. Open Command Prompt
2. Navigate to the project folder:
   ```
   cd path\to\CrazeDyn-Panel\Main
   ```
3. Install required Python packages:
   ```
   pip install PyQt6 psutil requests
   ```
4. Run the application:
   ```
   python -m app
   ```

---

## 🛠 First-Time Setup

When you first start CrazeDyn Panel:

1. **Create Your First Server**
   - Click "Create Server"
   - Enter server name and settings
   - Choose storage allocation (1-100 GB)
   - Select Paper MC version
   - Set memory allocation (RAM)

2. **Server Management**
   - Use the dashboard to start/stop servers
   - View real-time statistics in the sidebar
   - Access console, file browser, and configuration

3. **Plugin Installation**
   - Browse and install plugins from the built-in browser
   - Manage existing plugins through the interface
   - Configure plugin settings easily

---

## 📊 System Requirements

### Minimum Requirements:
- **OS**: Windows 10/11
- **RAM**: 4 GB (8 GB recommended)
- **Storage**: 10 GB free space
- **CPU**: Dual-core processor
- **Network**: Internet connection for downloads

### Recommended for Multiple Servers:
- **RAM**: 16 GB or more
- **Storage**: 50 GB+ free space
- **CPU**: Quad-core processor
- **Network**: Stable broadband connection

---

## 🔧 Troubleshooting

### Java Not Found Error
- Reinstall Java using `openjdk-install.msi`
- Restart your computer
- Verify with `java -version` in Command Prompt

### Python Import Errors
- Reinstall Python with "Add to PATH" checked
- Run: `pip install PyQt6 psutil requests`
- Restart the application

### Server Won't Start
- Check if Java is installed correctly
- Verify server files were downloaded
- Check available RAM and disk space
- Review console output for error messages

### Port Already in Use
- Change server port in server settings
- Default port is 25565
- Each server needs a unique port

---

## 💡 Tips for Best Performance

1. **Memory Allocation**
   - Don't allocate more RAM than available
   - Leave 2-4 GB for your operating system
   - Monitor usage in the stats sidebar

2. **Storage Management**
   - Set appropriate storage limits during creation
   - Monitor disk usage in real-time
   - Clean up old backups and logs regularly

3. **Network Configuration**
   - Use Playit.gg plugin for easy external access
   - Configure firewall if needed
   - Port forward manually if required

---

## 📞 Need Help?

If you encounter issues:
1. Check this guide first
2. Look at console output for error messages
3. Verify Java and Python installations
4. Restart the application
5. Restart your computer if needed

---

## 🎉 You're Ready!

Congratulations! You now have CrazeDyn Panel installed and ready to manage your Minecraft servers like a pro. 

Create your first server and start building your Minecraft community today!