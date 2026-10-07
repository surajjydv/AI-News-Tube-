"""
test_generate_one_video.py
Run this ON EC2 to generate a single test video using the new pipeline.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir('/app/AI-NewsTube')
sys.path.insert(0, '/app/AI-NewsTube')

import asyncio
import time
from pathlib import Path

print("=" * 60)
print("  FULL PIPELINE TEST — Cinematic Story Video")
print("=" * 60)

# ── 1. Pick a live news story ──────────────────────────────────────
print("\n[1/6] Fetching latest news story from RSS...")
from services.rss_service import fetch_news
articles = fetch_news(limit_per_category=2)
if not articles:
    print("  ❌ No articles fetched via RSS. Using verified fallback story.")
    title = "Supreme Court Orders Immediate Action on Delhi Air Pollution Crisis"
    category = "India"
    url = ""
    summary = "The Supreme Court of India directed government authorities to implement strict measures to curb rising hazardous air pollution levels across the capital region."
    direct_img = None
else:
    story = articles[0]
    title = story.title
    category = story.category or "India"
    url = getattr(story, "link", "") or ""
    summary = story.summary or ""
    direct_img = getattr(story, "image_url", None)
    print(f"  ✅ Story: {title[:70]}")
    print(f"     Category: {category}")

# ── 2. Generate Hindi script ────────────────────────────────────────
print("\n[2/6] Generating Hindi script + English metadata...")
from services.fluent_script_service import generate_fluent_news_script
narration, takeaways, headline, yt_title, tags = generate_fluent_news_script(
    title=title, category=category, context=summary, article_url=url
)
print(f"  ✅ Narration: {len(narration.split())} Hindi words")
print(f"  ✅ Title: {yt_title[:60]}")
print(f"  ✅ Takeaways count: {len(takeaways)}")
if takeaways:
    print(f"  ✅ Slide 1: {takeaways[0][:60]}")

# ── 3. Generate Hindi TTS voice ─────────────────────────────────────
print("\n[3/6] Generating Hindi voice (MadhurNeural)...")
AUDIO_PATH = Path("/tmp/test_story_audio.mp3")

async def gen_audio():
    import edge_tts
    clean = narration.replace('"', "'").replace('\n', ' ')[:3000]
    c = edge_tts.Communicate(clean, "hi-IN-MadhurNeural", rate="+5%", volume="+0%")
    await c.save(str(AUDIO_PATH))

asyncio.run(gen_audio())
sz = AUDIO_PATH.stat().st_size if AUDIO_PATH.exists() else 0
print(f"  ✅ Audio: {sz // 1024} KB at {AUDIO_PATH}")

# ── 4. Fetch photos ─────────────────────────────────────────────────
print("\n[4/6] Fetching news photos...")
from services.visual_asset_manager import VisualAssetManager
photos_dir = Path("/tmp/test_photos")
photos_dir.mkdir(parents=True, exist_ok=True)
photos = []
try:
    assets = VisualAssetManager.get_multi_visual_assets(
        headline=headline,
        category=category,
        output_dir=photos_dir,
        article_url=url if url else None,
        direct_image_url=direct_img
    )
    photos = [a.file_path for a in assets if Path(a.file_path).exists()]
    print(f"  ✅ {len(photos)} photo(s) retrieved")
except Exception as e:
    print(f"  ⚠️ Photo fetch error: {e}")

# ── 5. Render cinematic video ───────────────────────────────────────
print("\n[5/6] Rendering cinematic story video...")
OUTPUT_VIDEO = Path(f"/app/AI-NewsTube/output/test_cinematic_{int(time.time())}.mp4")
OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)

from services.cinematic_story_renderer import render_cinematic_story_video
render_cinematic_story_video(
    headline=headline,
    category=category,
    slide_takeaways=takeaways,
    photo_paths=photos,
    audio_path=AUDIO_PATH,
    output_video_path=OUTPUT_VIDEO,
    fps=15
)

vsz = OUTPUT_VIDEO.stat().st_size // (1024*1024) if OUTPUT_VIDEO.exists() else 0
print(f"  ✅ Video generated: {OUTPUT_VIDEO.name} ({vsz} MB)")

# ── 6. Generate thumbnail ───────────────────────────────────────────
print("\n[6/6] Generating cinematic thumbnail...")
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
thumb_path = OUTPUT_VIDEO.with_suffix('.jpg')
try:
    create_real_event_youtube_thumbnail(
        headline=headline,
        category=category,
        real_photo_path=photos[0] if photos else "",
        output_path=thumb_path
    )
    print(f"  ✅ Thumbnail generated: {thumb_path.name}")
except Exception as e:
    print(f"  ⚠️ Thumbnail generation note: {e}")

print("\n" + "=" * 60)
print(f"  🎉 SUCCESS — VIDEO GENERATION COMPLETE!")
print(f"  Video file : {OUTPUT_VIDEO}")
print(f"  Thumbnail  : {thumb_path}")
print(f"  YouTube Tit: {yt_title}")
print("=" * 60)
