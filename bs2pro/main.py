# ...existing code...
import os
import logging
from logging.handlers import RotatingFileHandler
# ...existing code...

# Entry point: wire up controller, config, and GUI
from controller import BS2ProController
from config import ConfigManager
from gui import BS2ProGUI

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
    "autostart_mode": "Instant"
}

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
    handle_cli_args(controller, config_manager)
    BS2ProGUI(controller, config_manager, RPM_COMMANDS, COMMANDS, DEFAULT_SETTINGS)
