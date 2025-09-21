#!/usr/bin/env python3
"""Test script for system tray functionality"""

import sys
import os
import logging
import time
import threading

# Add the bs2pro directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bs2pro'))

try:
    import tkinter
    import tkinter.ttk
    # Mock customtkinter for testing
    sys.modules['customtkinter'] = type(sys)('customtkinter')
    sys.modules['customtkinter'].CTk = tkinter.Tk
    sys.modules['customtkinter'].CTkFrame = tkinter.Frame
    sys.modules['customtkinter'].CTkButton = tkinter.Button
    sys.modules['customtkinter'].CTkLabel = tkinter.Label
    sys.modules['customtkinter'].CTkComboBox = tkinter.ttk.Combobox
    sys.modules['customtkinter'].CTkSwitch = tkinter.Checkbutton
    sys.modules['customtkinter'].CTkToplevel = tkinter.Toplevel
    sys.modules['customtkinter'].CTkScrollableFrame = tkinter.Frame
    sys.modules['customtkinter'].CTkEntry = tkinter.Entry
    sys.modules['customtkinter'].CTkTextbox = tkinter.Text
    sys.modules['customtkinter'].CTkCanvas = tkinter.Canvas
    sys.modules['customtkinter'].CTkScrollbar = tkinter.Scrollbar
    sys.modules['customtkinter'].StringVar = tkinter.StringVar
    sys.modules['customtkinter'].BooleanVar = tkinter.BooleanVar
    sys.modules['customtkinter'].IntVar = tkinter.IntVar
    sys.modules['customtkinter'].set_appearance_mode = lambda x: None
    sys.modules['customtkinter'].set_default_color_theme = lambda x: None
    
    # Mock other dependencies
    sys.modules['cpu_monitor'] = type(sys)('cpu_monitor')
    sys.modules['cpu_monitor'].CPUMonitor = type('CPUMonitor', (), {})
    sys.modules['smart_mode'] = type(sys)('smart_mode')
    sys.modules['smart_mode'].SmartModeManager = type('SmartModeManager', (), {})
    
    from tray_manager import TrayManager
    import tkinter as tk
    print("✅ Tray manager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import tray manager: {e}")
    sys.exit(1)

def test_tray():
    """Test the tray functionality"""
    print("🧪 Testing system tray functionality...")
    
    # Create a simple tkinter window
    root = tk.Tk()
    root.title("Tray Test")
    root.geometry("300x200")
    
    # Create a simple GUI instance mock
    class MockGUI:
        def toggle_smart_mode(self):
            print("🔄 Smart mode toggled from tray!")
    
    gui = MockGUI()
    
    # Create tray manager
    tray_manager = TrayManager(root, gui)
    
    # Test tray creation
    print("🔧 Creating tray icon...")
    if tray_manager.create_tray_icon():
        print("✅ Tray icon created successfully")
    else:
        print("❌ Failed to create tray icon")
        return
    
    # Test tray start
    print("🚀 Starting tray...")
    if tray_manager.start_tray():
        print("✅ Tray started successfully")
    else:
        print("❌ Failed to start tray")
        return
    
    # Add a test button to the window
    def test_show():
        print("🖼️ Show window button clicked")
        tray_manager.show_window()
    
    def test_hide():
        print("👁️ Hide window button clicked")
        tray_manager.hide_window()
    
    tk.Button(root, text="Test Show Window", command=test_show).pack(pady=10)
    tk.Button(root, text="Test Hide Window", command=test_hide).pack(pady=10)
    tk.Button(root, text="Exit", command=root.quit).pack(pady=10)
    
    print("🎯 Test window created. Try clicking the tray icon!")
    print("   - Left click should show/hide the window")
    print("   - Right click should show the menu")
    print("   - Check the console for debug messages")
    
    # Start the GUI
    root.mainloop()
    
    # Cleanup
    tray_manager.stop_tray()
    print("🧹 Test completed")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    test_tray()
