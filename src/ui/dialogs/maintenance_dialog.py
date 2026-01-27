from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QProgressBar, QTextEdit, QMessageBox, QFrame, QScrollArea, QWidget)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
import hashlib
import os
import json
from src.core.character_service import CharacterService
from src.utils.image_loader import ImageLoader
from src.utils.translations import translator

class MaintenanceDialog(QDialog):
    def __init__(self, character_service: CharacterService, image_loader: ImageLoader, parent=None):
        super().__init__(parent)
        self.character_service = character_service
        self.image_loader = image_loader
        self.setWindowTitle(translator.get("maintenance_tools"))
        self.resize(500, 450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        lbl_header = QLabel("System Maintenance")
        lbl_header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_header)
        
        # --- Image Cache Section ---
        cache_frame = QFrame()
        cache_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 6px;")
        cache_layout = QHBoxLayout(cache_frame)
        
        lbl_cache = QLabel("<b>Image Cache</b><br>Clear temporary downloaded images.<br>Fixes display issues.")
        lbl_cache.setStyleSheet("border: none; background: transparent;")
        
        btn_clear_cache = QPushButton("Clear Cache")
        btn_clear_cache.setCursor(Qt.PointingHandCursor)
        btn_clear_cache.clicked.connect(self.clear_cache)
        
        cache_layout.addWidget(lbl_cache)
        cache_layout.addStretch()
        cache_layout.addWidget(btn_clear_cache)
        
        layout.addWidget(cache_frame)
        
        # --- Library Repair Section ---
        lib_frame = QFrame()
        lib_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 6px;")
        lib_layout = QHBoxLayout(lib_frame)
        
        lbl_lib = QLabel("<b>Library Repair</b><br>Remove ghost entries and fix missing metadata.<br>Use if installation list looks wrong.")
        lbl_lib.setStyleSheet("border: none; background: transparent;")
        
        btn_repair = QPushButton("Repair Library")
        btn_repair.setCursor(Qt.PointingHandCursor)
        btn_repair.clicked.connect(self.repair_library)
        
        lib_layout.addWidget(lbl_lib)
        lib_layout.addStretch()
        lib_layout.addWidget(btn_repair)
        
        layout.addWidget(lib_frame)

        # --- Integrity Check Section (New) ---
        integrity_frame = QFrame()
        integrity_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 6px;")
        int_layout = QHBoxLayout(integrity_frame)
        
        lbl_int = QLabel("<b>Integrity Check</b><br>Validate file structure of all characters.<br>Detects corrupted downloads.")
        lbl_int.setStyleSheet("border: none; background: transparent;")
        
        btn_int = QPushButton("Validate Files")
        btn_int.setCursor(Qt.PointingHandCursor)
        btn_int.clicked.connect(self.validate_integrity)
        
        int_layout.addWidget(lbl_int)
        int_layout.addStretch()
        int_layout.addWidget(btn_int)
        
        layout.addWidget(integrity_frame)

        # --- Duplicate Check Section (New - DNA Scanner) ---
        dup_frame = QFrame()
        dup_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 6px;")
        dup_layout = QHBoxLayout(dup_frame)
        
        lbl_dup = QLabel("<b>DNA Scanner</b><br>Analyze file hashes to find exact duplicates<br>with different names.")
        lbl_dup.setStyleSheet("border: none; background: transparent;")
        
        btn_dup = QPushButton("Scan DNA")
        btn_dup.setCursor(Qt.PointingHandCursor)
        btn_dup.clicked.connect(self.check_duplicates)
        
        dup_layout.addWidget(lbl_dup)
        dup_layout.addStretch()
        dup_layout.addWidget(btn_dup)
        
        layout.addWidget(dup_frame)
        
        # --- Log Area ---
        lbl_log = QLabel("Activity Log:")
        layout.addWidget(lbl_log)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Close
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def log(self, message):
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{time_str}] {message}")

    def clear_cache(self):
        self.log("Clearing image cache...")
        try:
            self.image_loader.clear_cache()
            self.log("Success: Image cache cleared.")
            QMessageBox.information(self, "Success", "Image cache has been cleared.\nImages will be re-downloaded as needed.")
        except Exception as e:
            self.log(f"Error: {e}")

    def repair_library(self):
        self.log("Starting library repair check...")
        try:
            result = self.character_service.repair_library()
            
            removed = result.get('orphans_removed', 0)
            created = result.get('metadata_created', 0)
            
            self.log(f"Scan complete.")
            self.log(f"- Orphaned metadata removed: {removed}")
            self.log(f"- Recovered character metadata: {created}")
            
            if removed > 0 or created > 0:
                QMessageBox.information(self, "Repair Complete", 
                                      f"Library repaired successfully.\n\nRemoved {removed} orphans.\nRecovered {created} characters.")
                # We should probably signal the main window to refresh
                parent = self.parent()
                if parent and hasattr(parent, 'load_installed_characters'):
                     parent.load_installed_characters()
            else:
                QMessageBox.information(self, "Library Healthy", "No issues found in your library.")
                
        except Exception as e:
            self.log(f"Error during repair: {e}")
            QMessageBox.critical(self, "Error", f"Repair failed: {str(e)}")

    def validate_integrity(self):
        self.log("Starting integrity validation...")
        errors = self.character_service.validate_library_integrity()
        
        self.log(f"Scan complete. Found {len(errors)} issues.")
        
        if not errors:
             QMessageBox.information(self, "Integrity Check", "All character files appear valid.")
        else:
             msg = "Found the following issues:\n\n"
             for e in errors[:10]:
                 msg += f"- {e['filename']}: {e['error']}\n"
             
             if len(errors) > 10:
                 msg += f"...and {len(errors)-10} more."
                 
             QMessageBox.warning(self, "Integrity Issues", msg)

    def check_duplicates(self):
        self.log("Starting DNA Scan (Hash Analysis)...")
        path = self.character_service.get_game_path()
        if not path or not os.path.exists(path):
            self.log("Error: Game path not found.")
            return

        files = [f for f in os.listdir(path) if f.lower().endswith('.chf')]
        self.log(f"Scanning {len(files)} files...")
        
        hashes = {}
        duplicates = []
        
        # Calculate hashes
        for f in files:
            full_path = os.path.join(path, f)
            try:
                with open(full_path, "rb") as file:
                    # Read chunks to handle potential large files, though chf are small
                    file_hash = hashlib.md5(file.read()).hexdigest()
                    
                if file_hash in hashes:
                    # Found duplicate
                    original = hashes[file_hash]
                    duplicates.append((original, f))
                    self.log(f"MATCH: '{f}' is a clone of '{original}'")
                else:
                    hashes[file_hash] = f
            except Exception as e:
                self.log(f"Error reading {f}: {e}")

        if not duplicates:
             self.log("Scan complete. No genetic duplicates found.")
             QMessageBox.information(self, "DNA Scan", "No duplicates found. Your clone army is unique.")
        else:
             self.log(f"Scan complete. Found {len(duplicates)} duplicate sets.")
             reply = QMessageBox.question(self, "Duplicates Found", 
                                        f"Found {len(duplicates)} files that are exact copies of others.\nDo you want to delete the duplicates?",
                                        QMessageBox.Yes | QMessageBox.No)
             
             if reply == QMessageBox.Yes:
                 count = 0
                 for orig, dupe in duplicates:
                     try:
                         # Delete dupe
                         os.remove(os.path.join(path, dupe))
                         # Try delete associated json/thumb
                         base = dupe[:-4]
                         if os.path.exists(os.path.join(path, f"{base}.json")):
                             os.remove(os.path.join(path, f"{base}.json"))
                         if os.path.exists(os.path.join(path, f"{base}_thumb.jpg")):
                             os.remove(os.path.join(path, f"{base}_thumb.jpg"))
                         count += 1
                     except: pass
                 
                 self.log(f"Cleaned up {count} clones.")
                 QMessageBox.information(self, "Cleanup", f"Deleted {count} duplicate files.")
                 
                 # Helper to refresh main window if possible
                 parent = self.parent()
                 if parent and hasattr(parent, 'load_installed_characters'):
                      parent.load_installed_characters()
