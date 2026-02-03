from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QCursor

class FooterBar(QFrame):
    launch_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FooterBar")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 15) # Bottom padding for visual breathing room
        layout.setSpacing(15)
        
        # --- Left: Status Area ---
        self.status_container = QWidget()
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(2)
        
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("FooterStatusLabel")
        
        self.sub_status_label = QLabel("BioMetrics Systems Online")
        self.sub_status_label.setObjectName("FooterSubStatusLabel")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.sub_status_label)
        
        layout.addWidget(self.status_container)
        
        # Spacer
        layout.addStretch()
        
        # --- Right: Launch Module ---
        
        # Version Label (Small, next to button)
        self.version_label = QLabel("LIVE 3.24.X")
        self.version_label.setObjectName("FooterVersionLabel")
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.version_label)
        
        # THE BIG BUTTON
        self.launch_btn = QPushButton("LAUNCH GAME")
        self.launch_btn.setObjectName("FooterLaunchButton")
        self.launch_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.launch_btn.clicked.connect(self.launch_clicked.emit)
        
        # Add Shadow to Button
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 255, 100, 80)) # Green Glow
        shadow.setOffset(0, 0)
        self.launch_btn.setGraphicsEffect(shadow)
        
        layout.addWidget(self.launch_btn)

    def set_status(self, text):
        self.status_label.setText(text)
        
    def set_version_text(self, text):
        self.version_label.setText(text)
        
    def set_launch_text(self, text):
        self.launch_btn.setText(text)
