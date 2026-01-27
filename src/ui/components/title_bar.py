from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenuBar
from PySide6.QtCore import Qt, Signal, QPoint
import os

class TitleBar(QWidget):
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    mute_toggled = Signal(bool) # is_muted
    
    def __init__(self, title="Window", parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 0, 0)
        self.layout.setSpacing(10)
        
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        
        # Load Icon
        from PySide6.QtGui import QPixmap
        from src.utils.paths import get_resource_path
        
        search_path = get_resource_path("src/assets/icons/app_icon.png")
        if os.path.exists(search_path):
             pixmap = QPixmap(search_path)
             self.icon_label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self.layout.addWidget(self.icon_label)

        # Title Label
        self.title_label = QLabel(title)
        self.title_label.setObjectName("TitleLabel")
        self.layout.addWidget(self.title_label)
        
        self.layout.addStretch()
        
        # Window Controls Container
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Mute
        self.btn_mute = QPushButton("🔊")
        self.btn_mute.setObjectName("TitleBarButton")
        self.btn_mute.setFixedWidth(40) # Slightly wider for emoji?
        self.btn_mute.clicked.connect(self.toggle_mute)
        self.controls_layout.addWidget(self.btn_mute)
        


        # Minimize
        self.btn_min = QPushButton("─")
        self.btn_min.setObjectName("TitleBarButton")
        self.btn_min.clicked.connect(self.minimize_clicked.emit)
        self.controls_layout.addWidget(self.btn_min)
        
        self.is_muted = False
    
    def set_mute_state(self, is_muted):
        self.is_muted = is_muted
        self.btn_mute.setText("🔇" if self.is_muted else "🔊")
        
        # Maximize/Restore
        self.btn_max = QPushButton("□")
        self.btn_max.setObjectName("TitleBarButton")
        self.btn_max.clicked.connect(self.maximize_clicked.emit)
        self.controls_layout.addWidget(self.btn_max)
        
        # Close
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("TitleBarCloseButton")
        self.btn_close.clicked.connect(self.close_clicked.emit)
        self.controls_layout.addWidget(self.btn_close)
        
        self.layout.addLayout(self.controls_layout)
        
    def set_maximized_icon(self, is_maximized):
        self.btn_max.setText("❐" if is_maximized else "□")

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.btn_mute.setText("🔇" if self.is_muted else "🔊")
        self.mute_toggled.emit(self.is_muted)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximize_clicked.emit()
        super().mouseDoubleClickEvent(event)

class CustomMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomMenuBar")
