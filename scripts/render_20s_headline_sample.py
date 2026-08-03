import os
import sys
import time
import numpy as np
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import VIDEOS_DIR, ASSETS_DIR
from agents.graphics_agent import render_tv_broadcast_frame
from utils.logger import logger

def generate_20s_sample():
    """Generates a 20-second 1080p sample video of the CNN/BBC/Aaj Tak Glassmorphic Headline Card."""
    logger.info("🎬 Rendering 20-Second Sample Video (Glassmorphic Headline Card)...")
    
    headline_text = "भारत और अमेरिका के बीच नया व्यापार समझौता तय, देश को होगा भारी आर्थिक फायदा"
    ticker_items = [
        "सरकार ने किसानों के लिए नई योजना का किया ऐलान",
        "शेयर बाजार में रिकॉर्ड तेजी, सेंसेक्स 600 अंक चढ़ा",
        "भारतीय अंतरिक्ष एजेंसी ने रचा नया इतिहास",
        "मौसम विभाग का उत्तर भारत में भारी बारिश का अलर्ट"
    ]
    quick_cards = [
        "[INDIA]\nव्यापार समझौता\nतय हुआ",
        "[BUSINESS]\nसेंसेक्स 600 अंक\nउछला",
        "[WEATHER]\nउत्तर भारत में\nभारी बारिश",
        "[TECH]\nनई चिप नीति\nलागू हुई"
    ]

    # Render a sample preview photo
    photo_path = ASSETS_DIR / "sample_news_photo.jpg"
    if not photo_path.exists():
        card = Image.new("RGB", (1200, 750), (15, 25, 55))
        card.save(photo_path)

    fps = 24
    duration = 20
    total_frames = fps * duration

    try:
        from moviepy import VideoClip
    except ImportError:
        from moviepy.video.VideoClip import VideoClip

    def make_frame(t):
        frame_img = render_tv_broadcast_frame(
            headline_text=headline_text,
            news_photo_path=str(photo_path),
            global_t=t,
            category="TOP STORIES",
            ticker_headlines=ticker_items,
            quick_cards=quick_cards
        )
        return np.array(frame_img)

    clip = VideoClip(make_frame, duration=duration)
    output_path = VIDEOS_DIR / "sample_20s_headline_broadcast.mp4"
    clip.write_videofile(str(output_path), fps=fps, codec="libx264")
    
    logger.info(f"✅ 20-Second Sample Video Created: {output_path.name} ({output_path.stat().st_size} bytes)")
    
    # Save preview screenshot
    preview_img = render_tv_broadcast_frame(
        headline_text=headline_text,
        news_photo_path=str(photo_path),
        global_t=2.0,
        category="TOP STORIES",
        ticker_headlines=ticker_items,
        quick_cards=quick_cards
    )
    preview_path = ASSETS_DIR / "headline_card_preview.png"
    preview_img.save(preview_path)
    logger.info(f"📸 Preview Screenshot Saved: {preview_path.name}")

if __name__ == "__main__":
    generate_20s_sample()
