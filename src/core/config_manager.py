import json
import os
import logging
from typing import Dict, Any, Optional
from PySide6.QtCore import QStandardPaths

logger = logging.getLogger(__name__)

class ConfigManager:
    DEFAULT_GAME_PATH = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\USER\Client\0\CustomCharacters"
    APP_NAME = "SCCharacterInstaller"
    ORG_NAME = "Antigravity"
    
    def __init__(self):
        self.config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        self.config_file = os.path.join(self.config_dir, "config.json")
        self._ensure_config_dir()
        self.config: Dict[str, Any] = self._load_config()
        
    def _ensure_config_dir(self):
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create config directory: {e}")

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                # Backup corrupted config
                try:
                    backup_path = self.config_file + ".bak"
                    import shutil
                    shutil.copy2(self.config_file, backup_path)
                    logger.info(f"Corrupted config backed up to {backup_path}")
                except Exception as backup_error:
                    logger.error(f"Failed to backup corrupted config: {backup_error}")
        return self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        # Try to auto-detect path if default doesn't exist
        path = self.DEFAULT_GAME_PATH
        if not os.path.exists(path):
            detected = self.auto_detect_path()
            if detected:
                path = detected
                
        return {
            "game_path": path,
            "theme": "dark",
            "language": "es",
            "sound_enabled": True
        }
        
    def save_config(self):
        try:
            self._ensure_config_dir()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
    def get_game_path(self) -> str:
        return self.config.get("game_path", self.DEFAULT_GAME_PATH)
        
    def set_game_path(self, path: str):
        self.config["game_path"] = path
        self.save_config()
        
    def validate_path(self) -> bool:
        """
        Checks if the configured game path exists.
        If the path exists but 'CustomCharacters' subdir is missing, it creates it.
        Returns True if the final path is valid and writable.
        """
        path = self.get_game_path()
        try:
            if not os.path.exists(path):
                # Check if parent exists and we just need to create the folder
                if path.endswith("CustomCharacters"):
                    parent = os.path.dirname(path)
                    if os.path.exists(parent):
                        try:
                            os.makedirs(path, exist_ok=True)
                            return True
                        except OSError:
                            return False
                return False
            
            # Ensure it is a directory
            if not os.path.isdir(path):
                return False
                
            # Check writability
            if not os.access(path, os.W_OK):
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error validating path: {e}")
            return False

    def auto_detect_path(self) -> Optional[str]:
        """
        Attempts to find the Star Citizen CustomCharacters directory.
        """
        common_paths = [
            r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE",
            r"C:\Program Files\Roberts Space Industries\StarCitizen\PTU",
            r"D:\Program Files\Roberts Space Industries\StarCitizen\LIVE",
            r"D:\Program Files\Roberts Space Industries\StarCitizen\PTU",
            r"C:\Games\StarCitizen\LIVE",
            r"D:\Games\StarCitizen\LIVE"
        ]
        
        suffix = r"USER\Client\0\CustomCharacters"
        
        for base in common_paths:
            full_path = os.path.join(base, suffix)
            if os.path.exists(full_path):
                return full_path
                
            # Check if base exists but suffix is missing (maybe just create it?)
            if os.path.exists(base):
                # Check if USER/Client/0 exists
                client_path = os.path.join(base, r"USER\Client\0")
                if os.path.exists(client_path):
                    return full_path # It's a valid candidate to create
                    
        return None
        
    def get_custom_ptu_path(self) -> Optional[str]:
        return self.config.get("custom_ptu_path", None)
        
    def set_custom_ptu_path(self, path: str):
        self.config["custom_ptu_path"] = path if path.strip() else None
        self.save_config()

    # --- Favorites Management ---
    def get_favorites(self) -> list:
        return self.config.get("favorites", [])

    def add_favorite(self, character_name: str):
        favs = self.get_favorites()
        if character_name not in favs:
            favs.append(character_name)
            self.config["favorites"] = favs
            self.save_config()

    def remove_favorite(self, character_name: str):
        favs = self.get_favorites()
        if character_name in favs:
            favs.remove(character_name)
            self.config["favorites"] = favs
            self.save_config()

    def is_favorite(self, character_name: str) -> bool:
        return character_name in self.get_favorites()

    def set_muted(self, muted: bool):
        self.config["sound_enabled"] = not muted
        self.save_config()

    def is_muted(self) -> bool:
        return not self.config.get("sound_enabled", True)

    # --- Stream/OBS Integration ---
    def get_obs_integration_enabled(self) -> bool:
        return self.config.get("obs_integration_enabled", True)

    def set_obs_integration_enabled(self, enabled: bool):
        self.config["obs_integration_enabled"] = enabled
        self.save_config()

    def get_stream_output_path(self) -> str:
        """Returns the path where stream info (txt/images) will be written."""
        # Default to a folder named "StreamKit" in the Documents/BioMetrics or similar
        # For simplicity, let's use a subdirectory of the main config dir or a specific Documents folder
        # The user PROBABLY wants this accessible. 
        # Let's use: User Documents/BioMetrics/StreamKit
        # If not set in config, return default.
        custom = self.config.get("stream_output_path")
        if custom:
            return custom
            
        docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        # Assuming app name used elsewhere is "BioMetrics" implicitly or checking if we can use a standard folder
        return os.path.join(docs, "BioMetrics", "StreamKit")

    def set_stream_output_path(self, path: str):
        self.config["stream_output_path"] = path
        self.save_config()

