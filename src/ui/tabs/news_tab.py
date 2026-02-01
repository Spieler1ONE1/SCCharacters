from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QScrollArea, QFrame, QPushButton)
from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QRunnable, QObject, Slot
from PySide6.QtGui import QDesktopServices, QPixmap, QColor
import datetime

from src.core.news_fetcher import NewsFetcher
from src.ui.styles import ThemeColors
from src.utils.translations import translator
from src.ui.dialogs.news_reader import NewsReaderDialog
import urllib.parse

class NewsWorkerSignals(QObject):
    finished = Signal(list)
    error = Signal(str)

class NewsWorker(QRunnable):
    def __init__(self, page=1):
        super().__init__()
        self.signals = NewsWorkerSignals()
        self.fetcher = NewsFetcher()
        self.page = page

    @Slot()
    def run(self):
        try:
            items = self.fetcher.fetch_news(page=self.page)
            self.signals.finished.emit(items)
        except Exception as e:
            self.signals.error.emit(str(e))

class NewsTranslationWorker(QObject):
    # Signals must be on QObject
    finished = Signal()
    item_translated = Signal(int, str, str) # index, title, description
    
    def __init__(self, items, lang_code):
        super().__init__()
        self.items = items
        self.lang_code = lang_code
        self._is_running = True

    def run(self):
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target=self.lang_code)
            
            for i, item in enumerate(self.items):
                if not self._is_running: break
                
                try:
                    # Translate Title
                    tr_title = translator.translate(item['title'])
                    
                    # Translate Description (truncate)
                    desc_text = item['description'].replace('\n', ' ')[:500]
                    tr_desc = translator.translate(desc_text)
                    
                    self.item_translated.emit(i, tr_title, tr_desc)
                except Exception as e:
                    # If failed, just skip emission or verify
                    pass
                    
        except ImportError:
            pass
        
        self.finished.emit()
            
    def stop(self):
        self._is_running = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl(self.item['link']))

    def update_text(self, new_title, new_description):
        # Helper to find labels in layout since we didn't save them as self.title_lbl
        # Actually in init we did: title = QLabel...
        # We need to access them. Best to refactor init to store self.title_lbl
        pass
        
