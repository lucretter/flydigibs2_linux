#!/usr/bin/env python3
"""
Test script for Smart Mode functionality
This script tests the smart mode components without requiring the full GUI
"""

import sys
import os
import time
import json

# Add the bs2pro directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bs2pro'))

def test_cpu_monitor():
    """Test CPU temperature monitoring"""
    print("🌡️  Testing CPU Monitor...")
    
    try:
        from cpu_monitor import CPUMonitor
        
        monitor = CPUMonitor()
        temp = monitor.get_temperature()
        
        if temp > 0:
            print(f"✅ CPU Temperature: {temp:.1f}°C")
            return True
        else:
            print("❌ Could not read CPU temperature")
            return False
            
    except Exception as e:
        print(f"❌ CPU Monitor error: {e}")
        return False

def test_smart_mode():
    """Test Smart Mode configuration"""
    print("\n🤖 Testing Smart Mode...")
    
    try:
        from smart_mode import SmartModeManager
        
        manager = SmartModeManager()
        
        # Test default configuration
        print(f"✅ Smart Mode enabled: {manager.is_smart_mode_enabled()}")
        print(f"✅ Temperature ranges: {len(manager.temperature_ranges)}")
        
        # Test RPM calculation
        test_temps = [45, 55, 65, 75, 85]
        for temp in test_temps:
            rpm = manager.get_rpm_for_temperature(temp)
            range_info = manager.get_range_for_temperature(temp)
            print(f"   {temp}°C → {rpm} RPM ({range_info['description'] if range_info else 'Unknown'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Smart Mode error: {e}")
        return False

def test_tray_manager():
    """Test System Tray functionality"""
    print("\n🎯 Testing Tray Manager...")
    
    try:
        from tray_manager import TrayManager
        
        # Create a dummy root window for testing
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        class DummyGUI:
            def toggle_smart_mode(self):
                print("   Toggle smart mode called")
            def center_window(self):
                print("   Center window called")
            def cleanup(self):
                print("   Cleanup called")
        
        gui = DummyGUI()
        tray_manager = TrayManager(root, gui)
        
        print(f"✅ Tray available: {tray_manager.tray_available}")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Tray Manager error: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    print("📦 Testing Dependencies...")
    
    dependencies = [
        ('customtkinter', 'CustomTkinter GUI library'),
        ('pystray', 'System tray functionality'),
        ('PIL', 'Pillow image processing'),
        ('psutil', 'System monitoring'),
        ('hidapi', 'HID device communication')
    ]
    
    all_available = True
    
    for module, description in dependencies:
        try:
            if module == 'PIL':
                import PIL
                print(f"✅ {description}: Available")
            else:
                __import__(module)
                print(f"✅ {description}: Available")
        except ImportError:
            print(f"❌ {description}: Missing")
            all_available = False
    
    return all_available

def main():
    """Run all tests"""
    print("🚀 Testing Smart Mode Components\n")
    
    # Test dependencies first
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n⚠️  Some dependencies are missing. Install them with:")
        print("   pip3 install customtkinter pystray pillow psutil hidapi")
        print("\n   Or test via GitHub Actions build instead.")
        return
    
    # Test individual components
    cpu_ok = test_cpu_monitor()
    smart_ok = test_smart_mode()
    tray_ok = test_tray_manager()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"   CPU Monitor: {'✅' if cpu_ok else '❌'}")
    print(f"   Smart Mode: {'✅' if smart_ok else '❌'}")
    print(f"   Tray Manager: {'✅' if tray_ok else '❌'}")
    
    if all([deps_ok, cpu_ok, smart_ok, tray_ok]):
        print("\n🎉 All tests passed! Smart Mode is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
