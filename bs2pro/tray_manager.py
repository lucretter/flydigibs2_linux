#!/usr/bin/env python3
"""
System Tray Manager for BS2PRO Controller
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
import os

class TrayManager:
    def __init__(self, root, gui_instance):
        self.root = root
        self.gui = gui_instance
        self.tray_icon = None
        self.is_minimized = False
        
        # Try to import pystray for system tray functionality
        try:
            import pystray
            from PIL import Image
            self.pystray = pystray
            self.PIL = Image
            self.tray_available = True
        except ImportError:
            self.tray_available = False
            logging.warning("pystray not available - system tray functionality disabled")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not self.tray_available:
            return False
        
        try:
            # Create a simple icon (you can replace this with your app icon)
            icon_image = self._create_icon_image()
            
            # Create menu items
            menu = self.pystray.Menu(
                self.pystray.MenuItem("Show BS2PRO Controller", self.show_window),
                self.pystray.MenuItem("Smart Mode", self.toggle_smart_mode),
                self.pystray.MenuItem("Exit", self.quit_app)
            )
            
            # Create tray icon
            self.tray_icon = self.pystray.Icon(
                "bs2pro_controller",
                icon_image,
                "BS2PRO Controller",
                menu
            )
            
            return True
        except Exception as e:
            logging.error(f"Error creating tray icon: {e}")
            return False
    
    def _create_icon_image(self):
        """Create a simple icon image"""
        try:
            # Try to load the app icon
            icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
            if os.path.exists(icon_path):
                return self.PIL.Image.open(icon_path)
        except Exception:
            pass
        
        # Create a simple colored square as fallback
        return self.PIL.Image.new('RGB', (64, 64), color='blue')
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.after(0, self._show_window)
    
    def _show_window(self):
        """Show window (called from main thread)"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_minimized = False
    
    def hide_window(self):
        """Hide the main window to system tray"""
        if self.tray_available and self.tray_icon:
            self.root.withdraw()
            self.is_minimized = True
        else:
            # Fallback: minimize to taskbar
            self.root.iconify()
            self.is_minimized = True
    
    def toggle_smart_mode(self, icon=None, item=None):
        """Toggle smart mode from tray menu"""
        self.root.after(0, self._toggle_smart_mode)
    
    def _toggle_smart_mode(self):
        """Toggle smart mode (called from main thread)"""
        if hasattr(self.gui, 'toggle_smart_mode'):
            self.gui.toggle_smart_mode()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.root.after(0, self._quit_app)
    
    def _quit_app(self):
        """Quit app (called from main thread)"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
    
    def start_tray(self):
        """Start the system tray icon"""
        if self.tray_available and self.create_tray_icon():
            # Run tray icon in a separate thread
            import threading
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            return True
        return False
    
    def stop_tray(self):
        """Stop the system tray icon"""
        if self.tray_icon:
            self.tray_icon.stop()
    
    def update_tray_tooltip(self, text):
        """Update the tray icon tooltip"""
        if self.tray_icon:
            self.tray_icon.title = text
    
    def is_window_minimized(self):
        """Check if window is minimized to tray"""
        return self.is_minimized
