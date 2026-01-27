from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFileDialog, QMessageBox, QCheckBox, QComboBox, QFrame, QWidget)
from PySide6.QtCore import Qt
from src.core.config_manager import ConfigManager
from src.utils.translations import translator
from src.ui.widgets import setup_localized_context_menu

class SettingsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, theme_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.setWindowTitle(self.tr("settings_title"))
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def tr(self, key, **kwargs):
        return translator.get(key, **kwargs)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Game Path Section
        path_layout = QVBoxLayout()
        path_label = QLabel(self.tr("game_path_label"))
        path_layout.addWidget(path_label)
        
        input_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(self.config_manager.get_game_path())
        setup_localized_context_menu(self.path_input)
        input_layout.addWidget(self.path_input)
        
        btn_browse = QPushButton(self.tr("browse"))
        btn_browse.clicked.connect(self.browse_path)
        input_layout.addWidget(btn_browse)
        
        path_layout.addLayout(input_layout)
        
        # Auto-detect button
        btn_detect = QPushButton(self.tr("auto_detect"))
        btn_detect.clicked.connect(self.auto_detect)
        path_layout.addWidget(btn_detect)
        
        layout.addLayout(path_layout)

        # --- Theme Section ---
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Visual Theme:")
        self.theme_combo = QComboBox()
        
        # Options
        self.themes = [
            ("BioMetrics Default (Dark)", "default"),
            ("Drake Interplanetary (Industrial)", "drake"),
            ("Origin Jumpworks (Luxury)", "origin"),
            ("Aegis Dynamics (Military)", "aegis"),
            ("Clean Light", "light"),
            ("Auto (System)", "auto")
        ]
        
        current_theme = self.config_manager.config.get("theme", "auto")
        if current_theme == "dark": current_theme = "default" # normalizing
        
        for name, key in self.themes:
            self.theme_combo.addItem(name, key)
            
        # Set current selection
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        else:
             self.theme_combo.setCurrentIndex(self.theme_combo.findData("auto"))
             
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # Custom PTU Path Section
        ptu_layout = QVBoxLayout()
        ptu_label = QLabel("Custom PTU Path (Optional):")
        ptu_layout.addWidget(ptu_label)
        
        ptu_input_layout = QHBoxLayout()
        self.ptu_input = QLineEdit()
        current_ptu = self.config_manager.get_custom_ptu_path()
        self.ptu_input.setText(current_ptu if current_ptu else "")
        self.ptu_input.setPlaceholderText("Full path to CustomCharacters in PTU (optional)")
        setup_localized_context_menu(self.ptu_input)
        
        ptu_input_layout.addWidget(self.ptu_input)
        
        btn_browse_ptu = QPushButton(self.tr("browse"))
        btn_browse_ptu.clicked.connect(self.browse_ptu_path)
        ptu_input_layout.addWidget(btn_browse_ptu)
        
        ptu_layout.addLayout(ptu_input_layout)
        layout.addLayout(ptu_layout)
        
        # --- Stream Integration Section ---
        stream_group = QFrame()
        stream_group.setFrameShape(QFrame.StyledPanel)
        stream_layout = QVBoxLayout(stream_group)
        
        self.chk_stream_enabled = QCheckBox("Enable Stream Integration (OBS Kit)")
        self.chk_stream_enabled.setChecked(self.config_manager.get_obs_integration_enabled())
        self.chk_stream_enabled.stateChanged.connect(self.toggle_stream_path)
        stream_layout.addWidget(self.chk_stream_enabled)
        
        self.stream_path_container = QWidget()
        self.stream_path_layout = QVBoxLayout(self.stream_path_container)
        self.stream_path_layout.setContentsMargins(0, 5, 0, 0)
        
        lbl_stream = QLabel("Output Folder for Overlays (.txt/.jpg):")
        self.stream_path_layout.addWidget(lbl_stream)
        
        stream_input_box = QHBoxLayout()
        self.stream_path_input = QLineEdit()
        self.stream_path_input.setText(self.config_manager.get_stream_output_path())
        setup_localized_context_menu(self.stream_path_input)
        
        btn_browse_stream = QPushButton(self.tr("browse"))
        btn_browse_stream.clicked.connect(self.browse_stream_path)
        
        stream_input_box.addWidget(self.stream_path_input)
        stream_input_box.addWidget(btn_browse_stream)
        
        self.stream_path_layout.addLayout(stream_input_box)
        stream_layout.addWidget(self.stream_path_container)
        
        layout.addWidget(stream_group)
        self.toggle_stream_path(self.chk_stream_enabled.checkState())
        
        # --- Automation Section ---
        auto_group = QFrame()
        auto_group.setFrameShape(QFrame.StyledPanel)
        auto_layout = QVBoxLayout(auto_group)
        
        auto_label = QLabel("Automation Features")
        auto_label.setStyleSheet("font-weight: bold;")
        auto_layout.addWidget(auto_label)
        
        # Auto Backup
        self.chk_auto_backup = QCheckBox("Enable Smart Auto-Backup (On Game Exit)")
        self.chk_auto_backup.setChecked(self.config_manager.config.get("auto_backup_enabled", True))
        auto_layout.addWidget(self.chk_auto_backup)
        
        # Cloud Sync
        self.chk_cloud_sync = QCheckBox("Enable Cloud Sync (Copy to External Folder)")
        self.chk_cloud_sync.setChecked(self.config_manager.config.get("cloud_sync_enabled", False))
        self.chk_cloud_sync.stateChanged.connect(self.toggle_cloud_path)
        auto_layout.addWidget(self.chk_cloud_sync)
        
        self.cloud_path_container = QWidget()
        self.cloud_path_layout = QVBoxLayout(self.cloud_path_container)
        self.cloud_path_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_cloud = QLabel("Cloud Folder (Dropbox/OneDrive):")
        self.cloud_path_layout.addWidget(lbl_cloud)
        
        cloud_input_box = QHBoxLayout()
        self.cloud_path_input = QLineEdit()
        self.cloud_path_input.setText(self.config_manager.config.get("cloud_sync_path", ""))
        setup_localized_context_menu(self.cloud_path_input)
        
        btn_browse_cloud = QPushButton(self.tr("browse"))
        btn_browse_cloud.clicked.connect(self.browse_cloud_path)
        
        cloud_input_box.addWidget(self.cloud_path_input)
        cloud_input_box.addWidget(btn_browse_cloud)
        
        self.cloud_path_layout.addLayout(cloud_input_box)
        auto_layout.addWidget(self.cloud_path_container)
        
        layout.addWidget(auto_group)
        self.toggle_cloud_path(self.chk_cloud_sync.checkState())
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(self.tr("save"))
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton(self.tr("cancel"))
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
    def browse_path(self):
        current_path = self.path_input.text()
        path = QFileDialog.getExistingDirectory(self, self.tr("browse"), current_path)
        if path:
            self.path_input.setText(path)
            
    def browse_ptu_path(self):
        current = self.ptu_input.text()
        path = QFileDialog.getExistingDirectory(self, "Select PTU Folder", current)
        if path:
            self.ptu_input.setText(path)

    def browse_stream_path(self):
        current = self.stream_path_input.text()
        path = QFileDialog.getExistingDirectory(self, "Select Stream Output Folder", current)
        if path:
            self.stream_path_input.setText(path)

    def toggle_stream_path(self, state):
        self.stream_path_container.setVisible(bool(state))

    def toggle_cloud_path(self, state):
        self.cloud_path_container.setVisible(bool(state))
        
    def browse_cloud_path(self):
        current = self.cloud_path_input.text()
        path = QFileDialog.getExistingDirectory(self, "Select Cloud Service Folder", current)
        if path:
            self.cloud_path_input.setText(path)

    def auto_detect(self):
        path = self.config_manager.auto_detect_path()
        if path:
            self.path_input.setText(path)
            QMessageBox.information(self, self.tr("path_detected_title"), self.tr("path_detected", path=path))
        else:
            QMessageBox.warning(self, self.tr("error"), self.tr("path_not_found"))
            
    def save_settings(self):
        new_path = self.path_input.text()
        ptu_path = self.ptu_input.text()
        
        # Save custom PTU path (no strict validation, just save)
        self.config_manager.set_custom_ptu_path(ptu_path)

        # Save Theme
        selected_theme = self.theme_combo.currentData()
        # Update via manager (also saves)
        self.theme_manager.set_theme_mode(selected_theme)

        # Save Stream Settings
        self.config_manager.set_obs_integration_enabled(self.chk_stream_enabled.isChecked())
        self.config_manager.set_stream_output_path(self.stream_path_input.text())
        
        # Save Automation Settings
        self.config_manager.config["auto_backup_enabled"] = self.chk_auto_backup.isChecked()
        self.config_manager.config["cloud_sync_enabled"] = self.chk_cloud_sync.isChecked()
        self.config_manager.config["cloud_sync_path"] = self.cloud_path_input.text()
        self.config_manager.save_config()

        # Validate
        # We temporarily set it to validate
        old_path = self.config_manager.get_game_path()
        self.config_manager.set_game_path(new_path)
        
        if self.config_manager.validate_path():
            self.accept()
        else:
            # Revert
            self.config_manager.set_game_path(old_path)
            QMessageBox.warning(self, self.tr("invalid_path_title"), 
                              self.tr("invalid_path_msg"))
