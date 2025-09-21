#!/usr/bin/env python3
"""
Tray Manager for BS2PRO Controller
Uses native Linux system tray with libappindicator
"""
import logging
import os
import subprocess
import time
import threading
import signal

class TrayManager:
    def __init__(self, root, gui_instance):
        self.root = root
        self.gui = gui_instance
        self.is_minimized = False
        self.tray_available = False
        self.notification_available = False
        self.native_tray = None
        
        # Check for native system tray support
        self._check_tray_support()
        
        # Check for notification support
        self._check_notification_support()
        
        # Always use simple tray manager for now (more reliable)
        try:
            from simple_tray_manager import SimpleTrayManager
            self.native_tray = SimpleTrayManager(root, gui_instance)
            logging.info("Simple tray manager initialized")
        except ImportError as e:
            logging.warning(f"Could not load simple tray manager: {e}")
            self.tray_available = False
        
        # Set up signal handlers for tray communication
        self._setup_signal_handlers()
        
        logging.info(f"Tray manager initialized - tray: {self.tray_available}, notifications: {self.notification_available}")
    
    def _check_tray_support(self):
        """Check if we can use tray functionality"""
        # We can always use the simple tray approach
        self.tray_available = True
        logging.info("Simple tray support available")
    
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
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for tray communication"""
        def signal_handler_show(signum, frame):
            logging.info("Received show window signal from tray")
            self.show_window()
        
        def signal_handler_toggle(signum, frame):
            logging.info("Received toggle smart mode signal from tray")
            self.toggle_smart_mode()
        
        def signal_handler_quit(signum, frame):
            logging.info("Received quit signal from tray")
            self.quit_app()
        
        # Set up signal handlers
        signal.signal(signal.SIGUSR1, signal_handler_show)
        signal.signal(signal.SIGUSR2, signal_handler_toggle)
        signal.signal(signal.SIGTERM, signal_handler_quit)
    
    def start_tray(self):
        """Start the tray functionality"""
        if self.native_tray:
            return self.native_tray.start_tray()
        else:
            # Fallback to simple taskbar minimization
            self.tray_available = True
            logging.info("Tray manager started (taskbar only)")
            return True
    
    def hide_window(self):
        """Hide the main window"""
        if self.native_tray and self.native_tray.is_tray_working():
            self.native_tray.hide_window()
        else:
            # Fallback to taskbar minimization
            try:
                self.root.iconify()
                self.is_minimized = True
                logging.info("Window minimized to taskbar")
                
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
            logging.info("Window restored")
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
        """Update tooltip"""
        if self.native_tray:
            self.native_tray.update_tray_tooltip(text)
    
    def is_window_minimized(self):
        """Check if window is minimized"""
        return self.is_minimized
    
    def is_tray_working(self):
        """Check if tray functionality is working"""
        if self.native_tray:
            return self.native_tray.is_tray_working()
        return self.tray_available
    
    def stop_tray(self):
        """Stop the tray functionality"""
        if self.native_tray:
            self.native_tray.stop_tray()
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