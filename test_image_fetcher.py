import requests
import re
import urllib.parse
from pathlib import Path
from PIL import Image

def test_web_search(query: str, out_file: Path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&qft=+filterui:imagesize-large&form=HDRSC2&first=1"
    resp = requests.get(url, headers=headers, timeout=8)
    murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+)&quot;', resp.text)
    if not murls:
        murls = re.findall(r'\"murl\":\"(https?://[^\"]+)\"', resp.text)
    
    print(f"Found {len(murls)} potential URLs")
    for u in murls[:10]:
        try:
            r = requests.get(u, headers=headers, timeout=6)
            if r.status_code == 200 and len(r.content) > 15000:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                img = Image.open(out_file)
                w, h = img.size
                if w >= 600 and h >= 400:
                    print(f"✅ Downloaded valid news photo: {u[:60]} -> Size: {w}x{h}")
                    return True
        except Exception as e:
            print(f"Skipping {u[:40]}: {e}")
    return False

if __name__ == "__main__":
    test_web_search("Varanasi ghats submerged flood news", Path("test_downloaded_press_photo.jpg"))
