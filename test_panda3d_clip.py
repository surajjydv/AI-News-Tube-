import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure the global engine boots up first
from scripts.go_live import render_clip

print("Testing full video clip render with Panda3D...")
try:
    # Render a 30s clip (will fetch real news, script, voice, and Panda3D frames)
    out_path = render_clip(1023)
    print(f"Success! Output saved to: {out_path}")
except Exception as e:
    print(f"Failed: {e}")
