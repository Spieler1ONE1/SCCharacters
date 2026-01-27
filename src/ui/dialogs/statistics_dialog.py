
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# Simple charting if possible, otherwise use progress bars
# We'll use styled progress bars for stats

class StatisticsDialog(QDialog):
    def __init__(self, installed_chars, online_chars, parent=None):
        super().__init__(parent)
        self.installed = installed_chars
        self.online_chars = online_chars
        self.setWindowTitle("Library Statistics")
        self.resize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title = QLabel("📊 Library Analytics")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)
        
        # Grid for cards
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # 1. Total Installed
        self.add_stat_card(grid, 0, 0, "Installed", str(len(self.installed)), "#6366f1")
        
        # 2. Total Database
        self.add_stat_card(grid, 0, 1, "Database Size", str(len(self.online_chars) if self.online_chars else "?"), "#10b981")
        
        # 3. New Today (Mock logic or real if date avail)
        # self.add_stat_card(grid, 1, 0, "Added Today", "0", "#f59e0b")
        
        layout.addLayout(grid)
        
        # Distribution
        dist_label = QLabel("Tag Distribution (Top 5)")
        dist_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(dist_label)
        
        stats_container = QFrame()
        stats_container.setStyleSheet("background-color: rgba(255,255,255,0.05); border-radius: 8px; padding: 15px;")
        stats_layout = QVBoxLayout(stats_container)
        
        # Calculate tags
        tag_counts = {}
        for c in self.installed:
            for t in c.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
                
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        max_val = sorted_tags[0][1] if sorted_tags else 1
        
        for tag, count in sorted_tags:
            row = QHBoxLayout()
            lbl = QLabel(f"{tag}")
            lbl.setFixedWidth(100)
            
            # Bar
            pct = int((count / max_val) * 100)
            bar = QFrame()
            bar.setFixedHeight(12)
            bar.setStyleSheet(f"""
                background-color: #334155; 
                border-radius: 6px;
                background-image: linear-gradient(to right, #6366f1 {pct}%, transparent {pct}%);
            """) # CSS Gradient linear doesn't work well in Qt stylesheets like this for values on the fly without complex string manip
            
            # Simple progress bar widget
            from PySide6.QtWidgets import QProgressBar
            pbar = QProgressBar()
            pbar.setValue(pct)
            pbar.setTextVisible(False)
            pbar.setFixedHeight(8)
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #334155;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: #6366f1;
                    border-radius: 4px;
                }}
            """)
            
            count_lbl = QLabel(str(count))
            
            row.addWidget(lbl)
            row.addWidget(pbar)
            row.addWidget(count_lbl)
            stats_layout.addLayout(row)
            
        layout.addWidget(stats_container)
        
        layout.addStretch()
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def add_stat_card(self, grid, row, col, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {color}; border-radius: 12px; color: white;")
        frame.setFixedHeight(100)
        
        fl = QVBoxLayout(frame)
        
        t = QLabel(title)
        t.setStyleSheet("font-size: 14px; opacity: 0.8;")
        v = QLabel(value)
        v.setStyleSheet("font-size: 32px; font-weight: bold;")
        
        fl.addWidget(t)
        fl.addWidget(v)
        
        grid.addWidget(frame, row, col)
