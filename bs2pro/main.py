import tkinter as tk
from tkinter import ttk
import os
import sys
import logging
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from controller import BS2ProController
from config import ConfigManager
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import sys
import logging
RPM_COMMANDS = {
    1300: "5aa52605001405440000000000000000000000000000000000000000000000",
    1700: "5aa5260500a406d50000000000000000000000000000000000000000000000",
    1900: "5aa52605006c079e0000000000000000000000000000000000000000000000",
    2100: "5aa52605013408680000000000000000000000000000000000000000000000",
    2400: "5aa52605016009950000000000000000000000000000000000000000000000",
    2700: "5aa52605018c0ac20000000000000000000000000000000000000000000000"
}

# Command definitions
COMMANDS = {
    "rpm_on": "5aa54803014c00000000000000000000000000000000000000000000000000",
    "rpm_off": "5aa54803004b00000000000000000000000000000000000000000000000000",
    "autostart_off": "5aa50d03001000000000000000000000000000000000000000000000000000",
    "autostart_instant": "5aa50d03011100000000000000000000000000000000000000000000000000",
    "autostart_delayed": "5aa50d03021200000000000000000000000000000000000000000000000000",
    "startwhenpowered_on": "5aa50c03011000000000000000000000000000000000000000000000000000",
    "startwhenpowered_off": [
        "5aa50c03011000000000000000000000000000000000000000000000000000",
        "5aa50c03021100000000000000000000000000000000000000000000000000"
    ]
}


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "bs2pro_controller")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")
LOG_FILE = os.path.join(CONFIG_DIR, "bs2pro.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

DEFAULT_SETTINGS = {
    "last_rpm": "1300",
    "rpm_indicator": "True",
    "start_when_powered": "True",
    "autostart_mode": "Instant"
}



controller = BS2ProController()
config_manager = ConfigManager(CONFIG_FILE, DEFAULT_SETTINGS)
def send_command(hex_cmd):
    return controller.send_command(hex_cmd, status_callback=lambda msg, style: device_status_label.config(text=msg, bootstyle=style))

def save_setting(key, value):
    config_manager.save_setting(key, value)

def load_setting(key, default=None):
    return config_manager.load_setting(key, default)

def initialize_settings():
    return config_manager.initialize_settings()

def apply_initial_settings():
    rpm = int(DEFAULT_SETTINGS["last_rpm"])
    send_command(RPM_COMMANDS[rpm])
    if DEFAULT_SETTINGS["rpm_indicator"] == "True":
        send_command(COMMANDS["rpm_on"])
    else:
        send_command(COMMANDS["rpm_off"])
    if DEFAULT_SETTINGS["start_when_powered"] == "True":
        send_command(COMMANDS["startwhenpowered_on"])
    else:
        for cmd in COMMANDS["startwhenpowered_off"]:
            send_command(cmd)
    send_command(COMMANDS[f"autostart_{DEFAULT_SETTINGS['autostart_mode'].lower()}"])

def on_rpm_select(event=None):
    rpm = int(rpm_combobox.get())
    success = send_command(RPM_COMMANDS[rpm])
    rpm_display_label.config(text=f"Fan Speed: {rpm} RPM")
    save_setting("last_rpm", rpm)
    if not success:
        rpm_display_label.config(text=f"Failed to set RPM: {rpm}")

def on_rpm_toggle():
    state = rpm_var.get()
    cmd = COMMANDS["rpm_on"] if state else COMMANDS["rpm_off"]
    success = send_command(cmd)
    save_setting("rpm_indicator", str(state))
    if not success:
        device_status_label.config(text="Failed to toggle RPM indicator", bootstyle="danger")

def on_autostart_select(event=None):
    mode = autostart_combobox.get()
    cmd = COMMANDS[f"autostart_{mode.lower()}"]
    success = send_command(cmd)
    save_setting("autostart_mode", mode)
    if not success:
        device_status_label.config(text="Failed to set autostart mode", bootstyle="danger")

def on_start_toggle():
    state = start_var.get()
    success = True
    if state:
        success = send_command(COMMANDS["startwhenpowered_on"])
    else:
        for cmd in COMMANDS["startwhenpowered_off"]:
            if not send_command(cmd):
                success = False
    save_setting("start_when_powered", str(state))
    if not success:
        device_status_label.config(text="Failed to toggle start when powered", bootstyle="danger")

# Initialize settings
first_run = initialize_settings()
if first_run:
    apply_initial_settings()

def handle_cli_args():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg.startswith("rpm_"):
            try:
                rpm_value = int(arg.split("_")[1])
                if rpm_value in RPM_COMMANDS:
                    send_command(RPM_COMMANDS[rpm_value])
                    save_setting("last_rpm", rpm_value)
                    print(f"✅ RPM set to {rpm_value}")
                else:
                    print(f"❌ Unsupported RPM value: {rpm_value}")
            except ValueError:
                print("❌ Invalid RPM format. Use: rpm_1300, rpm_2700, etc.")
        elif arg in COMMANDS:
            cmd = COMMANDS[arg]
            if isinstance(cmd, list):
                for c in cmd:
                    send_command(c)
            else:
                send_command(cmd)
            print(f"✅ Command '{arg}' sent.")
        else:
            print(f"❌ Unknown command: {arg}")
        sys.exit(0)

handle_cli_args()

# GUI setup
root = tb.Window(themename="darkly")
root.title("BS2PRO Controller")
root.geometry("400x400")
root.resizable(True, True)

main_frame = tb.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

device_status_label = tb.Label(main_frame, text="Detecting BS2PRO...", bootstyle="warning")
device_status_label.pack(pady=(0, 10))

    # Use controller to check device status
def update_device_status():
    vid, pid = controller.detect_bs2pro()
    if vid and pid:
        device_status_label.config(text=f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", bootstyle="success")
    else:
        device_status_label.config(text="❌ BS2PRO not detected", bootstyle="danger")

update_device_status()

controls_frame = tb.LabelFrame(main_frame, text="Controls", padding=10, bootstyle="secondary")
controls_frame.pack(fill="x", pady=(0, 10))

canvas = tb.Canvas(controls_frame, height=180, highlightthickness=0)
scrollbar = tb.Scrollbar(controls_frame, orient="vertical", command=canvas.yview, bootstyle="dark")
scrollable_frame = tb.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

tb.Label(scrollable_frame, text="Autostart Mode:", bootstyle="light").pack(pady=(10, 2))
autostart_combobox = tb.Combobox(scrollable_frame, values=["OFF", "Instant", "Delayed"], state="readonly", bootstyle="info")
autostart_combobox.set(load_setting("autostart_mode", "OFF"))
autostart_combobox.pack(pady=5)
autostart_combobox.bind("<<ComboboxSelected>>", on_autostart_select)

rpm_var = tk.BooleanVar(value=load_setting("rpm_indicator", "False") == "True")
rpm_toggle = tb.Checkbutton(scrollable_frame, text="RPM Indicator", variable=rpm_var, command=on_rpm_toggle, bootstyle="success")
rpm_toggle.pack(fill="x", pady=8)

start_var = tk.BooleanVar(value=load_setting("start_when_powered", "False") == "True")
start_toggle = tb.Checkbutton(scrollable_frame, text="Start When Powered", variable=start_var, command=on_start_toggle, bootstyle="danger")
start_toggle.pack(fill="x", pady=8)

rpm_frame = tb.LabelFrame(main_frame, text="Fan Speed", padding=10, bootstyle="secondary")
rpm_frame.pack(fill="x", pady=(0, 10))

tb.Label(rpm_frame, text="Select RPM:", bootstyle="light").pack(pady=(0, 5))
rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
rpm_combobox = tb.Combobox(rpm_frame, values=rpm_values, state="readonly", width=10, bootstyle="primary")
rpm_combobox.pack(pady=5)

last_rpm = int(load_setting("last_rpm", 1900))
rpm_combobox.set(last_rpm)
rpm_combobox.bind("<<ComboboxSelected>>", on_rpm_select)

rpm_display_label = tb.Label(rpm_frame, text=f"Fan Speed: {last_rpm} RPM", font=("Segoe UI", 10, "bold"), bootstyle="light")
rpm_display_label.pack(pady=15)

root.mainloop()
