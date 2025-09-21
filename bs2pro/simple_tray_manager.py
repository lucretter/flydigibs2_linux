#!/usr/bin/env python3
"""
Simple Tray Manager for BS2PRO Controller
Fallback implementation when pystray is not available or not working
"""
import logging
import os
import subprocess
import time

class SimpleTrayManager:
    def __init__(self, root, gui_instance):
        self.root = root
        self.gui = gui_instance
        self.is_minimized = False
        self.tray_available = False
        
        # Check if we can use system notifications
        self.notification_available = self._check_notification_support()
        
        if self.notification_available:
            logging.info("Simple tray manager initialized with notification support")
        else:
            logging.warning("Simple tray manager initialized without notification support")
    
    def _check_notification_support(self):
        """Check if we can send system notifications"""
        try:
            # Try to send a test notification
            subprocess.run(['notify-send', '--version'], 
                         capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def start_tray(self):
        """Start the simple tray functionality"""
        self.tray_available = True
        logging.info("Simple tray manager started")
        return True
    
    def hide_window(self):
        """Hide the main window (minimize to taskbar)"""
        try:
            self.root.iconify()  # Minimize to taskbar
            self.is_minimized = True
            logging.info("Window minimized to taskbar")
            
            # Send notification about how to restore
            if self.notification_available:
                self._send_notification(
                    "BS2PRO Controller",
                    "App minimized to taskbar. Click the taskbar icon to restore.",
                    timeout=5000
                )
        except Exception as e:
            logging.error(f"Error hiding window: {e}")
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.is_minimized = False
            logging.info("Window restored from taskbar")
        except Exception as e:
            logging.error(f"Error showing window: {e}")
    
    def _send_notification(self, title, message, timeout=3000):
        """Send a system notification"""
        if not self.notification_available:
            return
        
        try:
            subprocess.run([
                'notify-send',
                '--app-name=BS2PRO Controller',
                f'--expire-time={timeout}',
                title,
                message
            ], timeout=5)
        except Exception as e:
            logging.warning(f"Could not send notification: {e}")
    
    def update_tray_tooltip(self, text):
        """Update tooltip (not applicable for simple tray)"""
        pass
    
    def is_window_minimized(self):
        """Check if window is minimized"""
        return self.is_minimized
    
    def is_tray_working(self):
        """Check if tray functionality is working"""
        return self.tray_available
    
    def stop_tray(self):
        """Stop the tray functionality"""
        self.tray_available = False
        logging.info("Simple tray manager stopped")
    
    def toggle_smart_mode(self, icon=None, item=None):
        """Toggle smart mode (not applicable for simple tray)"""
        if hasattr(self.gui, 'toggle_smart_mode'):
            self.gui.toggle_smart_mode()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        if hasattr(self.gui, 'force_exit'):
            self.gui.force_exit()
        else:
            self.root.quit()
