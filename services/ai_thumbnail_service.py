"""
services/ai_thumbnail_service.py
================================
AI-Powered High-CTR YouTube Thumbnail Generator.
Integrates Gemini Imagen, OpenAI DALL-E 3, and Pollinations Flux.1 with
3D extruded typography, high-contrast visual grading, and viral YouTube packaging.
"""

import os
import sys
import time
import urllib.parse
import requests
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import THUMBNAILS_DIR, CHANNEL_NAME
from utils.logger import logger
from utils.font_utils import load_font, sanitize_text, draw_shaped_text


def generate_ai_thumbnail_prompt(headline: str, category: str, summary: str = "") -> str:
    """Uses Groq LLM to generate a dramatic, high-CTR cinematic news thumbnail prompt from the headline."""
    from services.groq_service import generate_text

    clean_hl = sanitize_text(headline)
    prompt = (
        f"You are an expert YouTube thumbnail designer and cinematic prompt engineer.\n"
        f"HEADLINE: '{clean_hl}'\n"
        f"CATEGORY: {category}\n\n"
        f"Write a hyper-dramatic, photorealistic 16:9 image prompt in English for Flux / Midjourney / Imagen.\n"
        f"Include: central dramatic subject with intense expression or high-stakes event, split cinematic rim lighting, "
        f"hyper-detailed background, 8k resolution, editorial realism, photorealistic depth of field.\n"
        f"Do NOT include any text, letters, logos, or watermarks in the prompt.\n"
        f"Keep the prompt under 40 words.\n"
        f"Return ONLY the prompt string."
    )
    try:
        res = generate_text(prompt, temperature=0.3)
        res_clean = res.strip().strip('"').strip("'")
        if len(res_clean) > 20:
            return res_clean
    except Exception as e:
        logger.warning(f"AI Prompt generation note: {e}")

    return f"Dramatic cinematic news scene of {clean_hl}, high contrast lighting, photorealistic 8k documentary visual, cinematic atmosphere"


def fetch_ai_image_gemini(prompt: str, output_path: Path) -> bool:
    """Generates image using Google Gemini Imagen API if GEMINI_API_KEY is available."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return False
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        logger.info("  🎨 Generating image via Google Gemini Imagen...")
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=dict(number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg")
        )
        for gen_img in result.generated_images:
            output_path.write_bytes(gen_img.image.image_bytes)
            logger.info("  ✅ Google Gemini Imagen generation succeeded!")
            return True
    except Exception as e:
        logger.warning(f"  Gemini Imagen note: {e}")
    return False


def fetch_ai_image_openai(prompt: str, output_path: Path) -> bool:
    """Generates image using OpenAI DALL-E 3 if OPENAI_API_KEY is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        logger.info("  🎨 Generating image via OpenAI DALL-E 3...")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        img_url = response.data[0].url
        if img_url:
            r = requests.get(img_url, timeout=25)
            if r.status_code == 200:
                output_path.write_bytes(r.content)
                logger.info("  ✅ OpenAI DALL-E 3 generation succeeded!")
                return True
    except Exception as e:
        logger.warning(f"  OpenAI DALL-E 3 note: {e}")
    return False


