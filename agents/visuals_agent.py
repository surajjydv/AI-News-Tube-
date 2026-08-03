import os
import sys
import time
import json
import requests
from pathlib import Path

# Ensure project root is always in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config.settings import ASSETS_DIR
from services.groq_service import generate_text
from services.rss_service import get_realtime_ticker_headlines
from models.news_models import GeneratedScript, MediaAsset
from utils.logger import logger

# Paths for cached studio assets
STUDIO_ASSETS_DIR = ASSETS_DIR / "studio"
STUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

ANCHOR_IMAGE_PATH = STUDIO_ASSETS_DIR / "ai_anchor_3d.png"
STUDIO_BG_PATH = STUDIO_ASSETS_DIR / "studio_background.png"
CHANNEL_LOGO_PATH = STUDIO_ASSETS_DIR / "channel_logo_3d.png"

PEXELS_API_KEY = "tMiZhafYzUHfNIUQbq5VwDe38aVyJhPjMqj0k5pFufAqBOvXH6b2UcfR"


# ─────────────────────────────────────────────────────────────
# VISUAL RESEARCH AGENT: MEDIA RETRIEVAL ENGINE
# ─────────────────────────────────────────────────────────────
class VisualResearchEngine:
    """
    Dedicated Visual Research Engine:
    Executes VisualAssetManager search workflow (Wikimedia -> Pexels -> Pixabay -> Unsplash -> Min 1280x720 validation).
    Renders 'Visual currently unavailable' placeholder card if all sources fail.
    """

    @classmethod
    def research_media(cls, keyword: str, output_path: Path, idx: int = 1, headline: str = "", category: str = "NEWS") -> MediaAsset:
        from services.visual_asset_manager import VisualAssetManager
        return VisualAssetManager.get_visual_asset(headline or keyword, category, output_path)




def generate_ai_anchor(force: bool = False) -> Path:
    if ANCHOR_IMAGE_PATH.exists() and not force:
        return ANCHOR_IMAGE_PATH

    logger.info("  🧑‍💼 Generating 3D AI News Anchor Presenter Avatar...")
    prompt = requests.utils.quote(
        "3D digital human TV news anchor presenter avatar, handsome male or stylish female journalist, "
        "wearing formal navy blue suit jacket, sitting at modern television news studio desk, "
        "3D character render, Octane Render style, Unreal Engine 5 aesthetic, photorealistic 8k"
    )
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=1080&nologo=true&seed=777"

    try:
        resp = requests.get(url, timeout=35)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(ANCHOR_IMAGE_PATH, "wb") as f:
                f.write(resp.content)
            return ANCHOR_IMAGE_PATH
    except Exception:
        pass

    _create_anchor_placeholder()
    return ANCHOR_IMAGE_PATH


def generate_3d_channel_logo(force: bool = False) -> Path:
    if CHANNEL_LOGO_PATH.exists() and not force:
        return CHANNEL_LOGO_PATH

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
    return CHANNEL_LOGO_PATH


def _create_anchor_placeholder():
    img = Image.new("RGBA", (800, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(300, 80), (500, 300)], fill=(60, 60, 80, 255))
    draw.polygon([(250, 300), (550, 300), (600, 800), (200, 800)], fill=(40, 40, 60, 255))
    img.save(ANCHOR_IMAGE_PATH, "PNG")


def create_studio_background(force: bool = False) -> Path:
    if STUDIO_BG_PATH.exists() and not force:
        return STUDIO_BG_PATH

    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (12, 17, 35))
    draw = ImageDraw.Draw(img)

    for y in range(h):
        r = int(12 + (25 - 12) * (y / h))
        g = int(17 + (35 - 17) * (y / h))
        b = int(35 + (65 - 35) * (y / h))
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    for x in range(0, w, 120):
        draw.line([(x, 0), (x, h - 300)], fill=(30, 40, 70), width=1)

    for y_pos in [150, 300, 450]:
        draw.rectangle([(0, y_pos), (w, y_pos + 2)], fill=(40, 60, 120))

    draw.rectangle([(0, 0), (w, 4)], fill=(220, 38, 38))
    draw.rectangle([(0, 0), (4, h)], fill=(180, 30, 30))
    draw.rectangle([(w - 4, 0), (w, h)], fill=(180, 30, 30))

    desk_y = h - 280
    for y in range(desk_y, h):
        progress = (y - desk_y) / 280
        r = int(20 + 15 * progress)
        g = int(25 + 10 * progress)
        b = int(50 + 20 * progress)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    draw.rectangle([(0, desk_y), (w, desk_y + 8)], fill=(200, 40, 40))
    draw.rectangle([(0, desk_y + 8), (w, desk_y + 60)], fill=(25, 30, 55))

    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img.save(STUDIO_BG_PATH, "PNG", quality=95)
    return STUDIO_BG_PATH


def generate_search_keywords(topic_title: str, category: str) -> List[str]:
    prompt = f"Given news topic '{topic_title}' category '{category}', return 5 concise search keywords for real news photography as JSON list of strings."
    try:
        response = generate_text(prompt, temperature=0.2)
        clean_json = response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        keywords = json.loads(clean_json)
        if isinstance(keywords, list) and len(keywords) >= 5:
            return keywords[:5]
    except Exception:
        pass

    return [f"{category} news", f"{topic_title.split()[0]} event", "press conference", "breaking news", "news broadcast"]


def visuals_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Visuals Agent:
    Executes Visual Research Strategy (NASA API -> Pexels -> Wikimedia -> AI Fallback).
    Attaches media_assets with on_screen_credit strings.
    """
    logger.info("=" * 50)
    logger.info("🎨 VISUALS AGENT (Visual Research Strategy — Real Media First)")
    logger.info("=" * 50)

    anchor_path = generate_ai_anchor()
    logo_path = generate_3d_channel_logo()
    studio_path = create_studio_background()

    keywords = generate_search_keywords(script_obj.topic_title, script_obj.category)
    logger.info(f"  📸 Visual Research Keywords: {keywords}")

    pip_photos: List[str] = []
    media_assets: List[MediaAsset] = []
    timestamp = int(time.time())

    for idx, kw in enumerate(keywords, start=1):
        output_file = ASSETS_DIR / f"pip_photo_{timestamp}_{idx}.jpg"
        logger.info(f"  🔍 Visual Researching media {idx}/{len(keywords)}: '{kw}'...")

        asset = VisualResearchEngine.research_media(
            keyword=kw,
            output_path=output_file,
            idx=idx,
            headline=script_obj.topic_title,
            category=script_obj.category
        )

        pip_photos.append(asset.file_path)
        media_assets.append(asset)
        logger.info(f"  ✅ Asset {idx} [{asset.media_type.upper()}] Credit: '{asset.on_screen_credit}' -> {Path(asset.file_path).name}")

    # Step 4: Fetch real-time headlines for bottom news ticker slide
    logger.info("📌 Step 4: Fetching Real-Time Breaking News Headlines for Ticker Slide...")
    ticker_news = get_realtime_ticker_headlines(limit=10)
    script_obj.ticker_headlines = ticker_news
    script_obj.media_assets = media_assets
    logger.info(f"  📰 Ticker headlines ready: {len(ticker_news)} items")

    # Store all paths in image_paths:
    # Format: [anchor_path, studio_bg_path, logo_path, pip_photo_1, pip_photo_2, ...]
    script_obj.image_paths = [str(anchor_path), str(studio_path), str(logo_path)] + pip_photos

    logger.info(f"🎨 Visuals Agent Completed — Retained {len(media_assets)} researched media assets with credits!")
    return script_obj

