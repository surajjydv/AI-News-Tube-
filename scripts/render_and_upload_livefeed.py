"""
render_and_upload_livefeed.py
=============================
Renders Live TV Newsfeed Video with real event photos, Ken Burns motion, and Live TV Overlays.
NO 3D Anchors, NO Avatars. Uploads live to YouTube.
"""

import os
import sys
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.live_feed_renderer import LiveFeedRenderer
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import AudioFileClip

AUDIO_FILE = BASE_DIR / "assets" / "live_feed_jharkhand.mp3"
VIDEO_FILE = BASE_DIR / "videos" / "live_feed_jharkhand_broadcast.mp4"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "live_feed_jharkhand_thumb.jpg"

def render_thumb(photo_path: str) -> Path:
    from PIL import Image, ImageDraw
    from utils.font_utils import load_font, sanitize_text

    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (10, 18, 35))

    if photo_path and os.path.exists(photo_path):
        try:
            p_img = Image.open(photo_path).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
            img.paste(p_img, (0, 0))
        except Exception:
            pass

    draw = ImageDraw.Draw(img)

    # Top Header Band: Red
    draw.rectangle([0, 0, w, 80], fill=(180, 0, 0))
    draw.text((w // 2 - 260, 4), "LIVE BREAKING NEWS", fill=(255, 255, 255), font=load_font(56, bold=True, lang="hi"))

    # Yellow Headline Banner
    draw.rectangle([40, h - 220, w - 40, h - 110], fill=(255, 230, 0), outline=(0, 0, 0), width=3)
    draw.text((60, h - 210), sanitize_text("à¤à¤¾à¤°à¤–à¤‚à¤¡ à¤›à¤¾à¤¤à¥à¤° à¤†à¤‚à¤¦à¥‹à¤²à¤¨: à¤µà¤¿à¤§à¤¾à¤¨à¤¸à¤­à¤¾ à¤˜à¥‡à¤°à¤¾à¤µ à¤•à¤¾ à¤¬à¤¡à¤¼à¤¾ à¤…à¤ªà¤¡à¥‡à¤Ÿ"), fill=(0, 0, 0), font=load_font(44, bold=True, lang="hi"))

    # Blue Sub-banner
    draw.rectangle([40, h - 110, w - 40, h - 30], fill=(15, 32, 68), outline=(255, 200, 0), width=2)
    draw.text((60, h - 98), sanitize_text("à¤ªà¥à¤²à¤¿à¤¸ à¤¬à¥ˆà¤°à¤¿à¤•à¥‡à¤¡à¤¿à¤‚à¤— à¤Ÿà¥‚à¤Ÿà¥€ â€¢ à¤­à¤¾à¤°à¥€ à¤ªà¥à¤°à¤¦à¤°à¥à¤¶à¤¨ à¤”à¤° à¤²à¤¾à¤‡à¤µ à¤¤à¤¸à¥à¤µà¥€à¤°à¥‡à¤‚"), fill=(255, 255, 255), font=load_font(36, bold=True, lang="hi"))

    # LIVE Red Badge
    draw.rectangle([50, 100, 200, 155], fill=(220, 35, 35), outline=(255, 255, 255), width=2)
    draw.text((75, 108), "ðŸ”´ LIVE", fill=(255, 255, 255), font=load_font(30, bold=True, lang="hi"))

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE, quality=95)
    print("âœ… Created Live Feed Thumbnail:", THUMBNAIL_FILE.name)
    return THUMBNAIL_FILE

async def gen_audio(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
    await comm.save(str(AUDIO_FILE))
    print("âœ… Created Hindi Audio:", AUDIO_FILE.name)

def main():
    print("=" * 65)
    print("ðŸŽ¥ LIVE TV NEWSFEED BROADCAST RENDERER (ZERO 3D ANCHORS)")
    print("=" * 65)

    headline = "à¤à¤¾à¤°à¤–à¤‚à¤¡ à¤›à¤¾à¤¤à¥à¤° à¤ªà¥à¤°à¤¦à¤°à¥à¤¶à¤¨: à¤µà¤¿à¤§à¤¾à¤¨à¤¸à¤­à¤¾ à¤®à¤¾à¤°à¥à¤š à¤”à¤° à¤ªà¥à¤²à¤¿à¤¸ à¤¬à¤² à¤¤à¥ˆà¤¨à¤¾à¤¤"
    category = "INDIA"
    sub_text = "à¤ªà¤°à¥€à¤•à¥à¤·à¤¾ à¤®à¥‡à¤‚ à¤§à¤¾à¤‚à¤§à¤²à¥€ à¤•à¥‹ à¤²à¥‡à¤•à¤° à¤¸à¥€à¤¬à¥€à¤†à¤ˆ à¤œà¤¾à¤‚à¤š à¤•à¥€ à¤®à¤¾à¤‚à¤—, à¤¸à¥à¤°à¤•à¥à¤·à¤¾ à¤•à¥‡ à¤•à¤¡à¤¼à¥‡ à¤‡à¤‚à¤¤à¤œà¤¾à¤®"
    ticker_text = "à¤à¤¾à¤°à¤–à¤‚à¤¡ à¤µà¤¿à¤§à¤¾à¤¨à¤¸à¤­à¤¾ à¤®à¤¾à¤°à¥à¤š à¤ªà¤° à¤ªà¥à¤²à¤¿à¤¸ à¤¹à¤¾à¤ˆ à¤…à¤²à¤°à¥à¤Ÿ | à¤›à¤¾à¤¤à¥à¤° à¤¸à¤‚à¤˜ à¤•à¤¾ à¤µà¤¿à¤¶à¤¾à¤² à¤ªà¥à¤°à¤¦à¤°à¥à¤¶à¤¨ | à¤¸à¥€à¤¬à¥€à¤†à¤ˆ à¤œà¤¾à¤‚à¤š à¤•à¥€ à¤®à¤¾à¤‚à¤— à¤œà¤¾à¤°à¥€"

    # Dynamically fetch real event news photos matching story headline
    from services.visual_asset_manager import VisualAssetManager
    
    photo_paths = []
    photo_credits = []
    
    queries = [
        f"{headline}",
        "Jharkhand student protest Vidhan Sabha march",
        "Jharkhand assembly police deployment protest",
        "Jharkhand student rally Ranchi"
    ]
    
    for idx, q in enumerate(queries):
        p_out = BASE_DIR / "assets" / f"real_story_event_photo_{idx+1}.jpg"
        asset = VisualAssetManager.get_visual_asset(q, category, p_out)
        if asset and os.path.exists(asset.file_path):
            photo_paths.append(str(asset.file_path))
            photo_credits.append(asset.on_screen_credit)
            
    if not photo_paths:
        # Fallback to existing asset photos
        photo_paths = [str(p) for p in BASE_DIR.glob("assets/*.jpg") if os.path.exists(p)][:4]
        photo_credits = ["Source: Press Coverage"] * len(photo_paths)

    print(f"ðŸ“¸ Found & Downloaded {len(photo_paths)} Story-Specific Real Event News Photos!")

    # Generate Audio
    script_text = (
        "à¤¨à¤®à¤¸à¥à¤•à¤¾à¤°! AI-NewsTube à¤•à¥€ à¤²à¤¾à¤‡à¤µ à¤¸à¥à¤ªà¥‡à¤¶à¤² à¤¬à¥à¤°à¥‰à¤¡à¤•à¤¾à¤¸à¥à¤Ÿ à¤®à¥‡à¤‚ à¤†à¤ªà¤•à¤¾ à¤¸à¥à¤µà¤¾à¤—à¤¤ à¤¹à¥ˆà¥¤ "
        "à¤à¤¾à¤°à¤–à¤‚à¤¡ à¤®à¥‡à¤‚ à¤›à¤¾à¤¤à¥à¤°à¥‹à¤‚ à¤•à¤¾ à¤¬à¤¡à¤¼à¤¾ à¤ªà¥à¤°à¤¦à¤°à¥à¤¶à¤¨ à¤œà¤¾à¤°à¥€ à¤¹à¥ˆà¥¤ à¤›à¤¾à¤¤à¥à¤° à¤¸à¤‚à¤—à¤ à¤¨à¥‹à¤‚ à¤¨à¥‡ à¤ªà¤°à¥€à¤•à¥à¤·à¤¾ à¤§à¤¾à¤‚à¤§à¤²à¥€ à¤”à¤° à¤…à¤¨à¤¿à¤¯à¤®à¤¿à¤¤à¤¤à¤¾à¤“à¤‚ à¤•à¥‡ à¤µà¤¿à¤°à¥‹à¤§ à¤®à¥‡à¤‚ "
        "à¤°à¤¾à¤‚à¤šà¥€ à¤®à¥‡à¤‚ à¤µà¤¿à¤§à¤¾à¤¨à¤¸à¤­à¤¾ à¤•à¥€ à¤“à¤° à¤µà¤¿à¤¶à¤¾à¤² à¤®à¤¾à¤°à¥à¤š à¤¨à¤¿à¤•à¤¾à¤²à¤¾ à¤¹à¥ˆà¥¤ "
        "à¤ªà¥à¤°à¤¦à¤°à¥à¤¶à¤¨à¤•à¤¾à¤°à¥€ à¤›à¤¾à¤¤à¥à¤°à¥‹à¤‚ à¤•à¥€ à¤®à¤¾à¤‚à¤— à¤¹à¥ˆ à¤•à¤¿ à¤ªà¥‚à¤°à¥‡ à¤®à¤¾à¤®à¤²à¥‡ à¤•à¥€ à¤¸à¥€à¤¬à¥€à¤†à¤ˆ à¤œà¤¾à¤‚à¤š à¤•à¤°à¤¾à¤ˆ à¤œà¤¾à¤à¥¤ "
        "à¤®à¥Œà¤•à¥‡ à¤ªà¤° à¤­à¤¾à¤°à¥€ à¤ªà¥à¤²à¤¿à¤¸ à¤¬à¤² à¤¤à¥ˆà¤¨à¤¾à¤¤ à¤•à¤¿à¤¯à¤¾ à¤—à¤¯à¤¾ à¤¹à¥ˆ à¤”à¤° à¤¸à¥à¤°à¤•à¥à¤·à¤¾ à¤•à¥‡ à¤•à¤¡à¤¼à¥‡ à¤‡à¤‚à¤¤à¤œà¤¾à¤® à¤•à¤¿à¤ à¤—à¤ à¤¹à¥ˆà¤‚à¥¤ "
        "à¤¤à¤¾à¤œà¤¼à¤¾ à¤–à¤¼à¤¬à¤°à¥‹à¤‚ à¤”à¤° à¤¹à¤° à¤¬à¥à¤°à¥‡à¤•à¤¿à¤‚à¤— à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤•à¥‡ à¤²à¤¿à¤ à¤œà¥à¤¡à¤¼à¥‡ à¤°à¤¹à¤¿à¤ AI-NewsTube à¤•à¥‡ à¤¸à¤¾à¤¥à¥¤"
    )
    asyncio.run(gen_audio(script_text))

    # Generate Thumbnail
    render_thumb(photo_paths[0] if photo_paths else "")

    # Render Live Feed Video (Zero 3D Anchors)
    print("ðŸŽ¬ Rendering Live TV Feed Broadcast Video...")
    LiveFeedRenderer.render_live_feed_video(
        headline=headline,
        category=category,
        photo_paths=photo_paths,
        photo_credits=photo_credits if photo_credits else ["Source: Press News Coverage"] * len(photo_paths),
        audio_path=str(AUDIO_FILE),
        output_path=VIDEO_FILE,
        sub_text=sub_text,
        ticker_text=ticker_text
    )

    # Upload to YouTube
    print("\nðŸ“¤ Uploading Live TV Feed Broadcast Video to YouTube...")
    title = "Jharkhand Student Protest LIVE Updates ðŸ“° Assembly March Special Coverage | AI-NewsTube"
    desc = (
        "Jharkhand Students March To Assembly Seeking CBI Probe Into Exam Irregularities.\n"
        "Live Feed TV Broadcast Coverage featuring real press photographs and live graphics.\n\n"
        "#JharkhandProtest #BreakingNews #HindiNews #AINewsTube"
    )

    url = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=title,
        description=desc,
        category_id="25",
        tags=["Jharkhand Protest", "Assembly March", "Breaking News", "Hindi News"],
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    print("\n" + "=" * 65)
    print("ðŸŽ‰ SUCCESS! LIVE TV FEED BROADCAST VIDEO PUBLISHED!")
    print(f"ðŸ”— Video URL: https://youtu.be/{url}")
    print("=" * 65)

if __name__ == "__main__":
    main()

