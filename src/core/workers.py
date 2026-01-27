import os
import time
import logging
from typing import List, Optional, Callable, Dict, Any
from PySide6.QtCore import QRunnable, QObject, Signal, Slot, QUrl

from src.core.models import Character
from src.core.scraper import Scraper
from src.core.downloader import Downloader

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals:
        finished: No data
        result: object data returned from processing
        error: str error message
        progress: str progress message or int progress value
    """
    finished = Signal()
    result = Signal(object)
    error = Signal(str)
    progress = Signal(str)

class BaseWorker(QRunnable):
    """
    Abstract base worker for handling threaded tasks with standard signals.
    """
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        pass

class ScraperWorker(BaseWorker):
    """
    Worker to fetch characters from the web via Scraper.
    """
    def __init__(self, scraper: Scraper, start_page: int = 1, pages_to_fetch: int = 1, search_query: Optional[str] = None):
        super().__init__()
        self.scraper = scraper
        self.start_page = start_page
        self.pages_to_fetch = pages_to_fetch
        self.search_query = search_query

    @Slot()
    def run(self):
        try:
            if self.pages_to_fetch == 1:
                # Simple sequential fetch (common case)
                chars = self.scraper.get_character_list(page=self.start_page, search_query=self.search_query)
                self.signals.result.emit(chars)
                self.signals.finished.emit()
            else:
                # Parallel fetch for bulk loading
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                all_characters = []
                pages = range(self.start_page, self.start_page + self.pages_to_fetch)
                results_map = {}
                
                with ThreadPoolExecutor(max_workers=min(10, self.pages_to_fetch)) as executor:
                    future_to_page = {
                        executor.submit(self.scraper.get_character_list, page=p, search_query=self.search_query): p 
                        for p in pages
                    }
                    
                    completed_count = 0
                    for future in as_completed(future_to_page):
                        page = future_to_page[future]
                        try:
                            chars = future.result()
                            if chars:
                                results_map[page] = chars
                            completed_count += 1
                            self.signals.progress.emit(f"Fetched page {completed_count}/{self.pages_to_fetch}")
                        except Exception as e:
                            logger.error(f"Error fetching page {page}: {e}")
                
                # Assemble in order
                for p in sorted(results_map.keys()):
                    all_characters.extend(results_map[p])
                    
                self.signals.result.emit(all_characters)
                self.signals.finished.emit()
                
        except Exception as e:
            logger.error(f"ScraperWorker error: {e}")
            self.signals.error.emit(str(e))

class SyncAllWorker(BaseWorker):
    """
    Worker to sync ALL characters (deep scan).
    """
    def __init__(self, scraper: Scraper, stop_check: Optional[Callable[[], bool]] = None):
        super().__init__()
        self.scraper = scraper
        self.stop_check = stop_check
        
    @Slot()
    def run(self):
        try:
            def callback(msg):
                self.signals.progress.emit(msg)
                
            characters = self.scraper.get_all_characters(callback=callback, stop_check=self.stop_check)
            self.signals.result.emit(characters)
            self.signals.finished.emit()
        except Exception as e:
            logger.error(f"SyncAllWorker error: {e}")
            self.signals.error.emit(str(e))

class InstallWorker(BaseWorker):
    """
    Worker to install a specific character.
    """
    def __init__(self, downloader: Downloader, character: Character):
        super().__init__()
        self.downloader = downloader
        self.character = character
        
    @Slot()
    def run(self):
        try:
            success = self.downloader.install_character(self.character)
            if success:
                self.signals.result.emit([self.character]) # Return list for consistency if needed or just the char
            else:
                self.signals.error.emit(f"Failed to install {self.character.name}")
            self.signals.finished.emit()
        except Exception as e:
            logger.error(f"InstallWorker error: {e}")
            self.signals.error.emit(str(e))

class InstalledCharactersWorker(BaseWorker):
    """
    Worker to scan the local directory for installed characters.
    """
    def __init__(self, game_path: str):
        super().__init__()
        self.game_path = game_path
        
    @Slot()
    def run(self):
        try:
            if not os.path.exists(self.game_path):
                self.signals.result.emit([])
                self.signals.finished.emit()
                return

            files = [f for f in os.listdir(self.game_path) if f.lower().endswith('.chf')]
            files.sort()
            
            chars = []
            self.scraper = Scraper() # Initialize scraper for potential metadata recovery
            
            # Helper to process a single file (extracted for threading)
            def process_file_metadata(f):
                try:
                    name = os.path.splitext(f)[0]
                    file_full_path = os.path.join(self.game_path, f)
                    json_path = os.path.join(self.game_path, f"{name}.json")
                    thumb_path = os.path.join(self.game_path, f"{name}_thumb.jpg")
                    
                    mtime = os.path.getmtime(file_full_path)
                    
                    # Check for custom thumbnail
                    image_url = ""
                    if os.path.exists(thumb_path):
                         # Convert to file URI
                         image_url = QUrl.fromLocalFile(thumb_path).toString()

                    char_data = {
                        "name": name,
                        "url_detail": "",
                        "image_url": image_url,
                        "author": "Local",
                        "author_image": "",
                        "download_url": None,
                        "status": "installed",
                        "install_date": mtime,
                        "tags": [],
                        "downloads": 0,
                        "likes": 0,
                        "created_at": "",
                        "local_filename": f
                    }
                    
                    # Try to load richer metadata if available
                    if os.path.exists(json_path):
                        try:
                            import json
                            with open(json_path, 'r') as jf:
                                metadata = json.load(jf)
                                # Update but preserve local status
                                char_data.update(metadata)
                                char_data["status"] = "installed"
                                char_data["local_filename"] = f 
                                
                                # Clean up extra keys that are not in dataclass
                                valid_keys = {'name', 'url_detail', 'image_url', 'author', 'author_image', 'download_url', 'status', 'install_date', 'tags', 'downloads', 'likes', 'created_at', 'local_filename'}
                                keys_to_remove = [k for k in char_data if k not in valid_keys]
                                for k in keys_to_remove:
                                    del char_data[k]
                        except Exception:
                            pass # Ignore malformed json
                    else:
                        # No metadata found (manual install) - Fetch online
                        try:
                             # Clean name for search (remove obvious separators)
                             search_name = name.replace("_", " ").strip()
                             
                             # Search
                             found_chars = self.scraper.get_character_list(page=1, search_query=search_name)
                             
                             if found_chars:
                                 # Use the first match (assumed most relevant)
                                 match = found_chars[0]
                                 
                                 char_data["image_url"] = match.image_url
                                 char_data["author"] = match.author
                                 char_data["author_image"] = match.author_image
                                 char_data["url_detail"] = match.url_detail
                                 char_data["tags"] = match.tags
                                 char_data["downloads"] = match.downloads
                                 char_data["likes"] = match.likes
                                 char_data["created_at"] = match.created_at
                                 
                                 # Save valid metadata to json to avoid re-scraping and speed up future loads
                                 try:
                                    import json
                                    to_save = char_data.copy()
                                    with open(json_path, 'w') as jf:
                                        json.dump(to_save, jf, indent=4)
                                 except Exception as save_err:
                                    logger.warning(f"Failed to save metadata for {name}: {save_err}")

                        except Exception as e:
                            logger.warning(f"Failed to fetch metadata for local char {name}: {e}")
                    
                    return Character(**char_data)
                except Exception as e:
                    logger.error(f"Error processing file {f}: {e}")
                    return None

            # Use ThreadPoolExecutor to process files in parallel
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            # Limit workers to avoid spamming the API too hard (e.g. 5 concurrent requests)
            max_workers = 5
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {executor.submit(process_file_metadata, f): f for f in files}
                
                # Collect results
                for future in as_completed(future_to_file):
                    result = future.result()
                    if result:
                        chars.append(result)
            
            # Sort chars by name (or install date?) - keeping mostly original sort order is hard with as_completed
            # So let's sort explicitly by name at the end
            chars.sort(key=lambda c: c.name.lower())

            self.signals.result.emit(chars)
            self.signals.finished.emit()
            
        except Exception as e:
            logger.error(f"InstalledCharactersWorker error: {e}")
            self.signals.error.emit(str(e))

class PrefetchSignals(QObject):
    page_ready = Signal(int, list) # page_num, characters

class PrefetchWorker(QRunnable):
    """
    Worker to proactively fetch next pages in the background.
    """
    def __init__(self, scraper: Scraper, start_page: int = 2, search_query: Optional[str] = None):
        super().__init__()
        self.scraper = scraper
        self.current_page = start_page
        self.search_query = search_query
        self.signals = PrefetchSignals()
        self.is_running = True
        
    @Slot()
    def run(self):
        while self.is_running:
            try:
                if not self.is_running: break
                
                chars = self.scraper.get_character_list(self.current_page, search_query=self.search_query)
                if not chars:
                    break
                
                if not self.is_running: break

                self.signals.page_ready.emit(self.current_page, chars)
                self.current_page += 1
                
                # Sleep to be polite
                import time
                for _ in range(10): # Check stop every 10ms
                    if not self.is_running: break
                    time.sleep(0.01)
            except Exception as e:
                logger.error(f"Prefetch error: {e}")
                break
    
    def stop(self):
        self.is_running = False

class UpdateWorker(BaseWorker):
    """
    Worker to check for application updates.
    """
    def __init__(self, manager_factory: Callable[[], Any]):
        super().__init__()
        self.manager_factory = manager_factory # Avoid import loops by passing factory or class

    @Slot()
    def run(self):
        try:
            manager = self.manager_factory()
            exists, manifest = manager.check_for_updates()
            self.signals.result.emit((exists, manifest))
            self.signals.finished.emit()
        except Exception as e:
            logger.error(f"UpdateWorker error: {e}")
            self.signals.error.emit(str(e))

