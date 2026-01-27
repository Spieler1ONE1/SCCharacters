from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QPushButton, QLabel, QInputDialog, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt
import os
import zipfile
import shutil

class ManageCollectionsDialog(QDialog):
    def __init__(self, collection_manager, game_path, parent=None):
        super().__init__(parent)
        self.collection_manager = collection_manager
        self.game_path = game_path
        self.setWindowTitle("Manage Collections")
        self.resize(400, 500)
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        
        btn_rename = QPushButton("Rename")
        btn_rename.clicked.connect(self.rename_selected)

        btn_export = QPushButton("Export Pack")
        btn_export.setToolTip("Export collection as shareable .scpack")
        btn_export.clicked.connect(self.export_selected)
        
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        btn_delete.clicked.connect(self.delete_selected)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_rename)
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def refresh_list(self):
        self.list_widget.clear()
        cols = self.collection_manager.get_all_collections()
        self.list_widget.addItems(sorted(cols))

    def rename_selected(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Collection", 
                                          f"Rename '{old_name}' to:", text=old_name)
        if ok and new_name and new_name != old_name:
            if self.collection_manager.rename_collection(old_name, new_name):
                self.refresh_list()
            else:
                QMessageBox.warning(self, "Error", "Name already exists or invalid.")

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        name = item.text()
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete collection '{name}'?\nThe characters will remain installed.",
                                   QMessageBox.Yes | QMessageBox.No)
                                   
        if reply == QMessageBox.Yes:
            self.collection_manager.delete_collection(name)
            self.refresh_list()

    def export_selected(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        col_name = item.text()
        chars = self.collection_manager.get_characters_in_collection(col_name) # Ensure this exists or use .collections[col_name]
        
        if not chars:
            QMessageBox.warning(self, "Empty", "This collection is empty.")
            return

        # Prepare Pack
        default_name = f"{col_name}_SquadronPack.scpack"
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Squadron Pack", default_name, "StarChar Pack (*.scpack)")
        
        if not save_path:
            return
            
        try:
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 1. Create Manifest
                import json
                manifest = {
                    "version": 1,
                    "type": "collection",
                    "collection_name": col_name,
                    "characters": chars,
                    "created_at": str(os.path.getmtime(self.game_path) if os.path.exists(self.game_path) else "")
                }
                zf.writestr("manifest.json", json.dumps(manifest, indent=4))
                
                # 2. Add Character Files
                added_count = 0
                for char_name in chars:
                    # Finds files by name... simplistic approach
                    # Real files are named {char_name}.chf usually
                    base_name = char_name
                    
                    # We try to match exactly or close
                    chf_path = os.path.join(self.game_path, f"{base_name}.chf")
                    json_path = os.path.join(self.game_path, f"{base_name}.json")
                    thumb_path = os.path.join(self.game_path, f"{base_name}_thumb.jpg")
                    
                    if os.path.exists(chf_path):
                        zf.write(chf_path, f"{base_name}.chf")
                        if os.path.exists(json_path):
                            zf.write(json_path, f"{base_name}.json")
                        if os.path.exists(thumb_path):
                            zf.write(thumb_path, f"{base_name}_thumb.jpg")
                        added_count += 1
                
            QMessageBox.information(self, "Export Success", f"Exported {added_count} characters to {os.path.basename(save_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
