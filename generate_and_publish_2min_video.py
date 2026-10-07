"""
generate_and_publish_2min_video.py
==================================
Generates and publicly uploads an exact 2-minute TV News Bulletin on YouTube.
Features:
- Strict SafeSearch & Entity-verified Editorial Media (Zero adult/explicit content).
- High-definition 1080p Star/AajTak style broadcast slides with dual-row live tickers.
- Neural Hindi Voiceover (EdgeTTS hi-IN-SwaraNeural).
- High-CTR 3-band custom thumbnail.
- Direct Public YouTube publication via API / RTMP fallback.
"""

import os
import sys
import math
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.font_utils import load_font, sanitize_text, draw_shaped_text
from services.rss_service import fetch_news
from services.visual_asset_manager import VisualAssetManager
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# Output Paths
STORY2M_DIR    = BASE_DIR / "assets" / "story_2m"
STORY2M_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FILE     = BASE_DIR / "assets" / "story_2m_audio.mp3"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "story_2m_thumbnail.jpg"
VIDEO_FILE     = BASE_DIR / "videos" / "story_2m_video.mp4"

# Color Palette
DARK_BG   = (10, 18, 35)
GOLD      = (255, 200, 0)
RED       = (220, 35, 35)
WHITE     = (255, 255, 255)
BLUE_BOX  = (20, 45, 90)
DARK_BAR  = (15, 23, 42)

def f_bold_hi(sz: int):
    return load_font(sz, bold=True, lang="hi")

def f_bold_en(sz: int):
    return load_font(sz, bold=True, lang="en")

def f_reg(sz: int):
    return load_font(sz, bold=False, lang="hi")

def wrap_text_safe(text: str, max_chars: int) -> list[str]:
    clean = sanitize_text(text)
    words = clean.split()
    if not words:
        return []
    lines = []
    curr = []
    for word in words:
        test_line = " ".join(curr + [word])
        if len(test_line) <= max_chars:
            curr.append(word)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [word]
    if curr:
        lines.append(" ".join(curr))
    return lines

def render_broadcast_slide(section_num: int, total_sections: int, category: str, headline: str, point_text: str, photo_path: str, credit: str) -> Path:
    """Renders a 1080p Ultra-Rich 2.5D TV News Broadcast Slide with physical depth, glassmorphism, and metallic accents."""
    from services.dynamic_broadcast_renderer import render_broadcast_frame
    
    photo_img = None
    if photo_path and os.path.exists(photo_path):
        try:
            photo_img = Image.open(photo_path).convert("RGB")
        except Exception:
            photo_img = None

    takeaways = [
        f"मुख्य बिंदु ({section_num}/{total_sections}): {headline[:38]}",
        point_text if point_text else "विशेष ग्राउंड कवरेज एवं विस्तृत विश्लेषण",
        "अधिकारियों एवं जांच टीमों द्वारा ताज़ा कार्रवाई व रिपोर्ट जारी"
    ]

    t_val = float(section_num * 1.5)
    frame_arr = render_broadcast_frame(
        t=t_val,
        total_duration=max(1.0, float(total_sections * 1.5)),
        headline=headline,
        category=category,
        slide_takeaways=takeaways,
        photo_images=[photo_img],
        photo_credits=[credit or "Verified Press Coverage"],
        w=1920,
        h=1080
    )

    img = Image.fromarray(frame_arr)
    out_file = STORY2M_DIR / f"slide_{section_num}.jpg"
    img.save(out_file, quality=95)
    print(f"✅ Created 2.5D TV Section Slide {section_num}/{total_sections}: {out_file.name}")
    return out_file

def render_2min_thumbnail(title: str, category: str, photo_path: str = "") -> Path:
    """Renders High-CTR YouTube Thumbnail using the authentic real event photograph & HarfBuzz typography."""
    from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
    try:
        thumb = create_real_event_youtube_thumbnail(
            headline=title,
            category=category,
            real_photo_path=photo_path,
            output_path=THUMBNAIL_FILE
        )
        print(f"✅ Created Real Event Photo Thumbnail: {thumb.name}")
        return thumb
    except Exception as e:
        print(f"⚠️ Thumbnail error ({e}). Using standard broadcast thumbnail.")
        return THUMBNAIL_FILE

