from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                                 QHBoxLayout, QTextBrowser, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
import os
import subprocess
import sys
import tempfile

from src.core.updater import UpdateManager
from src.utils.translations import translator

class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str) # Path del archivo o None si falló
    
    def __init__(self, manager, url):
        super().__init__()
        self.manager = manager
        self.url = url
        
    def run(self):
        path = self.manager.download_update(self.url, self.update_progress)
        self.finished.emit(path)
        
    def update_progress(self, val):
        self.progress.emit(val)

class UpdateDialog(QDialog):
    def __init__(self, manifest, parent=None):
        super().__init__(parent)
        self.manifest = manifest
        self.manager = UpdateManager()
        self.installer_path = None
        
        self.setWindowTitle(self.tr("update_available_title", version=manifest.get('latest_version')))
        self.setFixedWidth(400)
        
        self.setup_ui()
    
    def tr(self, key, **kwargs):
        return translator.get(key, **kwargs)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        lbl_title = QLabel(self.tr("update_header", version=self.manifest.get('latest_version')))
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_title)
        
        # Changelog
        self.txt_changelog = QTextBrowser()
        changelog = self.manifest.get("changelog", [])
        if isinstance(changelog, list):
            self.txt_changelog.setHtml("<ul>" + "".join([f"<li>{item}</li>" for item in changelog]) + "</ul>")
        else:
            self.txt_changelog.setText(str(changelog))
        layout.addWidget(self.txt_changelog)
        
        # Progress Bar (Hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_update = QPushButton(self.tr("update_now"))
        self.btn_update.clicked.connect(self.start_download)
        # Style for primary button
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        
        self.btn_later = QPushButton(self.tr("update_later"))
        self.btn_later.clicked.connect(self.reject)
        
        self.btn_skip = QPushButton(self.tr("update_skip"))
        self.btn_skip.clicked.connect(self.skip_version)
        
        btn_layout.addWidget(self.btn_skip)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_later)
        btn_layout.addWidget(self.btn_update)
        
        layout.addLayout(btn_layout)
        
    def start_download(self):
        self.btn_update.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        url = self.manifest.get("download_url")
        self.thread = DownloadThread(self.manager, url)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.start()
        
    def on_download_finished(self, path):
        if path and os.path.exists(path):
            expected_hash = self.manifest.get("sha256_hash")
            if self.manager.verify_integrity(path, expected_hash):
                self.installer_path = path
                self.install_update()
            else:
                QMessageBox.critical(self, self.tr("update_integrity_error_title"), 
                                     self.tr("update_integrity_error_msg"))
                self.btn_update.setEnabled(True)
                self.btn_later.setEnabled(True)
        else:
            QMessageBox.warning(self, self.tr("error"), self.tr("update_download_error"))
            self.btn_update.setEnabled(True)
            self.btn_later.setEnabled(True)
            
    def install_update(self):
        reply = QMessageBox.question(self, self.tr("update_install_title"), 
                                     self.tr("update_install_msg"),
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Ejecutar el instalador y cerrar esta app
            # Determine if we are running as a frozen application (exe)
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
                new_exe = self.installer_path
                
                # Create a batch script to handle the swap
                # 1. Wait for current app to close
                # 2. Overwrite current exe with new one
                # 3. Restart the application
                # 4. cleanup
                batch_content = f"""
@echo off
timeout /t 3 /nobreak > NUL
move /Y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
                try:
                    fd, bat_path = tempfile.mkstemp(suffix=".bat", text=True)
                    with os.fdopen(fd, 'w') as f:
                        f.write(batch_content)
                    
                    # Launch the batch file without creating a window
                    CREATE_NO_WINDOW = 0x08000000
                    subprocess.Popen([bat_path], shell=True, creationflags=CREATE_NO_WINDOW)
                    
                    # Close the application
                    sys.exit(0)
                    
                except Exception as e:
                    QMessageBox.critical(self, self.tr("error"), f"Error preparing update: {e}")
            else:
                # Development mode / Source code
                try:
                    # Just launch the new exe to test it, but we can't overwrite source code
                    QMessageBox.information(self, "Dev Mode", 
                                          "Running from source. The downloaded EXE will be launched, but source code is not updated.")
                    os.startfile(self.installer_path)
                    sys.exit(0)
                except Exception as e:
                    QMessageBox.critical(self, self.tr("error"), self.tr("update_start_error", error=e))
        else:
            self.accept() # Cerrar diálogo pero seguir usando la app antigua temporalmente

    def skip_version(self):
        # Aquí podrías guardar en config la versión para no volver a avisar
        # config_manager.set_skipped_version(self.manifest['latest_version'])
        self.reject()
