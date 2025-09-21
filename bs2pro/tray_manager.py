#!/usr/bin/env python3
"""
Tray Manager for BS2PRO Controller
Uses native Linux system tray without pystray dependency
"""
import logging
import os
import subprocess
import time
import threading

class TrayManager:
    def __init__(self, root, gui_instance):
        self.root = root
        self.gui = gui_instance
        self.is_minimized = False
        self.tray_available = False
        self.notification_available = False
        
        # Check for native system tray support
        self._check_tray_support()
        
        # Check for notification support
        self._check_notification_support()
        
        logging.info(f"Tray manager initialized - tray: {self.tray_available}, notifications: {self.notification_available}")
    
    def _check_tray_support(self):
        """Check if we can use native system tray"""
        # We can always minimize to taskbar, so this is always available
        self.tray_available = True
    
    def _check_notification_support(self):
        """Check if we can send system notifications"""
        try:
            subprocess.run(['notify-send', '--version'], 
                         capture_output=True, check=True, timeout=5)
            self.notification_available = True
            logging.info("System notifications available")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.notification_available = False
            logging.warning("System notifications not available")
    
    def start_tray(self):
        """Start the tray functionality"""
        self.tray_available = True
        logging.info("Tray manager started")
        return True
    
    def hide_window(self):
        """Hide the main window to taskbar"""
        try:
            # Minimize to taskbar
            self.root.iconify()
            self.is_minimized = True
            logging.info("Window minimized to taskbar")
            
            # Send notification about how to restore
            if self.notification_available:
                self._send_notification(
                    "BS2PRO Controller",
                    "App minimized to taskbar. Click the taskbar icon to restore.",
                    timeout=5000
                )
            else:
                logging.info("No notification system available - user should check taskbar")
                
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
                '--icon=applications-system',
                title,
                message
            ], timeout=5)
        except Exception as e:
            logging.warning(f"Could not send notification: {e}")
    
    def update_tray_tooltip(self, text):
        """Update tooltip (not applicable for native tray)"""
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
        logging.info("Tray manager stopped")
    
    def toggle_smart_mode(self, icon=None, item=None):
        """Toggle smart mode"""
        if hasattr(self.gui, 'toggle_smart_mode'):
            self.gui.toggle_smart_mode()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        if hasattr(self.gui, 'force_exit'):
            self.gui.force_exit()
        else:
            self.root.quit()