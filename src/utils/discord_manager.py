import logging
import time
from pypresence import Presence
import asyncio
from PySide6.QtCore import QThread, Signal, QObject, Slot

logger = logging.getLogger(__name__)

class DiscordWorker(QObject):
    """Worker to handle Discord RPC in a separate thread to avoid freezing UI."""
    finished = Signal()
    
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.rpc = None
        self.connected = False
        self.disabled = False
        self._start_time = None

    @Slot()
    def connect(self):
        if self.disabled:
             return

        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            self._start_time = time.time()
            logger.info("Discord RPC Connected")
        except Exception as e:
            err_str = str(e)
            if "4000" in err_str or "Client ID is Invalid" in err_str:
                 logger.warning(f"Discord RPC Disabled: Invalid Client ID ({err_str}).")
                 self.disabled = True
            else:
                 logger.warning(f"Discord RPC failed to connect: {e}")
            self.connected = False

    @Slot(str, str, str, str)
    def update_status(self, details, state, large_image, large_text):
        if self.disabled:
            return

        if not self.connected:
            # Try to reconnect once if not connected
            self.connect()
            if not self.connected:
                return
        
        try:
            self.rpc.update(
                details=details,
                state=state,
                large_image=large_image or "logo", # Assuming 'logo' is an uploaded asset key
                large_text=large_text or "Star Citizen Character Manager",
                start=self._start_time
            )
        except Exception as e:
            logger.warning(f"Failed to update Discord status: {e}")
            self.connected = False
            # We don't loop reconnect here to avoid hammering

    @Slot()
    def clear(self):
        if self.connected:
            try:
                self.rpc.clear()
            except:
                pass

    @Slot()
    def close(self):
        if self.connected:
            try:
                self.rpc.close()
            except:
                pass
        self.finished.emit()

class DiscordManager(QObject):
    # Signals to communicate with worker
    _request_connect = Signal()
    _request_update = Signal(str, str, str, str)
    _request_close = Signal()

    CLIENT_ID = "1322368759676665856" # Placeholder Client ID
    
    def __init__(self):
        super().__init__()
        
        # Setup Thread
        self.thread = QThread()
        self.worker = DiscordWorker(self.CLIENT_ID)
        self.worker.moveToThread(self.thread)
        
        # Connect Signals
        self.thread.started.connect(self.worker.connect)
        self._request_connect.connect(self.worker.connect)
        self._request_update.connect(self.worker.update_status)
        self._request_close.connect(self.worker.close)
        
        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def update_presence(self, details="Browsing Characters", state="Online Mode"):
        # "star_citizen_logo" would need to be an asset key uploaded to the App on Discord Dev Portal
        self._request_update.emit(
            details, 
            state,
            "sc_logo", # Placeholder key
            "SC Character Manager"
        )
            
    def close(self):
        self._request_close.emit()
        self.thread.quit()
        self.thread.wait()
