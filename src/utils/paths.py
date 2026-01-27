import sys
import os

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Dev Mode: Resolve relative to this file (src/utils/paths.py) -> Project Root (2 levels up)
        # This ensures it works even if CWD is not the project root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    full_path = os.path.join(base_path, relative_path)
    return full_path.replace("\\", "/")

def get_assets_path():
    return get_resource_path("src/assets")
