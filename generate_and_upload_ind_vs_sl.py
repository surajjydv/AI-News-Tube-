"""
generate_and_upload_ind_vs_sl.py
=================================
Renders a 25-second IND vs SL Cricket Match news video, generates a custom thumbnail,
and uploads it live to YouTube with title, description, and tags via YouTube Data API v3.
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# Output Paths
AUDIO_FILE = BASE_DIR / "assets" / "ind_vs_sl_audio.mp3"
FRAME_FILE = BASE_DIR / "assets" / "ind_vs_sl_frame.jpg"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "ind_vs_sl_thumbnail.jpg"
VIDEO_FILE = BASE_DIR / "videos" / "ind_vs_sl_match_update.mp4"

# News Script
HEADLINE_HINDI = "IND vs SL: भारत बनाम श्रीलंका महामुकाबला आज, टीम इंडिया जीत के लिए तैयार!"
SCRIPT_TEXT = (
    "नमस्कार! AI-NewsTube की स्पोर्ट्स बुलेटिन में आपका स्वागत है। "
    "आज भारत और श्रीलंका के बीच रोमांचक महामुकाबला खेला जा रहा है। "
    "भारतीय कप्तान और स्टार खिलाड़ियों की नजरें आज शानदार प्रदर्शन और बड़ी जीत दर्ज करने पर होंगी। "
    "क्रिकेट फैंस में इस मुकाबले को लेकर भारी उत्साह देखा जा रहा है। "
    "ताज़ा अपडेट्स और हाइलाइट्स के लिए देखते रहिए AI-NewsTube!"
)

# Colors
NAVY = (10, 25, 47)
GOLD = (255, 193, 7)
RED = (220, 38, 38)
WHITE = (255, 255, 255)
BLUE = (30, 64, 175)
DARK_BLUE = (15, 23, 42)

def get_hindi_font(size: int):
    font_paths = [
        "C:\\Windows\\Fonts\\Nirmala.ttf",
        "C:\\Windows\\Fonts\\NirmalaB.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_graphics_frame(width=1920, height=1080) -> Path:
    """Creates a broadcast TV news frame for IND vs SL match update."""
    img = Image.new("RGB", (width, height), DARK_BLUE)
    draw = ImageDraw.Draw(img)

    # 1. Background Gradient / Header
    for y in range(0, 300):
        r = int(10 + (20 * y / 300))
        g = int(25 + (40 * y / 300))
        b = int(47 + (100 * y / 300))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Center Vs Banner Background
    draw.rectangle([100, 220, width - 100, 750], fill=(20, 30, 60), outline=GOLD, width=3)
    
    # 2. Team Badges / Text
    font_xl = get_hindi_font(75)
    font_l = get_hindi_font(55)
    font_m = get_hindi_font(38)
    font_s = get_hindi_font(28)

    # Top Header Pill
    draw.rectangle([0, 0, width, 90], fill=(15, 23, 42))
    draw.rectangle([50, 20, 250, 70], fill=RED)
    draw.text((70, 30), "LIVE SPORTS", fill=WHITE, font=font_m)
    draw.text((width - 320, 30), "AI-NEWSTUBE LIVE", fill=GOLD, font=font_m)

    # Match Cards
    # IND Card
    draw.rectangle([160, 280, 780, 680], fill=BLUE, outline=GOLD, width=4)
    draw.text((220, 340), "INDIA", fill=WHITE, font=font_xl)
    draw.text((220, 440), "TEAM INDIA", fill=GOLD, font=font_l)
    draw.text((220, 530), "🏏 Form: WWW", fill=WHITE, font=font_m)

    # VS Center Badge
    draw.ellipse([880, 410, 1040, 570], fill=RED, outline=GOLD, width=4)
    draw.text((920, 455), "VS", fill=WHITE, font=font_xl)

    # SL Card
    draw.rectangle([1140, 280, 1760, 680], fill=(15, 76, 129), outline=GOLD, width=4)
    draw.text((1200, 340), "SRI LANKA", fill=WHITE, font=font_xl)
    draw.text((1200, 440), "LANKAN LIONS", fill=GOLD, font=font_l)
    draw.text((1200, 530), "🏏 Form: WLW", fill=WHITE, font=font_m)

    # 3. Lower Third Banner (News Headline)
    draw.rectangle([0, 800, width, 970], fill=(180, 0, 0))
    draw.rectangle([0, 790, width, 800], fill=GOLD)
    draw.rectangle([0, 970, width, 980], fill=GOLD)
    
    # Headline Text
    draw.text((80, 840), HEADLINE_HINDI, fill=WHITE, font=font_l)

    # Ticker Bar
    draw.rectangle([0, 980, width, 1080], fill=(10, 15, 30))
    ticker_text = "🔥 SPORTS UPDATE: IND vs SL CRICKET MATCH TODAY | MATCH STARTS AT 7:00 PM IST | AI-NEWSTUBE"
    draw.text((50, 1010), ticker_text, fill=GOLD, font=font_m)

    FRAME_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(FRAME_FILE)
    print(f"✅ Created Broadcast Frame: {FRAME_FILE.name}")
    return FRAME_FILE

def create_youtube_thumbnail() -> Path:
    """Creates a high-impact YouTube Thumbnail (1280x720)."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), DARK_BLUE)
    draw = ImageDraw.Draw(img)

    # Background halves (Blue for India, Dark Blue for SL)
    draw.polygon([(0,0), (680,0), (600,h), (0,h)], fill=(15, 52, 130))
    draw.polygon([(680,0), (w,0), (w,h), (600,h)], fill=(10, 20, 40))
    draw.line([(680,0), (600,h)], fill=GOLD, width=8)

    font_xl = get_hindi_font(60)
    font_l = get_hindi_font(48)
    font_m = get_hindi_font(36)

    # Badges
    # RED Top Banner
    draw.rectangle([40, 30, 420, 95], fill=RED)
    draw.text((60, 42), "🔥 आज का महामुकाबला", fill=WHITE, font=font_m)

    # Teams Text
    draw.text((60, 160), "INDIA", fill=GOLD, font=font_xl)
    draw.text((60, 240), "vs SRI LANKA", fill=WHITE, font=font_l)

    # Big Impact Hindi Text Box
    draw.rectangle([40, 450, w - 40, 640], fill=(220, 38, 38), outline=GOLD, width=4)
    draw.text((70, 480), "IND vs SL: कौन जीतेगा आज का मैच?", fill=WHITE, font=font_xl)
    draw.text((70, 560), "भारत बनाम श्रीलंका | Live Score & Updates", fill=GOLD, font=font_m)

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE)
    print(f"✅ Created YouTube Thumbnail: {THUMBNAIL_FILE.name}")
    return THUMBNAIL_FILE

