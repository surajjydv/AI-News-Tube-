"""
scripts/generate_sports_bulletin.py
====================================
Generates a complete Full HD (1080p) Sports Category News Bulletin video.
Features:
- Category: SPORTS (खेल समाचार)
- 100% Real Sports Action Photography (Cricket / Stadium / Trophy / Match - NO AI images)
- Saral Hindi Neural Voiceover
- High-level 3D Broadcast UI with Live Sports Ticker & Sports Highlights Side Cards
"""

import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.settings import ASSETS_DIR, VIDEOS_DIR, VOICE_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from agents.graphics_agent import render_tv_broadcast_frame, fetch_news_photo
from utils.logger import logger

OUTPUT_VIDEO = VIDEOS_DIR / "sports_news_bulletin_1080p.mp4"
SPORTS_PHOTO = ASSETS_DIR / "real_sports_photo.jpg"

# Complete Sports Saral Hindi News Script
SPORTS_SCRIPT_TEXT = (
    "नमस्कार! खेल जगत की सबसे बड़ी और धमाकेदार ख़बर में आपका स्वागत है। "
    "T20 वर्ल्ड कप के महामुकाबले में भारतीय क्रिकेट टीम ने शानदार प्रदर्शन करते हुए ऐतिहासिक जीत हासिल कर ली है। "
    "कप्तान रोहित शर्मा की तूफानी बल्लेबाजी और गेंदबाजों के बेहतरीन प्रदर्शन के दम पर टीम इंडिया ने विरोधी टीम को पछाड़ दिया। "
    "इस शानदार जीत के साथ ही भारत ने सेमीफाइनल में अपनी जगह पक्की कर ली है। "
    "खेल जगत की हर ताज़ा और लाइव अपडेट के लिए बने रहें हमारे साथ।"
)

SPORTS_HEADLINE = "T20 वर्ल्ड कप: भारतीय टीम की धमाकेदार ऐतिहासिक जीत, सेमीफाइनल में बनाई जगह"

SPORTS_TICKER_ITEMS = [
    "🏆 T20 वर्ल्ड कप: भारत ने दर्ज की ऐतिहासिक जीत, सेमीफाइनल में पक्की की जगह",
    "💥 कप्तान रोहित शर्मा की तूफानी पारी, 41 गेंदों में बनाए 92 रन",
    "🔥 भारतीय गेंदबाजों का कहर: आखिरी ओवरों में पलटा मैच का रुख",
    "🇮🇳 देश भर में जश्न का माहौल: क्रिकेट प्रशंसकों में भारी उत्साह",
    "⚡ AI-NewsTube Sports: खेल जगत की सबसे तेज़ और सटीक ख़बरें"
]

SPORTS_QUICK_CARDS = [
    "[ऐतिहासिक जीत]\nT20 वर्ल्ड कप में\nभारत का परचम",
    "[कप्तान की पारी]\nरोहित शर्मा का\nतूफानी 92 रन",
    "[सेमीफाइनल एंट्री]\nशानदार प्रदर्शन से\nबनाई जगह"
]


def fetch_real_sports_photo() -> Path:
    """Fetches 100% Real Sports Photography (Cricket / Stadium / Match action - NO AI)."""
    logger.info("  📸 Step 1: Fetching 100% Real Sports Photography (NO AI images)...")
    sports_keywords = ["cricket stadium match", "cricket trophy team india", "stadium crowd sports"]

    for idx, kw in enumerate(sports_keywords, start=1):
        if fetch_news_photo(kw, SPORTS_PHOTO, idx):
            logger.info(f"  ✅ Real Sports Photo fetched: {SPORTS_PHOTO.name}")
            return SPORTS_PHOTO

    # Fallback to visual research photos
    pip_files = sorted(list(ASSETS_DIR.glob("pip_photo_*.jpg")))
    if pip_files:
        return pip_files[0]
    return SPORTS_PHOTO


def generate_sports_voiceover() -> Path:
    """Generates Saral Hindi voiceover using Voice Agent."""
    logger.info("  🎙️ Step 2: Synthesizing Sports Bulletin Saral Hindi voiceover...")
    script_obj = GeneratedScript(
        topic_title="T20 वर्ल्ड कप भारत जीत",
        category="SPORTS",
        script_text=SPORTS_SCRIPT_TEXT,
        word_count=len(SPORTS_SCRIPT_TEXT.split())
    )
    res_script = voice_agent(script_obj)
    if res_script.audio_path and Path(res_script.audio_path).exists():
        logger.info(f"  ✅ Voiceover generated: {res_script.audio_path}")
        return Path(res_script.audio_path)
    return None


def render_sports_bulletin_video(audio_file: Path, photo_file: Path) -> Path:
    """Composites and renders 1080p MP4 Sports News Bulletin video."""
    logger.info("  🎬 Step 3: Compositing 1080p MP4 Sports Broadcast Video...")

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
        target_duration = min(35.0, max(25.0, audio_clip.duration))

    fps = 24

    def make_frame(t):
        frame_img = render_tv_broadcast_frame(
            headline_text=SPORTS_HEADLINE,
            news_photo_path=str(photo_file) if photo_file and photo_file.exists() else None,
            global_t=t,
            category="SPORTS",
            ticker_headlines=SPORTS_TICKER_ITEMS,
            quick_cards=SPORTS_QUICK_CARDS
        )
        return __import__("numpy").array(frame_img)

    video = VideoClip(make_frame, duration=target_duration)

    if audio_clip:
        try:
            video = video.with_audio(audio_clip)
        except Exception:
            try:
                video.audio = audio_clip
            except Exception:
                pass

    logger.info(f"  🎥 Rendering {target_duration:.1f}s Sports Broadcast Video @ {fps} FPS...")
    video.write_videofile(
        str(OUTPUT_VIDEO),
        fps=fps,
        codec="libx264",
        audio_codec="aac" if audio_clip else None,
        threads=4
    )
    logger.info(f"  ✅ Sports News Bulletin MP4 Generated: {OUTPUT_VIDEO.name} ({OUTPUT_VIDEO.stat().st_size / 1024 / 1024:.2f} MB)")
    return OUTPUT_VIDEO


def main():
    print("=" * 65)
    print("🏏 AI-NewsTube — Full Sports News Bulletin Generator (100% Real Media)")
    print("=" * 65)

    photo_path = fetch_real_sports_photo()
    voice_path = generate_sports_voiceover()
    out_video  = render_sports_bulletin_video(voice_path, photo_path)

    print("\n" + "=" * 65)
    print("🎉 SPORTS NEWS BULLETIN GENERATED SUCCESSFULLY!")
    print(f"  🎥 File Path : {out_video}")
    print(f"  📊 File Size : {out_video.stat().st_size / 1024 / 1024:.2f} MB")
    print("=" * 65)


if __name__ == "__main__":
    main()
