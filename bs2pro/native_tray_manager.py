#!/usr/bin/env python3
"""
Native Tray Manager for BS2PRO Controller
Uses native Linux system tray with libappindicator
"""
import logging
import os
import subprocess
import time
import threading
import tempfile

class NativeTrayManager:
    def __init__(self, root, gui_instance):
        self.root = root
        self.gui = gui_instance
        self.is_minimized = False
        self.tray_available = False
        self.notification_available = False
        self.tray_process = None
        self.tray_script_path = None
        
        # Check for native system tray support
        self._check_tray_support()
        
        # Check for notification support
        self._check_notification_support()
        
        logging.info(f"Native tray manager initialized - tray: {self.tray_available}, notifications: {self.notification_available}")
    
    def _check_tray_support(self):
        """Check if we can use native system tray"""
        try:
            # Check for libappindicator or ayatana-appindicator
            result = subprocess.run(['pkg-config', '--exists', 'libappindicator-0.1'], 
                                 capture_output=True, timeout=5)
            if result.returncode == 0:
                self.tray_available = True
                logging.info("libappindicator available")
                return
            
            result = subprocess.run(['pkg-config', '--exists', 'ayatana-appindicator-0.1'], 
                                 capture_output=True, timeout=5)
            if result.returncode == 0:
                self.tray_available = True
                logging.info("ayatana-appindicator available")
                return
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: check if we can at least minimize
        self.tray_available = True  # We can always minimize to taskbar
        logging.info("Using fallback tray (taskbar only)")
    
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
    
    def _create_tray_script(self):
        """Create a Python script for the system tray icon"""
        script_content = '''#!/usr/bin/env python3
import sys
import os
import subprocess
import signal
import time

# Add the bs2pro directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def show_window():
    """Show the main window"""
    try:
        # Send a signal to the main process to show window
        subprocess.run(['pkill', '-USR1', 'bs2pro_controller'], timeout=5)
    except Exception as e:
        print(f"Error showing window: {e}")

def toggle_smart_mode():
    """Toggle smart mode"""
    try:
        # Send a signal to the main process to toggle smart mode
        subprocess.run(['pkill', '-USR2', 'bs2pro_controller'], timeout=5)
    except Exception as e:
        print(f"Error toggling smart mode: {e}")

def quit_app():
    """Quit the application"""
    try:
        # Send a signal to the main process to quit
        subprocess.run(['pkill', '-TERM', 'bs2pro_controller'], timeout=5)
    except Exception as e:
        print(f"Error quitting app: {e}")

def main():
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        
        # Try ayatana-appindicator first, then fallback to libappindicator
        try:
            gi.require_version('AyatanaAppIndicator3', '0.1')
            from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator3
            print("Using ayatana-appindicator")
        except ValueError:
            try:
                gi.require_version('AppIndicator3', '0.1')
                from gi.repository import Gtk, AppIndicator3
                print("Using libappindicator")
            except ValueError:
                print("Neither ayatana-appindicator nor libappindicator available")
                sys.exit(1)
        
        # Create the indicator
        indicator = AppIndicator3.Indicator.new(
            "bs2pro-controller",
            "applications-system",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        
        # Set the status
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # Create menu
        menu = Gtk.Menu()
        
        # Show Window item
        show_item = Gtk.MenuItem.new_with_label("Show Window")
        show_item.connect("activate", lambda x: show_window())
        menu.append(show_item)
        
        # Toggle Smart Mode item
        smart_item = Gtk.MenuItem.new_with_label("Toggle Smart Mode")
        smart_item.connect("activate", lambda x: toggle_smart_mode())
        menu.append(smart_item)
        
        # Separator
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)
        
        # Quit item
        quit_item = Gtk.MenuItem.new_with_label("Quit")
        quit_item.connect("activate", lambda x: quit_app())
        menu.append(quit_item)
        
        # Show all menu items
        menu.show_all()
        
        # Set the menu
        indicator.set_menu(menu)
        
        # Set up signal handlers
        def on_clicked(indicator, button, time):
            if button == 1:  # Left click
                show_window()
        
        indicator.connect("button-press-event", on_clicked)
        
        # Start the GTK main loop
        Gtk.main()
        
    except ImportError as e:
        print(f"Required libraries not available: {e}")
        print("Falling back to taskbar minimization")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating tray icon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        # Create temporary script file
        script_fd, self.tray_script_path = tempfile.mkstemp(suffix='.py', prefix='bs2pro_tray_')
        os.close(script_fd)
        
        with open(self.tray_script_path, 'w') as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod(self.tray_script_path, 0o755)
        
        logging.info(f"Created tray script: {self.tray_script_path}")
    
    def start_tray(self):
        """Start the tray functionality"""
        if not self.tray_available:
            logging.warning("System tray not available")
            return False
        
        try:
            # Create the tray script
            self._create_tray_script()
            
            # Start the tray process
            self.tray_process = subprocess.Popen([
                'python3', self.tray_script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to start
            time.sleep(1.0)
            
            # Check if it's still running
            if self.tray_process.poll() is None:
                logging.info("System tray icon started successfully")
                return True
            else:
                logging.warning("Tray process exited immediately, falling back to taskbar")
                return False
                
        except Exception as e:
            logging.error(f"Error starting tray: {e}")
            return False
    
    def hide_window(self):
        """Hide the main window to system tray"""
        try:
            # Hide the window
            self.root.withdraw()
            self.is_minimized = True
            logging.info("Window hidden to system tray")
            
            # Send notification
            if self.notification_available:
                self._send_notification(
                    "BS2PRO Controller",
                    "App minimized to system tray. Right-click the tray icon for options.",
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
            logging.info("Window restored from system tray")
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
        return self.tray_available and self.tray_process and self.tray_process.poll() is None
    
    def stop_tray(self):
        """Stop the tray functionality"""
        if self.tray_process:
            try:
                self.tray_process.terminate()
                self.tray_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tray_process.kill()
            except Exception as e:
                logging.warning(f"Error stopping tray process: {e}")
        
        # Clean up script file
        if self.tray_script_path and os.path.exists(self.tray_script_path):
            try:
                os.unlink(self.tray_script_path)
            except Exception as e:
                logging.warning(f"Error cleaning up tray script: {e}")
        
        self.tray_available = False
        logging.info("Native tray manager stopped")
    
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
