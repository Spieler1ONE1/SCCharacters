import os
import requests
import logging
import shutil
import time
from typing import Optional
from .models import Character
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class Downloader:
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        from src.core.stream_integration import StreamIntegration
        from src.core.backup_manager import BackupManager
        self.stream_integration = StreamIntegration(config_manager)
        self.backup_manager = BackupManager(config_manager)
        
    def install_character(self, character: Character) -> bool:
        """
        Downloads the character file and installs it to the configured directory.
        Returns True if successful, False otherwise.
        """
        if not character.download_url:
            logger.error(f"No download URL for character {character.name}")
            character.status = "error"
            return False
            
        target_dir = self.config_manager.get_game_path()
        if not self._ensure_directory(target_dir):
            character.status = "error"
            return False
            
        # Check for duplicates (Name + Author)
        existing_filename = self._find_existing_character(target_dir, character)
        if existing_filename:
            logger.info(f"Character '{character.name}' by '{character.author}' is already installed as {existing_filename}. Skipping download.")
            character.status = "installed"
            character.local_filename = existing_filename
            
            # Update Stream Info
            self.stream_integration.update_stream_info(character)
            return True
                
        try:
            character.status = "downloading"
            
            # Determine filename
            filename = self._get_filename(character)
            temp_path = os.path.join(target_dir, f".tmp_{filename}")
            final_path = self._get_unique_path(target_dir, filename)
            
            logger.info(f"Downloading {character.name} to {final_path}")
            
            if self._download_file(character.download_url, temp_path):
                # Validate file (e.g. check if not empty)
                if os.path.getsize(temp_path) > 0:
                    # Time Capsule: Backup if target exists
                    if os.path.exists(final_path):
                        self.backup_manager.create_snapshot(final_path, reason="Pre-Update")
                        
                    os.replace(temp_path, final_path)
                    
                    # Save metadata
                    try:
                        import json
                        json_path = os.path.splitext(final_path)[0] + ".json"
                        metadata = {
                            "name": character.name,
                            "author": character.author,
                            "image_url": character.image_url,
                            "url_detail": character.url_detail,
                            "download_url": character.download_url
                        }
                        with open(json_path, 'w') as f:
                            json.dump(metadata, f, indent=4)
                    except Exception as e:
                        logger.error(f"Failed to save metadata for {character.name}: {e}")
                        
                    character.status = "installed"
                    character.local_filename = os.path.basename(final_path) # Store exact filename
                    logger.info(f"Successfully installed {character.name}")
                    
                    # Update Stream Info
                    self.stream_integration.update_stream_info(character)
                    
                    return True
                else:
                    logger.error(f"Downloaded file for {character.name} is empty")
                    os.remove(temp_path)
            
            character.status = "error"
            return False
            
        except Exception as e:
            logger.error(f"Error installing character {character.name}: {e}")
            character.status = "error"
            return False

    def install_from_url(self, url: str) -> bool:
        """
        Installs a character from a direct URL.
        """
        char = Character(name="Direct Download", url_detail="", image_url="", download_url=url)
        return self.install_character(char)

    def install_from_file(self, source_path: str) -> bool:
        """
        Installs a character from a local file.
        """
        if not os.path.isfile(source_path):
            return False
            
        target_dir = self.config_manager.get_game_path()
        if not self._ensure_directory(target_dir):
            return False
            
        try:
            filename = os.path.basename(source_path)
            target_path = self._get_unique_path(target_dir, filename)
            
            shutil.copy2(source_path, target_path)
            logger.info(f"Installed from file: {source_path} -> {target_path}")
            return True
        except Exception as e:
            logger.error(f"Error installing from file: {e}")
            return False

    def _download_file(self, url: str, target_path: str) -> bool:
        """
        Downloads a file from a URL to a target path with retry logic.
        
        Args:
            url (str): Source URL.
            target_path (str): Destination file path.
            
        Returns:
            bool: True if download successful, False otherwise.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if os.path.exists(target_path):
                    try:
                        os.remove(target_path)
                    except OSError:
                        pass
                
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    
        return False

    def _ensure_directory(self, path: str) -> bool:
        """Ensures that the directory exists, attempting to create it if necessary."""
        if not os.path.exists(path):
            if not self.config_manager.validate_path():
                logger.error(f"Target directory does not exist and could not be created: {path}")
                return False
        return True

    def _get_filename(self, character: Character) -> str:
        """
        Determines the filename for a character.
        Uses the URL's basename if it's a .chf file, otherwise sanitizes the character name.
        """
        # Try to use the basename from URL if it looks like a file
        if character.download_url and character.download_url.lower().endswith('.chf'):
            return character.download_url.split('/')[-1]
            
        # Fallback to safe name
        safe_name = "".join([c for c in character.name if c.isalnum() or c in (' ', '-', '_')]).strip()
        return f"{safe_name}.chf"

    def _get_unique_path(self, directory: str, filename: str) -> str:
        """Generates a unique file path to avoid overwrites."""
        target_path = os.path.join(directory, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(directory, f"{base}_{counter}{ext}")
            counter += 1
        return target_path

    def _find_existing_character(self, target_dir: str, character: Character) -> Optional[str]:
        """
        Scans the directory for an existing installed character matching the given one.
        Checks for exact download_url match OR (Name + Author) match.
        Returns the .chf filename if found, None otherwise.
        """
        import json
        if not os.path.exists(target_dir):
            return None
            
        try:
            for entry in os.scandir(target_dir):
                if entry.is_file() and entry.name.lower().endswith('.json'):
                    try:
                        with open(entry.path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        # 1. Check strict Download URL match (most reliable)
                        if character.download_url and data.get('download_url') == character.download_url:
                             return entry.name.rsplit('.', 1)[0] + ".chf"
                             
                        # 2. Check Name + Author match
                        # We normalize strings to be safe
                        local_name = (data.get('name') or "").strip().lower()
                        target_name = (character.name or "").strip().lower()
                        
                        if local_name == target_name:
                            # If author is present in both, must match
                            local_author = (data.get('author') or "").strip().lower()
                            target_author = (character.author or "").strip().lower()
                            
                            # If one has author and other doesn't? 
                            # Usually author is key. If target has author, it must match.
                            if target_author and local_author == target_author:
                                return entry.name.rsplit('.', 1)[0] + ".chf"
                            
                            # If target has no author (maybe manually created?), relying on name is risky but acceptable for "duplicates"
                            if not target_author:
                                return entry.name.rsplit('.', 1)[0] + ".chf"
                                
                    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                        continue
        except OSError:
            pass
            
        return None

