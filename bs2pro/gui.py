import customtkinter as ctk
import os
import sys
import logging

class BS2ProGUI:
    def __init__(self, controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
        self.controller = controller
        self.config_manager = config_manager
        self.rpm_commands = rpm_commands
        self.commands = commands
        self.default_settings = default_settings
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # "light" or "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("BS2PRO Controller")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        
        # Set window icon if provided
        if icon_path and os.path.exists(icon_path):
            try:
                self.icon = ctk.CTkImage(light_image=icon_path, dark_image=icon_path, size=(32, 32))
                self.root.iconbitmap(icon_path)
            except Exception as e:
                logging.warning(f"Could not load icon: {e}")
        
        self.setup_widgets()
        self.update_device_status()
        self.root.mainloop()

    def on_rpm_select(self, event=None):
        rpm = int(self.rpm_combobox.get())
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

    def on_autostart_select(self, event=None):
        mode = self.autostart_combobox.get()
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
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header()
        
        # Device status section
        self.create_device_status()
        
        # Controls section
        self.create_controls_section()
        
        # Fan speed section
        self.create_fan_speed_section()
        
        # Footer
        self.create_footer()

    def create_header(self):
        """Create modern header with title"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="BS2PRO Controller",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Advanced Gamepad Configuration",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def create_device_status(self):
        """Create device status section"""
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.pack(fill="x", pady=(0, 20))
        
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
        self.controls_frame.pack(fill="x", pady=(0, 20))
        
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
            height=35
        )
        self.autostart_combobox.set(self.config_manager.load_setting("autostart_mode", "OFF"))
        self.autostart_combobox.pack(anchor="w")
        self.autostart_combobox.bind("<<ComboboxSelected>>", self.on_autostart_select)

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
        self.rpm_frame.pack(fill="x", pady=(0, 20))
        
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
            height=35
        )
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.rpm_combobox.set(str(last_rpm))
        self.rpm_combobox.pack(anchor="w")
        self.rpm_combobox.bind("<<ComboboxSelected>>", self.on_rpm_select)

        # Current RPM display
        self.rpm_display_label = ctk.CTkLabel(
            self.rpm_frame,
            text=f"Current Speed: {last_rpm} RPM",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f538d"
        )
        self.rpm_display_label.pack(pady=(15, 20))

    def create_footer(self):
        """Create modern footer"""
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
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
