import tkinter as tk
from tkinter import ttk
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
        
        # Create main window with modern styling
        self.root = tk.Tk()
        self.root.title("BS2PRO Controller")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        self.root.configure(bg="#f8f9fa")
        
        # Set window icon if provided
        if icon_path and os.path.exists(icon_path):
            try:
                self.icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, self.icon)
            except Exception as e:
                logging.warning(f"Could not load icon: {e}")
        
        # Configure modern styles
        self.setup_modern_styles()
        self.setup_widgets()
        self.update_device_status()
        self.root.mainloop()

    def on_rpm_select(self, event=None):
        rpm = int(self.rpm_combobox.get())
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, foreground=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(self.rpm_commands[rpm], status_callback=status_callback)
        self.rpm_display_label.config(text=f"Current Speed: {rpm} RPM")
        self.config_manager.save_setting("last_rpm", rpm)
        if not success:
            self.rpm_display_label.config(text=f"Failed to set RPM: {rpm}")

    def on_rpm_toggle(self):
        state = self.rpm_var.get()
        cmd = self.commands["rpm_on"] if state else self.commands["rpm_off"]
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, foreground=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(cmd, status_callback=status_callback)
        self.config_manager.save_setting("rpm_indicator", str(state))
        if not success:
            self.device_status_label.config(text="Failed to toggle RPM indicator", foreground="red")

    def on_autostart_select(self, event=None):
        mode = self.autostart_combobox.get()
        cmd = self.commands[f"autostart_{mode.lower()}"]
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, foreground=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(cmd, status_callback=status_callback)
        self.config_manager.save_setting("autostart_mode", mode)
        if not success:
            self.device_status_label.config(text="Failed to set autostart mode", foreground="red")

    def on_start_toggle(self):
        state = self.start_var.get()
        success = True
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, foreground=self.get_color(style))
            self.root.after(2000, self.reset_status_message)
        if state:
            success = self.controller.send_command(self.commands["startwhenpowered_on"], status_callback=status_callback)
        else:
            for cmd in self.commands["startwhenpowered_off"]:
                if not self.controller.send_command(cmd, status_callback=status_callback):
                    success = False
        self.config_manager.save_setting("start_when_powered", str(state))
        if not success:
            self.device_status_label.config(text="Failed to toggle start when powered", foreground="red")

    def reset_status_message(self):
        self.update_device_status()
        
    def get_color(self, style):
        """Convert style to modern color"""
        color_map = {
            "success": self.colors['success'],
            "danger": self.colors['danger'], 
            "warning": self.colors['warning'],
            "info": self.colors['info'],
            "light": self.colors['text_muted']
        }
        return color_map.get(style, self.colors['text'])

    def setup_modern_styles(self):
        # Configure modern ttk styles
        style = ttk.Style()
        
        # Modern color scheme
        self.colors = {
            'primary': '#007bff',
            'secondary': '#6c757d', 
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'white': '#ffffff',
            'border': '#dee2e6',
            'text': '#212529',
            'text_muted': '#6c757d'
        }
        
        # Configure styles with modern colors and fonts
        style.configure("TLabel", 
                       font=("Segoe UI", 10),
                       background=self.colors['light'],
                       foreground=self.colors['text'])
        
        style.configure("TButton",
                       font=("Segoe UI", 10, "bold"),
                       padding=(20, 10))
        
        style.configure("TCheckbutton",
                       font=("Segoe UI", 10),
                       background=self.colors['light'],
                       foreground=self.colors['text'])
        
        style.configure("TCombobox",
                       font=("Segoe UI", 10),
                       padding=(8, 6))
        
        style.configure("TLabelframe",
                       font=("Segoe UI", 11, "bold"),
                       background=self.colors['light'],
                       foreground=self.colors['dark'],
                       borderwidth=1,
                       relief="solid")
        
        style.configure("TLabelframe.Label",
                       font=("Segoe UI", 11, "bold"),
                       background=self.colors['light'],
                       foreground=self.colors['primary'])
        
        # Configure button styles
        style.configure("Primary.TButton",
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map("Primary.TButton",
                 background=[('active', '#0056b3'),
                           ('pressed', '#004085')])
        
        # Configure success button
        style.configure("Success.TButton",
                       background=self.colors['success'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map("Success.TButton",
                 background=[('active', '#1e7e34'),
                           ('pressed', '#155724')])
        
        # Configure danger button
        style.configure("Danger.TButton",
                       background=self.colors['danger'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map("Danger.TButton",
                 background=[('active', '#c82333'),
                           ('pressed', '#bd2130')])

    def setup_widgets(self):
        # Main container with modern padding
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill="both", expand=True)
        
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
        """Create modern header with title and icon"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="BS2PRO Controller",
            font=("Segoe UI", 18, "bold"),
            foreground=self.colors['primary']
        )
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text="Advanced Gamepad Configuration",
            font=("Segoe UI", 10),
            foreground=self.colors['text_muted']
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

    def create_device_status(self):
        """Create device status section with modern styling"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill="x", pady=(0, 20))
        
        # Status container with border
        status_container = tk.Frame(status_frame, bg=self.colors['white'], relief="solid", bd=1)
        status_container.pack(fill="x", padx=5, pady=5)
        
        # Status label
        self.device_status_label = ttk.Label(
            status_container,
            text="Detecting BS2PRO...",
            font=("Segoe UI", 11, "bold"),
            foreground=self.colors['warning'],
            background=self.colors['white']
        )
        self.device_status_label.pack(pady=15, padx=15)

    def create_controls_section(self):
        """Create controls section with modern card layout"""
        self.controls_frame = ttk.LabelFrame(
            self.main_frame, 
            text="Device Settings", 
            padding=20
        )
        self.controls_frame.pack(fill="x", pady=(0, 20))

        # Autostart Mode
        autostart_frame = ttk.Frame(self.controls_frame)
        autostart_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            autostart_frame, 
            text="Autostart Mode:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        
        ttk.Label(
            autostart_frame,
            text="Configure how the device starts up",
            font=("Segoe UI", 9),
            foreground=self.colors['text_muted']
        ).pack(anchor="w", pady=(2, 8))
        
        self.autostart_combobox = ttk.Combobox(
            autostart_frame,
            values=["OFF", "Instant", "Delayed"],
            state="readonly",
            width=15
        )
        self.autostart_combobox.set(self.config_manager.load_setting("autostart_mode", "OFF"))
        self.autostart_combobox.pack(anchor="w")
        self.autostart_combobox.bind("<<ComboboxSelected>>", self.on_autostart_select)

        # Toggle switches section
        toggles_frame = ttk.Frame(self.controls_frame)
        toggles_frame.pack(fill="x", pady=(10, 0))

        # RPM Indicator
        self.rpm_var = tk.BooleanVar(value=self.config_manager.load_setting("rpm_indicator", "False") == "True")
        self.rpm_toggle = ttk.Checkbutton(
            toggles_frame,
            text="RPM Indicator",
            variable=self.rpm_var,
            command=self.on_rpm_toggle
        )
        self.rpm_toggle.pack(fill="x", pady=8)

        # Start When Powered
        self.start_var = tk.BooleanVar(value=self.config_manager.load_setting("start_when_powered", "False") == "True")
        self.start_toggle = ttk.Checkbutton(
            toggles_frame,
            text="Start When Powered",
            variable=self.start_var,
            command=self.on_start_toggle
        )
        self.start_toggle.pack(fill="x", pady=8)

    def create_fan_speed_section(self):
        """Create fan speed section with modern styling"""
        self.rpm_frame = ttk.LabelFrame(
            self.main_frame, 
            text="Fan Speed Control", 
            padding=20
        )
        self.rpm_frame.pack(fill="x", pady=(0, 20))
        
        # RPM selection
        rpm_select_frame = ttk.Frame(self.rpm_frame)
        rpm_select_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            rpm_select_frame, 
            text="Select Fan Speed:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        
        ttk.Label(
            rpm_select_frame,
            text="Choose the RPM for optimal cooling performance",
            font=("Segoe UI", 9),
            foreground=self.colors['text_muted']
        ).pack(anchor="w", pady=(2, 8))
        
        self.rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
        self.rpm_combobox = ttk.Combobox(
            rpm_select_frame,
            values=self.rpm_values,
            state="readonly",
            width=15
        )
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.rpm_combobox.set(last_rpm)
        self.rpm_combobox.pack(anchor="w")
        self.rpm_combobox.bind("<<ComboboxSelected>>", self.on_rpm_select)

        # Current RPM display
        self.rpm_display_label = ttk.Label(
            self.rpm_frame,
            text=f"Current Speed: {last_rpm} RPM",
            font=("Segoe UI", 12, "bold"),
            foreground=self.colors['primary']
        )
        self.rpm_display_label.pack(pady=(15, 0))

    def create_footer(self):
        """Create modern footer"""
        footer_frame = ttk.Frame(self.main_frame)
        footer_frame.pack(fill="x", pady=(10, 0))
        
        # Footer text
        footer_label = ttk.Label(
            footer_frame,
            text="BS2PRO Controller v1.1.4 • Made with ❤️",
            font=("Segoe UI", 8),
            foreground=self.colors['text_muted']
        )
        footer_label.pack(anchor="center")

    def update_device_status(self):
        vid, pid = self.controller.detect_bs2pro()
        if vid and pid:
            self.device_status_label.config(
                text=f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", 
                foreground=self.colors['success']
            )
        else:
            self.device_status_label.config(
                text="❌ BS2PRO not detected", 
                foreground=self.colors['danger']
            )
