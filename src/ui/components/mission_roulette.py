from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                               QHBoxLayout, QGraphicsOpacityEffect, QFrame, 
                               QGraphicsDropShadowEffect, QWidget, QApplication,
                               QTextEdit)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QSize, QPoint, QRect, QEvent
from PySide6.QtGui import QColor, QFont
import random

class MissionScanner(QWidget):
    """
    Simulates a decoding/scanning effect for text.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self.setStyleSheet("background-color: #00f3ff;")
        
        # Glow
        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(QColor("#00f3ff"))
        glow.setBlurRadius(15)
        self.setGraphicsEffect(glow)
        
    def scan_anim(self, target_widget):
        # We don't actually move this widget, we just use it as a visual separator or progress bar
        pass

class MissionRouletteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mission Generator")
        self.setFixedSize(500, 650)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_data()
        self.setup_ui()
        
        # Animations
        self.setWindowOpacity(0)
        self.scale_anim = QPropertyAnimation(self, b"windowOpacity")
        self.scale_anim.setDuration(400)
        self.scale_anim.setStartValue(0)
        self.scale_anim.setEndValue(1)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBack)
        self.scale_anim.start()

    def setup_data(self):
        self.objectives = [
            "Assassination", "Data Heist", "Bunker Raid", "Cargo Transport", 
            "Search & Rescue", "Mining Operation", "Bounty Hunting", 
            "Investigation", "Sabotage", "Escort Mission", "Salvage Run"
        ]
        
        self.locations = [
            "MicroTech", "Hurston", "ArcCorp", "Crusader", "Grim Hex", 
            "Daymar", "Yela", "Cellin", "Wala", "Lyria", "Magda", "Arial", "Aberdeen"
        ]
        
        self.restrictions = [
            "Pistol Only", "No Heavy Armor", "Stealth Only (No kills if possible)", 
            "Sniper Rifle Only", "No HUD (F4)", "Starter Ship Only", 
            "Ground Vehicles Only", "No Medpens", "Night Time Only", 
            "Must use Silencer", "No Shields", "Under 5 Minutes"
        ]
        
        self.rewards = [
            "10,000 aUEC", "25,000 aUEC", "Rare Loot", "Reputation Gain", 
            "New Ship Component", "Street Cred"
        ]
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container
        self.container = QFrame(self)
        self.container.setObjectName("MissionContainer")
        self.container.setStyleSheet("""
            QFrame#MissionContainer {
                background-color: rgba(10, 15, 25, 0.98);
                border: 2px solid #ffcc00;
                border-radius: 10px;
                border-bottom-left-radius: 30px;
            }
        """)
        
        # Glow
        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(QColor("#ffcc00")) # Amber/Gold for missions
        glow.setBlurRadius(20)
        self.container.setGraphicsEffect(glow)
        
        layout.addWidget(self.container)
        
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(30, 40, 30, 40)
        inner_layout.setSpacing(20)
        
        # Header
        header = QLabel("MISSION BRIEFING")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            color: #ffcc00; 
            font-size: 24px; 
            font-weight: 900; 
            letter-spacing: 4px;
            font-family: 'Segoe UI', sans-serif;
            border-bottom: 2px solid rgba(255, 204, 0, 0.3);
            padding-bottom: 10px;
        """)
        inner_layout.addWidget(header)
        
        # Data Grid
        self.labels = {}
        
        grid = QVBoxLayout()
        grid.setSpacing(15)
        
        self.add_field(grid, "OBJECTIVE", "decoding...")
        self.add_field(grid, "LOCATION", "analyzing...")
        self.add_field(grid, "RESTRICTION", "calculating...")
        
        inner_layout.addLayout(grid)
        
        # Console Output (Fluff)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            background-color: rgba(0,0,0,0.5);
            color: #00ff00;
            font-family: Consolas, monospace;
            font-size: 10px;
            border: 1px solid #333;
        """)
        self.console.setFixedHeight(100)
        inner_layout.addWidget(self.console)
        
        inner_layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_gen = QPushButton("GENERATE OPERATION")
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        self.btn_gen.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 204, 0, 0.1);
                color: #ffcc00;
                font-weight: bold;
                padding: 15px;
                border: 1px solid #ffcc00;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffcc00;
                color: #000;
            }
        """)
        self.btn_gen.clicked.connect(self.start_generation)
        
        self.btn_close = QPushButton("DECLINE")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                font-weight: bold;
                padding: 15px;
                border: none;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        self.btn_close.clicked.connect(self.close_animated)
        
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_gen)
        
        inner_layout.addLayout(btn_layout)
        
        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        
        self.iterations = 0
        
    def add_field(self, layout, title, default_text):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(5)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #888; font-size: 10px; letter-spacing: 2px;")
        
        lbl_val = QLabel(default_text)
        lbl_val.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold; font-family: Consolas;")
        
        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        
        layout.addWidget(container)
        self.labels[title] = lbl_val

    def start_generation(self):
        self.btn_gen.setEnabled(False)
        self.console.clear()
        self.log("Initializing secure connection...")
        self.iterations = 0
        self.timer.start(50)
        
    def log(self, text):
        self.console.append(f"> {text}")
        
    def tick(self):
        self.iterations += 1
        
        # Scramble effect
        self.labels["OBJECTIVE"].setText(random.choice(self.objectives).upper())
        self.labels["LOCATION"].setText(random.choice(self.locations).upper())
        self.labels["RESTRICTION"].setText(self.generate_random_hash())
        
        if self.iterations % 5 == 0:
            self.log(f"Decoding packet {random.randint(1000,9999)}...")
        
        if self.iterations > 30:
            self.timer.stop()
            self.finalize()
            
    def generate_random_hash(self):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(12))

    def finalize(self):
        obj = random.choice(self.objectives)
        loc = random.choice(self.locations)
        rst = random.choice(self.restrictions)
        
        self.labels["OBJECTIVE"].setText(obj.upper())
        self.labels["LOCATION"].setText(loc.upper())
        self.labels["RESTRICTION"].setText(rst.upper())
        
        self.log("MISSION GENERATED SUCCESSFULLY.")
        self.log("AWAITING OPERATOR ACKNOWLEDGEMENT.")
        
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("REROLL MISSION")

    def close_animated(self):
        self.scale_anim.setDirection(QPropertyAnimation.Backward)
        self.scale_anim.finished.connect(self.close)
        self.scale_anim.start()
