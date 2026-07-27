import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR
from services.groq_service import generate_text
from services.rss_service import get_realtime_ticker_headlines
from models.news_models import GeneratedScript
from utils.logger import logger

STUDIO_ASSETS_DIR = ASSETS_DIR / "studio"
STUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

STUDIO_BG_PATH = STUDIO_ASSETS_DIR / "studio_background.png"
CHANNEL_LOGO_PATH = STUDIO_ASSETS_DIR / "channel_logo_3d.png"

PEXELS_API_KEY = "tMiZhafYzUHfNIUQbq5VwDe38aVyJhPjMqj0k5pFufAqBOvXH6b2UcfR"


def create_3d_channel_logo(force: bool = False) -> Path:
    """Creates a sleek 3D metallic channel emblem logo for AI-NEWSTUBE."""
    if CHANNEL_LOGO_PATH.exists() and not force:
        return CHANNEL_LOGO_PATH

    logger.info("  🎨 Graphics Agent: Designing 3D Metallic Channel Logo...")
    w, h = 420, 120
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([(10, 10), (w - 10, h - 10)], radius=18, fill=(220, 38, 38, 240), outline=(234, 179, 8, 255), width=4)
    draw.rounded_rectangle([(16, 16), (w - 16, h // 2 + 5)], radius=12, fill=(255, 255, 255, 50))

    try:
        from agents.video_agent import _load_font
        font = _load_font(34, bold=True)
    except Exception:
        font = ImageFont.load_default(size=30)

    draw.text((36, 40), "AI-NEWSTUBE", fill=(15, 23, 42, 220), font=font)
    draw.text((34, 38), "AI-NEWSTUBE", fill=(255, 255, 255, 255), font=font)

    img.save(CHANNEL_LOGO_PATH, "PNG")
    logger.info(f"  ✅ Graphics Agent: 3D Channel Logo created: {CHANNEL_LOGO_PATH.name}")
    return CHANNEL_LOGO_PATH


def create_studio_background(force: bool = False) -> Path:
    """Creates a 1920x1080 news studio background using PIL."""
    if STUDIO_BG_PATH.exists() and not force:
        return STUDIO_BG_PATH

    logger.info("  🏢 Graphics Agent: Designing news studio background...")

    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), (12, 17, 35))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = int(12 + (25 - 12) * (y / height))
        g = int(17 + (35 - 17) * (y / height))
        b = int(35 + (65 - 35) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    for x in range(0, width, 120):
        draw.line([(x, 0), (x, height - 300)], fill=(30, 40, 70), width=1)

    for y_pos in [150, 300, 450]:
        draw.rectangle([(0, y_pos), (width, y_pos + 2)], fill=(40, 60, 120))

    # Top & side LED strips
    draw.rectangle([(0, 0), (width, 4)], fill=(220, 38, 38))
    draw.rectangle([(0, 0), (4, height)], fill=(180, 30, 30))
    draw.rectangle([(width - 4, 0), (width, height)], fill=(180, 30, 30))

    # Desk area
    desk_y = height - 280
    for y in range(desk_y, height):
        progress = (y - desk_y) / 280
        r = int(20 + 15 * progress)
        g = int(25 + 10 * progress)
        b = int(50 + 20 * progress)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    draw.rectangle([(0, desk_y), (width, desk_y + 8)], fill=(200, 40, 40))
    draw.rectangle([(0, desk_y + 8), (width, desk_y + 60)], fill=(25, 30, 55))

    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img.save(STUDIO_BG_PATH, "PNG", quality=95)
    return STUDIO_BG_PATH


def generate_search_keywords(topic_title: str, category: str) -> List[str]:
    """Extract 5 search keywords for fetching reference news photos."""
    prompt = f"""Given this news story:
Topic: {topic_title}
Category: {category}

Extract 5 concise search queries (2-4 words each in English) for real news photography.
Return ONLY a valid JSON list of 5 strings:
["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"]
"""
    try:
        response = generate_text(prompt, temperature=0.2)
        clean_json = response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        keywords = json.loads(clean_json)
        if isinstance(keywords, list) and len(keywords) >= 5:
            return keywords[:5]
    except Exception:
        pass

    return [f"{category} news", f"{topic_title.split()[0]} event", "press conference", "breaking news", "news broadcast"]


def fetch_news_photo(keyword: str, output_path: Path, idx: int) -> bool:
    """Fetch real news photo from Pexels for PiP display."""
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(keyword)}&per_page=5&orientation=landscape&size=medium"
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                photo = photos[idx % len(photos)]
                img_url = photo.get("src", {}).get("medium", photo.get("src", {}).get("small", ""))
                if img_url:
                    img_resp = requests.get(img_url, timeout=10)
                    if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                        with open(output_path, "wb") as f:
                            f.write(img_resp.content)
                        return True
    except Exception:
        pass

    try:
        photo_prompt = requests.utils.quote(f"News photograph of {keyword}, photorealistic, HD")
        url = f"https://image.pollinations.ai/prompt/{photo_prompt}?width=640&height=420&nologo=true&seed={idx + 100}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass

    return False


def graphics_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Graphics Agent: Prepares studio background, 3D logo, PiP news photos, and real-time news ticker.
    """
    logger.info("=" * 50)
    logger.info("🎨 GRAPHICS AGENT (Studio BG + 3D Logo + PiP Photos + News Ticker)")
    logger.info("=" * 50)

    # 1. Studio BG & 3D Logo
    studio_path = create_studio_background()
    logo_path = create_3d_channel_logo()

    # 2. PiP Reference Photos
    keywords = generate_search_keywords(script_obj.topic_title, script_obj.category)
    logger.info(f"  📸 Graphics Keywords: {keywords}")

    pip_photos: List[str] = []
    timestamp = int(time.time())

    for idx, kw in enumerate(keywords, start=1):
        output_file = ASSETS_DIR / f"pip_photo_{timestamp}_{idx}.jpg"
        if fetch_news_photo(kw, output_file, idx):
            pip_photos.append(str(output_file))

    # 3. Real-Time RSS News Ticker Headlines
    ticker_news = get_realtime_ticker_headlines(limit=10)
    script_obj.ticker_headlines = ticker_news

    # Format image_paths: [anchor_path, studio_bg_path, logo_path, pip_photo_1, pip_photo_2, ...]
    anchor_path = script_obj.image_paths[0] if script_obj.image_paths else str(STUDIO_ASSETS_DIR / "ai_anchor_3d.png")
    script_obj.image_paths = [anchor_path, str(studio_path), str(logo_path)] + pip_photos

    logger.info(f"✅ Graphics Agent Completed — Studio BG + 3D Logo + {len(pip_photos)} PiP photos + Ticker Ready!")
    return script_obj
