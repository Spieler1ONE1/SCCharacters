from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                               QHBoxLayout, QGraphicsOpacityEffect, QFrame, 
                               QGraphicsDropShadowEffect, QWidget, QApplication)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QSize, QPoint, QRect, QEvent
from PySide6.QtGui import QPixmap, QColor, QLinearGradient, QPalette, QBrush
import random
from src.ui.widgets import TiltLabel
from src.utils.image_loader import ImageLoader
from src.utils.translations import translator

class ScannerOverlay(QWidget):
    """Moving scan line effect"""
    def __init__(self, parent=None, width=250, height=250):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.line = QFrame(self)
        self.line.setFixedSize(width, 2)
        self.line.setStyleSheet("background-color: rgba(0, 243, 255, 0.8); box-shadow: 0 0 10px #00f3ff;")
        
        # Glow for the line
        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(QColor("#00f3ff"))
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        self.line.setGraphicsEffect(glow)

        self.anim = QPropertyAnimation(self.line, b"pos")
        self.anim.setDuration(1500)
        self.anim.setStartValue(QPoint(0, 0))
        self.anim.setEndValue(QPoint(0, height))
        self.anim.setLoopCount(-1) # Infinite
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        
    def start(self):
        self.anim.start()
        
    def stop(self):
        self.anim.stop()
        self.hide()

