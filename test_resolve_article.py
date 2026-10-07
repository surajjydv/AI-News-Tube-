import base64
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

def decode_google_news_url(url: str) -> str:
    """Decodes Google News base64 article URL to the direct publisher URL."""
    if "news.google.com" not in url:
        return url
    match = re.search(r'/articles/([A-Za-z0-9_\-]+)', url)
    if match:
        token = match.group(1)
        padded = token + "=" * (-len(token) % 4)
        try:
            raw_bytes = base64.urlsafe_b64decode(padded)
            # Find embedded URL
            urls = re.findall(rb'https?://[a-zA-Z0-9_\-\./\?=&%#~+]+', raw_bytes)
            for u in urls:
                u_str = u.decode('utf-8', errors='ignore')
                if "google" not in u_str and len(u_str) > 15:
                    return u_str
        except Exception as e:
            pass
    return url

def fetch_real_article_og_image(article_url: str) -> str:
    resolved_url = decode_google_news_url(article_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        r = requests.get(resolved_url, headers=headers, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for tag in [
                soup.find("meta", property="og:image"),
                soup.find("meta", attrs={"name": "twitter:image"}),
                soup.find("meta", property="og:image:secure_url"),
                soup.find("link", rel="image_src")
            ]:
                if tag and tag.get("content"):
                    return tag["content"].strip()
                if tag and tag.get("href"):
                    return tag["href"].strip()
    except Exception as e:
        print("Error fetching og:image:", e)
    return ""

# Test with live feeds
from services.rss_service import fetch_news
articles = fetch_news(limit_per_category=3)
print(f"Fetched {len(articles)} fresh articles.")
for art in articles[:5]:
    print("=" * 60)
    print("Title:", art.title)
    print("Direct Feed Image:", art.image_url)
    resolved = decode_google_news_url(art.link)
    print("Resolved URL:", resolved)
    og_img = fetch_real_article_og_image(art.link)
    print("Extracted Real Event Photo:", og_img)
