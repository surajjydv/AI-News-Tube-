"""
generate_and_upload_5min_story.py
=================================
Generates and uploads a 5-minute Broadcast Video & High-CTR Thumbnail on a major trending news story.
Utilizes real event photo scraping, entity relevance checks, HTML-sanitized text, and neural Hindi narration.
"""

import os
import sys
import math
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.font_utils import load_font, sanitize_text
from services.rss_service import fetch_news
from services.visual_asset_manager import VisualAssetManager
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# Output Paths
STORY5M_DIR    = BASE_DIR / "assets" / "story_5m"
STORY5M_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FILE     = BASE_DIR / "assets" / "story_5m_audio.mp3"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "story_5m_thumbnail.jpg"
VIDEO_FILE     = BASE_DIR / "videos" / "story_5m_video.mp4"

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
    """Safely wraps text into lines without empty lines or overflow bugs."""
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
        f"à¤®à¥à¤–à¥à¤¯ à¤¬à¤¿à¤‚à¤¦à¥ ({section_num}/{total_sections}): {headline[:38]}",
        point_text if point_text else "à¤µà¤¿à¤¶à¥‡à¤· à¤—à¥à¤°à¤¾à¤‰à¤‚à¤¡ à¤•à¤µà¤°à¥‡à¤œ à¤à¤µà¤‚ à¤µà¤¿à¤¸à¥à¤¤à¥ƒà¤¤ à¤µà¤¿à¤¶à¥à¤²à¥‡à¤·à¤£",
        "à¤…à¤§à¤¿à¤•à¤¾à¤°à¤¿à¤¯à¥‹à¤‚ à¤à¤µà¤‚ à¤œà¤¾à¤‚à¤š à¤Ÿà¥€à¤®à¥‹à¤‚ à¤¦à¥à¤µà¤¾à¤°à¤¾ à¤¤à¤¾à¤œà¤¼à¤¾ à¤•à¤¾à¤°à¥à¤°à¤µà¤¾à¤ˆ à¤µ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ à¤œà¤¾à¤°à¥€"
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
    out_file = STORY5M_DIR / f"slide_{section_num}.jpg"
    img.save(out_file, quality=95)
    print(f"âœ… Created 2.5D TV Section Slide {section_num}/{total_sections}: {out_file.name}")
    return out_file


def render_5min_thumbnail(title: str, category: str, photo_path: str = "") -> Path:
    """Renders High-CTR YouTube Thumbnail using the authentic real event photograph & HarfBuzz typography."""
    from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
    try:
        thumb = create_real_event_youtube_thumbnail(
            headline=title,
            category=category,
            real_photo_path=photo_path,
            output_path=THUMBNAIL_FILE
        )
        print(f"âœ… Created Real Event Photo Thumbnail: {thumb.name}")
        return thumb
    except Exception as e:
        print(f"âš ï¸ Thumbnail error ({e}). Using standard broadcast thumbnail.")
        return THUMBNAIL_FILE

