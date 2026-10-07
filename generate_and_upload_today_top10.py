"""
generate_and_upload_today_top10.py
==================================
Fetches today's top 10 real news stories, retrieves real event photos via og:image scraper & GNews,
renders a 1080p Top 10 News Bulletin with custom viral thumbnail, and uploads live to YouTube.
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from utils.font_utils import load_font, sanitize_text
from services.rss_service import fetch_news
from services.visual_asset_manager import VisualAssetManager
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# Output Directory
TOP10_DIR = BASE_DIR / "assets" / "top10_today"
TOP10_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FILE     = BASE_DIR / "assets" / "top10_today_audio.mp3"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "top10_today_thumbnail.jpg"
VIDEO_FILE     = BASE_DIR / "videos" / "top10_today_bulletin.mp4"

# Color Palette
DARK_BG   = (10, 18, 35)
GOLD      = (255, 200, 0)
RED       = (220, 35, 35)
WHITE     = (255, 255, 255)
BLUE_BOX  = (20, 45, 90)
DARK_BAR  = (15, 23, 42)
LIGHT_BLUE= (220, 240, 255)

def f_bold(sz: int):
    return load_font(sz, bold=True, lang="hi")

def f_reg(sz: int):
    return load_font(sz, bold=False, lang="hi")

def render_top10_slide(story_num: int, category: str, headline: str, summary: str, photo_path: str, credit: str) -> Path:
    """Renders a 1080p Broadcast Slide for a specific story out of 10."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # 1. Top Header Bar
    draw.rectangle([0, 0, w, 100], fill=DARK_BAR)
    draw.rectangle([60, 20, 380, 80], fill=RED)
    draw.text((85, 33), sanitize_text(f"TOP 10 NEWS • 0{story_num}/10" if story_num < 10 else f"TOP 10 NEWS • {story_num}/10"), fill=WHITE, font=f_bold(30))
    draw.text((w - 420, 33), sanitize_text("AI-NEWSTUBE SPECIAL REPORT"), fill=GOLD, font=f_bold(30))

    # Category Pill
    draw.rectangle([80, 130, 380, 190], fill=(30, 80, 180), outline=GOLD, width=2)
    draw.text((105, 142), sanitize_text(f"📌 {category.upper()}"), fill=WHITE, font=f_bold(32))

    # Real Photo Box (Left side)
    if photo_path and os.path.exists(photo_path):
        try:
            p_img = Image.open(photo_path).convert("RGB").resize((860, 700), Image.Resampling.LANCZOS)
            img.paste(p_img, (80, 220))
            draw.rectangle([80, 220, 940, 920], outline=GOLD, width=4)
            # Photo Credit Overlay
            draw.rectangle([80, 875, 940, 920], fill=(0, 0, 0))
            draw.text((100, 888), sanitize_text(credit or "Source: News Coverage"), fill=WHITE, font=f_reg(22))
        except Exception:
            pass

    # Story Content Box (Right side)
    draw.rectangle([980, 220, 1840, 920], fill=BLUE_BOX, outline=GOLD, width=4)

    # Headline Box
    draw.rectangle([980, 220, 1840, 320], fill=(15, 30, 65))
    
    # Wrap Headline Text
    clean_h = sanitize_text(headline)
    words = clean_h.split()
    h_lines = []
    curr = []
    for word in words:
        curr.append(word)
        if len(" ".join(curr)) > 26:
            h_lines.append(" ".join(curr[:-1]))
            curr = [word]
    if curr:
        h_lines.append(" ".join(curr))

    y_h = 240
    for hl in h_lines[:2]:
        draw.text((1010, y_h), hl, fill=GOLD, font=f_bold(36))
        y_h += 44

    # Summary Text Lines
    clean_s = sanitize_text(summary or headline)
    s_words = clean_s.split()
    s_lines = []
    curr_s = []
    for w_item in s_words:
        curr_s.append(w_item)
        if len(" ".join(curr_s)) > 30:
            s_lines.append(" ".join(curr_s[:-1]))
            curr_s = [w_item]
    if curr_s:
        s_lines.append(" ".join(curr_s))

    y_s = 350
    for sl in s_lines[:7]:
        draw.text((1010, y_s), sl, fill=WHITE, font=f_reg(32))
        y_s += 48

    # Bottom Ticker Bar
    draw.rectangle([0, 960, w, h], fill=DARK_BAR)
    draw.text((60, 995), sanitize_text("🔥 ताज़ा समाचार: आज की 10 बड़ी मुख्य ख़बरें | AI-NewsTube स्पेशल बुलेटिन"), fill=GOLD, font=f_bold(36))

    out_file = TOP10_DIR / f"top10_slide_{story_num}.jpg"
    img.save(out_file)
    print(f"✅ Created Slide {story_num}/10: {out_file.name}")
    return out_file

