from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                               QHBoxLayout, QLabel)
from PySide6.QtCore import Qt
import logging
import os

class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.resize(800, 600)
        self.setup_ui()
        self.load_log()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Info Label
        self.info_label = QLabel("Viewing current session log:")
        layout.addWidget(self.info_label)
        
        # Text Area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFontFamily("Consolas, monospace")
        layout.addWidget(self.text_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_log)
        
        btn_copy = QPushButton("Copy to Clipboard")
        btn_copy.clicked.connect(self.text_edit.selectAll)
        btn_copy.clicked.connect(self.text_edit.copy)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_copy)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def load_log(self):
        # We need to find the log file from the logging configuration
        # Assuming the standard setup in main.py uses a FileHandler
        log_file = None
        root_logger = logging.getLogger()
        for h in root_logger.handlers:
            if isinstance(h, logging.FileHandler):
                log_file = h.baseFilename
                break
                
        if log_file and os.path.exists(log_file):
            self.info_label.setText(f"Log File: {log_file}")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    self.text_edit.setPlainText(content)
                    # Scroll to bottom
                    sb = self.text_edit.verticalScrollBar()
                    sb.setValue(sb.maximum())
            except Exception as e:
                self.text_edit.setPlainText(f"Error reading log file: {e}")
        else:
            self.text_edit.setPlainText("No log file found for this session.")
