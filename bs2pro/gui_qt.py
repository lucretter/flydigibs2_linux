#!/usr/bin/env python3
"""
PyQt6 Native GUI for BS2PRO Controller
Provides native KDE/Plasma theme integration with Breeze theme support
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QCheckBox, QGroupBox, QFrame, QSystemTrayIcon, QMenu, QMessageBox, QDialog, QScrollArea,
    QLineEdit, QSpinBox
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QColor, QMouseEvent

# Import PyQtGraph for interactive plotting
import pyqtgraph as pg


# Custom PlotWidget that properly handles mouse events
class DraggablePlotWidget(pg.PlotWidget):
    """Custom PlotWidget that allows proper mouse event handling for dragging"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_graph = None
        
    def set_parent_graph(self, parent_graph):
        """Set reference to parent TemperatureRPMGraph"""
        self.parent_graph = parent_graph
        
    def mousePressEvent(self, event):
        """Override mouse press event"""
        if self.parent_graph:
            result = self.parent_graph.handle_mouse_press(event)
            if result:
                return  # Event was handled
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Override mouse move event"""
        if self.parent_graph:
            result = self.parent_graph.handle_mouse_move(event)
            if result:
                return  # Event was handled
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Override mouse release event"""
        if self.parent_graph:
            result = self.parent_graph.handle_mouse_release(event)
            if result:
                return  # Event was handled
        super().mouseReleaseEvent(event)


class TemperatureRPMGraph(QWidget):
    """Interactive graph for configuring temperature vs RPM relationships"""
    
    pointsChanged = pyqtSignal()  # Signal emitted when points change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fixed_temps = [30, 40, 50, 60, 70, 80, 90, 100]  # Fixed temperature points
        self.available_rpms = [1300, 1700, 1900, 2100, 2400, 2700]  # Available RPM values
        self.points = []  # List of (temp, rpm) tuples - one for each fixed temperature
        self.min_rpm = min(self.available_rpms)
        self.max_rpm = max(self.available_rpms)
        self.dragging_point = None
        self.init_ui()
        self.setup_graph()
        self.load_default_points()
        
    def init_ui(self):
        """Initialize the graph UI"""
        layout = QVBoxLayout(self)
        
        # Create the plot widget using our custom draggable version
        self.plot_widget = DraggablePlotWidget()
        self.plot_widget.set_parent_graph(self)
        layout.addWidget(self.plot_widget)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Reset to Default")
        clear_btn.clicked.connect(self.clear_points)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
    def setup_graph(self):
        """Setup the graph with proper axes and styling"""
        # Get system theme colors
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPalette
        
        app = QApplication.instance()
        palette = app.palette()
        
        # Determine if we're in dark mode
        bg_color = palette.color(QPalette.ColorRole.Window)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        
        is_dark = bg_color.lightness() < 128
        
        if is_dark:
            # Dark theme colors
            bg_color_str = 'black'
            text_color_str = 'white'
            grid_color = (60, 60, 60)
            point_color = (100, 150, 255)
            line_color = (100, 150, 255)
            rpm_line_color = (80, 80, 80)
        else:
            # Light theme colors
            bg_color_str = 'white'
            text_color_str = 'black'
            grid_color = (200, 200, 200)
            point_color = (50, 100, 200)
            line_color = (50, 100, 200)
            rpm_line_color = (220, 220, 220)
        
        # Configure plot with system theme
        self.plot_widget.setBackground(bg_color_str)
        self.plot_widget.setTitle("Fan Speed vs Temperature", color=text_color_str, size='14pt')
        
        # Configure axes
        self.plot_widget.setLabel('left', 'Fan Speed (RPM)', color=text_color_str, size='12pt')
        self.plot_widget.setLabel('bottom', 'Temperature (°C)', color=text_color_str, size='12pt')
        
        # Create equal spacing for RPM values by using linear mapping
        # Instead of using actual RPM values as Y coordinates, we'll map them to equal intervals
        rpm_count = len(self.available_rpms)
        y_positions = [i * 100 for i in range(rpm_count)]  # Equal spacing of 100 units
        
        # Set custom Y-axis ticks with equal spacing
        y_axis = self.plot_widget.getAxis('left')
        y_ticks = [(y_pos, str(rpm)) for y_pos, rpm in zip(y_positions, self.available_rpms)]
        y_axis.setTicks([y_ticks])
        
        # Set axis ranges with equal spacing
        self.plot_widget.setXRange(25, 105)
        self.plot_widget.setYRange(-50, (rpm_count - 1) * 100 + 50)
        
        # Disable mouse interaction (zooming/panning)
        self.plot_widget.getViewBox().setMouseEnabled(x=False, y=False)
        self.plot_widget.getViewBox().setLimits(xMin=25, xMax=105, yMin=-50, yMax=(rpm_count - 1) * 100 + 50)
        self.plot_widget.setMenuEnabled(False)
        
        # Remove all grid lines - no showGrid() call
        
        # Add subtle horizontal lines at each RPM level only (no vertical lines)
        for i, rpm in enumerate(self.available_rpms):
            y_pos = i * 100
            line = pg.InfiniteLine(pos=y_pos, angle=0, pen=pg.mkPen(color=rpm_line_color, width=1, style=Qt.PenStyle.DashLine))
            line.setOpacity(0.3)
            self.plot_widget.addItem(line)
        
        # Store the Y position mapping for coordinate conversion
        self.rpm_to_y_pos = {rpm: i * 100 for i, rpm in enumerate(self.available_rpms)}
        self.y_pos_to_rpm = {i * 100: rpm for i, rpm in enumerate(self.available_rpms)}
        
        # Create scatter plot for points
        self.scatter = pg.ScatterPlotItem(size=12, brush=pg.mkBrush(*point_color, 255), pen=pg.mkPen(color=text_color_str, width=2))
        self.plot_widget.addItem(self.scatter)
        
        # Create line connecting the points
        self.curve = pg.PlotCurveItem(pen=pg.mkPen(color=line_color, width=3))
        self.plot_widget.addItem(self.curve)
        
        # Enable direct dragging by using mouse event override in custom plot widget
        self.dragging_point = None
        self.is_dragging = False
        
        # Enable mouse tracking for drag operations
        self.plot_widget.setMouseTracking(True)
        
    def on_plot_mouse_click(self, event):
        """Handle mouse clicks for dragging points"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked on a point
            pos = event.scenePos()
            plot_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            click_x, click_y = plot_pos.x(), plot_pos.y()
            
            # Find the closest point
            closest_point_idx = None
            min_distance = float('inf')
            
            for i, (temp, rpm) in enumerate(self.points):
                distance = ((temp - click_x) ** 2 + (rpm - click_y) ** 2) ** 0.5
                if distance < min_distance and distance < 20:  # Within 20 units
                    min_distance = distance
                    closest_point_idx = i
            
            if closest_point_idx is not None:
                self.dragging_point = closest_point_idx
                event.accept()
            else:
                self.dragging_point = None
        elif event.button() == Qt.MouseButton.LeftButton and self.dragging_point is not None:
            # Stop dragging
            self.dragging_point = None
            event.accept()
    
    def on_plot_mouse_move(self, event):
        """Handle mouse movement for dragging points"""
        if self.dragging_point is not None and event.buttons() & Qt.MouseButton.LeftButton:
            pos = event.scenePos()
            plot_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            
            new_temp = max(0, min(100, plot_pos.x()))
            new_rpm = plot_pos.y()
            
            # Find the closest available RPM
            closest_rpm = min(self.available_rpms, key=lambda x: abs(x - new_rpm))
            
            # Update the point
            self.points[self.dragging_point] = (new_temp, closest_rpm)
            self.update_plot()
            self.pointsChanged.emit()
            
            event.accept()
        
    def load_default_points(self):
        """Load default temperature points for each RPM level"""
        # Create default temperature progression: 20°C, 35°C, 45°C, 55°C, 70°C, 85°C
        default_temps = [20, 35, 45, 55, 70, 85]
        
        for rpm, temp in zip(self.available_rpms, default_temps):
            self.points.append((temp, rpm))
        
        self.update_plot()
        self.pointsChanged.emit()
        
    def on_mouse_click(self, event):
        """Handle mouse clicks on the graph - now used for dragging points"""
        # Mouse clicks are handled by the scatter plot item for dragging
        pass
        
    def on_point_dragged(self, points, offset):
        """Handle when points are dragged to new positions"""
        for i, point in enumerate(points):
            # Get the new position
            new_temp = point.pos().x()
            new_rpm = point.pos().y()
            
            # Constrain to valid ranges
            new_temp = max(0, min(100, new_temp))
            new_rpm = max(1300, min(2700, new_rpm))
            
            # Find the closest available RPM (snap to available RPMs)
            closest_rpm = min(self.available_rpms, key=lambda x: abs(x - new_rpm))
            
            # Update the point position
            point.setPos(new_temp, closest_rpm)
            
            # Update our internal points list
            for j, (temp, rpm) in enumerate(self.points):
                if rpm == closest_rpm:
                    self.points[j] = (new_temp, closest_rpm)
                    break
        
        self.pointsChanged.emit()
        
    def load_default_points(self):
        """Load default RPM points for each fixed temperature"""
        # Create default RPM progression using available RPM values
        # Start with lower RPMs for cooler temperatures, higher for hotter
        default_rpms = [
            1300,  # 30°C
            1300,  # 40°C  
            1700,  # 50°C
            1900,  # 60°C
            2100,  # 70°C
            2100,  # 80°C
            2400,  # 90°C
            2700   # 100°C
        ]
        
        self.points = []
        for temp, rpm in zip(self.fixed_temps, default_rpms):
            self.points.append((temp, rpm))
        
        self.update_plot()
        self.pointsChanged.emit()
        
    def handle_mouse_press(self, event):
        """Handle mouse press events for drag and drop functionality"""
        if event.button() == Qt.MouseButton.LeftButton and not self.is_dragging:
            # Convert to scene coordinates
            pos = self.plot_widget.mapToScene(event.pos())
            plot_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            click_x, click_y = plot_pos.x(), plot_pos.y()
            
            # Find the closest point using equal spacing coordinates
            closest_point_idx = None
            min_distance = float('inf')
            
            for i, (temp, rpm) in enumerate(self.points):
                y_pos = self.rpm_to_y_pos[rpm]
                x_distance = abs(temp - click_x)
                y_distance = abs(y_pos - click_y)
                total_distance = (x_distance**2 + (y_distance/10)**2)**0.5
                
                if x_distance < 5 and total_distance < min_distance:
                    min_distance = total_distance
                    closest_point_idx = i
            
            if closest_point_idx is not None and min_distance < 20:
                # Start dragging
                self.dragging_point = closest_point_idx
                self.is_dragging = True
                return True
        return False
        
    def handle_mouse_move(self, event):
        """Handle mouse move events for drag and drop functionality"""
        if self.is_dragging and self.dragging_point is not None:
            # Convert to scene coordinates
            pos = self.plot_widget.mapToScene(event.pos())
            plot_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            
            # Only allow Y-axis movement (RPM adjustment)
            fixed_temp = self.fixed_temps[self.dragging_point]
            new_y = plot_pos.y()
            
            # Find the closest Y position and corresponding RPM
            closest_y_pos = min(self.y_pos_to_rpm.keys(), key=lambda y: abs(y - new_y))
            closest_rpm = self.y_pos_to_rpm[closest_y_pos]
            
            # Only update if the RPM actually changed
            old_temp, old_rpm = self.points[self.dragging_point]
            if closest_rpm != old_rpm:
                self.points[self.dragging_point] = (fixed_temp, closest_rpm)
                self.update_plot()
                self.pointsChanged.emit()
            return True
        return False
                
    def handle_mouse_release(self, event):
        """Handle mouse release events for drag and drop functionality"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.dragging_point = None
            self.is_dragging = False
            return True
        return False
        
    def set_ranges(self, ranges):
        """Set graph points from temperature ranges"""
        try:
            # Convert ranges to graph points
            # For now, use a simple approach: take the RPM at the midpoint of each range
            new_points = []
            
            for range_data in ranges:
                # Use the midpoint temperature of the range
                mid_temp = (range_data['min_temp'] + range_data['max_temp']) / 2
                rpm = range_data['rpm']
                
                # Find the closest fixed temperature point
                closest_temp = min(self.fixed_temps, key=lambda t: abs(t - mid_temp))
                
                # Make sure the RPM is in available RPMs
                closest_rpm = min(self.available_rpms, key=lambda r: abs(r - rpm))
                
                new_points.append((closest_temp, closest_rpm))
            
            # Remove duplicates (if multiple ranges map to the same temperature)
            unique_points = {}
            for temp, rpm in new_points:
                unique_points[temp] = rpm
            
            # Fill in any missing temperature points with default values
            self.points = []
            for temp in self.fixed_temps:
                if temp in unique_points:
                    self.points.append((temp, unique_points[temp]))
                else:
                    # Use a default RPM value
                    default_rpm = self.available_rpms[2] if len(self.available_rpms) > 2 else self.available_rpms[0]
                    self.points.append((temp, default_rpm))
            
            self.update_plot()
            self.pointsChanged.emit()
            
        except Exception as e:
            logging.error(f"Error setting ranges: {e}")
            # Fall back to default points
            self.clear_points()
        
    def clear_points(self):
        """Reset all points to default RPM values"""
        self.points = []
        self.load_default_points()
        
    def add_point(self, temp, rpm):
        """Add or update a point for the given temperature"""
        # Find the point for this temperature and update its RPM
        for i, (existing_temp, existing_rpm) in enumerate(self.points):
            if existing_temp == temp:
                # Update existing point
                self.points[i] = (temp, rpm)
                self.update_plot()
                self.pointsChanged.emit()
                return
                
        # If temperature not found, add it (though this shouldn't happen with fixed temps)
        self.points.append((temp, rpm))
        self.update_plot()
        self.pointsChanged.emit()
        
    def sort_points(self):
        """Sort points by temperature"""
        self.points.sort(key=lambda x: x[0])
        
    def update_plot(self):
        """Update the plot with current points using equal spacing coordinate system"""
        if not self.points:
            self.scatter.setData([], [])
            if hasattr(self, 'curve'):
                self.curve.setData([], [])
            return
            
        temps, rpms = zip(*sorted(self.points, key=lambda x: x[0]))
        
        # Convert RPM values to Y positions for equal spacing
        y_positions = [self.rpm_to_y_pos[rpm] for rpm in rpms]
        
        self.scatter.setData(list(temps), y_positions)
        
        # Update the connecting curve
        if hasattr(self, 'curve'):
            self.curve.setData(list(temps), y_positions)
        
    def get_ranges(self):
        """Convert graph points to temperature ranges for smart mode"""
        if len(self.points) < 2:
            return []
            
        ranges = []
        sorted_points = sorted(self.points, key=lambda x: x[0])  # Sort by temperature
        
        for i in range(len(sorted_points) - 1):
            temp_min, rpm_current = sorted_points[i]
            temp_max, _ = sorted_points[i + 1]
            
            ranges.append({
                'min_temp': temp_min,
                'max_temp': temp_max - 1,  # Subtract 1 to avoid overlap
                'rpm': int(rpm_current),
                'description': f'Range {temp_min}-{temp_max-1}°C'
            })
        
        # Add the final range
        last_temp, last_rpm = sorted_points[-1]
        ranges.append({
            'min_temp': last_temp,
            'max_temp': 100,  # Max temperature
            'rpm': int(last_rpm),
            'description': f'Range {last_temp}-100°C'
        })
        
        return ranges


