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
        pass

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
            
            # Check if hid has Device attribute
            if not hasattr(hid, 'Device'):
                if status_callback:
                    status_callback("❌ HID Device not available", "danger")
                logging.error("HID Device not available - hidapi version issue")
                return False
                
            dev = hid.Device(vid=vid, pid=pid)
            payload = bytes.fromhex(hex_cmd)
            dev.write(payload)
            dev.read(32, timeout=1000)
            dev.close()
            if status_callback:
                status_callback("✅ Command sent successfully", "success")
            logging.info(f"Command sent: {hex_cmd}")
            return True
        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ HID error: {e}", "danger")
            logging.error(f"HID error: {e}")
            return False
