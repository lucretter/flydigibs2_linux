import configparser
import os

class ConfigManager:
    def __init__(self, config_file, default_settings):
        self.config_file = config_file
        self.default_settings = default_settings

    def save_setting(self, key, value):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
        if "Settings" not in config:
            config["Settings"] = {}
        config["Settings"][key] = str(value)
        with open(self.config_file, "w") as f:
            config.write(f)

    def load_setting(self, key, default=None):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            return config.get("Settings", key, fallback=default)
        return default

    def initialize_settings(self):
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if not os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config["Settings"] = self.default_settings
            with open(self.config_file, "w") as f:
                config.write(f)
            return True
        return False
