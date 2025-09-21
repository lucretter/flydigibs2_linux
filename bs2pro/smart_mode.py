#!/usr/bin/env python3
"""
Smart Mode Configuration and Management
"""
import logging
import json
import os

class SmartModeManager:
    def __init__(self, config_file=None):
        if config_file is None:
            # Use the same config directory as the main application
            config_dir = os.path.join(os.path.expanduser("~"), ".config", "bs2pro_controller")
            os.makedirs(config_dir, exist_ok=True)
            self.config_file = os.path.join(config_dir, "smart_mode.json")
        else:
            self.config_file = config_file
        self.temperature_ranges = []
        self.is_enabled = False
        self.load_config()
    
    def load_config(self):
        """Load smart mode configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.temperature_ranges = data.get('temperature_ranges', [])
                    self.is_enabled = data.get('enabled', False)
            else:
                # Default configuration
                self.temperature_ranges = [
                    {"min_temp": 0, "max_temp": 50, "rpm": 1300, "description": "Low temperature"},
                    {"min_temp": 50, "max_temp": 60, "rpm": 1700, "description": "Normal temperature"},
                    {"min_temp": 60, "max_temp": 70, "rpm": 1900, "description": "Warm temperature"},
                    {"min_temp": 70, "max_temp": 80, "rpm": 2100, "description": "Hot temperature"},
                    {"min_temp": 80, "max_temp": 100, "rpm": 2700, "description": "Very hot temperature"}
                ]
                self.save_config()
        except Exception as e:
            logging.error(f"Error loading smart mode config: {e}")
            self.temperature_ranges = []
            self.is_enabled = False
    
    def save_config(self):
        """Save smart mode configuration to file"""
        try:
            data = {
                'enabled': self.is_enabled,
                'temperature_ranges': self.temperature_ranges
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving smart mode config: {e}")
    
    def add_temperature_range(self, min_temp, max_temp, rpm, description=""):
        """Add a new temperature range"""
        range_data = {
            "min_temp": min_temp,
            "max_temp": max_temp,
            "rpm": rpm,
            "description": description
        }
        self.temperature_ranges.append(range_data)
        self.temperature_ranges.sort(key=lambda x: x['min_temp'])
        self.save_config()
    
    
    def get_rpm_for_temperature(self, temperature):
        """Get the appropriate RPM for a given temperature"""
        for range_data in self.temperature_ranges:
            if range_data['min_temp'] <= temperature < range_data['max_temp']:
                return range_data['rpm']
        
        # If temperature is above all ranges, use the highest RPM
        if self.temperature_ranges:
            return max(range_data['rpm'] for range_data in self.temperature_ranges)
        
        return 1300  # Default RPM
    
    def get_range_for_temperature(self, temperature):
        """Get the range description for a given temperature"""
        for range_data in self.temperature_ranges:
            if range_data['min_temp'] <= temperature < range_data['max_temp']:
                return range_data
        
        return None
    
    def set_enabled(self, enabled):
        """Enable or disable smart mode"""
        self.is_enabled = enabled
        self.save_config()
    
    def is_smart_mode_enabled(self):
        """Check if smart mode is enabled"""
        return self.is_enabled
    
    def get_temperature_ranges(self):
        """Get all temperature ranges"""
        return self.temperature_ranges.copy()
