import requests
from bs4 import BeautifulSoup
import re

url = "https://news.google.com/rss/articles/CBMivgFBVV95cUxNYmxPS0ZJZ1V0UVpfTjRMMERTRG10dTF5NGJqMWV5N1VvR1hPcWtpUU9SZlU5NUJsQVY2MUQ4eGF4MTFXZHJrZUNVZC03U3I3ZVhHei02MWpSNEZhS1F4UnR6THU4Z2E4RFA1ZVN2NFlGLVY5NklvRnVIblRxbHdpb3Z5T0t6cHlEVnpsajdPY2NHekxTNkZxd1JEZG5MT3FEVVNGaldWTVZ6WU1PS00tN0VZWHZYcThTeUNHSmRR0gHDAUFVX3lxTFBTQTRkOEpVb1c4d3ZIbHhtMGRnZlFYbFRCdm4xaS1iM19MMjV4TU01SHV1UXR5aTJyWnFFT3oyc3VBckVpSXh2cEdOT2NUaV9CMVJjTDBBY3dFU05KUVVnSXZaTndLbEtsenN0a3BfZEFzQnpjLWFVc0NKZlRNWmVOLUlqaXMzdWhTd01aZDhtamtuVHUwVnNmQ0RPODdvdTN4d3daZFJzQ082ek5HakdWc0tOSmhsWE5uem5Sei1za0VCcw?oc=5"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
print(f"Final URL: {resp.url}, Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, 'html.parser')
og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
if og_img:
    print("Found og:image:", og_img.get("content"))
else:
    print("No og:image meta tag")

# Check all images in article
imgs = soup.find_all("img")
print(f"Total img tags: {len(imgs)}")
for im in imgs[:5]:
    src = im.get("src") or im.get("data-src")
    if src and "http" in src:
        print("  -> img src:", src)