async def generate_narration(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
        await comm.save(str(AUDIO_FILE))
        print(f"âœ… Generated 5-Minute Hindi Narration Audio (EdgeTTS): {AUDIO_FILE.name}")
    except Exception as e:
        print(f"âš ï¸ EdgeTTS temporary network error ({e}); switching to gTTS Hindi voiceover...")
        try:
            from gtts import gTTS
            tts = gTTS(text=script_text, lang="hi", slow=False)
            tts.save(str(AUDIO_FILE))
            print(f"âœ… Generated 5-Minute Hindi Narration Audio (gTTS Fallback): {AUDIO_FILE.name}")
        except Exception as e2:
            print(f"âŒ Audio narration generation failed: {e2}")
            raise e2


def render_5min_video(slide_paths: list, total_duration: float) -> Path:
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
    print(f"âœ… Rendered 5-Minute Video (Ultrafast 5 FPS): {VIDEO_FILE.name}")
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

def main():
    print("=" * 65)
    print("ðŸŽ¥ 5-MINUTE SINGLE STORY MULTI-ARTICLE SPECIAL REPORT GENERATOR & UPLOADER")
    print("=" * 65)

    # 1. Fetch News Articles and filter against processed stories
    print("ðŸ” STEP 1: Fetching Fresh Multi-Source News Articles (Anti-Repetition)...")
    articles = fetch_news(limit_per_category=5)
    if not articles:
        print("âŒ No news articles found!")
        return

    processed = load_processed_titles()
    fresh_articles = [a for a in articles if a.title not in processed]
    if not fresh_articles:
        print("â„¹ï¸ All fetched articles previously processed; using latest fresh headline.")
        fresh_articles = articles

    top_art = fresh_articles[0]
    multi_sources = [a.category.title() for a in fresh_articles[:3]]
    combined_texts = " ".join([sanitize_text(a.summary or a.title) for a in fresh_articles[:3]])

    print(f"âœ… Primary News Story: [{top_art.category}] '{top_art.title}'")
    print(f"ðŸ“° Synthesizing Multi-Source News Articles from: {', '.join(multi_sources)}")


    # 2. Retrieve Real Event Photo (Strict Safety & Filtered Editorial Sources)
    print("\nðŸ“¸ STEP 2: Scrape Real Event Photo (Strict SafeSearch & Verification)...")
    out_photo = STORY5M_DIR / "main_story_real.jpg"
    asset = VisualAssetManager.get_visual_asset(
        headline=top_art.title,
        category=top_art.category,
        output_path=out_photo,
        article_url=top_art.link,
        direct_image_url=top_art.image_url
    )
    print(f"âœ… Photo Asset: Source '{asset.source_name}', Path '{asset.file_path}'")

    # 3. Create Multi-Article Synthesized 5-Minute Hindi Script & 6 Breakdown Sections
    print("\nðŸ“ STEP 3: Creating Multi-Article Synthesized Script & 6 Breakdown Sections...")
    clean_title = sanitize_text(top_art.title)
    clean_summary = sanitize_text(top_art.summary or top_art.title)

    sections = [
        ("à¤®à¥à¤–à¥à¤¯ à¤¸à¤®à¤¾à¤šà¤¾à¤° à¤à¤µà¤‚ à¤¶à¥à¤°à¥à¤†à¤¤", f"à¤¨à¤®à¤¸à¥à¤•à¤¾à¤°! AI-NewsTube à¤•à¥€ 5 à¤®à¤¿à¤¨à¤Ÿ à¤•à¥€ à¤‡à¤¸ à¤µà¤¿à¤¶à¥‡à¤· à¤®à¤²à¥à¤Ÿà¥€-à¤¸à¥‹à¤°à¥à¤¸ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ à¤®à¥‡à¤‚ à¤†à¤ªà¤•à¤¾ à¤¸à¥à¤µà¤¾à¤—à¤¤ à¤¹à¥ˆà¥¤ à¤†à¤œ à¤•à¥€ à¤¸à¤¬à¤¸à¥‡ à¤¬à¤¡à¤¼à¥€ à¤®à¥à¤–à¥à¤¯ à¤–à¤¼à¤¬à¤°: {clean_title}à¥¤ à¤µà¤¿à¤­à¤¿à¤¨à¥à¤¨ à¤ªà¥à¤°à¤®à¥à¤– à¤¸à¤®à¤¾à¤šà¤¾à¤° à¤¸à¥à¤°à¥‹à¤¤à¥‹à¤‚ ({', '.join(multi_sources[:2])}) à¤•à¥‡ à¤…à¤¨à¥à¤¸à¤¾à¤° à¤‡à¤¸ à¤˜à¤Ÿà¤¨à¤¾ à¤¨à¥‡ à¤ªà¥‚à¤°à¥‡ à¤¦à¥‡à¤¶ à¤•à¤¾ à¤§à¥à¤¯à¤¾à¤¨ à¤–à¥€à¤‚à¤šà¤¾ à¤¹à¥ˆà¥¤"),
        ("à¤ªà¥à¤°à¤¥à¤® à¤¸à¥à¤°à¥‹à¤¤ à¤µà¤¿à¤µà¤°à¤£ à¤à¤µà¤‚ à¤—à¥à¤°à¤¾à¤‰à¤‚à¤¡ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ", f"à¤®à¥à¤–à¥à¤¯ à¤¸à¤®à¤¾à¤šà¤¾à¤° à¤à¤œà¥‡à¤‚à¤¸à¥€ {multi_sources[0]} à¤•à¥€ à¤µà¤¿à¤¸à¥à¤¤à¥ƒà¤¤ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ à¤•à¥‡ à¤®à¥à¤¤à¤¾à¤¬à¤¿à¤•, {clean_summary}à¥¤ à¤˜à¤Ÿà¤¨à¤¾ à¤¸à¥à¤¥à¤² à¤ªà¤° à¤®à¥Œà¤œà¥‚à¤¦ à¤ªà¥à¤°à¤¤à¥à¤¯à¤•à¥à¤·à¤¦à¤°à¥à¤¶à¤¿à¤¯à¥‹à¤‚ à¤”à¤° à¤…à¤§à¤¿à¤•à¤¾à¤°à¤¿à¤¯à¥‹à¤‚ à¤¨à¥‡ à¤¸à¥à¤¥à¤¿à¤¤à¤¿ à¤•à¥€ à¤—à¤‚à¤­à¥€à¤°à¤¤à¤¾ à¤•à¥‹ à¤°à¥‡à¤–à¤¾à¤‚à¤•à¤¿à¤¤ à¤•à¤¿à¤¯à¤¾ à¤¹à¥ˆà¥¤"),
        ("à¤¦à¥à¤µà¤¿à¤¤à¥€à¤¯ à¤¸à¥à¤°à¥‹à¤¤ à¤µà¤¿à¤¶à¥à¤²à¥‡à¤·à¤£ à¤à¤µà¤‚ à¤ªà¥à¤°à¤®à¥à¤– à¤†à¤‚à¤•à¤¡à¤¼à¥‡", f"à¤µà¤¹à¥€à¤‚ à¤¦à¥‚à¤¸à¤°à¥‡ à¤ªà¥à¤°à¤®à¥à¤– à¤¸à¤®à¤¾à¤šà¤¾à¤° à¤ªà¤¤à¥à¤° {len(multi_sources) > 1 and multi_sources[1] or 'à¤¨à¥‡à¤¶à¤¨à¤² à¤®à¥€à¤¡à¤¿à¤¯à¤¾'} à¤•à¥€ à¤—à¥à¤°à¤¾à¤‰à¤‚à¤¡ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ à¤•à¥‡ à¤…à¤¨à¥à¤¸à¤¾à¤°, {combined_texts[:220]}à¥¤ à¤¸à¥à¤°à¤•à¥à¤·à¤¾ à¤¬à¤²à¥‹à¤‚ à¤”à¤° à¤ªà¥à¤°à¤¶à¤¾à¤¸à¤¨à¤¿à¤• à¤…à¤§à¤¿à¤•à¤¾à¤°à¤¿à¤¯à¥‹à¤‚ à¤¨à¥‡ à¤¤à¥à¤°à¤‚à¤¤ à¤®à¥Œà¤•à¥‡ à¤ªà¤° à¤ªà¤¹à¥à¤‚à¤šà¤•à¤° à¤°à¤¾à¤¹à¤¤ à¤”à¤° à¤¬à¤šà¤¾à¤µ à¤•à¤¾à¤°à¥à¤¯ à¤¤à¥‡à¤œ à¤•à¤° à¤¦à¤¿à¤¯à¤¾ à¤¹à¥ˆà¥¤"),
        ("à¤¤à¥€à¤¸à¤°à¥‡ à¤¸à¥à¤°à¥‹à¤¤ à¤•à¥€ à¤ªà¥à¤°à¤¤à¤¿à¤•à¥à¤°à¤¿à¤¯à¤¾à¤à¤‚ à¤à¤µà¤‚ à¤¬à¤¯à¤¾à¤¨", f"à¤¤à¥€à¤¸à¤°à¥‡ à¤®à¥€à¤¡à¤¿à¤¯à¤¾ à¤•à¤µà¤°à¥‡à¤œ à¤¸à¥à¤°à¥‹à¤¤ {len(multi_sources) > 2 and multi_sources[2] or 'à¤²à¤¾à¤‡à¤µ à¤…à¤ªà¤¡à¥‡à¤Ÿà¥à¤¸'} à¤•à¥‡ à¤…à¤¨à¥à¤¸à¤¾à¤°, à¤‡à¤¸ à¤ªà¥‚à¤°à¥‡ à¤˜à¤Ÿà¤¨à¤¾à¤•à¥à¤°à¤® à¤ªà¤° à¤¶à¤¾à¤¸à¤¨ à¤”à¤° à¤µà¤¿à¤ªà¤•à¥à¤· à¤•à¥€ à¤“à¤° à¤¸à¥‡ à¤¤à¥€à¤–à¥€ à¤ªà¥à¤°à¤¤à¤¿à¤•à¥à¤°à¤¿à¤¯à¤¾à¤à¤‚ à¤¸à¤¾à¤®à¤¨à¥‡ à¤†à¤ˆ à¤¹à¥ˆà¤‚à¥¤ à¤¸à¤°à¤•à¤¾à¤° à¤¨à¥‡ à¤®à¤¾à¤®à¤²à¥‡ à¤•à¥€ à¤‰à¤šà¥à¤šà¤¸à¥à¤¤à¤°à¥€à¤¯ à¤œà¤¾à¤‚à¤š à¤•à¥‡ à¤†à¤¦à¥‡à¤¶ à¤œà¤¾à¤°à¥€ à¤•à¤° à¤¦à¤¿à¤ à¤¹à¥ˆà¤‚à¥¤"),
        ("à¤®à¤²à¥à¤Ÿà¥€-à¤¸à¥‹à¤°à¥à¤¸ à¤µà¤¿à¤¶à¥à¤²à¥‡à¤·à¤£ à¤à¤µà¤‚ à¤­à¤µà¤¿à¤·à¥à¤¯ à¤ªà¤° à¤…à¤¸à¤°", f"à¤¤à¥€à¤¨à¥‹à¤‚ à¤ªà¥à¤°à¤®à¥à¤– à¤¸à¤®à¤¾à¤šà¤¾à¤° à¤¸à¥à¤°à¥‹à¤¤à¥‹à¤‚ à¤•à¥€ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿà¥‹à¤‚ à¤•à¤¾ à¤¤à¥à¤²à¤¨à¤¾à¤¤à¥à¤®à¤• à¤µà¤¿à¤¶à¥à¤²à¥‡à¤·à¤£ à¤•à¤°à¤¨à¥‡ à¤ªà¤° à¤¯à¤¹ à¤¸à¥à¤ªà¤·à¥à¤Ÿ à¤¹à¥‹à¤¤à¤¾ à¤¹à¥ˆ à¤•à¤¿ à¤‡à¤¸ à¤®à¤¾à¤®à¤²à¥‡ à¤•à¤¾ à¤ªà¥à¤°à¤¶à¤¾à¤¸à¤¨à¤¿à¤• à¤”à¤° à¤¸à¤¾à¤®à¤¾à¤œà¤¿à¤• à¤ªà¥à¤°à¤­à¤¾à¤µ à¤¦à¥‚à¤°à¤—à¤¾à¤®à¥€ à¤¹à¥‹à¤¨à¥‡ à¤µà¤¾à¤²à¤¾ à¤¹à¥ˆà¥¤ à¤­à¤µà¤¿à¤·à¥à¤¯ à¤®à¥‡à¤‚ à¤¸à¥à¤°à¤•à¥à¤·à¤¾ à¤”à¤° à¤¨à¥€à¤¤à¤¿à¤—à¤¤ à¤¬à¤¦à¤²à¤¾à¤µà¥‹à¤‚ à¤ªà¤° à¤œà¥‹à¤° à¤¦à¤¿à¤¯à¤¾ à¤œà¤¾ à¤°à¤¹à¤¾ à¤¹à¥ˆà¥¤"),
        ("à¤¨à¤¿à¤·à¥à¤•à¤°à¥à¤· à¤à¤µà¤‚ à¤²à¤¾à¤‡à¤µ à¤—à¥à¤°à¤¾à¤‰à¤‚à¤¡ à¤…à¤ªà¤¡à¥‡à¤Ÿ", f"AI-NewsTube à¤‡à¤¸ à¤¬à¤¡à¤¼à¥€ à¤–à¤¼à¤¬à¤° à¤¸à¥‡ à¤œà¥à¤¡à¤¼à¥‡ à¤¸à¤­à¥€ à¤¸à¤®à¤¾à¤šà¤¾à¤° à¤¸à¥à¤°à¥‹à¤¤à¥‹à¤‚ à¤•à¥€ à¤ªà¤²-à¤ªà¤² à¤•à¥€ à¤²à¤¾à¤‡à¤µ à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤ªà¤° à¤²à¤—à¤¾à¤¤à¤¾à¤° à¤¨à¤œà¤° à¤¬à¤¨à¤¾à¤ à¤¹à¥à¤ à¤¹à¥ˆà¥¤ à¤¤à¤¾à¤œà¤¼à¤¾ à¤–à¤¼à¤¬à¤°à¥‹à¤‚ à¤”à¤° à¤¨à¤¿à¤·à¥à¤ªà¤•à¥à¤· à¤µà¤¿à¤¶à¥à¤²à¥‡à¤·à¤£ à¤•à¥‡ à¤²à¤¿à¤ à¤œà¥à¤¡à¤¼à¥‡ à¤°à¤¹à¤¿à¤ AI-NewsTube à¤•à¥‡ à¤¸à¤¾à¤¥à¥¤ à¤§à¤¨à¥à¤¯à¤µà¤¾à¤¦!")
    ]

    # 3. Build Fluent 5-Minute Script & Broadcast Slides (Zero Greetings, 100% Storytelling)
    print("\nðŸ“ STEP 3: Generating Fluent 5-Minute Broadcast Script (Zero Welcome, Pure Storytelling)...")
    clean_title = sanitize_text(top_art.title)
    clean_summary = sanitize_text(top_art.summary or top_art.title)

    from services.fluent_script_service import generate_fluent_news_script
    full_narr_text, slide_takeaways, b_head, viral_title, yt_tags = generate_fluent_news_script(
        title=top_art.title,
        category=top_art.category,
        context=combined_texts,
        article_url=top_art.link,
        target_minutes=5
    )

    slide_paths = []
    total_sec_count = len(slide_takeaways)
    for idx, takeaway in enumerate(slide_takeaways, start=1):
        s_path = render_broadcast_slide(
            section_num=idx,
            total_sections=total_sec_count,
            category=top_art.category,
            headline=b_head,
            point_text=takeaway,
            photo_path=asset.file_path,
            credit=asset.on_screen_credit
        )
        slide_paths.append(s_path)

    # 4. Generate Thumbnail
    print("\nðŸŽ¨ STEP 4: Creating High-CTR 3-Band Thumbnail...")
    render_5min_thumbnail(b_head, top_art.category, asset.file_path)

    # 5. Synthesize 5-Minute Audio
    print("\nðŸŽ™ï¸ STEP 5: Synthesizing Hindi Audio Narration...")
    asyncio.run(generate_narration(full_narr_text))

    audio_clip = AudioFileClip(str(AUDIO_FILE))
    duration = audio_clip.duration
    audio_clip.close()

    # 6. Render Video
    print(f"\nðŸŽ¬ STEP 6: Rendering 1080p Video ({duration:.1f} seconds)...")
    render_5min_video(slide_paths, duration)

    # 7. Upload to YouTube
    print("\nðŸ“¤ STEP 7: Uploading 5-Minute Special Report to YouTube...")
    video_title = viral_title if viral_title else f"{b_head} ðŸ“° Special Report | NewsTube"
    if len(video_title) > 98:
        video_title = video_title[:95] + "..."

    description = (
        f"ðŸ”´ {video_title}\n\n"
        f"ðŸ“Œ à¤®à¥à¤–à¥à¤¯ à¤¬à¤¿à¤‚à¤¦à¥:\n"
        f"â€¢ {slide_takeaways[0] if len(slide_takeaways) > 0 else b_head}\n"
        f"â€¢ {slide_takeaways[1] if len(slide_takeaways) > 1 else 'à¤—à¥à¤°à¤¾à¤‰à¤‚à¤¡ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ: à¤µà¤¿à¤¸à¥à¤¤à¥ƒà¤¤ à¤œà¤¾à¤¨à¤•à¤¾à¤°à¥€'}\n"
        f"â€¢ {slide_takeaways[2] if len(slide_takeaways) > 2 else 'à¤†à¤§à¤¿à¤•à¤¾à¤°à¤¿à¤• à¤¬à¤¯à¤¾à¤¨ à¤à¤µà¤‚ à¤¤à¤¾à¤œà¤¼à¤¾ à¤¸à¥à¤¥à¤¿à¤¤à¤¿'}\n\n"
        f"ðŸ“– à¤ªà¥‚à¤°à¥€ à¤°à¤¿à¤ªà¥‹à¤°à¥à¤Ÿ:\n{full_narr_text}\n\n"
        f"Category: {top_art.category.upper()}\n"
        f"Headline: {b_head}\n\n"
        "#SpecialReport #TodayNews #HindiNews #BreakingNews #NewsTube"
    )
    combined_tags = list(dict.fromkeys(yt_tags + ["Special Report", "Today News", "Breaking News", "Hindi News", "NewsTube", top_art.category]))

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=video_title,
        description=description,
        category_id="25",
        tags=combined_tags[:15],
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    # Record title in processed set
    save_processed_title(top_art.title)

    print("\n" + "=" * 65)
    print("ðŸŽ‰ SUCCESS! 5-MINUTE SPECIAL REPORT VIDEO & THUMBNAIL PUBLISHED!")
    print(f"ðŸ”— Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()

