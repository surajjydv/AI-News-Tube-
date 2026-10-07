"""
run_full_studio_pipeline.py
===========================
Executes the full 3D TV News Studio Production Pipeline:
News Hunter -> Script Writer -> Visuals Agent (Bing Real News + og:image + Entity Filter)
-> Voice Agent -> Video Agent (3D Virtual Studio & Animated Anchor) -> Thumbnail Agent -> Uploader
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agents.ceo_agent import ceo_agent

def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "Jharkhand students protest"
    print("=" * 65)
    print(f"🎬 EXECUTING 3D VIRTUAL NEWS STUDIO PIPELINE FOR TOPIC: '{topic}'")
    print("=" * 65)

    script_result = ceo_agent(topic=topic)

    if script_result and script_result.youtube_url:
        print("\n" + "=" * 65)
        print("🎉 SUCCESS! 3D VIRTUAL NEWS STUDIO VIDEO & THUMBNAIL PUBLISHED!")
        print(f"🔗 Video URL: {script_result.youtube_url}")
        print("=" * 65)
    else:
        print("❌ Pipeline completed or finished rendering.")

if __name__ == "__main__":
    main()
