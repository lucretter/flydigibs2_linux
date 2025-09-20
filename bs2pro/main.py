import os
import logging
from logging.handlers import RotatingFileHandler

# Entry point: wire up controller, config, and GUI
from controller import BS2ProController
from config import ConfigManager
from gui import BS2ProGUI
from udev_manager import UdevRulesManager

RPM_COMMANDS = {
    1300: "5aa52605001405440000000000000000000000000000000000000000000000",
    1700: "5aa5260500a406d50000000000000000000000000000000000000000000000",
    1900: "5aa52605006c079e0000000000000000000000000000000000000000000000",
    2100: "5aa52605013408680000000000000000000000000000000000000000000000",
    2400: "5aa52605016009950000000000000000000000000000000000000000000000",
    2700: "5aa52605018c0ac20000000000000000000000000000000000000000000000"
}

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
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")
LOG_FILE = os.path.join(CONFIG_DIR, "bs2pro.log")

# Set up log rotation: 1MB per file, keep 3 backups
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
log_handler.setFormatter(log_formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(log_handler)

DEFAULT_SETTINGS = {
    "last_rpm": "1300",
    "rpm_indicator": "True",
    "start_when_powered": "True",
    "autostart_mode": "Instant",
    "udev_rules_installed": "False"
}

def check_and_prompt_udev_rules(controller, config_manager):
    """Check if udev rules are needed and prompt user if necessary"""
    # Import tkinter here to avoid issues with CLI mode
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        logging.warning("tkinter not available, skipping udev rules prompt")
        return
    
    # Detect device to get vendor and product IDs
    vid, pid = controller.detect_bs2pro()
    
    if vid is None or pid is None:
        logging.warning("BS2PRO device not detected, skipping udev check")
        return
    
    # Check if udev rules are already marked as installed in config
    udev_installed = config_manager.load_setting("udev_rules_installed", "False") == "True"
    
    if udev_installed:
        logging.info("udev rules already marked as installed in config")
        return
    
    # Create udev manager and check if rules exist
    udev_manager = UdevRulesManager(vid, pid)
    
    if not udev_manager.udev_rules_exist():
        # Rules don't exist, prompt user to install them
        logging.info("udev rules not found, prompting user for installation")
        
        # Create a temporary root window for the dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Prompt user
        udev_manager.prompt_for_udev_installation(root)
        
        # Mark as installed in config (even if user declined, to avoid repeated prompts)
        config_manager.save_setting("udev_rules_installed", "True")
        
        root.destroy()

def handle_cli_args(controller, config_manager):
    import sys
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg.startswith("rpm_"):
            try:
                rpm_value = int(arg.split("_")[1])
                if rpm_value in RPM_COMMANDS:
                    controller.send_command(RPM_COMMANDS[rpm_value])
                    config_manager.save_setting("last_rpm", rpm_value)
                    print(f"✅ RPM set to {rpm_value}")
                else:
                    print(f"❌ Unsupported RPM value: {rpm_value}")
            except ValueError:
                print("❌ Invalid RPM format. Use: rpm_1300, rpm_2700, etc.")
        elif arg in COMMANDS:
            cmd = COMMANDS[arg]
            if isinstance(cmd, list):
                for c in cmd:
                    controller.send_command(c)
            else:
                controller.send_command(cmd)
            print(f"✅ Command '{arg}' sent.")
        else:
            print(f"❌ Unknown command: {arg}")
        sys.exit(0)

if __name__ == "__main__":
    controller = BS2ProController()
    config_manager = ConfigManager(CONFIG_FILE, DEFAULT_SETTINGS)
    
    # Initialize settings if this is the first run
    config_manager.initialize_settings()
    
    # Handle CLI args first (before any GUI stuff)
    handle_cli_args(controller, config_manager)
    
    # Check and prompt for udev rules if needed (only in GUI mode)
    check_and_prompt_udev_rules(controller, config_manager)
    
    # Start the GUI
    BS2ProGUI(controller, config_manager, RPM_COMMANDS, COMMANDS, DEFAULT_SETTINGS)