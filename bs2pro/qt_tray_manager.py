import os
import sys
import logging
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtCore import QCoreApplication


import os
import sys
import logging
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtCore import QCoreApplication


class QtTrayManager:
    """Simplified Qt-based system tray manager for better KDE/Wayland compatibility."""
    
    def __init__(self, gui_instance, icon_path=None):
        """
        Initialize the Qt tray manager.
        
        Args:
            gui_instance: The main GUI instance (BS2ProGUI)
            icon_path: Path to the icon file
        """
        self.gui = gui_instance
        self.icon_path = icon_path
        self.tray_icon = None
        self.qt_app = None
        self.is_running = False
        
    def _load_icon(self):
        """Load the icon for the tray."""
        try:
            if self.icon_path and os.path.exists(self.icon_path):
                logging.info(f"Attempting to load icon from: {self.icon_path}")
                # Try to load the actual icon file
                icon = QIcon(self.icon_path)
                if not icon.isNull():
                    logging.info("Loaded icon from file successfully")
                    # Verify icon has sizes
                    sizes = icon.availableSizes()
                    logging.info(f"Icon available sizes: {sizes}")
                    return icon
                else:
                    logging.warning("QIcon.isNull() returned True, icon file may be invalid")
            else:
                logging.warning(f"Icon file not found at: {self.icon_path}")
            
            # Fallback: create a simple colored square
            logging.info("Creating fallback blue square icon")
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor('blue'))  # Blue square as fallback
            icon = QIcon(pixmap)
            logging.info("Fallback icon created successfully")
            return icon
            
        except Exception as e:
            logging.error(f"Error loading icon: {e}")
            # Last resort fallback
            logging.info("Creating emergency red square icon")
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor('red'))
            return QIcon(pixmap)
    
    def _create_menu(self):
        """Create the context menu for the tray icon."""
        menu = QMenu()
        
        # Show action
        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)
        
        # Hide action
        hide_action = QAction("Hide", menu)
        hide_action.triggered.connect(self._hide_window)
        menu.addAction(hide_action)
        
        menu.addSeparator()
        
        # RPM Settings action
        rpm_action = QAction("RPM Settings", menu)
        rpm_action.triggered.connect(self._show_window)  # Just show window for now
        menu.addAction(rpm_action)
        
        # Smart Mode action
        smart_action = QAction("Smart Mode", menu)
        smart_action.triggered.connect(self._toggle_smart_mode)
        menu.addAction(smart_action)
        
        menu.addSeparator()
        
        # About action
        about_action = QAction("About", menu)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)
        
        # Exit action
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self._quit_application)
        menu.addAction(exit_action)
        
        logging.info("Qt tray menu created successfully")
        return menu
    
    def _show_window(self):
        """Handle show window."""
        logging.info("Qt Tray: Show window requested")
        try:
            if self.gui and self.gui.root:
                self.gui.root.after_idle(self._restore_window)
        except Exception as e:
            logging.error(f"Error showing window: {e}")
    
    def _restore_window(self):
        """Restore the window to normal state."""
        try:
            logging.info("Qt Tray: Restoring window")
            self.gui.root.deiconify()
            self.gui.root.lift()
            self.gui.root.focus_force()
            self.gui.root.state('normal')
            self.gui.root.attributes('-topmost', True)
            self.gui.root.attributes('-topmost', False)
            logging.info("Window restored from Qt tray")
        except Exception as e:
            logging.error(f"Error restoring window: {e}")
    
    def _hide_window(self):
        """Handle hide window."""
        logging.info("Qt Tray: Hide window requested")
        try:
            if self.gui and self.gui.root:
                self.gui.root.after_idle(self.gui.root.withdraw)
        except Exception as e:
            logging.error(f"Error hiding window: {e}")
    
    def _toggle_smart_mode(self):
        """Toggle smart mode on/off."""
        logging.info("Qt Tray: Smart mode toggle requested")
        try:
            if self.gui and hasattr(self.gui, 'toggle_smart_mode'):
                self.gui.root.after_idle(self.gui.toggle_smart_mode)
                logging.info("Smart mode toggled from Qt tray")
            else:
                logging.warning("Smart mode toggle not available")
        except Exception as e:
            logging.error(f"Error toggling smart mode from Qt tray: {e}")
    
    def _show_about(self):
        """Show about dialog."""
        logging.info("Qt Tray: About dialog requested")
        try:
            msg = QMessageBox()
            msg.setWindowTitle("About BS2PRO Controller")
            msg.setText("BS2PRO Controller\n\nA system tray application for controlling the BS2PRO device.\n\nRight-click the tray icon for options.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
        except Exception as e:
            logging.error(f"Error showing about dialog: {e}")
    
    def _quit_application(self):
        """Handle quit application."""
        logging.info("Qt Tray: Quit application requested")
        try:
            self.stop()
            if self.gui and self.gui.root:
                self.gui.root.after_idle(self._quit_app)
        except Exception as e:
            logging.error(f"Error quitting application: {e}")
    
    def _quit_app(self):
        """Actually quit the application in the main thread."""
        try:
            if self.gui:
                self.gui.cleanup()
            if self.gui and self.gui.root:
                self.gui.root.quit()
                self.gui.root.destroy()
        except Exception as e:
            logging.error(f"Error in quit app: {e}")
    
    def start(self):
        """Start the Qt tray icon."""
        if self.is_running:
            logging.warning("Qt tray icon is already running")
            return False
        
        try:
            # Get or create QApplication
            self.qt_app = QApplication.instance()
            if self.qt_app is None:
                self.qt_app = QApplication([])
                logging.info("Created new QApplication instance")
            else:
                logging.info("Using existing QApplication instance")
            
            # Check if system tray is available
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logging.error("System tray not available")
                return False
            
            # Create tray icon
            self.tray_icon = QSystemTrayIcon()
            
            # Set icon
            icon = self._load_icon()
            self.tray_icon.setIcon(icon)
            logging.info("Qt tray icon set")
            
            # Set tooltip
            self.tray_icon.setToolTip("BS2PRO Controller")
            
            # Create and set menu
            menu = self._create_menu()
            self.tray_icon.setContextMenu(menu)
            logging.info("Qt tray menu set")
            
            # Connect left click to show window
            self.tray_icon.activated.connect(self._on_tray_activated)
            logging.info("Qt tray activation signal connected")
            
            # Show the tray icon
            self.tray_icon.show()
            logging.info("Qt tray icon shown")
            
            self.is_running = True
            
            # CRITICAL: Start processing Qt events alongside tkinter
            self._start_qt_event_processing()
            
            logging.info("Qt tray icon started successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error starting Qt tray icon: {e}")
            self.is_running = False
            return False

    def _start_qt_event_processing(self):
        """Start Qt event processing that works with tkinter mainloop."""
        def process_qt_events():
            """Process Qt events periodically."""
            if self.is_running and self.qt_app:
                try:
                    # Process all pending Qt events
                    self.qt_app.processEvents()
                except Exception as e:
                    logging.error(f"Error processing Qt events: {e}")
            
            # Schedule next processing (every 50ms)
            if self.is_running and self.gui and self.gui.root:
                self.gui.root.after(50, process_qt_events)
        
        # Start the periodic event processing
        if self.gui and self.gui.root:
            logging.info("Starting Qt event processing with tkinter integration")
            self.gui.root.after(100, process_qt_events)  # Start after a short delay
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation (clicks)."""
        logging.info(f"Qt Tray activated with reason: {reason}")
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Left click
            self._show_window()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:  # Double click
            self._show_window()
        # Right click shows context menu automatically
    
    def stop(self):
        """Stop the Qt tray icon."""
        if not self.is_running:
            return
        
        try:
            self.is_running = False  # Stop event processing first
            
            if self.tray_icon:
                self.tray_icon.hide()
                
            # Process any remaining Qt events
            if self.qt_app:
                self.qt_app.processEvents()
                
            logging.info("Qt tray icon stopped")
        except Exception as e:
            logging.error(f"Error stopping Qt tray icon: {e}")
    
    def update_tooltip(self, text):
        """Update the tray icon tooltip."""
        try:
            if self.tray_icon and self.is_running:
                self.tray_icon.setToolTip(text)
        except Exception as e:
            logging.error(f"Error updating tooltip: {e}")
    
    def is_tray_available(self):
        """Check if system tray is available."""
        try:
            return QSystemTrayIcon.isSystemTrayAvailable()
        except Exception:
            return False