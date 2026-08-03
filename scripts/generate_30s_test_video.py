"""
scripts/generate_30s_test_video.py
================──────────────────
Generates a complete 30-second Full HD (1080p) AI-NewsTube broadcast test video.
Features:
- 30-second total duration (720 frames @ 24 FPS)
- Saral Hindi (80-year-old accessible natural conversational Hindi) neural voiceover
- 3D spatial virtual newsroom studio background with curved LED wall and specular desk
- High-contrast Devanagari Hindi lower-thirds, headline cards, and continuous news ticker
"""

import os
import sys
import time
import asyncio
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure project root is importable
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Fix Windows console UTF-8 output encoding
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.settings import ASSETS_DIR, VIDEOS_DIR, VOICE_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from agents.graphics_agent import render_tv_broadcast_frame
from utils.logger import logger

OUTPUT_VIDEO = VIDEOS_DIR / "test_broadcast_30sec.mp4"
SAMPLE_VOICE_PATH = VOICE_DIR / "test_30sec_hindi_voice.mp3"

# 30-second Saral Hindi news script (accessible to 80-year-old viewers)
HINDI_SCRIPT_TEXT = (
    "नमस्कार! AI-NewsTube की बड़ी ख़बर में आपका स्वागत है। "
    "आज की मुख्य बात यह है कि देश भर के वरिष्ठ नागरिकों और परिवारों के लिए सरकार ने एक नई और आसान सहायता योजना का ऐलान किया है। "
    "इस फैसले से लाखों परिवारों को सीधा आर्थिक लाभ मिलेगा और बैंकिंग सेवाएं अब और भी सरल हो जाएंगी। "
    "आगे की हर मुख्य और साफ़ ख़बर देखने के लिए हमारे चैनल को सब्सक्राइब ज़रूर करें।"
)

HEADLINE_TEXT = "वरिष्ठ नागरिकों और परिवारों के लिए सरकार का बड़ा ऐलान, मिलेगा सीधा आर्थिक लाभ"
TICKER_ITEMS = [
    "सरकार का बड़ा फैसला: बुजुर्गों और परिवारों के लिए नई सहायता योजना",
    "बैंकिंग सेवाएं हुई और भी सरल, सीधे खाते में आएगी मदद",
    "देश भर में खुशी की लहर, लाखों परिवारों को मिलेगा लाभ",
    "AI-NewsTube पर देखें सबसे साफ़ और सच्ची ख़बरें"
]
QUICK_CARDS = [
    "[बड़ी योजना]\nपरिवारों को\nसीधा लाभ",
    "[आर्थिक राहत]\nसरल बैंकिंग\nसुविधा",
    "[जनहित फैसला]\nदेश भर में\nनया ऐलान"
]


def generate_30s_voiceover() -> Path:
    """Generates 30-second Saral Hindi neural voiceover using Voice Agent."""
    logger.info("  🎙️ Step 1: Synthesizing 30-second Saral Hindi neural voiceover...")
    script_obj = GeneratedScript(
        topic_title="वरिष्ठ नागरिक सहायता योजना",
        category="TOP STORIES",
        script_text=HINDI_SCRIPT_TEXT,
        word_count=len(HINDI_SCRIPT_TEXT.split())
    )
    res_script = voice_agent(script_obj)
    if res_script.audio_path and Path(res_script.audio_path).exists():
        logger.info(f"  ✅ Voiceover generated: {res_script.audio_path}")
        return Path(res_script.audio_path)
    return None


