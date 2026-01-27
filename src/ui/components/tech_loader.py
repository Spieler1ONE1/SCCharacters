from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QLinearGradient, QBrush, QConicalGradient

class TechLoader(QWidget):
    """
    An advanced animated tech-style circle that simulates a fingerprint/scanner/reactor.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.angle_1 = 0
        self.angle_2 = 0
        self.angle_3 = 0
        
        self.scanning = False
        self.scan_line_y = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) # ~60fps
        
        self.color_accent = QColor("#3b82f6") # Blue
        self.color_glow = QColor("#60a5fa")   # Lighter Blue
        self.color_core = QColor("#2563eb")
        
        self.scale_factor = 1.0
        self.breathing_dir = 1
        self.pulse_alpha = 100
        self.pulse_dir = 1
        
        self.hovered = False
        self.is_success = False

    def set_success(self):
        self.is_success = True
        self.color_accent = QColor("#10b981") # Emerald Green
        self.color_glow = QColor("#34d399")
        self.color_core = QColor("#059669")
        self.scanning = False
        self.scale_factor = 1.2 # Pop effect

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)
        
    def update_animation(self):
        # Rotate rings at different speeds
        self.angle_1 = (self.angle_1 + (8 if self.scanning else 1.5)) % 360
        self.angle_2 = (self.angle_2 - (5 if self.scanning else 1)) % 360
        self.angle_3 = (self.angle_3 + (3 if self.scanning else 0.5)) % 360
        
        # Core Pulse
        if self.pulse_dir == 1:
            self.pulse_alpha += 2
            if self.pulse_alpha >= 200: self.pulse_dir = -1
        else:
            self.pulse_alpha -= 2
            if self.pulse_alpha <= 80: self.pulse_dir = 1

        # Idle Breathing Effect or Success Pulse
        if not self.scanning:
            if self.is_success:
                # Quick pulse down from 1.2 to 1.0
                if self.scale_factor > 1.0:
                    self.scale_factor -= 0.02
                else:
                    self.scale_factor = 1.0
            else:
                if self.breathing_dir == 1:
                    self.scale_factor += 0.001
                    if self.scale_factor >= 1.03: self.breathing_dir = -1
                else:
                    self.scale_factor -= 0.001
                    if self.scale_factor <= 0.97: self.breathing_dir = 1
        else:
             # Snap to 1.0 when scanning starts
             self.scale_factor = 1.0

        if self.scanning:
            self.scan_line_y += 12 # Scan speed
            if self.scan_line_y > self.height():
                self.scan_line_y = 0
                
        self.update()
        
    def start_scan(self):
        self.scanning = True
        self.scan_line_y = 0
        
    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Colors
        accent = self.color_accent.lighter(130) if self.hovered else self.color_accent
        glow = self.color_glow.lighter(130) if self.hovered else self.color_glow
        
        center = QPoint(self.width() // 2, self.height() // 2)
        radius = min(self.width(), self.height()) // 2 - 15
        
        painter.save()
        painter.translate(center)
        painter.scale(self.scale_factor, self.scale_factor)
        
        # 1. Central Core (Pulsing)
        core_radius = 40
        radial = QLinearGradient(-core_radius, -core_radius, core_radius, core_radius)
        c_core = QColor(self.color_core)
        c_core.setAlpha(self.pulse_alpha)
        radial.setColorAt(0, c_core)
        radial.setColorAt(1, Qt.transparent)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(c_core)
        painter.setOpacity(self.pulse_alpha / 255.0)
        painter.drawEllipse(QPoint(0,0), core_radius, core_radius)
        painter.setOpacity(1.0)
        
        # 2. Ring 1 (Outer - Fast)
        painter.save()
        painter.rotate(self.angle_1)
        pen = QPen(accent)
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # Segments
        painter.drawArc(QRectF(-radius, -radius, radius*2, radius*2), 0, 100 * 16)
        painter.drawArc(QRectF(-radius, -radius, radius*2, radius*2), 120 * 16, 40 * 16)
        painter.drawArc(QRectF(-radius, -radius, radius*2, radius*2), 180 * 16, 140 * 16)
        painter.restore()
        
        # 3. Ring 2 (Middle - Counter - Dashed)
        painter.save()
        painter.rotate(self.angle_2)
        r2 = radius - 15
        pen_dim = QPen(glow)
        pen_dim.setWidth(2)
        pen_dim.setStyle(Qt.DotLine)
        painter.setPen(pen_dim)
        painter.drawEllipse(QRectF(-r2, -r2, r2*2, r2*2))
        
        # Add decorative triangles
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawConvexPolygon([QPoint(0, -r2-5), QPoint(-4, -r2-12), QPoint(4, -r2-12)])
        painter.rotate(120)
        painter.drawConvexPolygon([QPoint(0, -r2-5), QPoint(-4, -r2-12), QPoint(4, -r2-12)])
        painter.rotate(120)
        painter.drawConvexPolygon([QPoint(0, -r2-5), QPoint(-4, -r2-12), QPoint(4, -r2-12)])
        painter.restore()
        
        # 4. Ring 3 (Inner - Slow - Tech lines)
        painter.save()
        painter.rotate(self.angle_3)
        r3 = radius - 35
        pen_thin = QPen(accent)
        pen_thin.setWidth(1)
        painter.setPen(pen_thin)
        # Draw tech bracket
        path_rect = QRectF(-r3, -r3, r3*2, r3*2)
        painter.drawArc(path_rect, 45 * 16, 90 * 16)
        painter.drawArc(path_rect, 225 * 16, 90 * 16)
        painter.restore()
        
        # 5. Success Checkmark
        if self.is_success:
            painter.save()
            # Simple checkmark
            pen_success = QPen(Qt.white)
            pen_success.setWidth(4)
            pen_success.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_success)
            
            # Draw check
            # Points relative to center
            p1 = QPoint(-15, 5)
            p2 = QPoint(-5, 15)
            p3 = QPoint(20, -15)
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)
            painter.restore()

        painter.restore() # Undo scale/translate
        
        # 6. Scan Line (Overlay)
        if self.scanning:
            scan_y = self.scan_line_y
            
            # Gradient Bar
            gradient = QLinearGradient(0, scan_y - 30, 0, scan_y + 10)
            c1 = QColor(accent)
            c1.setAlpha(0)
            c2 = QColor(accent) 
            c2.setAlpha(200) # Bright center
            c3 = QColor(Qt.white)
            c3.setAlpha(220) # Hot leading edge
            
            gradient.setColorAt(0, c1)
            gradient.setColorAt(0.8, c2)
            gradient.setColorAt(1.0, c3)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRect(0, scan_y - 25, self.width(), 35)
            
            # Grid effect on scan
            pen_grid = QPen(QColor(255, 255, 255, 50))
            pen_grid.setWidth(1)
            painter.setPen(pen_grid)
            painter.drawLine(0, scan_y, self.width(), scan_y)
