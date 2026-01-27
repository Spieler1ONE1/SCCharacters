from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QGraphicsOpacityEffect, QStyleOption, QStyle, QApplication)
from PySide6.QtCore import (Qt, QTimer, QRect, QPropertyAnimation, 
                            QEasingCurve, QParallelAnimationGroup, QPoint, Signal)
from PySide6.QtGui import QPainter, QImage, QPixmap, QRadialGradient, QColor, QPen, QBrush

import random
from src.ui.components.tech_loader import TechLoader
from src.utils.translations import translator

class CRTOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Restore: Use a larger noise texture for the original "fine grain" look
        self.noise_texture = self._generate_noise_texture(512, 512)
        
        # Keep Optimization: Cache static elements
        self.static_overlay = None
        
        self.scanline_timer = QTimer(self)
        self.scanline_timer.timeout.connect(self.update)
        # 50ms = 20 FPS. Smooth enough, but 5x lighter than drawing lines every frame.
        self.scanline_timer.start(50) 
        
    def _generate_noise_texture(self, w, h):
        image = QImage(w, h, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        # Original color style
        painter.setPen(QPen(QColor(200, 255, 255, 30)))
        
        # Increase density for larger texture to match original density
        for _ in range(15000):
            x = random.randint(0, w)
            y = random.randint(0, h)
            painter.drawPoint(x, y)
            
        painter.end()
        return QPixmap.fromImage(image)
    
    def resizeEvent(self, event):
        self._update_static_cache(event.size())
        super().resizeEvent(event)
        
    def _update_static_cache(self, size):
        if size.isEmpty(): return
        
        self.static_overlay = QPixmap(size)
        self.static_overlay.fill(Qt.transparent)
        
        painter = QPainter(self.static_overlay)
        w, h = size.width(), size.height()
        
        # 1. Vignette (Static)
        radial = QRadialGradient(w/2, h/2, max(w, h)*0.85)
        radial.setColorAt(0.0, Qt.transparent)
        radial.setColorAt(0.6, QColor(0, 10, 20, 10)) 
        radial.setColorAt(1.0, QColor(0, 0, 0, 180)) 
        painter.fillRect(0, 0, w, h, QBrush(radial))
        
        # 2. Scanlines (Static)
        painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
        for y in range(0, h, 3):
            painter.drawLine(0, y, w, y)
            
        painter.end()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 1. Draw Static Cache first (Vignette + Scanlines)
        if self.static_overlay:
            painter.drawPixmap(0, 0, self.static_overlay)
            
        # 2. Restore: Draw Tiled Noise (Original Effect)
        # This preserves the "static" look the user liked, but is fast because
        # we aren't redrawing the background scanlines/gradients every frame.
        off_x = random.randint(0, 100)
        off_y = random.randint(0, 100)
        painter.drawTiledPixmap(self.rect(), self.noise_texture, QPoint(off_x, off_y))

class SplashOverlayWidget(QWidget):
    """
    Self-contained Splash Screen with CRT effect and animations.
    """
    finished = Signal() # Emitted when validation/entrance is complete and overlay fades out
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("SplashOverlay")
        self.setStyleSheet("""
            QWidget#SplashOverlay {
                background: qradialgradient(cx:0.5, cy:0.5, radius: 1.0, fx:0.5, fy:0.5, stop:0 #1f2937, stop:1 #0b0f19);
                border-radius: 20px;
            }
        """)
        
        self.setup_ui()
        
        # Overlay Logic
        self.splash_loading = False
        self.splash_text_visible = True
        
        self.splash_blink_timer = QTimer(self)
        self.splash_blink_timer.timeout.connect(self.splash_blink_text)
        self.splash_blink_timer.start(800)
        
    def setup_ui(self):
        # Layout for Splash
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- CRT Effect Overlay ---
        self.crt_overlay = CRTOverlay(self)
        self.crt_overlay.raise_() 
        
        # --- Splash Window Controls ---
        top_controls = QHBoxLayout()
        top_controls.addStretch()
        
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                font-weight: bold;
                font-size: 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #374151;
                color: #f9fafb;
            }
        """
        btn_close_style = """
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                font-weight: bold;
                font-size: 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #dc2626;
                color: white;
            }
        """

        btn_min = QPushButton("-", self)
        btn_min.setFixedSize(30, 30)
        btn_min.setCursor(Qt.PointingHandCursor)
        btn_min.setStyleSheet(btn_style)
        # Assuming parent is window for min/close
        if self.parent() and hasattr(self.parent(), 'showMinimized'):
            btn_min.clicked.connect(self.parent().showMinimized)
        
        btn_close = QPushButton("×", self)
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(btn_close_style)
        if self.parent() and hasattr(self.parent(), 'close'):
            btn_close.clicked.connect(self.parent().close)

        top_controls.addWidget(btn_min)
        top_controls.addWidget(btn_close)
        
        layout.addLayout(top_controls)
        layout.addStretch(1) # Push content to center
        
        layout.setSpacing(20)
        
        # 1. Tech Fingerprint Icon
        self.splash_scanner = TechLoader(self)
        # We need another container for center content to keep it vertically centered
        center_container = QVBoxLayout()
        center_container.setAlignment(Qt.AlignCenter)
        center_container.addWidget(self.splash_scanner, 0, Qt.AlignCenter)
        
        # 2. Main Text
        # Safe translation
        title_text = translator.get("splash_title")
        if not title_text or title_text == "splash_title": title_text = "SYSTEM INITIALIZED"
        
        self.splash_title = QLabel(title_text, self)
        self.splash_title.setAlignment(Qt.AlignCenter)
        self.splash_title.setStyleSheet("""
            color: #f9fafb;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        center_container.addWidget(self.splash_title)
        
        # 3. Subtitle / Prompt
        touch_text = translator.get("splash_touch")
        if not touch_text or touch_text == "splash_touch": touch_text = "TOUCH TO START"
        
        self.splash_prompt = QLabel(touch_text)
        self.splash_prompt.setAlignment(Qt.AlignCenter)
        self.splash_prompt.setStyleSheet("""
            color: #3b82f6;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 2px;
        """)
        center_container.addWidget(self.splash_prompt)
        
        layout.addLayout(center_container)
        layout.addStretch(1) 

    def resizeEvent(self, event):
        if hasattr(self, 'crt_overlay'):
            self.crt_overlay.resize(self.size())
        super().resizeEvent(event)

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def splash_blink_text(self):
        if self.splash_loading: return
        self.splash_text_visible = not self.splash_text_visible
        color = '#3b82f6' if self.splash_text_visible else '#1f2937'
        self.splash_prompt.setStyleSheet(f"""
            color: {color};
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 2px;
        """)

    def mousePressEvent(self, event):
        if not self.splash_loading:
            self.start_implosion()
            
    def start_implosion(self):
        self.splash_loading = True
        self.splash_blink_timer.stop()
        
        # Animación "Implosión" (Colapso hacia el centro)
        print("DEBUG: Starting Implosion Animation")
        
        self.splash_group = QParallelAnimationGroup(self)
        
        # 1. Opacidad
        self.splash_opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.splash_opacity)
        
        anim_op = QPropertyAnimation(self.splash_opacity, b"opacity")
        anim_op.setDuration(400)
        anim_op.setStartValue(1.0)
        anim_op.setEndValue(0.0)
        
        # 2. Geometría (Colapso hacia el centro)
        geo = self.geometry()
        center = geo.center()
        # Colapsar a un cuadro pequeño en el centro
        end_geo = QRect(center.x() - 1, center.y() - 1, 2, 2)
        
        anim_geo = QPropertyAnimation(self, b"geometry")
        anim_geo.setDuration(400)
        anim_geo.setStartValue(geo)
        anim_geo.setEndValue(end_geo)
        anim_geo.setEasingCurve(QEasingCurve.InBack) # Efecto de "aspiración"
        
        self.splash_group.addAnimation(anim_op)
        self.splash_group.addAnimation(anim_geo)
        
        self.splash_group.finished.connect(self._on_finished)
        self.splash_group.start()
        
    def _on_finished(self):
        self.hide()
        self.finished.emit()
        self.deleteLater()

    def fade_in(self, duration=800):
        """Starts a fade-in animation (for logout/reset). Returns the animation object."""
        self.show()
        self.raise_()
        
        self.splash_opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.splash_opacity)
        self.splash_opacity.setOpacity(0.0)
        
        anim = QPropertyAnimation(self.splash_opacity, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.start()
        
        # Reset internal state
        self.splash_loading = False
        self.splash_blink_timer.start()
        
        return anim
