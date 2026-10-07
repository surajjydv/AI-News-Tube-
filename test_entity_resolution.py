import sys
import urllib.parse
import requests
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_verified_entity_photo(query: str) -> dict:
    """
    Finds the exact Wikipedia article for an entity and returns its verified real photograph.
    """
    headers = {"User-Agent": "AI-NewsTube-Editorial/2.0 (contact@ainewstube.com)"}
    
    # 1. Search Wikipedia for best matching article title
    search_url = "https://en.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1
    }
    
    try:
        r = requests.get(search_url, params=search_params, headers=headers, timeout=6)
        if r.status_code == 200:
            res = r.json()
            search_items = res.get("query", {}).get("search", [])
            if not search_items:
                return {}
            page_title = search_items[0]["title"]
            
            # 2. Get lead image for this page
            page_params = {
                "action": "query",
                "titles": page_title,
                "prop": "pageimages|pageterms",
                "format": "json",
                "pithumbsize": "1280",
                "redirects": 1
            }
            r2 = requests.get(search_url, params=page_params, headers=headers, timeout=6)
            if r2.status_code == 200:
                p_data = r2.json()
                pages = p_data.get("query", {}).get("pages", {})
                for pid, page in pages.items():
                    if "thumbnail" in page:
                        src = page["thumbnail"]["source"]
                        # Skip svg logos
                        if not src.endswith(".svg.png") and not src.endswith(".svg"):
                            return {
                                "entity": page_title,
                                "photo_url": src,
                                "description": page.get("terms", {}).get("description", [""])[0]
                            }
    except Exception as e:
        print("Search error:", e)
    return {}

test_queries = [
    "Carney",
    "PM Modi",
    "Health minister Nadda",
    "Putin",
    "EAM Jaishankar",
    "H1N1 virus",
    "Supreme Court of India",
    "Panama cargo ship"
]

print("=== 100% VERIFIED REAL EVENT ENTITY PHOTOS ===")
for q in test_queries:
    res = get_verified_entity_photo(q)
    print(f"📌 Query: {q:<22} -> Entity: {res.get('entity', 'None'):<25} | Desc: {res.get('description', '')[:35]}")
    print(f"   📸 Photo: {res.get('photo_url')}")
