#!/usr/bin/env python3
"""
CPU Temperature Monitoring Module
"""
import os
import logging
import subprocess
import threading
import time

class CPUMonitor:
    def __init__(self):
        self.temperature = 0
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        
    def add_callback(self, callback):
        """Add a callback function to be called when temperature changes"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove a callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, temperature):
        """Notify all registered callbacks of temperature change"""
        for callback in self.callbacks:
            try:
                callback(temperature)
            except Exception as e:
                logging.error(f"Error in temperature callback: {e}")
    
    def get_cpu_temperature(self):
        """Get current CPU temperature"""
        try:
            # Try different methods to get CPU temperature
            temp = self._try_hwmon()
            if temp is not None:
                return temp
                
            temp = self._try_thermal_zone()
            if temp is not None:
                return temp
                
            temp = self._try_sensors()
            if temp is not None:
                return temp
                
            temp = self._try_vcgencmd()
            if temp is not None:
                return temp
                
            # Fallback: return a default temperature
            logging.warning("Could not read CPU temperature, using default")
            return 45.0
            
        except Exception as e:
            logging.error(f"Error reading CPU temperature: {e}")
            return 45.0
    
    def _try_thermal_zone(self):
        """Try to read from thermal zone (Linux)"""
        try:
            thermal_files = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/thermal/thermal_zone1/temp",
                "/sys/class/thermal/thermal_zone2/temp"
            ]
            
            for thermal_file in thermal_files:
                if os.path.exists(thermal_file):
                    with open(thermal_file, 'r') as f:
                        temp_millicelsius = int(f.read().strip())
                        temp_celsius = temp_millicelsius / 1000.0
                        # Skip thermal_zone0 as it's often not the CPU temperature
                        if thermal_file != "/sys/class/thermal/thermal_zone0/temp" and 20 <= temp_celsius <= 100:
                            return temp_celsius
        except Exception:
            pass
        return None
    
    def _try_hwmon(self):
        """Try to read from hwmon (Linux) - most reliable for CPU temperature"""
        try:
            hwmon_path = "/sys/class/hwmon"
            if not os.path.exists(hwmon_path):
                return None
                
            # Look for CPU temperature sensors
            cpu_temps = []
            for hwmon_dir in os.listdir(hwmon_path):
                if hwmon_dir.startswith('hwmon'):
                    hwmon_full_path = os.path.join(hwmon_path, hwmon_dir)
                    for temp_file in os.listdir(hwmon_full_path):
                        if temp_file.startswith('temp') and temp_file.endswith('_input'):
                            temp_file_path = os.path.join(hwmon_full_path, temp_file)
                            try:
                                with open(temp_file_path, 'r') as f:
                                    temp_raw = f.read().strip()
                                    temp_celsius = float(temp_raw) / 1000.0
                                    if 20 <= temp_celsius <= 100:  # Reasonable temperature range
                                        cpu_temps.append(temp_celsius)
                            except Exception:
                                continue
            
            if cpu_temps:
                # Return the highest temperature (likely CPU)
                return max(cpu_temps)
        except Exception:
            pass
        return None
    
    def _try_sensors(self):
        """Try to read from sensors command"""
        try:
            result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Core 0' in line or 'Package id 0' in line or 'Tdie' in line:
                        # Extract temperature from line like "Core 0: +45.0°C"
                        parts = line.split('+')
                        if len(parts) > 1:
                            temp_part = parts[1].split('°')[0]
                            temp = float(temp_part)
                            if 20 <= temp <= 100:
                                return temp
        except Exception:
            pass
        return None
    
    def _try_vcgencmd(self):
        """Try to read from vcgencmd (Raspberry Pi)"""
        try:
            result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Output format: "temp=45.0'C"
                temp_str = result.stdout.strip()
                if 'temp=' in temp_str:
                    temp_part = temp_str.split('temp=')[1].split("'")[0]
                    temp = float(temp_part)
                    if 20 <= temp <= 100:
                        return temp
        except Exception:
            pass
        return None
    
    def start_monitoring(self, interval=2):
        """Start monitoring CPU temperature"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitor_thread.start()
        logging.info("CPU temperature monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring CPU temperature"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logging.info("CPU temperature monitoring stopped")
    
    def _monitor_loop(self, interval):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                temp = self.get_cpu_temperature()
                if temp != self.temperature:
                    self.temperature = temp
                    self._notify_callbacks(temp)
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Error in temperature monitoring loop: {e}")
                time.sleep(interval)
    
    def get_temperature(self):
        """Get the last known temperature"""
        return self.temperature
