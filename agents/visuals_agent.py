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
from models.news_models import GeneratedScript
from utils.logger import logger


# ─────────────────────────────────────────────────────────────
# Paths for cached studio assets (generated once, reused)
# ─────────────────────────────────────────────────────────────
STUDIO_ASSETS_DIR = ASSETS_DIR / "studio"
STUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

ANCHOR_IMAGE_PATH = STUDIO_ASSETS_DIR / "ai_anchor_3d.png"
STUDIO_BG_PATH = STUDIO_ASSETS_DIR / "studio_background.png"
CHANNEL_LOGO_PATH = STUDIO_ASSETS_DIR / "channel_logo_3d.png"

# Free API keys for fetching reference news photos (PiP display)
PEXELS_API_KEY = "tMiZhafYzUHfNIUQbq5VwDe38aVyJhPjMqj0k5pFufAqBOvXH6b2UcfR"


# ─────────────────────────────────────────────────────────────
# 1. Generate 3D AI Anchor Image (3D Digital Presenter Avatar)
# ─────────────────────────────────────────────────────────────
def generate_ai_anchor(force: bool = True) -> Path:
    """
    Generates a realistic 3D AI News Anchor presenter avatar using Pollinations AI.
    """
    if ANCHOR_IMAGE_PATH.exists() and not force:
        logger.info("  ✅ 3D AI Anchor image already cached, reusing.")
        return ANCHOR_IMAGE_PATH

    logger.info("  🧑‍💼 Generating 3D AI News Anchor Presenter Avatar (3D Render Style)...")

    prompt = requests.utils.quote(
        "3D digital human TV news anchor presenter avatar, handsome male or stylish female journalist, "
        "wearing formal navy blue suit jacket, sitting at modern television news studio desk, "
        "3D character render, Octane Render style, Unreal Engine 5 aesthetic, "
        "volumetric studio lights, upper body shot, photorealistic 8k render quality"
    )
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=1080&nologo=true&seed=777"

    try:
        resp = requests.get(url, timeout=35)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(ANCHOR_IMAGE_PATH, "wb") as f:
                f.write(resp.content)
            logger.info(f"  ✅ 3D AI Anchor generated successfully: {ANCHOR_IMAGE_PATH.name} ({len(resp.content)} bytes)")
            return ANCHOR_IMAGE_PATH
    except Exception as e:
        logger.warning(f"  ⚠️ Failed to generate 3D AI anchor from web API ({e}), building fallback.")

    _create_anchor_placeholder()
    return ANCHOR_IMAGE_PATH


