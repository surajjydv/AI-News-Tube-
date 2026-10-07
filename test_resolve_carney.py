import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.visual_asset_manager import VisualAssetManager

headline = '"We Got Attacked": Canada\'s Carney Says US Launched \'Trade War\' - NDTV'
category = "World"
output_dir = BASE_DIR / "assets" / "test_carney"

assets = VisualAssetManager.get_multi_visual_assets(
    headline=headline,
    category=category,
    output_dir=output_dir,
    max_photos=3
)

print("\n=== RESOLVED REAL VISUAL ASSETS ===")
for i, a in enumerate(assets, 1):
    print(f"📸 Photo {i}: {a.source_name} | {a.on_screen_credit} | Path: {Path(a.file_path).name}")