def render_top10_thumbnail(photo_paths: list) -> Path:
    """Renders a High-CTR 3-Band + 4-Photo Grid Thumbnail."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 1. TOP HEADER SECTION (3 BANDS)
    # Band 1: Red
    draw.rectangle([0, 0, w, 80], fill=(170, 0, 0))
    draw.text((w // 2 - 200, 2), "TOP 10 NEWS TODAY", fill=WHITE, font=f_bold(60))

    # Band 2: Yellow
    draw.rectangle([0, 80, w, 200], fill=(255, 230, 0))
    draw.text((w // 2 - 460, 108), sanitize_text("आज की 10 बड़ी मुख्य खबरें"), fill=(0, 0, 0), font=f_bold(52))

    # Band 3: Dark Blue
    draw.rectangle([0, 200, w, 300], fill=(12, 28, 70))
    draw.text((w // 2 - 460, 222), sanitize_text("देश और दुनिया का पूरा अपडेट एक साथ"), fill=WHITE, font=f_bold(46))

    draw.line([(0, 300), (w, 300)], fill=WHITE, width=5)

    # 2. BOTTOM 4-PHOTO GRID (y: 305 to 720)
    grid_y = 305
    grid_h = h - grid_y
    col_w = (w - 6) // 4 # ~318px wide each

    for idx in range(4):
        x = idx * (col_w + 2)
        p_path = photo_paths[idx] if idx < len(photo_paths) else None
        if p_path and os.path.exists(p_path):
            try:
                p_img = Image.open(p_path).convert("RGB").resize((col_w, grid_h), Image.Resampling.LANCZOS)
                img.paste(p_img, (x, grid_y))
            except Exception:
                draw.rectangle([x, grid_y, x + col_w, h], fill=(20, 40, 80))
        else:
            draw.rectangle([x, grid_y, x + col_w, h], fill=(20, 40, 80))
        
        # White vertical divider
        if idx > 0:
            draw.line([(x, grid_y), (x, h)], fill=WHITE, width=4)

    # Badge Overlay
    draw.rectangle([w - 240, h - 60, w - 15, h - 15], fill=RED, outline=GOLD, width=2)
    draw.text((w - 225, h - 52), "10 BIG STORIES", fill=WHITE, font=f_bold(22))

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE, quality=95)
    print(f"✅ Created Top 10 Thumbnail: {THUMBNAIL_FILE.name}")
    return THUMBNAIL_FILE

async def generate_narration(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
    await comm.save(str(AUDIO_FILE))
    print(f"✅ Generated Hindi Audio Narration: {AUDIO_FILE.name}")

def render_top10_video(slide_paths: list, total_duration: float) -> Path:
    VIDEO_FILE.parent.mkdir(parents=True, exist_ok=True)
    fps = 25
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
        fps=fps
    )
    print(f"✅ Rendered Top 10 Video Bulletin: {VIDEO_FILE.name}")
    return VIDEO_FILE

def main():
    print("=" * 65)
    print("📰 TODAY'S TOP 10 HEADLINE NEWS BULLETIN GENERATOR & UPLOADER")
    print("=" * 65)

    # 1. Fetch 10 Real News Articles
    print("🔍 STEP 1: Fetching Today's 10 Real Trending News Stories...")
    articles = fetch_news(limit_per_category=2)
    top10 = articles[:10]
    
    if not top10:
        print("❌ No news articles found!")
        return

    print(f"✅ Retreived {len(top10)} top news stories across categories.")

    # 2. Retrieve Real News Photos for each story (og:image + GNews + Stock)
    print("\n📸 STEP 2: Fetching Real Event Photos for each story (Tier-1 og:image Scrape)...")
    slide_paths = []
    photo_paths = []
    script_segments = [
        "नमस्कार! AI-NewsTube की आज की 10 बड़ी मुख्य ख़बरों के बुलेटिन में आपका स्वागत है। "
        "आइए जानते हैं देश और दुनिया की आज की 10 सबसे महत्वपूर्ण ख़बरें विस्तार से।"
    ]

    for idx, art in enumerate(top10, start=1):
        out_img = TOP10_DIR / f"story_{idx}_real.jpg"
        print(f"\n[Story {idx}/10] [{art.category}] '{art.title}'")
        
        # Use our new Tier-1 og:image + GNews + Stock fallback asset manager!
        asset = VisualAssetManager.get_visual_asset(
            headline=art.title,
            category=art.category,
            output_path=out_img,
            article_url=art.link
        )
        
        photo_paths.append(asset.file_path)

        # Render Slide
        slide_file = render_top10_slide(
            story_num=idx,
            category=art.category,
            headline=art.title,
            summary=art.summary,
            photo_path=asset.file_path,
            credit=asset.on_screen_credit
        )
        slide_paths.append(slide_file)

        # Add segment text for TTS
        script_segments.append(
            f"ख़बर संख्या {idx}: {art.category} से बड़ी ख़बर। "
            f"{art.title}। {art.summary[:180] if art.summary else ''}"
        )

    script_segments.append(
        "यह थीं आज की 10 बड़ी मुख्य ख़बरें। ताज़ा समाचार और हर अपडेट के लिए देखते रहिए AI-NewsTube। धन्यवाद!"
    )
    full_script_text = " ".join(script_segments)

    # 3. Create High-CTR Thumbnail
    print("\n🎨 STEP 3: Creating High-CTR Viral 3-Band Thumbnail...")
    render_top10_thumbnail(photo_paths)

    # 4. Generate Neural Audio
    print("\n🎙️ STEP 4: Synthesizing Hindi Audio Narration...")
    asyncio.run(generate_narration(full_script_text))

    audio_clip = AudioFileClip(str(AUDIO_FILE))
    duration = audio_clip.duration
    audio_clip.close()

    # 5. Render Video
    print(f"\n🎬 STEP 5: Rendering 1080p Full HD Video ({duration:.1f} sec)...")
    render_top10_video(slide_paths, duration)

    # 6. Upload to YouTube
    print("\n📤 STEP 6: Uploading Top 10 News Bulletin to YouTube...")
    title = "आज की 10 बड़ी मुख्य खबरें 📰 Today Top 10 Headlines News | 10 Big Stories Update"
    description = (
        "Today's Top 10 Headlines News Bulletin - आज की 10 बड़ी मुख्य ख़बरें!\n\n"
        "देखिए देश, दुनिया, खेल, राजनीति और टेक्नोलॉजी की आज की 10 सबसे बड़ी ख़बरें एक साथ AI-NewsTube पर।\n\n"
        "10 Major News Stories:\n" +
        "\n".join([f"{i+1}. [{a.category.upper()}] {a.title}" for i, a in enumerate(top10)]) +
        "\n\n#Top10News #TodayNews #HindiNews #BreakingNews #IndiaNews #NewsTube"
    )
    tags = [
        "Today Top 10 News", "Top 10 Headlines", "Aaj Ki Badi Khabrein",
        "Hindi News", "Breaking News India", "Latest News Today", "AI NewsTube"
    ]

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=title,
        description=description,
        category_id="25", # News & Politics
        tags=tags,
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! TODAY'S TOP 10 NEWS BULLETIN & THUMBNAIL PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()
