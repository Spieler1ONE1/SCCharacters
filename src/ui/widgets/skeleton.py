from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QBrush, QPen

class SkeletonCard(QFrame):
    """
    A unified skeleton loading card that displays a shimmering loading state.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 320)
        self.setStyleSheet("background-color: transparent;")
        
        self.shimmer_pos = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_shimmer)
        self.timer.start(16) # ~60fps
        
        # Colors - Dark Mode defaults
        self.color_base = QColor("#1f2937") # Gray 800
        self.color_highlight = QColor("#374151") # Gray 700
        self.color_bg = QColor("#111827") # Darker BG or Transparent

    def update_shimmer(self):
        # Move gradient from -1 to 2
        self.shimmer_pos += 0.02
        if self.shimmer_pos > 2.0:
            self.shimmer_pos = -0.5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 0. Draw Card Background (Glass-like)
        bg_color = QColor(0, 0, 0, 80) # Semi-transparent dark
        painter.setBrush(bg_color)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1)) # Subtle border
        painter.drawRoundedRect(0, 0, w-1, h-1, 16, 16)
        
        # Define the shimmering area
        gradient = QLinearGradient(0, 0, w, 0)
        
        pos = self.shimmer_pos
        
        # Use slightly transparent bones
        c_base = QColor(255, 255, 255, 10)
        c_light = QColor(255, 255, 255, 40)
        
        gradient.setStart(pos * w - 100, 0)
        gradient.setFinalStop(pos * w + 100, 0)
        
        gradient.setColorAt(0, c_base)
        gradient.setColorAt(0.5, c_light)
        gradient.setColorAt(1, c_base)
        
        brush = QBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush) 
        
        # Bones Layout matches CharacterCard
        
        # 1. Image Placeholder
        painter.drawRoundedRect(10, 10, 180, 180, 8, 8)
        
        # 2. Title Lines
        painter.drawRoundedRect(10, 210, 140, 16, 4, 4)
        painter.drawRoundedRect(10, 235, 100, 16, 4, 4)
        
        # 3. Author Line
        painter.drawRoundedRect(50, 265, 100, 12, 4, 4)
        
        # 4. Button/Action Placeholder
        painter.drawRoundedRect(10, 285, 180, 35, 8, 8) 
        
        painter.end()