def fetch_ai_image_flux(prompt: str, output_path: Path) -> bool:
    """Generates photorealistic 16:9 image using Flux.1 engine via Pollinations AI (Zero-config, high-speed)."""
    try:
        logger.info(f"  🎨 Generating photorealistic visual via Flux.1...")
        logger.info(f"     Prompt: '{prompt[:90]}...'")
        encoded = urllib.parse.quote(prompt)
        seed = int(time.time() * 1000) % 999999
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux&nologo=true&seed={seed}"
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 10000:
            output_path.write_bytes(r.content)
            logger.info(f"  ✅ Flux.1 AI Image Generation succeeded! ({len(r.content)} bytes)")
            return True
        else:
            logger.warning(f"  Flux.1 generation returned HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"  Flux.1 generation error: {e}")
    return False


def generate_short_thumbnail_headline(title: str, category: str = "General") -> Tuple[str, str]:
    """
    Generates a high-CTR 2-part punchy headline (Line 1: Hook, Line 2: Context)
    specifically designed to maximize YouTube Click-Through Rate.
    """
    clean = sanitize_text(title).strip("\"' ")
    if " - " in clean:
        clean = clean.split(" - ")[0].strip()

    try:
        from services.groq_service import generate_text
        prompt = (
            f"You are the top YouTube packaging expert for a viral Hindi news/analysis channel.\n"
            f"ARTICLE TITLE: '{clean}'\n"
            f"CATEGORY: {category}\n\n"
            f"Create a high-CTR 2-line YouTube thumbnail text in HINDI (Devanagari script, max 3-4 words per line).\n"
            f"Line 1 MUST be a shocking high-stakes hook (e.g. 'बड़ा धमाका!', 'देश में हड़कंप!', '20 सांसद सस्पेंड?').\n"
            f"Line 2 MUST be the specific entity or action (e.g. 'सीबीआई का छापा', 'संसद में बवाल', 'पूरी सच्चाई').\n\n"
            f"Respond ONLY with a JSON list of two strings: [\"LINE_1\", \"LINE_2\"]"
        )
        res = generate_text(prompt, temperature=0.25, max_tokens=60)
        from utils.json_utils import extract_json_from_llm
        lines = extract_json_from_llm(res)
        if isinstance(lines, list) and len(lines) >= 2:
            l1 = sanitize_text(str(lines[0])).strip("\"' ")
            l2 = sanitize_text(str(lines[1])).strip("\"' ")
            if 2 <= len(l1) <= 35 and 2 <= len(l2) <= 35:
                return l1, l2
    except Exception:
        pass

    # Heuristic Fallback
    words = clean.split()
    half = len(words) // 2
    l1 = " ".join(words[:max(3, half)])[:28]
    l2 = " ".join(words[max(3, half):])[:32] if len(words) > 3 else "बड़ी ख़बर"
    return l1, l2


def draw_3d_text_extrusion(
    canvas: Image.Image,
    pos: Tuple[int, int],
    text: str,
    font_size: int,
    text_color: Tuple[int, int, int],
    depth: int = 7,
    angle_dx: int = 2,
    angle_dy: int = 3
):
    """Draws massive 3D extruded text with depth bevel layers and outer drop shadow."""
    x, y = pos

    # Outer soft drop shadow
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for s_step in range(1, 4):
        draw_shaped_text(shadow_layer, (x + s_step * angle_dx + 3, y + s_step * angle_dy + 3),
                         text, font_size=font_size, bold=True, text_color=(0, 0, 0, 160))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=5))
    canvas.paste(shadow_layer, (0, 0), shadow_layer)

    # 3D Depth Extrusion Layers (from dark rear to mid front)
    for step in range(depth, 0, -1):
        ratio = step / float(depth)
        ext_r = int(text_color[0] * 0.15 + (1 - ratio) * 25)
        ext_g = int(text_color[1] * 0.15 + (1 - ratio) * 25)
        ext_b = int(text_color[2] * 0.15 + (1 - ratio) * 25)
        draw_shaped_text(canvas, (x + step * angle_dx, y + step * angle_dy),
                         text, font_size=font_size, bold=True, text_color=(ext_r, ext_g, ext_b))

    # Crisp black outline boundary for mobile readability
    for ox in range(-3, 4):
        for oy in range(-3, 4):
            if ox * ox + oy * oy <= 9:
                draw_shaped_text(canvas, (x + ox, y + oy),
                                 text, font_size=font_size, bold=True, text_color=(0, 0, 0))

    # Front face of text
    draw_shaped_text(canvas, (x, y), text, font_size=font_size, bold=True, text_color=text_color)


