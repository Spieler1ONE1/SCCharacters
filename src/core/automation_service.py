import time
import os
import subprocess
import shutil
import logging
from PySide6.QtCore import QObject, Signal, QThread, QTimer

logger = logging.getLogger(__name__)

class ProcessMonitorWorker(QObject):
    """
    Background worker that monitors the Star Citizen process.
    Emits signals when the game starts or stops.
    """
    game_started = Signal()
    game_stopped = Signal()
    
    def __init__(self, process_name="StarCitizen.exe"):
        super().__init__()
        self.process_name = process_name
        self._running = False
        self._is_game_running = False
        self._stop_flag = False

    def start_monitoring(self):
        self._stop_flag = False
        while not self._stop_flag:
            currently_running = self._check_process()
            
            if currently_running and not self._is_game_running:
                # Transition: Started
                self._is_game_running = True
                self.game_started.emit()
                
            elif not currently_running and self._is_game_running:
                # Transition: Stopped
                self._is_game_running = False
                self.game_stopped.emit()
                
            # Sleep 30s
            for _ in range(30):
                if self._stop_flag: break
                time.sleep(1)

    def stop(self):
        self._stop_flag = True

    def _check_process(self) -> bool:
        """Checks if process is running using tasklist (Windows)."""
        try:
            # shell=True to hide window? NO, use startupinfo to hide if needed, but check_output usually fine
            # We use tasklist /FI "IMAGENAME eq StarCitizen.exe"
            output = subprocess.check_output(
                f'tasklist /FI "IMAGENAME eq {self.process_name}"', 
                shell=True, 
                stderr=subprocess.STDOUT
            ).decode('utf-8', errors='ignore')
            
            return self.process_name.lower() in output.lower()
        except Exception:
            return False

class AutomationService(QObject):
    log_message = Signal(str, str) # level, msg

    def __init__(self, config_manager, character_service):
        super().__init__()
        self.config_manager = config_manager
        self.character_service = character_service
        
        self.monitor_thread = QThread()
        self.worker = ProcessMonitorWorker()
        self.worker.moveToThread(self.monitor_thread)
        
        self.monitor_thread.started.connect(self.worker.start_monitoring)
        self.worker.game_started.connect(self._on_game_start)
        self.worker.game_stopped.connect(self._on_game_stop)
        
    def start(self):
        if self.config_manager.config.get("auto_backup_enabled", True): # Default True for now?
            self.monitor_thread.start()
            self.log_message.emit("INFO", "Automation Service: Monitoring Star Citizen process...")

    def stop(self):
        if self.monitor_thread.isRunning():
            self.worker.stop()
            self.monitor_thread.quit()
            self.monitor_thread.wait()

    def _on_game_start(self):
        self.log_message.emit("INFO", "Game Process Detected. Monitoring for changes...")

    def _on_game_stop(self):
        self.log_message.emit("INFO", "Game Process Terminated. Initiating Auto-Sequences...")
        
        # 1. Auto Backup
        if self.config_manager.config.get("auto_backup_enabled", True):
            self._perform_auto_backup()
            
        # 2. Cloud Sync
        if self.config_manager.config.get("cloud_sync_enabled", False):
            self._perform_cloud_sync()

    def _perform_auto_backup(self):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"AutoBackup_{timestamp}.zip"
            
            # Save to default backup folder or a specific one?
            backups_dir = os.path.join(self.config_manager.config_dir, "Backups")
            os.makedirs(backups_dir, exist_ok=True)
            
            target = os.path.join(backups_dir, filename)
            self.character_service.create_backup(target)
            
            self.log_message.emit("INFO", f"Auto-Backup created: {filename}")
            
            # Cleanup old backups? (Keep last 5)
            self._cleanup_old_backups(backups_dir)
            
        except Exception as e:
            self.log_message.emit("ERROR", f"Auto-Backup Failed: {e}")

    def _cleanup_old_backups(self, backup_dir):
        try:
            files = sorted(
                [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("AutoBackup_")],
                key=os.path.getmtime
            )
            keep = 5
            if len(files) > keep:
                for f in files[:-keep]:
                    os.remove(f)
                    self.log_message.emit("INFO", f"Removed old backup: {os.path.basename(f)}")
        except:
            pass

    def _perform_cloud_sync(self):
        target_path = self.config_manager.config.get("cloud_sync_path")
        if not target_path or not os.path.exists(target_path):
            self.log_message.emit("WARNING", "Cloud Sync Skipped: Path invalid")
            return
            
        try:
            # Sync .chf and .json files
            src_dir = self.character_service.get_game_path()
            count = 0
            for item in src_dir.iterdir():
                if item.suffix in ['.chf', '.json']:
                    shutil.copy2(item, os.path.join(target_path, item.name))
                    count += 1
            self.log_message.emit("INFO", f"Cloud Sync: {count} files synced to {target_path}")
        except Exception as e:
            self.log_message.emit("ERROR", f"Cloud Sync Failed: {e}")
