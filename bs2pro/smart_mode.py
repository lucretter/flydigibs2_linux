#!/usr/bin/env python3
"""
Smart Mode Configuration and Management
"""
import logging
import json
import os
import time

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
        self.last_temperature = None  # Track last temperature for stability
        self.last_rpm = None  # Track last RPM to prevent unnecessary changes
        self.pending_rpm_change = None  # Track pending RPM change for delay
        self.rpm_change_time = None  # Track when RPM change was requested
        self.rpm_change_delay = 10.0  # 10 second delay for RPM decreases
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
        """Get the appropriate RPM for a given temperature with stability improvements and delay for RPM decreases"""
        current_time = time.time()
        
        # Check if we have a pending RPM change that hasn't been applied yet
        if (self.pending_rpm_change is not None and 
            self.rpm_change_time is not None and 
            self.last_rpm is not None):
            
            time_elapsed = current_time - self.rpm_change_time
            
            # If delay period hasn't passed, keep current RPM
            if time_elapsed < self.rpm_change_delay:
                logging.debug(f"RPM decrease delayed: {temperature}°C -> waiting {self.rpm_change_delay - time_elapsed:.1f}s more (pending: {self.pending_rpm_change})")
                # Update last temperature even during delay
                self.last_temperature = temperature
                return self.last_rpm
            else:
                # Delay period has passed, apply the pending change
                logging.debug(f"Applying delayed RPM change: {self.last_rpm} -> {self.pending_rpm_change}")
                self.last_rpm = self.pending_rpm_change
                self.pending_rpm_change = None
                self.rpm_change_time = None
                self.last_temperature = temperature
                return self.last_rpm
        
        # Add temperature hysteresis to prevent rapid oscillations, but only if no delay is pending
        # Only change RPM if temperature has changed by more than 1°C or if this is the first reading
        if (self.last_temperature is not None and 
            abs(temperature - self.last_temperature) < 1.0 and 
            self.last_rpm is not None and
            self.pending_rpm_change is None):  # Don't apply hysteresis if we have a pending change
            logging.debug(f"Temperature hysteresis: {temperature}°C -> keeping RPM {self.last_rpm} (last temp: {self.last_temperature}°C)")
            return self.last_rpm  # Keep the same RPM to prevent oscillation
        
        # Update last temperature
        self.last_temperature = temperature
        logging.debug(f"Processing temperature change: {temperature}°C")
        
        # Calculate what the new RPM should be
        new_rpm = self._calculate_target_rpm(temperature)
        
        # If this is the first reading, apply immediately
        if self.last_rpm is None:
            self.last_rpm = new_rpm
            return new_rpm
        
        # If RPM is increasing (temperature going up), apply immediately for safety
        if new_rpm > self.last_rpm:
            logging.debug(f"Temperature increase: {temperature}°C -> RPM {self.last_rpm} -> {new_rpm} (immediate)")
            self.last_rpm = new_rpm
            # Cancel any pending decrease
            self.pending_rpm_change = None
            self.rpm_change_time = None
            return new_rpm
        
        # If RPM is decreasing (temperature going down), add delay
        elif new_rpm < self.last_rpm:
            # If we don't already have a pending change, start the delay timer
            if self.pending_rpm_change is None:
                self.pending_rpm_change = new_rpm
                self.rpm_change_time = current_time
                logging.debug(f"Temperature decrease: {temperature}°C -> RPM {self.last_rpm} -> {new_rpm} (delayed {self.rpm_change_delay}s)")
            # If we have a different pending change, update it
            elif self.pending_rpm_change != new_rpm:
                self.pending_rpm_change = new_rpm
                self.rpm_change_time = current_time
                logging.debug(f"Updated pending RPM change: {temperature}°C -> RPM {self.last_rpm} -> {new_rpm} (delayed {self.rpm_change_delay}s)")
            
            # Keep current RPM until delay expires
            return self.last_rpm
        
        # RPM is the same, no change needed
        return self.last_rpm

    def _calculate_target_rpm(self, temperature):
        """Calculate the target RPM for a given temperature without applying delays"""
        # First, try to find an exact range match
        for range_data in self.temperature_ranges:
            if range_data['min_temp'] <= temperature < range_data['max_temp']:
                return range_data['rpm']
        
        # If no exact match, find the closest range intelligently
        if self.temperature_ranges:
            # Sort ranges by min_temp to ensure proper ordering
            sorted_ranges = sorted(self.temperature_ranges, key=lambda x: x['min_temp'])
            
            # If temperature is below all ranges, use the lowest RPM
            if temperature < sorted_ranges[0]['min_temp']:
                return sorted_ranges[0]['rpm']
            
            # If temperature is above all ranges, use the highest RPM
            if temperature >= sorted_ranges[-1]['max_temp']:
                return sorted_ranges[-1]['rpm']
            
            # Temperature is between ranges - find the closest one
            # This handles edge cases where temperature falls exactly on boundaries
            closest_range = None
            min_distance = float('inf')
            
            for range_data in sorted_ranges:
                # Calculate distance to range center
                range_center = (range_data['min_temp'] + range_data['max_temp']) / 2
                distance = abs(temperature - range_center)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_range = range_data
            
            if closest_range:
                return closest_range['rpm']
        
        # Final fallback
        return 1300
    
    def get_range_for_temperature(self, temperature):
        """Get the range description for a given temperature"""
        for range_data in self.temperature_ranges:
            if range_data['min_temp'] <= temperature < range_data['max_temp']:
                return range_data
        
        return None
    
    def set_enabled(self, enabled):
        """Enable or disable smart mode"""
        self.is_enabled = enabled
        # Reset hysteresis and delay tracking when toggling smart mode
        if enabled:
            self.last_temperature = None
            self.last_rpm = None
            self.pending_rpm_change = None
            self.rpm_change_time = None
        self.save_config()
    
    def is_smart_mode_enabled(self):
        """Check if smart mode is enabled"""
        return self.is_enabled
    
    def get_temperature_ranges(self):
        """Get all temperature ranges"""
        return self.temperature_ranges.copy()
    
    def get_pending_change_status(self):
        """Get status of any pending RPM changes"""
        if self.pending_rpm_change is not None and self.rpm_change_time is not None:
            current_time = time.time()
            time_elapsed = current_time - self.rpm_change_time
            time_remaining = max(0, self.rpm_change_delay - time_elapsed)
            
            return {
                'has_pending': True,
                'current_rpm': self.last_rpm,
                'pending_rpm': self.pending_rpm_change,
                'time_remaining': time_remaining,
                'delay_total': self.rpm_change_delay
            }
        
        return {'has_pending': False}