# Import our existing modules
try:
    from .cpu_monitor import TemperatureMonitor
    from .smart_mode import SmartModeManager
except ImportError:
    # Fallback for direct execution
    from cpu_monitor import TemperatureMonitor
    from smart_mode import SmartModeManager


class SmartModeConfigDialog(QDialog):
    """Smart Mode Configuration Dialog with Graph and Range modes"""
    
    def __init__(self, parent, smart_mode_manager):
        super().__init__(parent)
        self.smart_mode_manager = smart_mode_manager
        self.range_widgets = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Smart Mode Configuration")
        self.setModal(True)
        self.resize(900, 700)  # Increased size for graph
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        
        # Title
        title_label = QLabel("Fan Speed Configuration")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Graph widget (only mode now)
        self.graph_widget = TemperatureRPMGraph()
        layout.addWidget(self.graph_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Load existing ranges (after UI is fully set up)
        try:
            self.load_ranges()
        except Exception as e:
            logging.error(f"Error loading ranges: {e}")
            # Continue without loading ranges
            
    def create_graph_mode_widget(self):
        """Create the graph-based configuration widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel("Click on the graph to add temperature/RPM points.\n"
                             "Right-click points to remove them.\n"
                             "The fan will interpolate between points.")
        instructions.setStyleSheet("color: gray;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create the graph widget
        self.graph_widget = TemperatureRPMGraph()
        layout.addWidget(self.graph_widget)
        
        # Connect graph changes to preview update
        self.graph_widget.pointsChanged.connect(self.update_preview)
        
        return widget
        
    def create_range_mode_widget(self):
        """Create the traditional range configuration widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for ranges
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        # Widget inside scroll area
        scroll_widget = QWidget()
        self.ranges_layout = QVBoxLayout(scroll_widget)
        self.ranges_layout.setSpacing(6)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add New Range")
        add_btn.clicked.connect(self.add_new_range)
        controls_layout.addWidget(add_btn)
        
        sort_btn = QPushButton("Sort Ranges")
        sort_btn.clicked.connect(self.sort_ranges)
        sort_btn.setToolTip("Sort temperature ranges by minimum temperature")
        controls_layout.addWidget(sort_btn)
        
        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self.validate_ranges)
        validate_btn.setToolTip("Check if the current configuration is valid")
        controls_layout.addWidget(validate_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        return widget
        
            
    def load_ranges(self):
        """Load existing ranges into both graph and range widgets"""
        # Load from smart mode manager
        ranges = self.smart_mode_manager.temperature_ranges
        
        if ranges:
            # Convert ranges to graph points
            for range_data in ranges:
                temp = (range_data['min_temp'] + range_data['max_temp']) / 2  # Use midpoint
                rpm = range_data['rpm']
                self.graph_widget.add_point(temp, rpm)
                
            # Also create range widgets for range mode
            for range_data in ranges:
                self.add_range_widget(range_data)
        else:
            # Add some default points for demonstration
            self.graph_widget.add_point(40, 800)
            self.graph_widget.add_point(60, 1200)
            self.graph_widget.add_point(80, 1800)
            
        self.update_preview()
        
    def add_range_widget(self, range_data=None):
        """Add a new range widget (for range mode)"""
        if range_data is None:
            range_data = {'temp_min': 0, 'temp_max': 0, 'rpm': 0}
        
        # Create a widget for this range
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        
        # Temperature range inputs
        temp_min_label = QLabel("Min Temp (°C):")
        temp_min_spin = QSpinBox()
        temp_min_spin.setRange(0, 100)
        temp_min_spin.setValue(range_data.get('temp_min', 0))
        
        temp_max_label = QLabel("Max Temp (°C):")
        temp_max_spin = QSpinBox()
        temp_max_spin.setRange(0, 100)
        temp_max_spin.setValue(range_data.get('temp_max', 0))
        
        # RPM input
        rpm_label = QLabel("RPM:")
        rpm_spin = QSpinBox()
        rpm_spin.setRange(0, 10000)
        rpm_spin.setValue(range_data.get('rpm', 0))
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_range_widget(range_widget))
        
        # Add to layout
        range_layout.addWidget(temp_min_label)
        range_layout.addWidget(temp_min_spin)
        range_layout.addWidget(temp_max_label)
        range_layout.addWidget(temp_max_spin)
        range_layout.addWidget(rpm_label)
        range_layout.addWidget(rpm_spin)
        range_layout.addWidget(remove_btn)
        
        # Add to range mode layout
        self.ranges_layout.addWidget(range_widget)
        
        # Store references for saving
        range_widget.temp_min_spin = temp_min_spin
        range_widget.temp_max_spin = temp_max_spin
        range_widget.rpm_spin = rpm_spin
        
    def remove_range_widget(self, range_widget):
        """Remove a range widget from the range mode"""
        range_widget.setParent(None)
        range_widget.deleteLater()
        
    def add_new_range(self):
        """Add new range in range mode"""
        self.add_range_widget()
        
    def sort_ranges(self):
        """Sort ranges in range mode"""
        pass
        
    def validate_ranges(self):
        """Validate ranges in range mode"""
        pass
        
    def save_configuration(self):
        """Save the configuration from current mode"""
        try:
            # Clear existing ranges
            self.smart_mode_manager.temperature_ranges = []
            
            # Get ranges based on current mode
            if self.mode_combo.currentData() == "graph":
                ranges_data = self.graph_widget.get_ranges()
            else:
                # Get from range widgets
                ranges_data = []
                for widget_data in self.range_widgets:
                    min_temp = widget_data['min_spin'].value()
                    max_temp = widget_data['max_spin'].value()
                    rpm = int(widget_data['rpm_combo'].currentText())
                    description = widget_data['desc_edit'].text() or "Range"
                    
                    ranges_data.append({
                        'min_temp': min_temp,
                        'max_temp': max_temp,
                        'rpm': rpm,
                        'description': description
                    })
            
            # Validate ranges
            if not ranges_data:
                QMessageBox.warning(self, "No Ranges", "Please add at least one temperature range.")
                return
                
            # Check for overlaps (critical error)
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['max_temp'] > ranges_data[i + 1]['min_temp']:
                    QMessageBox.warning(self, "Overlapping Ranges", 
                                      "Temperature ranges cannot overlap. Please adjust the ranges.")
                    return
            
            # Add ranges to smart mode manager
            for range_data in ranges_data:
                self.smart_mode_manager.add_temperature_range(
                    range_data['min_temp'],
                    range_data['max_temp'],
                    range_data['rpm'],
                    range_data['description']
                )
            
            # Save configuration
            self.smart_mode_manager.save_config()
            
            # Show success message
            QMessageBox.information(self, "Success", 
                                  f"Smart mode configuration saved with {len(ranges_data)} ranges!")
            
            # Accept dialog
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def update_preview(self):
        """Update the configuration preview"""
        try:
            # Get ranges based on current mode
            if self.mode_combo.currentData() == "graph":
                ranges_data = self.graph_widget.get_ranges()
            else:
                ranges_data = []
                for widget_data in self.range_widgets:
                    min_temp = widget_data['min_spin'].value()
                    max_temp = widget_data['max_spin'].value()
                    rpm = int(widget_data['rpm_combo'].currentText())
                    description = widget_data['desc_edit'].text() or f"Range {len(ranges_data)+1}"
                    
                    ranges_data.append({
                        'min_temp': min_temp,
                        'max_temp': max_temp,
                        'rpm': rpm,
                        'description': description
                    })
            
            # Sort by temperature for preview
            ranges_data.sort(key=lambda x: x['min_temp'])
            
            # Create preview text
            preview_lines = ["Fan speed behavior preview:"]
            
            for i, range_data in enumerate(ranges_data):
                temp_range = f"{range_data['min_temp']}°C - {range_data['max_temp']}°C"
                preview_lines.append(f"• {temp_range}: {range_data['rpm']} RPM ({range_data['description']})")
            
            # Check for issues
            critical_issues = []
            warning_issues = []
            
            # Check for invalid ranges
            for range_data in ranges_data:
                if range_data['min_temp'] >= range_data['max_temp']:
                    critical_issues.append("Invalid temperature range")
                    break
            
            # Check for overlaps
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['max_temp'] > ranges_data[i + 1]['min_temp']:
                    critical_issues.append("Overlapping ranges")
                    break
            
            # Check RPM progression
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['rpm'] >= ranges_data[i + 1]['rpm']:
                    warning_issues.append("RPM doesn't increase with temperature")
                    break
            
            if critical_issues:
                preview_lines.append("")
                preview_lines.append("❌ Critical issues: " + ", ".join(critical_issues))
                self.preview_label.setStyleSheet("color: #dc3545; font-style: italic;")
            elif warning_issues:
                preview_lines.append("")
                preview_lines.append("⚠️ Warning: " + ", ".join(warning_issues))
                self.preview_label.setStyleSheet("color: #ffc107; font-style: italic;")
            else:
                preview_lines.append("")
                preview_lines.append("✅ Configuration looks good!")
                self.preview_label.setStyleSheet("color: #28a745; font-style: italic;")
            
            self.preview_label.setText("\n".join(preview_lines))
            
        except Exception as e:
            self.preview_label.setText(f"Error updating preview: {e}")
            self.preview_label.setStyleSheet("color: #dc3545; font-style: italic;")


