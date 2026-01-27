from dataclasses import dataclass
from typing import Optional

@dataclass
class Character:
    name: str
    url_detail: str
    image_url: str
    author: str = "Unknown"
    author_image: str = ""
    download_url: Optional[str] = None
    status: str = "not_installed"  # not_installed, installed, downloading, error
    install_date: float = 0.0
    tags: list = None
    downloads: int = 0
    likes: int = 0
    created_at: str = ""
    local_filename: Optional[str] = None # For reliable uninstalling

    @property
    def is_new(self) -> bool:
        if not self.created_at:
            return False
        try:
            from datetime import datetime, timedelta, timezone
            
            # Handle format variants if known, otherwise assume ISO
            # API usually returns ISO 8601: "2023-11-15T12:00:00.000Z"
            # We replace Z with +00:00 for fromisoformat compatibility in Py3.10-, 
            # or just rely on robust parsing if available.
            # Python 3.11+ handles Z, 3.10 might not without replace.
            ts_str = self.created_at.replace("Z", "+00:00")
            created_dt = datetime.fromisoformat(ts_str)
            
            # Ensure timezone awareness
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
                
            now = datetime.now(timezone.utc)
            
            # Define "This Week" as last 7 days
            delta = now - created_dt
            return delta.days < 7
        except Exception:
            # If parsing fails, assume not new
            return False

