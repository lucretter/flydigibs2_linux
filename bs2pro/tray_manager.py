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
            self.Image = Image
            self.tray_available = True
            logging.info("System tray dependencies loaded successfully")
        except ImportError as e:
            self.tray_available = False
            logging.warning(f"pystray not available - system tray functionality disabled: {e}")
    
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
                self.pystray.MenuItem("Toggle Smart Mode", self.toggle_smart_mode),
                self.pystray.MenuItem("Exit", self.quit_app)
            )
            
            # Create tray icon with click handler
            self.tray_icon = self.pystray.Icon(
                "bs2pro_controller",
                icon_image,
                "BS2PRO Controller",
                menu,
                default_action=self.show_window  # Left-click action
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
                logging.info(f"Loading app icon from: {icon_path}")
                icon = self.Image.open(icon_path)
                # Resize to standard tray icon size (16x16 or 32x32)
                icon = icon.resize((32, 32), self.Image.Resampling.LANCZOS)
                return icon
        except Exception as e:
            logging.warning(f"Could not load app icon: {e}")
        
        # Create a simple colored square as fallback
        logging.info("Creating fallback icon")
        return self.Image.new('RGB', (32, 32), color='blue')
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        logging.info("Show window requested from tray")
        self.root.after(0, self._show_window)
    
    def _show_window(self):
        """Show window (called from main thread)"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.is_minimized = False
            logging.info("Window shown from tray")
        except Exception as e:
            logging.error(f"Error showing window: {e}")
    
    def hide_window(self):
        """Hide the main window to system tray"""
        if self.tray_available and self.tray_icon:
            try:
                self.root.withdraw()
                self.is_minimized = True
                logging.info("Window hidden to system tray")
            except Exception as e:
                logging.error(f"Error hiding window to tray: {e}")
                # Fallback: minimize to taskbar
                self.root.iconify()
                self.is_minimized = True
        else:
            # Fallback: minimize to taskbar
            self.root.iconify()
            self.is_minimized = True
            logging.warning("System tray not available - minimizing to taskbar instead")
    
    def toggle_smart_mode(self, icon=None, item=None):
        """Toggle smart mode from tray menu"""
        self.root.after(0, self._toggle_smart_mode)
    
    def _toggle_smart_mode(self):
        """Toggle smart mode (called from main thread)"""
        if hasattr(self.gui, 'toggle_smart_mode'):
            self.gui.toggle_smart_mode()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        logging.info("Quit app requested from tray")
        self.root.after(0, self._quit_app)
    
    def _quit_app(self):
        """Quit app (called from main thread)"""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
            # Use the GUI's force_exit method to properly clean up
            if hasattr(self.gui, 'force_exit'):
                self.gui.force_exit()
            else:
                self.root.quit()
            logging.info("App quit from tray")
        except Exception as e:
            logging.error(f"Error quitting app: {e}")
    
    def start_tray(self):
        """Start the system tray icon"""
        if not self.tray_available:
            logging.warning("System tray not available - pystray not installed")
            return False
            
        if not self.create_tray_icon():
            logging.error("Failed to create tray icon")
            return False
            
        try:
            # Run tray icon in a separate thread
            import threading
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            logging.info("System tray icon started successfully")
            return True
        except Exception as e:
            logging.error(f"Error starting tray icon: {e}")
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
    
    def is_tray_working(self):
        """Check if system tray is working properly"""
        return self.tray_available and self.tray_icon is not None
