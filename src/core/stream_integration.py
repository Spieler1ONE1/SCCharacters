import os
import logging
import shutil
import requests
from pathlib import Path
from src.core.models import Character
from src.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class StreamIntegration:
    """
    Handles updating text and image files for OBS/Stream integration.
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def update_stream_info(self, character: Character):
        """
        Updates the files in the StreamKit folder with the given character's info.
        """
        if not self.config_manager.get_obs_integration_enabled():
            return

        target_dir = self.config_manager.get_stream_output_path()
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create StreamKit directory {target_dir}: {e}")
            return

        # 1. Update Text Files
        self._write_file(target_dir, "current_name.txt", character.name)
        
        # Build a bio/info string
        info_parts = []
        if character.author and character.author != "Unknown":
            info_parts.append(f"Author: {character.author}")
        if character.downloads > 0:
            info_parts.append(f"Downloads: {character.downloads}")
        
        info_str = " | ".join(info_parts)
        self._write_file(target_dir, "current_info.txt", info_str)
        
        # 2. Update Image
        self._update_image(target_dir, character.image_url)

    def _write_file(self, directory: str, filename: str, content: str):
        try:
            path = os.path.join(directory, filename)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content if content else "")
        except Exception as e:
            logger.error(f"Failed to write stream info file {filename}: {e}")

    def _update_image(self, directory: str, image_url: str):
        target_path = os.path.join(directory, "current_image.jpg")
        
        if not image_url:
            # Maybe clear the image or leave previous? 
            # Better to clear or put a placeholder to avoid confusion.
            # For now, let's just delete it if it exists.
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except: pass
            return

        try:
            # If it's a local file
            if os.path.isfile(image_url):
                shutil.copy2(image_url, target_path)
                return

            # If it's a URL
            if image_url.startswith("http"):
                response = requests.get(image_url, stream=True, timeout=5)
                if response.status_code == 200:
                    with open(target_path, 'wb') as f:
                        response.raw.decode_content = True
                        shutil.copyfileobj(response.raw, f)
                else:
                    logger.warning(f"Failed to download stream image from {image_url}: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to update stream image: {e}")