class BS2ProQtGUI(QMainWindow):
    """Native PyQt6 GUI for BS2PRO Controller with KDE/Breeze theme integration"""
    
    def __init__(self, controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
        super().__init__()
        
        # Store references
        self.controller = controller
        self.config_manager = config_manager
        self.rpm_commands = rpm_commands
        self.commands = commands
        self.default_settings = default_settings
        self.icon_path = icon_path
        
        # Initialize monitoring components
        self.cpu_monitor = TemperatureMonitor()
        temperature_source = self.config_manager.load_setting("temperature_source", "cpu")
        self.cpu_monitor.set_source(temperature_source)
        self.smart_mode_manager = SmartModeManager()
        self.current_rpm = None
        self.displayed_rpm = None  # Track what's currently displayed
        self.displayed_autostart = None  # Track autostart setting
        self.displayed_rpm_mode = None  # Track RPM mode setting
        self.displayed_start_powered = None  # Track start when powered setting
        
        # Initialize system tray
        self.tray_icon = None
        self.minimize_to_tray = True
        
        # Initialize UI
        self.init_ui()
        self.setup_monitoring()
        self.update_device_status()
        
        # Setup system tray if available
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.setup_system_tray()
        
        # Show window
        self.show()
        
    def init_ui(self):
        """Initialize the user interface with native Qt styling"""
        self.setWindowTitle("BS2PRO Controller")
        self.setMinimumSize(450, 540)  # Increased height from 480 to 540
        self.resize(450, 580)  # Increased height from 520 to 580
        
        # Set window icon
        if self.icon_path and os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout with balanced spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)  # Increased width margins
        main_layout.setSpacing(10)  # Increased from 8 to 10
        
        # Header section
        self.create_header_section(main_layout)
        
        # Device status section
        self.create_device_status_section(main_layout)
        
        # Device settings section
        self.create_device_settings_section(main_layout)
        
        # Fan speed control section
        self.create_fan_speed_section(main_layout)
        
        # Smart mode section
        self.create_smart_mode_section(main_layout)
        
        # Add stretch to push everything to top
        main_layout.addStretch()
        
        # Footer
        self.create_footer_section(main_layout)
        
        # Center window on screen
        self.center_window()
        
    def create_header_section(self, parent_layout):
        """Create the header section with app title"""
        header_label = QLabel("BS2PRO Controller")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #2980b9; margin: 4px 0px;")  # Reduced margin
        parent_layout.addWidget(header_label)
        
    def create_device_status_section(self, parent_layout):
        """Create device status display"""
        status_group = QGroupBox("Device Status")
        status_group.setMinimumHeight(65)  # Increased from 55 to accommodate longer device text
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        
        self.status_label = QLabel("Device Status: Not Connected")
        status_font = QFont()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 6px;")  # Increased padding for better text display
        
        status_layout.addWidget(self.status_label)
        parent_layout.addWidget(status_group)
        
    def create_device_settings_section(self, parent_layout):
        """Create device settings controls"""
        settings_group = QGroupBox("Device Settings")
        settings_group.setMinimumHeight(110)  # Increased from 100
        settings_layout = QGridLayout(settings_group)
        settings_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        settings_layout.setSpacing(8)  # Increased spacing
        
        # Autostart Mode
        autostart_label = QLabel("Autostart Mode:")
        autostart_label.setToolTip("Configure how the device starts up")
        settings_layout.addWidget(autostart_label, 0, 0)
        
        self.autostart_combo = QComboBox()
        self.autostart_combo.addItems(["OFF", "Instant", "Delayed"])
        self.autostart_combo.setCurrentText(self.config_manager.load_setting("autostart", "off").title())
        self.autostart_combo.currentTextChanged.connect(self.on_autostart_select)
        self.autostart_combo.setToolTip("Choose autostart behavior")
        self.autostart_combo.setMinimumWidth(140)  # Increased from 120
        self.autostart_combo.setMinimumHeight(24)  # Ensure proper height
        self.autostart_combo.setStyleSheet("padding-left: 8px; padding-right: 8px;")  # Add left/right padding
        settings_layout.addWidget(self.autostart_combo, 0, 1)
        
        # Initialize tracking variables for config monitoring
        self.displayed_autostart = self.config_manager.load_setting("autostart", "off")
        
        # RPM Indicator checkbox
        self.rpm_indicator_cb = QCheckBox("RPM Indicator")
        self.rpm_indicator_cb.setChecked(self.config_manager.load_setting("rpm_mode", "off") == "on")
        self.rpm_indicator_cb.toggled.connect(self.on_rpm_toggle)
        self.rpm_indicator_cb.setToolTip("Enable/disable RPM feedback from device")
        settings_layout.addWidget(self.rpm_indicator_cb, 1, 0, 1, 2)
        
        # Start When Powered checkbox
        self.start_powered_cb = QCheckBox("Start When Powered")
        self.start_powered_cb.setChecked(self.config_manager.load_setting("start_when_powered", "off") == "on")
        self.start_powered_cb.toggled.connect(self.on_start_toggle)
        self.start_powered_cb.setToolTip("Automatically start when device is powered on")
        settings_layout.addWidget(self.start_powered_cb, 2, 0, 1, 2)
        
        # Initialize remaining tracking variables
        self.displayed_rpm_mode = self.config_manager.load_setting("rpm_mode", "off")
        self.displayed_start_powered = self.config_manager.load_setting("start_when_powered", "off")
        
        parent_layout.addWidget(settings_group)
        
    def create_fan_speed_section(self, parent_layout):
        """Create fan speed controls"""
        fan_group = QGroupBox("Fan Speed Control")
        fan_group.setMinimumHeight(90)  # Increased from 80
        fan_layout = QVBoxLayout(fan_group)
        fan_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        fan_layout.setSpacing(8)  # Increased spacing
        
        # RPM selection row
        rpm_row = QHBoxLayout()
        
        rpm_label = QLabel("Select Fan Speed:")
        rpm_row.addWidget(rpm_label)
        
        self.rpm_combo = QComboBox()
        self.rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]
        self.rpm_combo.addItems([str(rpm) for rpm in self.rpm_values])
        self.rpm_combo.setMinimumWidth(100)
        self.rpm_combo.setMinimumHeight(24)  # Ensure proper height
        last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
        self.displayed_rpm = last_rpm  # Track what's currently displayed
        self.rpm_combo.setCurrentText(str(last_rpm))
        self.rpm_combo.currentTextChanged.connect(self.on_rpm_select)
        self.rpm_combo.setToolTip("Choose fan RPM setting")
        self.rpm_combo.setMinimumWidth(120)
        self.rpm_combo.setStyleSheet("padding-left: 8px; padding-right: 8px;")  # Add left/right padding
        rpm_row.addWidget(self.rpm_combo)
        
        rpm_row.addStretch()
        fan_layout.addLayout(rpm_row)
        
        # Current RPM display
        self.rpm_display_label = QLabel(f"Current: {last_rpm} RPM")
        rpm_font = QFont()
        rpm_font.setBold(True)
        self.rpm_display_label.setFont(rpm_font)
        self.rpm_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rpm_display_label.setStyleSheet("color: #1f538d; padding: 3px;")  # Reduced padding
        fan_layout.addWidget(self.rpm_display_label)
        
        parent_layout.addWidget(fan_group)
        
    def create_smart_mode_section(self, parent_layout):
        """Create smart mode controls"""
        smart_group = QGroupBox("Smart Mode")
        smart_group.setMinimumHeight(120)  # Increased from 105 to accommodate all text
        smart_layout = QVBoxLayout(smart_group)
        smart_layout.setContentsMargins(10, 8, 10, 8)  # Increased padding
        smart_layout.setSpacing(8)  # Increased spacing
        
        # Temperature source selector
        source_layout = QHBoxLayout()
        source_label = QLabel("Temperature Source:")
        self.temp_source_combo = QComboBox()
        
        # Build available options
        available_options = ["CPU", "GPU", "Average"]
        
        self.temp_source_combo.addItems(available_options)
        
        # Set current selection, handling fallback if current source is not available
        current_source = self.cpu_monitor.source
        selected_text = "CPU"  # Default fallback
        
        if current_source == "cpu":
            selected_text = "CPU"
        elif current_source == "gpu":
            selected_text = "GPU"
        elif current_source == "average":
            selected_text = "Average"
        else:
            # Fallback to CPU for any other source
            selected_text = "CPU"
            self.cpu_monitor.set_source("cpu")
        
        if selected_text in available_options:
            self.temp_source_combo.setCurrentText(selected_text)
        else:
            self.temp_source_combo.setCurrentText("CPU")
            # Update the monitor source to match the fallback
            self.cpu_monitor.set_source("cpu")
        
        self.temp_source_combo.currentTextChanged.connect(self.on_temp_source_changed)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.temp_source_combo)
        source_layout.addStretch()
        smart_layout.addLayout(source_layout)
        
        # Smart mode enable checkbox
        self.smart_mode_cb = QCheckBox("Enable Smart Mode (Auto-adjust based on temperature)")
        self.smart_mode_cb.setChecked(self.smart_mode_manager.is_smart_mode_enabled())
        self.smart_mode_cb.toggled.connect(self.on_smart_mode_toggle)
        self.smart_mode_cb.setToolTip("Automatically adjust fan speed based on selected temperature source")
        smart_layout.addWidget(self.smart_mode_cb)
        
        # Temperature and config row
        temp_config_row = QHBoxLayout()
        
        # Temperature display (left side)
        temp_info_layout = QVBoxLayout()
        
        self.temp_label = QLabel(f"{self.get_source_display_name()} Temperature: --°C")
        temp_font = QFont()
        temp_font.setBold(True)
        self.temp_label.setFont(temp_font)
        self.temp_label.setStyleSheet("color: #17a2b8; padding: 2px;")
        temp_info_layout.addWidget(self.temp_label)
        
        self.smart_status_label = QLabel("Smart Mode: Off")
        self.smart_status_label.setStyleSheet("color: gray; font-size: 10px; padding: 2px;")
        temp_info_layout.addWidget(self.smart_status_label)
        
        temp_config_row.addLayout(temp_info_layout)
        temp_config_row.addStretch()
        
        # Configure button (right side)
        self.configure_btn = QPushButton("Configure")
        self.configure_btn.clicked.connect(self.open_smart_mode_config)
        self.configure_btn.setToolTip("Configure temperature ranges and RPM settings")
        self.configure_btn.setMinimumWidth(100)
        self.configure_btn.setMaximumWidth(120)
        temp_config_row.addWidget(self.configure_btn)
        
        smart_layout.addLayout(temp_config_row)
        parent_layout.addWidget(smart_group)
        
    def create_footer_section(self, parent_layout):
        """Create footer with version info"""
        # Add small spacer before footer
        parent_layout.addSpacing(8)
        
        footer_label = QLabel("BS2PRO Controller v2.9.0 • Made with ❤️")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: gray; font-size: 10px; padding: 4px;")
        parent_layout.addWidget(footer_label)
        
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        window = self.frameGeometry()
        center = screen.center()
        window.moveCenter(center)
        self.move(window.topLeft())
        
    def setup_monitoring(self):
        """Setup CPU and RPM monitoring"""
        # Setup CPU monitoring callbacks
        self.cpu_monitor.add_callback(self.on_temperature_changed)
        self.cpu_monitor.start_monitoring()
        
        # Setup RPM monitoring callbacks
        self.controller.add_rpm_callback(self.on_rpm_update)
        self.controller.start_rpm_monitoring()
        
        # Setup config monitoring timer to detect external RPM changes
        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.check_config_changes)
        self.config_timer.start(1000)  # Check every second
        
        # Setup device status monitoring timer
        self.device_status_timer = QTimer()
        self.device_status_timer.timeout.connect(self.update_device_status)
        self.device_status_timer.start(1000)  # Check every second
        
    def check_config_changes(self):
        """Check for external config changes (e.g., from CLI commands)"""
        try:
            # Check RPM changes
            current_last_rpm = int(self.config_manager.load_setting("last_rpm", 1900))
            if self.displayed_rpm != current_last_rpm:
                logging.warning(f"Detected RPM change from config: {self.displayed_rpm} -> {current_last_rpm}")
                self.displayed_rpm = current_last_rpm
                # Update the combo box and display
                self.rpm_combo.blockSignals(True)  # Prevent triggering on_rpm_select
                self.rpm_combo.setCurrentText(str(current_last_rpm))
                self.rpm_combo.blockSignals(False)
                self.rpm_display_label.setText(f"Current: {current_last_rpm} RPM")
            
            # Check autostart changes
            current_autostart = self.config_manager.load_setting("autostart", "off")
            if self.displayed_autostart != current_autostart:
                logging.warning(f"Detected autostart change from config: {self.displayed_autostart} -> {current_autostart}")
                self.displayed_autostart = current_autostart
                # Update the combo box
                self.autostart_combo.blockSignals(True)
                self.autostart_combo.setCurrentText(current_autostart.title())
                self.autostart_combo.blockSignals(False)
            
            # Check RPM mode changes
            current_rpm_mode = self.config_manager.load_setting("rpm_mode", "off")
            if self.displayed_rpm_mode != current_rpm_mode:
                logging.warning(f"Detected RPM mode change from config: {self.displayed_rpm_mode} -> {current_rpm_mode}")
                self.displayed_rpm_mode = current_rpm_mode
                # Update the checkbox
                self.rpm_indicator_cb.blockSignals(True)
                self.rpm_indicator_cb.setChecked(current_rpm_mode == "on")
                self.rpm_indicator_cb.blockSignals(False)
            
            # Check start when powered changes
            current_start_powered = self.config_manager.load_setting("start_when_powered", "off")
            if self.displayed_start_powered != current_start_powered:
                logging.warning(f"Detected start_when_powered change from config: {self.displayed_start_powered} -> {current_start_powered}")
                self.displayed_start_powered = current_start_powered
                # Update the checkbox
                self.start_powered_cb.blockSignals(True)
                self.start_powered_cb.setChecked(current_start_powered == "on")
                self.start_powered_cb.blockSignals(False)
                
        except Exception as e:
            logging.debug(f"Error checking config changes: {e}")
        
    def setup_system_tray(self):
        """Setup system tray icon"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            
            # Set icon
            if self.icon_path and os.path.exists(self.icon_path):
                self.tray_icon.setIcon(QIcon(self.icon_path))
            else:
                # Fallback icon
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor('blue'))
                self.tray_icon.setIcon(QIcon(pixmap))
            
            # Create context menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show_window)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            smart_action = QAction("Toggle Smart Mode", self)
            smart_action.triggered.connect(self.toggle_smart_mode_from_tray)
            tray_menu.addAction(smart_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Exit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.setToolTip("BS2PRO Controller")
            
            # Connect double-click to show window
            self.tray_icon.activated.connect(self.on_tray_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
            logging.info("System tray icon created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create system tray icon: {e}")
            self.tray_icon = None
            
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
            
    def show_window(self):
        """Show and restore window"""
        self.show()
        self.raise_()
        self.activateWindow()
        
    def toggle_smart_mode_from_tray(self):
        """Toggle smart mode from tray menu"""
        current_state = self.smart_mode_cb.isChecked()
        self.smart_mode_cb.setChecked(not current_state)
        
    def quit_application(self):
        """Quit the application"""
        self.cleanup()
        QApplication.quit()
        
    # Event handlers
    def on_autostart_select(self, selected_value):
        """Handle autostart mode selection"""
        cmd = self.commands[f"autostart_{selected_value.lower()}"]
        success = self.controller.send_command(cmd, status_callback=self.create_status_callback())
        self.config_manager.save_setting("autostart", selected_value.lower())
        if not success:
            self.update_status("Failed to set autostart mode", "#dc3545")
            
    def on_rpm_toggle(self, checked):
        """Handle RPM indicator toggle"""
        cmd = self.commands["rpm_on"] if checked else self.commands["rpm_off"]
        success = self.controller.send_command(cmd, status_callback=self.create_status_callback())
        self.config_manager.save_setting("rpm_mode", "on" if checked else "off")
        if not success:
            self.update_status("Failed to toggle RPM indicator", "#dc3545")
            
    def on_start_toggle(self, checked):
        """Handle start when powered toggle"""
        success = True
        status_callback = self.create_status_callback()
        if checked:
            success = self.controller.send_command(self.commands["startwhenpowered_on"], status_callback=status_callback)
        else:
            for cmd in self.commands["startwhenpowered_off"]:
                if not self.controller.send_command(cmd, status_callback=status_callback):
                    success = False
        self.config_manager.save_setting("start_when_powered", "on" if checked else "off")
        if not success:
            self.update_status("Failed to toggle start when powered", "#dc3545")
            
    def on_rpm_select(self, selected_value):
        """Handle RPM selection"""
        rpm = int(selected_value)
        success = self.controller.send_command(self.rpm_commands[rpm], status_callback=self.create_status_callback())
        self.config_manager.save_setting("last_rpm", rpm)
        if not success:
            self.update_status(f"Failed to set RPM: {rpm}", "#dc3545")
            
    def on_rpm_update(self, rpm):
        """Handle real-time RPM updates"""
        try:
            self.rpm_display_label.setText(f"Current: {rpm} RPM")
            logging.info(f"RPM updated from device: {rpm}")
        except Exception as e:
            logging.error(f"Error updating RPM display: {e}")
            
    def on_temperature_changed(self, temperature):
        """Handle temperature changes"""
        source_name = self.get_source_display_name()
        self.temp_label.setText(f"{source_name} Temperature: {temperature:.1f}°C")
        
        # Auto-adjust RPM if smart mode is enabled
        if self.smart_mode_manager.is_smart_mode_enabled():
            self.auto_adjust_rpm(temperature)
            
    def on_smart_mode_toggle(self, checked):
        """Handle smart mode toggle"""
        self.smart_mode_manager.set_enabled(checked)
        
        if checked:
            try:
                ranges = self.smart_mode_manager.get_temperature_ranges()
                if not ranges:
                    self.smart_status_label.setText("Smart Mode: No temperature ranges configured")
                    self.smart_status_label.setStyleSheet("color: #ffc107;")
                    return
                
                current_temp = self.cpu_monitor.get_temperature()
                if current_temp <= 0:
                    self.smart_status_label.setText("Smart Mode: On - Waiting for temperature data")
                    self.smart_status_label.setStyleSheet("color: #17a2b8;")
                    return
                
                self.smart_status_label.setText(f"Smart Mode: On - Monitoring {self.get_source_display_name()} temperature")
                self.smart_status_label.setStyleSheet("color: #28a745;")
                
                # Auto-adjust with a small delay
                QTimer.singleShot(100, lambda: self.auto_adjust_rpm(current_temp))
                
            except Exception as e:
                logging.error(f"Error enabling smart mode: {e}")
                self.smart_status_label.setText("Smart Mode: Error - Check configuration")
                self.smart_status_label.setStyleSheet("color: #dc3545;")
        else:
            self.smart_status_label.setText("Smart Mode: Off")
            self.smart_status_label.setStyleSheet("color: gray;")
            self.current_rpm = None
            
    def auto_adjust_rpm(self, temperature):
        """Automatically adjust RPM based on temperature"""
        try:
            target_rpm = self.smart_mode_manager.get_rpm_for_temperature(temperature)
            range_info = self.smart_mode_manager.get_range_for_temperature(temperature)
            
            # Validate target RPM
            if target_rpm is None or target_rpm < 1000 or target_rpm > 3000:
                logging.warning(f"Invalid target RPM: {target_rpm}")
                self.smart_status_label.setText("Smart Mode: Invalid RPM configuration")
                self.smart_status_label.setStyleSheet("color: #dc3545;")
                return
            
            # Check if RPM command exists
            if target_rpm not in self.rpm_commands:
                logging.warning(f"RPM command not found for {target_rpm}")
                self.smart_status_label.setText("Smart Mode: RPM command not available")
                self.smart_status_label.setStyleSheet("color: #dc3545;")
                return
            
            # Only change RPM if it's different from current
            if target_rpm != self.current_rpm:
                self.current_rpm = target_rpm
                
                # Send command to device
                success = self.controller.send_command(self.rpm_commands[target_rpm], status_callback=self.create_status_callback())
                
                if success:
                    # Update combobox selection
                    self.rpm_combo.setCurrentText(str(target_rpm))
                    
                    # Update smart status
                    if range_info:
                        self.smart_status_label.setText(f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)")
                        self.smart_status_label.setStyleSheet("color: #28a745;")
                    else:
                        self.smart_status_label.setText(f"Smart Mode: {target_rpm} RPM (Auto)")
                        self.smart_status_label.setStyleSheet("color: #28a745;")
                    
                    # Save setting
                    self.config_manager.save_setting("last_rpm", target_rpm)
                else:
                    self.smart_status_label.setText("Smart Mode: Failed to adjust RPM")
                    self.smart_status_label.setStyleSheet("color: #dc3545;")
            else:
                # RPM is already correct, just update status
                if range_info:
                    self.smart_status_label.setText(f"Smart Mode: {range_info['description']} ({range_info['min_temp']}-{range_info['max_temp']}°C)")
                    self.smart_status_label.setStyleSheet("color: #28a745;")
                else:
                    self.smart_status_label.setText(f"Smart Mode: {target_rpm} RPM (Auto)")
                    self.smart_status_label.setStyleSheet("color: #28a745;")
                    
        except Exception as e:
            logging.error(f"Error in auto RPM adjustment: {e}")
            self.smart_status_label.setText("Smart Mode: Error")
            self.smart_status_label.setStyleSheet("color: #dc3545;")
            
    def open_smart_mode_config(self):
        """Open the smart mode configuration dialog"""
        try:
            dialog = SmartModeConfigDialog(self, self.smart_mode_manager)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Configuration was saved, update status
                self.update_status("Smart mode configuration updated", "#28a745")
                # Refresh smart mode status if it's currently active
                if self.smart_mode_cb.isChecked():
                    self.on_temperature_changed(self.cpu_monitor.get_temperature())
        except Exception as e:
            logging.error(f"Error opening smart mode config: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open configuration dialog: {e}")
    
    def on_temp_source_changed(self, source_text):
        """Handle temperature source selection change"""
        source_map = {
            "CPU": "cpu",
            "GPU": "gpu", 
            "Average": "average"
        }
        
        source = source_map.get(source_text, "cpu")
        self.cpu_monitor.set_source(source)
        
        # Save to config
        self.config_manager.save_setting("temperature_source", source)
        
        # Update temperature display
        self.update_temperature_display()
        
        # Update smart mode tooltip
        if self.smart_mode_cb:
            self.smart_mode_cb.setToolTip(f"Automatically adjust fan speed based on {source_text} temperature")
            
    def update_temperature_display(self):
        """Update the temperature display with current temperature"""
        current_temp = self.cpu_monitor.get_temperature()
        source_name = self.get_source_display_name()
        self.temp_label.setText(f"{source_name} Temperature: {current_temp:.1f}°C")
            
    def get_source_display_name(self):
        """Get display name for current temperature source"""
        source_map = {
            "cpu": "CPU",
            "gpu": "GPU", 
            "average": "Average"
        }
        
        return source_map.get(self.cpu_monitor.source, "CPU")
            
    def open_smart_mode_config(self):
        """Open smart mode configuration dialog"""
        dialog = SmartModeConfigDialog(self, self.smart_mode_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Configuration was saved, update display
            logging.info("Smart mode configuration updated")
            
    def create_status_callback(self):
        """Create status callback for device operations"""
        def status_callback(msg, style):
            color_map = {
                "success": "#28a745",
                "danger": "#dc3545", 
                "warning": "#ffc107",
                "info": "#17a2b8",
                "light": "#6c757d"
            }
            color = color_map.get(style, "#ffffff")
            self.update_status(msg, color)
            # Auto-reset status after 2 seconds
            QTimer.singleShot(2000, self.update_device_status)
        return status_callback
        
    def update_status(self, message, color):
        """Update status message with color"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
    def update_device_status(self):
        """Update device status display"""
        vid, pid, device_path = self.controller.detect_bs2pro()
        if vid and pid:
            self.update_status(f"✅ BS2PRO detected (VID: {hex(vid)}, PID: {hex(pid)})", "#28a745")
        else:
            self.update_status("❌ BS2PRO not detected", "#dc3545")
            
    # Window event handlers
    def closeEvent(self, event):
        """Handle window close event"""
        if self.minimize_to_tray and self.tray_icon and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            self.hide()
            event.ignore()
        else:
            # Actually close the application
            self.cleanup()
            event.accept()
            
    def changeEvent(self, event):
        """Handle window state changes"""
        if (event.type() == event.Type.WindowStateChange and 
            self.minimize_to_tray and 
            self.tray_icon and 
            self.tray_icon.isVisible() and 
            self.isMinimized()):
            # Hide window when minimized if tray is available
            self.hide()
            event.ignore()
        else:
            super().changeEvent(event)
            
    def cleanup(self):
        """Cleanup resources"""
        if self.cpu_monitor:
            self.cpu_monitor.stop_monitoring()
        if self.controller:
            self.controller.stop_rpm_monitoring()
        if hasattr(self, 'config_timer') and self.config_timer:
            self.config_timer.stop()
        if hasattr(self, 'device_status_timer') and self.device_status_timer:
            self.device_status_timer.stop()
        if self.tray_icon:
            self.tray_icon.hide()


