import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import THUMBNAILS_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from utils.logger import logger


def thumbnail_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Thumbnail Agent: Generates High-CTR 1280x720 Broadcast News Thumbnail & SEO Metadata.
    """
    logger.info("=" * 50)
    logger.info("🖼️ THUMBNAIL AGENT (High-CTR Broadcast Design)")
    logger.info("=" * 50)

    ts = int(time.time())
    thumb_path = THUMBNAILS_DIR / f"thumb_{ts}.jpg"
    w, h = 1280, 720


    img = Image.new("RGB", (w, h), (10, 12, 28))
    draw = ImageDraw.Draw(img)

    # Background Navy/Crimson Gradient
    for y in range(h):
        progress = y / h
        r = int(14 + 180 * progress)
        g = int(12 + 15 * progress)
        b = int(28 + 20 * progress)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Red & Gold Metallic Border Frame
    draw.rectangle([(0, 0), (w, 16)], fill=(220, 38, 38))
    draw.rectangle([(0, 16), (w, 24)], fill=(255, 215, 0))
    draw.rectangle([(0, h - 24), (w, h - 16)], fill=(255, 215, 0))
    draw.rectangle([(0, h - 16), (w, h)], fill=(220, 38, 38))

    # Badge Pill
    draw.rounded_rectangle([(40, 40), (480, 100)], radius=12, fill=(220, 38, 38), outline=(255, 215, 0), width=3)
    try:
        from agents.video_agent import _load_font
        draw.text((60, 52), f"🚨 BREAKING  |  {CHANNEL_NAME}", fill=(255, 255, 255), font=_load_font(28, bold=True))
        hl_font = _load_font(52, bold=True)
    except Exception:
        hl_font = ImageFont.load_default()

    # Large High-CTR Headline Text
    clean_title = script_obj.topic_title.replace("\n", " ").strip()
    words = clean_title.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=hl_font)
        if bbox[2] - bbox[0] > w - 160 and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    for i, line in enumerate(lines[:3]):
        draw.text((64, 224 + i * 75), line, fill=(10, 10, 15), font=hl_font)
        draw.text((60, 220 + i * 75), line, fill=(255, 215, 0), font=hl_font)

    img.save(thumb_path, "JPEG", quality=95)
    logger.info(f"  ✅ Thumbnail Agent: High-CTR Thumbnail created ({thumb_path.name})")
    script_obj.thumbnail_path = str(thumb_path)

    return script_obj
