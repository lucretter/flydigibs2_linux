import customtkinter as ctk
import os
import sys
import logging
import tkinter as tk
from tkinter import messagebox
from cpu_monitor import CPUMonitor
from smart_mode import SmartModeManager

# Try to import Qt tray manager for system tray functionality
try:
    from qt_tray_manager import QtTrayManager
    TRAY_AVAILABLE = True
except ImportError:
    logging.warning("Qt tray manager not available - running without system tray support")
    QtTrayManager = None
    TRAY_AVAILABLE = False

class BS2ProGUI:
    def __init__(self, controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
        self.controller = controller
        self.config_manager = config_manager
        self.rpm_commands = rpm_commands
        self.commands = commands
        self.default_settings = default_settings
        self.icon_path = icon_path
        
        # Initialize smart mode and CPU monitoring
        self.cpu_monitor = CPUMonitor()
        self.smart_mode_manager = SmartModeManager()
        self.current_rpm = None  # Track current RPM for smart mode
        
        # Initialize tray manager
        self.tray_manager = None
        self.minimize_to_tray = True  # Option to minimize to tray instead of taskbar
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # "light" or "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("BS2PRO Controller")
        
        # Set window to be compact but resizable
        self.root.geometry("400x300")
        self.root.resizable(True, True)
        
        # Set window icon if provided
        if icon_path and os.path.exists(icon_path):
            try:
                # Use standard tkinter method for icon (works better with taskbar)
                import tkinter as tk
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
            except Exception as e:
                logging.warning(f"Could not load icon: {e}")
        
        self.setup_widgets()
        self.update_device_status()
        
        # Initialize system tray if available
        self._setup_tray()
        
        # Setup CPU monitoring callbacks
        self.cpu_monitor.add_callback(self.on_temperature_change)
        
        # Start CPU monitoring
        self.cpu_monitor.start_monitoring()
        
        # Setup RPM monitoring callbacks
        self.controller.add_rpm_callback(self.on_rpm_update)
        
        # Start RPM monitoring
        self.controller.start_rpm_monitoring()
        
        # Center window after widgets are created with proper sizing
        self.root.after(100, self.center_window)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind window state change event for minimize handling
        self.root.bind('<Unmap>', self._on_window_state_change)
        self.root.bind('<Map>', self._on_window_map)
        
        self.root.mainloop()

    def center_window(self):
        """Center the window on the screen and size to content"""
        self.root.update_idletasks()
        
        # Get the actual window size after widgets are rendered
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        
        # Ensure minimum width and appropriate height that shows all content
        width = max(width, 400)
        height = max(height, 290)  # Enough to show all content without excessive empty space
        
        # Calculate center position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Apply the geometry
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_tray(self):
        """Set up the system tray icon."""
        if TRAY_AVAILABLE and QtTrayManager:
            try:
                # Add a small delay to ensure GUI is fully initialized
                self.root.after(500, self._initialize_tray)
            except Exception as e:
                logging.error(f"Failed to schedule tray initialization: {e}")
        else:
            logging.info("System tray not available")

    def _initialize_tray(self):
        """Initialize the tray icon after GUI is ready."""
        try:
            if TRAY_AVAILABLE and QtTrayManager:
                logging.info("Initializing Qt system tray")
                self.tray_manager = QtTrayManager(self, self.icon_path)
                if self.tray_manager.start():
                    logging.info("Qt system tray icon initialized successfully")
                else:
                    logging.error("Failed to start Qt tray manager")
                    self.tray_manager = None
            else:
                logging.warning("Qt tray manager not available")
                self.tray_manager = None
                
        except Exception as e:
            logging.error(f"Failed to initialize system tray: {e}")
            self.tray_manager = None

    def _on_window_state_change(self, event):
        """Handle window state changes (minimize, etc.)."""
        # Only handle events for the main window and when it's being minimized
        if event.widget == self.root and self.minimize_to_tray and self.tray_manager:
            # Check if the window is actually being minimized
            if self.root.state() == 'iconic':
                self.root.after(100, self._minimize_to_tray)

    def _on_window_map(self, event):
        """Handle window being mapped (shown)."""
        if event.widget == self.root:
            logging.debug("Window mapped (shown)")

    def _minimize_to_tray(self):
        """Minimize the window to system tray."""
        if self.tray_manager and self.tray_manager.is_running:
            self.root.withdraw()  # Hide window
            logging.info("Window minimized to system tray")

    def show_from_tray(self):
        """Show window from system tray (called by tray manager)."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.state('normal')

    def toggle_smart_mode(self):
        """Toggle smart mode on/off (called from tray menu)."""
        try:
            if hasattr(self, 'smart_mode_enabled_var'):
                current_state = self.smart_mode_enabled_var.get()
                self.smart_mode_enabled_var.set(not current_state)
                logging.info(f"Smart mode toggled to: {not current_state}")
        except Exception as e:
            logging.error(f"Error toggling smart mode: {e}")

    def on_rpm_select(self, selected_value=None):
        # CustomTkinter passes the selected value directly
        if selected_value is None:
            rpm = int(self.rpm_combobox.get())
        else:
            rpm = int(selected_value)
        
        success = self.controller.send_command(self.rpm_commands[rpm], status_callback=self._create_status_callback())
        # Don't update RPM display here - let live monitoring handle it
        self.config_manager.save_setting("last_rpm", rpm)
        if not success:
            self.status_label.configure(text=f"Failed to set RPM: {rpm}", text_color="#dc3545")

    def on_rpm_toggle(self):
        state = self.rpm_var.get()
        cmd = self.commands["rpm_on"] if state else self.commands["rpm_off"]
        success = self.controller.send_command(cmd, status_callback=self._create_status_callback())
        self.config_manager.save_setting("rpm_indicator", str(state))
        if not success:
            self.status_label.configure(text="Failed to toggle RPM indicator", text_color="#dc3545")

    def on_rpm_update(self, rpm):
        """Callback for real-time RPM updates from the device"""
        try:
            # Update the RPM display with real-time data
            self.rpm_display_label.configure(text=f"Current: {rpm} RPM")
            logging.info(f"RPM updated from device: {rpm}")
        except Exception as e:
            logging.error(f"Error updating RPM display: {e}")

    def on_autostart_select(self, selected_value=None):
        # CustomTkinter passes the selected value directly
        if selected_value is None:
            mode = self.autostart_combobox.get()
        else:
            mode = selected_value
        
        cmd = self.commands[f"autostart_{mode.lower()}"]
        success = self.controller.send_command(cmd, status_callback=self._create_status_callback())
        self.config_manager.save_setting("autostart_mode", mode)
        if not success:
            self.status_label.configure(text="Failed to set autostart mode", text_color="#dc3545")

    def on_start_toggle(self):
        state = self.start_var.get()
        success = True
        status_callback = self._create_status_callback()
        if state:
            success = self.controller.send_command(self.commands["startwhenpowered_on"], status_callback=status_callback)
        else:
            for cmd in self.commands["startwhenpowered_off"]:
                if not self.controller.send_command(cmd, status_callback=status_callback):
                    success = False
        self.config_manager.save_setting("start_when_powered", str(state))
        if not success:
            self.status_label.configure(text="Failed to toggle start when powered", text_color="#dc3545")

    def reset_status_message(self):
        self.update_device_status()
        
    def get_color(self, style):
        """Convert style to CustomTkinter color"""
        color_map = {
            "success": "#28a745",
            "danger": "#dc3545", 
            "warning": "#ffc107",
            "info": "#17a2b8",
            "light": "#6c757d"
        }
        return color_map.get(style, "#ffffff")
    
    def _create_status_callback(self):
        """Create a status callback function for device status updates"""
        def status_callback(msg, style):
            self.status_label.configure(text=msg, text_color=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        return status_callback

    def setup_widgets(self):
        # Main container with proper spacing
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Header section
        self.create_header()
        
        # Device status section
        self.create_device_status()
        
        # Controls section
        self.create_controls_section()
        
        # Fan speed section
        self.create_fan_speed_section()
        
        # Smart mode section
        self.create_smart_mode_section()
        
        # Footer
        self.create_footer()

    def create_header(self):
        """Create ultra-compact header with title"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 6))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="BS2PRO Controller",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w")

    def create_device_status(self):
        """Create ultra-compact device status section"""
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.pack(fill="x", pady=(0, 6), padx=6)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Device Status: Not Connected",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_label.pack(pady=6)

    def create_controls_section(self):
        """Create ultra-compact controls section"""
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(fill="x", pady=(0, 4))
        
        # Section title
        title_label = ctk.CTkLabel(
            self.controls_frame,
            text="Device Settings",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(pady=(4, 2), padx=6, anchor="w")

        # Create a horizontal layout for controls
        controls_container = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        controls_container.pack(fill="x", padx=6, pady=(0, 4))

        # Left side - Autostart Mode
        left_frame = ctk.CTkFrame(controls_container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        
        ctk.CTkLabel(
            left_frame, 
            text="Autostart Mode:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.autostart_combobox = ctk.CTkComboBox(
            left_frame,
            values=["OFF", "Instant", "Delayed"],
            width=120,
            height=26,
            command=self.on_autostart_select,
            fg_color="#3a3a3a",
            dropdown_fg_color="#2a2a2a",
            dropdown_hover_color="#4a4a4a",
            button_color="#1f538d",
            button_hover_color="#14375e",
            border_color="#565b5e",
            text_color="white",
            dropdown_text_color="white"
        )
        self.autostart_combobox.set(self.config_manager.load_setting("autostart_mode", "OFF"))
        self.autostart_combobox.pack(anchor="w", pady=(2, 0))

        # Right side - Toggle switches
        right_frame = ctk.CTkFrame(controls_container, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True)

        # RPM Indicator
        self.rpm_var = ctk.BooleanVar(value=self.config_manager.load_setting("rpm_indicator", "False") == "True")
        self.rpm_toggle = ctk.CTkSwitch(
            right_frame,
            text="RPM Indicator",
            variable=self.rpm_var,
            command=self.on_rpm_toggle
        )
        self.rpm_toggle.pack(anchor="w", pady=1)

        # Start When Powered
        self.start_var = ctk.BooleanVar(value=self.config_manager.load_setting("start_when_powered", "False") == "True")
        self.start_toggle = ctk.CTkSwitch(
            right_frame,
            text="Start When Powered",
            variable=self.start_var,
            command=self.on_start_toggle
        )
        self.start_toggle.pack(anchor="w", pady=1)

    def create_fan_speed_section(self):
        """Create ultra-compact fan speed section"""
        self.rpm_frame = ctk.CTkFrame(self.main_frame)
        self.rpm_frame.pack(fill="x", pady=(0, 4))
        
        # Section title
        title_label = ctk.CTkLabel(
            self.rpm_frame,
            text="Fan Speed Control",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(pady=(4, 2), padx=6, anchor="w")
        
        # Horizontal layout for fan speed controls
        fan_container = ctk.CTkFrame(self.rpm_frame, fg_color="transparent")
        fan_container.pack(fill="x", padx=6, pady=(0, 4))
        
        # Left side - RPM selection
        left_frame = ctk.CTkFrame(fan_container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        
        ctk.CTkLabel(
            left_frame, 
            text="Select Fan Speed:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
        self.rpm_combobox = ctk.CTkComboBox(
            left_frame,
            values=[str(rpm) for rpm in self.rpm_values],
            width=120,
            height=26,
            command=self.on_rpm_select,
            fg_color="#3a3a3a",
            dropdown_fg_color="#2a2a2a",
            dropdown_hover_color="#4a4a4a",
            button_color="#1f538d",
            button_hover_color="#14375e",
            border_color="#565b5e",
            text_color="white",
            dropdown_text_color="white"
        )
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.rpm_combobox.set(str(last_rpm))
        self.rpm_combobox.pack(anchor="w", pady=(2, 0))

        # Right side - Current RPM display
        right_frame = ctk.CTkFrame(fan_container, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True)
        
        self.rpm_display_label = ctk.CTkLabel(
            right_frame,
            text=f"Current: {last_rpm} RPM",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1f538d"
        )
        self.rpm_display_label.pack(anchor="center", pady=(8, 0))

    def create_smart_mode_section(self):
        """Create ultra-compact smart mode section"""
        self.smart_mode_frame = ctk.CTkFrame(self.main_frame)
        self.smart_mode_frame.pack(fill="x", pady=(0, 4))
        
        # Section title
        title_label = ctk.CTkLabel(
            self.smart_mode_frame,
            text="Smart Mode",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(pady=(4, 2), padx=6, anchor="w")
        
        # Smart mode container
        smart_container = ctk.CTkFrame(self.smart_mode_frame, fg_color="transparent")
        smart_container.pack(fill="x", padx=6, pady=(0, 4))
        
        # Top row - Smart mode toggle
        self.smart_mode_var = ctk.BooleanVar(value=self.smart_mode_manager.is_smart_mode_enabled())
        self.smart_mode_switch = ctk.CTkSwitch(
            smart_container,
            text="Enable Smart Mode (Auto-adjust based on CPU temp)",
            variable=self.smart_mode_var,
            command=self.on_smart_mode_toggle
        )
        self.smart_mode_switch.pack(anchor="w", pady=(0, 4))
        
        # Bottom row - Temperature info and config button
        bottom_row = ctk.CTkFrame(smart_container, fg_color="transparent")
        bottom_row.pack(fill="x")
        
        # Left side - Temperature display
        temp_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        temp_frame.pack(side="left", fill="both", expand=True)
        
        self.temp_label = ctk.CTkLabel(
            temp_frame,
            text="CPU Temperature: --°C",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#17a2b8"
        )
        self.temp_label.pack(anchor="w")
        
        self.smart_status_label = ctk.CTkLabel(
            temp_frame,
            text="Smart Mode: Off",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        self.smart_status_label.pack(anchor="w", pady=(1, 0))
        
        # Right side - Configure button
        config_button = ctk.CTkButton(
            bottom_row,
            text="Configure",
            command=self.open_smart_mode_config,
            width=100,
            height=24
        )
        config_button.pack(side="right", padx=(6, 0))

    def create_footer(self):
        """Create ultra-compact footer"""
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(2, 0))
        
        # Footer text
        footer_label = ctk.CTkLabel(
            footer_frame,
            text="BS2PRO Controller v2.3.0 • Made with ❤️",
            font=ctk.CTkFont(size=8),
            text_color="gray"
        )
        footer_label.pack(anchor="center")

    def update_device_status(self):
        vid, pid = self.controller.detect_bs2pro()
        if vid and pid:
            self.status_label.configure(
                text=f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", 
                text_color="#28a745"
            )
        else:
            self.status_label.configure(
                text="❌ BS2PRO not detected", 
                text_color="#dc3545"
            )
    
    def on_temperature_change(self, temperature):
        """Called when CPU temperature changes"""
        # Update temperature display
        self.temp_label.configure(text=f"CPU Temperature: {temperature:.1f}°C")
        
        # Auto-adjust RPM if smart mode is enabled
        if self.smart_mode_manager.is_smart_mode_enabled():
            self.auto_adjust_rpm(temperature)
    
    def auto_adjust_rpm(self, temperature):
        """Automatically adjust RPM based on temperature"""
        try:
            # Get target RPM and range info
            target_rpm = self.smart_mode_manager.get_rpm_for_temperature(temperature)
            range_info = self.smart_mode_manager.get_range_for_temperature(temperature)
            
            # Validate target RPM
            if target_rpm is None or target_rpm < 1000 or target_rpm > 3000:
                logging.warning(f"Invalid target RPM: {target_rpm}")
                self.smart_status_label.configure(
                    text="Smart Mode: Invalid RPM configuration",
                    text_color="#dc3545"
                )
                return
            
            # Check if RPM command exists
            if target_rpm not in self.rpm_commands:
                logging.warning(f"RPM command not found for {target_rpm}")
                self.smart_status_label.configure(
                    text="Smart Mode: RPM command not available",
                    text_color="#dc3545"
                )
                return
            
            # Only change RPM if it's different from current
            if target_rpm != self.current_rpm:
                self.current_rpm = target_rpm
                
                # Send command to device
                success = self.controller.send_command(self.rpm_commands[target_rpm], status_callback=self._create_status_callback())
                
                if success:
                    # Update combobox selection
                    self.rpm_combobox.set(str(target_rpm))
                    # Don't update RPM display here - let live monitoring handle it
                    
                    # Update smart status
                    if range_info:
                        self.smart_status_label.configure(
                            text=f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)",
                            text_color="#28a745"
                        )
                    else:
                        self.smart_status_label.configure(
                            text=f"Smart Mode: {target_rpm} RPM (Auto)",
                            text_color="#28a745"
                        )
                    
                    # Save setting
                    self.config_manager.save_setting("last_rpm", target_rpm)
                else:
                    self.smart_status_label.configure(
                        text="Smart Mode: Failed to adjust RPM",
                        text_color="#dc3545"
                    )
            else:
                # RPM is already correct, just update status
                if range_info:
                    self.smart_status_label.configure(
                        text=f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)",
                        text_color="#28a745"
                    )
                else:
                    self.smart_status_label.configure(
                        text=f"Smart Mode: {target_rpm} RPM (Auto)",
                        text_color="#28a745"
                    )
                    
        except Exception as e:
            logging.error(f"Error in auto RPM adjustment: {e}")
            self.smart_status_label.configure(
                text="Smart Mode: Error",
                text_color="#dc3545"
            )
    
    def on_smart_mode_toggle(self):
        """Handle smart mode toggle"""
        enabled = self.smart_mode_var.get()
        self.smart_mode_manager.set_enabled(enabled)
        
        if enabled:
            try:
                # Check if we have temperature ranges
                ranges = self.smart_mode_manager.get_temperature_ranges()
                if not ranges:
                    self.smart_status_label.configure(
                        text="Smart Mode: No temperature ranges configured",
                        text_color="#ffc107"
                    )
                    return
                
                # Get current temperature and adjust if needed
                current_temp = self.cpu_monitor.get_temperature()
                if current_temp <= 0:
                    self.smart_status_label.configure(
                        text="Smart Mode: On - Waiting for temperature data",
                        text_color="#17a2b8"
                    )
                    return
                
                self.smart_status_label.configure(
                    text="Smart Mode: On - Monitoring CPU temperature",
                    text_color="#28a745"
                )
                
                # Adjust RPM based on current temperature with a small delay
                self.root.after(100, lambda: self.auto_adjust_rpm(current_temp))
                
            except Exception as e:
                logging.error(f"Error enabling smart mode: {e}")
                self.smart_status_label.configure(
                    text="Smart Mode: Error - Check configuration",
                    text_color="#dc3545"
                )
        else:
            self.smart_status_label.configure(
                text="Smart Mode: Off",
                text_color="gray"
            )
            self.current_rpm = None
    
    def open_smart_mode_config(self):
        """Open smart mode configuration dialog"""
        self.create_smart_mode_config_dialog()
    
    def create_smart_mode_config_dialog(self):
        """Create smart mode configuration dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Smart Mode Configuration")
        dialog.geometry("600x450")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (450 // 2)
        dialog.geometry(f"600x450+{x}+{y}")
        
        # Make sure dialog is visible before grabbing focus
        dialog.lift()
        dialog.focus_force()
        
        # Use after() to ensure dialog is fully rendered before grabbing focus
        dialog.after(100, lambda: dialog.grab_set())
        
        # Auto-adjust size after content is loaded
        dialog.after(200, lambda: self.auto_adjust_dialog_size(dialog))
        
        # Main frame with compact padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Temperature Range Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 10))
        
        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text="Configure temperature ranges and their corresponding RPM values.\nRanges should not overlap and should be in ascending order.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        instructions.pack(pady=(0, 10))
        
        # Temperature ranges list
        ranges_frame = ctk.CTkScrollableFrame(main_frame, height=250)
        ranges_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Load current ranges
        ranges = self.smart_mode_manager.get_temperature_ranges()
        self.range_widgets = []
        
        for i, range_data in enumerate(ranges):
            self.create_range_widget(ranges_frame, i, range_data)
        
        # Add new range button
        add_button = ctk.CTkButton(
            main_frame,
            text="Add New Range",
            command=lambda: self.add_new_range(ranges_frame),
            width=120,
            height=28
        )
        add_button.pack(pady=(0, 8))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(8, 0))
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Configuration",
            command=lambda: self.save_smart_mode_config_simple(dialog),
            width=120,
            height=28
        )
        save_button.pack(side="left", padx=(0, 8))
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=120,
            height=28
        )
        cancel_button.pack(side="left")
    
    def create_range_widget(self, parent, index, range_data):
        """Create a temperature range widget"""
        range_frame = ctk.CTkFrame(parent)
        range_frame.pack(fill="x", pady=3)
        
        # Min temp
        min_label = ctk.CTkLabel(range_frame, text="Min:", width=40)
        min_label.pack(side="left", padx=(8, 3), pady=6)
        
        min_entry = ctk.CTkEntry(range_frame, width=70, placeholder_text="Min temp")
        min_entry.insert(0, str(range_data['min_temp']))
        min_entry.pack(side="left", padx=(0, 3), pady=6)
        
        # Max temp
        max_label = ctk.CTkLabel(range_frame, text="Max:", width=40)
        max_label.pack(side="left", padx=(8, 3), pady=6)
        
        max_entry = ctk.CTkEntry(range_frame, width=70, placeholder_text="Max temp")
        max_entry.insert(0, str(range_data['max_temp']))
        max_entry.pack(side="left", padx=(0, 3), pady=6)
        
        # RPM
        rpm_label = ctk.CTkLabel(range_frame, text="RPM:", width=40)
        rpm_label.pack(side="left", padx=(8, 3), pady=6)
        
        rpm_entry = ctk.CTkEntry(range_frame, width=70, placeholder_text="RPM")
        rpm_entry.insert(0, str(range_data['rpm']))
        rpm_entry.pack(side="left", padx=(0, 3), pady=6)
        
        # Description
        desc_entry = ctk.CTkEntry(range_frame, width=120, placeholder_text="Description")
        desc_entry.insert(0, range_data.get('description', ''))
        desc_entry.pack(side="left", padx=(8, 3), pady=6)
        
        # Remove button
        remove_button = ctk.CTkButton(
            range_frame,
            text="✕",
            command=lambda: self.remove_range_widget(parent, range_frame, index),
            width=35,
            height=26,
            fg_color="#dc3545",
            hover_color="#c82333",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        remove_button.pack(side="right", padx=(3, 8), pady=6)
        
        # Store widget references
        widget_data = {
            'frame': range_frame,
            'min_entry': min_entry,
            'max_entry': max_entry,
            'rpm_entry': rpm_entry,
            'desc_entry': desc_entry,
            'index': index
        }
        self.range_widgets.append(widget_data)
    
    def auto_adjust_dialog_size(self, dialog):
        """Automatically adjust dialog size based on content"""
        try:
            # Update the dialog to get accurate size requirements
            dialog.update_idletasks()
            
            # Get the required size
            req_width = dialog.winfo_reqwidth()
            req_height = dialog.winfo_reqheight()
            
            # Add some padding
            padding = 30
            new_width = max(600, req_width + padding)
            new_height = max(400, req_height + padding)
            
            # Get screen dimensions
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            
            # Ensure dialog doesn't exceed screen size
            new_width = min(new_width, screen_width - 100)
            new_height = min(new_height, screen_height - 100)
            
            # Center the dialog with new size
            x = (screen_width - new_width) // 2
            y = (screen_height - new_height) // 2
            
            # Apply new geometry
            dialog.geometry(f"{new_width}x{new_height}+{x}+{y}")
            
            logging.info(f"Dialog auto-adjusted to {new_width}x{new_height}")
            
        except Exception as e:
            logging.warning(f"Could not auto-adjust dialog size: {e}")
    
    def add_new_range(self, parent):
        """Add a new temperature range"""
        new_range = {
            'min_temp': 0,
            'max_temp': 10,
            'rpm': 1300,
            'description': 'New range'
        }
        self.create_range_widget(parent, len(self.range_widgets), new_range)
        
        # Auto-adjust dialog size after adding new range
        dialog = parent.winfo_toplevel()
        dialog.after(100, lambda: self.auto_adjust_dialog_size(dialog))
    
    def remove_range_widget(self, parent, widget_frame, index):
        """Remove a temperature range widget"""
        widget_frame.destroy()
        # Update indices for remaining widgets
        for widget in self.range_widgets:
            if widget['index'] > index:
                widget['index'] -= 1
        
        # Auto-adjust dialog size after removing range
        dialog = parent.winfo_toplevel()
        dialog.after(100, lambda: self.auto_adjust_dialog_size(dialog))
    
    def save_smart_mode_config_simple(self, dialog):
        """Save smart mode configuration using a simpler approach"""
        try:
            # Clear existing ranges
            self.smart_mode_manager.temperature_ranges = []
            
            # Try to collect data from widgets first
            ranges_data = []
            for i, widget in enumerate(self.range_widgets):
                try:
                    # Use a more robust method to get values
                    min_temp_str = widget['min_entry']._entry.get()
                    max_temp_str = widget['max_entry']._entry.get()
                    rpm_str = widget['rpm_entry']._entry.get()
                    description = widget['desc_entry']._entry.get()
                    
                    # Convert to numbers
                    min_temp = float(min_temp_str) if min_temp_str else 0
                    max_temp = float(max_temp_str) if max_temp_str else 50
                    rpm = int(rpm_str) if rpm_str else 1300
                    
                    # Validate range
                    if min_temp >= max_temp:
                        messagebox.showerror("Error", f"Range {i+1}: Min temperature must be less than max temperature")
                        return
                    
                    if rpm < 1000 or rpm > 3000:
                        messagebox.showerror("Error", f"Range {i+1}: RPM must be between 1000 and 3000")
                        return
                    
                    ranges_data.append({
                        'min_temp': min_temp,
                        'max_temp': max_temp,
                        'rpm': rpm,
                        'description': description if description else f"Range {i+1}"
                    })
                    
                except (ValueError, AttributeError) as e:
                    logging.warning(f"Error reading widget {i}: {e}")
                    # Skip invalid widgets
                    continue
            
            # If no valid ranges found, use defaults
            if not ranges_data:
                logging.info("No valid custom ranges found, using defaults")
                default_ranges = [
                    {"min_temp": 0, "max_temp": 50, "rpm": 1300, "description": "Cool"},
                    {"min_temp": 50, "max_temp": 60, "rpm": 1700, "description": "Normal"},
                    {"min_temp": 60, "max_temp": 70, "rpm": 1900, "description": "Warm"},
                    {"min_temp": 70, "max_temp": 80, "rpm": 2100, "description": "Hot"},
                    {"min_temp": 80, "max_temp": 100, "rpm": 2700, "description": "Critical"}
                ]
                ranges_data = default_ranges
                message_text = "Smart mode configuration saved with default ranges!"
            else:
                message_text = f"Smart mode configuration saved with {len(ranges_data)} custom ranges!"
            
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
            
            # Close dialog
            dialog.destroy()
            
            # Show success message
            messagebox.showinfo("Success", message_text)
            
        except Exception as e:
            logging.error(f"Error saving smart mode config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    
    
    def on_closing(self):
        """Handle window closing event (X button)"""
        if self.minimize_to_tray and self.tray_manager and self.tray_manager.is_running:
            # Instead of closing, minimize to tray
            self._minimize_to_tray()
        else:
            # Actually close the application
            self.cleanup()
            self.root.destroy()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.cpu_monitor:
            self.cpu_monitor.stop_monitoring()
        if self.controller:
            self.controller.stop_rpm_monitoring()
        if self.tray_manager:
            self.tray_manager.stop()