class RouletteDialog(QDialog):
    character_selected = Signal(object) 

    def __init__(self, characters, image_loader, sound_manager, parent=None):
        super().__init__(parent)
        self.characters = [c for c in characters if c.image_url]
        self.image_loader = image_loader
        self.sound_manager = sound_manager
        
        self.setWindowTitle(translator.get("roulette"))
        self.setFixedSize(450, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.current_index = 0
        self.spin_count = 0
        self.max_spins = 40
        self.interval = 50
        
        self.setup_ui()

        
        # Animations
        self.setWindowOpacity(0)
        self.scale_anim = QPropertyAnimation(self, b"windowOpacity")
        self.scale_anim.setDuration(500)
        self.scale_anim.setStartValue(0)
        self.scale_anim.setEndValue(1)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBack)
        self.scale_anim.start()
        
        self.scale_anim.start()
        
        # Flags
        self.intro_finished = False
        self.scale_anim.finished.connect(self.on_intro_finished)

    def on_intro_finished(self):
        # Only if we are moving forward (opening)
        if self.scale_anim.direction() == QPropertyAnimation.Forward:
            self.intro_finished = True
            
    def showEvent(self, event):
        super().showEvent(event)
        # Center on parent if possible
        if self.parent():
            geo = self.parent().geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)
            
            # Enable Blur on Parent
            if hasattr(self.parent(), 'blur_effect'):
                self.parent().blur_effect.setBlurRadius(0)
                self.parent().blur_effect.setEnabled(True)
                
                self.blur_anim = QPropertyAnimation(self.parent().blur_effect, b"blurRadius")
                self.blur_anim.setDuration(500)
                self.blur_anim.setStartValue(0)
                self.blur_anim.setEndValue(15)
                self.blur_anim.setEasingCurve(QEasingCurve.OutCubic)
                self.blur_anim.start()
            
        self.activateWindow()
        self.raise_()
        self.start_spin()

    def event(self, event):
        # Handle focus loss (click outside)
        if event.type() == QEvent.WindowDeactivate:
             if self.intro_finished:
                 # Check where focus went after a tiny delay to allow app state to update
                 QTimer.singleShot(10, self._check_focus_and_close)
        return super().event(event)

    def _check_focus_and_close(self):
        # If the parent (Main Window) is now the active window, it means the user clicked inside the app.
        if self.parent() and self.parent().isActiveWindow():
            self.close_animated()
            
    # Removed explicit eventFilter as it was unreliable regarding coordinates
    
    def close_animated(self):
        # Prevent multiple calls or closing while opening
        if not self.intro_finished:
             return
             
        # Check if already closing to prevent loop
        if hasattr(self, '_is_closing') and self._is_closing:
            return
            
        self._is_closing = True
        
        # Animate Blur Out
        if self.parent() and hasattr(self.parent(), 'blur_effect'):
            # Create a localized animation for the blur to ensure it runs
            self.blur_out_anim = QPropertyAnimation(self.parent().blur_effect, b"blurRadius")
            self.blur_out_anim.setDuration(450)
            self.blur_out_anim.setStartValue(self.parent().blur_effect.blurRadius())
            self.blur_out_anim.setEndValue(0)
            self.blur_out_anim.setEasingCurve(QEasingCurve.InCubic)
            self.blur_out_anim.start()

        self.scale_anim.stop() # Stop any current animation
        self.scale_anim.setDirection(QPropertyAnimation.Backward)
        # Ensure we don't have multiple connections
        try:
            self.scale_anim.finished.disconnect()
        except:
            pass
            
        self.scale_anim.finished.connect(self._finish_closing)
        self.scale_anim.start()

    def _finish_closing(self):
        # Disable blur
        if self.parent() and hasattr(self.parent(), 'blur_effect'):
            self.parent().blur_effect.setEnabled(False)

        self._is_closing = False # Reset flag just in case
        super().reject() # This is the critical call to exit exec() loop

    def reject(self):
        self.close_animated()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Main HUD Container ---
        self.container = QFrame(self)
        self.container.setObjectName("HudContainer")
        self.container.setStyleSheet("""
            QFrame#HudContainer {
                background-color: rgba(5, 10, 20, 0.95);
                border: 2px solid #00f3ff;
                border-radius: 20px;
                border-top-left-radius: 40px;
                border-bottom-right-radius: 40px;
            }
        """)
        
        # Outer Glow
        container_glow = QGraphicsDropShadowEffect(self)
        container_glow.setColor(QColor("#00f3ff"))
        container_glow.setBlurRadius(20)
        container_glow.setOffset(0,0)
        self.container.setGraphicsEffect(container_glow)
        
        layout.addWidget(self.container)
        
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(20, 30, 20, 30)
        inner_layout.setAlignment(Qt.AlignCenter)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        
        # Blinking indicator
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet("color: #ff0055; font-size: 16px;")
        header_layout.addWidget(self.indicator)
        
        title = QLabel(translator.get("roulette_title"))
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True) # Allow wrap if needed
        # Dynamic font size logic isn't easily possible in stylesheet alone without custom widget
        # But we can limit max width or use ensure it fits.
        title.setStyleSheet("""
            color: #00f3ff; 
            font-weight: 900; 
            font-size: 16px; 
            letter-spacing: 2px; 
            font-family: 'Segoe UI', sans-serif;
            text-transform: uppercase;
        """)
        header_layout.addWidget(title, 1) # Add stretch factor to take up space
        
        header_layout.addStretch()
        
        # Tech decoration text
        deco = QLabel("SYS.RNG.v2")
        deco.setStyleSheet("color: rgba(0, 243, 255, 0.5); font-size: 10px;")
        header_layout.addWidget(deco)
        
        inner_layout.addLayout(header_layout)
        
        # Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(0, 243, 255, 0.3); height: 1px; border: none;")
        inner_layout.addWidget(line)
        
        inner_layout.addSpacing(30)
        
        # --- Image Area ---
        image_container = QWidget()
        image_container.setFixedSize(260, 260)
        img_layout = QVBoxLayout(image_container)
        img_layout.setContentsMargins(0,0,0,0)
        
        # The Image
        self.image_display = TiltLabel()
        self.image_display.setFixedSize(250, 250)
        self.image_display.setStyleSheet("""
            border-radius: 125px; 
            border: 3px dashed rgba(0, 243, 255, 0.4);
            background-color: #000;
        """)
        self.image_display.setScaledContents(True)
        img_layout.addWidget(self.image_display, alignment=Qt.AlignCenter)
        
        # Scanner Overlay (positioned absolute roughly)
        self.scanner = ScannerOverlay(self.image_display, 250, 250)
        self.scanner.start()
        
        inner_layout.addWidget(image_container, alignment=Qt.AlignCenter)
        
        inner_layout.addSpacing(20)
        
        # --- Name Label ---
        self.name_label = QLabel("INITIALIZING...")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True) # Critical for long names
        # Reduced base font size slightly to accommodate longer names better
        self.name_label.setStyleSheet("""
            color: #fff; 
            font-size: 20px; 
            font-weight: bold; 
            background: rgba(0, 243, 255, 0.1); 
            padding: 8px; 
            border-radius: 5px;
            border-left: 4px solid #00f3ff;
            border-right: 4px solid #00f3ff;
        """)
        inner_layout.addWidget(self.name_label)
        
        inner_layout.addStretch()
        
        # --- Actions ---
        self.btn_install = QPushButton(translator.get("roulette_install"))
        self.btn_install.setCursor(Qt.PointingHandCursor)
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 243, 255, 0.1);
                color: #00f3ff;
                font-weight: bold;
                padding: 15px;
                border: 1px solid #00f3ff;
                border-radius: 4px;
                font-size: 14px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #00f3ff;
                color: #050a14;
                box-shadow: 0 0 15px #00f3ff;
            }
        """)
        self.btn_install.clicked.connect(self.accept_selection)
        self.btn_install.hide()
        inner_layout.addWidget(self.btn_install)
        
        self.btn_spin_again = QPushButton(translator.get("roulette_spin"))
        self.btn_spin_again.setCursor(Qt.PointingHandCursor)
        self.btn_spin_again.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 85, 0.1);
                color: #ff0055;
                font-weight: bold;
                padding: 15px;
                border: 1px solid #ff0055;
                border-radius: 4px;
                font-size: 14px;
                letter-spacing: 1px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #ff0055;
                color: #fff;
                box-shadow: 0 0 15px #ff0055;
            }
        """)
        self.btn_spin_again.clicked.connect(self.start_spin)
        self.btn_spin_again.hide()
        inner_layout.addWidget(self.btn_spin_again)
        
        self.btn_close = QPushButton(translator.get("cancel"))
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 0.5); 
                background: transparent; 
                border: none;
                margin-top: 5px;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        self.btn_close.clicked.connect(self.close_animated)
        inner_layout.addWidget(self.btn_close)

    def start_spin(self):
        if not self.characters:
            self.name_label.setText("NO DATA")
            return
            
        # Reset State
        self.spin_count = 0
        self.interval = 50
        
        # Reset UI
        self.btn_install.hide()
        if hasattr(self, 'btn_spin_again'):
            self.btn_spin_again.hide()
            
        self.scanner.show()
        self.scanner.start()
            
        if hasattr(self, 'timer'):
            self.timer.stop()
            
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(self.interval)
        
        # Blink indicator
        if hasattr(self, 'indicator_timer'):
            self.indicator_timer.stop()
            
        self.indicator_timer = QTimer(self)
        self.indicator_timer.timeout.connect(self._blink_indicator)
        self.indicator_timer.start(300)

    def _blink_indicator(self):
        cur = self.indicator.styleSheet()
        if "color: #ff0055" in cur:
            self.indicator.setStyleSheet("color: #333; font-size: 16px;")
        else:
            self.indicator.setStyleSheet("color: #ff0055; font-size: 16px;")

    def tick(self):
        self.spin_count += 1
        
        idx = random.randint(0, len(self.characters) - 1)
        char = self.characters[idx]
        self.selected_char = char
        
        self.name_label.setText(char.name.upper())
        self.image_loader.load_image(char.image_url, self.update_image)
        
        # Tech glitch effect styling on image border
        colors = ["#00f3ff", "#ff0055", "#ccff00", "#ffffff"]
        c = random.choice(colors)
        self.image_display.setStyleSheet(f"""
            border-radius: 125px; 
            border: 3px dashed {c};
            background-color: #000;
        """)
        
        if self.spin_count > self.max_spins:
            current_interval = self.timer.interval()
            if current_interval < 400:
                self.timer.setInterval(int(current_interval * 1.3))
            else:
                self.stop_spin()

    def update_image(self, pixmap):
        self.image_display.setPixmap(pixmap)
        # Play tick sound
        if self.sound_manager:
            self.sound_manager.play_hover()

    def stop_spin(self):
        self.timer.stop()
        self.indicator_timer.stop()
        self.indicator.setStyleSheet("color: #00ff9d; font-size: 16px;") # Green light
        self.scanner.stop()
        self.scanner.hide()
        
        if self.sound_manager:
            self.sound_manager.play_success()
        
        # Success Style
        self.image_display.setStyleSheet("""
            border-radius: 125px; 
            border: 4px solid #00ff9d;
            background-color: #000;
        """)
        
        # Add a flash effect to name
        self.flash_anim = QPropertyAnimation(self.name_label, b"styleSheet")
        # Creating a simple flash via timer because animating stylesheet is heavy/complex
        self.name_label.setStyleSheet("""
            color: #00ff9d; 
            font-size: 22px; 
            font-weight: bold; 
            background: rgba(0, 255, 157, 0.1); 
            padding: 8px; 
            border-radius: 5px;
            border: 2px solid #00ff9d;
        """)
        
        self.btn_install.show()
        if hasattr(self, 'btn_spin_again'):
            self.btn_spin_again.show()

    def done(self, r):
        # Ensure blur is removed when dialog closes (covers both accept and reject)
        if self.parent() and hasattr(self.parent(), 'blur_effect'):
            self.parent().blur_effect.setEnabled(False)
        super().done(r)

    def accept_selection(self):
        if hasattr(self, 'selected_char'):
            self.character_selected.emit(self.selected_char)
            self.accept()
