#!/usr/bin/env python3
"""
Simple Tray Manager for BS2PRO Controller
Uses a simple approach without complex system dependencies
"""
import logging
import os
import subprocess
import time
import threading
import tkinter as tk
from tkinter import messagebox

class SimpleTrayManager:
    def __init__(self, root, gui_instance):
        self.root = root
        self.gui = gui_instance
        self.is_minimized = False
        self.tray_available = True
        self.notification_available = False
        self.tray_window = None
        
        # Check for notification support
        self._check_notification_support()
        
        logging.info(f"Simple tray manager initialized - notifications: {self.notification_available}")
    
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
        logging.info("Simple tray manager started")
        return True
    
    def hide_window(self):
        """Hide the main window and show a small control window"""
        try:
            # Hide the main window
            self.root.withdraw()
            self.is_minimized = True
            logging.info("Window hidden to tray")
            
            # Create a small control window
            self._create_tray_window()
            
            # Send notification
            if self.notification_available:
                self._send_notification(
                    "BS2PRO Controller",
                    "App minimized. Use the small control window to restore.",
                    timeout=5000
                )
                
        except Exception as e:
            logging.error(f"Error hiding window: {e}")
    
    def _create_tray_window(self):
        """Create a small control window"""
        try:
            if self.tray_window and self.tray_window.winfo_exists():
                return
            
            # Create a small window
            self.tray_window = tk.Toplevel()
            self.tray_window.title("BS2PRO Controller")
            self.tray_window.geometry("200x100")
            self.tray_window.resizable(False, False)
            
            # Make it stay on top
            self.tray_window.attributes('-topmost', True)
            
            # Add buttons
            show_btn = tk.Button(self.tray_window, text="Show Main Window", 
                               command=self.show_window, width=20)
            show_btn.pack(pady=5)
            
            smart_btn = tk.Button(self.tray_window, text="Toggle Smart Mode", 
                                command=self.toggle_smart_mode, width=20)
            smart_btn.pack(pady=5)
            
            quit_btn = tk.Button(self.tray_window, text="Quit", 
                               command=self.quit_app, width=20)
            quit_btn.pack(pady=5)
            
            # Position it in the top-right corner
            self.tray_window.geometry("+{}+{}".format(
                self.root.winfo_screenwidth() - 220, 50))
            
            # Handle window close
            self.tray_window.protocol("WM_DELETE_WINDOW", self.show_window)
            
            logging.info("Tray control window created")
            
        except Exception as e:
            logging.error(f"Error creating tray window: {e}")
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        try:
            # Destroy the tray window
            if self.tray_window and self.tray_window.winfo_exists():
                self.tray_window.destroy()
                self.tray_window = None
            
            # Show the main window
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.is_minimized = False
            logging.info("Window restored from tray")
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
        if self.tray_window and self.tray_window.winfo_exists():
            self.tray_window.title(f"BS2PRO Controller - {text}")
    
    def is_window_minimized(self):
        """Check if window is minimized"""
        return self.is_minimized
    
    def is_tray_working(self):
        """Check if tray functionality is working"""
        return self.tray_available
    
    def stop_tray(self):
        """Stop the tray functionality"""
        if self.tray_window and self.tray_window.winfo_exists():
            self.tray_window.destroy()
        self.tray_available = False
        logging.info("Simple tray manager stopped")
    
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
