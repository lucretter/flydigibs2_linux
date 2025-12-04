import logging
import threading
import time

# Import RPM monitor with fallback for packaging
try:
    from .rpm_monitor import RPMMonitor
except ImportError:
    from rpm_monitor import RPMMonitor

# Try different ways to import hidapi
try:
    import hid
except ImportError:
    try:
        import hidapi as hid
    except ImportError:
        hid = None

# Also try to import hidapi directly for low-level access
try:
    import hidapi
    HIDAPI_DIRECT = True
except ImportError:
    hidapi = None
    HIDAPI_DIRECT = False

class BS2ProController:
    def __init__(self):
        # Collect HID library metadata (keep logs concise)
        self.hid_info = {
            'available': hid is not None,
            'module': getattr(hid, '__name__', None) if hid is not None else None,
            'location': getattr(hid, '__file__', None) if hid is not None else None,
            'version': getattr(hid, '__version__', None) if hid is not None else None,
            'direct_hidapi': HIDAPI_DIRECT,
        }

        if self.hid_info['available']:
            # Keep this at DEBUG level so normal startup stays concise
            logging.debug(
                f"HID library available: module={self.hid_info['module']} "
                f"version={self.hid_info['version'] or 'unknown'} "
                f"location={self.hid_info['location'] or 'unknown'}"
            )
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
            return None, None, None
        
        # Known Flydigi vendor IDs (can be extended if needed)
        FLYDIGI_VENDOR_IDS = [
            0x37d7,  # Flydigi vendor ID
        ]
        
        try:
            devices = hid.enumerate()
            logging.debug(f"Enumerating {len(devices)} HID devices...")
            for d in devices:
                # Handle both dictionary-style and attribute-style access for different hidapi versions
                product_string = ""
                manufacturer_string = ""
                vendor_id = None
                product_id = None
                device_path = None
                
                # Check if it's a dictionary (most common case)
                if isinstance(d, dict):
                    product_string = d.get("product_string", "")
                    manufacturer_string = d.get("manufacturer_string", "")
                    vendor_id = d.get("vendor_id")
                    product_id = d.get("product_id")
                    device_path = d.get("path")
                else:
                    # Try attribute access for object-style access
                    try:
                        product_string = getattr(d, 'product_string', '')
                        manufacturer_string = getattr(d, 'manufacturer_string', '')
                        vendor_id = getattr(d, 'vendor_id', None)
                        product_id = getattr(d, 'product_id', None)
                        device_path = getattr(d, 'path', None)
                    except (AttributeError, TypeError):
                        # Skip this device if we can't access its info
                        continue
                
                # Normalize strings for comparison (case-insensitive)
                product_upper = product_string.upper() if product_string else ""
                manufacturer_upper = manufacturer_string.upper() if manufacturer_string else ""
                
                # Log all devices in verbose mode for debugging
                logging.debug(f"HID device: VID=0x{vendor_id:04x}, PID=0x{product_id:04x}, "
                           f"manufacturer='{manufacturer_string}', product='{product_string}', path={device_path}")
                
                # Detection heuristics (in order of preference):
                # 1. Product string contains "BS2" (catches BS2, BS2PRO, BS2 Pro, etc.)
                # 2. Manufacturer is "Flydigi" AND product contains "BS2"
                # 3. Manufacturer is "Flydigi" (fallback for any Flydigi device)
                # 4. Vendor ID matches known Flydigi vendor IDs AND product contains "BS2"
                
                is_bs2_product = "BS2" in product_upper if product_upper else False
                is_flydigi_manufacturer = "FLYDIGI" in manufacturer_upper if manufacturer_upper else False
                is_flydigi_vendor = vendor_id in FLYDIGI_VENDOR_IDS if vendor_id is not None else False
                
                # Primary detection: Product name contains "BS2"
                if is_bs2_product:
                    try:
                        vid_hex = f"0x{vendor_id:04x}" if vendor_id is not None else str(vendor_id)
                        pid_hex = f"0x{product_id:04x}" if product_id is not None else str(product_id)
                    except Exception:
                        vid_hex = vendor_id
                        pid_hex = product_id
                    logging.info(f"BS2Pro device detected (by product name): VID={vid_hex}, PID={pid_hex}, "
                               f"manufacturer='{manufacturer_string}', product='{product_string}', path={device_path}")
                    return vendor_id, product_id, device_path
                
                # Secondary detection: Flydigi manufacturer + BS2 product
                if is_flydigi_manufacturer and is_bs2_product:
                    try:
                        vid_hex = f"0x{vendor_id:04x}" if vendor_id is not None else str(vendor_id)
                        pid_hex = f"0x{product_id:04x}" if product_id is not None else str(product_id)
                    except Exception:
                        vid_hex = vendor_id
                        pid_hex = product_id
                    logging.info(f"BS2Pro device detected (by manufacturer + product): VID={vid_hex}, PID={pid_hex}, "
                               f"manufacturer='{manufacturer_string}', product='{product_string}', path={device_path}")
                    return vendor_id, product_id, device_path
                
                # Tertiary detection: Flydigi vendor ID + BS2 product (when manufacturer string unavailable)
                if is_flydigi_vendor and is_bs2_product:
                    try:
                        vid_hex = f"0x{vendor_id:04x}" if vendor_id is not None else str(vendor_id)
                        pid_hex = f"0x{product_id:04x}" if product_id is not None else str(product_id)
                    except Exception:
                        vid_hex = vendor_id
                        pid_hex = product_id
                    logging.info(f"BS2Pro device detected (by vendor ID + product): VID={vid_hex}, PID={pid_hex}, "
                               f"manufacturer='{manufacturer_string}', product='{product_string}', path={device_path}")
                    return vendor_id, product_id, device_path
                
                # Last resort: Flydigi manufacturer only (very permissive, logs warning)
                if is_flydigi_manufacturer:
                    try:
                        vid_hex = f"0x{vendor_id:04x}" if vendor_id is not None else str(vendor_id)
                        pid_hex = f"0x{product_id:04x}" if product_id is not None else str(product_id)
                    except Exception:
                        vid_hex = vendor_id
                        pid_hex = product_id
                    logging.warning(f"BS2Pro device detected (by manufacturer only - may be incorrect): "
                                  f"VID={vid_hex}, PID={pid_hex}, manufacturer='{manufacturer_string}', "
                                  f"product='{product_string}', path={device_path}")
                    return vendor_id, product_id, device_path
                
                # Final fallback: Flydigi vendor ID only (when strings are empty/unavailable)
                # This handles cases where HID device doesn't expose product/manufacturer strings
                if is_flydigi_vendor and vendor_id is not None and product_id is not None:
                    try:
                        vid_hex = f"0x{vendor_id:04x}" if vendor_id is not None else str(vendor_id)
                        pid_hex = f"0x{product_id:04x}" if product_id is not None else str(product_id)
                    except Exception:
                        vid_hex = vendor_id
                        pid_hex = product_id
                    logging.info(f"BS2Pro device detected (by vendor ID only - strings unavailable): "
                               f"VID={vid_hex}, PID={pid_hex}, manufacturer='{manufacturer_string}', "
                               f"product='{product_string}', path={device_path}")
                    return vendor_id, product_id, device_path
            
            logging.debug("BS2Pro device not found in HID enumeration")
            return None, None, None
        except Exception as e:
            logging.error(f"Error enumerating HID devices: {e}")
            return None, None, None

    def startup_summary(self):
        """Log a concise startup summary with important runtime info.

        This avoids spamming the normal logs with repetitive Qt/debug info
        while surfacing the most important bits (HID availability and
        detected device info).
        """
        lines = []
        lines.append("Application startup summary:")
        lines.append(f"  HID library: {'available' if self.hid_info['available'] else 'missing'}")
        if self.hid_info['available']:
            lines.append(f"    module: {self.hid_info['module']}")
            lines.append(f"    version: {self.hid_info['version'] or 'unknown'}")
            if self.hid_info['location']:
                lines.append(f"    location: {self.hid_info['location']}")
        lines.append(f"  HIDAPI direct available: {HIDAPI_DIRECT}")

        vid, pid, path = self.detect_bs2pro()
        if vid is not None and pid is not None:
            try:
                lines.append(f"  BS2Pro device: VID=0x{vid:04x}, PID=0x{pid:04x}")
            except Exception:
                lines.append(f"  BS2Pro device: VID={vid}, PID={pid}")
            if path:
                lines.append(f"    path: {path}")
        else:
            lines.append("  BS2Pro device: not detected")

        logging.info('\n'.join(lines))

    def send_command(self, hex_cmd, status_callback=None):
        if hid is None:
            if status_callback:
                status_callback("❌ HID library not available", "danger")
            logging.error("HID library not available")
            return False
            
        # Retry logic for device access conflicts
        for attempt in range(5):
            try:
                # Use shared device if available, otherwise create temporary one
                dev = self._get_shared_device()
                if dev:
                    logging.debug("Using shared device for command")
                    payload = bytes.fromhex(hex_cmd)
                    
                    # Handle direct hidapi access
                    if isinstance(dev, dict) and dev.get('type') == 'direct':
                        if HIDAPI_DIRECT:
                            # Write the command
                            bytes_written = hidapi.hidapi.hid_write(dev['handle'], payload, len(payload))
                            if bytes_written > 0:
                                # Read response
                                response_buffer = hidapi.ffi.new("unsigned char[]", 32)
                                bytes_read = hidapi.hidapi.hid_read_timeout(dev['handle'], response_buffer, 32, 1000)
                                logging.debug(f"HID write: {bytes_written} bytes, read: {bytes_read} bytes")
                    else:
                        # Regular hidapi device
                        dev.write(payload)
                        # Try with timeout first, fallback to without timeout
                        try:
                            dev.read(32, timeout=1000)
                        except TypeError:
                            # Some versions don't support timeout parameter
                            dev.read(32)
                else:
                    # Fallback to creating temporary device
                    vid, pid, device_path = self.detect_bs2pro()
                    if vid is None or pid is None:
                        if status_callback:
                            status_callback("❌ BS2PRO device not found", "danger")
                        logging.error("BS2PRO device not found.")
                        return False
                    
                    # Try different hidapi APIs based on version, starting with most compatible
                    device_opened = False
                    
                    # Method 0: Try device() constructor with path (most reliable for BS2Pro)
                    if hasattr(hid, 'device') and device_path and not device_opened:
                        try:
                            dev = hid.device()
                            dev.open_path(device_path)
                            device_opened = True
                            payload = bytes.fromhex(hex_cmd)
                            dev.write(payload)
                            # Try without timeout since this hidapi version doesn't support it
                            try:
                                dev.read(32)
                            except Exception:
                                pass  # Read may not be necessary for command sending
                            dev.close()
                            logging.debug("Used device() + open_path() successfully")
                        except Exception as e:
                            logging.debug(f"device() + open_path() failed: {e}")
                    
                    # Method 1: Try direct hidapi low-level access
                    if HIDAPI_DIRECT and not device_opened:
                        try:
                            device_handle = hidapi.hidapi.hid_open(vid, pid, hidapi.ffi.NULL)
                            if device_handle != hidapi.ffi.NULL:
                                device_opened = True
                                payload = bytes.fromhex(hex_cmd)
                                # Write the command
                                bytes_written = hidapi.hidapi.hid_write(device_handle, payload, len(payload))
                                if bytes_written > 0:
                                    # Read response
                                    response_buffer = hidapi.ffi.new("unsigned char[]", 32)
                                    bytes_read = hidapi.hidapi.hid_read_timeout(device_handle, response_buffer, 32, 1000)
                                    logging.debug(f"HID write: {bytes_written} bytes, read: {bytes_read} bytes")
                                hidapi.hidapi.hid_close(device_handle)
                                logging.debug("Used direct hidapi low-level access successfully")
                        except Exception as e:
                            logging.debug(f"Direct hidapi access failed: {e}")
                    
                    # Method 2: Try hid.open() function
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
                    
                    # Method 3: Try device().open() (traditional approach)
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
                            logging.debug(f"hid.device().open() failed: {e}")
                    
                    # Skip Method 4 (Device class) as it's broken on this system
                    
                    if not device_opened:
                        if attempt < 4:  # Don't log error on last attempt
                            logging.debug(f"Failed to create shared HID device with any method, retrying in 200ms (attempt {attempt + 1}/5)")
                            time.sleep(0.2)
                            continue
                        else:
                            if status_callback:
                                status_callback("❌ Failed to open HID device", "danger")
                            logging.error("All HID device opening methods failed")
                            return False
                
                if status_callback:
                    status_callback("✅ Command sent successfully", "success")
                logging.info(f"Command sent: {hex_cmd}")
                return True
            except Exception as e:
                if attempt < 4:  # Don't log error on last attempt
                    logging.debug(f"Shared device not available, retrying in 200ms (attempt {attempt + 1}/5)")
                    time.sleep(0.2)
                    continue
                else:
                    if status_callback:
                        status_callback(f"⚠️ HID error: {e}", "danger")
                    logging.error(f"HID error: {e}")
                    return False
    
    def _get_shared_device(self):
        """Get shared HID device for both reading and writing"""
        with self.device_lock:
            if self.shared_device is None:
                try:
                    vid, pid, device_path = self.detect_bs2pro()
                    if vid is None or pid is None:
                        return None
                    
                    logging.debug(f"Creating shared HID device VID={vid:04x}, PID={pid:04x}")
                    if device_path:
                        logging.debug(f"Device path: {device_path}")
                    
                    # Try different hidapi APIs, starting with most compatible
                    device_created = False
                    
                    # Method 0: Try device() constructor with path (most reliable for BS2Pro)
                    if hasattr(hid, 'device') and device_path and not device_created:
                        try:
                            self.shared_device = hid.device()
                            self.shared_device.open_path(device_path)
                            device_created = True
                            logging.debug("Created shared device with device() + open_path()")
                        except Exception as e:
                            logging.debug(f"device() + open_path() failed: {e}")
                    
                    # Method 1: Try direct hidapi low-level access
                    if HIDAPI_DIRECT and not device_created:
                        try:
                            device_handle = hidapi.hidapi.hid_open(vid, pid, hidapi.ffi.NULL)
                            if device_handle != hidapi.ffi.NULL:
                                # For shared device, we'll store the handle differently
                                self.shared_device = {'handle': device_handle, 'type': 'direct'}
                                device_created = True
                                logging.debug("Created shared device with direct hidapi access")
                        except Exception as e:
                            logging.debug(f"Direct hidapi access failed: {e}")
                    
                    # Method 2: Try hid.open() function
                    if hasattr(hid, 'open') and not device_created:
                        try:
                            self.shared_device = hid.open(vid, pid)
                            if self.shared_device is not None:
                                device_created = True
                                logging.debug("Created shared device with hid.open()")
                        except Exception as e:
                            logging.debug(f"hid.open() failed: {e}")
                    
                    # Method 3: Try device().open() (traditional approach)
                    if hasattr(hid, 'device') and not device_created:
                        try:
                            self.shared_device = hid.device()
                            self.shared_device.open(vid, pid)
                            device_created = True
                            logging.debug("Created shared device with device().open()")
                        except Exception as e:
                            logging.debug(f"hid.device().open() failed: {e}")
                            self.shared_device = None
                    
                    # Skip Method 3 (Device class) as it's broken on this system
                    
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
                    # Handle direct hidapi access case
                    if isinstance(self.shared_device, dict) and self.shared_device.get('type') == 'direct':
                        if HIDAPI_DIRECT:
                            hidapi.hidapi.hid_close(self.shared_device['handle'])
                            logging.debug("Direct hidapi shared device closed")
                    elif hasattr(self.shared_device, 'close'):
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
    
