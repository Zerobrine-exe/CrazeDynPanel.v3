import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                            QListWidget, QTextEdit, QProgressBar, QComboBox,
                            QLineEdit, QSpinBox, QGroupBox, QGridLayout,
                            QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
                            QFrame, QSplitter, QTreeWidget, QTreeWidgetItem,
                            QScrollArea, QCheckBox, QPushButton, QFileDialog,
                            QPlainTextEdit, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from typing import List

# Import core modules
sys.path.append(str(Path(__file__).parent.parent))
from core.server_manager import ServerManager, MinecraftServer
from core.downloader import PaperMCDownloader, DependencyChecker
from core.spigot_browser import SpigotMCBrowser as SpigotBrowser, PluginInfo
from utils.server_stats_monitor import ServerStatsMonitor
from utils.icon_manager import icon_manager, get_icon

class ModernButton(QPushButton):
    """Modern styled button with hover effects"""
    
    def __init__(self, text: str, primary: bool = False):
        super().__init__(text)
        self.primary = primary
        self.setStyleSheet(self._get_style())
        
    def _get_style(self):
        if self.primary:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                               stop:0 #00d4ff, stop:1 #0099cc);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                               stop:0 #00e6ff, stop:1 #00aadd);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                               stop:0 #0099cc, stop:1 #007799);
                }
            """
        else:
            return """
                QPushButton {
                    background: #2d3142;
                    color: #e6e6e6;
                    border: 1px solid #4f5565;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #3d4152;
                    border-color: #00d4ff;
                }
                QPushButton:pressed {
                    background: #1d2132;
                }
            """

class StatusIndicator(QLabel):
    """Animated status indicator"""
    
    def __init__(self, status: str = "stopped"):
        super().__init__()
        self.status = status
        self.setFixedSize(20, 20)
        self.update_status(status)
        
    def update_status(self, status: str):
        self.status = status
        colors = {
            "running": "#00ff88",
            "starting": "#ffaa00", 
            "stopping": "#ff6600",
            "stopped": "#ff4444",
            "unknown": "#888888"
        }
        
        color = colors.get(status, "#888888")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 10px;
                border: 2px solid #333;
            }}
        """)