# ─────────────────────────────────────────────────────────────
# 2. Render 3D Metallic Channel Logo
# ─────────────────────────────────────────────────────────────
def generate_3d_channel_logo(force: bool = False) -> Path:
    """Creates a sleek 3D metallic channel emblem logo for AI-NEWSTUBE."""
    if CHANNEL_LOGO_PATH.exists() and not force:
        return CHANNEL_LOGO_PATH

    logger.info("  🎨 Designing 3D Metallic Channel Logo...")
    w, h = 420, 120
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 3D Metallic border bevel & shadow
    draw.rounded_rectangle([(10, 10), (w - 10, h - 10)], radius=18, fill=(220, 38, 38, 240), outline=(234, 179, 8, 255), width=4)
    # Gloss highlight top half
    draw.rounded_rectangle([(16, 16), (w - 16, h // 2 + 5)], radius=12, fill=(255, 255, 255, 50))

    # Inner 3D emblem text
    try:
        from agents.video_agent import _load_font
        font = _load_font(34, bold=True)
    except Exception:
        font = ImageFont.load_default(size=30)

    # Drop shadow
    draw.text((36, 40), "AI-NEWSTUBE", fill=(15, 23, 42, 220), font=font)
    # Bright 3D text highlight
    draw.text((34, 38), "AI-NEWSTUBE", fill=(255, 255, 255, 255), font=font)

    img.save(CHANNEL_LOGO_PATH, "PNG")
    logger.info(f"  ✅ 3D Channel Logo created: {CHANNEL_LOGO_PATH.name}")
    return CHANNEL_LOGO_PATH


def _create_anchor_placeholder():
    """Creates a simple anchor silhouette placeholder if AI generation fails."""
    img = Image.new("RGBA", (800, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Simple silhouette shape
    # Head
    draw.ellipse([(300, 80), (500, 300)], fill=(60, 60, 80, 255))
    # Body
    draw.polygon([(250, 300), (550, 300), (600, 800), (200, 800)], fill=(40, 40, 60, 255))
    # Blazer collar
    draw.polygon([(320, 300), (400, 450), (480, 300)], fill=(180, 40, 40, 255))

    img.save(ANCHOR_IMAGE_PATH, "PNG")
    logger.info("  ✅ Anchor placeholder silhouette created.")


# ─────────────────────────────────────────────────────────────
# 2. Create Professional News Studio Background
# ─────────────────────────────────────────────────────────────
def create_studio_background(force: bool = False) -> Path:
    """
    Creates a professional 1920x1080 news studio background using PIL.
    Dark navy blue studio with modern design elements.
    """
    if STUDIO_BG_PATH.exists() and not force:
        logger.info("  ✅ Studio background already cached, reusing.")
        return STUDIO_BG_PATH

    logger.info("  🏢 Designing news studio background...")

    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), (12, 17, 35))
    draw = ImageDraw.Draw(img)

    # ── Gradient background (dark navy → slightly lighter) ──
    for y in range(height):
        r = int(12 + (25 - 12) * (y / height))
        g = int(17 + (35 - 17) * (y / height))
        b = int(35 + (65 - 35) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ── Studio wall panels (subtle vertical lines) ──
    for x in range(0, width, 120):
        alpha_variation = 15 + (x % 3) * 5
        draw.line([(x, 0), (x, height - 300)], fill=(30, 40, 70), width=1)

    # ── Decorative horizontal light strips on wall ──
    for y_pos in [150, 300, 450]:
        draw.rectangle([(0, y_pos), (width, y_pos + 2)], fill=(40, 60, 120))

    # ── World map outline (subtle background element) ──
    # Simple geometric shapes suggesting a map
    map_color = (25, 35, 65)
    # Left continent shape
    draw.ellipse([(100, 100), (500, 400)], fill=map_color, outline=(35, 50, 85))
    draw.ellipse([(350, 150), (700, 350)], fill=map_color, outline=(35, 50, 85))
    # Right shapes
    draw.ellipse([(900, 80), (1200, 350)], fill=map_color, outline=(35, 50, 85))
    draw.ellipse([(1100, 200), (1400, 380)], fill=map_color, outline=(35, 50, 85))

    # ── Glowing accent lines (studio LED strips) ──
    # Top accent line
    draw.rectangle([(0, 0), (width, 4)], fill=(220, 38, 38))
    # Side accent
    draw.rectangle([(0, 0), (4, height)], fill=(180, 30, 30))
    draw.rectangle([(width - 4, 0), (width, height)], fill=(180, 30, 30))

    # ── News desk area (bottom portion) ──
    desk_y = height - 280
    # Desk surface — dark gradient with glossy look
    for y in range(desk_y, height):
        progress = (y - desk_y) / 280
        r = int(20 + 15 * progress)
        g = int(25 + 10 * progress)
        b = int(50 + 20 * progress)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Desk front panel
    draw.rectangle([(0, desk_y), (width, desk_y + 8)], fill=(200, 40, 40))  # Red accent strip
    draw.rectangle([(0, desk_y + 8), (width, desk_y + 60)], fill=(25, 30, 55))  # Dark panel

    # Channel logo area on desk
    draw.rectangle([(width // 2 - 150, desk_y + 15), (width // 2 + 150, desk_y + 50)], fill=(200, 40, 40))

    # ── PiP frame area (left side — for news photos) ──
    pip_x, pip_y = 80, 120
    pip_w, pip_h = 580, 380
    # PiP border glow
    draw.rectangle(
        [(pip_x - 4, pip_y - 4), (pip_x + pip_w + 4, pip_y + pip_h + 4)],
        fill=(200, 40, 40)
    )
    # PiP inner dark area (will be replaced with news photo in video)
    draw.rectangle(
        [(pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h)],
        fill=(10, 15, 30)
    )

    # Apply slight blur to soften the studio
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    img.save(STUDIO_BG_PATH, "PNG", quality=95)
    logger.info(f"  ✅ Studio background created: {STUDIO_BG_PATH.name}")
    return STUDIO_BG_PATH


# ─────────────────────────────────────────────────────────────
# 3. Fetch Reference News Photos (for PiP display)
# ─────────────────────────────────────────────────────────────
def generate_search_keywords(topic_title: str, category: str) -> List[str]:
    """Extract 5 search keywords for fetching reference news photos (PiP)."""
    prompt = f"""Given this news story:
Topic: {topic_title}
Category: {category}

Extract 5 concise search queries (2-4 words each in English) to find real news photography.
Focus on concrete visual subjects — people, places, objects.

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
    except Exception as e:
        logger.warning(f"Keyword extraction failed ({e}). Using fallback.")

    return [
        f"{category} news",
        f"{topic_title.split()[0]} event",
        "press conference",
        "breaking news",
        "news broadcast"
    ]


def fetch_news_photo(keyword: str, output_path: Path, idx: int) -> bool:
    """Fetch a real copyright-free photo from Pexels for PiP display."""
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        url = (
            f"https://api.pexels.com/v1/search?"
            f"query={requests.utils.quote(keyword)}&per_page=5&orientation=landscape&size=medium"
        )
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

    # Fallback: Pollinations AI
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


# ─────────────────────────────────────────────────────────────
# Main Visuals Agent
# ─────────────────────────────────────────────────────────────
def visuals_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Visuals Agent — Studio Mode:
    1. Generates/caches AI news anchor image
    2. Creates/caches professional news studio background
    3. Fetches 5 real news reference photos for Picture-in-Picture display
    """
    logger.info("=" * 50)
    logger.info("🎨 VISUALS AGENT (Studio Mode — Anchor + News Photos)")
    logger.info("=" * 50)

    # Step 1: 3D AI Anchor (cached)
    logger.info("📌 Step 1: 3D AI News Presenter Anchor")
    anchor_path = generate_ai_anchor()

    # Step 2: 3D Channel Logo & Studio Background (cached)
    logger.info("📌 Step 2: 3D Channel Logo & News Studio Background")
    logo_path = generate_3d_channel_logo()
    studio_path = create_studio_background()

    # Step 3: News reference photos for PiP
    logger.info("📌 Step 3: Fetching News Reference Photos (PiP)")
    keywords = generate_search_keywords(script_obj.topic_title, script_obj.category)
    logger.info(f"  📸 Keywords: {keywords}")

    pip_photos: List[str] = []
    timestamp = int(time.time())

    for idx, kw in enumerate(keywords, start=1):
        output_file = ASSETS_DIR / f"pip_photo_{timestamp}_{idx}.jpg"
        logger.info(f"  🔍 Fetching PiP photo {idx}/{len(keywords)}: '{kw}'...")

        if fetch_news_photo(kw, output_file, idx):
            pip_photos.append(str(output_file))
            logger.info(f"  ✅ PiP photo {idx} ready: {output_file.name}")
        else:
            logger.warning(f"  ⚠️ PiP photo {idx} failed, will use studio-only frame.")

    # Step 4: Fetch real-time headlines for bottom news ticker slide
    logger.info("📌 Step 4: Fetching Real-Time Breaking News Headlines for Ticker Slide...")
    ticker_news = get_realtime_ticker_headlines(limit=10)
    script_obj.ticker_headlines = ticker_news
    logger.info(f"  📰 Ticker headlines ready: {len(ticker_news)} items")

    # Store all paths in image_paths:
    # Format: [anchor_path, studio_bg_path, logo_path, pip_photo_1, pip_photo_2, ...]
    script_obj.image_paths = [str(anchor_path), str(studio_path), str(logo_path)] + pip_photos

    logger.info(f"🎨 Visuals Agent Completed — 3D Anchor + 3D Logo + Studio + {len(pip_photos)} PiP photos + Ticker Ready!")
    return script_obj
