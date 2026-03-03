import requests
import logging
import time
import json
from typing import List, Optional, Dict, Any, Tuple
from .models import Character

logger = logging.getLogger(__name__)

# Must match star-citizen-heads API: GET /api/heads?orderBy=latest|like|download|oldest
# (CharacterOrderBy type in app/api/db/character.ts)
ORDER_BY_LATEST = "latest"   # newest first (createdAt desc)
ORDER_BY_OLDEST = "oldest"   # oldest first (createdAt asc)
ORDER_BY_LIKE = "like"       # most liked first
ORDER_BY_DOWNLOAD = "download"  # most downloaded first

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

    def get_character_list(
        self,
        page: int = 1,
        search_query: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> Tuple[List[Character], bool]:
        """
        Fetches a page of characters from the star-citizen-heads API.
        Returns (characters, has_next_page) using body.hasNextPage from the API.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                params: Dict[str, str] = {"page": str(page)}
                if search_query:
                    params["search"] = search_query
                if order_by:
                    params["orderBy"] = order_by

                url = f"{self.BASE_URL}/api/heads"
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if "body" not in data or "rows" not in data["body"]:
                    logger.warning(f"Unexpected JSON structure: {data.keys()}")
                    return ([], False)

                rows = data["body"]["rows"]
                has_next = bool(data["body"].get("hasNextPage", False))
                characters = []
                for item in rows:
                    char = self._process_item(item)
                    if char:
                        characters.append(char)
                return (characters, has_next)

            except requests.RequestException as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Response was not JSON")
                return ([], False)
            except Exception as e:
                logger.error(f"Unexpected error scraping page {page}: {e}")
                return ([], False)
        return ([], False)

    def get_random_characters(self, count: int = 20) -> List[Character]:
        """
        Fetches random characters from the star-citizen-heads API (GET /api/heads/random?count=N).
        Public endpoint, no auth. Used by the roulette.
        """
        count = max(2, min(50, count))
        url = f"{self.BASE_URL}/api/heads/random"
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params={"count": str(count)}, timeout=15)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    logger.warning("Random API did not return a list")
                    return []
                characters = []
                for item in data:
                    char = self._process_item(item)
                    if char:
                        characters.append(char)
                return characters
            except requests.RequestException as e:
                logger.warning(f"Random API attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Random API response was not JSON")
                return []
            except Exception as e:
                logger.error(f"Random API error: {e}")
                return []
        return []

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
    chars, has_next = scraper.get_character_list()
    print(f"Found {len(chars)} characters, has_next={has_next}.")
    if chars:
        print(f"First: {chars[0]}")
