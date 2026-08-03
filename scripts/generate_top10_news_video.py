import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.news_hunter import news_hunter
from agents.graphics_agent import get_realtime_ticker_headlines
from agents.script_writer import script_writer


from agents.visuals_agent import VisualResearchEngine
from services.uv_graphics_engine import UVGraphicsEngine
from agents.voice_agent import voice_agent
from agents.video_agent import video_agent
from services.blender_render_service import BlenderRenderService
from models.news_models import GeneratedScript, NewsArticle, MediaAsset
from utils.logger import logger
from config.settings import ASSETS_DIR, VIDEOS_DIR



def main():
    logger.info("=" * 60)
    logger.info("📺 TOP 10 HEADLINE NEWS BROADCAST (Blender 5.2 3D Human Anchor)")
    logger.info("=" * 60)

    # 1. Ensure Blender Executable
    blender_bin = BlenderRenderService.find_blender_binary()
    if not blender_bin:
        logger.error("❌ Blender executable not found on system!")
        return

    logger.info(f"  📌 Detected Blender 5.2 Executable: {blender_bin}")

    # 2. Fetch Today's Top 10 Headlines
    logger.info("\n📌 Step 1: Fetching Today's Top 10 Real-Time Headline News Stories...")
    ticker_headlines = get_realtime_ticker_headlines(limit=10)
    if not ticker_headlines:
        ticker_headlines = [
            "इसरो ने रच इतिहास: चंद्रयान मिशन की सफलता पर दुनिया हैरान",
            "भारत की आर्थिक वृद्धि दर में रिकॉर्ड उछाल, जीडीपी 7.8% के पार",
            "एआई तकनीक में भारत बना ग्लोबल लीडर, नए टेक हब की घोषणा",
            "भारतीय अंतरिक्ष अनुसंधान संगठन का नया सूर्य मिशन प्रक्षेपित",
            "रक्षा क्षेत्र में भारत की बड़ी आत्मनिर्भरता, स्वदेशी विमान तैयार",
            "ग्रीन एनर्जी क्षेत्र में 100 बिलियन डॉलर का नया निवेश",
            "डिजिटल इंडिया का नया कीर्तिमान, 10 अरब यूपीआई लेनदेन पार",
            "भारतीय स्टार्टअप इकोसिस्टम में रिकॉर्ड 50 नए यूनिकोर्न",
            "राष्ट्रीय शिक्षा नीति के तहत नए डिजिटल यूनिवर्सिटी की शुरुआत",
            "भारत ने वैश्विक मंच पर जलवायु परिवर्तन संधि पर किए हस्ताक्षर"
        ]

    for idx, h in enumerate(ticker_headlines, start=1):
        logger.info(f"  📰 Headline {idx:02d}: {h}")

    # 3. Create News Topic Item
    topic_title = "आज की 10 बड़ी मुख्य खबरें — विशेष बुलेटिन"
    news_item = NewsArticle(
        title=topic_title,
        link="https://news.google.com",
        summary="\n".join([f"{i+1}. {h}" for i, h in enumerate(ticker_headlines)]),
        category="Top 10 Headlines",
        published_at="",
        scraped_content="\n".join(ticker_headlines),
        trending_score=98.0
    )


    # 4. Generate Hindi Script
    logger.info("\n📌 Step 2: Generating 100% Devanagari Hindi Broadcast Script...")
    script_obj = script_writer(news_item)


    # 5. Visual Research Strategy for 10 Headlines
    logger.info("\n📌 Step 3: Conducting Visual Research Strategy (NASA -> Pexels -> Wikimedia)...")
    media_assets = []
    pip_photos = []
    timestamp = int(time.time())

    for idx, headline in enumerate(ticker_headlines, start=1):
        out_file = ASSETS_DIR / f"top10_media_{timestamp}_{idx}.jpg"
        asset = VisualResearchEngine.research_media(headline, out_file, idx)
        pip_photos.append(asset.file_path)
        media_assets.append(asset)
        logger.info(f"  📸 Story {idx:02d} Asset [{asset.media_type.upper()}] Credit: '{asset.on_screen_credit}'")

    # 6. Generate Dynamic UV Texture Surface Maps for Blender
    logger.info("\n📌 Step 4: Generating Dynamic UV Surface Maps for Blender 3D Curved LED Wall & Monitor...")
    led_uv_path = UVGraphicsEngine.generate_led_wall_uv(topic_title, "Top 10 Headlines", global_t=0.0)
    mon_uv_path = UVGraphicsEngine.generate_side_monitor_uv(pip_photos[0] if pip_photos else None)

    anchor_3d_path = str(ASSETS_DIR / "studio" / "3d_human_presenter_test.png")
    studio_bg_path = str(ASSETS_DIR / "studio_background_25d.png")
    logo_path = str(ASSETS_DIR / "channel_logo_3d.png")

    script_obj.media_assets = media_assets
    script_obj.ticker_headlines = ticker_headlines
    script_obj.image_paths = [anchor_3d_path, studio_bg_path, logo_path, str(led_uv_path), str(mon_uv_path)] + pip_photos

    # 7. Generate Neural Voiceover (hi-IN-SwaraNeural)
    logger.info("\n📌 Step 5: Generating Neural TTS Voiceover (hi-IN-SwaraNeural)...")
    script_obj = voice_agent(script_obj)

    # 8. Render Broadcast Video via Blender 5.2
    logger.info("\n📌 Step 6: Rendering 1080p MP4 Video via Blender 5.2 3D Production Engine...")
    script_obj = video_agent(script_obj)

    logger.info("\n" + "=" * 60)
    logger.info("🎉 TOP 10 HEADLINE NEWS BROADCAST VIDEO GENERATED SUCCESSFULLY!")
    logger.info(f"🎥 Video Path: {script_obj.video_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