async def generate_audio():
    """Generates Hindi TTS Audio using edge-tts."""
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(SCRIPT_TEXT, voice="hi-IN-SwaraNeural")
    await communicate.save(str(AUDIO_FILE))
    print(f"✅ Generated Hindi Audio: {AUDIO_FILE.name}")

def render_video(duration_sec: float) -> Path:
    """Renders 1080p MP4 video combining image frame and audio."""
    VIDEO_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate image clip repeated for total duration
    fps = 25
    num_frames = int(duration_sec * fps) + fps # 1 second extra buffer
    
    clip = ImageSequenceClip([str(FRAME_FILE)] * num_frames, fps=fps)
    audio = AudioFileClip(str(AUDIO_FILE))
    
    final_clip = clip.with_audio(audio)
    final_clip.write_videofile(
        str(VIDEO_FILE),
        codec="libx264",
        audio_codec="aac",
        fps=fps
    )
    print(f"✅ Video Rendered Successfully: {VIDEO_FILE.name}")
    return VIDEO_FILE

def main():
    print("🚀 STEP 1: Creating Broadcast Frame & Thumbnail...")
    create_graphics_frame()
    create_youtube_thumbnail()

    print("🎙️ STEP 2: Generating Hindi Audio...")
    asyncio.run(generate_audio())

    # Get Audio Duration
    audio_clip = AudioFileClip(str(AUDIO_FILE))
    duration = audio_clip.duration
    audio_clip.close()

    print(f"🎬 STEP 3: Rendering Video ({duration:.1f} seconds)...")
    render_video(duration)

    # STEP 4: YouTube Upload
    print("📤 STEP 4: Uploading Video to YouTube...")
    title = "IND vs SL Today Match Update 🏏 भारत बनाम श्रीलंका महामुकाबला | India vs Sri Lanka Highlights"
    description = (
        "IND vs SL Today Match Update: भारत बनाम श्रीलंका आज का महामुकाबला!\n\n"
        "भारतीय क्रिकेट टीम और श्रीलंका के बीच रोमांचक मुकाबला। "
        "मैच की ताज़ा ख़बरें, प्लेइंग 11 और ताज़ा अपडेट्स देखें AI-NewsTube पर।\n\n"
        "#INDvsSL #IndiavsSriLanka #CricketNews #HindiNews #TeamIndia #NewsTube #Shorts"
    )
    tags = [
        "IND vs SL", "India vs Sri Lanka", "IND vs SL Today Match",
        "Cricket News", "Team India", "Rohit Sharma", "Virat Kohli",
        "Hindi News", "AI NewsTube", "Sports Bulletin"
    ]

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=title,
        description=description,
        category_id="17", # Sports category
        tags=tags,
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Video & Thumbnail Uploaded to YouTube!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 60)

if __name__ == "__main__":
    main()
