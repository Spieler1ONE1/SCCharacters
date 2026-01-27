from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from src.ui.anim_config import AnimConfig
from src.ui.styles import ThemeColors

class ToastNotification(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        # Remove Qt.SubWindow to avoid taskbar artifacts
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Styles allow Toast to look good
        self.update_theme(True)
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(AnimConfig.get_duration(AnimConfig.DURATION_NORMAL))
        self.anim.finished.connect(self.on_anim_finished)

    def update_theme(self, is_dark):
        c = ThemeColors(is_dark)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {c.bg_secondary};
                color: {c.text_primary};
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                border: 1px solid {c.border};
            }}
        """)

    def show_message(self, message, duration=2000):
        self.setText(message)
        self.adjustSize()
        
        # Center horizontally at the bottom
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 50
            self.move(x, y)
            
        self.show()
        self.opacity_effect.setOpacity(0)
        
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(AnimConfig.EASING_ENTRY)
        self.anim.start()
        
        self.timer.start(duration)

    def fade_out(self):
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(AnimConfig.EASING_EXIT)
        self.anim.start()
        
    def on_anim_finished(self):
        if self.opacity_effect.opacity() == 0:
            self.hide()