class ServerCard(QFrame):
    """Individual server card widget"""
    
    def __init__(self, server: MinecraftServer, parent=None):
        super().__init__(parent)
        self.server = server
        self.parent_window = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #2d3142;
                border: 1px solid #4f5565;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #00d4ff;
                background: #3d4152;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with name and status
        header = QHBoxLayout()
        
        # Server name
        name_label = QLabel(self.server.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e6e6e6;")
        header.addWidget(name_label)
        
        header.addStretch()
        
        # Status indicator
        self.status_indicator = StatusIndicator(self.server.status)
        header.addWidget(self.status_indicator)
        
        layout.addLayout(header)
        
        # Server info
        info_layout = QGridLayout()
        
        # Version
        info_layout.addWidget(QLabel("Version:"), 0, 0)
        version_label = QLabel(self.server.jar.replace("paper-", "").replace(".jar", ""))
        version_label.setStyleSheet("color: #00d4ff;")
        info_layout.addWidget(version_label, 0, 1)
        
        # RAM
        info_layout.addWidget(QLabel("RAM:"), 1, 0)
        ram_label = QLabel(f"{self.server.min_ram} - {self.server.max_ram}")
        ram_label.setStyleSheet("color: #00ff88;")
        info_layout.addWidget(ram_label, 1, 1)
        
        # Port
        info_layout.addWidget(QLabel("Port:"), 2, 0)
        port_label = QLabel(str(self.server.port))
        port_label.setStyleSheet("color: #ffaa00;")
        info_layout.addWidget(port_label, 2, 1)
        
        layout.addLayout(info_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.start_btn = ModernButton("Start", primary=True)
        self.start_btn.clicked.connect(self.start_server)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = ModernButton("Stop")
        self.stop_btn.clicked.connect(self.stop_server)
        
        self.restart_btn = ModernButton("Restart")
        self.restart_btn.clicked.connect(self.restart_server)
        buttons_layout.addWidget(self.restart_btn)
        
        # Manage button to open detailed view
        self.manage_btn = ModernButton("Manage", primary=False)
        self.manage_btn.clicked.connect(self.open_server_detail)
        buttons_layout.addWidget(self.manage_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        self.restart_btn = ModernButton("Restart")
        self.restart_btn.clicked.connect(self.restart_server)
        buttons_layout.addWidget(self.restart_btn)
        
        layout.addLayout(buttons_layout)
        
        self.update_buttons()
        
    def update_status(self, status: str):
        self.server.status = status
        self.status_indicator.update_status(status)
        self.update_buttons()
        
    def update_buttons(self):
        running = self.server.status == "running"
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.restart_btn.setEnabled(running)
        
    def start_server(self):
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            self.parent_window.server_manager.start_server(self.server.name)
            
    def stop_server(self):
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            self.parent_window.server_manager.stop_server(self.server.name)
            
    def restart_server(self):
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            self.parent_window.server_manager.restart_server(self.server.name)
    
    def open_server_detail(self):
        """Open detailed server management window"""
        if self.parent_window:
            detail_window = ServerDetailWindow(self.server, self.parent_window.server_manager, self.parent_window)
            detail_window.show()

class CreateServerDialog(QDialog):
    """Dialog for creating new servers"""
    
    def __init__(self, downloader: PaperMCDownloader, parent=None):
        super().__init__(parent)
        self.downloader = downloader
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Create New Minecraft Server")
        self.setModal(True)
        self.resize(500, 400)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background: #1e1f29;
                color: #e6e6e6;
            }
            QLabel {
                color: #e6e6e6;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #2d3142;
                color: #e6e6e6;
                border: 1px solid #4f5565;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #00d4ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        
        # Server name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("My Awesome Server")
        form.addRow("Server Name:", self.name_edit)
        
        # Version selection
        self.version_combo = QComboBox()
        versions = self.downloader.get_paper_versions()
        for version in versions.keys():
            self.version_combo.addItem(version)
        form.addRow("Paper Version:", self.version_combo)
        
        # RAM settings
        ram_layout = QHBoxLayout()
        
        self.min_ram_spin = QSpinBox()
        self.min_ram_spin.setRange(1, 32)
        self.min_ram_spin.setValue(2)
        self.min_ram_spin.setSuffix(" GB")
        ram_layout.addWidget(QLabel("Min:"))
        ram_layout.addWidget(self.min_ram_spin)
        
        self.max_ram_spin = QSpinBox()
        self.max_ram_spin.setRange(1, 32)
        self.max_ram_spin.setValue(4)
        self.max_ram_spin.setSuffix(" GB")
        ram_layout.addWidget(QLabel("Max:"))
        ram_layout.addWidget(self.max_ram_spin)
        
        ram_widget = QWidget()
        ram_widget.setLayout(ram_layout)
        form.addRow("RAM Allocation:", ram_widget)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(25565)
        form.addRow("Server Port:", self.port_spin)
        
        # Storage Allocation
        self.storage_spin = QSpinBox()
        self.storage_spin.setRange(1, 100)
        self.storage_spin.setValue(10)
        self.storage_spin.setSuffix(" GB")
        form.addRow("Storage Max:", self.storage_spin)
        
        # Storage path
        self.path_edit = QLineEdit()
        current_dir = os.getcwd()
        self.path_edit.setText(os.path.join(current_dir, "servers"))
        form.addRow("Storage Path:", self.path_edit)
        
        # Plugin pack installation checkbox
        self.plugin_pack_checkbox = QCheckBox("Install Basic Plugin Pack")
        self.plugin_pack_checkbox.setChecked(True)
        self.plugin_pack_checkbox.setStyleSheet("""
            QCheckBox {
                color: #e6e6e6;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background: #2d3142;
                border: 2px solid #4f5565;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #00d4ff;
                border: 2px solid #00d4ff;
                border-radius: 3px;
            }
        """)
        
        # Plugin pack description
        plugin_desc = QLabel("Includes: EssentialsX, ViaVersion, ViaBackwards, ServerNaptime, Geyser, Floodgate")
        plugin_desc.setStyleSheet("color: #888; font-size: 11px; margin-left: 25px;")
        plugin_desc.setWordWrap(True)
        
        # Add plugin pack section
        form.addRow("", self.plugin_pack_checkbox)
        form.addRow("", plugin_desc)
        
        # Playit.gg integration section
        playit_layout = QHBoxLayout()
        self.playit_checkbox = QCheckBox("Enable Playit.gg Remote Access")
        self.playit_checkbox.setChecked(False)
        self.playit_checkbox.setStyleSheet("""
            QCheckBox {
                color: #e6e6e6;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background: #2d3142;
                border: 2px solid #4f5565;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #00d4ff;
                border: 2px solid #00d4ff;
                border-radius: 3px;
            }
        """)
        
        self.playit_status_label = QLabel("❌ Not Installed")
        self.playit_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 11px;")
        
        playit_layout.addWidget(self.playit_checkbox)
        playit_layout.addWidget(self.playit_status_label)
        playit_layout.addStretch()
        
        playit_widget = QWidget()
        playit_widget.setLayout(playit_layout)
        
        # Playit description
        playit_desc = QLabel("🌐 Make your server accessible worldwide through Playit.gg tunneling")
        playit_desc.setStyleSheet("color: #888; font-size: 11px; margin-left: 25px;")
        playit_desc.setWordWrap(True)
        
        # Add Playit section
        form.addRow("", playit_widget)
        form.addRow("", playit_desc)
        
        layout.addLayout(form)
        
        # Update Playit status after UI setup
        self.update_playit_status()
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #00d4ff;")
        layout.addWidget(self.status_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                  QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_server_config(self):
        """Get the server configuration from the dialog"""
        return {
            "name": self.name_edit.text().strip(),
            "version": self.version_combo.currentText(),
            "min_ram": f"{self.min_ram_spin.value()}G",
            "max_ram": f"{self.max_ram_spin.value()}G",
            "port": self.port_spin.value(),
            "path": self.path_edit.text().strip(),
            "storage_limit": self.storage_spin.value(),
            "install_plugins": self.plugin_pack_checkbox.isChecked(),
            "enable_playit": self.playit_checkbox.isChecked()
        }
    
    def update_playit_status(self):
        """Update the Playit status display"""
        try:
            from playit_manager import playit_manager
            status_message = playit_manager.get_playit_status_message()
            self.playit_status_label.setText(status_message)
            
            if "Installed" in status_message:
                self.playit_status_label.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 11px;")
            else:
                self.playit_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 11px;")
        except Exception as e:
            self.playit_status_label.setText("❌ Error")
            self.playit_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 11px;")

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = ServerManager("Main/servers.json")
        self.downloader = PaperMCDownloader()
        self.server_cards = {}
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        self.setWindowTitle("CrazeDynPanel v2.0 - Professional Server Manager - Made by Zerobrine")
        self.setGeometry(100, 100, 1400, 900)  # Slightly larger for v2.0
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1f29;
                color: #e6e6e6;
            }
            QTabWidget::pane {
                border: 1px solid #4f5565;
                background: #1e1f29;
            }
            QTabBar::tab {
                background: #2d3142;
                color: #e6e6e6;
                padding: 10px 20px;
                border: 1px solid #4f5565;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #00d4ff;
                color: #1e1f29;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #3d4152;
            }
        """)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header with v2.0 branding
        header = QVBoxLayout()
        
        # Main title
        title_layout = QHBoxLayout()
        title = QLabel("🎮 CrazeDynPanel v2.0")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00d4ff; padding: 5px;")
        title_layout.addWidget(title)
        
        # Made by Zerobrine
        creator = QLabel("Made by Zerobrine")
        creator.setStyleSheet("font-size: 14px; color: #888; margin-left: 10px; font-style: italic;")
        title_layout.addWidget(creator)
        
        title_layout.addStretch()
        
        # Create server button with icon
        create_btn = ModernButton("+ Create Server", primary=True)
        create_icon = get_icon('create_server')
        if not create_icon.isNull():
            create_btn.setIcon(create_icon)
        create_btn.clicked.connect(self.create_server)
        title_layout.addWidget(create_btn)
        
        header.addLayout(title_layout)
        
        # Social links
        social_layout = QHBoxLayout()
        discord_label = QLabel("🔗 Discord: https://dc.gg/zerocloud")
        discord_label.setStyleSheet("font-size: 12px; color: #00d4ff; padding: 2px;")
        social_layout.addWidget(discord_label)
        
        youtube_label = QLabel("📺 YouTube: https://www.youtube.com/@Zerobrine_7")
        youtube_label.setStyleSheet("font-size: 12px; color: #ff6b6b; padding: 2px;")
        social_layout.addWidget(youtube_label)
        
        social_layout.addStretch()
        
        header.addLayout(social_layout)
        
        # Professional tagline
        tagline = QLabel("✨ Professional Edition • Advanced Plugin Management • Premium Features")
        tagline.setStyleSheet("font-size: 11px; color: #666; padding: 2px; text-align: center;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(tagline)
        
        layout.addLayout(header)
        
        # Tab widget with professional icons
        self.tab_widget = QTabWidget()
        
        # Dashboard tab
        self.dashboard_tab = self.create_dashboard_tab()
        dashboard_icon = get_icon('dashboard')
        if not dashboard_icon.isNull():
            self.tab_widget.addTab(self.dashboard_tab, dashboard_icon, "Dashboard")
        else:
            self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
        
        # Console tab
        self.console_tab = self.create_console_tab()
        console_icon = get_icon('console')
        if not console_icon.isNull():
            self.tab_widget.addTab(self.console_tab, console_icon, "Console")
        else:
            self.tab_widget.addTab(self.console_tab, "💻 Console")
        
        # Settings tab
        self.settings_tab = self.create_settings_tab()
        settings_icon = get_icon('settings')
        if not settings_icon.isNull():
            self.tab_widget.addTab(self.settings_tab, settings_icon, "Settings")
        else:
            self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        
        layout.addWidget(self.tab_widget)
        
        # Load existing servers
        self.refresh_servers()
        
    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Server list
        self.server_list_widget = QWidget()
        self.server_list_layout = QVBoxLayout(self.server_list_widget)
        
        # Scroll area would be better, but for now just vertical layout
        layout.addWidget(self.server_list_widget)
        
        return widget
        
    def create_console_tab(self):
        """Create the console tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Server selection
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        
        self.console_server_combo = QComboBox()
        server_layout.addWidget(self.console_server_combo)
        
        server_layout.addStretch()
        
        layout.addLayout(server_layout)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.console_output)
        
        # Command input
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Command:"))
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter server command...")
        self.command_input.returnPressed.connect(self.send_command)
        command_layout.addWidget(self.command_input)
        
        send_btn = ModernButton("Send")
        send_btn.clicked.connect(self.send_command)
        command_layout.addWidget(send_btn)
        
        layout.addLayout(command_layout)
        
        return widget
        
    def create_settings_tab(self):
        """Create the settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # System info group
        sys_group = QGroupBox("System Information")
        sys_layout = QFormLayout(sys_group)
        
        # Check dependencies
        java_info = DependencyChecker.check_java()
        python_info = DependencyChecker.check_python()
        system_info = DependencyChecker.get_system_info()
        
        java_status = "✅ Compatible" if java_info.get("compatible") else "❌ Needs Update"
        sys_layout.addRow("Java:", QLabel(f"{java_info.get('version', 'Not Found')} - {java_status}"))
        
        python_status = "✅ Compatible" if python_info.get("compatible") else "❌ Needs Update"
        sys_layout.addRow("Python:", QLabel(f"{python_info.get('version', 'Not Found')} - {python_status}"))
        
        sys_layout.addRow("OS:", QLabel(f"{system_info.get('os')} {system_info.get('architecture')}"))
        sys_layout.addRow("RAM:", QLabel(f"{system_info.get('total_ram')} GB"))
        sys_layout.addRow("CPU:", QLabel(f"{system_info.get('cpu_count')} cores"))
        
        layout.addWidget(sys_group)
        
        # Performance settings group
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)
        
        # Performance mode checkbox
        self.performance_mode_cb = QCheckBox("Performance Mode (Reduces monitoring frequency)")
        self.performance_mode_cb.setChecked(False)
        self.performance_mode_cb.toggled.connect(self.toggle_performance_mode)
        perf_layout.addRow(self.performance_mode_cb)
        
        # Network optimization checkbox
        self.network_optimization_cb = QCheckBox("Network Optimization (Reduces ping for local play)")
        self.network_optimization_cb.setChecked(True)
        perf_layout.addRow(self.network_optimization_cb)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
        
        return widget
    
    def toggle_performance_mode(self, enabled):
        """Toggle performance mode on/off"""
        if enabled:
            # Reduce monitoring frequency to minimum
            self.update_timer.stop()
            self.update_timer.start(30000)  # Update every 30 seconds in performance mode
            
            # Reduce server stats monitoring
            for card in self.server_cards.values():
                if hasattr(card, 'stats_monitor'):
                    card.stats_monitor.stop_monitoring()
                    card.stats_monitor.start_monitoring(15000)  # 15 second intervals
        else:
            # Restore normal frequency
            self.update_timer.stop()
            self.update_timer.start(10000)  # Normal 10 second intervals
            
            # Restore normal server stats monitoring
            for card in self.server_cards.values():
                if hasattr(card, 'stats_monitor'):
                    card.stats_monitor.stop_monitoring()
                    card.stats_monitor.start_monitoring(5000)  # Normal 5 second intervals
        
    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_server_status)
        self.update_timer.start(10000)  # Update every 10 seconds (reduced for performance)
        
    def refresh_servers(self):
        """Refresh the server list"""
        # Clear existing cards
        for card in self.server_cards.values():
            card.deleteLater()
        self.server_cards.clear()
        
        # Clear console combo
        self.console_server_combo.clear()
        
        # Add server cards
        for server in self.server_manager.servers.values():
            card = ServerCard(server, self)
            self.server_cards[server.name] = card
            self.server_list_layout.addWidget(card)
            
            # Add to console combo
            self.console_server_combo.addItem(server.name)
            
        # Add stretch at the end
        self.server_list_layout.addStretch()
        
    def create_server(self):
        """Show create server dialog"""
        dialog = CreateServerDialog(self.downloader, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_server_config()
            
            if not config["name"]:
                QMessageBox.warning(self, "Error", "Please enter a server name.")
                return
                
            if config["name"] in self.server_manager.servers:
                QMessageBox.warning(self, "Error", f"Server '{config['name']}' already exists.")
                return
                
            # Create the server
            success = self.server_manager.create_server(
                name=config["name"],
                version=config["version"],
                min_ram=config["min_ram"],
                max_ram=config["max_ram"],
                storage_path=config["path"],
                port=config["port"],
                storage_limit=config["storage_limit"]
            )
            
            if success:
                # Download server files and install plugins in background
                server = self.server_manager.servers[config["name"]]
                server_path = Path(server.path)
                
                # Download server files
                self.downloader.download_server_files(config["version"], server_path)
                
                # Install plugin pack if requested (silently in background)
                if config.get("install_plugins", False):
                    try:
                        plugins_path = server_path / "plugins"
                        self.downloader.download_basic_plugin_pack(plugins_path)
                    except Exception as e:
                        print(f"Plugin installation error: {e}")
                
                # Enable Playit.gg if requested
                if config.get("enable_playit", False):
                    try:
                        from playit_manager import playit_manager
                        print(f"🌐 Enabling Playit.gg for server '{config['name']}'...")
                        playit_success = playit_manager.enable_playit_for_server(config["name"], config["port"])
                        if playit_success:
                            QMessageBox.information(self, "Playit.gg Enabled", 
                                f"✅ Playit.gg has been enabled for server '{config['name']}'!\n"
                                "🌐 Visit https://playit.gg to configure your tunnels\n"
                                "📱 Your server is now accessible worldwide!")
                        else:
                            QMessageBox.warning(self, "Playit.gg Failed", 
                                f"❌ Failed to enable Playit.gg for server '{config['name']}'.\n"
                                "You can try enabling it later from the server settings.")
                    except Exception as e:
                        print(f"Playit integration error: {e}")
                        QMessageBox.warning(self, "Playit.gg Error", 
                            f"❌ Error enabling Playit.gg: {str(e)}")
                
                # Refresh server list
                self.refresh_servers()
            else:
                QMessageBox.critical(self, "Error", "Failed to create server.")
                
    def update_server_status(self):
        """Update server status indicators"""
        for name, card in self.server_cards.items():
            if name in self.server_manager.servers:
                server = self.server_manager.servers[name]
                current_status = self.server_manager.get_server_status(name)
                if server.status != current_status:
                    server.status = current_status
                    card.update_status(current_status)
                    
        # Update console if a server is selected
        current_server = self.console_server_combo.currentText()
        if current_server and current_server in self.server_manager.servers:
            console_lines = self.server_manager.get_console_output(current_server, 50)
            
            # Store current scroll position
            scrollbar = self.console_output.verticalScrollBar()
            was_at_bottom = scrollbar and scrollbar.value() >= scrollbar.maximum() - 10
            
            # Update console content with proper line breaks
            console_text = "\n".join(console_lines) if console_lines else ""
            if self.console_output.toPlainText() != console_text:
                self.console_output.setPlainText(console_text)
                
                # Auto-scroll to bottom only if already at bottom or new content
                if was_at_bottom or not console_lines:
                    cursor = self.console_output.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.console_output.setTextCursor(cursor)
                    if scrollbar:
                        scrollbar.setValue(scrollbar.maximum())
            
    def send_command(self):
        """Send command to selected server"""
        server_name = self.console_server_combo.currentText()
        command = self.command_input.text().strip()
        
        if not server_name or not command:
            return
            
        if self.server_manager.send_command(server_name, command):
            self.command_input.clear()
            # Add command to console output with proper formatting
            current_text = self.console_output.toPlainText()
            if current_text and not current_text.endswith('\n'):
                self.console_output.append(f">>> {command}")
            else:
                self.console_output.insertPlainText(f">>> {command}\n")
            
            # Auto-scroll to bottom
            cursor = self.console_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.console_output.setTextCursor(cursor)
        else:
            QMessageBox.warning(self, "Error", "Failed to send command. Server may not be running.")


class IPPortConfigDialog(QDialog):
    """Dialog for configuring server IP, port, and domain settings"""
    
    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.server = server
        self.setWindowTitle(f"Configure IP & Port - {server.name}")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background: #2d3142;
                color: #e6e6e6;
            }
            QLabel {
                color: #e6e6e6;
            }
        """)
        
        self.setup_ui()
        self.load_current_settings()
        
        # Connect hosting type changes
        self.hosting_combo.currentTextChanged.connect(self.on_hosting_type_changed)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🌐 Server Connection Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00d4ff; padding: 10px;")
        layout.addWidget(title)
        
        # Basic Settings Group
        basic_group = QGroupBox("Basic Connection Settings")
        basic_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4f5565;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        basic_layout = QGridLayout(basic_group)
        
        # Server Port
        basic_layout.addWidget(QLabel("Server Port:"), 0, 0)
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(25565)
        basic_layout.addWidget(self.port_edit, 0, 1)
        
        layout.addWidget(basic_group)
        
        # Domain Settings Group
        domain_group = QGroupBox("🌐 Domain & External Access")
        domain_group.setStyleSheet(basic_group.styleSheet())
        domain_layout = QGridLayout(domain_group)
        
        # Hosting Type
        domain_layout.addWidget(QLabel("Hosting Type:"), 0, 0)
        self.hosting_combo = QComboBox()
        self.hosting_combo.addItems([
            "🏠 Local Only (localhost)",
            "🚀 Playit.gg Tunnel (recommended)"
        ])
        self.hosting_combo.setCurrentIndex(1)  # Default to Playit.gg
        domain_layout.addWidget(self.hosting_combo, 0, 1)
        
        # External Address Display
        domain_layout.addWidget(QLabel("External Address:"), 1, 0)
        self.external_address_label = QLabel("📡 Will be generated after setup")
        self.external_address_label.setStyleSheet("color: #51cf66; font-weight: bold;")
        domain_layout.addWidget(self.external_address_label, 1, 1)
        
        layout.addWidget(domain_group)
        
        # Advanced Options Group
        advanced_group = QGroupBox("🔧 Advanced Options")
        advanced_group.setStyleSheet(basic_group.styleSheet())
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Auto-setup tunnels
        self.auto_setup_cb = QCheckBox("🚀 Auto-setup tunnel service (if not port forwarding)")
        self.auto_setup_cb.setChecked(True)
        self.auto_setup_cb.setToolTip("Automatically install and configure tunnel service")
        advanced_layout.addWidget(self.auto_setup_cb)
        
        # Show public address in console
        self.show_public_cb = QCheckBox("📺 Display external address prominently in console")
        self.show_public_cb.setChecked(True)
        self.show_public_cb.setToolTip("Show the external address in the server console header")
        advanced_layout.addWidget(self.show_public_cb)
        
        
        layout.addWidget(advanced_group)
        
        # Connection Test
        test_layout = QHBoxLayout()
        test_btn = ModernButton("🔍 Test Connection")
        test_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(test_btn)
        
        generate_btn = ModernButton("🎲 Generate Random Port")
        generate_btn.clicked.connect(self.generate_random_port)
        test_layout.addWidget(generate_btn)
        
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = ModernButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = ModernButton("Save Configuration", primary=True)
        save_btn.clicked.connect(self.save_configuration)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_current_settings(self):
        """Load current server settings into the dialog"""
        try:
            config_path = Path(self.server.path) / "server.properties"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('server-port='):
                            port_value = line.split('=', 1)[1].strip()
                            try:
                                self.port_edit.setValue(int(port_value))
                            except ValueError:
                                pass
        except Exception:
            pass
    
    def test_connection(self):
        """Test if the configured port is available"""
        import socket
        
        port = self.port_edit.value()
        
        try:
            # Try to bind to the port to test availability
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            
            if result == 0:
                QMessageBox.warning(self, "Port Test", f"Port {port} is already in use on localhost")
            else:
                QMessageBox.information(self, "Port Test", f"Port {port} is available on localhost")
                
        except Exception as e:
            QMessageBox.warning(self, "Test Error", f"Could not test connection: {str(e)}")
    
    def generate_random_port(self):
        """Generate a random available port"""
        import random
        import socket
        
        for _ in range(10):  # Try 10 times
            port = random.randint(25565, 35565)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result != 0:  # Port is available
                    self.port_edit.setValue(port)
                    QMessageBox.information(self, "Random Port", f"Generated available port: {port}")
                    return
            except:
                continue
        
        QMessageBox.warning(self, "Port Generation", "Could not find an available random port")
    
    def save_configuration(self):
        """Save the configuration to server.properties"""
        try:
            config_path = Path(self.server.path) / "server.properties"
            
            # Read existing properties with robust encoding
            properties = {}
            if config_path.exists():
                file_content = ""
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(config_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                    except Exception:
                        with open(config_path, 'r', encoding='cp1252', errors='replace') as f:
                            file_content = f.read()
                
                for line in file_content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.strip()] = value.strip()
            
            # Update with new values
            properties['server-port'] = str(self.port_edit.value())
            
            # Write back to file with robust encoding
            with open(config_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write("# Minecraft Server Properties\n")
                f.write(f"# Configured via CrazeDyn Panel\n")
                f.write("\n")
                
                for key, value in properties.items():
                    f.write(f"{key}={value}\n")
            
            # Save external hosting configuration
            hosting_type = self.hosting_combo.currentText()
            
            # Create external configuration file
            external_config = {
                'hosting_type': hosting_type,
                'auto_setup': self.auto_setup_cb.isChecked(),
                'show_public': self.show_public_cb.isChecked(),
                'external_address': ''  # Will be filled by tunnel services
            }
            
            external_config_path = Path(self.server.path) / "crazedyn_external.json"
            try:
                with open(external_config_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(external_config, f, indent=2)
            except Exception as e:
                print(f"Could not save external config: {e}")
            
            # Handle external hosting setup
            if self.auto_setup_cb.isChecked():
                if "Playit.gg" in hosting_type:
                    self.setup_playit_tunnel()
            
            QMessageBox.information(self, "Success", "Server configuration saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save configuration: {str(e)}")
    
    
    def on_hosting_type_changed(self):
        """Handle hosting type selection changes"""
        hosting_type = self.hosting_combo.currentText()
        
        if "Local Only" in hosting_type:
            self.external_address_label.setText("🏠 localhost only")
            self.auto_setup_cb.setEnabled(False)
        elif "Playit.gg" in hosting_type:
            self.external_address_label.setText("🚀 [random].ip.gl.ply.gg:[port]")
            self.auto_setup_cb.setEnabled(True)
    
    
    
    
    
    def setup_playit_tunnel(self):
        """Set up playit.gg tunnel for external access"""
        try:
            port = self.port_edit.value()
            
            instructions = f"""🚀 Playit.gg Tunnel Setup (Recommended)

🎯 **Quick Setup Guide:**

1️⃣ **Install Playit.gg Agent:**
   • Visit: https://playit.gg
   • Download the desktop app for your OS
   • Run installer and follow setup

2️⃣ **Create Account & Claim:**
   • Sign up for free account
   • Open playit.gg app → get claim URL
   • Follow claim process in browser

3️⃣ **Add Minecraft Tunnel:**
   • In dashboard: "Create Tunnel"
   • Protocol: Minecraft Java
   • Local Address: 127.0.0.1:{port}
   • Click "Create"

4️⃣ **Get Your Address:**
   • Copy the assigned address: [random].ip.gl.ply.gg:[port]
   • Share this with friends to connect!

✨ **Benefits:**
• Free forever
• No port forwarding needed
• Works behind any firewall/NAT
• Professional subdomain included
• 24/7 tunnel reliability

🔧 **Auto-Installation:**
CrazeDyn Panel can try to auto-install the agent for you."""

            reply = QMessageBox.question(self, "Playit.gg Setup", 
                                       instructions + "\n\nWould you like to try auto-installation?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.auto_install_playit()
            else:
                QMessageBox.information(self, "Manual Setup", 
                    "Please follow the manual setup instructions above.\n\n"
                    "Once configured, your server will be accessible externally!")
                
        except Exception as e:
            QMessageBox.warning(self, "Tunnel Error", f"Could not set up tunnel: {str(e)}")
    
    def auto_install_playit(self):
        """Attempt to automatically install Playit.gg"""
        try:
            import subprocess
            import platform
            import requests
            import os
            
            system = platform.system().lower()
            
            if system == "windows":
                # Download Windows installer
                QMessageBox.information(self, "Downloading Playit.gg", 
                    "Downloading Playit.gg installer...\n\n"
                    "This may take a moment.")
                
                url = "https://github.com/playit-cloud/playit-agent/releases/latest/download/playit-windows.exe"
                response = requests.get(url, stream=True)
                
                if response.status_code == 200:
                    installer_path = "playit-installer.exe"
                    with open(installer_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Run installer
                    subprocess.Popen([installer_path])
                    QMessageBox.information(self, "Installation Started", 
                        "Playit.gg installer launched!\n\n"
                        "1. Complete the installation\n"
                        "2. Run playit.gg and claim your account\n"
                        "3. Create a Minecraft tunnel\n\n"
                        "Then restart your server!")
                    
                else:
                    raise Exception("Failed to download installer")
                    
            elif system == "linux":
                # Install via package manager
                QMessageBox.information(self, "Installing Playit.gg", 
                    "Installing Playit.gg via package manager...\n\n"
                    "You may be prompted for admin password.")
                
                # Add repository and install
                commands = [
                    "curl -SsL https://playit-cloud.github.io/ppa/key.gpg | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/playit.gpg >/dev/null",
                    'echo "deb [signed-by=/etc/apt/trusted.gpg.d/playit.gpg] https://playit-cloud.github.io/ppa/data ./" | sudo tee /etc/apt/sources.list.d/playit-cloud.list',
                    "sudo apt update",
                    "sudo apt install -y playit"
                ]
                
                for cmd in commands:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(f"Command failed: {cmd}")
                
                QMessageBox.information(self, "Installation Complete", 
                    "Playit.gg installed successfully!\n\n"
                    "Next steps:\n"
                    "1. Run: playit setup\n"
                    "2. Follow claim URL process\n"
                    "3. Create Minecraft tunnel in dashboard\n\n"
                    "Your server will then be externally accessible!")
                
            else:
                QMessageBox.information(self, "Manual Installation", 
                    f"Auto-installation not available for {system}.\n\n"
                    "Please visit https://playit.gg and download manually.")
                
        except Exception as e:
            QMessageBox.warning(self, "Installation Error", 
                f"Could not auto-install Playit.gg: {str(e)}\n\n"
                "Please install manually from: https://playit.gg")


class ServerDetailWindow(QMainWindow):
    """Detailed server management window"""
    
    def __init__(self, server: MinecraftServer, server_manager: ServerManager, parent=None):
        super().__init__(parent)
        self.server = server
        self.server_manager = server_manager
        self.parent_window = parent
        self.current_plugin = None
        self.plugin_cache = {}
        
        # Initialize server stats monitor
        self.stats_monitor = ServerStatsMonitor(
            server_process_pid=server.pid if server.pid else None,
            server_path=Path(server.path),
            storage_limit=getattr(server, 'storage_limit', 10)
        )
        self.stats_monitor.stats_updated.connect(self.update_stats_display)
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        self.setWindowTitle(f"Managing Server: {self.server.name}")
        self.setGeometry(200, 200, 1000, 700)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1f29;
                color: #e6e6e6;
            }
            QTabWidget::pane {
                border: 1px solid #4f5565;
                background: #1e1f29;
            }
            QTabBar::tab {
                background: #2d3142;
                color: #e6e6e6;
                padding: 10px 20px;
                border: 1px solid #4f5565;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #00d4ff;
                color: #1e1f29;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #3d4152;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header with server info
        header = QHBoxLayout()
        title = QLabel(f"🎮 {self.server.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d4ff; padding: 10px;")
        header.addWidget(title)
        
        # Status indicator
        self.status_indicator = StatusIndicator(self.server.status)
        header.addWidget(self.status_indicator)
        
        header.addStretch()
        
        # Quick control buttons
        self.start_btn = ModernButton("Start", primary=True)
        self.start_btn.clicked.connect(self.start_server)
        header.addWidget(self.start_btn)
        
        self.stop_btn = ModernButton("Stop")
        self.stop_btn.clicked.connect(self.stop_server)
        header.addWidget(self.stop_btn)
        
        self.restart_btn = ModernButton("Restart")
        self.restart_btn.clicked.connect(self.restart_server)
        header.addWidget(self.restart_btn)
        
        layout.addLayout(header)
        
        # Tab widget for different management sections
        self.tab_widget = QTabWidget()
        
        # Console tab
        self.console_tab = self.create_console_tab()
        self.tab_widget.addTab(self.console_tab, "💻 Console")
        
        # Content browser tab
        self.content_tab = self.create_content_browser_tab()
        self.tab_widget.addTab(self.content_tab, "📁 Content Browser")
        
        # Configuration tab
        self.config_tab = self.create_config_tab()
        self.tab_widget.addTab(self.config_tab, "⚙️ Configuration")
        
        # Server Properties tab (easy toggles)
        self.properties_tab = self.create_properties_tab()
        self.tab_widget.addTab(self.properties_tab, "🎮 Server Properties")
        
        # Plugins tab
        self.plugins_tab = self.create_plugins_tab()
        self.tab_widget.addTab(self.plugins_tab, "🔌 Plugins")
        
        # Server info tab
        self.info_tab = self.create_info_tab()
        self.tab_widget.addTab(self.info_tab, "ℹ️ Server Info")
        
        layout.addWidget(self.tab_widget)
    
    def create_console_tab(self):
        """Create console tab for this specific server"""
        widget = QWidget()
        layout = QHBoxLayout(widget)  # Changed to horizontal to accommodate sidebar
        
        # Server connection info panel
        info_panel = QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background: #1a1d29;
                border: 2px solid #00d4ff;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        info_layout = QHBoxLayout(info_panel)
        
        # Server status
        self.server_status_label = QLabel("🔴 Offline")
        self.server_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6b6b;")
        info_layout.addWidget(self.server_status_label)
        
        info_layout.addWidget(QLabel("|"))
        
        # IP and Port display
        self.connection_label = QLabel("📡 localhost:25565")
        self.connection_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d4ff;")
        info_layout.addWidget(self.connection_label)
        
        info_layout.addStretch()
        
        # Configure IP/Port button
        configure_btn = ModernButton("⚙️ Configure IP & Port", primary=True)
        configure_btn.clicked.connect(self.configure_ip_port)
        info_layout.addWidget(configure_btn)
        
        # Copy connection info button
        copy_info_btn = ModernButton("📋 Copy Server Info")
        copy_info_btn.clicked.connect(self.copy_connection_info)
        info_layout.addWidget(copy_info_btn)
        
        # Create main splitter for console and stats
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #4f5565;
                width: 3px;
            }
        """)
        
        # Left side - Console area
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        console_layout.addWidget(info_panel)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        console_layout.addWidget(self.console_output)
        
        # Command input
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Command:"))
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter server command...")
        self.command_input.returnPressed.connect(self.send_command)
        command_layout.addWidget(self.command_input)
        
        send_btn = ModernButton("Send")
        send_btn.clicked.connect(self.send_command)
        command_layout.addWidget(send_btn)
        
        clear_btn = ModernButton("Clear")
        clear_btn.clicked.connect(lambda: self.console_output.clear())
        command_layout.addWidget(clear_btn)
        
        console_layout.addLayout(command_layout)
        
        # Right side - Server Stats Sidebar
        stats_sidebar = self.create_stats_sidebar()
        
        # Add widgets to splitter
        main_splitter.addWidget(console_widget)
        main_splitter.addWidget(stats_sidebar)
        
        # Set splitter proportions (console takes 75%, stats takes 25%)
        main_splitter.setSizes([750, 250])
        
        layout.addWidget(main_splitter)
        
        # Update connection display
        self.update_connection_display()
        
        # Start stats monitoring if server is running
        if self.server.status == "running" and self.server.pid:
            self.stats_monitor.connect_to_process(self.server.pid)
            self.stats_monitor.start_monitoring()
        
        return widget
    
    def create_stats_sidebar(self):
        """Create the server stats sidebar"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background: #1a1d29;
                border: 1px solid #4f5565;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("📊 Server Stats")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #00d4ff;
                background: transparent;
                border: none;
                padding: 5px;
                text-align: center;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Server Status
        self.stats_status_label = QLabel("🔴 Server Offline")
        self.stats_status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ff4444;
                background: transparent;
                border: none;
                padding: 5px;
                text-align: center;
            }
        """)
        self.stats_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_status_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #4f5565; background: #4f5565;")
        layout.addWidget(separator)
        
        # CPU Usage
        cpu_group = self.create_stat_group("💻 CPU Usage", "cpu")
        layout.addWidget(cpu_group)
        
        # Memory Usage
        memory_group = self.create_stat_group("🧠 Memory Usage", "memory")
        layout.addWidget(memory_group)
        
        # Disk Usage
        disk_group = self.create_stat_group("💾 Disk Usage", "disk")
        layout.addWidget(disk_group)
        
        # Server Info
        info_group = self.create_stat_group("🎮 Server Info", "info")
        layout.addWidget(info_group)
        
        # Performance
        perf_group = self.create_stat_group("⚡ Performance", "performance")
        layout.addWidget(perf_group)
        
        layout.addStretch()
        
        # Initialize stats display with offline state
        self.update_stats_display(self.stats_monitor._get_offline_stats())
        
        return sidebar
    
    def create_stat_group(self, title: str, group_type: str):
        """Create a statistics group widget"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #e6e6e6;
                background: transparent;
                border: 1px solid #4f5565;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00d4ff;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 15, 8, 8)
        
        if group_type == "cpu":
            self.cpu_percent_label = QLabel("0.0%")
            self.cpu_bar = QProgressBar()
            self.cpu_bar.setRange(0, 100)
            self.cpu_bar.setValue(0)
            layout.addWidget(self.cpu_percent_label)
            layout.addWidget(self.cpu_bar)
            
        elif group_type == "memory":
            self.memory_usage_label = QLabel("0 MB / 0 MB")
            self.memory_percent_label = QLabel("0.0%")
            self.memory_bar = QProgressBar()
            self.memory_bar.setRange(0, 100)
            self.memory_bar.setValue(0)
            layout.addWidget(self.memory_usage_label)
            layout.addWidget(self.memory_percent_label)
            layout.addWidget(self.memory_bar)
            
        elif group_type == "disk":
            self.disk_usage_label = QLabel("0 GB / 0 GB")
            self.disk_percent_label = QLabel("0.0%")
            self.disk_bar = QProgressBar()
            self.disk_bar.setRange(0, 100)
            self.disk_bar.setValue(0)
            layout.addWidget(self.disk_usage_label)
            layout.addWidget(self.disk_percent_label)
            layout.addWidget(self.disk_bar)
            
        elif group_type == "info":
            self.uptime_label = QLabel("⏱️ Uptime: Server offline")
            self.players_label = QLabel("👥 Players: 0 / 0")
            layout.addWidget(self.uptime_label)
            layout.addWidget(self.players_label)
            
        elif group_type == "performance":
            self.tps_label = QLabel("⚡ TPS: 0.0")
            self.tps_bar = QProgressBar()
            self.tps_bar.setRange(0, 20)
            self.tps_bar.setValue(0)
            layout.addWidget(self.tps_label)
            layout.addWidget(self.tps_bar)
        
        # Style all labels
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet("""
                    QLabel {
                        color: #e6e6e6;
                        background: transparent;
                        border: none;
                        font-size: 12px;
                        padding: 2px;
                    }
                """)
        
        return group
    
    def update_stats_display(self, stats: dict):
        """Update the stats display with new data"""
        try:
            if stats['online']:
                # Server is online
                self.stats_status_label.setText("🟢 Server Online")
                self.stats_status_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: bold;
                        color: #00ff88;
                        background: transparent;
                        border: none;
                        padding: 5px;
                        text-align: center;
                    }
                """)
                
                # Update CPU
                cpu_percent = stats['cpu_percent']
                self.cpu_percent_label.setText(f"{cpu_percent:.1f}%")
                self.cpu_bar.setValue(int(cpu_percent))
                self.cpu_bar.setStyleSheet(self.get_progress_bar_style(cpu_percent))
                
                # Update Memory
                memory = stats['memory_info']
                used_mb = memory['used'] / (1024 * 1024)
                total_mb = (memory['used'] + memory['available']) / (1024 * 1024)
                memory_percent = memory['percent']
                
                self.memory_usage_label.setText(f"{used_mb:.0f} MB / {total_mb:.0f} MB")
                self.memory_percent_label.setText(f"{memory_percent:.1f}%")
                self.memory_bar.setValue(int(memory_percent))
                self.memory_bar.setStyleSheet(self.get_progress_bar_style(memory_percent))
                
                # Update Disk
                disk = stats['disk_usage']
                if disk['total'] > 0:
                    used_gb = disk['used'] / (1024 * 1024 * 1024)
                    total_gb = disk['total'] / (1024 * 1024 * 1024)
                    disk_percent = disk['percent']
                    
                    self.disk_usage_label.setText(f"{used_gb:.1f} GB / {total_gb:.1f} GB")
                    self.disk_percent_label.setText(f"{disk_percent:.1f}%")
                    self.disk_bar.setValue(int(disk_percent))
                    self.disk_bar.setStyleSheet(self.get_progress_bar_style(disk_percent))
                else:
                    self.disk_usage_label.setText("0 GB / 0 GB")
                    self.disk_percent_label.setText("0.0%")
                    self.disk_bar.setValue(0)
                
                # Update Server Info
                self.uptime_label.setText(f"⏱️ Uptime: {stats['uptime']}")
                players = stats['players']
                self.players_label.setText(f"👥 Players: {players['online']} / {players['max']}")
                
                # Update Performance
                tps = stats['tps']
                self.tps_label.setText(f"⚡ TPS: {tps:.1f}")
                self.tps_bar.setValue(int(tps))
                tps_percent = (tps / 20.0) * 100  # TPS as percentage of perfect 20 TPS
                self.tps_bar.setStyleSheet(self.get_progress_bar_style(100 - tps_percent, reverse=True))
                
            else:
                # Server is offline
                self.stats_status_label.setText("🔴 Server Offline")
                self.stats_status_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: bold;
                        color: #ff4444;
                        background: transparent;
                        border: none;
                        padding: 5px;
                        text-align: center;
                    }
                """)
                
                # Reset all stats to offline state
                self.cpu_percent_label.setText("0.0%")
                self.cpu_bar.setValue(0)
                self.cpu_bar.setStyleSheet(self.get_progress_bar_style(0))
                
                self.memory_usage_label.setText("0 MB / 0 MB")
                self.memory_percent_label.setText("0.0%")
                self.memory_bar.setValue(0)
                self.memory_bar.setStyleSheet(self.get_progress_bar_style(0))
                
                self.disk_usage_label.setText("0 GB / 0 GB")
                self.disk_percent_label.setText("0.0%")
                self.disk_bar.setValue(0)
                self.disk_bar.setStyleSheet(self.get_progress_bar_style(0))
                
                self.uptime_label.setText("⏱️ Uptime: Server offline")
                self.players_label.setText("👥 Players: 0 / 0")
                
                self.tps_label.setText("⚡ TPS: 0.0")
                self.tps_bar.setValue(0)
                self.tps_bar.setStyleSheet(self.get_progress_bar_style(0))
                
        except Exception as e:
            print(f"Error updating stats display: {e}")
    
    def get_progress_bar_style(self, percentage: float, reverse: bool = False) -> str:
        """Get progress bar style based on percentage"""
        if reverse:
            # For TPS - reverse the color logic (low TPS = bad = red)
            if percentage < 20:  # Low TPS is bad
                color = "#ff4444"  # Red
            elif percentage < 50:
                color = "#ffaa00"  # Yellow
            else:
                color = "#00ff88"  # Green
        else:
            # Normal logic - high percentage = bad
            if percentage < 50:
                color = "#00ff88"  # Green
            elif percentage < 80:
                color = "#ffaa00"  # Yellow
            else:
                color = "#ff4444"  # Red
        
        return f"""
            QProgressBar {{
                border: 1px solid #4f5565;
                border-radius: 3px;
                background: #2d3142;
                text-align: center;
                color: #e6e6e6;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 2px;
            }}
        """
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop stats monitoring when window is closed
        self.stats_monitor.stop_monitoring()
        super().closeEvent(event)
    
    def create_content_browser_tab(self):
        """Create content browser for server files"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Main toolbar with Windows Explorer integration
        toolbar = QHBoxLayout()
        
        # Windows Explorer integration
        explorer_btn = ModernButton("🗂️ Open in Explorer", primary=True)
        explorer_btn.clicked.connect(self.open_in_explorer)
        explorer_btn.setToolTip("Open server folder in Windows Explorer")
        toolbar.addWidget(explorer_btn)
        
        plugins_btn = ModernButton("🔌 Plugins Folder")
        plugins_btn.clicked.connect(self.open_plugins_in_explorer)
        plugins_btn.setToolTip("Open plugins folder in Windows Explorer")
        toolbar.addWidget(plugins_btn)
        
        world_btn = ModernButton("🌍 World Folder")
        world_btn.clicked.connect(self.open_world_in_explorer)
        world_btn.setToolTip("Open world folder in Windows Explorer")
        toolbar.addWidget(world_btn)
        
        toolbar.addStretch()
        
        # File operations
        refresh_btn = ModernButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_file_tree)
        toolbar.addWidget(refresh_btn)
        
        new_folder_btn = ModernButton("📁 New Folder")
        new_folder_btn.clicked.connect(self.create_new_folder)
        toolbar.addWidget(new_folder_btn)
        
        upload_btn = ModernButton("📤 Upload File")
        upload_btn.clicked.connect(self.upload_file)
        toolbar.addWidget(upload_btn)
        
        layout.addLayout(toolbar)
        
        # Path display
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Server Path:"))
        
        self.path_label = QLabel(str(self.server.path))
        self.path_label.setStyleSheet("background: #0d1117; color: #c9d1d9; padding: 5px; border: 1px solid #30363d; font-family: 'Consolas', 'Monaco', monospace;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label)
        
        copy_path_btn = ModernButton("📋 Copy")
        copy_path_btn.clicked.connect(self.copy_path_to_clipboard)
        path_layout.addWidget(copy_path_btn)
        
        layout.addLayout(path_layout)
        
        # Multi-tab file browser
        self.browser_tabs = QTabWidget()
        self.browser_tabs.setTabsClosable(True)
        self.browser_tabs.tabCloseRequested.connect(self.close_browser_tab)
        
        # Main server folder tab
        main_tab = self.create_file_browser_tab(Path(self.server.path), "🏠 Server Root")
        self.browser_tabs.addTab(main_tab, "🏠 Server Root")
        
        # Add new tab button
        new_tab_btn = ModernButton("➕ New Tab")
        new_tab_btn.clicked.connect(self.add_browser_tab)
        self.browser_tabs.setCornerWidget(new_tab_btn)
        
        layout.addWidget(self.browser_tabs)
        
        # Archive operations toolbar
        archive_layout = QHBoxLayout()
        
        zip_btn = ModernButton("📦 Create ZIP")
        zip_btn.clicked.connect(self.create_zip_archive)
        zip_btn.setToolTip("Create ZIP archive from selected items")
        archive_layout.addWidget(zip_btn)
        
        unzip_btn = ModernButton("📂 Extract ZIP")
        unzip_btn.clicked.connect(self.extract_zip_archive)
        unzip_btn.setToolTip("Extract ZIP archive")
        archive_layout.addWidget(unzip_btn)
        
        archive_layout.addStretch()
        
        # Status bar for file operations
        self.status_label = QLabel("Ready - Drag and drop files to upload")
        self.status_label.setStyleSheet("color: #888; font-size: 12px; padding: 5px;")
        archive_layout.addWidget(self.status_label)
        
        layout.addLayout(archive_layout)
        
        # Enable drag and drop
        widget.setAcceptDrops(True)
        widget.dragEnterEvent = self.dragEnterEvent
        widget.dropEvent = self.dropEvent
        
        return widget
    
    def create_file_browser_tab(self, path: Path, title: str = None):
        """Create a file browser tab for a specific path"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Path navigation
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("📁"))
        
        path_edit = QLineEdit(str(path))
        path_edit.setStyleSheet("background: #0d1117; color: #c9d1d9; padding: 5px; border: 1px solid #30363d; font-family: 'Consolas', 'Monaco', monospace;")
        path_edit.returnPressed.connect(lambda: self.navigate_to_path(path_edit.text(), tab_widget))
        nav_layout.addWidget(path_edit)
        
        go_btn = ModernButton("Go")
        go_btn.clicked.connect(lambda: self.navigate_to_path(path_edit.text(), tab_widget))
        nav_layout.addWidget(go_btn)
        
        layout.addLayout(nav_layout)
        
        # File tree for this tab
        file_tree = QTreeWidget()
        file_tree.setHeaderLabels(["Name", "Type", "Size", "Modified"])
        file_tree.setStyleSheet("""
            QTreeWidget {
                background: #2d3142;
                color: #e6e6e6;
                border: 1px solid #4f5565;
                alternate-background-color: #3d4152;
            }
            QTreeWidget::item:selected {
                background: #00d4ff;
                color: #1e1f29;
            }
            QTreeWidget::item:hover {
                background: #3d4152;
            }
        """)
        file_tree.itemDoubleClicked.connect(self.open_file_advanced)
        file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        file_tree.customContextMenuRequested.connect(self.show_context_menu)
        file_tree.setAlternatingRowColors(True)
        file_tree.setSortingEnabled(True)
        file_tree.setAcceptDrops(True)
        file_tree.setDragDropMode(QTreeWidget.DragDropMode.DropOnly)
        
        layout.addWidget(file_tree)
        
        # Store path and tree reference
        tab_widget.current_path = path
        tab_widget.file_tree = file_tree
        tab_widget.path_edit = path_edit
        
        # Populate tree
        self.populate_tree_for_tab(tab_widget)
        
        return tab_widget
    
    def populate_tree_for_tab(self, tab_widget):
        """Populate file tree for a specific tab asynchronously"""
        file_tree = tab_widget.file_tree
        path = tab_widget.current_path
        
        file_tree.clear()
        
        try:
            # Get items but don't process them all at once
            items = list(path.iterdir())
            folders = [p for p in items if p.is_dir() and not p.name.startswith('.')]
            files = [p for p in items if p.is_file() and not p.name.startswith('.')]
            
            # Store items to process asynchronously
            tab_widget.pending_folders = sorted(folders, key=lambda x: x.name.lower())
            tab_widget.pending_files = sorted(files, key=lambda x: x.name.lower())
            tab_widget.processing_index = 0
            
            # Start async processing
            self.process_next_batch(tab_widget)
            
        except PermissionError:
            # Add permission error item
            item = QTreeWidgetItem(file_tree)
            item.setText(0, "❌ Access Denied")
            item.setText(1, "Error")
            item.setText(2, "")
            item.setText(3, "")
        except Exception as e:
            # Add generic error item
            item = QTreeWidgetItem(file_tree)
            item.setText(0, f"❌ Error: {str(e)[:50]}")
            item.setText(1, "Error")
            item.setText(2, "")
            item.setText(3, "")
    
    def process_next_batch(self, tab_widget):
        """Process next batch of files/folders asynchronously"""
        if not hasattr(tab_widget, 'pending_folders'):
            return
            
        file_tree = tab_widget.file_tree
        batch_size = 5  # Process 5 items at a time to prevent freezing
        
        # Process folders first
        if hasattr(tab_widget, 'pending_folders') and tab_widget.pending_folders:
            for _ in range(min(batch_size, len(tab_widget.pending_folders))):
                if tab_widget.pending_folders:
                    item_path = tab_widget.pending_folders.pop(0)
                    self.add_folder_item(file_tree, item_path)
        
        # Then process files
        elif hasattr(tab_widget, 'pending_files') and tab_widget.pending_files:
            for _ in range(min(batch_size, len(tab_widget.pending_files))):
                if tab_widget.pending_files:
                    item_path = tab_widget.pending_files.pop(0)
                    self.add_file_item(file_tree, item_path)
        
        # Continue processing if there are more items
        if (hasattr(tab_widget, 'pending_folders') and tab_widget.pending_folders) or \
           (hasattr(tab_widget, 'pending_files') and tab_widget.pending_files):
            # Schedule next batch with a small delay to keep UI responsive
            QTimer.singleShot(10, lambda: self.process_next_batch(tab_widget))
    
    def add_folder_item(self, file_tree, item_path):
        """Add a folder item to the tree"""
        item = QTreeWidgetItem(file_tree)
        item.setText(0, f"📁 {item_path.name}")
        item.setText(1, "Folder")
        item.setText(2, "")
        
        try:
            import datetime
            mod_time = item_path.stat().st_mtime
            mod_date = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
            item.setText(3, mod_date)
        except:
            item.setText(3, "Unknown")
        
        item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))
    
    def add_file_item(self, file_tree, item_path):
        """Add a file item to the tree"""
        item = QTreeWidgetItem(file_tree)
        
        # Add file type icons
        file_ext = item_path.suffix.lower()
        if file_ext in ['.jar']:
            icon = "☕"
        elif file_ext in ['.yml', '.yaml']:
            icon = "⚙️"
        elif file_ext in ['.txt', '.log']:
            icon = "📄"
        elif file_ext in ['.json']:
            icon = "📋"
        elif file_ext in ['.properties']:
            icon = "🔧"
        elif file_ext in ['.zip', '.rar', '.7z']:
            icon = "📦"
        else:
            icon = "📄"
        
        item.setText(0, f"{icon} {item_path.name}")
        item.setText(1, "File")
        
        try:
            size = item_path.stat().st_size
            if size < 1024:
                item.setText(2, f"{size} B")
            elif size < 1024 * 1024:
                item.setText(2, f"{size // 1024} KB")
            else:
                item.setText(2, f"{size // (1024 * 1024)} MB")
            
            import datetime
            mod_time = item_path.stat().st_mtime
            mod_date = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
            item.setText(3, mod_date)
        except:
            item.setText(2, "Unknown")
            item.setText(3, "Unknown")
        
        item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))
    
    def close_browser_tab(self, index):
        """Close a browser tab"""
        if self.browser_tabs.count() > 1:  # Keep at least one tab
            self.browser_tabs.removeTab(index)
    
    def add_browser_tab(self):
        """Add a new browser tab"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Browse")
        if folder_path:
            path = Path(folder_path)
            tab = self.create_file_browser_tab(path, f"📁 {path.name}")
            self.browser_tabs.addTab(tab, f"📁 {path.name}")
            self.browser_tabs.setCurrentWidget(tab)
    
    def navigate_to_path(self, path_str: str, tab_widget):
        """Navigate to a specific path in a tab"""
        try:
            path = Path(path_str)
            if path.exists():
                tab_widget.current_path = path
                self.populate_tree_for_tab(tab_widget)
                tab_widget.path_edit.setText(str(path))
                self.status_label.setText(f"Navigated to: {path}")
            else:
                QMessageBox.warning(self, "Error", f"Path does not exist: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid path: {str(e)}")
    
    def dragEnterEvent(self, a0):
        """Handle drag enter event for file uploads"""
        if a0.mimeData().hasUrls():
            a0.acceptProposedAction()
    
    def dropEvent(self, a0):
        """Handle drop event for file uploads"""
        files = [url.toLocalFile() for url in a0.mimeData().urls()]
        self.upload_dropped_files(files)
        a0.acceptProposedAction()
    
    def upload_dropped_files(self, file_paths):
        """Upload dropped files to current server directory"""
        try:
            # Get current tab's path
            current_tab = self.browser_tabs.currentWidget()
            if hasattr(current_tab, 'current_path'):
                target_dir = current_tab.current_path
            else:
                target_dir = Path(self.server.path)
            
            import shutil
            uploaded_count = 0
            
            for file_path in file_paths:
                source_path = Path(file_path)
                if source_path.exists():
                    if source_path.is_file():
                        dest_path = target_dir / source_path.name
                        shutil.copy2(source_path, dest_path)
                        uploaded_count += 1
                    elif source_path.is_dir():
                        dest_path = target_dir / source_path.name
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                        uploaded_count += 1
            
            # Refresh all tabs
            for i in range(self.browser_tabs.count()):
                tab = self.browser_tabs.widget(i)
                if hasattr(tab, 'file_tree'):
                    self.populate_tree_for_tab(tab)
            
            self.status_label.setText(f"Uploaded {uploaded_count} items via drag & drop")
            
        except Exception as e:
            QMessageBox.warning(self, "Upload Error", f"Could not upload files: {str(e)}")
    
    def create_zip_archive(self):
        """Create ZIP archive from selected items"""
        current_tab = self.browser_tabs.currentWidget()
        if not hasattr(current_tab, 'file_tree'):
            return
        
        selected_items = current_tab.file_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please select files or folders to archive")
            return
        
        zip_name, ok = QInputDialog.getText(self, "Create ZIP", "Enter archive name:")
        if not ok or not zip_name.strip():
            return
        
        if not zip_name.endswith('.zip'):
            zip_name += '.zip'
        
        zip_path = current_tab.current_path / zip_name
        
        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in selected_items:
                    file_path = item.data(0, Qt.ItemDataRole.UserRole)
                    if file_path:
                        path = Path(file_path)
                        if path.is_file():
                            zipf.write(path, path.name)
                        elif path.is_dir():
                            for file in path.rglob('*'):
                                if file.is_file():
                                    zipf.write(file, file.relative_to(path.parent))
            
            self.populate_tree_for_tab(current_tab)
            self.status_label.setText(f"Created archive: {zip_name}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create archive: {str(e)}")
    
    def extract_zip_archive(self):
        """Extract ZIP archive"""
        zip_file, _ = QFileDialog.getOpenFileName(self, "Select ZIP Archive", "", "ZIP files (*.zip)")
        if not zip_file:
            return
        
        current_tab = self.browser_tabs.currentWidget()
        if not hasattr(current_tab, 'current_path'):
            return
        
        extract_dir = current_tab.current_path
        
        try:
            import zipfile
            with zipfile.ZipFile(zip_file, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            self.populate_tree_for_tab(current_tab)
            self.status_label.setText(f"Extracted archive to: {extract_dir}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not extract archive: {str(e)}")
    
    def create_properties_tab(self):
        """Create server properties tab with easy toggle buttons"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("🎮 Server Properties - Easy Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00d4ff; padding: 10px;")
        layout.addWidget(title)
        
        # Scroll area for properties
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Connection Settings Group
        conn_group = QGroupBox("🌐 Connection Settings")
        conn_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4f5565;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        conn_layout = QGridLayout(conn_group)
        
        # Online Mode Toggle
        conn_layout.addWidget(QLabel("Online Mode:"), 0, 0)
        self.online_mode_cb = QCheckBox("Enable Authentication")
        self.online_mode_cb.setToolTip("Require players to authenticate with Mojang servers")
        self.online_mode_cb.stateChanged.connect(self.update_server_properties)
        conn_layout.addWidget(self.online_mode_cb, 0, 1)
        
        # Server IP
        conn_layout.addWidget(QLabel("Server IP:"), 1, 0)
        self.server_ip_edit = QLineEdit()
        self.server_ip_edit.setPlaceholderText("Leave empty for all interfaces")
        self.server_ip_edit.textChanged.connect(self.update_server_properties)
        conn_layout.addWidget(self.server_ip_edit, 1, 1)
        
        # Server Port
        conn_layout.addWidget(QLabel("Server Port:"), 2, 0)
        self.server_port_edit = QSpinBox()
        self.server_port_edit.setRange(1, 65535)
        self.server_port_edit.setValue(25565)
        self.server_port_edit.valueChanged.connect(self.update_server_properties)
        conn_layout.addWidget(self.server_port_edit, 2, 1)
        
        # Max Players
        conn_layout.addWidget(QLabel("Max Players:"), 3, 0)
        self.max_players_edit = QSpinBox()
        self.max_players_edit.setRange(1, 1000)
        self.max_players_edit.setValue(20)
        self.max_players_edit.valueChanged.connect(self.update_server_properties)
        conn_layout.addWidget(self.max_players_edit, 3, 1)
        
        scroll_layout.addWidget(conn_group)
        
        # Server Appearance Group
        appear_group = QGroupBox("🎨 Server Appearance")
        appear_group.setStyleSheet(conn_group.styleSheet())
        appear_layout = QGridLayout(appear_group)
        
        # MOTD
        appear_layout.addWidget(QLabel("MOTD (Message of the Day):"), 0, 0)
        self.motd_edit = QLineEdit()
        self.motd_edit.setPlaceholderText("A Minecraft Server")
        self.motd_edit.textChanged.connect(self.update_server_properties)
        appear_layout.addWidget(self.motd_edit, 0, 1)
        
        # Resource Pack
        appear_layout.addWidget(QLabel("Resource Pack URL:"), 1, 0)
        self.resource_pack_edit = QLineEdit()
        self.resource_pack_edit.setPlaceholderText("https://example.com/resourcepack.zip")
        self.resource_pack_edit.textChanged.connect(self.update_server_properties)
        appear_layout.addWidget(self.resource_pack_edit, 1, 1)
        
        # Force Resource Pack
        appear_layout.addWidget(QLabel("Force Resource Pack:"), 2, 0)
        self.force_resource_pack_cb = QCheckBox("Require players to use resource pack")
        self.force_resource_pack_cb.stateChanged.connect(self.update_server_properties)
        appear_layout.addWidget(self.force_resource_pack_cb, 2, 1)
        
        scroll_layout.addWidget(appear_group)
        
        # Gameplay Settings Group
        gameplay_group = QGroupBox("⚙️ Gameplay Settings")
        gameplay_group.setStyleSheet(conn_group.styleSheet())
        gameplay_layout = QGridLayout(gameplay_group)
        
        # Game Mode
        gameplay_layout.addWidget(QLabel("Default Game Mode:"), 0, 0)
        self.gamemode_combo = QComboBox()
        self.gamemode_combo.addItems(["survival", "creative", "adventure", "spectator"])
        self.gamemode_combo.currentTextChanged.connect(self.update_server_properties)
        gameplay_layout.addWidget(self.gamemode_combo, 0, 1)
        
        # Difficulty
        gameplay_layout.addWidget(QLabel("Difficulty:"), 1, 0)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["peaceful", "easy", "normal", "hard"])
        self.difficulty_combo.setCurrentText("easy")
        self.difficulty_combo.currentTextChanged.connect(self.update_server_properties)
        gameplay_layout.addWidget(self.difficulty_combo, 1, 1)
        
        # Hardcore Mode
        gameplay_layout.addWidget(QLabel("Hardcore Mode:"), 2, 0)
        self.hardcore_cb = QCheckBox("Enable hardcore mode")
        self.hardcore_cb.stateChanged.connect(self.update_server_properties)
        gameplay_layout.addWidget(self.hardcore_cb, 2, 1)
        
        # PvP
        gameplay_layout.addWidget(QLabel("PvP:"), 3, 0)
        self.pvp_cb = QCheckBox("Allow player vs player combat")
        self.pvp_cb.setChecked(True)
        self.pvp_cb.stateChanged.connect(self.update_server_properties)
        gameplay_layout.addWidget(self.pvp_cb, 3, 1)
        
        scroll_layout.addWidget(gameplay_group)
        
        # World Settings Group
        world_group = QGroupBox("🌍 World Settings")
        world_group.setStyleSheet(conn_group.styleSheet())
        world_layout = QGridLayout(world_group)
        
        # Level Name
        world_layout.addWidget(QLabel("World Name:"), 0, 0)
        self.level_name_edit = QLineEdit()
        self.level_name_edit.setText("world")
        self.level_name_edit.textChanged.connect(self.update_server_properties)
        world_layout.addWidget(self.level_name_edit, 0, 1)
        
        # Level Type
        world_layout.addWidget(QLabel("World Type:"), 1, 0)
        self.level_type_combo = QComboBox()
        self.level_type_combo.addItems(["minecraft:normal", "minecraft:flat", "minecraft:large_biomes", "minecraft:amplified"])
        self.level_type_combo.currentTextChanged.connect(self.update_server_properties)
        world_layout.addWidget(self.level_type_combo, 1, 1)
        
        # Generate Structures
        world_layout.addWidget(QLabel("Generate Structures:"), 2, 0)
        self.generate_structures_cb = QCheckBox("Generate villages, dungeons, etc.")
        self.generate_structures_cb.setChecked(True)
        self.generate_structures_cb.stateChanged.connect(self.update_server_properties)
        world_layout.addWidget(self.generate_structures_cb, 2, 1)
        
        scroll_layout.addWidget(world_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        load_btn = ModernButton("📂 Load Current Settings")
        load_btn.clicked.connect(self.load_server_properties)
        button_layout.addWidget(load_btn)
        
        save_btn = ModernButton("💾 Save Settings", primary=True)
        save_btn.clicked.connect(self.save_server_properties)
        button_layout.addWidget(save_btn)
        
        reset_btn = ModernButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self.reset_server_properties)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        scroll_layout.addLayout(button_layout)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Load current properties
        self.load_server_properties()
        
        return widget
    
    def load_server_properties(self):
        """Load current server.properties into the UI"""
        config_path = Path(self.server.path) / "server.properties"
        if not config_path.exists():
            return
        
        try:
            properties = {}
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.strip()] = value.strip()
            
            # Update UI elements
            self.online_mode_cb.setChecked(properties.get('online-mode', 'true').lower() == 'true')
            self.server_ip_edit.setText(properties.get('server-ip', ''))
            self.server_port_edit.setValue(int(properties.get('server-port', '25565')))
            self.max_players_edit.setValue(int(properties.get('max-players', '20')))
            self.motd_edit.setText(properties.get('motd', 'A Minecraft Server'))
            self.resource_pack_edit.setText(properties.get('resource-pack', ''))
            self.force_resource_pack_cb.setChecked(properties.get('require-resource-pack', 'false').lower() == 'true')
            self.gamemode_combo.setCurrentText(properties.get('gamemode', 'survival'))
            self.difficulty_combo.setCurrentText(properties.get('difficulty', 'easy'))
            self.hardcore_cb.setChecked(properties.get('hardcore', 'false').lower() == 'true')
            self.pvp_cb.setChecked(properties.get('pvp', 'true').lower() == 'true')
            self.level_name_edit.setText(properties.get('level-name', 'world'))
            self.level_type_combo.setCurrentText(properties.get('level-type', 'minecraft:normal'))
            self.generate_structures_cb.setChecked(properties.get('generate-structures', 'true').lower() == 'true')
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load server properties: {str(e)}")
    
    def update_server_properties(self):
        """Auto-save when properties change"""
        # This will be called on every change, but we'll just mark as modified
        pass
    
    def save_server_properties(self):
        """Save current UI settings to server.properties"""
        config_path = Path(self.server.path) / "server.properties"
        
        try:
            # Read existing file to preserve comments and order
            lines = []
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Update or add properties
            properties = {
                'online-mode': 'true' if self.online_mode_cb.isChecked() else 'false',
                'server-ip': self.server_ip_edit.text().strip(),
                'server-port': str(self.server_port_edit.value()),
                'max-players': str(self.max_players_edit.value()),
                'motd': self.motd_edit.text().strip() or 'A Minecraft Server',
                'resource-pack': self.resource_pack_edit.text().strip(),
                'require-resource-pack': 'true' if self.force_resource_pack_cb.isChecked() else 'false',
                'gamemode': self.gamemode_combo.currentText(),
                'difficulty': self.difficulty_combo.currentText(),
                'hardcore': 'true' if self.hardcore_cb.isChecked() else 'false',
                'pvp': 'true' if self.pvp_cb.isChecked() else 'false',
                'level-name': self.level_name_edit.text().strip() or 'world',
                'level-type': self.level_type_combo.currentText(),
                'generate-structures': 'true' if self.generate_structures_cb.isChecked() else 'false'
            }
            
            # Update existing lines or add new ones
            updated_lines = []
            used_keys = set()
            
            for line in lines:
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=', 1)[0].strip()
                    if key in properties:
                        updated_lines.append(f"{key}={properties[key]}\n")
                        used_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add any new properties
            for key, value in properties.items():
                if key not in used_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # Write back to file
            with open(config_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            QMessageBox.information(self, "Success", "Server properties saved successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save server properties: {str(e)}")
    
    def reset_server_properties(self):
        """Reset all properties to defaults"""
        reply = QMessageBox.question(self, "Reset Properties", 
                                   "Reset all server properties to default values?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.online_mode_cb.setChecked(True)
            self.server_ip_edit.setText("")
            self.server_port_edit.setValue(25565)
            self.max_players_edit.setValue(20)
            self.motd_edit.setText("A Minecraft Server")
            self.resource_pack_edit.setText("")
            self.force_resource_pack_cb.setChecked(False)
            self.gamemode_combo.setCurrentText("survival")
            self.difficulty_combo.setCurrentText("easy")
            self.hardcore_cb.setChecked(False)
            self.pvp_cb.setChecked(True)
            self.level_name_edit.setText("world")
            self.level_type_combo.setCurrentText("minecraft:normal")
            self.generate_structures_cb.setChecked(True)
    
    def configure_ip_port(self):
        """Configure custom IP and port for the server"""
        dialog = IPPortConfigDialog(self.server, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_connection_display()
            # Update the server properties if needed
            if hasattr(self, 'properties_tab'):
                self.load_server_properties()
    
    def update_connection_display(self):
        """Update the connection info display with external hosting support"""
        try:
            # Read current server properties with robust encoding
            config_path = Path(self.server.path) / "server.properties"
            server_ip = "localhost"
            server_port = "25565"
            external_info = ""
            
            if config_path.exists():
                file_content = ""
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(config_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                    except Exception:
                        with open(config_path, 'r', encoding='cp1252', errors='replace') as f:
                            file_content = f.read()
                
                # Parse server properties
                for line in file_content.splitlines():
                    if line.startswith('server-ip='):
                        ip_value = line.split('=', 1)[1].strip()
                        if ip_value:
                            server_ip = ip_value
                    elif line.startswith('server-port='):
                        server_port = line.split('=', 1)[1].strip()
            
            # Check for external hosting configuration
            external_config_path = Path(self.server.path) / "crazedyn_external.json"
            if external_config_path.exists():
                try:
                    import json
                    with open(external_config_path, 'r', encoding='utf-8') as f:
                        external_config = json.load(f)
                    
                    hosting_type = external_config.get('hosting_type', '')
                    domain = external_config.get('domain', '')
                    external_address = external_config.get('external_address', '')
                    
                    if external_address:
                        external_info = f" | 🌐 External: {external_address}"
                    elif domain:
                        external_info = f" | 🌍 Domain: {domain}:{server_port}"
                    elif "Playit.gg" in hosting_type:
                        external_info = f" | 🚀 Tunnel: Playit.gg"
                    elif "Ngrok" in hosting_type:
                        external_info = f" | 🔗 Tunnel: Ngrok"
                    elif "Direct IP" in hosting_type:
                        external_info = f" | 🌍 Public: [Your IP]:{server_port}"
                        
                except Exception:
                    pass
            
            # Update local connection display
            local_text = f"📡 Local: {server_ip or 'localhost'}:{server_port}"
            full_text = local_text + external_info
            
            if hasattr(self, 'connection_label') and self.connection_label:
                self.connection_label.setText(full_text)
                
                # Style based on external hosting
                if external_info:
                    self.connection_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d4ff; background: rgba(0, 212, 255, 0.1); padding: 5px; border-radius: 3px;")
                else:
                    self.connection_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d4ff;")
            
            # Update status based on server state
            if hasattr(self, 'server_status_label') and self.server_status_label:
                if hasattr(self.server, 'status') and self.server.status == 'running':
                    status_text = "🟢 Online"
                    if external_info:
                        status_text += " (Externally Accessible)"
                    self.server_status_label.setText(status_text)
                    self.server_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #51cf66;")
                else:
                    self.server_status_label.setText("🔴 Offline")
                    self.server_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6b6b;")
                
        except Exception as e:
            if hasattr(self, 'connection_label') and self.connection_label:
                self.connection_label.setText("📡 Error reading config")
            print(f"Error updating connection display: {e}")
    
    def copy_connection_info(self):
        """Copy server connection info to clipboard with external hosting support"""
        try:
            # Get local connection info
            config_path = Path(self.server.path) / "server.properties"
            server_ip = "localhost"
            server_port = "25565"
            
            if config_path.exists():
                file_content = ""
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(config_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                    except Exception:
                        with open(config_path, 'r', encoding='cp1252', errors='replace') as f:
                            file_content = f.read()
                
                for line in file_content.splitlines():
                    if line.startswith('server-ip='):
                        ip_value = line.split('=', 1)[1].strip()
                        if ip_value:
                            server_ip = ip_value
                    elif line.startswith('server-port='):
                        server_port = line.split('=', 1)[1].strip()
            
            # Check for external hosting
            external_config_path = Path(self.server.path) / "crazedyn_external.json"
            external_address = ""
            domain = ""
            hosting_type = ""
            
            if external_config_path.exists():
                try:
                    import json
                    with open(external_config_path, 'r', encoding='utf-8') as f:
                        external_config = json.load(f)
                    
                    hosting_type = external_config.get('hosting_type', '')
                    domain = external_config.get('domain', '')
                    external_address = external_config.get('external_address', '')
                except Exception:
                    pass
            
            # Build copy text
            copy_text = f"🎮 {self.server.name} Server Info\n\n"
            copy_text += f"📡 Local Connection: {server_ip or 'localhost'}:{server_port}\n"
            
            if external_address:
                copy_text += f"🌐 External Connection: {external_address}\n"
            elif domain:
                copy_text += f"🌍 Domain Connection: {domain}:{server_port}\n"
            elif "Playit.gg" in hosting_type:
                copy_text += f"🚀 External Access: Playit.gg tunnel configured\n"
            elif "Ngrok" in hosting_type:
                copy_text += f"🔗 External Access: Ngrok tunnel configured\n"
            elif "Direct IP" in hosting_type:
                copy_text += f"🌍 External Access: Direct IP hosting configured\n"
            else:
                copy_text += f"🏠 Access: Local network only\n"
            
            copy_text += f"\n📊 Status: {self.server.status.title()}\n"
            copy_text += f"🎯 Share this info with friends to connect!"
            
            # Copy to clipboard
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.setText(copy_text)
                
                QMessageBox.information(self, "Copied!", 
                    "Server connection info copied to clipboard!\n\n"
                    "You can now paste it to share with friends.")
            else:
                QMessageBox.warning(self, "Error", "Could not access clipboard.")
                
        except Exception as e:
            QMessageBox.warning(self, "Copy Error", f"Could not copy connection info: {str(e)}")
    
    def create_config_tab(self):
        """Create configuration editor tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        save_btn = ModernButton("💾 Save Config", primary=True)
        save_btn.clicked.connect(self.save_config)
        toolbar.addWidget(save_btn)
        
        reload_btn = ModernButton("🔄 Reload Config")
        reload_btn.clicked.connect(self.load_config)
        toolbar.addWidget(reload_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Config editor
        self.config_editor = QPlainTextEdit()
        self.config_editor.setStyleSheet("""
            QPlainTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.config_editor)
        
        # Load current config
        self.load_config()
        
        return widget
    
    def create_plugins_tab(self):
        """Create plugins management tab with SpigotMC browser"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Initialize SpigotMC browser
        self.spigot_browser = SpigotBrowser()
        
        # Create tab widget for installed plugins vs browser
        self.plugin_tabs = QTabWidget()
        self.plugin_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4f5565;
                background: #2d3142;
            }
            QTabBar::tab {
                background: #1e1f29;
                color: #e6e6e6;
                padding: 8px 16px;
                border: 1px solid #4f5565;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #00d4ff;
                color: #1e1f29;
                font-weight: bold;
            }
        """)
        
        # Installed plugins tab
        installed_tab = self.create_installed_plugins_tab()
        self.plugin_tabs.addTab(installed_tab, "🗺️ Installed")
        
        # Browser tab  
        browser_tab = self.create_plugin_browser_tab()
        self.plugin_tabs.addTab(browser_tab, "🔍 Browse SpigotMC")
        
        layout.addWidget(self.plugin_tabs)
        
        return widget
    
    def create_installed_plugins_tab(self):
        """Create tab for managing installed plugins"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        refresh_btn = ModernButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_plugins)
        toolbar.addWidget(refresh_btn)
        
        add_plugin_btn = ModernButton("➕ Add Local Plugin")
        add_plugin_btn.clicked.connect(self.add_plugin)
        toolbar.addWidget(add_plugin_btn)
        
        remove_btn = ModernButton("🗑️ Remove Plugin")
        remove_btn.clicked.connect(self.remove_plugin)
        toolbar.addWidget(remove_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Plugins list
        self.plugins_tree = QTreeWidget()
        self.plugins_tree.setHeaderLabels(["Plugin Name", "Status", "Version", "Size"])
        self.plugins_tree.setStyleSheet("""
            QTreeWidget {
                background: #2d3142;
                color: #e6e6e6;
                border: 1px solid #4f5565;
                alternate-background-color: #3d4152;
            }
            QTreeWidget::item:selected {
                background: #00d4ff;
                color: #1e1f29;
            }
        """)
        layout.addWidget(self.plugins_tree)
        
        # Load plugins
        self.refresh_plugins()
        
        return widget
    
    def create_plugin_browser_tab(self):
        """Create SpigotMC plugin browser tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search and filter toolbar
        search_layout = QHBoxLayout()
        
        # Search input
        search_layout.addWidget(QLabel("🔍 Search:"))
        self.plugin_search = QLineEdit()
        self.plugin_search.setPlaceholderText("Search plugins...")
        self.plugin_search.returnPressed.connect(self.search_plugins)
        search_layout.addWidget(self.plugin_search)
        
        # Category filter
        search_layout.addWidget(QLabel("🗂 Category:"))
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.search_plugins)
        search_layout.addWidget(self.category_combo)
        
        # Sort options
        search_layout.addWidget(QLabel("📦 Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Downloads", "Rating", "Name", "Updated"])
        self.sort_combo.setCurrentText("Downloads")
        self.sort_combo.currentTextChanged.connect(self.search_plugins)
        search_layout.addWidget(self.sort_combo)
        
        # Search button
        search_btn = ModernButton("🔍 Search", primary=True)
        search_btn.clicked.connect(self.search_plugins)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Quick access buttons
        quick_layout = QHBoxLayout()
        
        popular_btn = ModernButton("🔥 Popular")
        popular_btn.clicked.connect(self.load_popular_plugins)
        quick_layout.addWidget(popular_btn)
        
        recent_btn = ModernButton("🆕 Recent")
        recent_btn.clicked.connect(self.load_recent_plugins)
        quick_layout.addWidget(recent_btn)
        
        quick_layout.addStretch()
        
        layout.addLayout(quick_layout)
        
        # Plugin results area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - plugin list
        self.browser_list = QTreeWidget()
        self.browser_list.setHeaderLabels(["Name", "Author", "Downloads", "Rating", "Category"])
        self.browser_list.setStyleSheet(self.plugins_tree.styleSheet())
        self.browser_list.itemClicked.connect(self.show_plugin_details)
        splitter.addWidget(self.browser_list)
        
        # Right side - plugin details
        self.plugin_details = QWidget()
        self.setup_plugin_details_panel()
        splitter.addWidget(self.plugin_details)
        
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)
        
        # Status bar
        self.plugin_status = QLabel("🔄 Ready to browse plugins")
        self.plugin_status.setStyleSheet("color: #00d4ff; padding: 5px;")
        layout.addWidget(self.plugin_status)
        
        # Load categories and popular plugins
        self.load_plugin_categories()
        self.load_popular_plugins()
        
        return widget
    
    def create_info_tab(self):
        """Create server information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Server details
        details_group = QGroupBox("Server Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4f5565;
                border-radius: 5px;
                margin: 10px 0;
                padding-top: 10px;
                color: #00d4ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        details_layout = QGridLayout(details_group)
        
        details_layout.addWidget(QLabel("Name:"), 0, 0)
        details_layout.addWidget(QLabel(self.server.name), 0, 1)
        
        details_layout.addWidget(QLabel("Path:"), 1, 0)
        details_layout.addWidget(QLabel(str(self.server.path)), 1, 1)
        
        details_layout.addWidget(QLabel("JAR File:"), 2, 0)
        details_layout.addWidget(QLabel(self.server.jar), 2, 1)
        
        details_layout.addWidget(QLabel("Port:"), 3, 0)
        details_layout.addWidget(QLabel(str(self.server.port)), 3, 1)
        
        details_layout.addWidget(QLabel("RAM (Min/Max):"), 4, 0)
        details_layout.addWidget(QLabel(f"{self.server.min_ram} / {self.server.max_ram}"), 4, 1)
        
        details_layout.addWidget(QLabel("Status:"), 5, 0)
        self.status_label = QLabel(self.server.status)
        details_layout.addWidget(self.status_label, 5, 1)
        
        if hasattr(self.server, 'pid') and self.server.pid:
            details_layout.addWidget(QLabel("Process ID:"), 6, 0)
            details_layout.addWidget(QLabel(str(self.server.pid)), 6, 1)
        
        scroll_layout.addWidget(details_group)
        
        # System resources group
        resources_group = QGroupBox("Resource Usage")
        resources_group.setStyleSheet(details_group.styleSheet())
        resources_layout = QGridLayout(resources_group)
        
        # Add resource monitoring here (CPU, RAM usage, etc.)
        resources_layout.addWidget(QLabel("CPU Usage:"), 0, 0)
        self.cpu_label = QLabel("N/A")
        resources_layout.addWidget(self.cpu_label, 0, 1)
        
        resources_layout.addWidget(QLabel("Memory Usage:"), 1, 0)
        self.memory_label = QLabel("N/A")
        resources_layout.addWidget(self.memory_label, 1, 1)
        
        scroll_layout.addWidget(resources_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def setup_timer(self):
        """Setup timer for updating console and status"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_interface)
        self.timer.start(5000)  # Update every 5 seconds (reduced for performance)
    
    def update_interface(self):
        """Update console output and status"""
        # Update console with proper line formatting
        console_lines = self.server_manager.get_console_output(self.server.name, 100)
        
        # Store current scroll position  
        scrollbar = self.console_output.verticalScrollBar()
        was_at_bottom = scrollbar and scrollbar.value() >= scrollbar.maximum() - 10
        
        # Update console content with proper line breaks
        new_text = "\n".join(console_lines) if console_lines else ""
        current_text = self.console_output.toPlainText()
        
        if current_text != new_text:
            self.console_output.setPlainText(new_text)
            
            # Auto-scroll to bottom only if already at bottom or new content
            if was_at_bottom or not console_lines:
                cursor = self.console_output.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.console_output.setTextCursor(cursor)
                if scrollbar:
                    scrollbar.setValue(scrollbar.maximum())
        
        # Update status
        current_status = self.server_manager.get_server_status(self.server.name)
        if self.server.status != current_status:
            self.server.status = current_status
            self.status_indicator.update_status(current_status)
            self.status_label.setText(current_status)
    
    def start_server(self):
        """Start the server"""
        self.server_manager.start_server(self.server.name)
        
        # Wait a moment for server to start and then connect stats monitoring
        QTimer.singleShot(2000, self.connect_stats_monitor)
    
    def stop_server(self):
        """Stop the server"""
        self.server_manager.stop_server(self.server.name)
        
        # Disconnect stats monitoring
        self.stats_monitor.stop_monitoring()
        # Update display to show offline state
        self.update_stats_display(self.stats_monitor._get_offline_stats())
    
    def restart_server(self):
        """Restart the server"""
        self.server_manager.restart_server(self.server.name)
        
        # Stop monitoring during restart
        self.stats_monitor.stop_monitoring()
        self.update_stats_display(self.stats_monitor._get_offline_stats())
        
        # Wait for restart to complete and reconnect monitoring
        QTimer.singleShot(5000, self.connect_stats_monitor)
    
    def connect_stats_monitor(self):
        """Connect stats monitoring to running server process"""
        try:
            # Refresh server status
            current_server = self.server_manager.servers.get(self.server.name)
            if current_server and current_server.status == "running" and current_server.pid:
                # Update our server reference
                self.server = current_server
                
                # Connect to the running process
                if self.stats_monitor.connect_to_process(current_server.pid):
                    self.stats_monitor.start_monitoring()
                    print(f"Stats monitoring connected to server {self.server.name} (PID: {current_server.pid})")
                else:
                    print(f"Failed to connect stats monitoring to server {self.server.name}")
            else:
                print(f"Server {self.server.name} is not running or has no PID")
        except Exception as e:
            print(f"Error connecting stats monitor: {e}")
    
    def send_command(self):
        """Send command to server console"""
        command = self.command_input.text().strip()
        if command:
            if self.server_manager.send_command(self.server.name, command):
                self.command_input.clear()
                # Add command to console output with proper formatting
                current_text = self.console_output.toPlainText()
                if current_text and not current_text.endswith('\n'):
                    self.console_output.append(f">>> {command}")
                else:
                    self.console_output.insertPlainText(f">>> {command}\n")
                
                # Auto-scroll to bottom
                cursor = self.console_output.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.console_output.setTextCursor(cursor)
            else:
                QMessageBox.warning(self, "Error", "Failed to send command. Server may not be running.")
    
    def refresh_file_tree(self):
        """Refresh the file tree with server files"""
        current_tab = self.browser_tabs.currentWidget()
        if hasattr(current_tab, 'file_tree'):
            current_tab.file_tree.clear()
            self.populate_tree_for_tab(current_tab)
    
    def populate_tree_item(self, parent_item, path):
        """Populate tree widget with files and folders"""
        try:
            for item_path in sorted(path.iterdir()):
                if item_path.name.startswith('.'):
                    continue
                    
                item = QTreeWidgetItem(parent_item)
                item.setText(0, item_path.name)
                
                if item_path.is_dir():
                    item.setText(1, "Folder")
                    item.setText(2, "")
                    # Recursively add subdirectories
                    self.populate_tree_item(item, item_path)
                else:
                    item.setText(1, "File")
                    try:
                        size = item_path.stat().st_size
                        if size < 1024:
                            item.setText(2, f"{size} B")
                        elif size < 1024 * 1024:
                            item.setText(2, f"{size // 1024} KB")
                        else:
                            item.setText(2, f"{size // (1024 * 1024)} MB")
                    except:
                        item.setText(2, "Unknown")
                
                # Store full path for later use
                item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))
        
        except PermissionError:
            pass
    
    def open_file_advanced(self, item, column):
        """Handle double-click on file tree item with advanced actions"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            path = Path(file_path)
            if path.is_file():
                self.open_file_with_default_program(str(path))
            elif path.is_dir():
                self.open_folder_in_explorer(str(path))
    
    def open_file_with_default_program(self, file_path: str):
        """Open file with default Windows program"""
        try:
            import subprocess
            subprocess.run(['start', '', file_path], shell=True, check=True)
            self.status_label.setText(f"Opened: {Path(file_path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
    
    def open_folder_in_explorer(self, folder_path: str):
        """Open specific folder in Windows Explorer"""
        try:
            import subprocess
            import os
            # Normalize the path to handle any formatting issues
            normalized_path = os.path.normpath(str(folder_path))
            subprocess.run(['explorer', normalized_path], check=True)
            self.status_label.setText(f"Opened folder in Explorer")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
    
    def open_in_explorer(self):
        """Open main server folder in Windows Explorer"""
        self.open_folder_in_explorer(str(self.server.path))
    
    def open_plugins_in_explorer(self):
        """Open plugins folder in Windows Explorer"""
        plugins_path = Path(self.server.path) / "plugins"
        plugins_path.mkdir(exist_ok=True)
        self.open_folder_in_explorer(str(plugins_path))
    
    def open_world_in_explorer(self):
        """Open world folder in Windows Explorer"""
        world_path = Path(self.server.path) / "world"
        if world_path.exists():
            self.open_folder_in_explorer(str(world_path))
        else:
            QMessageBox.information(self, "Info", "World folder doesn't exist yet. Start the server to generate it.")
    
    def copy_path_to_clipboard(self):
        """Copy server path to clipboard"""
        try:
            from PyQt6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(str(self.server.path))
            self.status_label.setText("Path copied to clipboard")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not copy path: {str(e)}")
    
    def show_context_menu(self, position):
        """Show context menu for file operations"""
        current_tab = self.browser_tabs.currentWidget()
        if not hasattr(current_tab, 'file_tree'):
            return
        
        item = current_tab.file_tree.itemAt(position)
        if not item:
            return
        
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not file_path:
            return
        
        path = Path(file_path)
        menu = QMenu(self)
        
        if path.is_file():
            menu.addAction("📂 Open with default program", lambda: self.open_file_with_default_program(str(path)))
            menu.addAction("🗂️ Show in Explorer", lambda: self.show_in_explorer(str(path)))
            menu.addSeparator()
            menu.addAction("✏️ Rename", lambda: self.rename_item(item, path))
            menu.addAction("📋 Copy path", lambda: self.copy_item_path(str(path)))
            menu.addSeparator()
            menu.addAction("🗑️ Delete", lambda: self.delete_item(item, path))
        elif path.is_dir():
            menu.addAction("🗂️ Open in Explorer", lambda: self.open_folder_in_explorer(str(path)))
            menu.addSeparator()
            menu.addAction("📄 New file...", lambda: self.create_new_file(path))
            menu.addAction("📁 New folder...", lambda: self.create_new_folder_in(path))
            menu.addSeparator()
            menu.addAction("✏️ Rename", lambda: self.rename_item(item, path))
            menu.addAction("📋 Copy path", lambda: self.copy_item_path(str(path)))
            menu.addSeparator()
            menu.addAction("🗑️ Delete", lambda: self.delete_item(item, path))
        
        menu.exec(current_tab.file_tree.mapToGlobal(position))
    
    def show_in_explorer(self, file_path: str):
        """Show file in Windows Explorer"""
        try:
            import subprocess
            subprocess.run(['explorer', '/select,', file_path], check=True)
            self.status_label.setText("Showed in Explorer")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not show in Explorer: {str(e)}")
    
    def rename_item(self, item, path: Path):
        """Rename file or folder"""
        old_name = path.name
        new_name, ok = QInputDialog.getText(self, "Rename", f"Rename '{old_name}' to:", text=old_name)
        
        if ok and new_name.strip() and new_name != old_name:
            new_path = path.parent / new_name.strip()
            try:
                path.rename(new_path)
                self.refresh_file_tree()
                self.status_label.setText(f"Renamed '{old_name}' to '{new_name}'")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not rename: {str(e)}")
    
    def copy_item_path(self, path: str):
        """Copy item path to clipboard"""
        try:
            from PyQt6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(path)
            self.status_label.setText("Path copied to clipboard")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not copy path: {str(e)}")
    
    def delete_item(self, item, path: Path):
        """Delete file or folder"""
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete '{path.name}'?\\nThis cannot be undone.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                
                self.refresh_file_tree()
                self.status_label.setText(f"Deleted '{path.name}'")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {str(e)}")
    
    def create_new_file(self, parent_path: Path):
        """Create a new file in the specified directory"""
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name.strip():
            file_path = parent_path / file_name.strip()
            try:
                file_path.touch()
                self.refresh_file_tree()
                self.status_label.setText(f"Created file: {file_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create file: {str(e)}")
    
    def create_new_folder_in(self, parent_path: Path):
        """Create a new folder in the specified directory"""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name.strip():
            folder_path = parent_path / folder_name.strip()
            try:
                folder_path.mkdir(exist_ok=False)
                self.refresh_file_tree()
                self.status_label.setText(f"Created folder: {folder_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")
    
    def create_new_folder(self):
        """Create a new folder in server directory"""
        from PyQt6.QtWidgets import QInputDialog
        
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name.strip():
            folder_path = Path(self.server.path) / folder_name.strip()
            try:
                folder_path.mkdir(exist_ok=False)
                self.refresh_file_tree()
                QMessageBox.information(self, "Success", f"Created folder: {folder_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")
    
    def upload_file(self):
        """Upload a file to server directory"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload File")
        if file_path:
            source_path = Path(file_path)
            dest_path = Path(self.server.path) / source_path.name
            
            try:
                import shutil
                shutil.copy2(source_path, dest_path)
                self.refresh_file_tree()
                QMessageBox.information(self, "Success", f"Uploaded: {source_path.name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not upload file: {str(e)}")
    
    def load_config(self):
        """Load server.properties configuration"""
        config_path = Path(self.server.path) / "server.properties"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config_editor.setPlainText(f.read())
            else:
                self.config_editor.setPlainText("# server.properties file not found\\n# Start the server first to generate it")
        except Exception as e:
            self.config_editor.setPlainText(f"Error loading config: {str(e)}")
    
    def save_config(self):
        """Save server.properties configuration"""
        config_path = Path(self.server.path) / "server.properties"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(self.config_editor.toPlainText())
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save config: {str(e)}")
    
    def refresh_plugins(self):
        """Refresh the plugins list"""
        self.plugins_tree.clear()
        plugins_path = Path(self.server.path) / "plugins"
        
        if plugins_path.exists():
            for plugin_file in plugins_path.glob("*.jar"):
                item = QTreeWidgetItem(self.plugins_tree)
                item.setText(0, plugin_file.stem)
                item.setText(1, "Enabled" if plugin_file.suffix == ".jar" else "Disabled")
                item.setText(2, "Unknown")  # Version would need parsing
                
                try:
                    size = plugin_file.stat().st_size
                    if size < 1024 * 1024:
                        item.setText(3, f"{size // 1024} KB")
                    else:
                        item.setText(3, f"{size // (1024 * 1024)} MB")
                except:
                    item.setText(3, "Unknown")
                
                item.setData(0, Qt.ItemDataRole.UserRole, str(plugin_file))
                
                # Color coding for different statuses
                if plugin_file.suffix == ".jar":
                    item.setForeground(1, QColor("#00ff88"))  # Green for enabled
                else:
                    item.setForeground(1, QColor("#ff6b6b"))  # Red for disabled
    
    def setup_plugin_details_panel(self):
        """Setup the plugin details panel"""
        layout = QVBoxLayout(self.plugin_details)
        
        # Plugin header
        self.plugin_header = QLabel("Select a plugin to view details")
        self.plugin_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #00d4ff;
            padding: 10px;
            border: 1px solid #4f5565;
            border-radius: 5px;
            background: #1e1f29;
        """)
        layout.addWidget(self.plugin_header)
        
        # Plugin info scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.plugin_info_widget = QWidget()
        self.plugin_info_layout = QVBoxLayout(self.plugin_info_widget)
        scroll.setWidget(self.plugin_info_widget)
        layout.addWidget(scroll)
        
        # Download button
        self.download_btn = ModernButton("⬇️ Download & Install", primary=True)
        self.download_btn.clicked.connect(self.download_selected_plugin)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)
    
    def load_plugin_categories(self):
        """Load plugin categories from SpigotMC"""
        try:
            self.plugin_status.setText("🔄 Loading categories...")
            categories = self.spigot_browser.get_categories()
            self.category_combo.clear()
            self.category_combo.addItems(categories)
            self.plugin_status.setText(f"✅ Loaded {len(categories)} categories")
        except Exception as e:
            self.plugin_status.setText(f"❌ Error loading categories: {str(e)}")
    
    def search_plugins(self):
        """Search for plugins based on current filters"""
        try:
            query = self.plugin_search.text().strip()
            category = self.category_combo.currentText()
            sort_map = {
                "Downloads": "downloads",
                "Rating": "rating", 
                "Name": "name",
                "Updated": "updated"
            }
            sort = sort_map.get(self.sort_combo.currentText(), "downloads")
            
            self.plugin_status.setText("🔍 Searching plugins...")
            
            # Search plugins
            plugins, total_pages = self.spigot_browser.search_plugins(
                query=query,
                category=category if category != "All" else None,
                sort=sort,
                size=50
            )
            
            self.display_plugin_results(plugins)
            
            if plugins:
                self.plugin_status.setText(f"✅ Found {len(plugins)} plugins")
            else:
                self.plugin_status.setText("⚠️ No plugins found - Try different search terms or check your internet connection")
                # Clear the results display
                self.browser_list.clear()
                self.plugin_cache.clear()
                
        except Exception as e:
            self.plugin_status.setText(f"❌ Search error: {str(e)}")
            QMessageBox.warning(self, "Search Error", f"Failed to search plugins: {str(e)}")
    
    def load_popular_plugins(self):
        """Load popular plugins"""
        try:
            self.plugin_status.setText("🔥 Loading popular plugins...")
            plugins = self.spigot_browser.get_popular_plugins(30)
            self.display_plugin_results(plugins)
            
            if plugins:
                self.plugin_status.setText(f"✅ Loaded {len(plugins)} popular plugins")
            else:
                self.plugin_status.setText("⚠️ No popular plugins found - Check your internet connection")
                # Clear the results display
                self.browser_list.clear()
                self.plugin_cache.clear()
                
        except Exception as e:
            self.plugin_status.setText(f"❌ Error loading popular plugins: {str(e)}")
            QMessageBox.warning(self, "Load Error", f"Failed to load popular plugins: {str(e)}")
    
    def load_recent_plugins(self):
        """Load recently updated plugins"""
        try:
            self.plugin_status.setText("🆕 Loading recent plugins...")
            plugins = self.spigot_browser.get_recent_plugins(30)
            self.display_plugin_results(plugins)
            
            if plugins:
                self.plugin_status.setText(f"✅ Loaded {len(plugins)} recent plugins")
            else:
                self.plugin_status.setText("⚠️ No recent plugins found - Check your internet connection")
                # Clear the results display
                self.browser_list.clear()
                self.plugin_cache.clear()
                
        except Exception as e:
            self.plugin_status.setText(f"❌ Error loading recent plugins: {str(e)}")
            QMessageBox.warning(self, "Load Error", f"Failed to load recent plugins: {str(e)}")
    
    def display_plugin_results(self, plugins: List[PluginInfo]):
        """Display plugin search results"""
        self.browser_list.clear()
        self.plugin_cache.clear()
        
        for plugin in plugins:
            item = QTreeWidgetItem(self.browser_list)
            item.setText(0, plugin.name)
            item.setText(1, plugin.author)
            item.setText(2, f"{plugin.downloads:,}")
            item.setText(3, f"{plugin.rating:.1f}/5.0" if plugin.rating > 0 else "N/A")
            item.setText(4, plugin.category)
            
            # Store plugin data
            item.setData(0, Qt.ItemDataRole.UserRole, plugin.id)
            self.plugin_cache[plugin.id] = plugin
            
            # Color coding
            if plugin.premium:
                item.setForeground(0, QColor("#ffaa00"))  # Orange for premium
            elif plugin.rating >= 4.0:
                item.setForeground(0, QColor("#00ff88"))  # Green for highly rated
    
    def show_plugin_details(self, item):
        """Show detailed information about selected plugin"""
        plugin_id = item.data(0, Qt.ItemDataRole.UserRole)
        if plugin_id in self.plugin_cache:
            plugin = self.plugin_cache[plugin_id]
            self.current_plugin = plugin
            self.update_plugin_details_display(plugin)
            self.download_btn.setEnabled(not plugin.premium)
    
    def update_plugin_details_display(self, plugin: PluginInfo):
        """Update the plugin details display"""
        # Clear previous details
        for i in reversed(range(self.plugin_info_layout.count())):
            child = self.plugin_info_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Plugin header
        self.plugin_header.setText(f"🔌 {plugin.name} by {plugin.author}")
        
        # Plugin info
        info_items = [
            ("🏷️ Name:", plugin.name),
            ("👤 Author:", plugin.author),
            ("💫 Version:", plugin.version),
            ("📈 Downloads:", f"{plugin.downloads:,}"),
            ("⭐ Rating:", f"{plugin.rating:.1f}/5.0" if plugin.rating > 0 else "Not rated"),
            ("🗂 Category:", plugin.category),
            ("💰 Price:", "Free" if plugin.price == 0 else f"${plugin.price:.2f}"),
            ("📅 Updated:", plugin.updated),
        ]
        
        for label, value in info_items:
            row = QHBoxLayout()
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #00d4ff;")
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: #e6e6e6;")
            
            row.addWidget(label_widget)
            row.addWidget(value_widget)
            row.addStretch()
            
            row_widget = QWidget()
            row_widget.setLayout(row)
            self.plugin_info_layout.addWidget(row_widget)
        
        # Description
        desc_label = QLabel("📝 Description:")
        desc_label.setStyleSheet("font-weight: bold; color: #00d4ff; margin-top: 10px;")
        self.plugin_info_layout.addWidget(desc_label)
        
        desc_text = QLabel(plugin.description)
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("color: #e6e6e6; padding: 5px; background: #1e1f29; border-radius: 3px;")
        self.plugin_info_layout.addWidget(desc_text)
        
        # Premium warning
        if plugin.premium:
            premium_label = QLabel("⚠️ This is a premium plugin and cannot be downloaded automatically.")
            premium_label.setStyleSheet("color: #ffaa00; font-weight: bold; padding: 5px;")
            self.plugin_info_layout.addWidget(premium_label)
        
        self.plugin_info_layout.addStretch()
    
    def download_selected_plugin(self):
        """Download and install the selected plugin"""
        if not self.current_plugin:
            return
        
        if self.current_plugin.premium:
            QMessageBox.warning(self, "Premium Plugin", 
                "This is a premium plugin. Please purchase and download it manually from SpigotMC.")
            return
        
        try:
            plugins_path = Path(self.server.path) / "plugins"
            plugins_path.mkdir(exist_ok=True)
            
            self.plugin_status.setText(f"⬇️ Downloading {self.current_plugin.name}...")
            self.download_btn.setEnabled(False)
            self.download_btn.setText("⬇️ Downloading...")
            
            # Download plugin in a separate thread
            import threading
            download_thread = threading.Thread(
                target=self._download_plugin_thread,
                args=(self.current_plugin, plugins_path),
                daemon=True
            )
            download_thread.start()
            
        except Exception as e:
            self.plugin_status.setText(f"❌ Download failed: {str(e)}")
            QMessageBox.warning(self, "Download Error", f"Failed to download plugin: {str(e)}")
            self.download_btn.setEnabled(True)
            self.download_btn.setText("⬇️ Download & Install")
    
    def _download_plugin_thread(self, plugin: PluginInfo, destination: Path):
        """Download plugin in background thread"""
        try:
            success = self.spigot_browser.download_plugin(plugin, destination)
            
            if success:
                # Update UI in main thread
                QTimer.singleShot(0, lambda: self._download_complete(plugin.name, True))
            else:
                QTimer.singleShot(0, lambda: self._download_complete(plugin.name, False))
                
        except Exception as e:
            QTimer.singleShot(0, lambda: self._download_complete(plugin.name, False, str(e)))
    
    def _download_complete(self, plugin_name: str, success: bool, error: str = None):
        """Handle download completion"""
        if success:
            self.plugin_status.setText(f"✅ Successfully downloaded {plugin_name}")
            QMessageBox.information(self, "Download Complete", 
                f"Plugin '{plugin_name}' has been downloaded and installed!\n\n"
                "Restart your server to load the new plugin.")
            self.refresh_plugins()  # Refresh installed plugins list
        else:
            error_msg = f"Failed to download {plugin_name}"
            if error:
                error_msg += f": {error}"
            self.plugin_status.setText(f"❌ {error_msg}")
            QMessageBox.warning(self, "Download Failed", error_msg)
        
        self.download_btn.setEnabled(True)
        self.download_btn.setText("⬇️ Download & Install")
    
    def add_plugin(self):
        """Add a new plugin from local file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Add Plugin", "", "JAR Files (*.jar);;All Files (*)"
        )
        if file_path:
            source_path = Path(file_path)
            plugins_path = Path(self.server.path) / "plugins"
            plugins_path.mkdir(exist_ok=True)
            dest_path = plugins_path / source_path.name
            
            try:
                import shutil
                shutil.copy2(source_path, dest_path)
                self.refresh_plugins()
                QMessageBox.information(self, "Success", f"Added plugin: {source_path.name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not add plugin: {str(e)}")
    
    def remove_plugin(self):
        """Remove selected plugin"""
        selected_item = self.plugins_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin to remove.")
            return
        
        plugin_name = selected_item.text(0)
        plugin_path = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Remove Plugin",
            f"Are you sure you want to remove '{plugin_name}'?\n\n"
            "This will delete the plugin file permanently.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Path(plugin_path).unlink()
                self.refresh_plugins()
                QMessageBox.information(self, "Success", f"Removed plugin: {plugin_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not remove plugin: {str(e)}")
    
    def closeEvent(self, a0):
        """Handle window close event"""
        self.timer.stop()
        if a0:
            a0.accept()


def create_application():
    """Create and configure the application"""
    app = QApplication(sys.argv)
    app.setApplicationName("CrazeDyn Panel")
    app.setApplicationVersion("1.0.0")
    
    # Set app icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    return app

def main():
    """Main application entry point"""
    app = create_application()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start server monitoring
    window.server_manager.start_monitoring()
    
    # Run the application
    try:
        sys.exit(app.exec())
    except SystemExit:
        window.server_manager.stop_monitoring()
        pass