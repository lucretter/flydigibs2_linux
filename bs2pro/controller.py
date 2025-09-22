import logging
import threading

# Import RPM monitor with fallback for packaging
try:
    from .rpm_monitor import RPMMonitor
    logging.info("RPM monitor imported via relative import")
except ImportError as e:
    logging.info(f"Relative import failed: {e}")
    try:
        from rpm_monitor import RPMMonitor
        logging.info("RPM monitor imported via direct import")
    except ImportError as e:
        logging.info(f"Direct import failed: {e}")
        try:
            from bs2pro.rpm_monitor import RPMMonitor
            logging.info("RPM monitor imported via absolute import")
        except ImportError as e:
            logging.error(f"All RPM monitor imports failed: {e}")
            raise

# Try different ways to import hidapi
try:
    import hid
except ImportError:
    try:
        import hidapi as hid
    except ImportError:
        hid = None

class BS2ProController:
    def __init__(self):
        # Log hidapi information for debugging
        if hid is not None:
            logging.info(f"HID library loaded: {hid.__file__ if hasattr(hid, '__file__') else 'unknown location'}")
            logging.info(f"HID version: {hid.__version__ if hasattr(hid, '__version__') else 'unknown'}")
            logging.info(f"HID attributes: {[attr for attr in dir(hid) if not attr.startswith('_')]}")
        else:
            logging.warning("HID library not available")
        
        # Initialize RPM monitor with shared device access
        self.rpm_monitor = RPMMonitor()
        self.shared_device = None
        self.device_lock = threading.Lock()
        self.rpm_monitor.set_shared_device_access(self._get_shared_device, self._release_shared_device)

    def detect_bs2pro(self):
        if hid is None:
            logging.error("HID library not available")
            return None, None
        
        try:
            devices = hid.enumerate()
            for d in devices:
                # Handle both dictionary-style and attribute-style access for different hidapi versions
                try:
                    # Try attribute access first (newer hidapi)
                    product_string = getattr(d, 'product_string', '')
                    vendor_id = getattr(d, 'vendor_id', None)
                    product_id = getattr(d, 'product_id', None)
                except (AttributeError, TypeError):
                    # Fallback to dictionary access (older hidapi)
                    try:
                        product_string = d.get("product_string", "")
                        vendor_id = d.get("vendor_id")
                        product_id = d.get("product_id")
                    except (AttributeError, TypeError):
                        # Skip this device if we can't access its info
                        continue
                
                if product_string and "BS2PRO" in product_string:
                    return vendor_id, product_id
            return None, None
        except Exception as e:
            logging.error(f"Error enumerating HID devices: {e}")
            return None, None

    def send_command(self, hex_cmd, status_callback=None):
        if hid is None:
            if status_callback:
                status_callback("❌ HID library not available", "danger")
            logging.error("HID library not available")
            return False
            
        try:
            # Use shared device if available, otherwise create temporary one
            dev = self._get_shared_device()
            if dev:
                logging.debug("Using shared device for command")
                payload = bytes.fromhex(hex_cmd)
                dev.write(payload)
                # Try with timeout first, fallback to without timeout
                try:
                    dev.read(32, timeout=1000)
                except TypeError:
                    # Some versions don't support timeout parameter
                    dev.read(32)
            else:
                # Fallback to creating temporary device
                vid, pid = self.detect_bs2pro()
                if vid is None or pid is None:
                    if status_callback:
                        status_callback("❌ BS2PRO device not found", "danger")
                    logging.error("BS2PRO device not found.")
                    return False
                
                # Try different hidapi APIs based on version, starting with most compatible
                device_opened = False
                
                # Method 1: Try hid.open() function first (most compatible)
                if hasattr(hid, 'open') and not device_opened:
                    try:
                        dev = hid.open(vid, pid)
                        if dev is not None:
                            device_opened = True
                            payload = bytes.fromhex(hex_cmd)
                            dev.write(payload)
                            # Try with timeout first, fallback to without timeout
                            try:
                                dev.read(32, timeout=1000)
                            except TypeError:
                                # Some versions don't support timeout parameter
                                dev.read(32)
                            dev.close()
                    except Exception as e:
                        logging.debug(f"hid.open() failed: {e}")
                
                # Method 2: Try lowercase device() class
                if hasattr(hid, 'device') and not device_opened:
                    try:
                        dev = hid.device()
                        dev.open(vid, pid)
                        device_opened = True
                        payload = bytes.fromhex(hex_cmd)
                        dev.write(payload)
                        # Try with timeout first, fallback to without timeout
                        try:
                            dev.read(32, timeout=1000)
                        except TypeError:
                            # Some versions don't support timeout parameter
                            dev.read(32)
                        dev.close()
                    except Exception as e:
                        logging.debug(f"hid.device() failed: {e}")
                
                # Method 3: Try Device class without keyword arguments
                if hasattr(hid, 'Device') and not device_opened:
                    try:
                        dev = hid.Device()
                        dev.open(vid, pid)
                        device_opened = True
                        payload = bytes.fromhex(hex_cmd)
                        dev.write(payload)
                        # Try with timeout first, fallback to without timeout
                        try:
                            dev.read(32, timeout=1000)
                        except TypeError:
                            # Some versions don't support timeout parameter
                            dev.read(32)
                        dev.close()
                    except Exception as e:
                        logging.debug(f"hid.Device() failed: {e}")
                
                if not device_opened:
                    if status_callback:
                        status_callback("❌ Failed to open HID device", "danger")
                    logging.error("All HID device opening methods failed")
                    return False
                
            if status_callback:
                status_callback("✅ Command sent successfully", "success")
            logging.info(f"Command sent: {hex_cmd}")
            return True
        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ HID error: {e}", "danger")
            logging.error(f"HID error: {e}")
            return False
    
    def _get_shared_device(self):
        """Get shared HID device for both reading and writing"""
        with self.device_lock:
            if self.shared_device is None:
                try:
                    vid, pid = self.detect_bs2pro()
                    if vid is None or pid is None:
                        return None
                    
                    logging.debug(f"Creating shared HID device VID={vid:04x}, PID={pid:04x}")
                    
                    # Try different hidapi APIs, starting with most compatible
                    device_created = False
                    
                    # Method 1: Try hid.open() function first
                    if hasattr(hid, 'open') and not device_created:
                        try:
                            self.shared_device = hid.open(vid, pid)
                            if self.shared_device is not None:
                                device_created = True
                        except Exception as e:
                            logging.debug(f"hid.open() failed: {e}")
                    
                    # Method 2: Try lowercase device() class
                    if hasattr(hid, 'device') and not device_created:
                        try:
                            self.shared_device = hid.device()
                            self.shared_device.open(vid, pid)
                            device_created = True
                        except Exception as e:
                            logging.debug(f"hid.device() failed: {e}")
                            self.shared_device = None
                    
                    # Method 3: Try Device class without keyword arguments
                    if hasattr(hid, 'Device') and not device_created:
                        try:
                            self.shared_device = hid.Device()
                            self.shared_device.open(vid, pid)
                            device_created = True
                        except Exception as e:
                            logging.debug(f"hid.Device() failed: {e}")
                            self.shared_device = None
                    
                    if not device_created or self.shared_device is None:
                        logging.error("Failed to create shared HID device with any method")
                        return None
                    
                    logging.debug("Shared HID device created successfully")
                except Exception as e:
                    logging.error(f"Error creating shared HID device: {e}")
                    return None
            
            return self.shared_device
    
    def _release_shared_device(self):
        """Release shared device (called when RPM monitoring stops)"""
        with self.device_lock:
            if self.shared_device:
                try:
                    if hasattr(self.shared_device, 'close'):
                        self.shared_device.close()
                    self.shared_device = None
                    logging.debug("Shared HID device released")
                except Exception as e:
                    logging.error(f"Error releasing shared HID device: {e}")
    
    def start_rpm_monitoring(self, callback=None):
        """Start monitoring RPM data from the device"""
        logging.debug(f"start_rpm_monitoring called with callback: {callback is not None}")
        if callback:
            self.rpm_monitor.add_callback(callback)
        self.rpm_monitor.start_monitoring()
        logging.info("RPM monitoring started")
    
    def stop_rpm_monitoring(self):
        """Stop monitoring RPM data"""
        self.rpm_monitor.stop_monitoring()
        logging.info("RPM monitoring stopped")
    
    def get_current_rpm(self):
        """Get the current RPM value"""
        return self.rpm_monitor.get_current_rpm()
    
    def add_rpm_callback(self, callback):
        """Add a callback for RPM updates"""
        self.rpm_monitor.add_callback(callback)
    
