from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextBrowser, 
                               QComboBox, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextDocument

import requests
import json
import markdown
import base64
from bs4 import BeautifulSoup
from datetime import datetime
from deep_translator import GoogleTranslator

class ChangelogFetcher(QThread):
    finished = Signal(list) # Returns list of releases
    error = Signal(str)

    def run(self):
        try:
            # Fetch from GitHub API
            url = "https://api.github.com/repos/Spieler1ONE1/SCCharacters/releases"
            # GitHub requires a User-Agent
            headers = {"User-Agent": "SCCharactersApp"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                releases = response.json()
                self.finished.emit(releases)
            else:
                self.error.emit(f"Failed to fetch releases: {response.status_code} {response.reason}")
        except Exception as e:
            self.error.emit(str(e))

class TranslationWorker(QThread):
    finished = Signal(str, str) # release_tag, translated_text
    
    def __init__(self, release_tag, text, target_lang):
        super().__init__()
        self.release_tag = release_tag
        self.text = text
        self.target_lang = target_lang
        
    def run(self):
        try:
            # Check for internet or just try
            # GoogleTranslator handles splitting chunks if needed, but for changelogs it might be fine directly 
            # or we might want to split slightly. deep_translator usually handles reasonable lengths.
            translation = GoogleTranslator(source='auto', target=self.target_lang).translate(self.text)
            self.finished.emit(self.release_tag, translation)
        except Exception as e:
            # Fallback to original text on error
            self.finished.emit(self.release_tag, self.text)

class ChangelogTab(QWidget):
    def __init__(self, current_version="1.0.0", parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.releases = []
        self.translation_cache = {} # Map tag -> translated_body
        self.current_worker = None
        self.setup_ui()
        # Delay load slightly to ensure UI is ready
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title = QLabel(self.tr("Changelog"))
        title.setObjectName("H1")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(200)
        self.version_combo.currentIndexChanged.connect(self.on_version_changed)
        
        button_style = """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """

        btn_refresh = QPushButton("↻")
        btn_refresh.setToolTip(self.tr("Reload"))
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(button_style)
        btn_refresh.clicked.connect(self.load_data)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel(self.tr("Version:")))
        header_layout.addWidget(self.version_combo)
        header_layout.addWidget(btn_refresh)
        
        layout.addLayout(header_layout)

        # Content Area
        self.content_area = QTextBrowser()
        self.content_area.setOpenExternalLinks(True)
        # Use document CSS to force styling on markdown elements
        self.content_area.setStyleSheet("""
            QTextBrowser {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 15px;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        
        layout.addWidget(self.content_area)

    def load_data(self):
        self.content_area.setHtml(f"<div style='color: #94a3b8; font-style: italic;'>{self.tr('Loading updates...')}</div>")
        self.fetcher = ChangelogFetcher()
        self.fetcher.finished.connect(self.on_data_loaded)
        self.fetcher.error.connect(self.on_error)
        self.fetcher.start()

    def on_data_loaded(self, releases):
        try:
            self.releases = releases
            self.version_combo.blockSignals(True) # Prevent triggering change during clear
            self.version_combo.clear()
            self.translation_cache = {} # Clear cache on reload
            
            if not releases:
                 self.content_area.setHtml("<div style='color: #94a3b8;'>No release notes found.</div>")
                 self.version_combo.blockSignals(False)
                 return

            for release in releases:
                tag = release.get("tag_name", "Unknown")
                date_str = release.get("published_at", "")[:10]
                
                display_text = f"{tag} ({date_str})"
                
                # Normalize versions for comparison (remove 'v')
                tag_clean = tag.lstrip('v')
                curr_clean = self.current_version.lstrip('v')
                
                if tag_clean == curr_clean:
                    display_text += " (Current)"
                    
                self.version_combo.addItem(display_text, release)

            self.version_combo.blockSignals(False)
            
            if self.releases:
                self.version_combo.setCurrentIndex(0)
                self.display_release(self.releases[0])
        except Exception as e:
            self.on_error(f"UI Error: {str(e)}")

    def on_error(self, msg):
        self.content_area.setHtml(f"<div style='color: #ef4444; font-weight: bold;'>Error loading changelog:</div><br>{msg}")

    def on_version_changed(self, index):
        if index >= 0:
            release = self.version_combo.itemData(index)
            self.display_release(release)
    
    def on_translation_finished(self, tag, translated_text):
        self.translation_cache[tag] = translated_text
        
        # If currently selected release is the one we just translated, refresh view
        current_idx = self.version_combo.currentIndex()
        if current_idx >= 0:
            current_tag = self.version_combo.itemData(current_idx).get("tag_name")
            if current_tag == tag:
                self.display_release(self.version_combo.itemData(current_idx))

    def display_release(self, release):
        try:
            body = release.get("body")
            if not body:
                body = "*No description provided for this release.*"
            tag = release.get("tag_name")
            
            # Check Language
            from src.utils.translations import translator
            current_lang = translator.current_lang
            
            # If not English and not cached, start translation
            if current_lang != 'en':
                if tag in self.translation_cache:
                    body = self.translation_cache[tag]
                else:
                    # Trigger translation if not running for this tag
                    # We show original English meanwhile, maybe with a note
                    body = f"> *{self.tr('Translating...')}*\n\n" + body
                    
                    # Avoid spawning multiple workers for same tag
                    # Simple check: we just fire it. 
                    worker = TranslationWorker(tag, release.get("body", ""), current_lang)
                    worker.finished.connect(self.on_translation_finished)
                    worker.start()
                    # Store reference to prevent GC?
                    self.current_worker = worker # Only keeps last one, but fine for sequential browsing
            
            # Convert Markdown to HTML using the python-markdown library
            # 'extra' includes tables, fenced_code, etc.
            html_content = markdown.markdown(body, extensions=['extra', 'nl2br'])
            
            # Process images to embed them directly (fixes Qt display issues)
            soup = BeautifulSoup(html_content, 'html.parser')
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and src.startswith(('http://', 'https://')):
                    try:
                        # Fetch image
                        headers = {"User-Agent": "SCCharactersApp"}
                        response = requests.get(src, headers=headers, timeout=5)
                        if response.status_code == 200:
                            # Convert to base64
                            b64_data = base64.b64encode(response.content).decode('utf-8')
                            content_type = response.headers.get('Content-Type', 'image/png')
                            img['src'] = f"data:{content_type};base64,{b64_data}"
                    except Exception as img_err:
                        print(f"Failed to load image {src}: {img_err}")
            
            processed_html = str(soup)
            
            # Create a full HTML document with embedded CSS
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ 
                    color: #e2e8f0; 
                    font-family: 'Segoe UI', 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif;
                    font-size: 14pt;
                    background-color: #1e293b;
                    line-height: 1.6;
                }}
                h1 {{ color: #818cf8; font-size: 24pt; font-weight: bold; margin: 20px 0 10px 0; }}
                h2 {{ color: #a5b4fc; font-size: 20pt; font-weight: bold; margin: 15px 0 8px 0; border-bottom: 1px solid #334155; padding-bottom: 5px; }}
                h3 {{ color: #c7d2fe; font-size: 16pt; font-weight: bold; margin: 10px 0 5px 0; }}
                h4, h5, h6 {{ color: #e2e8f0; font-size: 14pt; font-weight: bold; }}
                
                p {{ margin-bottom: 15px; }}
                ul, ol {{ margin-left: 20px; margin-bottom: 15px; }}
                li {{ margin-bottom: 5px; }}
                
                a {{ color: #38bdf8; text-decoration: none; font-weight: bold; }}
                
                img {{ 
                    max-width: 100%; 
                    height: auto; 
                    display: block; 
                    margin: 15px auto; 
                    border-radius: 8px; 
                    border: 1px solid #334155;
                }}
                
                code {{ 
                    background-color: #334155; 
                    color: #f1f5f9; 
                    padding: 2px 4px; 
                    border-radius: 4px; 
                    font-family: 'Consolas', monospace; 
                    font-size: 13pt;
                }}
                
                pre {{ 
                    background-color: #0f172a; 
                    color: #cbd5e1; 
                    padding: 15px; 
                    border: 1px solid #334155; 
                    border-radius: 6px; 
                    margin: 15px 0;
                    white-space: pre-wrap;
                }}
                
                blockquote {{
                    border-left: 4px solid #64748b;
                    padding-left: 15px;
                    color: #94a3b8;
                    margin: 10px 0;
                    background-color: #1e293b; 
                }}
                
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0; 
                    background-color: #1e293b;
                    border: 1px solid #475569;
                }}
                th {{ 
                    background-color: #334155; 
                    color: #f1f5f9; 
                    padding: 12px; 
                    border: 1px solid #475569; 
                    font-weight: bold; 
                    text-align: left;
                }}
                td {{ 
                    padding: 10px; 
                    border: 1px solid #475569; 
                    color: #e2e8f0; 
                }}
                
                hr {{ color: #475569; background-color: #475569; height: 1px; border: none; margin: 30px 0; }}
            </style>
            </head>
            <body>
                {processed_html}
                <br><br>
            </body>
            </html>
            """
            
            self.content_area.setHtml(full_html)
        
        except Exception as e:
            self.on_error(f"Render Error: {str(e)}")

    def tr(self, text):
        # Fallback if no translator context
        from src.utils.translations import translator
        try:
            return translator.get(text)
        except Exception:
            return text