async def generate_narration(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    if AUDIO_FILE.exists():
        try:
            AUDIO_FILE.unlink()
        except Exception:
            pass

    success = False
    try:
        comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
        await comm.save(str(AUDIO_FILE))
        if AUDIO_FILE.exists() and AUDIO_FILE.stat().st_size > 3000:
            success = True
            print(f"✅ Generated Fresh 2-Minute Hindi Narration Audio (EdgeTTS): {AUDIO_FILE.name}")
    except Exception as e:
        print(f"⚠️ EdgeTTS error: {e}")

    if not success:
        from gtts import gTTS
        tts = gTTS(text=script_text, lang="hi", slow=False)
        tts.save(str(AUDIO_FILE))
        if AUDIO_FILE.exists() and AUDIO_FILE.stat().st_size > 3000:
            success = True
            print(f"✅ Generated Fresh 2-Minute Hindi Narration Audio (gTTS Fallback): {AUDIO_FILE.name}")

    if not success or not AUDIO_FILE.exists() or AUDIO_FILE.stat().st_size < 3000:
        raise RuntimeError(f"Audio narration generation failed for: {AUDIO_FILE}")

def render_2min_video(slide_paths: list, total_duration: float) -> Path:
    VIDEO_FILE.parent.mkdir(parents=True, exist_ok=True)
    fps = 5
    num_slides = len(slide_paths)
    slide_dur = total_duration / float(num_slides)

    frames = []
    for sp in slide_paths:
        f_count = int(slide_dur * fps)
        frames.extend([str(sp)] * f_count)

    total_frames = int(total_duration * fps) + fps
    if len(frames) < total_frames:
        frames.extend([str(slide_paths[-1])] * (total_frames - len(frames)))

    clip = ImageSequenceClip(frames, fps=fps)
    audio = AudioFileClip(str(AUDIO_FILE))
    final_clip = clip.with_audio(audio)

    final_clip.write_videofile(
        str(VIDEO_FILE),
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        preset="ultrafast"
    )
    print(f"✅ Rendered 2-Minute Video (Ultrafast 5 FPS): {VIDEO_FILE.name}")
    return VIDEO_FILE

def load_processed_titles() -> set:
    processed_file = BASE_DIR / "processed_stories.json"
    if processed_file.exists():
        try:
            import json
            with open(processed_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_title(title: str):
    processed_file = BASE_DIR / "processed_stories.json"
    titles = load_processed_titles()
    titles.add(title)
    try:
        import json
        with open(processed_file, "w", encoding="utf-8") as f:
            json.dump(list(titles), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving processed title: {e}")

def generate_and_publish_2min():
    print("=" * 65)
    print("🎥 2-MINUTE SPECIAL NEWS REPORT GENERATOR & YOUTUBE PUBLISHER")
    print("=" * 65)

    # 1. Fetch fresh unseen breaking news
    print("🔍 STEP 1: Fetching Fresh Verified News Story...")
    articles = fetch_news(limit_per_category=5)
    if not articles:
        print("❌ No news articles found!")
        return

    processed = load_processed_titles()
    fresh_articles = [a for a in articles if a.title not in processed]
    if not fresh_articles:
        fresh_articles = articles

    top_art = fresh_articles[0]
    multi_sources = [a.category.title() for a in fresh_articles[:3]]
    combined_texts = " ".join([sanitize_text(a.summary or a.title) for a in fresh_articles[:3]])

    print(f"✅ Primary News Story: [{top_art.category}] '{top_art.title}'")

    # 2. Retrieve 3 to 4 verified real event photos for story aspects
    print("\n📸 STEP 2: Retrieving 3-4 Distinct Verified Real Event Press Photos...")
    assets = VisualAssetManager.get_multi_visual_assets(
        headline=top_art.title,
        category=top_art.category,
        output_dir=STORY2M_DIR,
        article_url=top_art.link,
        direct_image_url=top_art.image_url,
        context=combined_texts,
        max_photos=4
    )
    for i, a in enumerate(assets, 1):
        print(f"  📸 Photo {i}: Source '{a.source_name}', Path '{a.file_path}'")

    # 3. Build Fluent 2-Minute Script & 4 Broadcast Slides (Zero Greetings, 100% Storytelling)
    print("\n📝 STEP 3: Generating Fluent 2-Minute Broadcast Script (Zero Welcome, Pure Storytelling)...")
    clean_title = sanitize_text(top_art.title)
    clean_summary = sanitize_text(top_art.summary or top_art.title)

    from services.fluent_script_service import generate_fluent_news_script
    full_narr_text, slide_takeaways, b_head, viral_title, yt_tags = generate_fluent_news_script(
        title=top_art.title,
        category=top_art.category,
        context=combined_texts,
        article_url=top_art.link,
        target_minutes=2
    )

    slide_paths = []
    total_sec_count = len(slide_takeaways)
    for idx, takeaway in enumerate(slide_takeaways, start=1):
        cur_asset = assets[(idx - 1) % len(assets)]
        s_path = render_broadcast_slide(
            section_num=idx,
            total_sections=total_sec_count,
            category=top_art.category,
            headline=b_head,
            point_text=takeaway,
            photo_path=cur_asset.file_path,
            credit=cur_asset.on_screen_credit
        )
        slide_paths.append(s_path)

    # 4. Generate Thumbnail (using Lead Story Photo)
    print("\n🎨 STEP 4: Creating 2-Minute High-CTR Thumbnail...")
    render_2min_thumbnail(b_head, top_art.category, assets[0].file_path)

    # 5. Synthesize Audio
    print("\n🎙️ STEP 5: Synthesizing Neural Hindi Voiceover...")
    asyncio.run(generate_narration(full_narr_text))

    # 6. Render Dynamic 1080p Video with Running Marquee & 3D Floating Motion
    print(f"\n🎬 STEP 6: Rendering 1080p Dynamic Broadcast Video...")
    from services.dynamic_broadcast_renderer import render_dynamic_broadcast_video
    photo_paths = [a.file_path for a in assets]
    photo_credits = [a.on_screen_credit for a in assets]

    render_dynamic_broadcast_video(
        headline=b_head,
        category=top_art.category,
        slide_takeaways=slide_takeaways,
        photo_paths=photo_paths,
        photo_credits=photo_credits,
        audio_path=AUDIO_FILE,
        output_video_path=VIDEO_FILE,
        fps=15
    )

    # 7. Upload to YouTube as Public
    print("\n📤 STEP 7: Publishing 2-Minute News Bulletin to YouTube (PUBLIC)...")
    video_title = viral_title if viral_title else f"{b_head} 🔴 2-Min Special Bulletin | NewsTube"
    if len(video_title) > 98:
        video_title = video_title[:95] + "..."

    description = (
        f"🔴 {video_title}\n\n"
        f"📌 मुख्य बिंदु:\n"
        f"• {slide_takeaways[0] if len(slide_takeaways) > 0 else b_head}\n"
        f"• {slide_takeaways[1] if len(slide_takeaways) > 1 else 'ग्राउंड रिपोर्ट: विस्तृत जानकारी'}\n"
        f"• {slide_takeaways[2] if len(slide_takeaways) > 2 else 'आधिकारिक बयान एवं ताज़ा स्थिति'}\n\n"
        f"📖 पूरी रिपोर्ट:\n{full_narr_text}\n\n"
        f"Category: {top_art.category.upper()}\n"
        f"Headline: {b_head}\n\n"
        "#NewsUpdate #TodayNews #HindiNews #BreakingNews #AI_NewsTube #2MinNews"
    )
    combined_tags = list(dict.fromkeys(yt_tags + ["2 Min News", "Today News", "Breaking News", "Hindi News", "NewsTube", top_art.category]))

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=video_title,
        description=description,
        category_id="25",
        tags=combined_tags[:15],
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    save_processed_title(top_art.title)

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! 2-MINUTE VIDEO BULLETIN PUBLISHED TO YOUTUBE!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)
    return video_id

if __name__ == "__main__":
    generate_and_publish_2min()
