import os
import sys
import json
import time
from pathlib import Path

# Ensure project root is always in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PIL import Image, ImageDraw
from config.settings import THUMBNAILS_DIR, DATA_DIR, CHANNEL_NAME
from services.groq_service import generate_text
from models.news_models import GeneratedScript
from utils.logger import logger


def generate_seo_metadata(topic_title: str, script_text: str, category: str) -> dict:
    """
    Uses LLM to generate YouTube SEO Title, Description, and Tags.
    """
    prompt = f"""Tum ek YouTube SEO Specialist ho.

Topic: {topic_title}
Category: {category}
Script: {script_text}

Generate optimized YouTube video metadata in JSON format:
1. "title": Catchy, high-CTR YouTube title under 70 chars with emojis.
2. "description": Engaging description including script summary, channel subscribe call to action, and 5 hashtags.
3. "tags": List of 10 relevant search keywords/tags.

Return ONLY valid JSON format:
{{
    "title": "Title here",
    "description": "Description here",
    "tags": ["tag1", "tag2", "tag3"]
}}
"""
    try:
        response = generate_text(prompt, temperature=0.5)
        clean_json = response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        logger.warning(f"Could not generate LLM SEO metadata ({e}). Using default templates.")

    return {
        "title": f"🚨 {topic_title[:60]} | {CHANNEL_NAME}",
        "description": f"{topic_title}\n\nSubscribe to {CHANNEL_NAME} for 24/7 trending news updates!\n\n#News #AINews #{category} #Trending #Updates",
        "tags": ["news", "ai news", category.lower(), "trending", "latest news", "india news"]
    }


def create_youtube_thumbnail(topic_title: str, category: str, output_path: Path) -> Path:
    """
    Renders a High-CTR 1280x720 YouTube Thumbnail with 3D Presenter, Curiosity Text Pill, and High-Contrast Typography.
    """
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(12, 17, 35))
    draw = ImageDraw.Draw(img)

    # 1. Background Gradient & Decorative Accents
    for y in range(height):
        progress = y / height
        r = int(12 + 20 * progress)
        g = int(17 + 15 * progress)
        b = int(35 + 30 * progress)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Top red accent bar
    draw.rectangle([(0, 0), (width, 8)], fill=(220, 38, 38))
    # Glowing side borders
    draw.rectangle([(0, 0), (8, height)], fill=(234, 179, 8))

    # 2. Top Category & Curiosity Badge Pill
    try:
        from agents.video_agent import _load_font
        badge_font = _load_font(26, bold=True)
        headline_font = _load_font(48, bold=True)
        sub_font = _load_font(22, bold=True)
    except Exception:
        badge_font = ImageFont.load_default(size=24)
        headline_font = ImageFont.load_default(size=40)
        sub_font = ImageFont.load_default(size=20)

    # Curiosity Pill Box
    draw.rounded_rectangle([(40, 40), (480, 105)], radius=12, fill=(220, 38, 38), outline=(234, 179, 8), width=3)
    draw.text((58, 56), f"🚨 {category.upper()} SPECIAL", fill=(255, 255, 255), font=badge_font)

    # 3. Main High-CTR Headline Pill (Left Side, 700px width)
    headline_w = 720
    draw.rounded_rectangle([(40, 135), (40 + headline_w, 580)], radius=18, fill=(15, 23, 42), outline=(239, 68, 68), width=4)
    # Red left accent strip
    draw.rounded_rectangle([(40, 135), (62, 580)], radius=10, fill=(239, 68, 68))
    # Top gold accent line
    draw.rectangle([(40, 135), (40 + headline_w, 140)], fill=(234, 179, 8))

    clean_title = topic_title.replace("\n", " ").strip()
    words = clean_title.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=headline_font)
        if bbox[2] - bbox[0] > (headline_w - 90) and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    y_pos = 170
    for line in lines[:4]:
        # Drop shadow
        draw.text((82, y_pos + 3), line, fill=(10, 10, 15), font=headline_font)
        # Gold/White text highlight
        text_fill = (234, 179, 8) if y_pos == 170 else (255, 255, 255)
        draw.text((80, y_pos), line, fill=text_fill, font=headline_font)
        y_pos += 90

    # 4. Overlay 3D AI Presenter Avatar on Right Side (if exists)
    anchor_3d_file = BASE_DIR / "assets" / "studio" / "ai_anchor_3d.png"
    if anchor_3d_file.exists():
        try:
            a_img = Image.open(anchor_3d_file).convert("RGBA")
            a_h = 680
            a_aspect = a_img.width / a_img.height
            a_w = int(a_h * a_aspect)
            resized_a = a_img.resize((a_w, a_h), Image.Resampling.LANCZOS)
            img.paste(resized_a, (width - a_w - 20, 40), resized_a)
        except Exception:
            pass

    # 5. Overlay 3D Channel Logo & Call to Action (Bottom Left)
    draw.rounded_rectangle([(40, 610), (450, 680)], radius=12, fill=(220, 38, 38), outline=(234, 179, 8), width=2)
    draw.text((58, 630), f"▶ SUBSCRIBE {CHANNEL_NAME}", fill=(255, 255, 255), font=sub_font)

    img.save(output_path, quality=95)
    return output_path


def thumbnail_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Thumbnail & SEO Agent: Generates 1280x720 YouTube Thumbnail and SEO metadata.
    """
    logger.info("=" * 50)
    logger.info("🖼️ THUMBNAIL & SEO AGENT")
    logger.info("=" * 50)

    timestamp = int(time.time())
    thumb_path = THUMBNAILS_DIR / f"thumbnail_{timestamp}.jpg"

    logger.info("Generating YouTube 1280x720 Thumbnail...")
    create_youtube_thumbnail(script_obj.topic_title, script_obj.category, thumb_path)
    script_obj.thumbnail_path = str(thumb_path)
    logger.info(f"✅ Thumbnail generated: {thumb_path.name}")

    logger.info("Generating YouTube SEO Title, Description, and Tags...")
    metadata = generate_seo_metadata(script_obj.topic_title, script_obj.script_text, script_obj.category)

    meta_file = DATA_DIR / f"metadata_{timestamp}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ SEO Metadata saved: {meta_file.name}")
    logger.info(f"📌 Suggested Title: {metadata.get('title')}")

    return script_obj