class SmartModeConfigDialog(QDialog):
    """Smart Mode Configuration Dialog"""
    
    def __init__(self, parent, smart_mode_manager):
        super().__init__(parent)
        self.smart_mode_manager = smart_mode_manager
        self.range_widgets = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Smart Mode Configuration")
        self.setModal(True)
        self.resize(800, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Fan Speed Configuration")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Profile selection
        profile_layout = QHBoxLayout()
        profile_label = QLabel("Profile:")
        profile_label.setStyleSheet("font-weight: bold;")
        profile_layout.addWidget(profile_label)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("🔇 Quiet (Conservative)", "quiet")
        self.profile_combo.addItem("⚖️ Balanced (Recommended)", "balanced") 
        self.profile_combo.addItem("🚀 Performance (Aggressive)", "performance")
        self.profile_combo.addItem("🎛️ Custom", "custom")
        self.profile_combo.setCurrentText("⚖️ Balanced (Recommended)")  # Default to balanced
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_combo)
        
        profile_layout.addStretch()
        layout.addLayout(profile_layout)
        
        # Graph widget (only mode now)
        self.graph_widget = TemperatureRPMGraph()
        self.graph_widget.pointsChanged.connect(self.on_graph_points_changed)
        layout.addWidget(self.graph_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Load existing ranges into both modes (after UI is fully set up)
        try:
            self.load_ranges()
        except Exception as e:
            logging.error(f"Error loading ranges: {e}")
            # Continue without loading ranges
            
    def create_graph_mode_widget(self):
        """Create the graph-based configuration widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel("Click on the graph to add temperature/RPM points.\n"
                             "Right-click points to remove them.\n"
                             "The fan will interpolate between points.")
        instructions.setStyleSheet("color: gray;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create the graph widget
        self.graph_widget = TemperatureRPMGraph()
        layout.addWidget(self.graph_widget)
        
        # Connect graph changes to preview update
        self.graph_widget.pointsChanged.connect(self.update_preview)
        
        return widget
        
    def create_range_mode_widget(self):
        """Create the traditional range configuration widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area for ranges
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        # Widget inside scroll area
        scroll_widget = QWidget()
        self.ranges_layout = QVBoxLayout(scroll_widget)
        self.ranges_layout.setSpacing(6)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add New Range")
        add_btn.clicked.connect(self.add_new_range)
        controls_layout.addWidget(add_btn)
        
        sort_btn = QPushButton("Sort Ranges")
        sort_btn.clicked.connect(self.sort_ranges)
        sort_btn.setToolTip("Sort temperature ranges by minimum temperature")
        controls_layout.addWidget(sort_btn)
        
        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self.validate_ranges)
        validate_btn.setToolTip("Check if the current configuration is valid")
        controls_layout.addWidget(validate_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        return widget
        
    def on_mode_changed(self):
        """Handle mode change between graph and range modes"""
        mode = self.mode_combo.currentData()
        if mode == "graph":
            self.stacked_widget.setCurrentIndex(0)  # Graph mode widget
            self.update_preview()
        else:
            self.stacked_widget.setCurrentIndex(1)  # Range mode widget
            self.update_preview()
        
    def center_dialog(self):
        """Center dialog on parent"""
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            center_point = parent_geometry.center()
            dialog_geometry = self.frameGeometry()
            dialog_geometry.moveCenter(center_point)
            self.move(dialog_geometry.topLeft())
            
    def load_ranges(self):
        """Load existing temperature ranges into graph widget"""
        try:
            ranges = self.smart_mode_manager.get_temperature_ranges()
            if ranges:
                # Convert ranges to graph points and load them
                self.graph_widget.set_ranges(ranges)
        except Exception as e:
            logging.error(f"Error loading ranges into graph: {e}")
            # Continue with default points
            
    def on_profile_changed(self):
        """Handle profile selection changes"""
        profile = self.profile_combo.currentData()
        if profile == "custom":
            return  # Don't change anything for custom
        
        # Set flag to prevent switching to custom mode during profile setting
        self._setting_profile = True
        
        # Define the three preset profiles based on your image and suggestions
        profiles = {
            "quiet": [
                # Conservative: Lower RPMs, more gradual increase
                (30, 1300), (40, 1300), (50, 1300), (60, 1700), 
                (70, 1900), (80, 2100), (90, 2400), (100, 2400)
            ],
            "balanced": [
                # Based on the curve shown in your image
                (30, 1300), (40, 1300), (50, 1700), (60, 1900),
                (70, 2100), (80, 2400), (90, 2700), (100, 2700)
            ],
            "performance": [
                # Aggressive: Higher RPMs, quicker response
                (30, 1300), (40, 1700), (50, 1900), (60, 2100),
                (70, 2400), (80, 2700), (90, 2700), (100, 2700)
            ]
        }
        
        if profile in profiles:
            # Set the points for the selected profile
            points = profiles[profile]
            self.graph_widget.points = list(points)
            self.graph_widget.update_plot()
            self.graph_widget.pointsChanged.emit()
            
        self._setting_profile = False
            
    def on_graph_points_changed(self):
        """Handle when graph points are changed manually - switch to Custom mode"""
        # Only switch to custom if we're not already setting a profile
        if hasattr(self, '_setting_profile') and self._setting_profile:
            return
            
        # Check if current points match any preset profile
        current_points = set(self.graph_widget.points)
        
        profiles = {
            "quiet": set([
                (30, 1300), (40, 1300), (50, 1300), (60, 1700), 
                (70, 1900), (80, 2100), (90, 2400), (100, 2400)
            ]),
            "balanced": set([
                (30, 1300), (40, 1300), (50, 1700), (60, 1900),
                (70, 2100), (80, 2400), (90, 2700), (100, 2700)
            ]),
            "performance": set([
                (30, 1300), (40, 1700), (50, 1900), (60, 2100),
                (70, 2400), (80, 2700), (90, 2700), (100, 2700)
            ])
        }
        
        # Check if current points match any preset
        matching_profile = None
        for profile_name, profile_points in profiles.items():
            if current_points == profile_points:
                matching_profile = profile_name
                break
        
        # Update combo box without triggering the change handler
        self._setting_profile = True
        if matching_profile:
            if matching_profile == "quiet":
                self.profile_combo.setCurrentText("🔇 Quiet (Conservative)")
            elif matching_profile == "balanced":
                self.profile_combo.setCurrentText("⚖️ Balanced (Recommended)")
            elif matching_profile == "performance":
                self.profile_combo.setCurrentText("🚀 Performance (Aggressive)")
        else:
            self.profile_combo.setCurrentText("🎛️ Custom")
        self._setting_profile = False
            
    def create_range_widget(self, range_data, index):
        """Create a temperature range widget"""
        range_frame = QFrame()
        range_frame.setFrameStyle(QFrame.Shape.Box)
        range_layout = QHBoxLayout(range_frame)
        range_layout.setContentsMargins(6, 6, 6, 6)  # Reduced from 8
        range_layout.setSpacing(6)  # Add tighter spacing between elements
        
        # Min temperature
        range_layout.addWidget(QLabel("Min:"))
        min_spin = QSpinBox()  # Changed from QDoubleSpinBox to QSpinBox
        min_spin.setRange(-50, 200)
        min_spin.setValue(int(range_data['min_temp']))  # Convert to int
        min_spin.setSuffix("°C")
        range_layout.addWidget(min_spin)
        
        # Max temperature
        range_layout.addWidget(QLabel("Max:"))
        max_spin = QSpinBox()  # Changed from QDoubleSpinBox to QSpinBox
        max_spin.setRange(-50, 200)
        max_spin.setValue(int(range_data['max_temp']))  # Convert to int
        max_spin.setSuffix("°C")
        range_layout.addWidget(max_spin)
        
        # RPM
        range_layout.addWidget(QLabel("RPM:"))
        rpm_combo = QComboBox()
        rpm_values = [1300, 1700, 1900, 2100, 2400, 2700]  # Available RPM values
        rpm_combo.addItems([str(rpm) for rpm in rpm_values])
        # Set current value or default to 1300
        current_rpm = str(range_data['rpm'])
        if current_rpm in [str(rpm) for rpm in rpm_values]:
            rpm_combo.setCurrentText(current_rpm)
        else:
            rpm_combo.setCurrentText("1300")  # Default fallback
        rpm_combo.setStyleSheet("padding-left: 8px; padding-right: 8px;")  # Add padding for consistency
        range_layout.addWidget(rpm_combo)
        
        # Description
        range_layout.addWidget(QLabel("Description:"))
        desc_edit = QLineEdit(range_data.get('description', ''))
        desc_edit.setMaximumWidth(120)  # Reduced from 150 for tighter layout
        range_layout.addWidget(desc_edit)
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_range_widget(range_frame))
        remove_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; }")
        range_layout.addWidget(remove_btn)
        
        # Store widget references
        widget_data = {
            'frame': range_frame,
            'min_spin': min_spin,
            'max_spin': max_spin,
            'rpm_combo': rpm_combo,  # Changed from rpm_spin to rpm_combo
            'desc_edit': desc_edit,
            'index': index
        }
        self.range_widgets.append(widget_data)
        self.ranges_layout.addWidget(range_frame)
        
        # Connect signals to update preview
        min_spin.valueChanged.connect(self.update_preview)
        max_spin.valueChanged.connect(self.update_preview)
        rpm_combo.currentTextChanged.connect(self.update_preview)
        desc_edit.textChanged.connect(self.update_preview)
        
    def add_new_range(self):
        """Add a new temperature range"""
        new_range = {
            'min_temp': 0,
            'max_temp': 10,
            'rpm': 1300,
            'description': 'New range'
        }
        self.create_range_widget(new_range, len(self.range_widgets))
        self.update_preview()
        
    def remove_range_widget(self, frame):
        """Remove a temperature range widget"""
        # Find and remove the widget from our list
        for i, widget_data in enumerate(self.range_widgets):
            if widget_data['frame'] == frame:
                self.range_widgets.pop(i)
                break
        
        # Remove from layout and delete
        self.ranges_layout.removeWidget(frame)
        frame.deleteLater()
        
        # Update preview
        self.update_preview()
        
    def sort_ranges(self):
        """Sort temperature ranges by minimum temperature"""
        try:
            if not self.range_widgets:
                QMessageBox.information(self, "No Ranges", "No temperature ranges to sort.")
                return

            # Collect current data
            ranges_data = []
            for widget_data in self.range_widgets:
                min_temp = widget_data['min_spin'].value()
                max_temp = widget_data['max_spin'].value()
                rpm = int(widget_data['rpm_combo'].currentText())
                description = widget_data['desc_edit'].text() or "Range"
                
                ranges_data.append({
                    'min_temp': min_temp,
                    'max_temp': max_temp,
                    'rpm': rpm,
                    'description': description,
                    'widget_data': widget_data
                })
            
            # Check if already sorted
            is_already_sorted = all(
                ranges_data[i]['min_temp'] <= ranges_data[i + 1]['min_temp']
                for i in range(len(ranges_data) - 1)
            )

            if is_already_sorted:
                QMessageBox.information(self, "Already Sorted",
                                      "Temperature ranges are already sorted by minimum temperature.")
                return

            # Sort by minimum temperature
            ranges_data.sort(key=lambda x: x['min_temp'])

            # Clear the current layout properly
            for widget_data in self.range_widgets:
                self.ranges_layout.removeWidget(widget_data['frame'])

            # Reorder range_widgets list and re-add widgets in sorted order
            self.range_widgets = [rd['widget_data'] for rd in ranges_data]

            # Update widget values and re-add to layout
            for i, range_data in enumerate(ranges_data):
                widget_data = range_data['widget_data']
                widget_data['min_spin'].setValue(range_data['min_temp'])
                widget_data['max_spin'].setValue(range_data['max_temp'])
                widget_data['rpm_combo'].setCurrentText(str(range_data['rpm']))
                widget_data['desc_edit'].setText(range_data['description'])
                widget_data['index'] = i

                # Re-add widget to layout
                self.ranges_layout.addWidget(widget_data['frame'])

            QMessageBox.information(self, "Ranges Sorted", 
                                  "Temperature ranges have been sorted by minimum temperature.")
            
        except Exception as e:
            QMessageBox.warning(self, "Sort Error", f"Failed to sort ranges: {e}")
            import logging
            logging.error(f"Sort ranges error: {e}", exc_info=True)
        
        # Update preview after sorting
        self.update_preview()
    
    def validate_ranges(self):
        """Validate the current temperature range configuration"""
        try:
            # Collect data from widgets
            ranges_data = []
            for widget_data in self.range_widgets:
                min_temp = widget_data['min_spin'].value()
                max_temp = widget_data['max_spin'].value()
                rpm = int(widget_data['rpm_combo'].currentText())
                description = widget_data['desc_edit'].text() or "Range"
                
                ranges_data.append({
                    'min_temp': min_temp,
                    'max_temp': max_temp,
                    'rpm': rpm,
                    'description': description
                })
            
            # Sort by min temperature for validation
            ranges_data.sort(key=lambda x: x['min_temp'])
            
            # Validation messages - separate errors and warnings
            error_messages = []
            warning_messages = []
            
            # Check individual ranges (errors)
            for i, range_data in enumerate(ranges_data):
                if range_data['min_temp'] >= range_data['max_temp']:
                    error_messages.append(f"❌ Range {i+1}: Min temperature ({range_data['min_temp']}°C) must be less than max temperature ({range_data['max_temp']}°C)")
            
            # Check for overlaps (errors)
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['max_temp'] > ranges_data[i + 1]['min_temp']:
                    error_messages.append(f"❌ Overlap: Range {i+1} ({ranges_data[i]['max_temp']}°C) overlaps with Range {i+2} ({ranges_data[i+1]['min_temp']}°C)")
            
            # Check RPM progression (warnings)
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['rpm'] >= ranges_data[i + 1]['rpm']:
                    warning_messages.append(f"⚠️ RPM Progression: Range {i+1} ({ranges_data[i]['rpm']} RPM) should have lower RPM than Range {i+2} ({ranges_data[i+1]['rpm']} RPM)")
            
            # Show appropriate message based on validation results
            if not error_messages and not warning_messages:
                QMessageBox.information(self, "Validation Passed", 
                                      "✅ All temperature ranges are valid!\n\n"
                                      "• No overlapping ranges\n"
                                      "• Proper temperature ordering\n"
                                      "• Correct RPM progression (higher temp = higher RPM)")
            elif error_messages and warning_messages:
                # Both errors and warnings - show errors first, then warnings
                error_text = "\n".join(error_messages)
                QMessageBox.warning(self, "Validation Errors", 
                                  f"Critical errors found:\n\n{error_text}\n\nPlease fix these issues before saving.")
                
                warning_text = "\n".join(warning_messages)
                QMessageBox.warning(self, "Validation Warnings", 
                                  f"RPM progression warnings:\n\n{warning_text}\n\nThese are recommendations - you can still save the configuration.")
            elif error_messages:
                # Only errors
                message = "Validation found critical errors:\n\n" + "\n".join(error_messages) + "\n\nPlease fix these issues before saving."
                QMessageBox.warning(self, "Validation Failed", message)
            else:
                # Only warnings
                message = "Validation found warnings (RPM progression):\n\n" + "\n".join(warning_messages) + "\n\nThese are recommendations - you can still save the configuration."
                QMessageBox.warning(self, "Validation Warnings", message)
            
        except Exception as e:
            QMessageBox.warning(self, "Validation Error", f"Failed to validate ranges: {e}")
    
    def update_preview(self):
        """Update the configuration preview"""
        try:
            if not self.range_widgets:
                self.preview_label.setText("Add temperature ranges above to see a preview of how the fan will behave.")
                return
            
            # Collect current data
            ranges_data = []
            for widget_data in self.range_widgets:
                min_temp = widget_data['min_spin'].value()
                max_temp = widget_data['max_spin'].value()
                rpm = int(widget_data['rpm_combo'].currentText())
                description = widget_data['desc_edit'].text() or f"Range {len(ranges_data)+1}"
                
                ranges_data.append({
                    'min_temp': min_temp,
                    'max_temp': max_temp,
                    'rpm': rpm,
                    'description': description
                })
            
            # Sort by temperature for preview
            ranges_data.sort(key=lambda x: x['min_temp'])
            
            # Create preview text
            preview_lines = ["Fan speed behavior preview:"]
            
            for i, range_data in enumerate(ranges_data):
                temp_range = f"{range_data['min_temp']}°C - {range_data['max_temp']}°C"
                preview_lines.append(f"• {temp_range}: {range_data['rpm']} RPM ({range_data['description']})")
            
            # Check for potential issues - separate critical errors from warnings
            critical_issues = []
            warning_issues = []
            
            # Check for invalid ranges (critical)
            for range_data in ranges_data:
                if range_data['min_temp'] >= range_data['max_temp']:
                    critical_issues.append("Invalid temperature range")
                    break
            
            # Check for overlaps (critical)
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['max_temp'] > ranges_data[i + 1]['min_temp']:
                    critical_issues.append("Overlapping ranges")
                    break
            
            # Check RPM progression (warning)
            for i in range(len(ranges_data) - 1):
                if ranges_data[i]['rpm'] >= ranges_data[i + 1]['rpm']:
                    warning_issues.append("RPM doesn't increase with temperature")
                    break
            
            if critical_issues:
                preview_lines.append("")
                preview_lines.append("❌ Critical issues: " + ", ".join(critical_issues))
                self.preview_label.setStyleSheet("color: #dc3545; font-style: italic;")  # Red for critical issues
            elif warning_issues:
                preview_lines.append("")
                preview_lines.append("⚠️ Warning: " + ", ".join(warning_issues))
                self.preview_label.setStyleSheet("color: #ffc107; font-style: italic;")  # Yellow for warnings
            else:
                preview_lines.append("")
                preview_lines.append("✅ Configuration looks good!")
                self.preview_label.setStyleSheet("color: #28a745; font-style: italic;")
            
            self.preview_label.setText("\n".join(preview_lines))
            
        except Exception as e:
            self.preview_label.setText(f"Error updating preview: {e}")
            self.preview_label.setStyleSheet("color: #dc3545; font-style: italic;")
        
    def save_configuration(self):
        """Save the temperature range configuration from graph"""
        try:
            # Get ranges from graph widget
            ranges = self.graph_widget.get_ranges()
            
            if not ranges:
                QMessageBox.warning(self, "No Configuration", "Please configure at least one temperature range.")
                return
            
            # Clear existing ranges and add new ones
            self.smart_mode_manager.temperature_ranges = []
            for range_data in ranges:
                self.smart_mode_manager.add_temperature_range(
                    range_data['min_temp'],
                    range_data['max_temp'],
                    range_data['rpm'],
                    range_data.get('description', 'Graph Range')
                )
            
            # Save configuration
            self.smart_mode_manager.save_config()
            
            # Show success message
            QMessageBox.information(self, "Success", 
                                  f"Smart mode configuration saved with {len(ranges)} ranges!")
            
            # Accept dialog
            self.accept()
            
        except Exception as e:
            logging.error(f"Error saving smart mode config: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")


