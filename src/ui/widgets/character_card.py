import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsOpacityEffect, QSizePolicy, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize, QPointF, QVariantAnimation
from PySide6.QtGui import QPixmap, QPainter, QTransform, QColor, QBrush, QPainterPath, QPen, QLinearGradient
from src.core.models import Character
from src.utils.image_loader import ImageLoader
from src.utils.translations import translator
from src.ui.widgets.flow_layout import FlowLayout
from src.ui.anim_config import AnimConfig
from src.ui.styles import ThemeColors

class TiltLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._zoom = 1.0
        self._tilt = QPointF(0, 0)
        self._scan_pos = -1.0 # 0.0 to 1.0. -1 means inactive.

        self._pixmap = None
        
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)
    
    def set_transform_params(self, zoom, tilt):
        self._zoom = zoom
        self._tilt = tilt
        self.update()
        
    def set_scan_pos(self, pos):
        self._scan_pos = pos
        self.update()
        
    def set_gleam_color(self, color_hex):
        c = QColor(color_hex)
        # Keep it subtle (low opacity) but tinted
        self._gleam_color = QColor(c.red(), c.green(), c.blue(), 60)
        self.update()

    def paintEvent(self, event):
        # Fallback to standard paint if no pixmap (e.g. showing text/placeholder)
        if not self._pixmap or self.text(): 
            super().paintEvent(event)
            return

        painter = QPainter(self)
        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        w, h = self.width(), self.height()
        center = QPointF(w / 2, h / 2)
        
        # Create 3D-like transform
        t = QTransform()
        t.translate(center.x(), center.y())
        t.rotate(self._tilt.x(), Qt.XAxis) 
        t.rotate(self._tilt.y(), Qt.YAxis)
        t.scale(self._zoom, self._zoom)
        t.translate(-center.x(), -center.y())
        
        painter.setTransform(t)
        
        # Draw Pixmap
        # Create rounded clip path
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 8, 8)
        
        painter.setClipPath(path)
        
        # Draw background manually inside the clip/transform (so it tilts)
        painter.fillPath(path, QColor("#0f172a"))
        
        if self.hasScaledContents():
            painter.drawPixmap(self.rect(), self._pixmap)
        else:
            # PARALLAX EFFECT: Shift image opposite to tilt
            limit = 6.0 
            off_x = self._tilt.y() * -limit
            off_y = self._tilt.x() * limit
            
            x = (w - self._pixmap.width()) / 2 + off_x
            y = (h - self._pixmap.height()) / 2 + off_y
            painter.drawPixmap(int(x), int(y), self._pixmap)
            
        # --- Biometric Scanner Effect ---
        # --- Soft Sheen Effect (Less Aggressive) ---
        if self._scan_pos >= 0.0 and self._scan_pos <= 1.5:
             scan_y = h * self._scan_pos
             # No hard line, just a soft white glow

             grad_trail = QLinearGradient(0, scan_y, 0, scan_y - 60)
             grad_trail.setColorAt(0.0, QColor(255, 255, 255, 30))
             grad_trail.setColorAt(1.0, QColor(255, 255, 255, 0))
             
             painter.setPen(Qt.NoPen)
             painter.fillPath(path, QBrush(grad_trail))

        # --- Install Animation (Holographic Fill) ---
        if hasattr(self, '_install_progress') and self._install_progress > 0:
            prog = self._install_progress
            # Fill from bottom
            fill_h = h * prog
            
            # Sci-Fi Grid Pattern
            painter.setClipPath(path)
            
            # Green/Cyan Tint
            c_fill = QColor(0, 243, 255, 40) # Cyan transparent
            painter.fillRect(0, h - fill_h, w, fill_h, c_fill)
            
            # Scan line at top of fill
            painter.setPen(QPen(QColor(0, 243, 255), 2))
            painter.drawLine(0, h - fill_h, w, h - fill_h)
            
            # Random Hex/Tech debris (simulated)
            if prog < 1.0:
                import random
                rng = random.Random(int(prog * 100)) # Stable-ish noise per frame
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 255, 255, 150))
                for _ in range(5):
                    rx = rng.randint(0, w)
                    ry = h - fill_h + rng.randint(0, 20)
                    painter.drawRect(rx, ry, 2, 2)

        # --- Uninstall Animation (Red Disintegrate) ---
        if hasattr(self, '_uninstall_progress') and self._uninstall_progress > 0:
             prog = self._uninstall_progress
             # Disintegrate from top
             # We want the image to look like it's being erased
             # Draw red overlay increasing
             
             painter.setClipPath(path)
             
             # Red Glitch Overlay
             c_erase = QColor(255, 50, 50, int(150 * prog))
             painter.fillRect(0, 0, w, h, c_erase)
             
             # Static lines
             painter.setPen(QColor(255, 0, 0, 200))
             for i in range(0, h, 4):
                 if (i // 4) % 2 == 0:
                     painter.drawLine(0, i, w, i)
        
        # --- Holo / Glare Effect ---
        # --- Holo / Glare Effect ---
        if self._tilt.manhattanLength() > 0:

            
            # 1. Tech Grid Overlay (Parallax)
            # Moves slightly opposite to tilt to create depth
            grid_off_x = self._tilt.y() * 2.0
            grid_off_y = self._tilt.x() * 2.0
            
            painter.setPen(QPen(QColor(255, 255, 255, 15), 1))
            
            # Vertical lines
            grid_step = 20
            start_x = int(grid_off_x) % grid_step
            for i in range(start_x, w, grid_step):
                 painter.drawLine(i, 0, i, h)
                 
            # Horizontal lines
            start_y = int(grid_off_y) % grid_step
            for i in range(start_y, h, grid_step):
                 painter.drawLine(0, i, w, i)

            # 2. Holographic Foil Sheen
            # A rainbow-like gradient that shifts across the card
            
            # Calculate angle based on tilt for dynamic direction
            angle = (self._tilt.x() + self._tilt.y()) * 5.0
            
            # Create a multi-stop gradient for "iridescence"
            # We stretch it essentially across the view
            
            # Position the center of the sheen based on tilt
            # Map tilt (-5 to 5) to (0 to 1) roughly
            pos_x = 0.5 + (self._tilt.y() / 15.0)
            pos_y = 0.5 + (self._tilt.x() / 15.0)
            
            grad_start = QPointF(w * (pos_x - 0.5), h * (pos_y - 0.5))
            grad_end   = QPointF(w * (pos_x + 0.5), h * (pos_y + 0.5))
            
            gradient = QLinearGradient(grad_start, grad_end)
            
            # Rainbow/Oil slick colors (Sci-fi version: Cyan/Pink/White)
            c_trans = QColor(255, 255, 255, 0)
            c_cyan  = QColor(0, 240, 255, 50)
            c_pink  = QColor(255, 0, 255, 30)
            c_white = QColor(255, 255, 255, 70)
            
            gradient.setColorAt(0.0, c_trans)
            gradient.setColorAt(0.4, c_cyan)
            gradient.setColorAt(0.5, c_white)
            gradient.setColorAt(0.6, c_pink)
            gradient.setColorAt(1.0, c_trans)
            
            painter.setPen(Qt.NoPen)
            painter.fillPath(path, QBrush(gradient))
        
        painter.end()

    def set_install_progress(self, val):
        self._install_progress = val
        self.update()

    def set_uninstall_progress(self, val):
        self._uninstall_progress = val
        self.update()

class CharacterCard(QFrame):
    install_clicked = Signal(Character)
    uninstall_clicked = Signal(Character)
    delete_clicked = Signal(Character)
    fav_clicked = Signal(Character, bool) # Character, is_fav
    thumbnail_dropped = Signal(Character, str) # Character, file_path
    selection_toggled = Signal(Character, bool) # NEW: Selection support

    def __init__(self, character: Character, image_loader: ImageLoader, sound_manager=None, parent=None):
        super().__init__(parent)
        self.character = character
        self.image_loader = image_loader
        self.sound_manager = sound_manager
        self.is_selected = False # State
        
        self.setFixedSize(200, 320)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("CharacterCard")
        
        # Drag & Drop for Thumbnails
        self.setAcceptDrops(True)

        # Animation State
        self._current_zoom = 1.0
        self._current_tilt = QPointF(0, 0)
        
        self.zoom_anim = QVariantAnimation(self)
        self.zoom_anim.setDuration(200)
        self.zoom_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.zoom_anim.valueChanged.connect(self._on_zoom_changed)
        
        self.entry_anim = QPropertyAnimation()
        self.entry_anim.setPropertyName(b"opacity")
        self.entry_anim.setDuration(AnimConfig.get_duration(AnimConfig.DURATION_NORMAL))
        self.entry_anim.setEasingCurve(AnimConfig.EASING_ENTRY)
        self.entry_anim.finished.connect(self._on_entry_finished)
        
        # Scanner Animation
        self.scan_anim = QVariantAnimation(self)
        self.scan_anim.setDuration(1200)
        self.scan_anim.setStartValue(0.0)
        self.scan_anim.setEndValue(1.5) # Go slightly past
        self.scan_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.scan_anim.valueChanged.connect(self._on_scan_value)
        
        self.setup_ui()
        # Ensure we start with a clean state, but don't force Dark.
        # The parent (MainWindow) handles applying the correct theme immediately after creation.
        # self.update_theme(True) <--- REMOVED
        self.load_image()

    def _on_scan_value(self, val):
        if hasattr(self, 'image_label'):
            self.image_label.set_scan_pos(val)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                path = urls[0].toLocalFile()
                if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    event.acceptProposedAction()
                    self.setStyleSheet(f"#CharacterCard {{ border: 2px dashed #3b82f6; }}")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        # Revert style
        self.setStyleSheet("") 
        event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.thumbnail_dropped.emit(self.character, path)
            self.setStyleSheet("") # Reset style
            event.acceptProposedAction()

    def _on_entry_finished(self):
        if self.graphicsEffect() and hasattr(self, 'opacity_effect'):
            if self.opacity_effect.opacity() == 1:
                self.setGraphicsEffect(None)

    def update_theme(self, is_dark):
        c = ThemeColors(is_dark)
        # Note: Background/Border handled by Global Stylesheet (styles.py) 
        # based on "CharacterCard" selector.
        
        # Update children if created
        if hasattr(self, 'image_label'):
             # Use transparent background so our custom paint handles the tilting box
             self.image_label.setStyleSheet(f"background-color: transparent; border-radius: 4px;")
        
        if hasattr(self, 'name_label'):
             self.name_label.setObjectName("CardTitle")
             # Force style re-polish
             self.name_label.setStyleSheet(f"/* */") 

        if hasattr(self, 'author_label'):
             self.author_label.setObjectName("CardAuthor")
             self.author_label.setStyleSheet(f"/* */")

        # Stats Badges
        if hasattr(self, 'dl_label'):
             self.dl_label.setObjectName("StatBadge")
             self.dl_label.setStyleSheet(f"/* */") # Rely on stylesheet
             
        if hasattr(self, 'like_label'):
             self.like_label.setObjectName("StatBadge")
             self.like_label.setStyleSheet(f"/* */")

        # Visual indicator for installed state (Ribbon or Glow)
        # We handle this via the button logic mostly, but can add border
        if self.character.status == "installed":
            pass # Stylesheet handles specific logic if needed, but we rely on buttons now

    def animate_in(self, delay=0):
        if AnimConfig.REDUCED_MOTION:
            if self.graphicsEffect(): self.setGraphicsEffect(None)
            self.setVisible(True)
            return

        self.setVisible(True)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.entry_anim.setTargetObject(self.opacity_effect)
        self.entry_anim.setStartValue(0.0)
        self.entry_anim.setEndValue(1.0)
        
        if delay > 0:
            self.delay_timer = QTimer(self)
            self.delay_timer.setSingleShot(True)
            self.delay_timer.timeout.connect(self.entry_anim.start)
            self.delay_timer.start(delay)
        else:
            self.entry_anim.start()

    def highlight_text(self, text):
        if not text:
            self.name_label.setText(self.character.name)
            self.author_label.setText(self.character.author)
            return
            
        def get_highlighted(original, query):
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            return pattern.sub(lambda m: f'<span style="background-color: #6366f1; color: #ffffff; border-radius: 2px; padding: 0 2px;">{m.group()}</span>', original)

        self.name_label.setText(get_highlighted(self.character.name, text))
        self.author_label.setText(get_highlighted(f"{self.character.author}", text))
        
    def _on_zoom_changed(self, value):
        self._current_zoom = value
        if hasattr(self, 'image_label'):
            self.image_label.set_transform_params(self._current_zoom, self._current_tilt)
            
    def enterEvent(self, event):
        if self.sound_manager:
            self.sound_manager.play_card_hover()
        self.zoom_anim.stop()
        self.zoom_anim.setStartValue(self._current_zoom)
        self.zoom_anim.setEndValue(1.1)
        self.zoom_anim.start()
        
        # Trigger Scanner
        self.scan_anim.stop()
        self.scan_anim.start()
        
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.zoom_anim.stop()
        self.zoom_anim.setStartValue(self._current_zoom)
        self.zoom_anim.setEndValue(1.0)
        self.zoom_anim.start()
        
        self._current_tilt = QPointF(0, 0)
        if hasattr(self, 'image_label'):
             self.image_label.set_transform_params(self._current_zoom, self._current_tilt)
             
        # Reset scanner
        # self.scan_anim.stop() 
        # Optional: Let it finish or reset?
        self.image_label.set_scan_pos(-1.0) # Hide immediately
        
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        rect = self.rect()
        center = rect.center()
        pos = event.pos()
        
        # Store for paintEvent
        self._mouse_pos = pos 
        
        dx = (pos.x() - center.x()) / (rect.width() / 2)
        dy = (pos.y() - center.y()) / (rect.height() / 2)
        
        dx = max(-1.0, min(1.0, dx))
        dy = max(-1.0, min(1.0, dy))
        
        # Subtle tilt only
        MAX_TILT = 5.0
        self._current_tilt = QPointF(-dy * MAX_TILT, dx * MAX_TILT)
        
        if hasattr(self, 'image_label'):
            self.image_label.set_transform_params(self._current_zoom, self._current_tilt)
            
        self.update() # Trigger repaint for holo effect
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        # We let the stylesheet handle the base background/border via generic QFrame painting
        # But we want to add a "Holo Glow" overlay on top or underneath.
        # Since we want to preserve the rounded corners and content, we'll draw ON TOP 
        # but with a CompositionMode or just a subtle transparent gradient.
        
        super().paintEvent(event)
        
        if not hasattr(self, '_mouse_pos') or self._mouse_pos is None:
            return
            
        # Only draw holo effect if mouse is inside (or recently inside)
        if not self.underMouse():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- Holographic Border Glow ---
        # Draw a radial gradient centered on the mouse that highlights the border
        
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 16, 16) # Match border radius
        
        # 1. Stroke Glow (The "Border" lighting up)
        # Gradient centered at mouse
        grad = QLinearGradient(0, 0, w, h) # Fallback
        # Radial looks better for "spotlight" effect on border
        from PySide6.QtGui import QRadialGradient
        
        # We want the glow to be strong near the mouse
        radial = QRadialGradient(self._mouse_pos, 120) 
        # Color: Cyan/Blue or based on Theme? Let's go generic Sci-Fi Cyan
        c_glow = QColor(99, 102, 241, 180) # Indigo-ish
        c_trans = QColor(99, 102, 241, 0)
        
        radial.setColorAt(0.0, c_glow)
        radial.setColorAt(1.0, c_trans)
        
        # Draw the border stroke with this gradient
        pen = QPen(QBrush(radial), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        
        # --- 2. Subtle Surface Sheen (Interstellar style) ---
        # Very faint white/blue wash over the card near mouse
        
        sheen_radial = QRadialGradient(self._mouse_pos, 250)
        c_sheen = QColor(255, 255, 255, 15) # Very subtle
        sheen_radial.setColorAt(0.0, c_sheen)
        sheen_radial.setColorAt(1.0, Qt.transparent)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sheen_radial))
        painter.drawPath(path)


    card_clicked = Signal(Character)

    def mousePressEvent(self, event):
        # Check if we clicked on a button
        child = self.childAt(event.pos())
        if child and isinstance(child, QPushButton):
            super().mousePressEvent(event)
            return
            
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.character)
            
        super().mousePressEvent(event)

    def setup_ui(self):
        # MAIN LAYOUT
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # --- 1. Image Area (Top) ---
        # Container for relative positioning
        self.image_container = QWidget()
        self.image_container.setFixedSize(180, 180)
        
        # Actual Image (TiltLabel)
        self.image_label = TiltLabel(self.image_container)
        self.image_label.setFixedSize(180, 180)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent; border-radius: 4px;") 
        self.image_label.setScaledContents(True)
        
        # Overlays: Fav, Select, New Badge (Reparented to image_container)
        # Selection
        self.btn_select = QPushButton("", self.image_container)
        self.btn_select.setCheckable(True)
        self.btn_select.setFixedSize(24, 24)
        self.btn_select.setCursor(Qt.PointingHandCursor)
        self.btn_select.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.5);
                border: 2px solid white;
                border-radius: 12px;
            }
            QPushButton:hover { border-color: #3b82f6; }
            QPushButton:checked {
                background-color: #3b82f6; border-color: #3b82f6;
            }
        """)
        self.btn_select.clicked.connect(self.on_selection_toggle)
        # Move selection button down to make room for "NEW" ribbon if needed
        # Or just keep it there if no conflict.
        # Since we move NEW to Top Left, lets shift this down slightly so they don't fight.
        # But wait, selection is usually omnipresent?
        # Actually, let's move it to top left but offset by Y=30 to be under the badge region.
        self.btn_select.move(8, 40)
        self.btn_select.show()
        
        # Favorite (Top Right)
        self.btn_fav = QPushButton("★", self.image_container)
        self.btn_fav.setFixedSize(32, 32)
        self.btn_fav.setCursor(Qt.PointingHandCursor)
        self.btn_fav.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.4);
                color: rgba(255, 255, 255, 0.7);
                border-radius: 16px;
                border: none;
                font-size: 18px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: rgba(244, 63, 94, 0.8);
                color: white;
            }
        """)
        self.btn_fav.clicked.connect(self.toggle_fav)
        self.btn_fav.move(140, 8) # 180 - 32 - 8 = 140
        self.btn_fav.show()
        
        # New Badge - Top Left Corner Ribbon
        if self.character.is_new:
            self.lbl_new = QLabel(translator.get("new_badge"), self.image_container)
            self.lbl_new.setAlignment(Qt.AlignCenter)
            self.lbl_new.setFixedSize(60, 24) # Larger
            self.lbl_new.setStyleSheet("""
                QLabel {
                    background-color: #2563eb; /* Stronger Blue */
                    color: white; 
                    font-weight: 800; 
                    font-size: 11px;
                    border-top-left-radius: 4px;
                    border-bottom-right-radius: 8px;
                    /* Shadow for visibility */
                    padding: 2px;
                }
            """)
            self.lbl_new.move(0, 0) # Top Left Absolute
            # Slight shadow effect
            effect = QGraphicsDropShadowEffect(self.lbl_new)
            effect.setBlurRadius(8)
            effect.setColor(QColor(0,0,0, 120))
            effect.setOffset(2, 2)
            self.lbl_new.setGraphicsEffect(effect)
            
            self.lbl_new.show()
            
        layout.addWidget(self.image_container, alignment=Qt.AlignCenter)
        
        # --- 2. Info Area (Middle) ---
        # Name
        self.name_label = QLabel(self.character.name)
        self.name_label.setObjectName("CardTitle")
        self.name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter | Qt.AlignTop) 
        self.name_label.setFixedHeight(40) 
        layout.addWidget(self.name_label)
        
        # Author
        self.author_label = QLabel(f"{self.character.author}")
        self.author_label.setObjectName("CardAuthor")
        self.author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.author_label)
        
        # Badges Row (Stats)
        badges_layout = QHBoxLayout()
        badges_layout.setContentsMargins(0, 4, 0, 4)
        badges_layout.setSpacing(8)
        badges_layout.setAlignment(Qt.AlignCenter)
        
        def fmt_num(n):
            if n >= 1000: return f"{n/1000:.1f}k"
            return str(n)

        # DL Badge
        if hasattr(self.character, 'downloads') and self.character.downloads > 0:
            self.dl_label = QLabel(f"⬇ {fmt_num(self.character.downloads)}")
            self.dl_label.setObjectName("StatBadge")
            badges_layout.addWidget(self.dl_label)

        # Like Badge
        if hasattr(self.character, 'likes') and self.character.likes > 0:
            self.like_label = QLabel(f"♥ {fmt_num(self.character.likes)}")
            self.like_label.setObjectName("StatBadge")
            badges_layout.addWidget(self.like_label)
            
        layout.addLayout(badges_layout)
        
        # --- 3. Action Area (Bottom) ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        
        self.btn_install = QPushButton(translator.get("install"))
        self.btn_install.setCursor(Qt.PointingHandCursor)
        self.btn_install.setMinimumHeight(34)
        self.btn_install.clicked.connect(self.on_install)
        
        self.btn_delete = QPushButton("🗑️") 
        self.btn_delete.setObjectName("deleteButton")
        self.btn_delete.setFixedSize(36, 34)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_delete.hide()
        
        btn_layout.addWidget(self.btn_install)
        btn_layout.addWidget(self.btn_delete)
        
        if self.character.status == "installed":
             self.mark_installed()
             
        layout.addLayout(btn_layout)
        
    def load_image(self):
        if self.character.image_url:
            self.image_loader.load_image(
                self.character.image_url, 
                self.set_image,
                self.on_image_error
            )
        else:
            self.set_placeholder_image()

    def start_install_anim(self):
        """Starts the sci-fi installation animation."""
        self._install_anim = QVariantAnimation(self)
        self._install_anim.setDuration(1500)
        self._install_anim.setStartValue(0.0)
        self._install_anim.setEndValue(1.0)
        self._install_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._install_anim.valueChanged.connect(self.image_label.set_install_progress)
        self._install_anim.finished.connect(lambda: self.image_label.set_install_progress(0)) # Reset
        self._install_anim.start()
        
        # Audio
        if self.sound_manager:
            # We use 'install_finished' as a generic pleasant sci-fi sound for now, 
            # ideally we'd have a loop but one-shot is fine for 1.5s
            self.sound_manager.play('click') # Initial click
            QTimer.singleShot(1400, lambda: self.sound_manager.play('install_finished'))

    def start_uninstall_anim(self):
        """Starts the sci-fi uninstallation animation."""
        self._uninstall_anim = QVariantAnimation(self)
        self._uninstall_anim.setDuration(1200)
        self._uninstall_anim.setStartValue(0.0)
        self._uninstall_anim.setEndValue(1.0)
        self._uninstall_anim.setEasingCurve(QEasingCurve.InExpo)
        self._uninstall_anim.valueChanged.connect(self.image_label.set_uninstall_progress)
        self._uninstall_anim.finished.connect(lambda: self.image_label.set_uninstall_progress(0))
        self._uninstall_anim.start()
        
        # Audio
        if self.sound_manager:
            self.sound_manager.play('trash')

    def set_image(self, pixmap):
        if hasattr(self, 'pulse_anim'):
            self.pulse_anim.stop()
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("")
        # Apply Vibe Color to Gleam
        avg_color = self.image_loader.get_average_color(pixmap)
        self.image_label.set_gleam_color(avg_color)
        
    def on_image_error(self, error):
        self.set_placeholder_image()
        
    def set_placeholder_image(self):
        pixmap = self.generate_placeholder()
        self.set_image(pixmap)

    def generate_placeholder(self):
        """Generates a unique gradient placeholder based on character name."""
        size = 180
        pixmap = QPixmap(size, size)
        
        h = hash(self.character.name)
        hue = abs(h) % 360
        
        from PySide6.QtGui import QLinearGradient
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(0, 0, size, size)
        c1 = QColor.fromHsl(hue, 200, 100)
        c2 = QColor.fromHsl((hue + 40) % 360, 200, 60)
        
        gradient.setColorAt(0, c1)
        gradient.setColorAt(1, c2)
        
        painter.fillRect(0, 0, size, size, gradient)
        
        # Initials
        painter.setPen(QColor(255, 255, 255, 240))
        font = painter.font()
        font.setFamily("Segoe UI")
        font.setPixelSize(60)
        font.setBold(True)
        painter.setFont(font)
        
        name_parts = self.character.name.split()
        initials = ""
        if name_parts:
            initials = name_parts[0][0].upper()
            if len(name_parts) > 1:
                initials += name_parts[1][0].upper()
        else:
            initials = "?"
            
        painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)
        painter.end()
        
        return pixmap
        
    def on_install(self):
        if self.character.status == "installed":
            return
        self.btn_install.setEnabled(False)
        self.btn_install.setText(translator.get("downloading"))
        self.start_install_anim()
        self.install_clicked.emit(self.character)
        
    def on_delete(self):
        self.start_uninstall_anim()
        self.delete_clicked.emit(self.character)
        
    def mark_installed(self):
        self.btn_install.setText(translator.get("installed"))
        self.btn_install.setEnabled(False) 
        self.btn_install.setStyleSheet("background-color: #10b981; border: none; color: white;") # Using success green
        self.btn_delete.show()
        
    def set_uninstall_mode(self):
        self.mark_installed()
        
    def mark_error(self):
        self.btn_install.setText(translator.get("error"))
        self.btn_install.setEnabled(True)
        self.btn_install.setStyleSheet("background-color: #ef4444; border: none;") # Using error red

    def set_favorite(self, is_fav: bool):
        if is_fav:
             # Make it Gold (Star)
             self.btn_fav.setStyleSheet("""
                QPushButton {
                    background-color: #f59e0b;
                    color: white;
                    border-radius: 16px;
                    border: none;
                    font-size: 20px;
                    font-weight: bold;
                    padding-bottom: 2px;
                }
             """)
        else:
             # Revert (Transparent Black)
             self.btn_fav.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 0.4);
                    color: rgba(255, 255, 255, 0.6);
                    border-radius: 16px;
                    border: none;
                    font-size: 20px;
                    font-weight: bold;
                    padding-bottom: 2px;
                }
                QPushButton:hover {
                    background-color: #fbbf24;
                    color: white;
                }
             """)

    def toggle_fav(self):
        # Check current state based on stylesheet (simple check)
        is_fav = "background-color: #f59e0b" in self.btn_fav.styleSheet()
        new_state = not is_fav
        
        self.set_favorite(new_state)
        self.fav_clicked.emit(self.character, new_state)

    def on_selection_toggle(self, checked):
        self.is_selected = checked
        self.selection_toggled.emit(self.character, checked)
        
    def set_selected(self, selected):
        self.is_selected = selected
        self.btn_select.setChecked(selected)

    def format_date(self, date_str):
        if not date_str:
            return ""
        try:
            from datetime import datetime
            # Handle Z manually or use robust parsing
            ts_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_str)
            return dt.strftime("%Y-%m-%d")
        except:
            return ""
