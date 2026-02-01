from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QComboBox, QPushButton, QMessageBox, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal, QThreadPool
from src.ui.widgets.auto_scroll_area import AutoScrollArea
from src.ui.widgets.flow_layout import FlowLayout
from src.utils.translations import translator
from src.core.workers import InstalledCharactersWorker
from src.ui.widgets import CharacterCard
from src.ui.anim_config import AnimConfig
import os
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtCore import QUrl, QTimer
from src.ui.widgets.skeleton import SkeletonCard

class InstalledTab(QWidget):
    custom_context_requested = Signal(object, object) # Character, global_pos
    filter_collection_requested = Signal(str, str) # collection_name, character_name_filter (future use)
    character_clicked = Signal(object) # passes Character
    delete_clicked = Signal(object)    # passes Character
    bulk_delete_clicked = Signal(list) # passes list[Character] NEW
    bulk_add_collection_clicked = Signal(list, str) # chars, collection_name (NEW)
    model_updated = Signal(list)       # passes list[Character] NEW
    deploy_loadout_clicked = Signal(str) # collection_name (NEW)

    def __init__(self, config_manager, character_service, image_loader, sound_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.character_service = character_service
        self.image_loader = image_loader
        self.sound_manager = sound_manager
        self.character_widgets = []
        self.selected_characters = set() # NEW
        self.collection_manager = None # Will be set by MainWindow
        self.current_collection_filter = None
        
        # Debounce Timer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # 300ms delay
        self.search_timer.timeout.connect(self.perform_filter)

        self.setup_ui()
        
    def tr(self, key, **kwargs):
        # Override tr to use translator
        return translator.get(key, **kwargs)

    def setup_ui(self):
        self.setObjectName("InstalledTab")
        layout = QVBoxLayout(self)
        
        # --- Toolbar ---
        toolbar_layout = QHBoxLayout()
        
        # Search
        self.search_installed = QLineEdit()
        self.search_installed.setPlaceholderText(self.tr("search_installed"))
        self.search_installed.setMinimumHeight(40)
        self.search_installed.setClearButtonEnabled(True)
        self.search_installed.textChanged.connect(self.on_search_text_changed)
        from src.ui.widgets import setup_localized_context_menu
        setup_localized_context_menu(self.search_installed)
        toolbar_layout.addWidget(self.search_installed)
        
        # Sort
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            self.tr("sort_name_az"), 
            self.tr("sort_name_za"), 
            self.tr("sort_date_new"), 
            self.tr("sort_date_old")
        ])
        self.sort_combo.setMinimumHeight(40)
        self.sort_combo.currentIndexChanged.connect(self.sort_installed_characters)
        toolbar_layout.addWidget(self.sort_combo)
        
        # Collection Filter
        self.filter_collection_combo = QComboBox()
        self.filter_collection_combo.addItem(self.tr("all_collections")) # default
        self.filter_collection_combo.setMinimumHeight(40)
        self.filter_collection_combo.currentIndexChanged.connect(self.on_collection_filter_changed)
        self.filter_collection_combo.currentIndexChanged.connect(self.on_collection_filter_changed)
        toolbar_layout.addWidget(self.filter_collection_combo)
        
        # Manage Collections
        self.btn_manage_cols = QPushButton("⚙️")
        self.btn_manage_cols.setFixedWidth(40)
        self.btn_manage_cols.setToolTip("Manage Collections")
        self.btn_manage_cols.clicked.connect(self.open_manage_collections)
        toolbar_layout.addWidget(self.btn_manage_cols)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(line)
        
        # Backups
        btn_backup = QPushButton(f"💾 {self.tr('backup_btn')}")
        btn_backup.setToolTip("Full Backup")
        btn_backup.clicked.connect(self.request_backup)
        toolbar_layout.addWidget(btn_backup)
        
        btn_restore = QPushButton(f"♻️ {self.tr('restore_btn')}")
        btn_restore.setToolTip("Restore from Zip")
        btn_restore.clicked.connect(self.request_restore)
        toolbar_layout.addWidget(btn_restore)
        
        # Separator 2
        line2 = QFrame()
        line2.setFrameShape(QFrame.VLine)
        line2.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(line2)

        # Open Folder
        self.btn_open_folder = QPushButton(self.tr("open_folder"))
        self.btn_open_folder.setMinimumHeight(40)
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self.open_install_folder)
        toolbar_layout.addWidget(self.btn_open_folder)
        
        # Refresh
        self.btn_refresh_installed = QPushButton(self.tr("refresh_list"))
        self.btn_refresh_installed.setMinimumHeight(40)
        self.btn_refresh_installed.setCursor(Qt.PointingHandCursor)
        self.btn_refresh_installed.clicked.connect(self.load_characters)
        
        # Bulk Uninstall
        self.btn_bulk_uninstall = QPushButton(self.tr("uninstall_selected"))
        self.btn_bulk_uninstall.setMinimumHeight(40)
        self.btn_bulk_uninstall.setCursor(Qt.PointingHandCursor)
        self.btn_bulk_uninstall.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 0 15px;")
        self.btn_bulk_uninstall.hide()
        self.btn_bulk_uninstall.clicked.connect(self.uninstall_selected)
        
        toolbar_layout.addWidget(self.btn_refresh_installed)
        toolbar_layout.addWidget(self.btn_refresh_installed)
        toolbar_layout.addWidget(self.btn_bulk_uninstall)
        
        # Loadout / Deploy Button (Only visible if a collection is selected)
        self.btn_deploy_loadout = QPushButton("🚀 Deploy Loadout")
        self.btn_deploy_loadout.setToolTip("Equip only characters from this collection")
        self.btn_deploy_loadout.setStyleSheet("background-color: #6366f1; color: white; font-weight: bold;")
        self.btn_deploy_loadout.hide()
        self.btn_deploy_loadout.clicked.connect(self.request_deploy_loadout)
        toolbar_layout.addWidget(self.btn_deploy_loadout)
        
        # Bulk Action Menu Button (Replaces simple bulk uninstall)
        self.btn_bulk_actions = QPushButton("⚡ Actions")
        self.btn_bulk_actions.hide()
        self.btn_bulk_actions.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold;")
        
        # Setup menu for bulk actions
        from PySide6.QtWidgets import QMenu
        self.bulk_menu = QMenu(self)
        self.btn_bulk_actions.setMenu(self.bulk_menu)
        
        # Will handle logic in update method
        
        toolbar_layout.addWidget(self.btn_bulk_actions)

        
        layout.addLayout(toolbar_layout)
        
        # --- Content Area ---
        scroll_area = AutoScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("InstalledContentWidget")
        self.flow_layout = FlowLayout(self.content_widget, margin=0, spacing=15)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)

    def load_characters(self):
        # Async load
        
        # Show Skeletons first
        self._show_skeletons()
        
        path = self.config_manager.get_game_path()
        try:
            worker = InstalledCharactersWorker(path)
            worker.signals.result.connect(self.on_characters_loaded)
            worker.signals.error.connect(lambda e: print(f"Error loading installed: {e}"))
            QThreadPool.globalInstance().start(worker)
        except Exception as e:
            print(f"Failed to start installed worker: {e}")

    def _show_skeletons(self):
        # Clear existing
        self._clear_layout()
        
        # Add 6 skeletons
        for _ in range(6):
            skel = SkeletonCard(self.content_widget)
            self.flow_layout.addWidget(skel)

    def on_characters_loaded(self, characters):
        # Clear skeletons
        self._clear_layout()
        self.character_widgets = []
        
        # Also remove any non-widget items just in case
        
        delay = 0
        
        if not characters:
            lbl = QLabel(self.tr("no_chars_local"))
            lbl.setStyleSheet("color: #888; font-size: 14px; margin: 20px;")
            self.flow_layout.addWidget(lbl)
            return

        for char in characters:
            card = CharacterCard(char, self.image_loader, self.sound_manager, parent=self.content_widget)
            card.mark_installed()
            card.delete_clicked.connect(self.delete_clicked.emit)
            card.card_clicked.connect(self.character_clicked.emit)
            card.thumbnail_dropped.connect(self.on_thumbnail_dropped)
            card.selection_toggled.connect(self.on_selection_toggled)

            # Restore selection
            # Local chars ID is local_filename usually unique, or name
            uid = char.local_filename or char.name
            if uid in self.selected_characters:
                card.set_selected(True)
            
            # Hide favorites for local
            if hasattr(card, 'btn_fav'):
                card.btn_fav.hide()

            card.setContextMenuPolicy(Qt.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, c=char: self.custom_context_requested.emit(c, card.mapToGlobal(pos)))
            
            # Hide initially until animation
            card.setVisible(False)
            
            self.flow_layout.addWidget(card)
            self.character_widgets.append(card)
            
            # Animate
            card.animate_in(delay)
            delay += AnimConfig.STAGGER_DELAY
            
        self.model_updated.emit(characters)

    def on_selection_toggled(self, character, is_selected):
        uid = character.local_filename or character.name
        if is_selected:
            self.selected_characters.add(uid)
        else:
            self.selected_characters.discard(uid)
            
        count = len(self.selected_characters)
        if count > 0:
            self.btn_bulk_uninstall.hide() # Hide the old button
            self.btn_bulk_actions.setText(f"⚡ Selected ({count})")
            self.btn_bulk_actions.show()
            self.update_bulk_menu()
        else:
            self.btn_bulk_uninstall.hide()
            self.btn_bulk_actions.hide()

    def update_bulk_menu(self):
        self.bulk_menu.clear()
        
        # Uninstall
        act_un = self.bulk_menu.addAction(f"🗑️ Uninstall ({len(self.selected_characters)})")
        act_un.triggered.connect(self.uninstall_selected)
        
        self.bulk_menu.addSeparator()
        
        # Add to Collection
        cols_menu = self.bulk_menu.addMenu("📂 Add to Collection...")
        if self.collection_manager:
            for col in self.collection_manager.get_all_collections():
                act = cols_menu.addAction(col)
                # Capture col with default arg
                act.triggered.connect(lambda c=False, name=col: self.bulk_add_to_collection(name))
                
    def bulk_add_to_collection(self, collection_name):
        # Identify characters
        target_chars = []
        for w in self.character_widgets:
             uid = w.character.local_filename or w.character.name
             if uid in self.selected_characters:
                 target_chars.append(w.character)
                 
        if target_chars:
            self.bulk_add_collection_clicked.emit(target_chars, collection_name)
            self.selected_characters.clear()
            self.btn_bulk_actions.hide()
            # Unselect all widgets
            for w in self.character_widgets: w.set_selected(False)



    def uninstall_selected(self):
        # Gather chars
        to_remove = []
        for w in self.character_widgets:
             c = w.character
             uid = c.local_filename or c.name
             if uid in self.selected_characters:
                 to_remove.append(c)
                 
        if not to_remove: return
        
        reply = QMessageBox.question(self, self.tr("confirm_uninstall"), 
                                     self.tr('confirm_uninstall_msg_bulk', count=len(to_remove)),
                                     QMessageBox.Yes | QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            # Emit batch for MainWindow to handle without extra confirmations
            self.bulk_delete_clicked.emit(to_remove)
            
            # Clear UI Selection
            self.selected_characters.clear()
            self.btn_bulk_uninstall.hide()

    def on_thumbnail_dropped(self, character, file_path):
        if self.character_service.save_custom_thumbnail(character, file_path):
            # Refresh this character's image
            # Find the card
            for widget in self.character_widgets:
                if widget.character == character:
                     # Force reload
                     # We need to update the character model's image_url or similar?
                     # Technically local characters rely on scraping or local path checks.
                     # If we just saved it, checking 'local_filename' again might not be enough if logic is in worker.
                     # But ImageLoader typically caches.
                     # Let's try to reload the image by constructing a file url?
                     path = self.character_service.get_game_path()
                     base_name = os.path.splitext(character.local_filename)[0]
                     thumb_path = path / f"{base_name}_thumb.jpg"
                     
                     if os.path.exists(thumb_path):
                         # Bust cache by appending time?
                         pixmap = QPixmap(str(thumb_path))
                         widget.set_image(pixmap)
                         # Also update internal model if needed
                         widget.show_toast = getattr(self.parent(), 'show_toast', None) # Hacky access to toast?
                         # Better emit toast signal
            
            # Ideally emit success toast
            pass
            
        # Apply current sort
        self.sort_installed_characters(self.sort_combo.currentIndex())
    
    def set_collection_manager(self, manager):
        self.collection_manager = manager
        self.refresh_collections_ui()

    def refresh_collections_ui(self):
        if not self.collection_manager: return
        
        current = self.filter_collection_combo.currentText()
        self.filter_collection_combo.blockSignals(True)
        self.filter_collection_combo.clear()
        
        self.filter_collection_combo.addItem(self.tr("all_collections"))
        for col in self.collection_manager.get_all_collections():
            self.filter_collection_combo.addItem(col)
            
        # Restore selection if still exists
        index = self.filter_collection_combo.findText(current)
        if index >= 0:
            self.filter_collection_combo.setCurrentIndex(index)
        else:
             self.filter_collection_combo.setCurrentIndex(0)
             self.current_collection_filter = None
             
        self.filter_collection_combo.blockSignals(False)
        # Apply filter again just in case changed
        self.filter_installed_characters(self.search_installed.text())

    def on_collection_filter_changed(self, index):
        if index <= 0:
            self.current_collection_filter = None
            self.btn_deploy_loadout.hide()
        else:
            self.current_collection_filter = self.filter_collection_combo.currentText()
            # Show Deploy button for "Loadouts" feature
            self.btn_deploy_loadout.show()
            self.btn_deploy_loadout.setText(f"🚀 Deploy '{self.current_collection_filter}'")
            
        self.filter_installed_characters(self.search_installed.text())

    def request_deploy_loadout(self):
        if self.current_collection_filter:
            reply = QMessageBox.question(self, "Deploy Loadout", 
                                       f"This will move all OTHER characters to storage and only keep '{self.current_collection_filter}' in the game folder. Continue?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.deploy_loadout_clicked.emit(self.current_collection_filter)

    def filter_by_collection(self, col_name):
        pass # MainWindow logic calls filter_installed... this is just signal routing usually
    

    def sort_installed_characters(self, index):
        if not self.character_widgets: return
            
        def sort_key(widget):
            char = widget.character
            if index == 0: # Name A-Z
                return char.name.lower()
            elif index == 1: # Name Z-A
                return char.name.lower()
            elif index == 2: # Date New
                return char.install_date or 0.0
            elif index == 3: # Date Old
                return char.install_date or 0.0
            return ""

        reverse = (index == 1 or index == 2)
        
        sorted_widgets = sorted(self.character_widgets, key=sort_key, reverse=reverse)
        
        # Re-add to layout in order
        for w in sorted_widgets:
            self.flow_layout.removeWidget(w)
            self.flow_layout.addWidget(w)
            
    def filter_installed_characters(self, text):
        text = text.lower().strip()
        
        # Get active collection list if any
        allowed_names = None
        if self.current_collection_filter and self.collection_manager:
             allowed_names = self.collection_manager.collections.get(self.current_collection_filter, [])
        
        for widget in self.character_widgets:
            char_name = widget.character.name.lower()
            
            # Text match
            match_text = (text in char_name)
            
            # Collection match
            match_col = True
            if allowed_names is not None:
                match_col = (widget.character.name in allowed_names)
                
            visible = match_text and match_col
            widget.setVisible(visible)

    def on_search_text_changed(self, text):
        self.search_timer.start()

    def perform_filter(self):
        text = self.search_installed.text()
        self.filter_installed_characters(text)

    def _clear_layout(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)


    def open_install_folder(self):
        path = self.config_manager.get_game_path()
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, self.tr("error"), f"{self.tr('error_path_not_found')}: {path}")

    def open_manage_collections(self):
        if not self.collection_manager: return
        from src.ui.dialogs.manage_collections import ManageCollectionsDialog
        path = self.config_manager.get_game_path()
        dlg = ManageCollectionsDialog(self.collection_manager, path, self)
        dlg.exec()
        self.refresh_collections_ui()

    def request_backup(self):
        # Forward to parent (MainWindow) logic if possible, or implement direct call
        # MainWindow has export_backup
        mw = self.window()
        if hasattr(mw, 'export_backup'):
            mw.export_backup()
        else:
            print("MainWindow backup method not found")

    def request_restore(self):
        mw = self.window()
        if hasattr(mw, 'import_backup'):
            mw.import_backup()
        else:
             print("MainWindow restore method not found")

    def update_theme(self, is_dark):
        for widget in self.character_widgets:
            widget.update_theme(is_dark)
