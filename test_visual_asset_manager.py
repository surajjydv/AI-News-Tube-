import os
import sys
import time
import requests
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR, PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_API_KEY
from utils.logger import logger

TEST_IMAGES_DIR = ASSETS_DIR / "test_images"
TEST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

queries = ["Narendra Modi", "Japan earthquake", "NASA Mars"]
api_status = {
    "Wikimedia Commons API": {"success": 0, "failed": 0, "last_error": "None"},
    "Pexels API": {"success": 0, "failed": 0, "last_error": "None"},
    "Pixabay API": {"success": 0, "failed": 0, "last_error": "None"},
    "Unsplash API": {"success": 0, "failed": 0, "last_error": "None"}
}

def test_wikimedia(query: str, idx: int):
    api_name = "Wikimedia Commons API"
    raw_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={requests.utils.quote(query)}&gsrnamespace=6&prop=imageinfo&iiprop=url|size&format=json&gsrlimit=5"
    headers = {"User-Agent": "AI-NewsTube-Bot/1.0 (https://ainewstube.org; newsbot@ainewstube.org)"}
    sanitized_url = raw_url

    print("\n" + "─" * 70)
    print(f"🌐 Testing API : {api_name}")
    print(f"📌 Search Query: '{query}'")
    print(f"🔗 Request URL : {sanitized_url}")

    try:
        resp = requests.get(raw_url, headers=headers, timeout=10)
        print(f"📶 HTTP Status : {resp.status_code}")
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            results_count = len(pages)
            print(f"🔢 Search Results Count: {results_count}")

            if results_count > 0:
                for page_id, page_info in pages.items():
                    imageinfo = page_info.get("imageinfo", [])
                    if imageinfo and "url" in imageinfo[0]:
                        img_url = imageinfo[0]["url"]
                        if img_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                            print(f"🖼️ Selected Image URL: {img_url}")
                            r = requests.get(img_url, headers=headers, timeout=12)
                            if r.status_code == 200 and len(r.content) > 5000:
                                file_path = TEST_IMAGES_DIR / f"wikimedia_{idx}.jpg"
                                with open(file_path, "wb") as f:
                                    f.write(r.content)
                                print(f"📁 Saved File Path  : {file_path}")

                                with Image.open(file_path) as img:
                                    w, h = img.size
                                    print(f"📐 Pillow Dimensions: {w} x {h} (Format: {img.format})")
                                    print(f"✅ Image Verification: VALID ({file_path.stat().st_size} bytes)")
                                    api_status[api_name]["success"] += 1
                                    return True
            else:
                api_status[api_name]["failed"] += 1
                api_status[api_name]["last_error"] = "0 results found"
        else:
            api_status[api_name]["failed"] += 1
            api_status[api_name]["last_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        print(f"❌ Error: {e}")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = str(e)

    return False

def test_nasa(query: str, idx: int):
    api_name = "NASA Open Media API"
    raw_url = f"https://images-api.nasa.gov/search?q={requests.utils.quote(query)}&media_type=image"
    sanitized_url = raw_url

    print("\n" + "─" * 70)
    print(f"🌐 Testing API : {api_name}")
    print(f"📌 Search Query: '{query}'")
    print(f"🔗 Request URL : {sanitized_url}")

    try:
        resp = requests.get(raw_url, timeout=10)
        print(f"📶 HTTP Status : {resp.status_code}")
        if resp.status_code == 200:
            items = resp.json().get("collection", {}).get("items", [])
            results_count = len(items)
            print(f"🔢 Search Results Count: {results_count}")

            if results_count > 0:
                for item in items[:3]:
                    links = item.get("links", [])
                    if links and "href" in links[0]:
                        img_url = links[0]["href"]
                        print(f"🖼️ Selected Image URL: {img_url}")
                        r = requests.get(img_url, timeout=12)
                        if r.status_code == 200 and len(r.content) > 5000:
                            file_path = TEST_IMAGES_DIR / f"nasa_{idx}.jpg"
                            with open(file_path, "wb") as f:
                                f.write(r.content)
                            print(f"📁 Saved File Path  : {file_path}")

                            with Image.open(file_path) as img:
                                w, h = img.size
                                print(f"📐 Pillow Dimensions: {w} x {h} (Format: {img.format})")
                                print(f"✅ Image Verification: VALID ({file_path.stat().st_size} bytes)")
                                if api_name not in api_status:
                                    api_status[api_name] = {"success": 0, "failed": 0, "last_error": "None"}
                                api_status[api_name]["success"] += 1
                                return True
            else:
                if api_name not in api_status:
                    api_status[api_name] = {"success": 0, "failed": 0, "last_error": "None"}
                api_status[api_name]["failed"] += 1
                api_status[api_name]["last_error"] = "0 results found"
        else:
            if api_name not in api_status:
                api_status[api_name] = {"success": 0, "failed": 0, "last_error": "None"}
            api_status[api_name]["failed"] += 1
            api_status[api_name]["last_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        print(f"❌ Error: {e}")
        if api_name not in api_status:
            api_status[api_name] = {"success": 0, "failed": 0, "last_error": "None"}
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = str(e)

    return False


def test_pexels(query: str, idx: int):
    api_name = "Pexels API"
    if not PEXELS_API_KEY:
        print("\n" + "─" * 70)
        print(f"🌐 Testing API : {api_name}")
        print("⚠️ Skipped: PEXELS_API_KEY not configured in environment")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = "API Key Missing"
        return False

    headers = {"Authorization": PEXELS_API_KEY}
    raw_url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=3&orientation=landscape"
    sanitized_url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=3&orientation=landscape [Authorization: REDACTED]"

    print("\n" + "─" * 70)
    print(f"🌐 Testing API : {api_name}")
    print(f"📌 Search Query: '{query}'")
    print(f"🔗 Request URL : {sanitized_url}")

    try:
        resp = requests.get(raw_url, headers=headers, timeout=10)
        print(f"📶 HTTP Status : {resp.status_code}")
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            results_count = len(photos)
            print(f"🔢 Search Results Count: {results_count}")

            if results_count > 0:
                photo = photos[0]
                img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                print(f"🖼️ Selected Image URL: {img_url}")
                r = requests.get(img_url, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000:
                    file_path = TEST_IMAGES_DIR / f"pexels_{idx}.jpg"
                    with open(file_path, "wb") as f:
                        f.write(r.content)
                    print(f"📁 Saved File Path  : {file_path}")

                    with Image.open(file_path) as img:
                        w, h = img.size
                        print(f"📐 Pillow Dimensions: {w} x {h} (Format: {img.format})")
                        print(f"✅ Image Verification: VALID ({file_path.stat().st_size} bytes)")
                        api_status[api_name]["success"] += 1
                        return True
            else:
                api_status[api_name]["failed"] += 1
                api_status[api_name]["last_error"] = "0 results found"
        else:
            api_status[api_name]["failed"] += 1
            api_status[api_name]["last_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        print(f"❌ Error: {e}")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = str(e)

    return False

def test_pixabay(query: str, idx: int):
    api_name = "Pixabay API"
    if not PIXABAY_API_KEY:
        print("\n" + "─" * 70)
        print(f"🌐 Testing API : {api_name}")
        print("⚠️ Skipped: PIXABAY_API_KEY not configured in environment")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = "API Key Missing"
        return False

    raw_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={requests.utils.quote(query)}&image_type=photo&orientation=horizontal&per_page=3"
    sanitized_url = f"https://pixabay.com/api/?key=REDACTED&q={requests.utils.quote(query)}&image_type=photo&orientation=horizontal&per_page=3"

    print("\n" + "─" * 70)
    print(f"🌐 Testing API : {api_name}")
    print(f"📌 Search Query: '{query}'")
    print(f"🔗 Request URL : {sanitized_url}")

    try:
        resp = requests.get(raw_url, timeout=10)
        print(f"📶 HTTP Status : {resp.status_code}")
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            results_count = len(hits)
            print(f"🔢 Search Results Count: {results_count}")

            if results_count > 0:
                hit = hits[0]
                img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                print(f"🖼️ Selected Image URL: {img_url}")
                r = requests.get(img_url, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000:
                    file_path = TEST_IMAGES_DIR / f"pixabay_{idx}.jpg"
                    with open(file_path, "wb") as f:
                        f.write(r.content)
                    print(f"📁 Saved File Path  : {file_path}")

                    with Image.open(file_path) as img:
                        w, h = img.size
                        print(f"📐 Pillow Dimensions: {w} x {h} (Format: {img.format})")
                        print(f"✅ Image Verification: VALID ({file_path.stat().st_size} bytes)")
                        api_status[api_name]["success"] += 1
                        return True
            else:
                api_status[api_name]["failed"] += 1
                api_status[api_name]["last_error"] = "0 results found"
        else:
            api_status[api_name]["failed"] += 1
            api_status[api_name]["last_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        print(f"❌ Error: {e}")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = str(e)

    return False

def test_unsplash(query: str, idx: int):
    api_name = "Unsplash API"
    if not UNSPLASH_API_KEY:
        print("\n" + "─" * 70)
        print(f"🌐 Testing API : {api_name}")
        print("⚠️ Skipped: UNSPLASH_API_KEY not configured in environment")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = "API Key Missing"
        return False

    headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
    raw_url = f"https://api.unsplash.com/search/photos?query={requests.utils.quote(query)}&per_page=3&orientation=landscape"
    sanitized_url = f"https://api.unsplash.com/search/photos?query={requests.utils.quote(query)}&per_page=3&orientation=landscape [Client-ID: REDACTED]"

    print("\n" + "─" * 70)
    print(f"🌐 Testing API : {api_name}")
    print(f"📌 Search Query: '{query}'")
    print(f"🔗 Request URL : {sanitized_url}")

    try:
        resp = requests.get(raw_url, headers=headers, timeout=10)
        print(f"📶 HTTP Status : {resp.status_code}")
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            results_count = len(results)
            print(f"🔢 Search Results Count: {results_count}")

            if results_count > 0:
                res = results[0]
                img_url = res.get("urls", {}).get("regular")
                print(f"🖼️ Selected Image URL: {img_url}")
                r = requests.get(img_url, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000:
                    file_path = TEST_IMAGES_DIR / f"unsplash_{idx}.jpg"
                    with open(file_path, "wb") as f:
                        f.write(r.content)
                    print(f"📁 Saved File Path  : {file_path}")

                    with Image.open(file_path) as img:
                        w, h = img.size
                        print(f"📐 Pillow Dimensions: {w} x {h} (Format: {img.format})")
                        print(f"✅ Image Verification: VALID ({file_path.stat().st_size} bytes)")
                        api_status[api_name]["success"] += 1
                        return True
            else:
                api_status[api_name]["failed"] += 1
                api_status[api_name]["last_error"] = "0 results found"
        else:
            api_status[api_name]["failed"] += 1
            api_status[api_name]["last_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        print(f"❌ Error: {e}")
        api_status[api_name]["failed"] += 1
        api_status[api_name]["last_error"] = str(e)

    return False

def main():
    print("=" * 70)
    print("🔬 VISUAL ASSET MANAGER INDEPENDENT DIAGNOSTIC TEST RUNNER")
    print("   Testing Queries: " + ", ".join([f"'{q}'" for q in queries]))
    print("=" * 70)

    for idx, q in enumerate(queries, start=1):
        if "nasa" in q.lower() or "mars" in q.lower() or "space" in q.lower():
            test_nasa(q, idx)
        test_wikimedia(q, idx)
        test_pexels(q, idx)
        test_pixabay(q, idx)
        test_unsplash(q, idx)

    print("\n" + "=" * 70)
    print("📊 INDEPENDENT API TEST SUMMARY REPORT")
    print("=" * 70)
    for api, status in api_status.items():
        if status["success"] > 0:
            res_str = "SUCCESS"
        else:
            res_str = f"FAILED ({status['last_error']})"
        print(f"  • {api:<25}: {res_str}")
    print("=" * 70)


if __name__ == "__main__":
    main()
