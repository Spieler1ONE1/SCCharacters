
from PySide6.QtCore import QUrl, QObject
from PySide6.QtMultimedia import QSoundEffect
import os
from src.utils.paths import get_assets_path

class SoundManager(QObject):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.sounds = {}
        self.muted = self.config_manager.is_muted()
        self._load_sounds()

    def _load_sounds(self):
        # Define sound events and their localized filenames if we had them
        # For now, we will try to load standard names.
        # User can place wav files in assets/sounds/
        sound_dir = os.path.join(get_assets_path(), "sounds")
        if not os.path.exists(sound_dir):
            return

        sound_files = {
            "startup": "startup.wav",
            "click": "click.wav",
            "hover": "hover.wav",
            "success": "success.wav",
            "error": "error.wav",
            "install_finished": "install_finished.wav",
            "trash": "trash.wav",
            "card_hover": "card_hover.wav",
            "login": "login.wav"
        }

        for name, filename in sound_files.items():
            path = os.path.join(sound_dir, filename)
            if os.path.exists(path):
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(path))
                effect.setVolume(0.10) # 20% Volume
                self.sounds[name] = effect

    def play(self, sound_name):
        if self.muted: return
        
        # Check config
        if not self.config_manager.config.get("enable_sounds", True):
            return

        if sound_name in self.sounds:
            # Randomize pitch slighly? No, keep simple.
            self.sounds[sound_name].play()
        else:
            # Fallback for now?
            pass

    def play_click(self): self.play("click")
    def play_hover(self): self.play("hover")
    def play_card_hover(self): self.play("card_hover")
    def play_success(self): self.play("success")
    def play_error(self): self.play("error")
    def play_login(self): self.play("login")

    def set_muted(self, muted):
        self.muted = muted
        self.config_manager.set_muted(muted)
