#!/usr/bin/env python3
"""
RPM Monitoring Module for BS2Pro
Captures and decodes RPM data sent by the cooling pad
"""
import logging
import threading
import time
import struct

# Try different ways to import hidapi
try:
    import hid
except ImportError:
    try:
        import hidapi as hid
    except ImportError:
        hid = None

class RPMMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        self.current_rpm = 0
        self.device = None
        self.vid = None
        self.pid = None
        
        
    def add_callback(self, callback):
        """Add a callback function to be called when RPM changes"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove a callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    
    def _notify_callbacks(self, rpm):
        """Notify all registered callbacks of RPM change"""
        for callback in self.callbacks:
            try:
                callback(rpm)
            except Exception as e:
                logging.error(f"Error in RPM callback: {e}")
    
    def detect_bs2pro(self):
        """Detect BS2Pro device"""
        if hid is None:
            logging.error("HID library not available")
            return False
        
        try:
            devices = hid.enumerate()
            for d in devices:
                if "BS2PRO" in d.get("product_string", ""):
                    self.vid = d["vendor_id"]
                    self.pid = d["product_id"]
                    logging.info(f"BS2Pro found: VID={self.vid:04x}, PID={self.pid:04x}")
                    return True
            return False
        except Exception as e:
            logging.error(f"Error enumerating HID devices: {e}")
            return False
    
    def _open_device(self):
        """Open HID device for reading"""
        if self.vid is None or self.pid is None:
            return False
            
        try:
            logging.info(f"Attempting to open HID device VID={self.vid:04x}, PID={self.pid:04x}")
            if hasattr(hid, 'Device'):
                # New hidapi API (0.14+)
                logging.info("Using new hidapi API (Device)")
                self.device = hid.Device(vid=self.vid, pid=self.pid)
                logging.info("Device opened successfully with new API")
                return True
            elif hasattr(hid, 'device'):
                # hidapi 0.14.0.post4 API (lowercase device)
                logging.info("Using hidapi 0.14.0.post4 API (device)")
                self.device = hid.device()
                self.device.open(self.vid, self.pid)
                logging.info("Device opened successfully with 0.14.0.post4 API")
                return True
            elif hasattr(hid, 'open'):
                # Old hidapi API (0.13 and earlier)
                logging.info("Using old hidapi API (open)")
                self.device = hid.open(self.vid, self.pid)
                success = self.device is not None
                if success:
                    logging.info("Device opened successfully with old API")
                else:
                    logging.warning("Device open returned None")
                return success
            else:
                logging.error("Unsupported hidapi version")
                return False
        except Exception as e:
            logging.error(f"Error opening HID device: {e}")
            return False
    
    def _close_device(self):
        """Close HID device"""
        if self.device:
            logging.info("Closing HID device")
            try:
                if hasattr(self.device, 'close'):
                    self.device.close()
                self.device = None
                logging.info("HID device closed successfully")
            except Exception as e:
                logging.error(f"Error closing HID device: {e}")
        else:
            logging.debug("No device to close")
    
    def _is_device_open(self):
        """Check if device is open and accessible"""
        if not self.device:
            return False
        
        try:
            if hasattr(self.device, 'read'):
                return True
            return False
        except:
            return False
    
    def _decode_rpm_data(self, data):
        """Decode RPM data from HID report"""
        try:
            # Convert bytes to hex string for analysis
            hex_data = data.hex()
            logging.info(f"Received data: {hex_data}")
            
            # Check if this is a BS2Pro status response
            # Pattern: 035aa5ef0b[changing_data]...
            if len(data) >= 10 and data[0] == 0x03 and data[1] == 0x5a and data[2] == 0xa5:
                logging.info("Detected BS2Pro status response")
                
                # Based on analysis, the most common RPM value is 1300 at position 8-9
                # Let's prioritize the most likely positions for actual fan RPM
                
                # Method 1: Look at bytes 8-9 (most common position for 1300 RPM)
                if len(data) >= 10:
                    rpm_bytes = data[8:10]
                    rpm_le = struct.unpack('<H', rpm_bytes)[0]
                    rpm_be = struct.unpack('>H', rpm_bytes)[0]
                    
                    logging.info(f"Bytes 8-9: {rpm_bytes.hex()} -> LE: {rpm_le}, BE: {rpm_be}")
                    
                    if 1000 <= rpm_le <= 3000:  # Realistic fan RPM range
                        logging.info(f"Found RPM (LE) at bytes 8-9: {rpm_le}")
                        return rpm_le
                    if 1000 <= rpm_be <= 3000:
                        logging.info(f"Found RPM (BE) at bytes 8-9: {rpm_be}")
                        return rpm_be
                
                # Method 2: Look at bytes 10-11 (also common for 1300 RPM)
                if len(data) >= 12:
                    rpm_bytes = data[10:12]
                    rpm_le = struct.unpack('<H', rpm_bytes)[0]
                    rpm_be = struct.unpack('>H', rpm_bytes)[0]
                    
                    if 1000 <= rpm_le <= 3000:
                        logging.info(f"Found RPM (LE) at bytes 10-11: {rpm_le}")
                        return rpm_le
                    if 1000 <= rpm_be <= 3000:
                        logging.info(f"Found RPM (BE) at bytes 10-11: {rpm_be}")
                        return rpm_be
                
                # Method 3: Look at bytes 13-14 (changing values that might be actual RPM)
                if len(data) >= 15:
                    rpm_bytes = data[13:15]
                    rpm_le = struct.unpack('<H', rpm_bytes)[0]
                    rpm_be = struct.unpack('>H', rpm_bytes)[0]
                    
                    if 1000 <= rpm_le <= 3000:
                        logging.info(f"Found RPM (LE) at bytes 13-14: {rpm_le}")
                        return rpm_le
                    if 1000 <= rpm_be <= 3000:
                        logging.info(f"Found RPM (BE) at bytes 13-14: {rpm_be}")
                        return rpm_be
                
                # Method 4: Look at bytes 14-15 (scaled values)
                if len(data) >= 16:
                    rpm_bytes = data[14:16]
                    rpm_le = struct.unpack('<H', rpm_bytes)[0]
                    rpm_be = struct.unpack('>H', rpm_bytes)[0]
                    
                    # Try scaled values
                    for scale in [10, 100]:
                        scaled_le = rpm_le * scale
                        scaled_be = rpm_be * scale
                        
                        if 1000 <= scaled_le <= 3000:
                            logging.info(f"Found RPM (scaled LE x{scale}) at bytes 14-15: {scaled_le}")
                            return scaled_le
                        if 1000 <= scaled_be <= 3000:
                            logging.info(f"Found RPM (scaled BE x{scale}) at bytes 14-15: {scaled_be}")
                            return scaled_be
                
                # No fallback methods - only use the accurate detection above
                logging.info("No valid RPM found in BS2Pro status response")
            
            logging.info("No BS2Pro status response detected")
            return None
            
        except Exception as e:
            logging.error(f"Error decoding RPM data: {e}")
            return None
    
    def _monitor_loop(self, interval=0.1):
        """Main monitoring loop"""
        logging.info("RPM monitoring started")
        
        while self.is_monitoring:
            try:
                if self.device is None:
                    logging.info("Device not open, attempting to open...")
                    if not self._open_device():
                        logging.warning("Failed to open device, retrying in 1 second...")
                        time.sleep(1)
                        continue
                    else:
                        logging.info("Device opened successfully")
                
                # Try to read data from the device
                try:
                    logging.info("Attempting to read from device...")
                    # Try with timeout first, fallback to without timeout
                    if hasattr(self.device, 'read'):
                        try:
                            logging.debug("Trying read with timeout...")
                            data = self.device.read(32, timeout=1000)  # 1000ms timeout
                            logging.info(f"Read completed, data: {data}")
                            if data:
                                # Convert list to bytes if necessary
                                if isinstance(data, list):
                                    data = bytes(data)
                                logging.info(f"Raw data: {data.hex()}")
                            else:
                                logging.info("No data received (timeout)")
                        except TypeError:
                            # Some versions don't support timeout parameter
                            logging.debug("Timeout not supported, trying without timeout...")
                            data = self.device.read(32)
                            logging.info(f"Read completed, data: {data}")
                            if data:
                                # Convert list to bytes if necessary
                                if isinstance(data, list):
                                    data = bytes(data)
                                logging.info(f"Raw data: {data.hex()}")
                            else:
                                logging.info("No data received (no timeout)")
                        except Exception as e:
                            logging.error(f"Read error: {e}")
                            data = None
                    else:
                        logging.warning("Device has no read method")
                        time.sleep(interval)
                        continue
                    
                    if data:
                        # Data received, process it
                        logging.info(f"Data received: {len(data)} bytes")
                        
                        rpm = self._decode_rpm_data(data)
                        if rpm is not None and rpm != self.current_rpm:
                            self.current_rpm = rpm
                            self._notify_callbacks(rpm)
                            logging.info(f"RPM updated: {rpm}")
                    else:
                        # No data received, try alternative approach
                        logging.debug("No data received, trying alternative read method...")
                        try:
                            # Try reading without timeout
                            if hasattr(self.device, 'read'):
                                data = self.device.read(32)
                                if data:
                                    # Convert list to bytes if necessary
                                    if isinstance(data, list):
                                        data = bytes(data)
                                    logging.info(f"Raw data (no timeout): {data.hex()}")
                                    rpm = self._decode_rpm_data(data)
                                    if rpm is not None and rpm != self.current_rpm:
                                        self.current_rpm = rpm
                                        self._notify_callbacks(rpm)
                                        logging.info(f"RPM updated: {rpm}")
                        except Exception as e:
                            logging.debug(f"Alternative read also failed: {e}")
                    
                except Exception as e:
                    logging.error(f"Error reading from device: {e}")
                    # Device might have disconnected, try to reconnect
                    logging.info("Closing device due to read error")
                    self._close_device()
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
            
            time.sleep(interval)
        
        self._close_device()
        logging.info("RPM monitoring stopped")
    
    def start_monitoring(self, interval=0.1):
        """Start monitoring RPM data"""
        logging.info(f"start_monitoring called, is_monitoring: {self.is_monitoring}")
        if self.is_monitoring:
            logging.warning("RPM monitoring is already running")
            return
        
        if not self.detect_bs2pro():
            logging.error("BS2Pro device not found for RPM monitoring")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitor_thread.start()
        logging.info("RPM monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring RPM data"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self._close_device()
        logging.info("RPM monitoring stopped")
    
    def get_current_rpm(self):
        """Get the current RPM value"""
        return self.current_rpm
