import logging

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
                dev.read(32, timeout=1000)
                dev.close()
            elif hasattr(hid, 'device'):
                # hidapi 0.14.0.post4 API (lowercase device)
                dev = hid.device()
                dev.open(vid, pid)
                payload = bytes.fromhex(hex_cmd)
                dev.write(payload)
                dev.read(32, timeout=1000)
                dev.close()
            elif hasattr(hid, 'open'):
                # Old hidapi API (0.13 and earlier)
                dev = hid.open(vid, pid)
                if dev is None:
                    raise Exception("Failed to open HID device")
                payload = bytes.fromhex(hex_cmd)
                dev.write(payload)
                dev.read(32, timeout=1000)
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
