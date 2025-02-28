import screen_brightness_control as sbc
import keyboard
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QProgressBar, QLabel, QVBoxLayout, 
                            QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPainterPath, QPen, QImage, QPixmap

# 创建一个信号发射器类来进行线程间通信
class BrightnessSignalEmitter(QObject):
    # 定义信号
    brightness_changed = pyqtSignal(int)

# 创建信号发射器实例
signal_emitter = BrightnessSignalEmitter()

class BrightnessOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口无边框和透明背景
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        
        self.visible_state = False  
        
        self.init_ui()
        
        # 简化定时器和动画变量
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.start_fade_out)
        self.fade_animation = None


    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 亮度图标标签
        self.icon_label = QLabel("🔆")
        self.icon_label.setFont(QFont("Segoe UI", 28))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("color: white;")
        
        # 亮度百分比标签
        self.percent_label = QLabel("50%")
        self.percent_label.setFont(QFont("Segoe UI", 14))
        self.percent_label.setAlignment(Qt.AlignCenter)
        self.percent_label.setStyleSheet("color: white; margin-bottom: 5px;")
        
        # 进度条
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
        
        # 添加控件到布局
        layout.addWidget(self.icon_label)
        layout.addWidget(self.percent_label)
        layout.addWidget(self.progress_bar)
        layout.setAlignment(Qt.AlignCenter)
        
        self.setLayout(layout)
        # self.setFixedSize(350, 350)
        
        # 设置窗口整体样式 - 调整背景颜色更深，增加不透明度
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 220); /* 更深的背景色 */
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 30); /* 添加微弱边框 */
            }
        """)
    
    # 添加阴影效果
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制阴影
        path = QPainterPath()
        path.addRoundedRect(5, 5, self.width()-10, self.height()-10, 10, 10)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 20, 20, 100))
        painter.drawPath(path.translated(2, 2))
        
        super().paintEvent(event)

    def show_with_value(self, value):
        # 更新值
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")
        
        # 停止任何计时器和动画
        self.hide_timer.stop()
        if self.fade_animation and self.fade_animation.state() == QPropertyAnimation.Running:
            self.fade_animation.stop()
            
        # 如果已经可见，只重置计时器并返回
        if self.isVisible() and self.windowOpacity() > 0.5 and self.visible_state:
            self.hide_timer.start(2000)
            return
            
        # 窗口不可见，需要显示它
        self.visible_state = True
        
        # 计算位置（因UI组件可能会改变大小，每次都重新计算）
        self.adjustSize()  # 先调整大小以适应内容
        screen_geometry = QApplication.primaryScreen().geometry()
        x = int((screen_geometry.width() - self.width()) // 2)
        y = int(screen_geometry.height() * 0.67)
        self.move(x, y)
        
        # 显示窗口（完全不透明）
        self.setWindowOpacity(1.0)
        self.show()
        
        # 启动隐藏计时器
        self.hide_timer.start(2000)

    def start_fade_out(self):
        # 创建并启动淡出动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide_and_reset)
        self.fade_animation.start()
    
    def hide_and_reset(self):
        # 隐藏窗口并重置状态
        self.hide()
        self.visible_state = False

# 创建系统托盘图标类
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        # 创建托盘图标
        icon = self.create_tray_icon()
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.app = app
        self.setup_menu()
        self.show()
        
    def create_tray_icon(self):
        # 创建一个简单的亮度图标
        img = QImage(64, 64, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆形
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor(255, 204, 0))
        painter.drawEllipse(12, 12, 40, 40)
        
        # 绘制光线
        import math
        painter.setPen(QPen(QColor(255, 204, 0), 3))
        for i in range(8):
            angle = i * 45 * math.pi / 180  # 转换为弧度
            # 计算起点坐标（从圆边缘开始）
            x1 = 32 + 20 * math.cos(angle)  
            y1 = 32 + 20 * math.sin(angle)
            # 计算终点坐标（向外延伸）
            x2 = 32 + 30 * math.cos(angle)  
            y2 = 32 + 30 * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.end()
        
        return QIcon(QPixmap.fromImage(img))
    
    def setup_menu(self):
        # 创建上下文菜单
        menu = QMenu()
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)
        
        # 设置托盘图标的上下文菜单
        self.setContextMenu(menu)
        # 允许点击托盘图标时显示菜单
        self.activated.connect(self.on_tray_icon_activated)
        
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # 单击
            self.contextMenu().popup(self.geometry().center())

    
    def save_icon_as_ico(self, filepath="brightness_icon.ico"):
        # 创建图标图像
        img = QImage(64, 64, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆形
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor(255, 204, 0))
        painter.drawEllipse(17, 17, 30, 30)
        
        # 绘制光线
        painter.setPen(QPen(QColor(255, 204, 0), 3))
        import math
        for i in range(8):
            angle = i * 45 * math.pi / 180  # 转换为弧度
            # 计算起点坐标（从圆边缘开始）
            x1 = 32 + 20 * math.cos(angle)  
            y1 = 32 + 20 * math.sin(angle)
            # 计算终点坐标（向外延伸）
            x2 = 32 + 30 * math.cos(angle)  
            y2 = 32 + 30 * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.end()
        
        # 转换为QPixmap并保存
        pixmap = QPixmap.fromImage(img)
        
        # 直接尝试保存为ico文件
        success = pixmap.save(filepath, "ICO")
        
        if success:
            print(f"图标已保存至: {os.path.abspath(filepath)}")
        else:
            # 如果无法直接保存为ICO，则保存为PNG
            png_path = filepath.replace('.ico', '.png')
            success = pixmap.save(png_path, "PNG")
            if success:
                print(f"图标已保存为PNG: {os.path.abspath(png_path)}")
                print("注意: 要转换为ICO文件，可能需要使用图像编辑工具")
            else:
                print("保存图标失败")

# 全局变量
app = QApplication(sys.argv)
overlay = BrightnessOverlay()

# 创建系统托盘图标
tray_icon = SystemTrayIcon(app)
# tray_icon.save_icon_as_ico()

# 连接信号到UI更新函数
signal_emitter.brightness_changed.connect(overlay.show_with_value)

def decrease_brightness():
    current = sbc.get_brightness(display=0)  # 获取当前亮度
    current = current[0]
    new_brightness = max(0, current - 10)   # 亮度减 10%
    sbc.set_brightness(new_brightness, display=0)
    # 通过信号发送亮度值，而不是直接调用UI方法
    signal_emitter.brightness_changed.emit(new_brightness)
    print(f"亮度降低到 {new_brightness}%")

def increase_brightness():
    current = sbc.get_brightness(display=0)
    current = current[0]
    new_brightness = min(100, current + 10)
    sbc.set_brightness(new_brightness, display=0)
    # 通过信号发送亮度值，而不是直接调用UI方法
    signal_emitter.brightness_changed.emit(new_brightness)
    print(f"亮度增加到 {new_brightness}%")

# 监听快捷键
keyboard.add_hotkey("win+enter", increase_brightness)
keyboard.add_hotkey("win+shift", decrease_brightness)

print("按 win+shift 降低亮度，win+enter 增加亮度")
print("程序已在系统托盘运行，右键点击托盘图标可退出")

# 显示当前亮度
current = sbc.get_brightness(display=0)[0]
overlay.show_with_value(current)

# 使用timer保持Qt事件循环运行，同时不阻塞keyboard库
timer = QTimer()
timer.timeout.connect(lambda: None)
timer.start(100)

sys.exit(app.exec_())