import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.visual_asset_manager import VisualAssetManager

headline = "वाराणसी के सभी घाट डूबे, छतों पर आरती-अंतिम संस्कार: MP-UP समेत 4 राज्यों में आज भारी बारिश"
category = "National"
article_url = "https://news.google.com/rss/articles/CBMivgFBVV95cUxNYmxPS0ZJZ1V0UVpfTjRMMERTRG10dTF5NGJqMWV5N1VvR1hPcWtpUU9SZlU5NUJsQVY2MUQ4eGF4MTFXZHJrZUNVZC03U3I3ZVhHei02MWpSNEZhS1F4UnR6THU4Z2E4RFA1ZVN2NFlGLVY5NklvRnVIblRxbHdpb3Z5T0t6cHlEVnpsajdPY2NHekxTNkZxd1JEZG5MT3FEVVNGaldWTVZ6WU1PS00tN0VZWHZYcThTeUNHSmRR0gHDAUFVX3lxTFBTQTRkOEpVb1c4d3ZIbHhtMGRnZlFYbFRCdm4xaS1iM19MMjV4TU01SHV1UXR5aTJyWnFFT3oyc3VBckVpSXh2cEdOT2NUaV9CMVJjTDBBY3dFU05KUVVnSXZaTndLbEtsenN0a3BfZEFzQnpjLWFVc0NKZlRNWmVOLUlqaXMzdWhTd01aZDhtamtuVHUwVnNmQ0RPODdvdTN4d3daZFJzQ082ek5HakdWc0tOSmhsWE5uem5Sei1za0VCcw?oc=5"
output_dir = BASE_DIR / "assets" / "test_visual_check"

print("Fetching Multi-Visual Real Event Assets...")
assets = VisualAssetManager.get_multi_visual_assets(
    headline=headline,
    category=category,
    output_dir=output_dir,
    article_url=article_url,
    max_photos=4
)

print(f"\n✅ Resolved {len(assets)} Visual Assets:")
for i, a in enumerate(assets, 1):
    print(f"  [{i}] Source: {a.source_name}, Path: {a.file_path}, Credit: {a.on_screen_credit}")
