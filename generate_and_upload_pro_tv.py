"""
generate_and_upload_pro_tv.py
=============================
Generates and uploads a 100% Professional TV News Broadcast Video & High-CTR Real Photo Thumbnail.
Features:
1. Real News Article / Press Photographs on full 16:9 stage.
2. Solid, High-Contrast TV News Lower-Third Banners (NO Blending, NO Transparency, NO 3D Avatars).
3. Live Hindi Devanagari Script Narration.
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

from services.pro_tv_engine import ProTVEngine
from services.rss_service import fetch_news
from services.visual_asset_manager import VisualAssetManager
from services.youtube_upload_service import upload_video_to_youtube
from utils.font_utils import sanitize_text
import edge_tts
from moviepy import AudioFileClip

AUDIO_FILE     = BASE_DIR / "assets" / "pro_tv_audio.mp3"
VIDEO_FILE     = BASE_DIR / "videos" / "pro_tv_video.mp4"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "pro_tv_thumbnail.jpg"

def render_pro_thumbnail(title: str, category: str, photo_path: str) -> Path:
    from PIL import Image, ImageDraw
    from utils.font_utils import load_font, sanitize_text

    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (12, 18, 32))

    if photo_path and os.path.exists(photo_path):
        try:
            p_img = Image.open(photo_path).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
            img.paste(p_img, (0, 0))
        except Exception:
            pass

    draw = ImageDraw.Draw(img)

    # 1. Solid Red Top Header Band
    draw.rectangle([0, 0, w, 85], fill=(210, 20, 20))
    draw.text((w // 2 - 250, 6), f"SPECIAL REPORT • {category.upper()}", fill=(255, 255, 255), font=load_font(54, bold=True, lang="hi"))

    # 2. Solid Yellow Headline Banner (NO BLENDING - 100% OPAQUE)
    draw.rectangle([40, h - 230, w - 40, h - 115], fill=(255, 220, 0), outline=(0, 0, 0), width=3)
    clean_t = sanitize_text(title)
    draw.text((65, h - 220), clean_t[:36], fill=(0, 0, 0), font=load_font(44, bold=True, lang="hi"))

    # 3. Solid Navy Sub-banner (100% OPAQUE)
    draw.rectangle([40, h - 115, w - 40, h - 30], fill=(10, 24, 55), outline=(255, 220, 0), width=2)
    draw.text((65, h - 102), sanitize_text("बड़ी ख़बर का पूरा सच और लाइव ग्राउंड अपडेट"), fill=(255, 255, 255), font=load_font(36, bold=True, lang="hi"))

    # 4. Live Badge
    draw.rectangle([50, 105, 210, 160], fill=(210, 20, 20), outline=(255, 255, 255), width=2)
    draw.text((75, 112), "🔴 LIVE", fill=(255, 255, 255), font=load_font(30, bold=True, lang="hi"))

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE, quality=95)
    print(f"✅ Professional Thumbnail Created: {THUMBNAIL_FILE.name}")
    return THUMBNAIL_FILE

async def generate_narration(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
    await comm.save(str(AUDIO_FILE))
    print(f"✅ Generated Hindi Audio Narration: {AUDIO_FILE.name}")

def main():
    print("=" * 65)
    print("🎥 PROFESSIONAL TV NEWS BROADCAST GENERATOR & UPLOADER")
    print("=" * 65)

    # 1. Fetch Top Article
    articles = fetch_news(limit_per_category=1)
    if not articles:
        print("❌ No news articles found!")
        return

    top_art = articles[0]
    print(f"📰 Article Selected: [{top_art.category}] '{top_art.title}'")

    # 2. Fetch Real Press Photo
    out_photo = BASE_DIR / "assets" / "pro_tv_photo.jpg"
    asset = VisualAssetManager.get_visual_asset(
        headline=top_art.title,
        category=top_art.category,
        output_path=out_photo,
        article_url=top_art.link
    )
    print(f"📸 Real Photo Asset: {asset.file_path} | Source: {asset.source_name}")

    clean_raw_title = sanitize_text(top_art.title)
    
    # 3. Dynamic Hindi Headline & Takeaway Translation via LLM/RSS Engine
    from services.rss_service import get_dynamic_hindi_news_data
    hindi_data = get_dynamic_hindi_news_data(clean_raw_title, top_art.category)

    hindi_headline = hindi_data.get("main_headline") or clean_raw_title
    hindi_takeaway = (hindi_data.get("sub_takeaways") or [clean_raw_title])[0].lstrip("• ").strip()
    ticker_items = hindi_data.get("ticker_headlines") or [hindi_headline]
    ticker_text = " | ".join(ticker_items)

    print(f"🇮🇳 Devanagari Hindi Headline: {hindi_headline}")
    print(f"📌 Devanagari Hindi Sub-Text: {hindi_takeaway}")

    # 4. Create Smart Hindi TV Anchor Narration Script
    script_text = (
        f"नमस्कार! AI-NewsTube की इस विशेष टीवी न्यूज़ बुलेटिन में आपका स्वागत है। "
        f"आज की सबसे बड़ी और महत्वपूर्ण ख़बर: {hindi_headline}। "
        f"{hindi_takeaway}। "
        f"मामले की गंभीरता को देखते हुए संबंधित विभागों को हाई अलर्ट पर रखा गया है और स्थिति पर लगातार नज़र रखी जा रही है। "
        f"देश और दुनिया की ताज़ा ख़बरों और हर ब्रेकिंग अपडेट के लिए जुड़े रहिए AI-NewsTube के साथ। धन्यवाद!"
    )
    asyncio.run(generate_narration(script_text))

    # 5. Create High-CTR Thumbnail with Hindi Headline
    render_pro_thumbnail(hindi_headline, top_art.category, asset.file_path)

    # 6. Render Video (ProTVEngine - 100% Devanagari Hindi, Solid Banners, Real Photos)
    print("🎬 Rendering Professional TV Broadcast Video (100% Devanagari Hindi, Real Photos)...")
    ProTVEngine.render_pro_tv_video(
        headline=hindi_headline,
        category=top_art.category,
        photo_paths=[asset.file_path],
        photo_credits=[asset.on_screen_credit],
        audio_path=str(AUDIO_FILE),
        output_path=VIDEO_FILE,
        sub_text=hindi_takeaway[:90],
        ticker_text=f"🔥 विशेष कवरेज: {hindi_headline} | {ticker_text}"
    )

    # 6. Upload to YouTube
    print("\n📤 Uploading Professional TV Broadcast Video to YouTube...")
    video_title = f"{clean_title[:75]} 📰 TV News Special | AI-NewsTube"
    description = (
        f"Professional TV News Coverage - {clean_title}\n\n"
        f"देखिए आज की इस बड़ी ख़बर की पूरी विस्तृत रिपोर्ट और ग्राउंड अपडेट AI-NewsTube पर।\n\n"
        f"Category: {top_art.category.upper()}\n"
        f"Headline: {clean_title}\n\n"
        "#TodayNews #HindiNews #BreakingNews #TVNews #AI_NewsTube"
    )

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=video_title,
        description=description,
        category_id="25",
        tags=["TV News", "Today News", "Breaking News", "Hindi News", "AI NewsTube"],
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! PROFESSIONAL TV BROADCAST VIDEO PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()
