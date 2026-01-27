import os
import requests
import shutil
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot, QStandardPaths, Qt
from PySide6.QtGui import QPixmap, QColor, QImage

class ImageLoaderSignals(QObject):
    finished = Signal(QPixmap)
    error = Signal(str)

import time

class ImageLoaderTask(QRunnable):
    def __init__(self, url, cache_dir, session):
        super().__init__()
        self.url = url
        self.cache_dir = cache_dir
        self.session = session
        self.signals = ImageLoaderSignals()
        
    @Slot()
    def run(self):
        if not self.url:
            self.signals.error.emit("No URL provided")
            return
            
        try:
            # Create cache dir if needed
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                
            # Generate filename using hash
            import hashlib
            filename = hashlib.md5(self.url.encode('utf-8')).hexdigest() + ".png"
            cache_path = os.path.join(self.cache_dir, filename)
            
            pixmap = QPixmap()
            
            # Check cache
            if os.path.exists(cache_path):
                if pixmap.load(cache_path):
                    self.signals.finished.emit(pixmap)
                    return
            
            # Download using session with retry logic
            success = False
            last_error = None
            
            for attempt in range(3):
                try:
                    response = self.session.get(self.url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.content
                    if pixmap.loadFromData(data):
                        try:
                            with open(cache_path, 'wb') as f:
                                f.write(data)
                        except OSError:
                            pass
                        self.signals.finished.emit(pixmap)
                        success = True
                        break
                    else:
                        raise ValueError("Invalid image data received")
                        
                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        time.sleep(1) # Wait before retry
            
            if not success:
               self.signals.error.emit(str(last_error))

        except Exception as e:
            self.signals.error.emit(str(e))

class ImageLoader:
    def __init__(self):
        self.threadpool = QThreadPool()
        # Increased thread count safely now that we reuse connections
        self.threadpool.setMaxThreadCount(8) 
        
        # Use standard cache location
        cache_root = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        self.cache_dir = os.path.join(cache_root, "images")
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
    def load_image(self, url, callback, error_callback=None):
        task = ImageLoaderTask(url, self.cache_dir, self.session)
        task.signals.finished.connect(callback)
        if error_callback:
            task.signals.error.connect(error_callback)
        self.threadpool.start(task)
    
    def clear_cache(self):
        if os.path.exists(self.cache_dir):
            try:
                shutil.rmtree(self.cache_dir)
            except OSError:
                pass

    @staticmethod
    def get_average_color(pixmap: QPixmap) -> str:
        """
        Returns the hex string of the average color of the pixmap.
        Uses 1x1 scaling for extreme performance.
        """
        if pixmap.isNull():
            return "#000000"
        
        image = pixmap.toImage()
        # Scale to 1x1 to average pixels
        small = image.scaled(1, 1, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        color = QColor(small.pixelColor(0, 0))
        return color.name()

