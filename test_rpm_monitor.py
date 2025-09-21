#!/usr/bin/env python3
"""
Test script for RPM monitoring functionality
This script helps debug the RPM data capture from BS2Pro
"""
import sys
import os
import time
import logging

# Add the current directory to the path so we can import bs2pro
sys.path.insert(0, os.path.dirname(__file__))

# Import the modules
from bs2pro.controller import BS2ProController

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def rpm_callback(rpm):
    """Callback function for RPM updates"""
    print(f"🔄 RPM Update: {rpm} RPM")

def main():
    print("BS2Pro RPM Monitor Test")
    print("=" * 40)
    
    # Create controller
    controller = BS2ProController()
    
    # Check if device is detected
    vid, pid = controller.detect_bs2pro()
    if vid is None or pid is None:
        print("❌ BS2Pro device not found!")
        print("Please make sure your BS2Pro is connected and udev rules are installed.")
        return
    
    print(f"✅ BS2Pro detected: VID={vid:04x}, PID={pid:04x}")
    
    # Add RPM callback
    controller.add_rpm_callback(rpm_callback)
    
    # Start RPM monitoring
    print("🚀 Starting RPM monitoring...")
    controller.start_rpm_monitoring()
    
    try:
        print("📊 Monitoring RPM data... (Press Ctrl+C to stop)")
        print("💡 Try changing the fan speed on your BS2Pro to see RPM updates")
        
        # Monitor for 60 seconds or until interrupted
        start_time = time.time()
        while time.time() - start_time < 60:
            current_rpm = controller.get_current_rpm()
            if current_rpm > 0:
                print(f"📈 Current RPM: {current_rpm}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitoring...")
    finally:
        # Stop monitoring
        controller.stop_rpm_monitoring()
        print("✅ RPM monitoring stopped")

if __name__ == "__main__":
    main()
