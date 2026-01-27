from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QLineEdit, QComboBox, QMessageBox, QFrame, QApplication)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction

from src.ui.widgets.auto_scroll_area import AutoScrollArea
from src.ui.widgets.flow_layout import FlowLayout
from src.ui.widgets import CharacterCard, setup_localized_context_menu
from src.ui.widgets.skeleton import SkeletonCard
from src.ui.anim_config import AnimConfig
from src.core.workers import ScraperWorker, SyncAllWorker
from src.utils.translations import translator
from src.ui.styles import ThemeColors

class OnlineTab(QWidget):
    """
    Tab for browsing online characters.
    Handles scraping, filtering, sorting, and pagination.
    """
    character_clicked = Signal(object)
    install_clicked = Signal(object)
    delete_clicked = Signal(object)
    toast_requested = Signal(str, str)
    status_updated = Signal(str)
    sync_finished = Signal() # NEW: Sync finished signal

    def __init__(self, config_manager, theme_manager, scraper, image_loader, sound_manager, threadpool, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.scraper = scraper
        self.image_loader = image_loader
        self.sound_manager = sound_manager
        self.threadpool = threadpool
        
        # State
        self.all_characters = []
        self.display_candidates = []
        self.character_widgets = []
        self.selected_characters = set() # NEW: Selected chars
        self.installed_identifiers = set() # NEW: Installed Registry
        self.current_page = 1
        self.is_loading = False
        self.fully_synced = False
        self.pending_pages = 0
        self.stop_sync_flag = False
        self.sync_active = False
        self.PAGE_SIZE = 24
        
        # Search Debounce
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(800) # 800ms delay
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setup_ui()
        # Initial load is triggered by MainWindow to allow UI to settle

    def tr(self, key, **kwargs):
        return translator.get(key, **kwargs)

    def setup_ui(self):
        self.setObjectName("OnlineTab")
        layout = QVBoxLayout(self)
        
        # --- Hero Section ---
        hero_widget = QWidget()
        hero_widget.setObjectName("HeroWidget")
        hero_layout = QVBoxLayout(hero_widget)
        hero_layout.setContentsMargins(0, 10, 0, 20)
        hero_layout.setSpacing(5)
        
        self.hero_title = QLabel(self.tr("hero_title"))
        self.hero_title.setAlignment(Qt.AlignCenter)
        # Style will be set by update_theme
        
        self.hero_subtitle = QLabel(self.tr("hero_subtitle"))
        self.hero_subtitle.setAlignment(Qt.AlignCenter)
        
        hero_layout.addWidget(self.hero_title)
        hero_layout.addWidget(self.hero_subtitle)
        
        layout.addWidget(hero_widget)
        
        # --- Search Bar & Toolbar ---
        search_layout = QHBoxLayout()
        
        self.btn_reload = QPushButton(self.tr("reload"))
        self.btn_reload.setObjectName("actionButton")
        self.btn_reload.setMinimumHeight(40)
        self.btn_reload.setCursor(Qt.PointingHandCursor)
        self.btn_reload.clicked.connect(self.load_characters) 
        
        # Bulk Install Button (Hidden by default)
        self.btn_bulk_install = QPushButton(self.tr("install_selected"))
        self.btn_bulk_install.setObjectName("actionButton")
        self.btn_bulk_install.setMinimumHeight(40)
        self.btn_bulk_install.setCursor(Qt.PointingHandCursor)
        self.btn_bulk_install.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 0 15px;")
        self.btn_bulk_install.hide()
        self.btn_bulk_install.clicked.connect(self.install_selected)
        
        # Favorites Filter
        self.btn_filter_fav = QPushButton("♥")
        self.btn_filter_fav.setCheckable(True)
        self.btn_filter_fav.setCursor(Qt.PointingHandCursor)
        self.btn_filter_fav.setFixedSize(40, 40)
        self.btn_filter_fav.setToolTip(self.tr("show_favorites"))
        self.btn_filter_fav.clicked.connect(self.update_display_list) 
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            self.tr("sort_name_az"), 
            self.tr("sort_date_new"), 
            self.tr("sort_most_downloaded"),
            self.tr("sort_most_liked")
        ])
        self.sort_combo.setMinimumHeight(40)
        self.sort_combo.setMinimumHeight(40)
        # We use activated to detect re-selection of the same item (toggle behavior)
        self.sort_combo.activated.connect(self.on_sort_activated)
        
        # Internal state for toggles
        self.date_reverse = False # False = New-Old (Default), True = Old-New
        self.last_sort_index = 0
        
        # Search field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("filter_placeholder"))
        self.search_input.setMinimumHeight(40)
        self.search_input.setFixedWidth(250)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.perform_search)
        setup_localized_context_menu(self.search_input)
        
        search_layout.addWidget(self.btn_reload) 
        search_layout.addWidget(self.btn_bulk_install)
        search_layout.addWidget(self.btn_filter_fav) 
        search_layout.addWidget(self.sort_combo)
        


        search_layout.addStretch()
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # --- Content Area (Grid) ---
        self.scroll_area = AutoScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("ContentWidget")
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Grid for characters
        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("GridWidget")
        self.flow_layout = FlowLayout(self.grid_widget, margin=0, spacing=15)
        
        self.content_layout.addWidget(self.grid_widget)
        
        # Load More Button
        self.btn_load_more = QPushButton(self.tr("load_more"))
        self.btn_load_more.setMinimumHeight(40)
        self.btn_load_more.setCursor(Qt.PointingHandCursor)
        self.btn_load_more.clicked.connect(self.load_more_characters)
        self.btn_load_more.hide()
        
        self.content_layout.addWidget(self.btn_load_more)
        
        self.scroll_area.setWidget(self.content_widget)
        
        # Infinite Scroll
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll_bottom)
        
        layout.addWidget(self.scroll_area)
        
        self.update_theme() # Apply initial styles

    def update_theme(self, is_dark=None):
        if is_dark is None:
            is_dark = (self.theme_manager.get_effective_theme() == 'dark')
            
        c = ThemeColors(is_dark)
        
        self.hero_title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 800;
            color: {c.text_primary}; 
            letter-spacing: 1px;
            font-family: 'Segoe UI', sans-serif;
            background: transparent;
        """)
        self.hero_subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {c.text_secondary}; 
            font-weight: 500;
            background: transparent;
        """)
        
        self.btn_filter_fav.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {c.border};
                border-radius: 8px;
                color: {c.text_secondary};
                font-size: 18px;
            }}
            QPushButton:checked {{
                background-color: rgba(244, 63, 94, 0.2);
                border: 1px solid #f43f5e;
                color: #f43f5e;
            }}
            QPushButton:hover {{
                 background-color: {c.bg_tertiary};
            }}
        """)
        
        # Update cards
        for widget in self.character_widgets:
             if isinstance(widget, CharacterCard):
                widget.update_theme(is_dark)

    def load_characters(self):
        if self.is_loading: return
        self.is_loading = True
        
        self.show_skeletons()
        self.status_updated.emit(self.tr("loading"))
        self.btn_reload.setEnabled(False)
        self.btn_load_more.hide()
        
        # Reset
        self.current_page = 1
        self.all_characters = []
        self.fully_synced = False
        
        search_text = self.search_input.text().strip() or None
        
        # Determine pages to fetch
        pages = 5 
        self.pending_pages = 5
        sort_index = self.sort_combo.currentIndex()
        
        if search_text:
            pages = 1
            self.pending_pages = 1
        elif sort_index in [2, 3]: # Popularity sorts need deep scan locally if not API supported
            # Actually, standard scraper doesn't support server-side sort, so we need deep scan
            pages = 20
            self.pending_pages = 20
            self.status_updated.emit(self.tr("deep_scan"))

        worker = ScraperWorker(self.scraper, start_page=1, pages_to_fetch=pages, search_query=search_text)
        worker.signals.result.connect(self.on_characters_loaded)
        worker.signals.error.connect(self.on_load_error)
        worker.signals.progress.connect(self.status_updated.emit)
        self.threadpool.start(worker)

    def on_characters_loaded(self, characters):
        self.is_loading = False
        self.status_updated.emit(self.tr("ready"))
        self.btn_reload.setEnabled(True)
        self.all_characters = characters
        
        # Adjust current page
        self.current_page = self.pending_pages if hasattr(self, 'pending_pages') else 1

        self.populate_grid(characters, clear=True)
        self.scroll_area.verticalScrollBar().setValue(0)
        
        if characters:
            self.btn_load_more.show()
            self.btn_load_more.setText(self.tr("load_more"))
            self.btn_load_more.setEnabled(True)
            QTimer.singleShot(100, self.check_scroll_bottom)
        else:
            self.btn_load_more.hide()
            self.status_updated.emit(self.tr("no_chars_web"))

    def load_more_characters(self):
        if self.is_loading: return
        self.is_loading = True
        self.btn_load_more.setText(self.tr("loading"))
        
        # Local Pagination
        if self.fully_synced and self.display_candidates:
            QTimer.singleShot(50, self._process_local_load_more)
            return

        # Scraper Mode
        next_page = self.current_page + 1
        search_text = self.search_input.text().strip() or None
            
        worker = ScraperWorker(self.scraper, start_page=next_page, pages_to_fetch=1, search_query=search_text)
        worker.signals.result.connect(self.on_more_characters_loaded)
        worker.signals.error.connect(self.on_load_error)
        self.threadpool.start(worker)

    def _process_local_load_more(self):
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        new_batch = self.display_candidates[start:end]
        
        self.is_loading = False
        if new_batch:
            self.current_page += 1
            self.populate_grid(new_batch, clear=False)
            self.btn_load_more.setText(self.tr("load_more"))
            self.btn_load_more.setEnabled(True)
        else:
            self.btn_load_more.hide()
            
        if (self.current_page * self.PAGE_SIZE) >= len(self.display_candidates):
            self.btn_load_more.hide()

    def on_more_characters_loaded(self, characters):
        self.is_loading = False
        self.btn_load_more.setText(self.tr("load_more"))
        self.btn_load_more.setEnabled(True)
        
        if characters:
            # Filter duplicates
            new_chars = []
            existing_ids = {c.download_url for c in self.all_characters} 
            for char in characters:
                if char.download_url not in existing_ids:
                    new_chars.append(char)
                    existing_ids.add(char.download_url)
            
            if new_chars:
                scroll_bar = self.scroll_area.verticalScrollBar()
                current_scroll = scroll_bar.value()
                
                self.current_page += 1
                self.all_characters.extend(new_chars)
                self.populate_grid(new_chars, clear=False)
                self.status_updated.emit(self.tr("ready"))
                
                QTimer.singleShot(0, lambda: scroll_bar.setValue(current_scroll))
            else:
                 # Duplicate detection logic (skip forward)
                 expected_page = max(1, len(self.all_characters) // 12)
                 if self.current_page < expected_page:
                    self.current_page = expected_page
        else:
            self.btn_load_more.setText(self.tr("no_more_chars"))
            self.btn_load_more.setEnabled(False)

    def on_load_error(self, error_msg):
        self.is_loading = False
        self.status_updated.emit(self.tr("error"))
        self.btn_load_more.setText(self.tr("error"))
        self.btn_load_more.setEnabled(True)
        self.btn_reload.setEnabled(True)
        if getattr(self, 'sync_active', False):
             self.sync_active = False
        self.toast_requested.emit(self.tr("error"), str(error_msg))

    def populate_grid(self, characters, clear=True):
        if clear:
            while self.flow_layout.count():
                item = self.flow_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.setParent(None)
            self.character_widgets = []
        
        delay = 0
        is_dark = (self.theme_manager.get_effective_theme() == 'dark')

        for char in characters:
            card = CharacterCard(char, self.image_loader, self.sound_manager, parent=self.grid_widget)
            card.update_theme(is_dark)
            
            card.install_clicked.connect(self.install_clicked.emit)
            card.delete_clicked.connect(self.delete_clicked.emit)
            card.card_clicked.connect(self.character_clicked.emit)
            # Handle Favorites
            card.fav_clicked.connect(self.on_fav_toggled)
            card.selection_toggled.connect(self.on_selection_toggled)
            
            if self.config_manager.is_favorite(char.name):
                card.set_favorite(True)
                
            # Check Installed Status
            is_installed = False
            if char.download_url and char.download_url in self.installed_identifiers:
                is_installed = True
            elif char.name:
                key = f"{char.name.lower()}_{char.author.lower() if char.author else ''}"
                if key in self.installed_identifiers:
                    is_installed = True
            
            if is_installed or char.status == 'installed':
                char.status = 'installed'
                card.mark_installed()

            # Restore selection
            # Use unique ID if possible (download_url or name+author)
            uid = char.download_url or f"{char.name}_{char.author}"
            if uid in self.selected_characters:
                card.set_selected(True)

            card.setVisible(False)
            self.flow_layout.addWidget(card)
            self.character_widgets.append(card)
            
            card.animate_in(delay)
            delay += AnimConfig.STAGGER_DELAY

    def on_selection_toggled(self, character, is_selected):
        uid = character.download_url or f"{character.name}_{character.author}"
        if is_selected:
            self.selected_characters.add(uid)
        else:
            self.selected_characters.discard(uid)
            
        count = len(self.selected_characters)
        if count > 0:
            self.btn_bulk_install.setText(f"{self.tr('install')} ({count})")
            self.btn_bulk_install.show()
        else:
            self.btn_bulk_install.hide()

    def install_selected(self):
        # We need to find the character objects corresponding to the IDs
        # The IDs are in self.selected_characters
        to_install = []
        for char in self.all_characters:
             uid = char.download_url or f"{char.name}_{char.author}"
             if uid in self.selected_characters:
                 # Check if already installed
                 if char.status == 'installed':
                     continue
                 to_install.append(char)
        
        if not to_install: 
            count_total = len(self.selected_characters)
            if count_total > 0:
                 self.toast_requested.emit("Info", "Selected characters are already installed.")
            return
        
        self.toast_requested.emit("Bulk Install", f"Starting installation of {len(to_install)} characters...")
        
        # Trigger installs with slight delay to avoid freezing UI
        delay = 0
        for char in to_install:
            QTimer.singleShot(delay, lambda c=char: self.install_clicked.emit(c))
            delay += 500
            
        # Clear selection after starting
        for widget in self.character_widgets:
             if hasattr(widget, 'set_selected'):
                 widget.set_selected(False)
        self.selected_characters.clear()
        self.btn_bulk_install.hide()

    def on_fav_toggled(self, character, is_fav):
        if is_fav:
            self.config_manager.add_favorite(character.name)
        else:
            self.config_manager.remove_favorite(character.name)
        self.config_manager.save_config()

    def sync_all_characters(self):
        if getattr(self, 'sync_active', False):
             self.stop_sync_flag = True
             self.toast_requested.emit("Sync", "Stopping synchronization...")
             return
             
        if self.is_loading: return
        self.is_loading = True
        self.sync_active = True
        self.stop_sync_flag = False
        
        self.status_updated.emit(self.tr("sync_start"))
        self.btn_reload.setEnabled(False)
        self.toast_requested.emit("Sync_start", self.tr("sync_downloading"))
        
        self.show_skeletons()
        
        worker = SyncAllWorker(self.scraper, stop_check=lambda: self.stop_sync_flag)
        worker.signals.result.connect(self.on_sync_finished)
        worker.signals.error.connect(self.on_load_error)
        worker.signals.progress.connect(self.status_updated.emit)
        self.threadpool.start(worker)

    def on_sync_finished(self, characters):
        self.is_loading = False
        self.sync_active = False
        self.fully_synced = True
        self.status_updated.emit(self.tr("ready"))
        self.btn_reload.setEnabled(True)
        
        self.all_characters = characters

        self.sort_online_characters(self.sort_combo.currentIndex())
        
        if characters:
             msg = self.tr("sync_cancelled") if self.stop_sync_flag else self.tr("sync_success", count=len(characters))
             self.toast_requested.emit("Success", msg)
        
        self.sync_finished.emit()

    def on_sort_activated(self, index):
        # Specific logic for Date (index 1)
        if index == 1:
            if self.last_sort_index == 1:
                # Toggle
                self.date_reverse = not self.date_reverse
            else:
                # Reset to default (New-Old)
                self.date_reverse = False
            
            # Update text
            new_text = self.tr("sort_date_old") if self.date_reverse else self.tr("sort_date_new")
            self.sort_combo.setItemText(1, new_text)
        else:
            # Reset date state if switching away? Optional, but good for consistency.
            self.date_reverse = False
            self.sort_combo.setItemText(1, self.tr("sort_date_new"))

        self.last_sort_index = index
        self.sort_online_characters(index)

    def sort_online_characters(self, index):
        # Check if full sync needed
        if not self.fully_synced:
             if self.is_loading: return
             self.sync_all_characters()
             return

        if not self.all_characters: return

        self.show_skeletons()
        QTimer.singleShot(500, lambda: self._perform_local_sort(index))

    def _perform_local_sort(self, index):
        if not self.all_characters: return
        
        if index == 0: # Name A-Z
            self.all_characters.sort(key=lambda x: x.name.lower())
        elif index == 1: # Date
             # If date_reverse is True -> Old-New (Ascending)
             # If date_reverse is False -> New-Old (Descending)
             self.all_characters.sort(key=lambda x: x.created_at, reverse=not self.date_reverse)
        elif index == 2: # Most Downloaded
             self.all_characters.sort(key=lambda x: x.downloads, reverse=True)
        elif index == 3: # Most Liked
             self.all_characters.sort(key=lambda x: x.likes, reverse=True)

        self.update_display_list()

    def update_display_list(self):
        candidates = self.all_characters
        
        # Search Filter
        text = self.search_input.text().strip().lower()
        if text:
            candidates = [c for c in candidates if text in c.name.lower() or text in c.author.lower()]
            
        # Fav Filter
        if self.btn_filter_fav.isChecked():
            candidates = [c for c in candidates if self.config_manager.is_favorite(c.name)]


            
        self.display_candidates = candidates
        self.current_page = 1
        
        first_batch = self.display_candidates[:self.PAGE_SIZE]
        self.populate_grid(first_batch, clear=True)
        
        if len(self.display_candidates) > self.PAGE_SIZE:
            self.btn_load_more.show()
            self.btn_load_more.setText(self.tr("load_more"))
            self.btn_load_more.setEnabled(True)
        else:
            self.btn_load_more.hide()
            
        self.status_updated.emit(self.tr("ready") if self.display_candidates else self.tr("no_chars_web"))

    def on_search_text_changed(self, text):
        self.search_timer.start()

    def perform_search(self):
        self.search_timer.stop()
        
        # If fully synced, we just filter locally
        if self.fully_synced:
            self.update_display_list()
        else:
            # Trigger a fresh load from the scraper
            # load_characters will pick up the text from search_input
            self.load_characters()

    def show_skeletons(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        self.character_widgets = []
        for _ in range(12):
            skeleton = SkeletonCard()
            skeleton.setFixedSize(200, 300) # Optional hint
            self.flow_layout.addWidget(skeleton)

    def check_scroll_bottom(self):
        if not self.btn_load_more.isVisible(): return
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - 400:
            if not self.is_loading and self.btn_load_more.isEnabled():
                self.load_more_characters()

    def set_search(self, text):
        self.search_input.setText(text)
        self.search_input.setFocus()

    def update_installed_registry(self, installed_chars):
        """
        Updates the internal set of installed characters based on the InstalledTab's list.
        Then updates the UI of any currently displayed online characters.
        """
        self.installed_identifiers = set()
        for char in installed_chars:
            # 1. Download URL (best)
            if char.download_url:
                self.installed_identifiers.add(char.download_url)
            
            # 2. Name + Author (fallback)
            if char.name:
                key = f"{char.name.lower()}_{char.author.lower() if char.author else ''}"
                self.installed_identifiers.add(key)
        
        # Refresh current view
        self.markup_installed_characters()
        
    def markup_installed_characters(self):
        """Checks all displayed cards and marks them as installed if they match registry."""
        for widget in self.character_widgets:
            if not hasattr(widget, 'character'): continue
            
            c = widget.character
            is_installed = False
            
            # Check ID
            if c.download_url and c.download_url in self.installed_identifiers:
                is_installed = True
            elif c.name:
                key = f"{c.name.lower()}_{c.author.lower() if c.author else ''}"
                if key in self.installed_identifiers:
                    is_installed = True
                    
            if is_installed:
                # Update model and UI
                c.status = "installed"
                widget.mark_installed()
                # Also ensure selection handles it if needed (but mark_installed usually disables primary action)
                # If we want to prevent selection? 
                # widget.set_selected(False) ? 
                # Let's leave selection logic as is (user might want to select for other reasons, but install is blocked)

    def on_character_installed(self, character):
        for widget in self.character_widgets:
            if hasattr(widget, 'character') and widget.character.name == character.name:
                widget.mark_installed()
                
    def on_character_uninstalled(self, character):
        for widget in self.character_widgets:
            if hasattr(widget, 'character') and widget.character.name == character.name:
                # Reset card state
                # Reset card state
                widget.btn_install.setText(self.tr("install"))
                widget.btn_install.setEnabled(True)
                widget.btn_install.setStyleSheet("background-color: #0078d4; color: white;")
                widget.btn_delete.hide()
                
                # Update status
                widget.character.status = "not_installed"
                widget.character.local_filename = None
                
                # Remove border if applied
                if hasattr(widget, 'image_label'):
                     # Re-apply theme or just clear border manually (theme manager handles color, but border is manual)
                     # Best to call update_theme again but that might be heavy? 
                     # Let's just reset the style to transparent + radius
                     widget.image_label.setStyleSheet("background-color: transparent; border-radius: 4px;")
                
    def filter_loaded_characters(self, text):
        # Helper for local filtering if needed exposed?
        # self.on_search_text_changed(text) # Already connected
        pass


