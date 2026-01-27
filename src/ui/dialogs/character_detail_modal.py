
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QApplication, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QSize, QUrl, QPropertyAnimation, QEasingCurve, QPoint, QRect, Signal, QTimer, QParallelAnimationGroup, QVariantAnimation
from PySide6.QtGui import QPixmap, QDesktopServices, QColor, QPainter, QBrush, QPainterPath, QPen, QLinearGradient
from src.core.models import Character
from src.utils.image_loader import ImageLoader
from src.utils.translations import translator
from src.ui.styles import ThemeColors
from src.ui.widgets.flow_layout import FlowLayout

class CoverImageWidget(QWidget):
    """
    Renders the character image with 'object-fit: cover' logic.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._radius = 24 # Matches container radius
        self.setStyleSheet("background: transparent; border: none;")
        self.setAttribute(Qt.WA_TransparentForMouseEvents) 
        
        # Loading Pulse
        self.pulse_color = QColor("#1e293b")
        self.pulse_anim = QVariantAnimation(self)
        self.pulse_anim.setDuration(1000)
        self.pulse_anim.setLoopCount(-1) 
        self.pulse_anim.setStartValue(QColor("#1e293b"))
        self.pulse_anim.setEndValue(QColor("#334155"))
        self.pulse_anim.valueChanged.connect(self._on_pulse_value)
        self.pulse_anim.start()

    def _on_pulse_value(self, color):
        self.pulse_color = color
        self.update()
        
    def setPixmap(self, pixmap):
        self.pulse_anim.stop()
        self._pixmap = pixmap
        self.update()
        
    def start_biometric_scan(self):
        """Starts the sci-fi scanner effect."""
        self._scan_y = 0.0
        self._scanning = True
        
        self.scan_anim = QVariantAnimation(self)
        self.scan_anim.setDuration(3000) # 2 seconds scan
        self.scan_anim.setStartValue(0.0)
        self.scan_anim.setEndValue(1.0)
        self.scan_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.scan_anim.valueChanged.connect(self._on_scan_value)
        self.scan_anim.finished.connect(lambda: setattr(self, '_scanning', False))
        self.scan_anim.start()
        
    def _on_scan_value(self, val):
        self._scan_y = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
            
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            rect = self.rect()
            
            # Clip path for rounded corners (left side only)
            path = QPainterPath()
            path.moveTo(rect.bottomRight())
            path.lineTo(rect.topRight())
            path.lineTo(rect.topLeft() + QPoint(self._radius, 0))
            path.quadTo(rect.topLeft(), rect.topLeft() + QPoint(0, self._radius))
            path.lineTo(rect.bottomLeft() - QPoint(0, self._radius))
            path.quadTo(rect.bottomLeft(), rect.bottomLeft() + QPoint(self._radius, 0))
            path.lineTo(rect.bottomRight())
            path.closeSubpath()
            
            painter.setClipPath(path)
            
            if not self._pixmap:
                painter.fillRect(rect, self.pulse_color)
                return

            # Cover Logic
            img_w = self._pixmap.width()
            img_h = self._pixmap.height()
            
            if img_h == 0 or img_w == 0: return

            widget_ratio = rect.width() / rect.height()
            img_ratio = img_w / img_h
            
            if widget_ratio > img_ratio:
                new_w = rect.width()
                new_h = new_w / img_ratio
            else:
                new_h = rect.height()
                new_w = new_h * img_ratio
                
            x = (rect.width() - new_w) / 2
            y = (rect.height() - new_h) / 2
            
            target_rect = QRect(int(x), int(y), int(new_w), int(new_h))
            painter.drawPixmap(target_rect, self._pixmap)
            
            # Biometric Overlay
            if getattr(self, '_scanning', False):
                scan_y_pos = int(rect.height() * self._scan_y)
                
                # Draw Scan Line
                pen = QPen(QColor("#06b6d4")) # Cyan 500
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(0, scan_y_pos, rect.width(), scan_y_pos)
                
                # Draw Glow Gradient below/above
                grad = QLinearGradient(0, scan_y_pos - 40, 0, scan_y_pos)
                grad.setColorAt(0, QColor(6, 182, 212, 0))
                grad.setColorAt(1, QColor(6, 182, 212, 100))
                painter.fillRect(0, scan_y_pos - 40, rect.width(), 40, grad)
                
                # Draw Tech Data (Random numbers)
                if self._scan_y < 0.9:
                    import random
                    font = painter.font()
                    font.setFamily("Consolas")
                    font.setPixelSize(10)
                    painter.setFont(font)
                    painter.setPen(QColor("#67e8f9")) # Cyan 300
                    
                    data_str = f"DNA_SEQ_MATCH: {random.randint(90,99)}%\nBIOMETRIC_DATA: V{random.randint(1,9)}.{random.randint(0,9)}"
                    painter.drawText(10, scan_y_pos - 10, data_str)

        finally:
            painter.end()


class CharacterDetailModal(QWidget):
    """
    Overlay widget to display character details.
    Moved from QDialog to QWidget to ensure it moves perfectly with the parent window.
    """
    closed = Signal()
    tag_clicked = Signal(str)
    fav_clicked = Signal(Character, bool)

    install_clicked = Signal(Character)
    
    def __init__(self, character: Character, image_loader: ImageLoader, parent=None):
        super().__init__(parent)
        self.character = character
        self.image_loader = image_loader
        
        # Transparent background for the widget itself (we paint the dim overlay in paintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Opacity Effect for Fade Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.setup_ui()
        self.load_image()
        
    def paintEvent(self, event):
        # Draw the semi-transparent overlay background
        painter = QPainter(self)
        if not painter.isActive():
             return
        try:
            painter.setBrush(QColor(0, 0, 0, 180)) # Dark dim
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
        finally:
            painter.end()
        
    def setup_ui(self):
        # Determine theme
        is_dark = True
        if self.parent() and hasattr(self.parent(), 'theme_manager'):
             is_dark = (self.parent().theme_manager.get_effective_theme() == 'dark')
        c = ThemeColors(is_dark)

        # Layout - WE USE MANUAL LAYOUT (resizeEvent) to avoid conflict with animations
        # self.main_layout = QVBoxLayout(self)
        # self.main_layout.setContentsMargins(20, 20, 20, 20)
        # self.main_layout.setAlignment(Qt.AlignCenter)
        
        # Content Container
        self.container = QFrame(self)
        self.container.setObjectName("DetailContainer")
        # Max size constraint
        # Note: We'll update fixed size in resizeEvent too strictly speaking, 
        # but relative layout usually handles it if we don't fix it.
        # Let's use maximumSize and let layout handle centering.
        self.container.setMinimumSize(900, 600)
        self.container.setMaximumSize(1100, 850)
        
        self.container.setStyleSheet(f"""
            QFrame#DetailContainer {{
                background-color: {c.bg_primary};
                border: 1px solid {c.border};
                border-radius: 24px;
            }}
            QLabel {{ color: {c.text_primary}; border: none; background: none; }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # LEFT: Image
        self.image_widget = CoverImageWidget()
        self.image_widget.setMinimumWidth(400)
        container_layout.addWidget(self.image_widget, 40)
        
        # RIGHT: Info
        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(30, 30, 30, 30)
        info_layout.setSpacing(15)
        
        # Header (Title + Close)
        header_layout = QHBoxLayout()
        title_label = QLabel(self.character.name)
        title_label.setStyleSheet(f"font-size: 36px; font-weight: 800; color: {c.text_primary};")
        title_label.setWordWrap(True)
        
        # Close Button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("DetailCloseBtn")
        close_btn.setFixedSize(36, 36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.animate_close)
        close_btn.setStyleSheet(f"""
            QPushButton#DetailCloseBtn {{
                background-color: {c.bg_tertiary}; 
                color: {c.text_secondary}; 
                font-size: 16px; 
                border-radius: 18px;
                border: none;
                image: none;
                border-image: none;
                background-image: none;
            }}
            QPushButton#DetailCloseBtn:hover {{
                background-color: {c.error}; 
                color: white;
            }}
        """)
        
        header_layout.addWidget(title_label, 1)
        header_layout.setAlignment(Qt.AlignTop)
        
        # Action Row (Fav + Close)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        
        # Fav Button
        self.btn_fav = QPushButton("♥")
        self.btn_fav.setFixedSize(36, 36)
        self.btn_fav.setCursor(Qt.PointingHandCursor)
        self.update_fav_style(False) # Init state, will be updated if parent has config
        self.btn_fav.clicked.connect(self.toggle_fav)
        
        # Check initial state from config if possible
        if self.parent() and hasattr(self.parent(), 'config_manager'):
             is_fav = self.parent().config_manager.is_favorite(self.character.name)
             self.update_fav_style(is_fav)

        action_row.addWidget(self.btn_fav)
        action_row.addWidget(close_btn)
        
        header_layout.addLayout(action_row)
        info_layout.addLayout(header_layout)
        
        # Author
        author_label = QLabel(translator.get("by_author", author=self.character.author))
        author_label.setStyleSheet(f"font-size: 18px; color: {c.accent}; font-weight: 600;")
        info_layout.addWidget(author_label)
        
        # Divider
        self.add_divider(info_layout, c)
        
        # Stats
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(30)
        self.add_stat_big(stats_grid, translator.get("stat_downloads"), self.character.downloads or 0, "⬇", c)
        self.add_stat_big(stats_grid, translator.get("stat_likes"), self.character.likes or 0, "♥", c)
        stats_grid.addStretch()
        info_layout.addLayout(stats_grid)
        
        # Tags
        lbl_tags = QLabel(translator.get("label_tags"))
        lbl_tags.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {c.text_secondary}; text-transform: uppercase; letter-spacing: 1px;")
        info_layout.addWidget(lbl_tags)

        tags_scroll = QScrollArea()
        tags_scroll.setWidgetResizable(True)
        tags_scroll.setFrameShape(QFrame.NoFrame)
        tags_scroll.setStyleSheet("background: transparent; border: none;")
        tags_scroll.setMaximumHeight(150)
        
        tags_content = QWidget()
        tags_content.setStyleSheet("background: transparent;")
        tags_flow = FlowLayout(tags_content, margin=0, spacing=8)
        
        if self.character.tags:
            for tag in self.character.tags:
                pub_btn = QPushButton(tag)
                pub_btn.setCursor(Qt.PointingHandCursor)
                pub_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c.bg_tertiary}; 
                        color: {c.text_primary};
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-size: 13px;
                        border: 1px solid transparent;
                    }}
                    QPushButton:hover {{
                        background-color: {c.accent};
                        color: white;
                        border-color: {c.accent_hover};
                    }}
                """)
                # Capture tag variable in lambda default arg
                pub_btn.clicked.connect(lambda checked=False, t=tag: self.on_tag_click(t))
                tags_flow.addWidget(pub_btn)
        else:
             lbl = QLabel(translator.get("no_tags"))
             lbl.setStyleSheet(f"color: {c.text_disabled};")
             tags_flow.addWidget(lbl)
             
        tags_scroll.setWidget(tags_content)
        info_layout.addWidget(tags_scroll)
        
        info_layout.addStretch()
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)
        
        btn_view_web = QPushButton(translator.get("open_web"))
        btn_view_web.setObjectName("DetailWebBtn")
        btn_view_web.setCursor(Qt.PointingHandCursor)
        btn_view_web.setMinimumHeight(50)
        btn_view_web.setStyleSheet(f"""
            QPushButton#DetailWebBtn {{
                background-color: transparent;
                border: 2px solid {c.border};
                color: {c.text_primary};
                font-weight: 600;
                border-radius: 12px;
                padding: 0 20px;
                image: none;
                border-image: none;
                background-image: none;
            }}
            QPushButton#DetailWebBtn:hover {{
                border-color: {c.text_secondary};
                background-color: {c.bg_tertiary};
            }}
        """)
        btn_view_web.clicked.connect(self.open_web)
        
        self.btn_install = QPushButton(translator.get("install"))
        self.btn_install.setObjectName("DetailInstallBtn")
        self.btn_install.setCursor(Qt.PointingHandCursor)
        self.btn_install.setMinimumHeight(50)
        self.btn_install.setStyleSheet(f"""
            QPushButton#DetailInstallBtn {{
                background-color: {c.accent};
                color: white;
                font-size: 16px;
                font-weight: 700;
                border: none;
                border-radius: 12px;
                padding: 0 30px;
                image: none;
                border-image: none;
                background-image: none;
            }}
            QPushButton#DetailInstallBtn:hover {{
                background-color: {c.accent_hover};
            }}
            QPushButton#DetailInstallBtn:disabled {{
                background-color: {c.bg_tertiary};
                color: {c.text_disabled};
            }}
        """)
        
        if self.character.status == "installed":
             self.set_installed_state()
        else:
             self.btn_install.clicked.connect(self.on_install_requested)


        
        # Share Button
        btn_share = QPushButton("📸")
        btn_share.setToolTip(translator.get("share"))
        btn_share.setCursor(Qt.PointingHandCursor)
        btn_share.setMinimumHeight(50)
        btn_share.setFixedWidth(50)
        btn_share.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {c.border};
                border-radius: 12px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {c.bg_tertiary};
                border-color: {c.text_secondary};
            }}
        """)
        btn_share.clicked.connect(self.generate_share_card)



        # Holo ID Button
        btn_holo = QPushButton("🆔")
        btn_holo.setToolTip("Export Holo-ID")
        btn_holo.setCursor(Qt.PointingHandCursor)
        btn_holo.setMinimumHeight(50)
        btn_holo.setFixedWidth(50)
        btn_holo.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {c.border};
                border-radius: 12px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {c.bg_tertiary};
                border-color: {c.text_secondary};
            }}
        """)
        btn_holo.clicked.connect(self.generate_holo_id)
        
        actions_layout.addWidget(btn_share)
        actions_layout.addWidget(btn_holo)
        actions_layout.addWidget(btn_view_web)
        actions_layout.addWidget(self.btn_install)
        
        info_layout.addLayout(actions_layout)
        
        container_layout.addWidget(info_panel, 60)
        # self.main_layout.addWidget(self.container) # No layout
        
        self.is_animating = False

    def resizeEvent(self, event):
        # Manual centering to support animation without fighting layout
        if not hasattr(self, 'container'): return
        
        # Calculate target size (mimic previous constraints)
        w = min(self.width() - 40, 1100)
        h = min(self.height() - 40, 850)
        w = max(w, 900)
        h = max(h, 600)
        
        # Ensure it fits screen even if smaller than min
        w = min(w, self.width() - 20)
        h = min(h, self.height() - 20)
        
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        
        target_rect = QRect(int(x), int(y), int(w), int(h))
        
        # Only update if NOT currently animating (or if we are initializing)
        if not self.is_animating:
            self.container.setGeometry(target_rect)
            
        super().resizeEvent(event)

    def add_stat_big(self, layout, label, value, icon, c):
        v_box = QVBoxLayout()
        v_box.setSpacing(2)
        
        val_str = str(value)
        if value >= 1000: val_str = f"{value/1000:.1f}k"
        
        lbl_val = QLabel(f"{icon} {val_str}")
        lbl_val.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {c.text_primary};")
        
        lbl_desc = QLabel(label.upper())
        lbl_desc.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {c.text_secondary}; letter-spacing: 1px;")
        
        v_box.addWidget(lbl_val)
        v_box.addWidget(lbl_desc)
        layout.addLayout(v_box)

    def add_divider(self, layout, c):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {c.border};")
        line.setFixedHeight(1)
        layout.addWidget(line)

    def load_image(self):
        if self.character.image_url:
            self.image_loader.load_image(
                self.character.image_url,
                self.set_image
            )
            
    def set_image(self, pixmap):
        self.image_widget.setPixmap(pixmap)
        
    def on_install_requested(self):
        self.btn_install.setText(translator.get("downloading"))
        self.btn_install.setEnabled(False)
        self.install_clicked.emit(self.character)
        
    def set_installed_state(self):
        # Update UI to show installed
        c = ThemeColors(False) # Default/Base colors or try to get dynamic?
        # Actually we need theme context.
        # But for green success, hardcoded is usually fine or from ThemeColors
        self.btn_install.setText(translator.get("installed"))
        self.btn_install.setEnabled(False)
        self.btn_install.setStyleSheet(f"background-color: #10b981; color: white; border: none; border-radius: 12px; font-weight: 700;")

    def mousePressEvent(self, event):
        # Close if clicked outside
        if not self.container.geometry().contains(event.pos()):
            self.animate_close()
        
    def showEvent(self, event):
        if not self.graphicsEffect():
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)

        self.anim = QParallelAnimationGroup()
        
        # Opacity
        anim_op = QPropertyAnimation(self.opacity_effect, b"opacity")
        anim_op.setDuration(300)
        anim_op.setStartValue(0.0)
        anim_op.setEndValue(1.0)
        anim_op.setEasingCurve(QEasingCurve.OutQuad)
        
        # Geometry / Position (Pop up effect)
        # Force calculation of target geometry first
        self.resizeEvent(None)
        
        target_geo = self.container.geometry()
        start_geo = QRect(target_geo)
        start_geo.translate(0, 50)
        
        self.container.setGeometry(start_geo)
        
        anim_move = QPropertyAnimation(self.container, b"geometry")
        anim_move.setDuration(400)
        anim_move.setStartValue(start_geo)
        anim_move.setEndValue(target_geo)
        anim_move.setEasingCurve(QEasingCurve.OutBack) # Spring effect
        
        self.anim.addAnimation(anim_op)
        self.anim.addAnimation(anim_move)
        
        self.is_animating = True
        self.anim.finished.connect(self._on_shown_finished)
        self.anim.start()
        super().showEvent(event)

    def _on_shown_finished(self):
        self.setGraphicsEffect(None)
        self.is_animating = False
        self.image_widget.start_biometric_scan()

    def animate_close(self):
        # Prevent multiple calls
        if getattr(self, '_is_closing', False):
            return
        self._is_closing = True

        # Stop any running open animations
        if hasattr(self, 'anim') and (self.anim.state() == QPropertyAnimation.Running):
            self.anim.stop()

        # IMPORTANT: If show animation just finished, graphicsEffect might be None.
        # We need it for opacity animation.
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

        self.anim_close = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_close.setDuration(150)
        self.anim_close.setStartValue(1.0)
        self.anim_close.setEndValue(0.0)
        self.anim_close.setEasingCurve(QEasingCurve.InQuad)
        
        # Ensure we only connect once
        try:
            self.anim_close.finished.disconnect()
        except:
            pass
            
        self.anim_close.finished.connect(self._on_closed)
        self.anim_close.start()
        
    def _on_closed(self):
        self.setGraphicsEffect(None)
        self.close()
        self.closed.emit()

    def open_web(self):
        if self.character.url_detail:
            QDesktopServices.openUrl(QUrl(self.character.url_detail))

    def on_tag_click(self, tag):
        self.tag_clicked.emit(tag)
        self.animate_close()

    def update_fav_style(self, is_fav):
        if is_fav:
             self.btn_fav.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #f43f5e;
                    border-radius: 18px;
                    border: 2px solid #f43f5e;
                    font-size: 20px;
                }
             """)
             self.btn_fav.setProperty("is_fav", True)
        else:
             self.btn_fav.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #94a3b8;
                    border-radius: 18px;
                    border: none;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(244, 63, 94, 0.2);
                    color: #f43f5e;
                }
             """)
             self.btn_fav.setProperty("is_fav", False)

    def toggle_fav(self):
        curr = self.btn_fav.property("is_fav")
        new_state = not curr
        self.update_fav_style(new_state)
        
        # Update config directly if possible to keep in sync immediately
        if self.parent() and hasattr(self.parent(), 'config_manager'):
            if new_state:
                self.parent().config_manager.add_favorite(self.character.name)
            else:
                self.parent().config_manager.remove_favorite(self.character.name)
                
        # Emit signal to update UI elsewhere (like the card in the list)
        self.fav_clicked.emit(self.character, new_state)

    def generate_share_card(self):
        """Generates a shareable image and copies it to clipboard."""
        # 1. Create Pixmap (Instagram Story / Phone aspect ratio is good, but let's do a nice card 1200x630 for general social)
        w, h = 1200, 630
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        try:
            # Background (Dark Gradient)
            from PySide6.QtGui import QLinearGradient
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor("#0f172a")) # Slate 900
            grad.setColorAt(1, QColor("#1e293b")) # Slate 800
            painter.fillRect(0, 0, w, h, grad)
            
            # Draw Character Image (Left Side - Cover)
            img_w = int(w * 0.45)
            # Clip rect for image
            painter.save()
            path = QPainterPath()
            path.addRoundedRect(20, 20, img_w, h - 40, 24, 24)
            painter.setClipPath(path)
            
            # Draw the actual image if available
            if self.image_widget._pixmap:
                 # Scaled to cover
                 source = self.image_widget._pixmap
                 # Calculate aspect ratio
                 r_target = img_w / (h - 40)
                 r_source = source.width() / source.height()
                 
                 if r_source > r_target:
                     new_h = h - 40
                     new_w = new_h * r_source
                     x = 20 - (new_w - img_w) / 2
                     y = 20
                 else:
                     new_w = img_w
                     new_h = new_w / r_source
                     x = 20
                     y = 20 - (new_h - (h - 40)) / 2
                 
                 painter.drawPixmap(int(x), int(y), int(new_w), int(new_h), source)
            else:
                 painter.fillRect(20, 20, img_w, h - 40, QColor("#334155"))
            
            painter.restore()
            
            # Draw Info (Right Side)
            x_start = img_w + 60
            y_curr = 80
            
            # Title
            font = painter.font()
            font.setFamily("Segoe UI")
            font.setPixelSize(64)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#f8fafc"))
            
            name_rect = QRect(x_start, y_curr, w - x_start - 40, 200)
            painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.character.name)
            
            # Measure text height roughly
            name_metrics = painter.fontMetrics()
            name_h = name_metrics.boundingRect(name_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.character.name).height()
            y_curr += name_h + 20
            
            # Author
            font.setPixelSize(32)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#818cf8")) # Indigo 400
            painter.drawText(x_start, y_curr, f"by {self.character.author}")
            y_curr += 60
            
            # Divider
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#334155"))
            painter.drawRect(x_start, y_curr, 100, 4)
            y_curr += 40
            
            # Stats (Icons text logic is hard without specific icon font, so let's stick to text)
            font.setPixelSize(28)
            painter.setFont(font)
            painter.setPen(QColor("#94a3b8"))
            
            stats_text = f"Downloads: {self.character.downloads}    Likes: {self.character.likes}"
            painter.drawText(x_start, y_curr, stats_text)
            
            # Footer Branding
            font.setPixelSize(20)
            painter.setFont(font)
            painter.setPen(QColor("#64748b")) # Slate 500
            
            rect_footer = QRect(x_start, h - 60, w - x_start - 40, 40)
            painter.drawText(rect_footer, Qt.AlignRight | Qt.AlignBottom, "SC Character Installer")
            
        finally:
            painter.end()
            
        # Copy to Clipboard
        cb = QApplication.clipboard()
        cb.setPixmap(pixmap)
        
        # Show feedback
        # We need a parent toast access. Since we are in a modal child of MainWindow...
        parent = self.parent()
        while parent:
            if hasattr(parent, 'show_toast'):
                parent.show_toast(translator.get("success"), translator.get("msg_copied_clipboard"))
                break
                parent.show_toast(translator.get("success"), translator.get("msg_copied_clipboard"))
                break
            parent = parent.parent()

    def generate_holo_id(self):
        from src.ui.components.holo_id_card import HoloIdCard
        from PySide6.QtWidgets import QFileDialog
        
        # Create the widget off-screen (or hidden)
        # We need the pixmap from image_widget
        if not self.image_widget._pixmap:
            return
            
        card = HoloIdCard(self.character, self.image_widget._pixmap, self)
        
        # Ask where to save
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Holo-ID", f"{self.character.name}_ID.png", "PNG Files (*.png)")
        
        if file_path:
            pix = card.grab_image()
            pix.save(file_path)
            
            # Show feedback
            parent = self.parent()
            while parent:
                if hasattr(parent, 'show_toast'):
                    parent.show_toast("Holo-ID Exported", f"Saved to {file_path}")
                    break
                parent = parent.parent()
        
        card.deleteLater()


