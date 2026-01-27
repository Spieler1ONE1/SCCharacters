import darkdetect
from PySide6.QtCore import QObject, Signal
from src.core.config_manager import ConfigManager

class ThemeManager(QObject):
    theme_changed = Signal(str) # Emits 'dark' or 'light'

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self._current_theme_mode = self.config_manager.config.get("theme", "auto") # auto, dark, light
        
    def get_effective_theme(self) -> str:
        """Returns the effective theme name (e.g., 'default', 'light', 'drake', 'origin', 'aegis')."""
        if self._current_theme_mode == "auto":
            is_dark_system = darkdetect.isDark() if darkdetect else True
            return "default" if is_dark_system else "light"
        
        # Backward compatibility for 'dark' -> 'default'
        if self._current_theme_mode == "dark":
            return "default"
            
        return self._current_theme_mode.lower()

    def set_theme_mode(self, mode: str):
        """Sets the theme mode and saves config. Supports all theme keys."""
        self._current_theme_mode = mode
        self.config_manager.config["theme"] = mode
        self.config_manager.save_config()
        
        self.apply_theme()

    def apply_theme(self):
        """Emits signal to update UI."""
        effective = self.get_effective_theme()
        self.theme_changed.emit(effective)

    def toggle_theme(self):
        """Cycle: Auto -> Dark -> Light -> Auto"""
        modes = ["auto", "dark", "light"]
        try:
            idx = modes.index(self._current_theme_mode)
        except ValueError:
            idx = 0
        
        next_mode = modes[(idx + 1) % len(modes)]
        self.set_theme_mode(next_mode)
        return next_mode
