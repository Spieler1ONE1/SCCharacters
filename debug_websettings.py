
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
view = QWebEngineView()
settings = view.settings()
try:
    # Try the way I used it
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, True)
    print("Success: Direct attribute usage")
except AttributeError:
    print("Fail: AttributeError on direct usage")
except Exception as e:
    print(f"Fail: {e}")

try:
    # Try the correct enum way
    val = QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture
    settings.setAttribute(val, True)
    print("Success: Enum usage")
except AttributeError:
    print("Fail: AttributeError on Enum usage")
except Exception as e:
    print(f"Fail: {e}")
