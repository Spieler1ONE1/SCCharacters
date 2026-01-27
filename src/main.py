import sys
import os
import shutil
import logging
from PySide6.QtWidgets import QApplication
from datetime import datetime

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports after sys.path adjustment
from src.ui.main_window import MainWindow
# from src.ui.splash_screen import SplashScreen # Removed

# Setup logging
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = project_root

log_dir = os.path.join(base_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_path = os.path.join(log_dir, log_filename)

class ErrorTracker(logging.Handler):
    def __init__(self):
        super().__init__()
        self.has_error = False
    
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.has_error = True

error_tracker = ErrorTracker()

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_path, encoding='utf-8'),
                        logging.StreamHandler(sys.stdout),
                        error_tracker
                    ])

def main():
    app = QApplication(sys.argv)
    
    # Set app metadata
    app.setApplicationName("BioMetrics Manager")
    app.setOrganizationName("Antigravity")
    
    # Setup Icon
    # Setup Icon
    from PySide6.QtGui import QIcon
    from src.utils.paths import get_resource_path
    
    icon_path = get_resource_path("src/assets/icons/app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window directly (integrated splash)
    window = MainWindow()
    window.show()
    
    return app.exec()

def exception_hook(exctype, value, traceback):
    """
    Global function to catch unhandled exceptions.
    """
    logging.error("Unhandled exception occurred", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)

if __name__ == "__main__":
    import time
    
    # Register global exception hook
    sys.excepthook = exception_hook
    
    start_time = time.time()
    logging.info("Application starting...")
    
    try:
        exit_code = main()
    except Exception:
        # Fallback if main crashes nicely without sys.excepthook for some reason
        logging.error("Main execution failed", exc_info=True)
        exit_code = 1
    
    logging.info(f"Session finished. Duration: {time.time() - start_time:.2f}s")
    
    # Create a shutdown/cleanup routine
    logging.shutdown()
    
    # Remove log file if no errors occurred and clean exit
    if not error_tracker.has_error and exit_code == 0:
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except Exception as e:
            print(f"Failed to delete clean log: {e}")
            
    sys.exit(exit_code)