def render_30s_broadcast_video(audio_file: Path) -> Path:
    """Composites and renders 30-second 1080p MP4 broadcast video."""
    logger.info("  🎬 Step 2: Compositing 30-second 1080p MP4 broadcast video...")

    try:
        from moviepy import VideoClip, AudioFileClip
    except ImportError:
        from moviepy.video.VideoClip import VideoClip
        from moviepy.audio.AudioFileClip import AudioFileClip

    audio_clip = None
    if audio_file and audio_file.exists():
        try:
            audio_clip = AudioFileClip(str(audio_file))
        except Exception as e:
            logger.warning(f"Could not load audio clip: {e}")

    target_duration = 30.0
    if audio_clip and audio_clip.duration > 5.0:
        target_duration = min(35.0, max(28.0, audio_clip.duration))

    fps = 24
    w, h = 1920, 1080

    # Ensure news photo asset exists — fetch real photo from Pexels
    photo_path = ASSETS_DIR / "test_30s_photo.jpg"
    if photo_path.exists():
        photo_path.unlink()   # force-fresh photo each run

    import requests as _req
    fetched = False

    # SOURCE 1: Pollinations AI — generates realistic news-style photo (free, no key)
    try:
        logger.info("  📸 Generating news photo via Pollinations AI...")
        prompts = [
            "India parliament New Delhi professional news photography",
            "Indian government officials press conference podium news photo",
            "India news broadcast studio professional photograph",
        ]
        for i, prompt in enumerate(prompts):
            encoded = _req.utils.quote(prompt)
            url = (f"https://image.pollinations.ai/prompt/{encoded}"
                   f"?width=1280&height=720&nologo=true&seed={i+10}")
            resp = _req.get(url, timeout=28)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(photo_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"  ✅ Pollinations photo saved ({len(resp.content)//1024}KB)")
                fetched = True
                break
    except Exception as e:
        logger.warning(f"  Pollinations fetch error: {e}")

    # SOURCE 2: Picsum — real photograph (no key needed)
    if not fetched:
        try:
            logger.info("  📸 Fetching real photo from Picsum...")
            resp = _req.get("https://picsum.photos/1280/720.jpg",
                            timeout=12, allow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 20000:
                with open(photo_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"  ✅ Picsum photo saved ({len(resp.content)//1024}KB)")
                fetched = True
        except Exception as e:
            logger.warning(f"  Picsum fetch error: {e}")

    # SOURCE 3: Styled PIL fallback
    if not fetched:
        logger.info("  🎨 Using styled PIL fallback photo...")
        card = Image.new("RGB", (1280, 720), (6, 14, 38))
        pd   = ImageDraw.Draw(card)
        for y_r in range(720):
            t_r = y_r / 720
            pd.line([(0, y_r), (1280, y_r)],
                    fill=(int(6+24*t_r), int(14+20*t_r), int(38+52*t_r)))
        for x_r in range(0, 1280, 80):
            pd.line([(x_r, 0), (x_r, 720)], fill=(20, 38, 80), width=1)
        for y_r in range(0, 720, 80):
            pd.line([(0, y_r), (1280, y_r)], fill=(20, 38, 80), width=1)
        for radius in range(260, 0, -20):
            pd.ellipse(
                [(640-radius, 360-radius), (640+radius, 360+radius)],
                outline=(40, 100, 220), width=1
            )
        pd.rounded_rectangle([(160, 180), (1120, 540)], radius=24,
                             fill=(12, 28, 72), outline=(255, 215, 0), width=4)
        pd.text((260, 290), "AI-NEWSTUBE", fill=(255, 215, 0))
        pd.text((260, 360), "3D Studio  |  24x7 Hindi News", fill=(200, 220, 255))
        card.save(photo_path, "JPEG", quality=92)

    def make_frame(t: float):
        frame_img = render_tv_broadcast_frame(
            headline_text=HEADLINE_TEXT,
            news_photo_path=str(photo_path),
            global_t=t,
            category="बड़ी ख़बर",
            ticker_headlines=TICKER_ITEMS,
            quick_cards=QUICK_CARDS
        )
        return np.array(frame_img)

    video = VideoClip(make_frame, duration=target_duration)
    video = video.with_fps(fps)

    if audio_clip:
        video = video.with_audio(audio_clip)

    OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"  🎥 Rendering {target_duration:.1f}s Full HD 1080p video @ {fps} fps to {OUTPUT_VIDEO.name}...")
    
    video.write_videofile(
        str(OUTPUT_VIDEO),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )

    if audio_clip:
        audio_clip.close()
    video.close()

    logger.info(f"  ✅ 30-Second Broadcast Video Created: {OUTPUT_VIDEO.name} ({OUTPUT_VIDEO.stat().st_size / (1024*1024):.2f} MB)")
    return OUTPUT_VIDEO


def main():
    print("=" * 65)
    print("🚀 AI-NewsTube — 30-Second 1080p Broadcast Video Generator")
    print("=" * 65)

    # 1. Voiceover
    voice_path = generate_30s_voiceover()

    # 2. Render Video
    video_out = render_30s_broadcast_video(voice_path)

    if video_out.exists():
        size_mb = video_out.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 65)
        print("🎉 30-SECOND TEST VIDEO GENERATED SUCCESSFULLY!")
        print(f"  🎥 File Path : {video_out}")
        print(f"  📊 File Size : {size_mb:.2f} MB")
        print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
