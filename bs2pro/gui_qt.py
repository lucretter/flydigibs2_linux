#!/usr/bin/env python3
"""
PyQt6 Native GUI for BS2PRO Controller
Provides native KDE/Plasma theme integration with Breeze theme support
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QGroupBox, QFrame, QSystemTrayIcon, QMenu, QMessageBox, QDialog, QScrollArea,
    QLineEdit, QSpinBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QColor

# Import our existing modules
try:
    from .cpu_monitor import CPUMonitor
    from .smart_mode import SmartModeManager
except ImportError:
    # Fallback for direct execution
    from cpu_monitor import CPUMonitor
    from smart_mode import SmartModeManager


class BS2ProQtGUI(QMainWindow):
    """Native PyQt6 GUI for BS2PRO Controller with KDE/Breeze theme integration"""
    
    def __init__(self, controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
        super().__init__()
        
        # Store references
        self.controller = controller
        self.config_manager = config_manager
        self.rpm_commands = rpm_commands
        self.commands = commands
        self.default_settings = default_settings
        self.icon_path = icon_path
        
        # Initialize monitoring components
        self.cpu_monitor = CPUMonitor()
        self.smart_mode_manager = SmartModeManager()
        self.current_rpm = None
        
        # Initialize system tray
        self.tray_icon = None
        self.minimize_to_tray = True
        
        # Initialize UI
        self.init_ui()
        self.setup_monitoring()
        self.update_device_status()
        
        # Setup system tray if available
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.setup_system_tray()
        
        # Show window
        self.show()
        
    def init_ui(self):
        """Initialize the user interface with native Qt styling"""
        self.setWindowTitle("BS2PRO Controller")
        self.setMinimumSize(450, 480)  # Increased height from 420 to 480
        self.resize(450, 520)  # Increased height from 480 to 520
        
        # Set window icon
        if self.icon_path and os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout with balanced spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)  # Increased width margins
        main_layout.setSpacing(10)  # Increased from 8 to 10
        
        # Header section
        self.create_header_section(main_layout)
        
        # Device status section
        self.create_device_status_section(main_layout)
        
        # Device settings section
        self.create_device_settings_section(main_layout)
        
        # Fan speed control section
        self.create_fan_speed_section(main_layout)
        
        # Smart mode section
        self.create_smart_mode_section(main_layout)
        
        # Add stretch to push everything to top
        main_layout.addStretch()
        
        # Footer
        self.create_footer_section(main_layout)
        
        # Center window on screen
        self.center_window()
        
    def create_header_section(self, parent_layout):
        """Create the header section with app title"""
        header_label = QLabel("BS2PRO Controller")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #2980b9; margin: 4px 0px;")  # Reduced margin
        parent_layout.addWidget(header_label)
        
    def create_device_status_section(self, parent_layout):
        """Create device status display"""
        status_group = QGroupBox("Device Status")
        status_group.setMinimumHeight(65)  # Increased from 55 to accommodate longer device text
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        
        self.status_label = QLabel("Device Status: Not Connected")
        status_font = QFont()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 6px;")  # Increased padding for better text display
        
        status_layout.addWidget(self.status_label)
        parent_layout.addWidget(status_group)
        
    def create_device_settings_section(self, parent_layout):
        """Create device settings controls"""
        settings_group = QGroupBox("Device Settings")
        settings_group.setMinimumHeight(110)  # Increased from 100
        settings_layout = QGridLayout(settings_group)
        settings_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        settings_layout.setSpacing(8)  # Increased spacing
        
        # Autostart Mode
        autostart_label = QLabel("Autostart Mode:")
        autostart_label.setToolTip("Configure how the device starts up")
        settings_layout.addWidget(autostart_label, 0, 0)
        
        self.autostart_combo = QComboBox()
        self.autostart_combo.addItems(["OFF", "Instant", "Delayed"])
        self.autostart_combo.setCurrentText(self.config_manager.load_setting("autostart_mode", "OFF"))
        self.autostart_combo.currentTextChanged.connect(self.on_autostart_select)
        self.autostart_combo.setToolTip("Choose autostart behavior")
        self.autostart_combo.setMinimumWidth(140)  # Increased from 120
        self.autostart_combo.setMinimumHeight(24)  # Ensure proper height
        self.autostart_combo.setStyleSheet("padding-left: 8px; padding-right: 8px;")  # Add left/right padding
        settings_layout.addWidget(self.autostart_combo, 0, 1)
        
        # RPM Indicator checkbox
        self.rpm_indicator_cb = QCheckBox("RPM Indicator")
        self.rpm_indicator_cb.setChecked(self.config_manager.load_setting("rpm_indicator", "False") == "True")
        self.rpm_indicator_cb.toggled.connect(self.on_rpm_toggle)
        self.rpm_indicator_cb.setToolTip("Enable/disable RPM feedback from device")
        settings_layout.addWidget(self.rpm_indicator_cb, 1, 0, 1, 2)
        
        # Start When Powered checkbox
        self.start_powered_cb = QCheckBox("Start When Powered")
        self.start_powered_cb.setChecked(self.config_manager.load_setting("start_when_powered", "False") == "True")
        self.start_powered_cb.toggled.connect(self.on_start_toggle)
        self.start_powered_cb.setToolTip("Automatically start when device is powered on")
        settings_layout.addWidget(self.start_powered_cb, 2, 0, 1, 2)
        
        parent_layout.addWidget(settings_group)
        
    def create_fan_speed_section(self, parent_layout):
        """Create fan speed controls"""
        fan_group = QGroupBox("Fan Speed Control")
        fan_group.setMinimumHeight(90)  # Increased from 80
        fan_layout = QVBoxLayout(fan_group)
        fan_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        fan_layout.setSpacing(8)  # Increased spacing
        
        # RPM selection row
        rpm_row = QHBoxLayout()
        
        rpm_label = QLabel("Select Fan Speed:")
        rpm_row.addWidget(rpm_label)
        
        self.rpm_combo = QComboBox()
        self.rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
        self.rpm_combo.addItems([str(rpm) for rpm in self.rpm_values])
        self.rpm_combo.setMinimumWidth(100)
        self.rpm_combo.setMinimumHeight(24)  # Ensure proper height
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.rpm_combo.setCurrentText(str(last_rpm))
        self.rpm_combo.currentTextChanged.connect(self.on_rpm_select)
        self.rpm_combo.setToolTip("Choose fan RPM setting")
        self.rpm_combo.setMinimumWidth(120)
        self.rpm_combo.setStyleSheet("padding-left: 8px; padding-right: 8px;")  # Add left/right padding
        rpm_row.addWidget(self.rpm_combo)
        
        rpm_row.addStretch()
        fan_layout.addLayout(rpm_row)
        
        # Current RPM display
        self.rpm_display_label = QLabel(f"Current: {last_rpm} RPM")
        rpm_font = QFont()
        rpm_font.setBold(True)
        self.rpm_display_label.setFont(rpm_font)
        self.rpm_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rpm_display_label.setStyleSheet("color: #1f538d; padding: 3px;")  # Reduced padding
        fan_layout.addWidget(self.rpm_display_label)
        
        parent_layout.addWidget(fan_group)
        
    def create_smart_mode_section(self, parent_layout):
        """Create smart mode controls"""
        smart_group = QGroupBox("Smart Mode")
        smart_group.setMinimumHeight(120)  # Increased from 105 to accommodate all text
        smart_layout = QVBoxLayout(smart_group)
        smart_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        smart_layout.setSpacing(8)  # Increased spacing
        
        # Smart mode enable checkbox
        self.smart_mode_cb = QCheckBox("Enable Smart Mode (Auto-adjust based on CPU temp)")
        self.smart_mode_cb.setChecked(self.smart_mode_manager.is_smart_mode_enabled())
        self.smart_mode_cb.toggled.connect(self.on_smart_mode_toggle)
        self.smart_mode_cb.setToolTip("Automatically adjust fan speed based on CPU temperature")
        smart_layout.addWidget(self.smart_mode_cb)
        
        # Temperature and config row
        temp_config_row = QHBoxLayout()
        
        # Temperature display (left side)
        temp_info_layout = QVBoxLayout()
        
        self.temp_label = QLabel("CPU Temperature: --°C")
        temp_font = QFont()
        temp_font.setBold(True)
        self.temp_label.setFont(temp_font)
        self.temp_label.setStyleSheet("color: #17a2b8; padding: 2px;")
        temp_info_layout.addWidget(self.temp_label)
        
        self.smart_status_label = QLabel("Smart Mode: Off")
        self.smart_status_label.setStyleSheet("color: gray; font-size: 10px; padding: 2px;")
        temp_info_layout.addWidget(self.smart_status_label)
        
        temp_config_row.addLayout(temp_info_layout)
        temp_config_row.addStretch()
        
        # Configure button (right side)
        self.configure_btn = QPushButton("Configure")
        self.configure_btn.clicked.connect(self.open_smart_mode_config)
        self.configure_btn.setToolTip("Configure temperature ranges and RPM settings")
        self.configure_btn.setMinimumWidth(100)
        self.configure_btn.setMaximumWidth(120)
        temp_config_row.addWidget(self.configure_btn)
        
        smart_layout.addLayout(temp_config_row)
        parent_layout.addWidget(smart_group)
        
    def create_footer_section(self, parent_layout):
        """Create footer with version info"""
        # Add small spacer before footer
        parent_layout.addSpacing(8)
        
        footer_label = QLabel("BS2PRO Controller v2.3.0 • Made with ❤️")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: gray; font-size: 10px; padding: 4px;")
        parent_layout.addWidget(footer_label)
        
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        window = self.frameGeometry()
        center = screen.center()
        window.moveCenter(center)
        self.move(window.topLeft())
        
    def setup_monitoring(self):
        """Setup CPU and RPM monitoring"""
        # Setup CPU monitoring callbacks
        self.cpu_monitor.add_callback(self.on_temperature_change)
        self.cpu_monitor.start_monitoring()
        
        # Setup RPM monitoring callbacks
        self.controller.add_rpm_callback(self.on_rpm_update)
        self.controller.start_rpm_monitoring()
        
    def setup_system_tray(self):
        """Setup system tray icon"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            
            # Set icon
            if self.icon_path and os.path.exists(self.icon_path):
                self.tray_icon.setIcon(QIcon(self.icon_path))
            else:
                # Fallback icon
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor('blue'))
                self.tray_icon.setIcon(QIcon(pixmap))
            
            # Create context menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show_window)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            smart_action = QAction("Toggle Smart Mode", self)
            smart_action.triggered.connect(self.toggle_smart_mode_from_tray)
            tray_menu.addAction(smart_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Exit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.setToolTip("BS2PRO Controller")
            
            # Connect double-click to show window
            self.tray_icon.activated.connect(self.on_tray_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
            logging.info("System tray icon created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create system tray icon: {e}")
            self.tray_icon = None
            
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
            
    def show_window(self):
        """Show and restore window"""
        self.show()
        self.raise_()
        self.activateWindow()
        
    def toggle_smart_mode_from_tray(self):
        """Toggle smart mode from tray menu"""
        current_state = self.smart_mode_cb.isChecked()
        self.smart_mode_cb.setChecked(not current_state)
        
    def quit_application(self):
        """Quit the application"""
        self.cleanup()
        QApplication.quit()
        
    # Event handlers
    def on_autostart_select(self, selected_value):
        """Handle autostart mode selection"""
        cmd = self.commands[f"autostart_{selected_value.lower()}"]
        success = self.controller.send_command(cmd, status_callback=self.create_status_callback())
        self.config_manager.save_setting("autostart_mode", selected_value)
        if not success:
            self.update_status("Failed to set autostart mode", "#dc3545")
            
    def on_rpm_toggle(self, checked):
        """Handle RPM indicator toggle"""
        cmd = self.commands["rpm_on"] if checked else self.commands["rpm_off"]
        success = self.controller.send_command(cmd, status_callback=self.create_status_callback())
        self.config_manager.save_setting("rpm_indicator", str(checked))
        if not success:
            self.update_status("Failed to toggle RPM indicator", "#dc3545")
            
    def on_start_toggle(self, checked):
        """Handle start when powered toggle"""
        success = True
        status_callback = self.create_status_callback()
        if checked:
            success = self.controller.send_command(self.commands["startwhenpowered_on"], status_callback=status_callback)
        else:
            for cmd in self.commands["startwhenpowered_off"]:
                if not self.controller.send_command(cmd, status_callback=status_callback):
                    success = False
        self.config_manager.save_setting("start_when_powered", str(checked))
        if not success:
            self.update_status("Failed to toggle start when powered", "#dc3545")
            
    def on_rpm_select(self, selected_value):
        """Handle RPM selection"""
        rpm = int(selected_value)
        success = self.controller.send_command(self.rpm_commands[rpm], status_callback=self.create_status_callback())
        self.config_manager.save_setting("last_rpm", rpm)
        if not success:
            self.update_status(f"Failed to set RPM: {rpm}", "#dc3545")
            
    def on_rpm_update(self, rpm):
        """Handle real-time RPM updates"""
        try:
            self.rpm_display_label.setText(f"Current: {rpm} RPM")
            logging.info(f"RPM updated from device: {rpm}")
        except Exception as e:
            logging.error(f"Error updating RPM display: {e}")
            
    def on_temperature_change(self, temperature):
        """Handle CPU temperature changes"""
        self.temp_label.setText(f"CPU Temperature: {temperature:.1f}°C")
        
        # Auto-adjust RPM if smart mode is enabled
        if self.smart_mode_manager.is_smart_mode_enabled():
            self.auto_adjust_rpm(temperature)
            
    def on_smart_mode_toggle(self, checked):
        """Handle smart mode toggle"""
        self.smart_mode_manager.set_enabled(checked)
        
        if checked:
            try:
                ranges = self.smart_mode_manager.get_temperature_ranges()
                if not ranges:
                    self.smart_status_label.setText("Smart Mode: No temperature ranges configured")
                    self.smart_status_label.setStyleSheet("color: #ffc107;")
                    return
                
                current_temp = self.cpu_monitor.get_temperature()
                if current_temp <= 0:
                    self.smart_status_label.setText("Smart Mode: On - Waiting for temperature data")
                    self.smart_status_label.setStyleSheet("color: #17a2b8;")
                    return
                
                self.smart_status_label.setText("Smart Mode: On - Monitoring CPU temperature")
                self.smart_status_label.setStyleSheet("color: #28a745;")
                
                # Auto-adjust with a small delay
                QTimer.singleShot(100, lambda: self.auto_adjust_rpm(current_temp))
                
            except Exception as e:
                logging.error(f"Error enabling smart mode: {e}")
                self.smart_status_label.setText("Smart Mode: Error - Check configuration")
                self.smart_status_label.setStyleSheet("color: #dc3545;")
        else:
            self.smart_status_label.setText("Smart Mode: Off")
            self.smart_status_label.setStyleSheet("color: gray;")
            self.current_rpm = None
            
    def auto_adjust_rpm(self, temperature):
        """Automatically adjust RPM based on temperature"""
        try:
            target_rpm = self.smart_mode_manager.get_rpm_for_temperature(temperature)
            range_info = self.smart_mode_manager.get_range_for_temperature(temperature)
            
            # Validate target RPM
            if target_rpm is None or target_rpm < 1000 or target_rpm > 3000:
                logging.warning(f"Invalid target RPM: {target_rpm}")
                self.smart_status_label.setText("Smart Mode: Invalid RPM configuration")
                self.smart_status_label.setStyleSheet("color: #dc3545;")
                return
            
            # Check if RPM command exists
            if target_rpm not in self.rpm_commands:
                logging.warning(f"RPM command not found for {target_rpm}")
                self.smart_status_label.setText("Smart Mode: RPM command not available")
                self.smart_status_label.setStyleSheet("color: #dc3545;")
                return
            
            # Only change RPM if it's different from current
            if target_rpm != self.current_rpm:
                self.current_rpm = target_rpm
                
                # Send command to device
                success = self.controller.send_command(self.rpm_commands[target_rpm], status_callback=self.create_status_callback())
                
                if success:
                    # Update combobox selection
                    self.rpm_combo.setCurrentText(str(target_rpm))
                    
                    # Update smart status
                    if range_info:
                        self.smart_status_label.setText(f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)")
                        self.smart_status_label.setStyleSheet("color: #28a745;")
                    else:
                        self.smart_status_label.setText(f"Smart Mode: {target_rpm} RPM (Auto)")
                        self.smart_status_label.setStyleSheet("color: #28a745;")
                    
                    # Save setting
                    self.config_manager.save_setting("last_rpm", target_rpm)
                else:
                    self.smart_status_label.setText("Smart Mode: Failed to adjust RPM")
                    self.smart_status_label.setStyleSheet("color: #dc3545;")
            else:
                # RPM is already correct, just update status
                if range_info:
                    self.smart_status_label.setText(f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)")
                    self.smart_status_label.setStyleSheet("color: #28a745;")
                else:
                    self.smart_status_label.setText(f"Smart Mode: {target_rpm} RPM (Auto)")
                    self.smart_status_label.setStyleSheet("color: #28a745;")
                    
        except Exception as e:
            logging.error(f"Error in auto RPM adjustment: {e}")
            self.smart_status_label.setText("Smart Mode: Error")
            self.smart_status_label.setStyleSheet("color: #dc3545;")
            
    def open_smart_mode_config(self):
        """Open smart mode configuration dialog"""
        dialog = SmartModeConfigDialog(self, self.smart_mode_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Configuration was saved, update display
            logging.info("Smart mode configuration updated")
            
    def create_status_callback(self):
        """Create status callback for device operations"""
        def status_callback(msg, style):
            color_map = {
                "success": "#28a745",
                "danger": "#dc3545", 
                "warning": "#ffc107",
                "info": "#17a2b8",
                "light": "#6c757d"
            }
            color = color_map.get(style, "#ffffff")
            self.update_status(msg, color)
            # Auto-reset status after 2 seconds
            QTimer.singleShot(2000, self.update_device_status)
        return status_callback
        
    def update_status(self, message, color):
        """Update status message with color"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
    def update_device_status(self):
        """Update device status display"""
        vid, pid = self.controller.detect_bs2pro()
        if vid and pid:
            self.update_status(f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", "#28a745")
        else:
            self.update_status("❌ BS2PRO not detected", "#dc3545")
            
    # Window event handlers
    def closeEvent(self, event):
        """Handle window close event"""
        if self.minimize_to_tray and self.tray_icon and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            self.hide()
            event.ignore()
        else:
            # Actually close the application
            self.cleanup()
            event.accept()
            
    def changeEvent(self, event):
        """Handle window state changes"""
        if (event.type() == event.Type.WindowStateChange and 
            self.minimize_to_tray and 
            self.tray_icon and 
            self.tray_icon.isVisible() and 
            self.isMinimized()):
            # Hide window when minimized if tray is available
            self.hide()
            event.ignore()
        else:
            super().changeEvent(event)
            
    def cleanup(self):
        """Cleanup resources"""
        if self.cpu_monitor:
            self.cpu_monitor.stop_monitoring()
        if self.controller:
            self.controller.stop_rpm_monitoring()
        if self.tray_icon:
            self.tray_icon.hide()


class SmartModeConfigDialog(QDialog):
    """Smart Mode Configuration Dialog"""
    
    def __init__(self, parent, smart_mode_manager):
        super().__init__(parent)
        self.smart_mode_manager = smart_mode_manager
        self.range_widgets = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Smart Mode Configuration")
        self.setModal(True)
        self.resize(700, 600)  # Reduced width from 800 to 700 for tighter layout
        
        # Main layout with tighter spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 12
        layout.setSpacing(6)  # Reduced from 8
        
        # Title
        title_label = QLabel("Temperature Range Configuration")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel("Configure temperature ranges and their corresponding RPM values.\n"
                             "Ranges should not overlap and should be in ascending order.")
        instructions.setStyleSheet("color: gray;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Scroll area for ranges
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)  # Increased from 300 to show more elements
        
        # Widget inside scroll area
        scroll_widget = QWidget()
        self.ranges_layout = QVBoxLayout(scroll_widget)
        self.ranges_layout.setSpacing(6)  # Reduced from 8
        
        # Load existing ranges
        self.load_ranges()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Add new range button
        add_btn = QPushButton("Add New Range")
        add_btn.clicked.connect(self.add_new_range)
        layout.addWidget(add_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Center dialog
        self.center_dialog()
        
    def center_dialog(self):
        """Center dialog on parent"""
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            center_point = parent_geometry.center()
            dialog_geometry = self.frameGeometry()
            dialog_geometry.moveCenter(center_point)
            self.move(dialog_geometry.topLeft())
            
    def load_ranges(self):
        """Load existing temperature ranges"""
        ranges = self.smart_mode_manager.get_temperature_ranges()
        for i, range_data in enumerate(ranges):
            self.create_range_widget(range_data, i)
            
    def create_range_widget(self, range_data, index):
        """Create a temperature range widget"""
        range_frame = QFrame()
        range_frame.setFrameStyle(QFrame.Shape.Box)
        range_layout = QHBoxLayout(range_frame)
        range_layout.setContentsMargins(6, 6, 6, 6)  # Reduced from 8
        range_layout.setSpacing(6)  # Add tighter spacing between elements
        
        # Min temperature
        range_layout.addWidget(QLabel("Min:"))
        min_spin = QSpinBox()  # Changed from QDoubleSpinBox to QSpinBox
        min_spin.setRange(-50, 200)
        min_spin.setValue(int(range_data['min_temp']))  # Convert to int
        min_spin.setSuffix("°C")
        range_layout.addWidget(min_spin)
        
        # Max temperature
        range_layout.addWidget(QLabel("Max:"))
        max_spin = QSpinBox()  # Changed from QDoubleSpinBox to QSpinBox
        max_spin.setRange(-50, 200)
        max_spin.setValue(int(range_data['max_temp']))  # Convert to int
        max_spin.setSuffix("°C")
        range_layout.addWidget(max_spin)
        
        # RPM
        range_layout.addWidget(QLabel("RPM:"))
        rpm_combo = QComboBox()
        rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]  # Available RPM values
        rpm_combo.addItems([str(rpm) for rpm in rpm_values])
        # Set current value or default to 1300
        current_rpm = str(range_data['rpm'])
        if current_rpm in [str(rpm) for rpm in rpm_values]:
            rpm_combo.setCurrentText(current_rpm)
        else:
            rpm_combo.setCurrentText("1300")  # Default fallback
        rpm_combo.setStyleSheet("padding-left: 8px; padding-right: 8px;")  # Add padding for consistency
        range_layout.addWidget(rpm_combo)
        
        # Description
        range_layout.addWidget(QLabel("Description:"))
        desc_edit = QLineEdit(range_data.get('description', ''))
        desc_edit.setMaximumWidth(120)  # Reduced from 150 for tighter layout
        range_layout.addWidget(desc_edit)
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_range_widget(range_frame))
        remove_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; }")
        range_layout.addWidget(remove_btn)
        
        # Store widget references
        widget_data = {
            'frame': range_frame,
            'min_spin': min_spin,
            'max_spin': max_spin,
            'rpm_combo': rpm_combo,  # Changed from rpm_spin to rpm_combo
            'desc_edit': desc_edit,
            'index': index
        }
        self.range_widgets.append(widget_data)
        self.ranges_layout.addWidget(range_frame)
        
    def add_new_range(self):
        """Add a new temperature range"""
        new_range = {
            'min_temp': 0,
            'max_temp': 10,
            'rpm': 1300,
            'description': 'New range'
        }
        self.create_range_widget(new_range, len(self.range_widgets))
        
    def remove_range_widget(self, frame):
        """Remove a temperature range widget"""
        # Find and remove the widget from our list
        for i, widget_data in enumerate(self.range_widgets):
            if widget_data['frame'] == frame:
                self.range_widgets.pop(i)
                break
        
        # Remove from layout and delete
        self.ranges_layout.removeWidget(frame)
        frame.deleteLater()
        
    def save_configuration(self):
        """Save the temperature range configuration"""
        try:
            # Clear existing ranges
            self.smart_mode_manager.temperature_ranges = []
            
            # Collect data from widgets
            ranges_data = []
            for widget_data in self.range_widgets:
                min_temp = widget_data['min_spin'].value()
                max_temp = widget_data['max_spin'].value()
                rpm = int(widget_data['rpm_combo'].currentText())  # Get RPM from combo box
                description = widget_data['desc_edit'].text() or "Range"
                
                # Validate range
                if min_temp >= max_temp:
                    QMessageBox.warning(self, "Invalid Range", 
                                      f"Min temperature ({min_temp}) must be less than max temperature ({max_temp})")
                    return
                
                ranges_data.append({
                    'min_temp': min_temp,
                    'max_temp': max_temp,
                    'rpm': rpm,
                    'description': description
                })
            
            # Sort by min temperature
            ranges_data.sort(key=lambda x: x['min_temp'])
            
            # Check for overlaps
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['max_temp'] > ranges_data[i + 1]['min_temp']:
                    QMessageBox.warning(self, "Overlapping Ranges", 
                                      "Temperature ranges cannot overlap. Please adjust the ranges.")
                    return
            
            # Add ranges to smart mode manager
            for range_data in ranges_data:
                self.smart_mode_manager.add_temperature_range(
                    range_data['min_temp'],
                    range_data['max_temp'],
                    range_data['rpm'],
                    range_data['description']
                )
            
            # Save configuration
            self.smart_mode_manager.save_config()
            
            # Show success message
            QMessageBox.information(self, "Success", 
                                  f"Smart mode configuration saved with {len(ranges_data)} ranges!")
            
            # Accept dialog
            self.accept()
            
        except Exception as e:
            logging.error(f"Error saving smart mode config: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")


def apply_gnome_dark_palette(app):
    """Apply GNOME Adwaita dark mode palette colors"""
    try:
        from PyQt6.QtGui import QPalette, QColor
        
        palette = QPalette()
        # Adwaita dark theme colors
        palette.setColor(QPalette.ColorRole.Window, QColor(46, 52, 54))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.Base, QColor(36, 41, 46))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(46, 52, 54))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(46, 52, 54))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.Text, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.Button, QColor(54, 59, 61))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(252, 175, 62))
        palette.setColor(QPalette.ColorRole.Link, QColor(53, 132, 228))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(53, 132, 228))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        print("🌙 Applied GNOME dark mode palette")
        return True
    except Exception as e:
        print(f"🔍 Could not apply dark palette: {e}")
        return False


def create_qt_application(controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
    """Create and run the PyQt6 application"""
    # Set Qt environment variables for native theming before creating QApplication
    import os
    
    # Detect actual desktop environment first
    actual_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    
    # Configure Qt platform theme based on actual desktop environment
    if 'kde' in actual_desktop or 'plasma' in actual_desktop:
        os.environ['QT_QPA_PLATFORMTHEME'] = 'kde'
        os.environ['KDE_SESSION_VERSION'] = '5'
    elif 'gnome' in actual_desktop:
        # For GNOME, try gtk3 first (better libadwaita integration)
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
        
        # Detect GNOME dark/light theme preference
        try:
            import subprocess
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                color_scheme = result.stdout.strip().strip("'\"")
                if 'dark' in color_scheme.lower():
                    os.environ['GTK_THEME'] = 'Adwaita:dark'
                    print(f"🌙 Detected GNOME dark mode: {color_scheme}")
                else:
                    os.environ['GTK_THEME'] = 'Adwaita'
                    print(f"☀️ Detected GNOME light mode: {color_scheme}")
            else:
                # Fallback: check gtk-theme setting
                result2 = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                                       capture_output=True, text=True, timeout=2)
                if result2.returncode == 0:
                    gtk_theme = result2.stdout.strip().strip("'\"")
                    if 'dark' in gtk_theme.lower():
                        os.environ['GTK_THEME'] = 'Adwaita:dark'
                        print(f"🌙 Detected dark GTK theme: {gtk_theme}")
                    else:
                        os.environ['GTK_THEME'] = 'Adwaita'
                        print(f"☀️ Detected light GTK theme: {gtk_theme}")
        except Exception as e:
            print(f"🔍 Could not detect GNOME theme preference: {e}")
            # Safe fallback
            os.environ['GTK_THEME'] = 'Adwaita'
    elif 'xfce' in actual_desktop:
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
    else:
        # For other DEs, use gtk3 as a safe fallback
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
    
    # Don't override the style - let Qt choose the appropriate one
    os.environ['QT_STYLE_OVERRIDE'] = ''
    
    # Force Qt to use X11 instead of Wayland for better theme support
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    # Set Qt plugin paths - detect distribution-specific paths
    qt_plugin_paths = []
    
    # Common Qt6 plugin paths for different distributions
    potential_paths = [
        '/usr/lib64/qt6/plugins',           # Fedora, RHEL, CentOS, openSUSE
        '/usr/lib/x86_64-linux-gnu/qt6/plugins',  # Ubuntu, Debian
        '/usr/lib/qt6/plugins',             # Generic fallback
        '/usr/local/lib/qt6/plugins'        # Local installations
    ]
    
    # Add only existing paths
    for path in potential_paths:
        if os.path.exists(path):
            qt_plugin_paths.append(path)
    
    # Set Qt plugin path environment variable
    if qt_plugin_paths:
        os.environ['QT_PLUGIN_PATH'] = ':'.join(qt_plugin_paths)
        print(f"🔌 Qt Plugin Path: {os.environ.get('QT_PLUGIN_PATH')}")
    else:
        print("⚠️  No Qt plugin paths found")
        
    print(f"🔌 Platform Theme: {os.environ.get('QT_QPA_PLATFORMTHEME')}")
    print(f"🔌 Platform: {os.environ.get('QT_QPA_PLATFORM')}")
    
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    # Force system plugin paths, not venv paths - use detected paths
    if qt_plugin_paths:
        app.setLibraryPaths(qt_plugin_paths)
        print(f"🔌 App library paths set to: {app.libraryPaths()}")
    else:
        print("⚠️  Using default library paths")
        
    # Set application properties
    app.setApplicationName("BS2PRO Controller")
    app.setApplicationVersion("2.4.0")
    app.setOrganizationName("BS2PRO")
    
    # Debug: Print current style information
    print(f"🎨 Initial Qt Style: {app.style().objectName()}")
    
    try:
        from PyQt6.QtWidgets import QStyleFactory
        available_styles = QStyleFactory.keys()
        print(f"🎨 Available Styles: {', '.join(available_styles)}")
        
        # Try to detect and set the appropriate native style
        import os
        desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        print(f"🖥️  Desktop Environment: {desktop_env}")
        
        # Add detected Qt plugin paths
        for plugin_path in qt_plugin_paths:
            if os.path.exists(plugin_path):
                app.addLibraryPath(plugin_path)
                print(f"🔌 Added Qt plugin path: {plugin_path}")
        
        # Refresh available styles after adding plugin paths
        available_styles = QStyleFactory.keys()
        print(f"🎨 Updated Available Style Keys: {', '.join(available_styles)}")
        
        # Try to set native style based on desktop environment
        style_set_successfully = False
        
        # First, let Qt try to use the system's native theme automatically
        print(f"🎨 Attempting to use native system theme...")
        
        # Don't force any specific style - let Qt choose the best one for the system
        # Qt will automatically use the appropriate style based on:
        # - The desktop environment
        # - System theme settings
        # - Available platform plugins
        
        # Only intervene if the default choice is clearly suboptimal or for specific DE needs
        current_style = app.style().objectName().lower()
        
        if 'gnome' in desktop_env:
            # For GNOME, prefer system theme integration
            # If no GTK integration is available, Fusion is acceptable for GNOME
            if current_style in ['windows']:
                # Windows style is not appropriate for GNOME
                if 'Fusion' in available_styles:
                    try:
                        fusion_style = QStyleFactory.create('Fusion')
                        if fusion_style:
                            app.setStyle(fusion_style)
                            print("🎨 Set Fusion style for GNOME (good libadwaita-like appearance)")
                            
                            # Apply dark palette if GNOME is in dark mode
                            if os.environ.get('GTK_THEME', '').endswith(':dark'):
                                apply_gnome_dark_palette(app)
                            
                            style_set_successfully = True
                    except Exception as e:
                        print(f"🔍 Could not set Fusion style: {e}")
            else:
                print(f"🎨 Using system-chosen style for GNOME: {current_style}")
                
                # Apply dark palette if in dark mode, regardless of style
                if os.environ.get('GTK_THEME', '').endswith(':dark'):
                    apply_gnome_dark_palette(app)
                
                style_set_successfully = True
        elif current_style == 'windows' and 'Fusion' in available_styles:
            # Windows style is usually not desirable on Linux - prefer Fusion
            try:
                fusion_style = QStyleFactory.create('Fusion')
                if fusion_style:
                    app.setStyle(fusion_style)
                    print("🎨 Upgraded from Windows style to Fusion for better Linux experience")
                    style_set_successfully = True
            except Exception as e:
                print(f"🔍 Could not set Fusion style: {e}")
        else:
            # Let the system theme take precedence
            print(f"🎨 Using system-chosen style: {current_style}")
            style_set_successfully = True
        
        # Final verification
        final_style = app.style().objectName()
        print(f"🎨 Active Qt Style: {final_style}")
        
        # If no style was set successfully, ensure we at least have Fusion (better than Windows)
        if not style_set_successfully and final_style.lower() == 'windows':
            if 'Fusion' in available_styles:
                try:
                    fusion_style = QStyleFactory.create('Fusion')
                    if fusion_style:
                        app.setStyle(fusion_style)
                        print("🎨 Applied Fusion as fallback (better than Windows style)")
                except Exception:
                    pass
        
    except Exception as e:
        print(f"🎨 Could not get/set style info: {e}")
    
    # Enable automatic high DPI scaling (if available in this PyQt6 version)
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # These attributes may not be available in newer PyQt6 versions
        # High DPI is handled automatically in newer versions
        pass
    
    # Create main window
    window = BS2ProQtGUI(controller, config_manager, rpm_commands, commands, default_settings, icon_path)
    
    # Run application
    return app.exec()