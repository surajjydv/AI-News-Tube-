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

BASE_DIR = Path(__file__).resolve().parent
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
    draw.text((60, h - 210), sanitize_text("झारखंड छात्र आंदोलन: विधानसभा घेराव का बड़ा अपडेट"), fill=(0, 0, 0), font=load_font(44, bold=True, lang="hi"))

    # Blue Sub-banner
    draw.rectangle([40, h - 110, w - 40, h - 30], fill=(15, 32, 68), outline=(255, 200, 0), width=2)
    draw.text((60, h - 98), sanitize_text("पुलिस बैरिकेडिंग टूटी • भारी प्रदर्शन और लाइव तस्वीरें"), fill=(255, 255, 255), font=load_font(36, bold=True, lang="hi"))

    # LIVE Red Badge
    draw.rectangle([50, 100, 200, 155], fill=(220, 35, 35), outline=(255, 255, 255), width=2)
    draw.text((75, 108), "🔴 LIVE", fill=(255, 255, 255), font=load_font(30, bold=True, lang="hi"))

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE, quality=95)
    print("✅ Created Live Feed Thumbnail:", THUMBNAIL_FILE.name)
    return THUMBNAIL_FILE

async def gen_audio(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
    await comm.save(str(AUDIO_FILE))
    print("✅ Created Hindi Audio:", AUDIO_FILE.name)

def main():
    print("=" * 65)
    print("🎥 LIVE TV NEWSFEED BROADCAST RENDERER (ZERO 3D ANCHORS)")
    print("=" * 65)

    headline = "झारखंड छात्र प्रदर्शन: विधानसभा मार्च और पुलिस बल तैनात"
    category = "INDIA"
    sub_text = "परीक्षा में धांधली को लेकर सीबीआई जांच की मांग, सुरक्षा के कड़े इंतजाम"
    ticker_text = "झारखंड विधानसभा मार्च पर पुलिस हाई अलर्ट | छात्र संघ का विशाल प्रदर्शन | सीबीआई जांच की मांग जारी"

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

    print(f"📸 Found & Downloaded {len(photo_paths)} Story-Specific Real Event News Photos!")

    # Generate Audio
    script_text = (
        "नमस्कार! AI-NewsTube की लाइव स्पेशल ब्रॉडकास्ट में आपका स्वागत है। "
        "झारखंड में छात्रों का बड़ा प्रदर्शन जारी है। छात्र संगठनों ने परीक्षा धांधली और अनियमितताओं के विरोध में "
        "रांची में विधानसभा की ओर विशाल मार्च निकाला है। "
        "प्रदर्शनकारी छात्रों की मांग है कि पूरे मामले की सीबीआई जांच कराई जाए। "
        "मौके पर भारी पुलिस बल तैनात किया गया है और सुरक्षा के कड़े इंतजाम किए गए हैं। "
        "ताज़ा ख़बरों और हर ब्रेकिंग अपडेट के लिए जुड़े रहिए AI-NewsTube के साथ।"
    )
    asyncio.run(gen_audio(script_text))

    # Generate Thumbnail
    render_thumb(photo_paths[0] if photo_paths else "")

    # Render Live Feed Video (Zero 3D Anchors)
    print("🎬 Rendering Live TV Feed Broadcast Video...")
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
    print("\n📤 Uploading Live TV Feed Broadcast Video to YouTube...")
    title = "Jharkhand Student Protest LIVE Updates 📰 Assembly March Special Coverage | AI-NewsTube"
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
    print("🎉 SUCCESS! LIVE TV FEED BROADCAST VIDEO PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{url}")
    print("=" * 65)

if __name__ == "__main__":
    main()