# Refactoring NewsCard Init to store labels
# Refactoring NewsCard Init to store labels
class NewsCard(QFrame):
    link_activated = Signal(str)

    def __init__(self, item, image_loader, parent=None):
        super().__init__(parent)
        self.item = item
        self.image_loader = image_loader
        self.setObjectName("NewsCard")
        self.setStyleSheet("""
            #NewsCard {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 8px;
            }
            #NewsCard:hover {
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid rgba(99, 102, 241, 0.4);
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        # Main Layout (Horizontal - Side by Side)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(15)
        
        # Image (Left Side)
        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(240, 135) # 16:9 Aspect Ratio
        self.img_lbl.setStyleSheet("""
            background-color: #0f172a; 
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.05);
        """)
        self.img_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img_lbl)
        
        # Content Container (Right Side)
        # We don't need a wrapper widget for layout items necessarily, but it keeps structure clean
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 5, 0, 5) # Slight padding top/bottom
        content_layout.setSpacing(6)
        
        # Meta (Date / Source)
        date_str = "Unknown Date"
        if isinstance(item['date'], datetime.datetime):
             date_str = item['date'].strftime("%b %d, %Y").upper()
        else:
             date_str = "RECENT TRANSMISSION"

        self.meta_lbl = QLabel(f"{date_str} // {item['source'].upper()}")
        self.meta_lbl.setStyleSheet("font-size: 10px; color: #6366f1; font-weight: bold; letter-spacing: 1px;")
        
        # Title
        self.title_lbl = QLabel(item['title'])
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #f1f5f9; font-family: 'Segoe UI', sans-serif;")
        self.title_lbl.setWordWrap(True)
        # Force title to be top-aligned if not wrapped
        self.title_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Description
        self.desc_lbl = QLabel(item['description'])
        self.desc_lbl.setStyleSheet("font-size: 13px; color: #94a3b8; line-height: 1.4;")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Button / Action (Bottom)
        action_layout = QHBoxLayout()
        self.btn_read = QPushButton(translator.get('access_feed'))
        self.btn_read.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #38bdf8;
                font-weight: bold;
                font-size: 11px;
                border: none;
                text-align: left;
                padding: 0;
            }
            QPushButton:hover { text-decoration: underline; color: #7dd3fc; }
        """)
        action_layout.addWidget(self.btn_read)
        action_layout.addStretch()
        
        # Connect button click
        self.btn_read.clicked.connect(self.emit_link)
        
        content_layout.addWidget(self.meta_lbl)
        content_layout.addWidget(self.title_lbl)
        content_layout.addWidget(self.desc_lbl, 1) # Give description stretch factor?
        content_layout.addSpacing(5)
        content_layout.addLayout(action_layout)
        
        layout.addLayout(content_layout)
        
        # Load Image
        if item.get('image_url'):
            self.image_loader.load_image(item['image_url'], self._on_image_loaded)
        else:
            self.img_lbl.setText("NO SIGNAL")
            self.img_lbl.setStyleSheet("color: #475569; font-weight: bold;" + self.img_lbl.styleSheet())

    def _on_image_loaded(self, pixmap):
        if pixmap:
            # Scale keeping aspect ratio to avoid distortion
            scaled = pixmap.scaled(self.img_lbl.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            # Since we use KeepAspectRatioByExpanding, we might have overflow.
            # QLabel doesn't crop.
            # To fix "Horrible" distortion, we accept cropping essentially by just setting pixmap?
            # Or we use KeepAspectRatio and show black bars?
            # User hated STRETCHING (banner style).
            # The previous "good" version used KeepAspectRatio.
            # Let's try to fill the box cleanly.
            
            # Actually, standard KeepAspectRatio is safest to avoid "Horrible" stretching.
            # But let's try to duplicate a "Cover" effect by using a rounded mask if needed.
            # For now, let's stick to what worked: standard scaled.
            
            # Note: If we use KeepAspectRatioByExpanding, the label will Resize to fit the image if no fixed size?
            # We set FixedSize on label. So it will spill out or be clipped? 
            # QLabel paints the whole pixmap. 
            
            # Best Compromise:
            scaled = pixmap.scaled(self.img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_lbl.setPixmap(scaled)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.emit_link()

    def emit_link(self):
        self.link_activated.emit(self.item['link'])

    def update_text(self, new_title, new_description):
        self.title_lbl.setText(new_title)
        self.desc_lbl.setText(new_description)

# ... (Worker classes) ...
class NewsTranslationWorker(QRunnable):
    def __init__(self, items, lang_code):
        super().__init__()
        self.signals = TranslationSignals()
        self.items = items
        self.lang_code = lang_code
        self._is_running = True

    @Slot()
    def run(self):
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target=self.lang_code)
            
            for i, item in enumerate(self.items):
                if not self._is_running: break
                
                try:
                    # Translate Title
                    tr_title = translator.translate(item['title'])
                    
                    # Translate Description
                    desc_text = item['description'].replace('\n', ' ')[:500]
                    tr_desc = translator.translate(desc_text)
                    
                    self.signals.item_translated.emit(i, tr_title, tr_desc)
                except Exception:
                    pass
        except ImportError:
            pass
            
    def stop(self):
        self._is_running = False

class TranslationSignals(QObject):
    item_translated = Signal(int, str, str)

class NewsTab(QWidget):
    def __init__(self, image_loader, threadpool, parent=None):
        super().__init__(parent)
        self.main_window_ref = parent 
        self.image_loader = image_loader
        self.threadpool = threadpool
        self.last_update = None
        self.all_news_items = []
        self.displayed_count = 0
        self.current_page = 1
        self.is_fetching = False
        self.BATCH_SIZE = 10
        self.loading_more = False # For layout batching
        
        self.setup_ui()
        
        # Auto Update Timer (Every 15 minutes)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_news)
        self.timer.start(900000) 
        
        # Initial Load
        QTimer.singleShot(500, self.refresh_news)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header / Status
        self.header_layout = QHBoxLayout()
        self.lbl_status = QLabel("Checking comms array...")
        self.lbl_status.setStyleSheet("color: #64748b; font-size: 12px;")
        
        btn_refresh = QPushButton("Refresh Signal")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_news)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: transparent; color: #6366f1; border: 1px solid #6366f1; 
                border-radius: 4px; padding: 4px 8px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(99, 102, 241, 0.1); }
        """)
        
        self.header_layout.addWidget(self.lbl_status)
        self.header_layout.addStretch()
        self.header_layout.addWidget(btn_refresh)
        
        container = QWidget()
        container.setLayout(self.header_layout)
        layout.addWidget(container)
        
        layout.addSpacing(10)
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.viewport().setAttribute(Qt.WA_TranslucentBackground) 
        
        # Connect scrollbar to lazy load
        self.scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
        
        self.content = QWidget()
        self.content.setObjectName("NewsContent")
        self.content.setStyleSheet("background: transparent;")
        
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def refresh_news(self):
        self.lbl_status.setText("Establishing uplink...")
        self.current_page = 1
        self.all_news_items = []
        self.displayed_count = 0
        self.is_fetching = True
        
        # Clear existing
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.fetch_page(1)

    def fetch_page(self, page):
        worker = NewsWorker(page=page)
        worker.signals.finished.connect(self.on_news_loaded)
        worker.signals.error.connect(self.on_news_error)
        self.threadpool.start(worker)

    def on_news_loaded(self, items):
        self.is_fetching = False
        
        if not items and self.current_page == 1:
            self.lbl_status.setText("No signal detected.")
            lbl_empty = QLabel("No active transmissions found in sector.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #64748b; font-size: 16px; margin-top: 50px;")
            self.content_layout.addWidget(lbl_empty)
            return
            
        if not items:
            # End of all pages
            self.lbl_status.setText("Archive limit reached.")
            # Add end label
            lbl_end = QLabel("--- End of Transmissions ---")
            lbl_end.setAlignment(Qt.AlignCenter)
            lbl_end.setStyleSheet("color: #475569; font-size: 11px; margin: 20px 0;")
            self.content_layout.addWidget(lbl_end)
            return

        self.lbl_status.setText(f"Uplink Established. Archive Page {self.current_page}.")
        
        # Append new items to master list
        old_count = len(self.all_news_items)
        self.all_news_items.extend(items)
        
        # Determine if we should render immediately
        # Logic: If this was a fresh load (page 1) or a scroll load, we want to show them.
        # But we use load_more_news which uses batching.
        # So we just call load_more_news.
        
        self.load_more_news()
        self.last_update = datetime.datetime.now()

    def check_scroll_position(self, value):
        scrollbar = self.scroll.verticalScrollBar()
        if scrollbar.maximum() <= 0: return # If no scrollbar yet
        
        # Trigger when within range
        if scrollbar.maximum() - value <= 200:
            self.load_more_news()

    def load_more_news(self):
        # Prevent recursion loop if already fetching PAGE
        if self.loading_more: return
        
        # 1. Check if we have LOCAL items in buffer to show
        total_buffered = len(self.all_news_items)
        
        if self.displayed_count < total_buffered:
            self.loading_more = True
            try:
                end = min(self.displayed_count + self.BATCH_SIZE, total_buffered)
                batch = self.all_news_items[self.displayed_count:end]
                
                items_to_translate = []
                
                # Robust Language Detection
                current_lang = 'en'
                if hasattr(self, 'main_window_ref') and hasattr(self.main_window_ref, 'config_manager'):
                    current_lang = self.main_window_ref.config_manager.config.get("language", "en")
                else:
                    from src.utils.translations import translator
                    current_lang = getattr(translator, 'current_lang', 'en')

                # Critical Mapping for DeepTranslator/Google
                if current_lang == 'zh': current_lang = 'zh-CN'

                need_translation = (current_lang != 'en')

                for item in batch:
                    try:
                        # Defensive Card Creation
                        card = NewsCard(item, self.image_loader)
                        card.link_activated.connect(self.open_news_reader)
                        self.content_layout.addWidget(card)
                        
                        # Only add to translation queue if successfully added
                        items_to_translate.append(item)
                    except Exception as inner_e:
                        print(f"Error creating NewsCard for item '{item.get('title')}': {inner_e}")
                        import traceback
                        traceback.print_exc()

                layout_offset = self.displayed_count
                self.displayed_count = end

                if need_translation and items_to_translate:
                     self.start_batch_translation(items_to_translate, current_lang, layout_offset)
                
                # Force update to check scrollbar
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Recursively fill if scrollbar still missing and we have buffer
                if self.scroll.verticalScrollBar().maximum() <= 0 and self.displayed_count < total_buffered:
                    self.loading_more = False
                    self.load_more_news()
                    
            except Exception as e:
                print(f"Error rendering batch: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.loading_more = False
                
        # 2. If buffer exhausted, fetch NEXT PAGE
        elif not self.is_fetching:
             # We caught up with buffer, need more from web
             if len(self.all_news_items) > 0: # Only if we have some items already
                 self.is_fetching = True
                 self.current_page += 1
                 self.fetch_page(self.current_page)

    def start_batch_translation(self, items, lang_code, layout_offset):
        worker = NewsTranslationWorker(items, lang_code)
        # Use partial or lambda to pass offset? 
        # Can't easily pass extra args to connected slot without lambda.
        # Signals: int, str, str.
        # We can make a wrapper slot or modify worker to include offset?
        # Simpler: Make update_card_translation accept relative index and we add offset?
        # Limitation: Signals are fixed.
        # Solution: Use lambda in connect.
        worker.signals.item_translated.connect(
            lambda i, t, d: self.update_card_translation(i + layout_offset, t, d)
        )
        self.threadpool.start(worker)

    def update_card_translation(self, index, new_title, new_desc):
        # Find the card at index
        item = self.content_layout.itemAt(index)
        if item and item.widget():
            widget = item.widget()
            if isinstance(widget, NewsCard):
                widget.update_text(new_title, new_desc)

    def on_news_error(self, error):
        self.lbl_status.setText(f"Uplink Failed: {error}")

    def open_news_reader(self, url):
        # Try to get language from main window config first (most reliable)
        current_lang = 'en'
        if hasattr(self, 'main_window_ref') and hasattr(self.main_window_ref, 'config_manager'):
            current_lang = self.main_window_ref.config_manager.config.get("language", "en")
        else:
            # Fallback to global translator
            from src.utils.translations import translator
            current_lang = getattr(translator, 'current_lang', 'en')
        
        # Map 'zh' to 'zh-CN' for Google Translate if needed
        if current_lang == 'zh': current_lang = 'zh-CN'
        
        target_lang = current_lang if current_lang != 'en' else None
        
        dialog = NewsReaderDialog(
            url, 
            title="INCOMING TRANSMISSION", 
            parent=self, 
            target_language=target_lang
        )
        dialog.exec()

        
