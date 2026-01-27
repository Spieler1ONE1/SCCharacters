from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QGraphicsOpacityEffect, 
                                QHBoxLayout, QGridLayout, QSizePolicy)
from PySide6.QtCore import (Qt, QUrl, QSize, QPropertyAnimation, QParallelAnimationGroup, 
                            QSequentialAnimationGroup, QEasingCurve)
from PySide6.QtGui import QDesktopServices, QFont, QCursor, QIcon, QPixmap
import os
from src.ui.styles import ThemeColors
from src.utils.translations import translator

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QGraphicsOpacityEffect, 
                                QHBoxLayout, QGridLayout, QSizePolicy)
from PySide6.QtCore import (Qt, QUrl, QSize, QPropertyAnimation, QParallelAnimationGroup, 
                            QSequentialAnimationGroup, QEasingCurve)
from PySide6.QtGui import QDesktopServices, QFont, QCursor, QIcon, QPixmap
import os
from src.ui.styles import ThemeColors
from src.utils.translations import translator

class TechButton(QPushButton):
    """Minimalist Sci-Fi Button with Hover Glow Effect"""
    def __init__(self, text, url, accent_color="#3b82f6", parent=None):
        super().__init__(text, parent)
        self.url = url
        self.accent_color = accent_color
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(45)
        self.clicked.connect(self.open_link)
        self.update_style()
        
    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(20, 30, 40, 0.4);
                color: {self.accent_color};
                border: 1px solid rgba(255,255,255,0.1);
                border-left: 3px solid {self.accent_color};
                border-radius: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 13px;
                padding-left: 15px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: rgba({int(self.accent_color[1:3], 16)}, {int(self.accent_color[3:5], 16)}, {int(self.accent_color[5:7], 16)}, 0.1);
                border: 1px solid {self.accent_color};
                border-left: 5px solid {self.accent_color};
                color: #fff;
            }}
            QPushButton:pressed {{
                background-color: {self.accent_color};
                color: #000;
            }}
        """)
        
    def open_link(self):
        QDesktopServices.openUrl(QUrl(self.url))

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.update_theme(True) 
        
    def tr(self, key, **kwargs):
        return translator.get(key, **kwargs)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignTop)
        
        # --- 1. Identity Header (Minimalist) ---
        self.header_container = QWidget()
        header_layout = QVBoxLayout(self.header_container)
        header_layout.setContentsMargins(0, 0, 0, 20)
        header_layout.setSpacing(5)
        
        # "CREDITS // SYSTEM"
        self.title_label = QLabel(f"// {self.tr('credits_title').upper()}")
        self.title_label.setAlignment(Qt.AlignLeft)
        
        self.name_label = QLabel("SPIELERWAN")
        self.name_label.setAlignment(Qt.AlignLeft)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.name_label)
        
        layout.addWidget(self.header_container)
        
        # --- 2. Network Grid (Websites + Socials) ---
        self.network_container = QWidget()
        network_layout = QVBoxLayout(self.network_container)
        network_layout.setContentsMargins(0, 0, 0, 0)
        network_layout.setSpacing(15)
        
        # Sub-header style (reused)
        def create_sub_header(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; letter-spacing: 1px; font-family: 'Courier New';")
            return lbl

        # > DATA SOURCES
        network_layout.addWidget(create_sub_header(self.tr("credits_datasources")))
        
        grid_sources = QGridLayout()
        grid_sources.setSpacing(10)
        
        btn_source = TechButton(self.tr("credits_database"), "https://www.star-citizen-characters.com", "#22d3ee")
        btn_app = TechButton(self.tr("credits_app_portal"), "https://starchar.app", "#ec4899")
        
        grid_sources.addWidget(btn_source, 0, 0)
        grid_sources.addWidget(btn_app, 0, 1)
        network_layout.addLayout(grid_sources)
        
        # > TRANSMISSION
        network_layout.addSpacing(10)
        network_layout.addWidget(create_sub_header(self.tr("credits_transmission")))
        
        grid_socials = QGridLayout()
        grid_socials.setSpacing(10)
        
        # Columns
        btn_yt1 = TechButton("YOUTUBE: SpielerWAN", "https://www.youtube.com/@SpielerWAN", "#ef4444")
        btn_yt2 = TechButton("YOUTUBE: SCpi9", "https://www.youtube.com/@SCpi9", "#ef4444")
        btn_twitch = TechButton("TWITCH: Live Feed", "https://www.twitch.tv/spielerwan", "#a855f7")
        btn_twitter = TechButton(self.tr("credits_comms"), "https://x.com/SpielerWAN", "#3b82f6")
        btn_discord = TechButton(self.tr("credits_discord"), "https://discord.gg/TGjCmzHR", "#5865F2")
        
        grid_socials.addWidget(btn_yt1, 0, 0)
        grid_socials.addWidget(btn_yt2, 0, 1)
        grid_socials.addWidget(btn_twitch, 1, 0)
        grid_socials.addWidget(btn_twitter, 1, 1)
        grid_socials.addWidget(btn_discord, 2, 0, 1, 2)
        
        network_layout.addLayout(grid_socials)
        
        layout.addWidget(self.network_container)
        
        layout.addSpacing(30)
        
        # --- 3. Referral Panel (Tech Look) ---
        self.referral_frame = QFrame()
        self.referral_frame.setObjectName("RefPanel")
        ref_layout = QHBoxLayout(self.referral_frame)
        ref_layout.setContentsMargins(20, 20, 20, 20)
        ref_layout.setSpacing(20)
        
        # Left side: Text
        text_container = QWidget()
        text_bg = QVBoxLayout(text_container)
        text_bg.setContentsMargins(0, 0, 0, 0)
        text_bg.setSpacing(5)
        
        self.ref_title_label = QLabel(self.tr("credits_referral_title").upper())
        self.ref_desc_label = QLabel(self.tr("credits_referral_desc"))
        self.ref_desc_label.setWordWrap(True)
        
        text_bg.addWidget(self.ref_title_label)
        text_bg.addWidget(self.ref_desc_label)
        
        # Right side: Code Button
        self.ref_code_btn = QPushButton("STAR-SZ4B-VBHC")
        self.ref_code_btn.setCursor(Qt.PointingHandCursor)
        self.ref_code_btn.setFixedSize(200, 50)
        self.ref_code_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.robertsspaceindustries.com/enlist?referral=STAR-SZ4B-VBHC")))
        
        ref_layout.addWidget(text_container, 1)
        ref_layout.addWidget(self.ref_code_btn)
        
        layout.addWidget(self.referral_frame)
        
        # --- 4. Legal & Community Footer ---
        layout.addStretch()
        
        footer_container = QWidget()
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 20, 0, 0)
        footer_layout.setSpacing(10)
        footer_layout.setAlignment(Qt.AlignCenter)
        
        # Community Badge (Ajustado para no recortarse)
        self.badge_label = QLabel()
        self.badge_label.setAlignment(Qt.AlignCenter)
        # Importante: Permitir que el label se adapte si es necesario, pero fijar minimo
        self.badge_label.setMinimumSize(120, 120) 
        
        from src.utils.paths import get_resource_path
        image_path = get_resource_path("src/assets/made_by_community.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scaled contents False para mejor control manual, usamos scaled() del pixmap
                # Usamos 120x120 para que sea visible pero no enorme
                pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.badge_label.setPixmap(pixmap)
                footer_layout.addWidget(self.badge_label)
        
        # Add spacing to prevent overlap
        footer_layout.addSpacing(15)
        
        # Legal Disclaimer (Compacto)
        self.legal_label = QLabel()
        self.legal_label.setAlignment(Qt.AlignCenter)
        self.legal_label.setWordWrap(True)
        self.legal_label.setOpenExternalLinks(True)
        self.legal_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        legal_text = f"""
            <div style='color: #64748b; font-size: 10px; font-family: Segoe UI; line-height: 120%;'>
                <p>
                    <b>{self.tr('legal_fan_project')}</b><br>
                    <span style='color: #475569;'>{self.tr('legal_not_affiliated')}</span>
                </p>
                <p>
                    <a href='https://robertsspaceindustries.com/' style='color: #3b82f6; text-decoration: none;'>{self.tr('legal_official_site')}</a> | 
                    <a href='https://support.robertsspaceindustries.com/hc/en-us/articles/360006895793-Star-Citizen-Fankit-and-Fandom-FAQ' style='color: #3b82f6; text-decoration: none;'>{self.tr('legal_fandom_faq')}</a>
                </p>
                <p style='color: #334155; font-size: 9px;'>
                     {self.tr('legal_trademarks')}
                </p>
            </div>
        """
        self.legal_label.setText(legal_text)
        footer_layout.addWidget(self.legal_label)
        
        layout.addWidget(footer_container)

    def showEvent(self, event):
        super().showEvent(event)
        self.animate_in()

    def animate_in(self):
        items = [self.header_container, self.network_container, self.referral_frame, self.badge_label]
        self.anim_group = QParallelAnimationGroup(self)
        
        delay = 0
        for item in items:
            eff = QGraphicsOpacityEffect(self)
            item.setGraphicsEffect(eff)
            eff.setOpacity(0)
            
            seq = QSequentialAnimationGroup()
            if delay > 0: seq.addPause(delay)
            
            anim = QPropertyAnimation(eff, b"opacity")
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setDuration(800)
            anim.setEasingCurve(QEasingCurve.OutExpo)
            
            seq.addAnimation(anim)
            self.anim_group.addAnimation(seq)
            delay += 100
            
        self.anim_group.start()
        
    def update_theme(self, is_dark):
        c = ThemeColors(is_dark)
        
        # Minimalist Header
        self.title_label.setStyleSheet(f"color: {c.text_disabled}; font-family: 'Courier New'; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        self.name_label.setStyleSheet(f"color: {c.text_primary}; font-family: 'Segoe UI'; font-size: 42px; font-weight: 900; letter-spacing: -1px;")

        
        # Referral Panel
        self.referral_frame.setStyleSheet(f"""
            QFrame#RefPanel {{
                background-color: rgba(251, 191, 36, 0.05);
                border: 1px solid rgba(251, 191, 36, 0.2);
                border-radius: 8px;
            }}
        """)
        
        self.ref_title_label.setStyleSheet("color: #fbbf24; font-size: 16px; font-weight: 900; letter-spacing: 1px; font-family: 'Segoe UI';")
        self.ref_desc_label.setStyleSheet(f"color: {c.text_secondary}; font-size: 13px;")
        
        self.ref_code_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(251, 191, 36, 0.1);
                color: #fbbf24;
                border: 1px dashed #fbbf24;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #fbbf24;
                color: #000;
                border: 1px solid #fbbf24;
            }}
        """)
