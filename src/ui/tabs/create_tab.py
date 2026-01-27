
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QFrame, QMessageBox)
from PySide6.QtCore import Qt, QUrl, Slot, QTimer, QRectF
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineDownloadRequest
from PySide6.QtGui import QColor, QDesktopServices, QPainterPath, QRegion
import os
import shutil
from src.core.config_manager import ConfigManager
from src.ui.styles import ThemeColors
from src.utils.translations import translator

class CreateTab(QWidget):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        # Determine theme for initial load
        self.is_dark = (self.config_manager.config.get("theme", "dark") == "dark")
        self.theme_colors = ThemeColors(self.is_dark)

        # Setup WebEngine Logic first
        self.webview = QWebEngineView()
        
        # Configure Profile for Downloads
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.on_download_requested)
        
        # Create a page using this profile
        page = QWebEnginePage(self.profile, self.webview)
        
        # Set dark background to prevent white flash
        bg_color = self.theme_colors.bg_primary
        page.setBackgroundColor(QColor(bg_color))
        
        self.webview.setPage(page)
        self.webview.setStyleSheet(f"background-color: {bg_color};") # Ensure widget bg matches
        self.webview.setUrl(QUrl("https://starchar.app/"))
        
        self.setup_ui()
        
    def tr(self, key, **kwargs):
        return translator.get(key, **kwargs)

    def setup_ui(self):
        c = self.theme_colors
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(15, 15, 15, 15) # Floating with rounded corners

        # --- Web View ---
        # The webview takes the entire space as requested
        layout.addWidget(self.webview)

    def resizeEvent(self, event):
        if hasattr(self, 'webview') and self.webview:
             path = QPainterPath()
             rect = QRectF(self.webview.rect())
             path.addRoundedRect(rect, 20, 20)
             region = QRegion(path.toFillPolygon().toPolygon())
             self.webview.setMask(region)
        super().resizeEvent(event)

    def update_theme(self, is_dark):
        self.is_dark = is_dark
        self.theme_colors = ThemeColors(is_dark)
        c = self.theme_colors
        
        # Update Webview BG
        self.webview.page().setBackgroundColor(QColor(c.bg_primary))
        self.webview.setStyleSheet(f"background-color: {c.bg_primary};")

        
    @Slot(QWebEngineDownloadRequest)
    def on_download_requested(self, download_item: QWebEngineDownloadRequest):
        """
        Intercepts downloads from the webview.
        If it's a .chf, saves it directly to the SC CustomCharacters folder.
        """
        target_dir = self.config_manager.get_game_path()
        original_name = download_item.downloadFileName()
        
        if not os.path.exists(target_dir):
            if not self.config_manager.validate_path():
                 # Let user handle it if path is totally broken
                 download_item.accept()
                 return

        # Check for .chf OR if simple "Download" name which might be a blob
        is_chf = original_name.lower().endswith('.chf')
        
        # Sometimes blobs come with "Download" or UUIDs. 
        # Since this is a specialized tab for character creation, 
        # we can be a bit more aggressive if standard checks fail but it looks like an export.
        
        if is_chf:
            # Construct target path
            target_path = os.path.join(target_dir, original_name)
            
            # Check if file exists
            if os.path.exists(target_path):
                # Prompt user
                reply = QMessageBox.question(
                    self, 
                    self.tr("duplicate_file"),
                    self.tr("duplicate_msg", name=original_name),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                # We map Yes to Overwrite, No to Rename (Auto), Cancel to Abort
                # Actually standard buttons often confuse for this custom logic. 
                # Let's use custom button text if possible, but QMessageBox is rigid.
                # Let's assume: Yes = Overwrite, No = Create Copy.
                
                # Better Approach: Use standard buttons but explain in text
                # "File exists. Yes to Overwrite, No to Keep Both (Rename)."
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Overwrite
                    try:
                        os.remove(target_path)
                    except Exception as e:
                        print(f"Failed to remove existing file: {e}")
                elif reply == QMessageBox.StandardButton.No:
                    # Rename (Keep Both)
                    base, ext = os.path.splitext(original_name)
                    counter = 1
                    while os.path.exists(target_path):
                         target_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                         counter += 1
                else:
                    download_item.cancel()
                    return

            
            # IMPORTANT: QWebEngineDownloadRequest properties work best when absolute path is clear.
            # setDownloadDirectory expects the DIR.
            # setDownloadFileName expects the NAME.
            
            download_item.setDownloadDirectory(os.path.dirname(target_path))
            download_item.setDownloadFileName(os.path.basename(target_path))
            
            # Force save mode to avoid dialog
            # (Behavior might depend on OS, but this signals intent)
            
            # Connect finish signal
            download_item.finished.connect(lambda: self.on_download_finished(target_path))
            download_item.accept()
            print(f"Intercepted CHF download: {target_path}")
        else:
            # Let standard download happen for non-chf files
            download_item.accept()

    def on_download_finished(self, path):
         if self.parent() and hasattr(self.parent(), 'show_toast'):
              self.parent().show_toast(self.tr("success"), f"{self.tr('msg_saved')}: {os.path.basename(path)}")
         else:
              QMessageBox.information(self, self.tr("success"), f"{self.tr('msg_saved')}\n{path}")

    def open_install_folder(self):
        path = self.config_manager.get_game_path()
        if os.path.exists(path):
            os.startfile(path)
        else:
             QMessageBox.warning(self, self.tr("error"), self.tr("path_not_found"))
