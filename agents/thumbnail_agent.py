import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import THUMBNAILS_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from utils.logger import logger
from services.ai_thumbnail_service import create_ai_youtube_thumbnail


def thumbnail_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Thumbnail Agent: Generates High-CTR 1280x720 Broadcast News Thumbnail via AI Image Generation (Imagen / DALL-E / Flux) & SEO Overlay.
    """
    logger.info("=" * 50)
    logger.info("🖼️ THUMBNAIL AGENT (AI Prompt & Photorealistic Generation)")
    logger.info("=" * 50)

    ts = int(time.time())
    thumb_path = THUMBNAILS_DIR / f"thumb_{ts}.jpg"

    try:
        thumb_path = create_ai_youtube_thumbnail(
            headline=script_obj.topic_title,
            category=getattr(script_obj, "category", "National"),
            summary=script_obj.full_script[:200] if script_obj.full_script else "",
            output_path=thumb_path
        )
        logger.info(f"  ✅ Thumbnail Agent: AI High-CTR Thumbnail created ({thumb_path.name})")
    except Exception as e:
        logger.error(f"  ❌ Thumbnail Agent error: {e}")

    script_obj.thumbnail_path = str(thumb_path)
    return script_obj