def create_real_event_youtube_thumbnail(
    headline: str,
    category: str = "General",
    real_photo_path: Optional[str] = None,
    output_path: Optional[Path] = None,
    use_ai_generation: bool = True
) -> Path:
    """
    YouTube-Style Viral 3D Thumbnail (1280x720):
    1. AI Generation (Gemini Imagen -> OpenAI -> Pollinations Flux.1) or Real Event Photo.
    2. Vibrant color grade (enhanced contrast, clarity, sharpness).
    3. Multi-layer 3D extruded typography (Electric Yellow #FFE500 + Crisp White #FFFFFF).
    4. YouTube attention pill badge (RED / GOLD).
    """
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
    if not output_path:
        ts = int(time.time())
        output_path = THUMBNAILS_DIR / f"thumb_{ts}.jpg"
    else:
        output_path = Path(output_path)

    w, h = 1280, 720
    canvas = Image.new("RGBA", (w, h), (10, 14, 25, 255))

    bg_loaded = False
    temp_ai_bg = output_path.parent / f"ai_bg_{int(time.time())}.jpg"

    # Option A: Try AI-generated viral thumbnail visual if requested
    if use_ai_generation:
        try:
            prompt = generate_ai_thumbnail_prompt(headline, category)
            # Try Gemini -> OpenAI -> Flux
            if fetch_ai_image_gemini(prompt, temp_ai_bg) or \
               fetch_ai_image_openai(prompt, temp_ai_bg) or \
               fetch_ai_image_flux(prompt, temp_ai_bg):
                if temp_ai_bg.exists() and temp_ai_bg.stat().st_size > 5000:
                    real_photo_path = str(temp_ai_bg)
                    logger.info(f"🖼️ [Thumbnail Engine] Using AI-generated visual background for thumbnail.")
        except Exception as e:
            logger.warning(f"AI thumbnail background note: {e}")

    # Option B: Load Photo (AI visual or on-ground press photo)
    if real_photo_path and os.path.exists(str(real_photo_path)):
        try:
            raw_p = Image.open(real_photo_path).convert("RGBA")
            scale = max(w / float(raw_p.width), h / float(raw_p.height))
            sw, sh = int(raw_p.width * scale), int(raw_p.height * scale)
            scaled_p = raw_p.resize((sw, sh), Image.Resampling.LANCZOS)
            cx = (sw - w) // 2
            cy = max(0, (sh - h) // 4)
            cropped_p = scaled_p.crop((cx, cy, cx + w, cy + h))

            rgb_p = cropped_p.convert("RGB")
            # Enhance photo vibrancy (YouTube CTR style)
            rgb_p = ImageEnhance.Contrast(rgb_p).enhance(1.15)
            rgb_p = ImageEnhance.Color(rgb_p).enhance(1.20)
            rgb_p = ImageEnhance.Sharpness(rgb_p).enhance(1.35)
            canvas.paste(rgb_p.convert("RGBA"), (0, 0))
            bg_loaded = True
        except Exception as e:
            logger.warning(f"Could not load background image for thumbnail: {e}")

    # Clean up temp AI background file
    if temp_ai_bg.exists():
        try:
            temp_ai_bg.unlink()
        except Exception:
            pass

    # ── Lower-Third Gradient for Headline Contrast ──
    grad_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad_layer)
    y_start = int(h * 0.52)
    for y in range(y_start, h):
        factor = (y - y_start) / float(h - y_start)
        alpha = int(210 * (factor ** 1.4))
        gd.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, grad_layer)

    # ── YouTube Attention Pill Badge (Top-Left) ──
    badge_draw = ImageDraw.Draw(canvas)
    bx, by, bw, bh_px = 44, 38, 230, 44
    # 3D shadow for badge
    badge_draw.rounded_rectangle(
        [(bx + 3, by + 3), (bx + bw + 3, by + bh_px + 3)],
        radius=8, fill=(0, 0, 0, 180)
    )
    # Red gradient badge
    badge_draw.rounded_rectangle(
        [(bx, by), (bx + bw, by + bh_px)],
        radius=8, fill=(225, 20, 35, 255),
        outline=(255, 100, 100, 220), width=2
    )
    badge_text = "🔴 LIVE EXCLUSIVE"
    draw_shaped_text(canvas, (bx + 16, by + 9), badge_text, font_size=21, bold=True, text_color=(255, 255, 255))

    # ── 3D Extruded Two-Line Headline ──
    line1, line2 = generate_short_thumbnail_headline(headline, category)

    font_sz_l1 = 70 if len(line1) > 16 else 80
    font_sz_l2 = 60 if len(line2) > 20 else 68

    y_l1 = int(h * 0.64)
    y_l2 = int(h * 0.80)
    x_txt = 48

    # Line 1: Electric Yellow with 3D Depth Extrusion
    draw_3d_text_extrusion(
        canvas=canvas,
        pos=(x_txt, y_l1),
        text=line1,
        font_size=font_sz_l1,
        text_color=(255, 230, 0),
        depth=8,
        angle_dx=2,
        angle_dy=3
    )

    # Line 2: Crisp White with 3D Depth Extrusion
    draw_3d_text_extrusion(
        canvas=canvas,
        pos=(x_txt, y_l2),
        text=line2,
        font_size=font_sz_l2,
        text_color=(255, 255, 255),
        depth=7,
        angle_dx=2,
        angle_dy=3
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path), "JPEG", quality=96)
    logger.info(f"✅ [Viral YouTube 3D Thumbnail] Created: {output_path.name}")
    return output_path


# Backward compatibility aliases
create_ai_youtube_thumbnail = create_real_event_youtube_thumbnail