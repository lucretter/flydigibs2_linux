import logging

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
        self.rpm_monitor.set_shared_device_access(self.detect_bs2pro, self._get_shared_device, self._close_shared_device)

    def detect_bs2pro(self):
        if hid is None:
            logging.error("HID library not available")
            return None, None
        
        try:
            devices = hid.enumerate()
            for d in devices:
                if "BS2PRO" in d.get("product_string", ""):
                    return d["vendor_id"], d["product_id"]
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
            vid, pid = self.detect_bs2pro()
            if vid is None or pid is None:
                if status_callback:
                    status_callback("❌ BS2PRO device not found", "danger")
                logging.error("BS2PRO device not found.")
                return False
            
            # Try different hidapi APIs based on version
            if hasattr(hid, 'Device'):
                # New hidapi API (0.14+)
                dev = hid.Device(vid=vid, pid=pid)
                payload = bytes.fromhex(hex_cmd)
                dev.write(payload)
                # Try with timeout first, fallback to without timeout
                try:
                    dev.read(32, timeout=1000)
                except TypeError:
                    # Some versions don't support timeout parameter
                    dev.read(32)
                dev.close()
            elif hasattr(hid, 'device'):
                # hidapi 0.14.0.post4 API (lowercase device)
                dev = hid.device()
                dev.open(vid, pid)
                payload = bytes.fromhex(hex_cmd)
                dev.write(payload)
                # Try with timeout first, fallback to without timeout
                try:
                    dev.read(32, timeout=1000)
                except TypeError:
                    # Some versions don't support timeout parameter
                    dev.read(32)
                dev.close()
            elif hasattr(hid, 'open'):
                # Old hidapi API (0.13 and earlier)
                dev = hid.open(vid, pid)
                if dev is None:
                    raise Exception("Failed to open HID device")
                payload = bytes.fromhex(hex_cmd)
                dev.write(payload)
                # Try with timeout first, fallback to without timeout
                try:
                    dev.read(32, timeout=1000)
                except TypeError:
                    # Some versions don't support timeout parameter
                    dev.read(32)
                dev.close()
            else:
                if status_callback:
                    status_callback("❌ Unsupported hidapi version", "danger")
                logging.error("Unsupported hidapi version - no Device, device, or open method")
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
        """Get or create shared HID device for continuous access"""
        if self.shared_device is not None:
            return self.shared_device
            
        if hid is None:
            return None
            
        try:
            vid, pid = self.detect_bs2pro()
            if vid is None or pid is None:
                return None
            
            logging.info(f"Creating shared HID device VID={vid:04x}, PID={pid:04x}")
            if hasattr(hid, 'Device'):
                self.shared_device = hid.Device(vid=vid, pid=pid)
            elif hasattr(hid, 'device'):
                self.shared_device = hid.device()
                self.shared_device.open(vid, pid)
            elif hasattr(hid, 'open'):
                self.shared_device = hid.open(vid, pid)
            else:
                return None
            
            logging.info("Shared HID device created successfully")
            return self.shared_device
        except Exception as e:
            logging.error(f"Error creating shared HID device: {e}")
            return None
    
    def _close_shared_device(self, device):
        """Close shared HID device (only called when RPM monitoring stops)"""
        if self.shared_device and self.shared_device == device:
            try:
                if hasattr(self.shared_device, 'close'):
                    self.shared_device.close()
                self.shared_device = None
                logging.info("Shared HID device closed")
            except Exception as e:
                logging.error(f"Error closing shared HID device: {e}")
    
    def start_rpm_monitoring(self, callback=None):
        """Start monitoring RPM data from the device"""
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
    
    def remove_rpm_callback(self, callback):
        """Remove a callback for RPM updates"""
        self.rpm_monitor.remove_callback(callback)
