import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import requests
import re
import urllib.parse
import feedparser

def decode_google_news_url(url: str) -> str:
    """Decodes Google News RSS article link to original news publisher site."""
    try:
        if "/articles/" in url:
            parts = url.split("/articles/")[1].split("?")[0]
            # Try parsing URLs from raw response or fetching with desktop headers
            r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }, timeout=8)
            # Find data-n-au attribute or canonical link in HTML
            match = re.search(r'data-n-au=["\']([^"\']+)["\']', r.text)
            if match:
                return match.group(1)
            
            match_c = re.search(r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*rel=["\']nofollow["\']', r.text)
            if match_c and "google.com" not in match_c.group(1):
                return match_c.group(1)

            # Find any non-google URL in scripts
            found = re.findall(r'https?://(?:www\.)?(?!google|gstatic)[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}/[^\s"\'<>]+', r.text)
            if found:
                return found[0]
    except Exception as e:
        print(f"Decode error: {e}")
    return url

if __name__ == "__main__":
    rss_url = "https://news.google.com/rss/search?q=Jharkhand+students+protest+assembly&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    print(f"Parsed {len(feed.entries)} entries.")
    for entry in feed.entries[:3]:
        print("\nEntry Title:", entry.title)
        real_url = decode_google_news_url(entry.link)
        print("Real Resolved Publisher URL:", real_url)

        if "google.com" not in real_url:
            r = requests.get(real_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=8)
            matches = re.findall(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
            print("Extracted og:image:", matches)