def apply_gnome_dark_palette(app):
    """Apply GNOME Adwaita dark mode palette colors"""
    try:
        from PyQt6.QtGui import QPalette, QColor
        
        palette = QPalette()
        # Adwaita dark theme colors
        palette.setColor(QPalette.ColorRole.Window, QColor(46, 52, 54))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.Base, QColor(36, 41, 46))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(46, 52, 54))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(46, 52, 54))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.Text, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.Button, QColor(54, 59, 61))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(238, 238, 236))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(252, 175, 62))
        palette.setColor(QPalette.ColorRole.Link, QColor(53, 132, 228))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(53, 132, 228))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        print("🌙 Applied GNOME dark mode palette")
        return True
    except Exception as e:
        print(f"🔍 Could not apply dark palette: {e}")
        return False


def create_qt_application(controller, config_manager, rpm_commands, commands, default_settings, icon_path=None):
    """Create and run the PyQt6 application"""
    # Set Qt environment variables for native theming before creating QApplication
    import os
    
    # Detect actual desktop environment first
    actual_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    
    # Configure Qt platform theme based on actual desktop environment
    if 'kde' in actual_desktop or 'plasma' in actual_desktop:
        os.environ['QT_QPA_PLATFORMTHEME'] = 'kde'
        os.environ['KDE_SESSION_VERSION'] = '5'
    elif 'gnome' in actual_desktop:
        # For GNOME, try gtk3 first (better libadwaita integration)
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
        
        # Detect GNOME dark/light theme preference
        try:
            import subprocess
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                color_scheme = result.stdout.strip().strip("'\"")
                if 'dark' in color_scheme.lower():
                    os.environ['GTK_THEME'] = 'Adwaita:dark'
                    print(f"🌙 Detected GNOME dark mode: {color_scheme}")
                else:
                    os.environ['GTK_THEME'] = 'Adwaita'
                    print(f"☀️ Detected GNOME light mode: {color_scheme}")
            else:
                # Fallback: check gtk-theme setting
                result2 = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                                       capture_output=True, text=True, timeout=2)
                if result2.returncode == 0:
                    gtk_theme = result2.stdout.strip().strip("'\"")
                    if 'dark' in gtk_theme.lower():
                        os.environ['GTK_THEME'] = 'Adwaita:dark'
                        print(f"🌙 Detected dark GTK theme: {gtk_theme}")
                    else:
                        os.environ['GTK_THEME'] = 'Adwaita'
                        print(f"☀️ Detected light GTK theme: {gtk_theme}")
        except Exception as e:
            print(f"🔍 Could not detect GNOME theme preference: {e}")
            # Safe fallback
            os.environ['GTK_THEME'] = 'Adwaita'
    elif 'xfce' in actual_desktop:
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
    else:
        # For other DEs, use gtk3 as a safe fallback
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
    
    # Don't override the style - let Qt choose the appropriate one
    os.environ['QT_STYLE_OVERRIDE'] = ''
    
    # Force Qt to use X11 instead of Wayland for better theme support
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    # Set Qt plugin paths - detect distribution-specific paths
    qt_plugin_paths = []
    
    # Common Qt6 plugin paths for different distributions
    potential_paths = [
        '/usr/lib64/qt6/plugins',           # Fedora, RHEL, CentOS, openSUSE
        '/usr/lib/x86_64-linux-gnu/qt6/plugins',  # Ubuntu, Debian
        '/usr/lib/qt6/plugins',             # Generic fallback
        '/usr/local/lib/qt6/plugins'        # Local installations
    ]
    
    # Add only existing paths
    for path in potential_paths:
        if os.path.exists(path):
            qt_plugin_paths.append(path)
    
    # Set Qt plugin path environment variable
    if qt_plugin_paths:
        os.environ['QT_PLUGIN_PATH'] = ':'.join(qt_plugin_paths)
    # Log a concise Qt environment summary instead of many individual prints
    qt_summary = {
        'plugin_paths': os.environ.get('QT_PLUGIN_PATH'),
        'platform_theme': os.environ.get('QT_QPA_PLATFORMTHEME'),
        'platform': os.environ.get('QT_QPA_PLATFORM')
    }
    logging.info(f"Qt environment: plugin_paths={qt_summary['plugin_paths']}, "
                 f"platform_theme={qt_summary['platform_theme']}, platform={qt_summary['platform']}")
    
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    # Force system plugin paths, not venv paths - use detected paths
    if qt_plugin_paths:
        app.setLibraryPaths(qt_plugin_paths)
        logging.debug(f"Qt app library paths set to: {app.libraryPaths()}")
        
    # Set application properties
    app.setApplicationName("BS2PRO Controller")
    app.setApplicationVersion("2.9.0")
    app.setOrganizationName("BS2PRO")
    
    # Debug: store current style information, log concisely
    current_style_name = app.style().objectName()
    logging.debug(f"Initial Qt style: {current_style_name}")
    
    try:
        from PyQt6.QtWidgets import QStyleFactory
        available_styles = QStyleFactory.keys()

        # Try to detect and set the appropriate native style
        import os
        desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        logging.debug(f"Desktop Environment detected: {desktop_env}")

        # Add detected Qt plugin paths
        for plugin_path in qt_plugin_paths:
            if os.path.exists(plugin_path):
                app.addLibraryPath(plugin_path)
                logging.debug(f"Added Qt plugin path: {plugin_path}")

        # Refresh available styles after adding plugin paths
        available_styles = QStyleFactory.keys()
        logging.debug(f"Available Qt styles: {', '.join(available_styles)}")

        # Try to set native style based on desktop environment
        style_set_successfully = False

        current_style = app.style().objectName().lower()

        if 'gnome' in desktop_env:
            # For GNOME, prefer system theme integration
            # If no GTK integration is available, Fusion is acceptable for GNOME
            if current_style in ['windows'] and 'Fusion' in available_styles:
                try:
                    fusion_style = QStyleFactory.create('Fusion')
                    if fusion_style:
                        app.setStyle(fusion_style)
                        logging.info("Set Fusion style for GNOME (good libadwaita-like appearance)")
                        # Apply dark palette if GNOME is in dark mode
                        if os.environ.get('GTK_THEME', '').endswith(':dark'):
                            apply_gnome_dark_palette(app)
                        style_set_successfully = True
                except Exception as e:
                    logging.debug(f"Could not set Fusion style: {e}")
            else:
                logging.info(f"Using system-chosen Qt style for GNOME: {current_style}")
                # Apply dark palette if in dark mode, regardless of style
                if os.environ.get('GTK_THEME', '').endswith(':dark'):
                    apply_gnome_dark_palette(app)
                style_set_successfully = True
        elif current_style == 'windows' and 'Fusion' in available_styles:
            # Windows style is usually not desirable on Linux - prefer Fusion
            try:
                fusion_style = QStyleFactory.create('Fusion')
                if fusion_style:
                    app.setStyle(fusion_style)
                    logging.info("Upgraded from Windows style to Fusion for better Linux experience")
                    style_set_successfully = True
            except Exception as e:
                logging.debug(f"Could not set Fusion style: {e}")
        else:
            # Let the system theme take precedence
            logging.info(f"Using system-chosen Qt style: {current_style}")
            style_set_successfully = True

        # Final verification
        final_style = app.style().objectName()
        logging.info(f"Active Qt style: {final_style}")

        # If no style was set successfully, ensure we at least have Fusion (better than Windows)
        if not style_set_successfully and final_style.lower() == 'windows':
            if 'Fusion' in available_styles:
                try:
                    fusion_style = QStyleFactory.create('Fusion')
                    if fusion_style:
                        app.setStyle(fusion_style)
                        logging.info("Applied Fusion as fallback (better than Windows style)")
                except Exception:
                    pass
    except Exception as e:
        logging.debug(f"Could not get/set Qt style info: {e}")
    
    # Enable automatic high DPI scaling (if available in this PyQt6 version)
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # These attributes may not be available in newer PyQt6 versions
        # High DPI is handled automatically in newer versions
        pass
    
    # Create main window
    window = BS2ProQtGUI(controller, config_manager, rpm_commands, commands, default_settings, icon_path)
    
    # Run application
    return app.exec()