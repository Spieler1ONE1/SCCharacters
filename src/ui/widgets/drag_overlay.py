from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from src.ui.styles import ThemeColors

class DragOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.setup_ui()
        self.update_theme(True) # Default to Dark for now, or updated later

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Container Frame (The visible box)
        self.container = QFrame()
        self.container.setObjectName("DragOverlayFrame")
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)
        
        # Icon
        self.icon_label = QLabel("📂")
        self.icon_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.icon_label)
        
        # Text
        self.text_label = QLabel("Suelta el archivo para instalar")
        self.text_label.setObjectName("DragOverlayText")
        self.text_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.text_label)
        
        # Subtext
        self.subtext_label = QLabel(".chf files")
        self.subtext_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.subtext_label)
        
        layout.addWidget(self.container)

    def update_theme(self, is_dark):
        c = ThemeColors(is_dark)
        
        self.container.setStyleSheet(f"""
            QFrame#DragOverlayFrame {{
                background-color: {c.overlay_bg};
                border: 4px dashed {c.accent};
                border-radius: 20px;
            }}
        """)
        
        self.icon_label.setStyleSheet(f"""
            font-size: 64px;
            color: {c.accent_hover};
            background: transparent;
            border: none;
        """)
        
        self.text_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {c.text_primary};
            background: transparent;
            border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        
        self.subtext_label.setStyleSheet(f"""
            font-size: 16px;
            color: {c.text_secondary};
            background: transparent;
            border: none;
        """)
