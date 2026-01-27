from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QFont, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QRect, QPoint
import random

class HoloIdCard(QWidget):
    """
    A widget that renders a Sci-Fi Holographic ID Card.
    Designed to be rendered to a Pixmap for export.
    """
    def __init__(self, character, pixmap, parent=None):
        super().__init__(parent)
        self.character = character
        self.face_pixmap = pixmap
        # Standard ID Card Ratio (approx)
        self.setFixedSize(600, 350)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        w = self.width()
        h = self.height()
        
        # 1. Background (Glass effect)
        # Gradient from top-left to bottom-right
        bg_grad = QLinearGradient(0, 0, w, h)
        bg_grad.setColorAt(0, QColor(20, 30, 50, 230))
        bg_grad.setColorAt(1, QColor(10, 15, 25, 240))
        
        painter.setBrush(bg_grad)
        painter.setPen(QPen(QColor(100, 200, 255, 150), 2))
        
        # Draw tech shape (cut corners)
        corner = 20
        path = self._create_tech_path(0, 0, w, h, corner)
        painter.drawPath(path)
        
        # 2. Holographic Scan Lines Overlay
        painter.setClipPath(path)
        for i in range(0, h, 4):
            painter.fillRect(0, i, w, 1, QColor(100, 200, 255, 10))
            
        # 3. Content
        padding = 25
        
        # Photo Area
        photo_w = 120
        photo_h = 160
        photo_rect = QRect(padding, padding + 40, photo_w, photo_h)
        
        # Draw Photo Border
        painter.setPen(QPen(QColor("#00f3ff"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(photo_rect)
        
        # Draw Photo
        if self.face_pixmap:
            painter.drawPixmap(photo_rect, self.face_pixmap.scaled(photo_rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            
        # Draw ID information
        layout_x = padding + photo_w + 30
        
        # Header: UEE CITIZEN RECORD
        painter.setPen(QColor("#00f3ff"))
        font = QFont("Segoe UI", 10, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(font)
        painter.drawText(layout_x, padding + 20, "UEE ADVOCACY RECORD")
        
        # Name
        font.setPointSize(24)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(layout_x, padding + 60, self.character.name.upper())
        
        # Fields
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        y_cursor = padding + 100
        
        self._draw_field(painter, "CITIZEN ID:", self._generate_hash(10), layout_x, y_cursor)
        self._draw_field(painter, "HOME PLANET:", "STANTON SYSTEM", layout_x, y_cursor + 30)
        self._draw_field(painter, "STATUS:", "ACTIVE", layout_x, y_cursor + 60)
        self._draw_field(painter, "BLOOD TYPE:", "O+", layout_x + 200, y_cursor + 60)
        
        # Barcode / Tech decoration at bottom
        bar_y = h - 60
        painter.fillRect(padding, bar_y, w - padding*2, 20, QColor(0, 243, 255, 30))
        # Random bars
        x_bar = padding
        while x_bar < w - padding:
            bw = random.randint(2, 10)
            if random.random() > 0.5:
                painter.fillRect(x_bar, bar_y, bw, 20, QColor(0, 243, 255, 150))
            x_bar += bw + 2
            
        # Footer text
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QColor(100, 200, 255, 150))
        painter.drawText(padding, h - 15, "AUTHORIZED PERSONNEL ONLY // PROPERTY OF UEE")

    def _create_tech_path(self, x, y, w, h, c):
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        # Top Left
        path.moveTo(x + c, y)
        # Top Right
        path.lineTo(x + w, y)
        # Bottom Right (Angle cut)
        path.lineTo(x + w, y + h - c)
        path.lineTo(x + w - c, y + h)
        # Bottom Left
        path.lineTo(x, y + h)
        # Close (Top Left angle cut implicitly if we wanted, but let's keep it square)
        path.lineTo(x, y + c)
        path.closeSubpath()
        return path

    def _draw_field(self, painter, label, value, x, y):
        painter.setPen(QColor("#55aaff"))
        painter.drawText(x, y, label)
        
        w = painter.fontMetrics().horizontalAdvance(label)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(x + w + 10, y, value)
        
    def _generate_hash(self, length):
        chars = "0123456789ABCDEF"
        return "".join(random.choice(chars) for _ in range(length))

    def grab_image(self):
        """Returns QPixmap of the rendered card"""
        return self.grab()
