import tkinter as tk
msgcat_path = os.path.join(os.path.dirname(__file__), 'tcl', 'msgcat.tcl')
if os.path.exists(msgcat_path):
    tkinter.Tk().tk.eval(f'source "{msgcat_path}"')
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import os
import logging

class BS2ProGUI:
    def __init__(self, controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
        self.controller = controller
        self.config_manager = config_manager
        self.rpm_commands = rpm_commands
        self.commands = commands
        self.default_settings = default_settings
        self.root = tb.Window(themename="darkly")
        self.root.title("BS2PRO Controller")
        self.root.geometry("450x450")
        self.root.resizable(True, True)
        
        # Set window icon if provided - CORRECTLY PLACED INSIDE __init__
        if icon_path and os.path.exists(icon_path):
            try:
                self.icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, self.icon)
            except Exception as e:
                logging.warning(f"Could not load icon: {e}")
        
        self.setup_styles()
        self.setup_widgets()
        self.update_device_status()
        self.root.mainloop()

    def on_rpm_select(self, event=None):
        rpm = int(self.rpm_combobox.get())
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, bootstyle=style)
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(self.rpm_commands[rpm], status_callback=status_callback)
        self.rpm_display_label.config(text=f"Fan Speed: {rpm} RPM")
        self.config_manager.save_setting("last_rpm", rpm)
        if not success:
            self.rpm_display_label.config(text=f"Failed to set RPM: {rpm}")

    def on_rpm_toggle(self):
        state = self.rpm_var.get()
        cmd = self.commands["rpm_on"] if state else self.commands["rpm_off"]
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, bootstyle=style)
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(cmd, status_callback=status_callback)
        self.config_manager.save_setting("rpm_indicator", str(state))
        if not success:
            self.device_status_label.config(text="Failed to toggle RPM indicator", bootstyle="danger")

    def on_autostart_select(self, event=None):
        mode = self.autostart_combobox.get()
        cmd = self.commands[f"autostart_{mode.lower()}"]
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, bootstyle=style)
            self.root.after(2000, self.reset_status_message)
        success = self.controller.send_command(cmd, status_callback=status_callback)
        self.config_manager.save_setting("autostart_mode", mode)
        if not success:
            self.device_status_label.config(text="Failed to set autostart mode", bootstyle="danger")

    def on_start_toggle(self):
        state = self.start_var.get()
        success = True
        def status_callback(msg, style):
            self.device_status_label.config(text=msg, bootstyle=style)
            self.root.after(2000, self.reset_status_message)
        if state:
            success = self.controller.send_command(self.commands["startwhenpowered_on"], status_callback=status_callback)
        else:
            for cmd in self.commands["startwhenpowered_off"]:
                if not self.controller.send_command(cmd, status_callback=status_callback):
                    success = False
        self.config_manager.save_setting("start_when_powered", str(state))
        if not success:
            self.device_status_label.config(text="Failed to toggle start when powered", bootstyle="danger")

    def reset_status_message(self):
        self.update_device_status()
        
    def setup_styles(self):
        self.root.style.configure("TLabel", font=("Segoe UI", 13))
        self.root.style.configure("TButton", font=("Segoe UI", 13))
        self.root.style.configure("TCheckbutton", font=("Segoe UI", 13))
        self.root.style.configure("TCombobox", font=("Segoe UI", 13))
        self.root.style.configure("TLabelframe", font=("Segoe UI", 13, "bold"))

    def setup_widgets(self):
        self.main_frame = tb.Frame(self.root, padding=10)
        self.main_frame.pack(fill="both", expand=True)
        self.device_status_label = tb.Label(self.main_frame, text="Detecting BS2PRO...", bootstyle="warning")
        self.device_status_label.pack(pady=(0, 10))

        self.controls_frame = tb.LabelFrame(self.main_frame, text="Controls", padding=10, bootstyle="secondary")
        self.controls_frame.pack(fill="x", pady=(0, 10))

        # Autostart Mode Combobox
        tb.Label(self.controls_frame, text="Autostart Mode:", bootstyle="light").pack(pady=(10, 2))
        self.autostart_combobox = tb.Combobox(
            self.controls_frame,
            values=["OFF", "Instant", "Delayed"],
            state="readonly",
            bootstyle="info"
        )
        self.autostart_combobox.set(self.config_manager.load_setting("autostart_mode", "OFF"))
        self.autostart_combobox.pack(pady=5)
        self.autostart_combobox.bind("<<ComboboxSelected>>", self.on_autostart_select)

        # RPM Indicator Checkbutton
        self.rpm_var = tk.BooleanVar(value=self.config_manager.load_setting("rpm_indicator", "False") == "True")
        self.rpm_toggle = tb.Checkbutton(
            self.controls_frame,
            text="RPM Indicator",
            variable=self.rpm_var,
            command=self.on_rpm_toggle,
            bootstyle="success"
        )
        self.rpm_toggle.pack(fill="x", pady=8)

        # Start When Powered Checkbutton
        self.start_var = tk.BooleanVar(value=self.config_manager.load_setting("start_when_powered", "False") == "True")
        self.start_toggle = tb.Checkbutton(
            self.controls_frame,
            text="Start When Powered",
            variable=self.start_var,
            command=self.on_start_toggle,
            bootstyle="danger"
        )
        self.start_toggle.pack(fill="x", pady=8)

        # Fan Speed Frame and Combobox
        self.rpm_frame = tb.LabelFrame(self.main_frame, text="Fan Speed", padding=10, bootstyle="secondary")
        self.rpm_frame.pack(fill="x", pady=(0, 10))
        tb.Label(self.rpm_frame, text="Select RPM:", bootstyle="light").pack(pady=(0, 5))
        self.rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
        self.rpm_combobox = tb.Combobox(
            self.rpm_frame,
            values=self.rpm_values,
            state="readonly",
            width=10,
            bootstyle="primary"
        )
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.rpm_combobox.set(last_rpm)
        self.rpm_combobox.pack(pady=5)
        self.rpm_combobox.bind("<<ComboboxSelected>>", self.on_rpm_select)

        self.rpm_display_label = tb.Label(
            self.rpm_frame,
            text=f"Fan Speed: {last_rpm} RPM",
            font=("Segoe UI", 10, "bold"),
            bootstyle="light"
        )
        self.rpm_display_label.pack(pady=15)

    def update_device_status(self):
        vid, pid = self.controller.detect_bs2pro()
        if vid and pid:
            self.device_status_label.config(text=f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", bootstyle="success")
        else:
            self.device_status_label.config(text="❌ BS2PRO not detected", bootstyle="danger")