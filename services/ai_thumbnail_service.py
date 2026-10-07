import os
import sys
import time
import urllib.parse
import requests
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw

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
        f"You are an expert TV news thumbnail director and AI visual prompt engineer.\n"
        f"Headline: '{clean_hl}'\n"
        f"Category: {category}\n\n"
        f"Write a highly detailed, dramatic, photorealistic image prompt (in English) suitable for an AI image generator (like Flux / Imagen / DALL-E 3) "
        f"to create a compelling news thumbnail background for this exact news event.\n\n"
        f"Rules:\n"
        f"- Describe the main subject, setting, dramatic lighting, expressive atmosphere, and documentary news photo style.\n"
        f"- Include keywords: cinematic lighting, 8k uhd, editorial press photography, dramatic news visual, sharp focus.\n"
        f"- Avoid text in the image (text will be added in overlay).\n"
        f"- Keep the prompt under 45 words.\n"
        f"- Return ONLY the prompt text without any introductory commentary or quotes."
    )
    try:
        res = generate_text(prompt, temperature=0.25)
        res_clean = res.strip().strip('"').strip("'")
        if len(res_clean) > 20:
            return res_clean
    except Exception as e:
        logger.warning(f"AI Prompt generation note: {e}")

    return f"Cinematic dramatic editorial press photo of {clean_hl}, {category} news event, dramatic studio lighting, 8k resolution, documentary photojournalism"


def fetch_ai_image_gemini(prompt: str, output_path: Path) -> bool:
    """Generates image using Google Gemini Imagen API if GEMINI_API_KEY is available."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        logger.info("  🎨 Generating image via Google Gemini Imagen 3...")
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
            r = requests.get(img_url, timeout=20)
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
        logger.info(f"  🎨 Generating photorealistic image via Flux.1 (Pollinations AI)...")
        logger.info(f"     Prompt: '{prompt[:90]}...'")
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux&nologo=true&seed={int(time.time()) % 10000}"
        r = requests.get(url, timeout=35)
        if r.status_code == 200 and len(r.content) > 10000:
            output_path.write_bytes(r.content)
            logger.info("  ✅ Flux.1 AI Image Generation succeeded!")
            return True
        else:
            logger.warning(f"  Flux.1 generation returned HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"  Flux.1 generation error: {e}")
from PIL import ImageEnhance


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
            f"You are the head of YouTube packaging for a top Hindi news channel (Aaj Tak / ABP News).\n"
            f"ARTICLE TITLE: '{clean}'\n"
            f"CATEGORY: {category}\n\n"
            f"Create a high-CTR 2-line YouTube thumbnail text in HINDI (Devanagari script, max 3-4 words per line).\n"
            f"Line 1 MUST be a dramatic high-stakes hook (e.g. '20 सांसद बाहर?', 'भीषण तबाही!', 'संसद में भूचाल!').\n"
            f"Line 2 MUST be the key subject/entity (e.g. 'बड़ा फैसला', 'महुआ मोइत्रा का दावा', 'सैकड़ों लापता').\n\n"
            f"Respond ONLY with a JSON list of two strings: [\"LINE_1\", \"LINE_2\"]"
        )
        res = generate_text(prompt, temperature=0.2, max_tokens=60)
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


def create_real_event_youtube_thumbnail(
    headline: str,
    category: str = "General",
    real_photo_path: str = "",
    output_path: Optional[Path] = None
) -> Path:
    """
    Cinematic Dark YouTube Thumbnail (1280x720):
    1. Full-frame photo with deep cinematic colour grading (dark, high-contrast).
    2. Full-frame multi-stop gradient: black vignette all edges + heavy bottom.
    3. Subtle teal/blue left-edge glow for depth.
    4. Top-left red LIVE pill badge.
    5. Two-line glowing Hindi headline:
       - Line 1: Electric Gold with outer glow halo
       - Line 2: Pure White with subtle glow
    No channel name / logo.
    """
    from PIL import ImageFilter, ImageChops
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
    if not output_path:
        ts = int(time.time())
        output_path = THUMBNAILS_DIR / f"thumb_clean_{ts}.jpg"
    else:
        output_path = Path(output_path)

    w, h = 1280, 720
    canvas = Image.new("RGBA", (w, h), (5, 8, 18, 255))

    # ── 1. Photo with cinematic grade ──────────────────────────────────────
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
            # Enhance photo clarity and vibrant natural color (NO darkening)
            rgb_p = ImageEnhance.Contrast(rgb_p).enhance(1.08)
            rgb_p = ImageEnhance.Color(rgb_p).enhance(1.06)
            rgb_p = ImageEnhance.Sharpness(rgb_p).enhance(1.30)
            canvas.paste(rgb_p.convert("RGBA"), (0, 0))
        except Exception as e:
            logger.warning(f"  Could not load photo for thumbnail: {e}")

    # ── 2. Subtle Lower-Third Gradient Only (Behind headline text only) ─────────
    # Zero shadow over top 65% — preserves 100% natural lighting, face details, and background
    grad_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad_layer)
    y_start = int(h * 0.58)
    for y in range(y_start, h):
        factor = (y - y_start) / float(h - y_start)
        alpha = int(185 * (factor ** 1.6))
        gd.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, grad_layer)

    # ── 3. LIVE Alert Badge (top-left) ───────────────────────────────────────
    badge_draw = ImageDraw.Draw(canvas)
    bx, by, bw, bh_px = 44, 38, 220, 42
    # Badge shadow
    badge_draw.rounded_rectangle(
        [(bx + 2, by + 2), (bx + bw + 2, by + bh_px + 2)],
        radius=7, fill=(0, 0, 0, 140)
    )
    # Badge fill
    badge_draw.rounded_rectangle(
        [(bx, by), (bx + bw, by + bh_px)],
        radius=7, fill=(210, 15, 35, 250),
        outline=(255, 80, 80, 200), width=2
    )
    draw_shaped_text(canvas, (bx + 14, by + 8), "SRJ UNDERRATED", font_size=22, bold=True, text_color=(255, 255, 255))

    # ── 4. Two-line glowing headline with crisp outline ──────────────────────
    line1, line2 = generate_short_thumbnail_headline(headline, category)

    font_sz_l1 = 68 if len(line1) > 16 else 78
    font_sz_l2 = 58 if len(line2) > 20 else 66

    y_l1 = int(h * 0.65)
    y_l2 = int(h * 0.81)
    x_txt = 48

    # Crisp multi-directional 360-degree black stroke/shadow for 100% legibility
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                draw_shaped_text(canvas, (x_txt + dx, y_l1 + dy), line1, font_size=font_sz_l1, bold=True, text_color=(0, 0, 0))
                draw_shaped_text(canvas, (x_txt + dx, y_l2 + dy), line2, font_size=font_sz_l2, bold=True, text_color=(0, 0, 0))

    # Line 1 main — Electric Gold
    draw_shaped_text(canvas, (x_txt, y_l1), line1, font_size=font_sz_l1, bold=True, text_color=(255, 225, 0))

    # Line 2 main — Pure White
    draw_shaped_text(canvas, (x_txt, y_l2), line2, font_size=font_sz_l2, bold=True, text_color=(255, 255, 255))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path), "JPEG", quality=96)
    logger.info(f"✅ [Clean Bright Thumbnail] Created: {output_path.name}")
    return output_path


# Backward compatibility alias
create_ai_youtube_thumbnail = create_real_event_youtube_thumbnail
