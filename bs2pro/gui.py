import customtkinter as ctk
import os
import sys
import logging
import tkinter as tk
from tkinter import messagebox
from cpu_monitor import CPUMonitor
from smart_mode import SmartModeManager
from tray_manager import TrayManager

class BS2ProGUI:
    def __init__(self, controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
        self.controller = controller
        self.config_manager = config_manager
        self.rpm_commands = rpm_commands
        self.commands = commands
        self.default_settings = default_settings
        
        # Initialize smart mode and CPU monitoring
        self.cpu_monitor = CPUMonitor()
        self.smart_mode_manager = SmartModeManager()
        self.tray_manager = None
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # "light" or "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("BS2PRO Controller")
        
        # Set minimum size and auto-detect optimal size
        self.root.minsize(500, 700)
        self.root.geometry("600x750")
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
        
        # Initialize system tray
        self.tray_manager = TrayManager(self.root, self)
        self.tray_manager.start_tray()
        
        # Setup CPU monitoring callbacks
        self.cpu_monitor.add_callback(self.on_temperature_change)
        
        # Start CPU monitoring
        self.cpu_monitor.start_monitoring()
        
        # Center window after widgets are created
        self.root.after(100, self.center_window)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.mainloop()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        
        # Get the actual window size after widgets are rendered
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        
        # Ensure minimum size
        width = max(width, 600)
        height = max(height, 750)
        
        # Calculate center position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Apply the geometry
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def on_rpm_select(self, selected_value=None):
        # CustomTkinter passes the selected value directly
        if selected_value is None:
            rpm = int(self.rpm_combobox.get())
        else:
            rpm = int(selected_value)
        
        def status_callback(msg, style):
            self.device_status_label.configure(text=msg, text_color=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(self.rpm_commands[rpm], status_callback=status_callback)
        self.rpm_display_label.configure(text=f"Current Speed: {rpm} RPM")
        self.config_manager.save_setting("last_rpm", rpm)
        if not success:
            self.rpm_display_label.configure(text=f"Failed to set RPM: {rpm}")

    def on_rpm_toggle(self):
        state = self.rpm_var.get()
        cmd = self.commands["rpm_on"] if state else self.commands["rpm_off"]
        def status_callback(msg, style):
            self.device_status_label.configure(text=msg, text_color=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(cmd, status_callback=status_callback)
        self.config_manager.save_setting("rpm_indicator", str(state))
        if not success:
            self.device_status_label.configure(text="Failed to toggle RPM indicator", text_color="#dc3545")

    def on_autostart_select(self, selected_value=None):
        # CustomTkinter passes the selected value directly
        if selected_value is None:
            mode = self.autostart_combobox.get()
        else:
            mode = selected_value
        
        cmd = self.commands[f"autostart_{mode.lower()}"]
        def status_callback(msg, style):
            self.device_status_label.configure(text=msg, text_color=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(cmd, status_callback=status_callback)
        self.config_manager.save_setting("autostart_mode", mode)
        if not success:
            self.device_status_label.configure(text="Failed to set autostart mode", text_color="#dc3545")

    def on_start_toggle(self):
        state = self.start_var.get()
        success = True
        def status_callback(msg, style):
            self.device_status_label.configure(text=msg, text_color=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        if state:
            success = self.controller.send_command(self.commands["startwhenpowered_on"], status_callback=status_callback)
        else:
            for cmd in self.commands["startwhenpowered_off"]:
                if not self.controller.send_command(cmd, status_callback=status_callback):
                    success = False
        self.config_manager.save_setting("start_when_powered", str(state))
        if not success:
            self.device_status_label.configure(text="Failed to toggle start when powered", text_color="#dc3545")

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

    def setup_widgets(self):
        # Main container with better spacing
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
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
        """Create modern header with title"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="BS2PRO Controller",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")

    def create_device_status(self):
        """Create device status section"""
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.pack(fill="x", pady=(0, 25))
        
        # Status label
        self.device_status_label = ctk.CTkLabel(
            status_frame,
            text="Detecting BS2PRO...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffc107"
        )
        self.device_status_label.pack(pady=20)

    def create_controls_section(self):
        """Create controls section"""
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(fill="x", pady=(0, 25))
        
        # Section title
        title_label = ctk.CTkLabel(
            self.controls_frame,
            text="Device Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10), padx=20, anchor="w")

        # Autostart Mode
        autostart_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        autostart_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            autostart_frame, 
            text="Autostart Mode:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            autostart_frame,
            text="Configure how the device starts up",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w", pady=(2, 8))
        
        self.autostart_combobox = ctk.CTkComboBox(
            autostart_frame,
            values=["OFF", "Instant", "Delayed"],
            width=150,
            height=35,
            command=self.on_autostart_select
        )
        self.autostart_combobox.set(self.config_manager.load_setting("autostart_mode", "OFF"))
        self.autostart_combobox.pack(anchor="w")

        # Toggle switches section
        toggles_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=20, pady=(10, 20))

        # RPM Indicator
        self.rpm_var = ctk.BooleanVar(value=self.config_manager.load_setting("rpm_indicator", "False") == "True")
        self.rpm_toggle = ctk.CTkSwitch(
            toggles_frame,
            text="RPM Indicator",
            variable=self.rpm_var,
            command=self.on_rpm_toggle
        )
        self.rpm_toggle.pack(anchor="w", pady=8)

        # Start When Powered
        self.start_var = ctk.BooleanVar(value=self.config_manager.load_setting("start_when_powered", "False") == "True")
        self.start_toggle = ctk.CTkSwitch(
            toggles_frame,
            text="Start When Powered",
            variable=self.start_var,
            command=self.on_start_toggle
        )
        self.start_toggle.pack(anchor="w", pady=8)

    def create_fan_speed_section(self):
        """Create fan speed section"""
        self.rpm_frame = ctk.CTkFrame(self.main_frame)
        self.rpm_frame.pack(fill="x", pady=(0, 25))
        
        # Section title
        title_label = ctk.CTkLabel(
            self.rpm_frame,
            text="Fan Speed Control",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        # RPM selection
        rpm_select_frame = ctk.CTkFrame(self.rpm_frame, fg_color="transparent")
        rpm_select_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            rpm_select_frame, 
            text="Select Fan Speed:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            rpm_select_frame,
            text="Choose the RPM for optimal cooling performance",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w", pady=(2, 8))
        
        self.rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
        self.rpm_combobox = ctk.CTkComboBox(
            rpm_select_frame,
            values=[str(rpm) for rpm in self.rpm_values],
            width=150,
            height=35,
            command=self.on_rpm_select
        )
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.rpm_combobox.set(str(last_rpm))
        self.rpm_combobox.pack(anchor="w")

        # Current RPM display
        self.rpm_display_label = ctk.CTkLabel(
            self.rpm_frame,
            text=f"Current Speed: {last_rpm} RPM",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f538d"
        )
        self.rpm_display_label.pack(pady=(15, 20))

    def create_smart_mode_section(self):
        """Create smart mode section"""
        self.smart_mode_frame = ctk.CTkFrame(self.main_frame)
        self.smart_mode_frame.pack(fill="x", pady=(0, 25))
        
        # Section title
        title_label = ctk.CTkLabel(
            self.smart_mode_frame,
            text="Smart Mode",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Smart mode toggle
        smart_mode_frame = ctk.CTkFrame(self.smart_mode_frame, fg_color="transparent")
        smart_mode_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.smart_mode_var = ctk.BooleanVar(value=self.smart_mode_manager.is_smart_mode_enabled())
        self.smart_mode_switch = ctk.CTkSwitch(
            smart_mode_frame,
            text="Enable Smart Mode (Auto-adjust RPM based on CPU temperature)",
            variable=self.smart_mode_var,
            command=self.on_smart_mode_toggle
        )
        self.smart_mode_switch.pack(anchor="w", pady=8)
        
        # Temperature display
        temp_frame = ctk.CTkFrame(self.smart_mode_frame, fg_color="transparent")
        temp_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.temp_label = ctk.CTkLabel(
            temp_frame,
            text="CPU Temperature: --°C",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#17a2b8"
        )
        self.temp_label.pack(anchor="w")
        
        self.smart_status_label = ctk.CTkLabel(
            temp_frame,
            text="Smart Mode: Off",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.smart_status_label.pack(anchor="w", pady=(2, 0))
        
        # Configure button
        config_button = ctk.CTkButton(
            temp_frame,
            text="Configure Temperature Ranges",
            command=self.open_smart_mode_config,
            width=200,
            height=30
        )
        config_button.pack(anchor="w", pady=(10, 0))

    def create_footer(self):
        """Create modern footer"""
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(20, 10))
        
        # Footer text
        footer_label = ctk.CTkLabel(
            footer_frame,
            text="BS2PRO Controller v1.1.4 • Made with ❤️",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        footer_label.pack(anchor="center")

    def update_device_status(self):
        vid, pid = self.controller.detect_bs2pro()
        if vid and pid:
            self.device_status_label.configure(
                text=f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", 
                text_color="#28a745"
            )
        else:
            self.device_status_label.configure(
                text="❌ BS2PRO not detected", 
                text_color="#dc3545"
            )
    
    def on_temperature_change(self, temperature):
        """Called when CPU temperature changes"""
        # Update temperature display
        self.temp_label.configure(text=f"CPU Temperature: {temperature:.1f}°C")
        
        # Update tray tooltip
        if self.tray_manager:
            self.tray_manager.update_tray_tooltip(f"BS2PRO Controller - CPU: {temperature:.1f}°C")
        
        # Auto-adjust RPM if smart mode is enabled
        if self.smart_mode_manager.is_smart_mode_enabled():
            self.auto_adjust_rpm(temperature)
    
    def auto_adjust_rpm(self, temperature):
        """Automatically adjust RPM based on temperature"""
        try:
            target_rpm = self.smart_mode_manager.get_rpm_for_temperature(temperature)
            range_info = self.smart_mode_manager.get_range_for_temperature(temperature)
            
            # Only change RPM if it's different from current
            if target_rpm != self.current_rpm:
                self.current_rpm = target_rpm
                
                # Send command to device
                def status_callback(msg, style):
                    self.device_status_label.configure(text=msg, text_color=self.get_color(style))
                    self.root.after(2000, self.reset_status_message)
                
                success = self.controller.send_command(self.rpm_commands[target_rpm], status_callback=status_callback)
                
                if success:
                    # Update display
                    self.rpm_combobox.set(str(target_rpm))
                    self.rpm_display_label.configure(text=f"Current Speed: {target_rpm} RPM (Auto)")
                    
                    # Update smart status
                    if range_info:
                        self.smart_status_label.configure(
                            text=f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)",
                            text_color="#28a745"
                        )
                    
                    # Save setting
                    self.config_manager.save_setting("last_rpm", target_rpm)
                else:
                    self.smart_status_label.configure(
                        text="Smart Mode: Failed to adjust RPM",
                        text_color="#dc3545"
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
            self.smart_status_label.configure(
                text="Smart Mode: On - Monitoring CPU temperature",
                text_color="#28a745"
            )
            # Get current temperature and adjust if needed
            current_temp = self.cpu_monitor.get_temperature()
            if current_temp > 0:
                self.auto_adjust_rpm(current_temp)
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
        dialog.geometry("600x500")
        dialog.transient(self.root)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Make sure dialog is visible before grabbing focus
        dialog.lift()
        dialog.focus_force()
        
        # Use after() to ensure dialog is fully rendered before grabbing focus
        dialog.after(100, lambda: dialog.grab_set())
        
        # Initialize range data storage
        self.range_data_storage = []
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Temperature Range Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text="Configure temperature ranges and their corresponding RPM values.\nRanges should not overlap and should be in ascending order.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        instructions.pack(pady=(0, 20))
        
        # Temperature ranges list
        ranges_frame = ctk.CTkScrollableFrame(main_frame, height=250)
        ranges_frame.pack(fill="both", expand=True, pady=(0, 20))
        
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
            width=150
        )
        add_button.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Configuration",
            command=lambda: self.save_smart_mode_config_simple(dialog),
            width=150
        )
        save_button.pack(side="left", padx=(0, 10))
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=150
        )
        cancel_button.pack(side="left")
    
    def create_range_widget(self, parent, index, range_data):
        """Create a temperature range widget"""
        range_frame = ctk.CTkFrame(parent)
        range_frame.pack(fill="x", pady=5)
        
        # Min temp
        min_label = ctk.CTkLabel(range_frame, text="Min:", width=50)
        min_label.pack(side="left", padx=(10, 5), pady=10)
        
        min_entry = ctk.CTkEntry(range_frame, width=80, placeholder_text="Min temp")
        min_entry.insert(0, str(range_data['min_temp']))
        min_entry.pack(side="left", padx=(0, 5), pady=10)
        
        # Max temp
        max_label = ctk.CTkLabel(range_frame, text="Max:", width=50)
        max_label.pack(side="left", padx=(10, 5), pady=10)
        
        max_entry = ctk.CTkEntry(range_frame, width=80, placeholder_text="Max temp")
        max_entry.insert(0, str(range_data['max_temp']))
        max_entry.pack(side="left", padx=(0, 5), pady=10)
        
        # RPM
        rpm_label = ctk.CTkLabel(range_frame, text="RPM:", width=50)
        rpm_label.pack(side="left", padx=(10, 5), pady=10)
        
        rpm_entry = ctk.CTkEntry(range_frame, width=80, placeholder_text="RPM")
        rpm_entry.insert(0, str(range_data['rpm']))
        rpm_entry.pack(side="left", padx=(0, 5), pady=10)
        
        # Description
        desc_entry = ctk.CTkEntry(range_frame, width=150, placeholder_text="Description")
        desc_entry.insert(0, range_data.get('description', ''))
        desc_entry.pack(side="left", padx=(10, 5), pady=10)
        
        # Remove button
        remove_button = ctk.CTkButton(
            range_frame,
            text="Remove",
            command=lambda: self.remove_range_widget(parent, range_frame, index),
            width=80,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        remove_button.pack(side="right", padx=(5, 10), pady=10)
        
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
    
    def add_new_range(self, parent):
        """Add a new temperature range"""
        new_range = {
            'min_temp': 0,
            'max_temp': 10,
            'rpm': 1300,
            'description': 'New range'
        }
        self.create_range_widget(parent, len(self.range_widgets), new_range)
    
    def remove_range_widget(self, parent, widget_frame, index):
        """Remove a temperature range widget"""
        widget_frame.destroy()
        # Update indices for remaining widgets
        for widget in self.range_widgets:
            if widget['index'] > index:
                widget['index'] -= 1
    
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
    
    def save_smart_mode_config(self, dialog):
        """Save smart mode configuration"""
        try:
            # Clear existing ranges
            self.smart_mode_manager.temperature_ranges = []
            
            # Collect data from widgets before destroying dialog
            ranges_data = []
            for i, widget in enumerate(self.range_widgets):
                try:
                    # Check if widget still exists before accessing
                    if not widget['min_entry'].winfo_exists():
                        logging.warning(f"Widget {i} no longer exists, skipping")
                        continue
                    
                    min_temp = float(widget['min_entry'].get())
                    max_temp = float(widget['max_entry'].get())
                    rpm = int(widget['rpm_entry'].get())
                    description = widget['desc_entry'].get()
                    
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
                        'description': description
                    })
                except tk.TclError as tcl_err:
                    logging.warning(f"TclError accessing widget {i}: {tcl_err}")
                    continue
                except ValueError as ve:
                    messagebox.showerror("Error", f"Range {i+1}: Invalid value - {ve}")
                    return
                except Exception as e:
                    logging.warning(f"Error accessing widget {i}: {e}")
                    continue
            
            # Check if we have any valid ranges
            if not ranges_data:
                messagebox.showerror("Error", "No valid temperature ranges found. Please add at least one range.")
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
            
            # Close dialog
            dialog.destroy()
            
            # Show success message
            messagebox.showinfo("Success", "Smart mode configuration saved!")
            
        except Exception as e:
            logging.error(f"Error saving smart mode config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def toggle_smart_mode(self):
        """Toggle smart mode (for tray menu)"""
        self.smart_mode_var.set(not self.smart_mode_var.get())
        self.on_smart_mode_toggle()
    
    def on_closing(self):
        """Handle window closing event"""
        if self.tray_manager and self.tray_manager.tray_available:
            # Hide to system tray instead of closing
            self.tray_manager.hide_window()
        else:
            # Close normally
            self.cleanup()
            self.root.destroy()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.cpu_monitor:
            self.cpu_monitor.stop_monitoring()
        if self.tray_manager:
            self.tray_manager.stop_tray()
