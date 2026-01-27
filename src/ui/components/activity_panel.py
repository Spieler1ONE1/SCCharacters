from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QLabel, QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QObject, Slot
from PySide6.QtGui import QFont, QColor
import logging
import datetime

class LogSignal(QObject):
    log_received = Signal(str, str) # level, message

class QWidgetHandler(logging.Handler):
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter

    def emit(self, record):
        try:
            msg = self.format(record)
            self.signal_emitter.log_received.emit(record.levelname, msg)
        except Exception:
            self.handleError(record)

class ActivityPanel(QFrame):
    launch_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActivityPanel")
        self.setup_ui()
        self.setup_logging()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (Terminal Bar)
        header = QWidget()
        header.setObjectName("TerminalHeader")
        header.setStyleSheet("background-color: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.1);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel(">> SYSTEM_ACTIVITY_LOG")
        title_label.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-weight: bold; color: rgba(255,255,255,0.7);")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Launch Button (Compact)
        self.btn_launch = QPushButton("INITIATE LAUNCH SEQUENCE")
        self.btn_launch.setObjectName("LaunchButton")
        self.btn_launch.setCursor(Qt.PointingHandCursor)
        # Style will be enhanced in global stylesheet or here
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 60, 60, 0.1);
                border: 1px solid rgba(255, 60, 60, 0.5);
                color: #ff6b6b;
                font-weight: bold;
                padding: 4px 12px;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
            }
            QPushButton:hover {
                background-color: rgba(255, 60, 60, 0.3);
                border-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #ff6b6b;
                color: #000;
            }
        """)
        self.btn_launch.clicked.connect(self.launch_requested.emit)
        header_layout.addWidget(self.btn_launch)
        
        layout.addWidget(header)
        
        # Log View
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("TerminalLog")
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 10, 16, 0.95);
                border: none;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 5px;
            }
        """)
        self.log_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Minimalist
        
        layout.addWidget(self.log_view)
        
        # Initial Message
        self.add_log_message("INFO", "System initialized. Monitoring active...")
        
    def setup_logging(self):
        self.log_signal = LogSignal()
        self.log_signal.log_received.connect(self.add_log_message)
        
        self.handler = QWidgetHandler(self.log_signal)
        # Format: Time - Level - Message
        formatter = logging.Formatter('%(asctime)s > %(message)s', datefmt='%H:%M:%S')
        self.handler.setFormatter(formatter)
        
        # Attach to root logger
        logging.getLogger().addHandler(self.handler)
        
    def add_log_message(self, level, message):
        color = "#00ff00" # Default Green
        if level == "WARNING": color = "#f59e0b" # Amber
        if level == "ERROR": color = "#ef4444"   # Red
        if level == "CRITICAL": color = "#ff0000"
        
        # HTML formatting
        html = f'<span style="color: {color};">{message}</span>'
        self.log_view.append(html)
        
        # Auto scroll
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_theme(self, is_dark):
        # We can adjust terminal colors if needed, but terminals are usually dark.
        # Maybe change the border/accent color based on theme?
        # For now, it keeps its own "Hacker/Terminal" aesthetic which fits all sci-fi themes.
        pass
