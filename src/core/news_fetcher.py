import requests
import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)

class NewsFetcher:
    BASE_URL = "https://robertsspaceindustries.com"
    COMM_LINK_URL = "https://robertsspaceindustries.com/comm-link"
    
    def fetch_news(self, page: int = 1) -> List[Dict]:
        """
        Scrapes news from RSI Comm-Link page with pagination.
        """
        try:
            # Add User-Agent to avoid 403
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }
            
            params = {}
            if page > 1:
                params['page'] = page
                
            response = requests.get(self.COMM_LINK_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            return self._scrape_html(response.text)
            
        except Exception as e:
            logger.error(f"Error fetching news (page {page}): {e}")
            return []

    def _scrape_html(self, html_content: str) -> List[Dict]:
        items = []
        try:
            import re
            # Regex strategy since generic class names might change
            # We look for links to transmissions
            # Pattern: <a href="/comm-link/transmission/..." ... class="file-block-item ...">
            
            # Find all anchor blocks that look like news items
            # We assume they contain a background image style and some text
            
            # Simple heuristic: Split by "file-block-item" or look for hrefs
            # Let's try BeautifulSoup if available, else Regex
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Try to find the links
                # RSI usually uses 'a' tags with specific structure
                links = soup.find_all('a', href=re.compile(r'/comm-link/transmission/\d+'))
                
                seen_links = set()
                
                for link in links:
                    href = link.get('href')
                    if href in seen_links: continue
                    seen_links.add(href)
                    
                    full_link = self.BASE_URL + href if href.startswith('/') else href
                    
                    # Title
                    title = " ".join(link.get_text().split())
                    # Check nested title div if text is messy
                    t_el = link.find(class_=re.compile('title', re.I))
                    if t_el: 
                        title = t_el.get_text(strip=True)
                    
                    if not title: title = "Star Citizen News"
                    
                    # Image Extraction
                    image_url = None
                    
                    # 1. Check for div class="background" style="..."
                    bg_div = link.find('div', class_='background')
                    if bg_div:
                        style = bg_div.get('style', '')
                        img_match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                        if img_match:
                            image_url = img_match.group(1)
                            
                    # 2. Key Art / slideshow fallbacks
                    if not image_url:
                        img_tag = link.find('img')
                        if img_tag: image_url = img_tag.get('src')
                    
                    # Fix relative URLs
                    if image_url and image_url.startswith('/'):
                        image_url = self.BASE_URL + image_url
                        
                    # Description
                    # Often in <div class="body"><p>...</p></div> or <div class="description">
                    desc = ""
                    body_div = link.find(class_='body') or link.find(class_='description')
                    if body_div:
                        desc = body_div.get_text(strip=True)
                    
                    # Date
                    date_obj = None
                    # Try finding "time_ago" or similar if explicit time tag missing
                    # But often parsing "2 hours ago" is hard without library.
                    # We'll stick to 'time' tag if present, or fallback to now/unknown.
                    # RSI Comm-Link usually doesn't have absolute date easily visible in grid.
                    # We might leave it as None or datetime.now() if not found.
                    
                    items.append({
                        "title": title,
                        "link": full_link,
                        "description": desc,
                        "date": datetime.now(), # Grid view rarely has exact date parsable easily
                        "image_url": image_url,
                        "source": "Roberts Space Industries"
                    })
                    
                return items

            except ImportError:
                # Regex Fallback
                return [] 
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return []

    def _extract_from_element(self, item) -> Dict:
        """Helper for standard XML extraction"""
        title = item.findtext("title")
        link = item.findtext("link")
        description = item.findtext("description") or ""
        pub_date_str = item.findtext("pubDate")
        
        date_obj = None
        if pub_date_str:
            try:
                date_obj = parsedate_to_datetime(pub_date_str)
            except: pass

        image_url = None
        enclosure = item.find("enclosure")
        if enclosure is not None:
             image_url = enclosure.get("url")
             
        return {
            "title": title,
            "link": link,
            "description": self._clean_html(description),
            "date": date_obj,
            "image_url": image_url,
            "source": "Roberts Space Industries"
        }

    def _clean_html(self, raw_html):
        # Remove basic HTML tags for preview text
        import re
        clean = re.sub('<.*?>', '', raw_html)
        return clean.strip()[:200] + "..." if len(clean) > 200 else clean
