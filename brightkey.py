import screen_brightness_control as sbc
import keyboard
import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QProgressBar, QLabel, QVBoxLayout, 
                            QSystemTrayIcon, QMenu, QAction, QDialog, QGridLayout,
                            QPushButton, QSpinBox, QHBoxLayout, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QSize, pyqtSignal, QObject, QSettings
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPainterPath, QPen, QImage, QPixmap, QKeySequence



# Global variables and configuration
CONFIG_FILE = "brightkey_config.json"
# Default settings
increase_key = "win+enter"
decrease_key = "win+shift"
step_size = 10


def load_settings():
    global increase_key, decrease_key, step_size
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                increase_key = config.get("increase_key", increase_key)
                decrease_key = config.get("decrease_key", decrease_key)
                step_size = config.get("step_size", step_size)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        # Using default values

def save_settings(settings=None):
    if settings is None:
        settings = {
            "increase_key": increase_key,
            "decrease_key": decrease_key,
            "step_size": step_size
        }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Error saving configuration: {e}")

def decrease_brightness():
    current = sbc.get_brightness(display=0)  # Get current brightness
    current = current[0]
    new_brightness = max(0, current - step_size)   # Decrease brightness
    sbc.set_brightness(new_brightness, display=0)
    # Send brightness value through signal
    signal_emitter.brightness_changed.emit(new_brightness)
    print(f"Brightness decreased to {new_brightness}%")

def increase_brightness():
    current = sbc.get_brightness(display=0)
    current = current[0]
    new_brightness = min(100, current + step_size)
    sbc.set_brightness(new_brightness, display=0)
    # Send brightness value through signal
    signal_emitter.brightness_changed.emit(new_brightness)
    print(f"Brightness increased to {new_brightness}%")


# Create signal emitter class for inter-thread communication
class BrightnessSignalEmitter(QObject):
    # Define signal
    brightness_changed = pyqtSignal(int)

# Create signal emitter instance
signal_emitter = BrightnessSignalEmitter()

class BrightnessOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # Set window properties: frameless and transparent background
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        
        self.visible_state = False  
        
        self.init_ui()
        
        # Setup timer and animation variables
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.start_fade_out)
        self.fade_animation = None


    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Brightness icon label
        self.icon_label = QLabel("🔆")
        self.icon_label.setFont(QFont("Segoe UI", 28))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("color: white;")
        
        # Brightness percentage label
        self.percent_label = QLabel("50%")
        self.percent_label.setFont(QFont("Segoe UI", 14))
        self.percent_label.setAlignment(Qt.AlignCenter)
        self.percent_label.setStyleSheet("color: white; margin-bottom: 5px;")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(50)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        # self.progress_bar.setFixedWidth(300)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(80, 80, 80, 150);
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: white;
                border-radius: 3px;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(self.icon_label)
        layout.addWidget(self.percent_label)
        layout.addWidget(self.progress_bar)
        layout.setAlignment(Qt.AlignCenter)
        
        self.setLayout(layout)
        # self.setFixedSize(350, 350)
        
        # Set window overall style - Adjust background color and opacity
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 220); /* Deeper background color */
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 30); /* Add subtle border */
            }
        """)
    
    # Add shadow effect
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow
        path = QPainterPath()
        path.addRoundedRect(5, 5, self.width()-10, self.height()-10, 10, 10)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 20, 20, 100))
        painter.drawPath(path.translated(2, 2))
        
        super().paintEvent(event)

    def show_with_value(self, value):
        # Update value
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")
        
        # Stop any timers and animations
        self.hide_timer.stop()
        if self.fade_animation and self.fade_animation.state() == QPropertyAnimation.Running:
            self.fade_animation.stop()
            
        # If already visible, just reset timer and return
        if self.isVisible() and self.windowOpacity() > 0.5 and self.visible_state:
            self.hide_timer.start(2000)
            return
            
        # Window not visible, need to show it
        self.visible_state = True
        
        # Calculate position (UI components may change size, recalculate each time)
        self.adjustSize()  # Adjust size to fit content first
        screen_geometry = QApplication.primaryScreen().geometry()
        x = int((screen_geometry.width() - self.width()) // 2)
        y = int(screen_geometry.height() * 0.67)
        self.move(x, y)
        
        # Show window (fully opaque)
        self.setWindowOpacity(1.0)
        self.show()
        
        # Start hide timer
        self.hide_timer.start(2000)

    def start_fade_out(self):
        # Create and start fade-out animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide_and_reset)
        self.fade_animation.start()
    
    def hide_and_reset(self):
        # Hide window and reset state
        self.hide()
        self.visible_state = False

# Create system tray icon class
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        # Create tray icon
        icon = self.create_tray_icon()
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.app = app
        self.setup_menu()
        self.show()
        
    def create_tray_icon(self):
        # Create a simple brightness icon
        img = QImage(64, 64, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circle
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor(255, 204, 0))
        painter.drawEllipse(12, 12, 40, 40)
        
        # Draw rays
        import math
        painter.setPen(QPen(QColor(255, 204, 0), 3))
        for i in range(8):
            angle = i * 45 * math.pi / 180  # Convert to radians
            # Calculate start coordinates (from edge of circle)
            x1 = 32 + 20 * math.cos(angle)  
            y1 = 32 + 20 * math.sin(angle)
            # Calculate end coordinates (extending outward)
            x2 = 32 + 30 * math.cos(angle)  
            y2 = 32 + 30 * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.end()
        
        return QIcon(QPixmap.fromImage(img))
    
    def setup_menu(self):
        # Create context menu
        menu = QMenu()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # Separator
        menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.user_quit)
        menu.addAction(exit_action)
        
        # Set tray icon's context menu
        self.setContextMenu(menu)
        # Allow clicking tray icon to show menu
        self.activated.connect(self.on_tray_icon_activated)

    def user_quit(self):
        # Save settings before exiting
        print("Saving settings before exit")
        save_settings()
        self.app.quit()
    
    def show_settings(self):
        # Get current settings
        current_settings = {
            "increase_key": increase_key,
            "decrease_key": decrease_key,
            "step_size": step_size
        }
        
        # Show settings dialog
        dialog = SettingsDialog(None, current_settings)
        dialog.settingsChanged.connect(self.apply_settings)
        dialog.exec_()
    
    def apply_settings(self, new_settings):
        # Use global variables
        global increase_key, decrease_key, step_size
        
        try:
            # Cancel old hotkeys
            try:
                if increase_key:
                    keyboard.remove_hotkey(increase_key)
            except Exception as e:
                print(f"Error removing old hotkey (increase): {e}")
            
            try:
                if decrease_key:
                    keyboard.remove_hotkey(decrease_key)
            except Exception as e:
                print(f"Error removing old hotkey (decrease): {e}")
            
            # Apply new settings
            increase_key = new_settings["increase_key"]
            decrease_key = new_settings["decrease_key"]
            step_size = new_settings["step_size"]
            
            # Register new hotkeys - Add exception handling
            try:
                keyboard.add_hotkey(increase_key, increase_brightness)
                print(f"Increase brightness hotkey set: {increase_key}")
            except Exception as e:
                print(f"Failed to set increase hotkey: {e}")
                # If failed, try to restore default value
                increase_key = "win+enter"
                keyboard.add_hotkey(increase_key, increase_brightness)
                print(f"Restored default increase hotkey: {increase_key}")
            
            try:
                keyboard.add_hotkey(decrease_key, decrease_brightness)
                print(f"Decrease brightness hotkey set: {decrease_key}")
            except Exception as e:
                print(f"Failed to set decrease hotkey: {e}")
                # Restore default value
                decrease_key = "win+shift"
                keyboard.add_hotkey(decrease_key, decrease_brightness)
                print(f"Restored default decrease hotkey: {decrease_key}")
            
            # Save settings to config file
            save_settings({
                "increase_key": increase_key,
                "decrease_key": decrease_key,
                "step_size": step_size
            })
            
            print(f"Settings updated: Increase={increase_key}, Decrease={decrease_key}, Step={step_size}%")
        except Exception as e:
            print(f"Error applying settings: {e}")
            # Ensure program doesn't crash due to settings issues
        
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Single click
            self.contextMenu().popup(self.geometry().center())

    
    def save_icon_as_ico(self, filepath="brightness_icon.ico"):
        # Create icon image
        img = QImage(64, 64, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circle
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor(255, 204, 0))
        painter.drawEllipse(17, 17, 30, 30)
        
        # Draw rays
        painter.setPen(QPen(QColor(255, 204, 0), 3))
        import math
        for i in range(8):
            angle = i * 45 * math.pi / 180  # Convert to radians
            # Calculate start coordinates (from edge of circle)
            x1 = 32 + 20 * math.cos(angle)  
            y1 = 32 + 20 * math.sin(angle)
            # Calculate end coordinates (extending outward)
            x2 = 32 + 30 * math.cos(angle)  
            y2 = 32 + 30 * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.end()
        
        # Convert to QPixmap and save
        pixmap = QPixmap.fromImage(img)
        
        # Try to save directly as ico file
        success = pixmap.save(filepath, "ICO")
        
        if success:
            print(f"Icon saved to: {os.path.abspath(filepath)}")
        else:
            # If can't save directly as ICO, save as PNG
            png_path = filepath.replace('.ico', '.png')
            success = pixmap.save(png_path, "PNG")
            if success:
                print(f"Icon saved as PNG: {os.path.abspath(png_path)}")
                print("Note: To convert to ICO file, you may need an image editing tool")
            else:
                print("Failed to save icon")


class SettingsDialog(QDialog):
    settingsChanged = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_settings=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("BrightKey Settings")
        self.setMinimumWidth(400)
        self.current_settings = current_settings or {
            "increase_key": "win+enter",
            "decrease_key": "win+shift",
            "step_size": 10
        }
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Hotkey settings group
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QGridLayout()

        # add a warning label
        hotkey_layout.addWidget(QLabel("*BrightKey will automatically quit after changing settings, please reastart it to apply the new settings."), 3, 0, 1, 2)

        
        hotkey_layout.addWidget(QLabel("Increase Brightness:"), 0, 0)
        self.increase_key_edit = QLineEdit()
        self.increase_key_edit.setPlaceholderText("Example: win+enter")
        hotkey_layout.addWidget(self.increase_key_edit, 0, 1)
        
        hotkey_layout.addWidget(QLabel("Decrease Brightness:"), 1, 0)
        self.decrease_key_edit = QLineEdit()
        self.decrease_key_edit.setPlaceholderText("Example: win+shift")
        hotkey_layout.addWidget(self.decrease_key_edit, 1, 1)
        
        hotkey_layout.addWidget(QLabel("Note: Use keyboard library format, like 'ctrl+shift+a'"), 2, 0, 1, 2)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # Adjustment step settings group
        step_group = QGroupBox("Step Size Settings")
        step_layout = QHBoxLayout()
        
        step_layout.addWidget(QLabel("Brightness adjustment step size:"))
        self.step_size_spin = QSpinBox()
        self.step_size_spin.setRange(1, 100)
        self.step_size_spin.setSuffix("%")
        step_layout.addWidget(self.step_size_spin)
        
        step_group.setLayout(step_layout)
        layout.addWidget(step_group)
        
        # Button area
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_settings(self):
        self.increase_key_edit.setText(self.current_settings["increase_key"])
        self.decrease_key_edit.setText(self.current_settings["decrease_key"])
        self.step_size_spin.setValue(self.current_settings["step_size"])
    
    def save_settings(self):
        new_settings = {
            "increase_key": self.increase_key_edit.text(),
            "decrease_key": self.decrease_key_edit.text(),
            "step_size": self.step_size_spin.value()
        }
        self.settingsChanged.emit(new_settings)
        self.accept()



# Global variables
app = QApplication(sys.argv)
load_settings()
overlay = BrightnessOverlay()

# Create system tray icon
tray_icon = SystemTrayIcon(app)
# tray_icon.save_icon_as_ico()

# Connect signal to UI update function
signal_emitter.brightness_changed.connect(overlay.show_with_value)


# Monitor hotkeys
keyboard.add_hotkey(increase_key, increase_brightness)
keyboard.add_hotkey(decrease_key, decrease_brightness)

print(f"Press {decrease_key} to decrease brightness, {increase_key} to increase brightness")
print("Program is running in system tray, right-click the tray icon to exit")

# Show current brightness
current = sbc.get_brightness(display=0)[0]
overlay.show_with_value(current)

# Use timer to keep Qt event loop running while not blocking keyboard library
timer = QTimer()
timer.timeout.connect(lambda: None)
timer.start(100)

sys.exit(app.exec_())