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

# Try to import direct hidapi access
HIDAPI_DIRECT = False
try:
    import hidapi
    if hasattr(hidapi, 'hidapi') and hasattr(hidapi, 'ffi'):
        HIDAPI_DIRECT = True
        logging.debug("Direct hidapi access available")
except ImportError:
    logging.debug("Direct hidapi access not available")

class RPMMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        self.current_rpm = 0
        self.device = None
        self.vid = None
        self.pid = None
        
        # Shared device access
        self.get_shared_device_func = None
        self.release_shared_device_func = None
        
        
    def add_callback(self, callback):
        """Add a callback function to be called when RPM changes"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove a callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def set_shared_device_access(self, get_func, release_func):
        """Set shared device access functions"""
        self.get_shared_device_func = get_func
        self.release_shared_device_func = release_func
    
    
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
                # Handle both dictionary-style and attribute-style access for different hidapi versions
                product_string = ""
                vendor_id = None
                product_id = None
                
                # Check if it's a dictionary (most common case)
                if isinstance(d, dict):
                    product_string = d.get("product_string", "")
                    vendor_id = d.get("vendor_id")
                    product_id = d.get("product_id")
                else:
                    # Try attribute access for object-style access
                    try:
                        product_string = getattr(d, 'product_string', '')
                        vendor_id = getattr(d, 'vendor_id', None)
                        product_id = getattr(d, 'product_id', None)
                    except (AttributeError, TypeError):
                        # Skip this device if we can't access its info
                        continue
                
                if product_string and "BS2PRO" in product_string:
                    self.vid = vendor_id
                    self.pid = product_id
                    logging.info(f"BS2Pro found: VID={self.vid:04x}, PID={self.pid:04x}")
                    return True
            return False
        except Exception as e:
            logging.error(f"Error enumerating HID devices: {e}")
            return False
    
    def _open_device(self):
        """Open HID device for reading"""
        # Use shared device if available
        if self.get_shared_device_func:
            logging.debug("Using shared device for RPM monitoring")
            self.device = self.get_shared_device_func()
            if self.device:
                logging.debug("Shared device obtained successfully")
                return True
            else:
                logging.warning("Failed to get shared device")
                return False
        
        # Fallback to direct access
        if self.vid is None or self.pid is None:
            return False
            
        try:
            logging.info(f"Attempting to open HID device VID={self.vid:04x}, PID={self.pid:04x}")
            
            # Try different hidapi APIs, starting with most compatible
            device_opened = False
            
            # Method 0: Try direct hidapi low-level access (most reliable)
            if HIDAPI_DIRECT and not device_opened:
                try:
                    logging.info("Using direct hidapi low-level access")
                    device_handle = hidapi.hidapi.hid_open(self.vid, self.pid, hidapi.ffi.NULL)
                    if device_handle != hidapi.ffi.NULL:
                        # Store handle in a way compatible with monitoring code
                        self.device = {'handle': device_handle, 'type': 'direct'}
                        device_opened = True
                        logging.info("Device opened successfully with direct hidapi access")
                except Exception as e:
                    logging.debug(f"Direct hidapi access failed: {e}")
            
            # Method 1: Try hid.open() function first (most compatible)
            if hasattr(hid, 'open') and not device_opened:
                try:
                    logging.info("Using hidapi open() function")
                    self.device = hid.open(self.vid, self.pid)
                    if self.device is not None:
                        device_opened = True
                        logging.info("Device opened successfully with open() function")
                    else:
                        logging.debug("hid.open() returned None")
                except Exception as e:
                    logging.debug(f"hid.open() failed: {e}")
            
            # Method 2: Try lowercase device() class
            if hasattr(hid, 'device') and not device_opened:
                try:
                    logging.info("Using hidapi device() class")
                    self.device = hid.device()
                    self.device.open(self.vid, self.pid)
                    device_opened = True
                    logging.info("Device opened successfully with device() class")
                except Exception as e:
                    logging.debug(f"hid.device() failed: {e}")
                    self.device = None
            
            # Skip Method 3 (Device class) as it's broken on this system
            
            if not device_opened:
                logging.error("All HID device opening methods failed")
                return False
            
            return True
        except Exception as e:
            logging.error(f"Error opening HID device: {e}")
            return False
    
    def _close_device(self):
        """Close HID device"""
        if self.device:
            logging.debug("Closing HID device")
            try:
                # For shared devices, don't close the device
                if self.get_shared_device_func:
                    logging.debug("Releasing shared device")
                    if self.release_shared_device_func:
                        self.release_shared_device_func()
                    self.device = None
                else:
                    # For direct devices, close them
                    if isinstance(self.device, dict) and self.device.get('type') == 'direct':
                        if HIDAPI_DIRECT:
                            hidapi.hidapi.hid_close(self.device['handle'])
                            logging.debug("Direct hidapi device closed")
                    elif hasattr(self.device, 'close'):
                        self.device.close()
                    self.device = None
                logging.debug("HID device closed successfully")
            except Exception as e:
                logging.error(f"Error closing HID device: {e}")
        else:
            logging.debug("No device to close")
    
    
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
                    logging.debug("Attempting to read from device...")
                    data = None
                    
                    # Handle direct hidapi access
                    if isinstance(self.device, dict) and self.device.get('type') == 'direct':
                        if HIDAPI_DIRECT:
                            try:
                                logging.debug("Trying read with direct hidapi access...")
                                response_buffer = hidapi.ffi.new("unsigned char[]", 32)
                                bytes_read = hidapi.hidapi.hid_read_timeout(self.device['handle'], response_buffer, 32, 1000)
                                if bytes_read > 0:
                                    data = bytes(hidapi.ffi.buffer(response_buffer, bytes_read))
                                    logging.debug(f"Direct hidapi read completed, data: {data}")
                                else:
                                    logging.debug("No data received (direct hidapi timeout)")
                            except Exception as e:
                                logging.error(f"Direct hidapi read error: {e}")
                                data = None
                    
                    # Handle regular hidapi objects
                    elif hasattr(self.device, 'read'):
                        try:
                            logging.debug("Trying read without timeout...")
                            data = self.device.read(32)  # No timeout parameter
                            logging.debug(f"Read completed, data: {data}")
                            if data:
                                # Convert list to bytes if necessary
                                if isinstance(data, list):
                                    data = bytes(data)
                                logging.debug(f"Raw data: {data.hex()}")
                            else:
                                logging.debug("No data received")
                        except Exception as e:
                            logging.error(f"Read error: {e}")
                            data = None
                    else:
                        logging.warning("Device has no read method")
                        time.sleep(interval)
                        continue
                    
                    if data:
                        # Data received, process it
                        logging.debug(f"Data received: {len(data)} bytes")
                        
                        rpm = self._decode_rpm_data(data)
                        if rpm is not None and rpm != self.current_rpm:
                            self.current_rpm = rpm
                            self._notify_callbacks(rpm)
                            logging.info(f"RPM updated: {rpm}")
                    else:
                        # No data received, try alternative approach
                        logging.debug("No data received, trying alternative read method...")
                        try:
                            # Handle direct hidapi access for alternative read
                            if isinstance(self.device, dict) and self.device.get('type') == 'direct':
                                if HIDAPI_DIRECT:
                                    response_buffer = hidapi.ffi.new("unsigned char[]", 32)
                                    bytes_read = hidapi.hidapi.hid_read(self.device['handle'], response_buffer, 32)
                                    if bytes_read > 0:
                                        data = bytes(hidapi.ffi.buffer(response_buffer, bytes_read))
                                        logging.debug(f"Raw data (direct hidapi no timeout): {data.hex()}")
                                        rpm = self._decode_rpm_data(data)
                                        if rpm is not None and rpm != self.current_rpm:
                                            self.current_rpm = rpm
                                            self._notify_callbacks(rpm)
                                            logging.info(f"RPM updated: {rpm}")
                            # Try reading without timeout for regular devices
                            elif hasattr(self.device, 'read'):
                                data = self.device.read(32)
                                if data:
                                    # Convert list to bytes if necessary
                                    if isinstance(data, list):
                                        data = bytes(data)
                                    logging.debug(f"Raw data (no timeout): {data.hex()}")
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
        logging.debug(f"start_monitoring called, is_monitoring: {self.is_monitoring}")
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
