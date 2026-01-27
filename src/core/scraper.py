import requests
import logging
import time
import json
from typing import List, Optional, Callable, Dict, Any
from .models import Character
from src.utils.translations import translator

logger = logging.getLogger(__name__)

class Scraper:
    BASE_URL = "https://www.star-citizen-characters.com"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
             "Accept": "application/json"
        })

    def get_character_list(self, page: int = 1, search_query: str = None) -> List[Character]:
        """
        Fetches the list of characters using the internal API.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                params = {"page": str(page)}
                if search_query:
                    params["search"] = search_query

                url = f"{self.BASE_URL}/api/heads"
                
                logger.info(f"Fetching page {page} from {url}...")
                
                # Use session for connection pooling
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for body -> rows structure
                if "body" in data and "rows" in data["body"]:
                    rows = data["body"]["rows"]
                    characters = []
                    for item in rows:
                         char = self._process_item(item)
                         if char:
                             characters.append(char)
                    return characters
                else:
                    logger.warning(f"Unexpected JSON structure: {data.keys()}")
                    return []

            except requests.RequestException as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Response was not JSON")
                return []
            except Exception as e:
                logger.error(f"Unexpected error scraping page {page}: {e}")
                return []
        return []

    def get_all_characters(self, callback=None, stop_check=None) -> List[Character]:
        """
        Fetches ALL characters using parallel requests for maximum speed.
        """
        import concurrent.futures
        
        all_characters = []
        seen_urls = set()
        
        # Batch size for parallel requests
        # Fetches 20 pages at a time, with 10 workers concurrently
        # This should drastically speed up the sync
        BATCH_SIZE = 20 
        MAX_WORKERS = 10
        current_page = 1
        is_exhausted = False
        
        while not is_exhausted:
            if stop_check and stop_check():
                logger.info("Scraping cancelled by user.")
                break
                
            if callback:
                # Update UI with range
                callback(translator.get('downloading_db_pages').format(start=current_page, end=current_page + BATCH_SIZE - 1))
            
            # Submit batch
            futures_map = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                for i in range(BATCH_SIZE):
                    page_num = current_page + i
                    futures_map[executor.submit(self.get_character_list, page=page_num)] = page_num
                
                # Collect results as they complete
                results = {}
                for future in concurrent.futures.as_completed(futures_map):
                    if stop_check and stop_check():
                        executor.shutdown(wait=False)
                        return all_characters
                        
                    page_num = futures_map[future]
                    try:
                        chars = future.result()
                        results[page_num] = chars
                    except Exception as e:
                        logger.error(f"Error fetching page {page_num}: {e}")
                        results[page_num] = []

            # Process in order to detect end of list correctly
            # If page X is empty, we stop there.
            for i in range(BATCH_SIZE):
                page_num = current_page + i
                chars = results.get(page_num, [])
                
                if not chars:
                    is_exhausted = True
                    break
                
                for char in chars:
                    if char.download_url not in seen_urls:
                        seen_urls.add(char.download_url)
                        all_characters.append(char)
            
            if is_exhausted:
                break
                
            current_page += BATCH_SIZE
            # Minimal sleep to allow UI updates
            time.sleep(0.05)
            
        return all_characters

    def _process_item(self, item: dict) -> Optional[Character]:
        try:
            name = item.get("title", "Unknown")
            char_id = item.get("id")
            
            user_obj = item.get("user", {})
            author = user_obj.get("name", "Unknown") if isinstance(user_obj, dict) else "Unknown"
            
            image_url = item.get("previewUrl")
            if not image_url and isinstance(user_obj, dict):
                image_url = user_obj.get("image")
                
            detail_url = f"{self.BASE_URL}/character/{char_id}" if char_id else self.BASE_URL
            download_url = item.get("dnaUrl")
            
            if not download_url:
                return None

            tags = item.get("tags", [])
            created_at = item.get("createdAt", "")
            
            counts = item.get("_count", {})
            downloads = counts.get("characterDownloads", 0)
            likes = counts.get("characterLikes", 0)
            
            author_image = ""
            if isinstance(user_obj, dict):
                 author_image = user_obj.get("image", "")

            return Character(
                name=name,
                author=author,
                author_image=author_image,
                url_detail=detail_url,
                image_url=image_url or "",
                download_url=download_url,
                status="not_installed",
                tags=tags,
                downloads=downloads,
                likes=likes,
                created_at=created_at
            )
        except Exception as e:
            logger.warning(f"Error processing item: {e}")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = Scraper()
    chars = scraper.get_character_list()
    print(f"Found {len(chars)} characters.")
    if chars:
        print(f"First: {chars[0]}")
