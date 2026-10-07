import requests
import re
import html
import json

url = 'https://www.bing.com/images/search?q=Gyanesh+Kumar+Election+Commission+news+photo&qft=+filterui:photo-photo+filterui:aspect-wide&form=HDRSC2'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
resp = requests.get(url, headers=headers, timeout=6)

# Look for murl and metadata in Bing response
m_matches = re.findall(r'm="([^"]+)"', resp.text)
print(f"Total m matches: {len(m_matches)}")
for m in m_matches[:3]:
    try:
        clean_json = html.unescape(m)
        data = json.loads(clean_json)
        print("murl:", data.get("murl"))
        print("title (t):", data.get("t"))
        print("desc:", data.get("desc"))
        print("---")
    except Exception as e:
        print("JSON parse error:", e)
