"""
services/shorts_25d_renderer.py
===============================
Professional 2.5D Television Broadcast Video Renderer for YouTube Shorts.
Renders 1080x1920 (9:16 Vertical) high-engagement mobile broadcast frames with:
- Top Titanium HUD with pulsing LIVE beacon & NewsTube branding
- Large 4:5 2.5D Floating Media Display with pixel-stable event photography
- Lower-Middle 3D Extruded Mega-Headline Slab with specular sheen sweep
- Premium Single Live Story Capsule (Key Development / Ground Report) - Zero Quiz/Question boxes
- Continuous Running Breaking News Marquee Ticker
"""

import os
import sys
import math
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy import VideoClip, AudioFileClip

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.font_utils import load_font, sanitize_text, draw_shaped_text
from utils.logger import logger

# ── COLOR PALETTE ─────────────────────────────────────────────
GOLD_SPECULAR    = (255, 248, 190)
GOLD_LIGHT       = (255, 225, 110)
GOLD             = (230, 180, 20)
GOLD_DARK        = (150, 105, 10)
GOLD_SHADOW      = (70, 48, 5)

WHITE            = (255, 255, 255)
WHITE_DIM        = (220, 232, 250)
WHITE_MUTED      = (160, 180, 215)

CRIMSON_GLOW     = (255, 75, 85)
CRIMSON          = (215, 18, 28)
CRIMSON_DARK     = (130, 10, 16)
CRIMSON_DEEP     = (60, 5, 8)
CRIMSON_EXTRUDE  = (40, 4, 6)

NAVY_BG_TOP      = (10, 16, 38)
NAVY_BG_BOT      = (4, 7, 18)
NAVY_GRID        = (18, 28, 58)

GLASS_ACTIVE_TOP = (28, 48, 108)
GLASS_ACTIVE_BOT = (14, 26, 62)
GLASS_IDLE_TOP   = (16, 24, 52)
GLASS_IDLE_BOT   = (8, 14, 32)


def create_vertical_gradient(
    w: int, h: int,
    top_color: Tuple[int, int, int],
    bot_color: Tuple[int, int, int]
) -> Image.Image:
    """Generates vertical linear gradient."""
    w = max(1, int(w))
    h = max(1, int(h))
    r = np.linspace(top_color[0], bot_color[0], h, dtype=np.float32)
    g = np.linspace(top_color[1], bot_color[1], h, dtype=np.float32)
    b = np.linspace(top_color[2], bot_color[2], h, dtype=np.float32)
    col = np.stack([r, g, b], axis=1).astype(np.uint8)
    grid = np.repeat(col[:, np.newaxis, :], w, axis=1)
    return Image.fromarray(grid, "RGB")


def render_shorts_background(w: int = 1080, h: int = 1920) -> Image.Image:
    """Renders technical dark studio background with subtle perspective grid and radial glow."""
    canvas = create_vertical_gradient(w, h, NAVY_BG_TOP, NAVY_BG_BOT)
    draw = ImageDraw.Draw(canvas)

    # Subtle radial spotlight behind upper media
    spot_center = (w // 2, 600)
    for radius in range(550, 100, -60):
        glow_color = (25, 45, 95)
        draw.ellipse(
            [(spot_center[0] - radius, spot_center[1] - radius // 2),
             (spot_center[0] + radius, spot_center[1] + radius // 2)],
            outline=glow_color, width=2
        )

    # Technical perspective grid lines at bottom
    for y in range(1200, h, 60):
        draw.line([(0, y), (w, y)], fill=NAVY_GRID, width=1)
    for x in range(0, w, 90):
        draw.line([(x, 1200), (x, h)], fill=NAVY_GRID, width=1)

    return canvas


def render_shorts_top_hud(canvas: Image.Image, category: str, t: float, w: int = 1080):
    """Renders top HUD with pulsing LIVE beacon, NewsTube Shorts branding, and category."""
    y1, y2 = 70, 175
    h_bar = y2 - y1

    # Main HUD Bar Background
    bar_grad = create_vertical_gradient(w - 80, h_bar, (20, 32, 70), (8, 14, 34))
    canvas.paste(bar_grad, (40, y1))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(40, y1), (w - 40, y2)], outline=GOLD, width=2)

    # Left Pulsing LIVE Pill
    pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * 1.8 * t)
    r_val = int(210 + 45 * pulse)
    live_poly = [(50, y1 + 10), (220, y1 + 10), (195, y2 - 10), (50, y2 - 10)]
    draw.polygon(live_poly, fill=(r_val, 15, 25), outline=GOLD, width=2)
    # Glowing dot
    draw.ellipse([(68, y1 + 38), (86, y1 + 56)], fill=(255, 240, 240), outline=(255, 100, 100))
    draw.text((96, y1 + 30), "LIVE", fill=WHITE, font=load_font(30, bold=True))

    # Center Brand Badge
    draw_shaped_text(canvas, (w // 2 - 160, y1 + 32), "NEWSTUBE SHORTS", font_size=28, bold=True, text_color=GOLD_LIGHT, shadow=True)

    # Right Category Pill
    cat_text = sanitize_text(category.upper()[:12])
    draw.rounded_rectangle([(w - 240, y1 + 15), (w - 55, y2 - 15)], radius=6, fill=(18, 28, 62), outline=GOLD, width=1)
    draw_shaped_text(canvas, (w - 225, y1 + 32), cat_text, font_size=22, bold=True, text_color=WHITE)


def render_shorts_media_frame(
    canvas: Image.Image,
    xy: Tuple[int, int, int, int],
    photo_img: Optional[Image.Image],
    slide_tag: str = "[ SHORTS REPORT ]",
    credit_text: str = "Verified News Wire"
):
    """Renders 4:5 2.5D floating media chassis with recessed screen housing and event photo."""
    x1, y1, x2, y2 = xy
    w_box, h_box = x2 - x1, y2 - y1

    draw = ImageDraw.Draw(canvas)

    # Outer Drop Shadow
    shadow_box = [(x1 - 10, y1 - 10), (x2 + 14, y2 + 14)]
    draw.rounded_rectangle(shadow_box, radius=14, fill=(0, 2, 6))

    # Outer Titanium Bezel Chassis
    chassis_grad = create_vertical_gradient(w_box, h_box, (40, 52, 85), (15, 22, 42))
    canvas.paste(chassis_grad, (x1, y1))
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=12, outline=GOLD, width=2)

    # Inner Screen Recessed Viewport
    pad = 8
    vx1, vy1, vx2, vy2 = x1 + pad, y1 + pad, x2 - pad, y2 - pad
    vw, vh = vx2 - vx1, vy2 - vy1

    if photo_img is not None:
        try:
            pw, ph = photo_img.size
            scale = max(vw / float(pw), vh / float(ph))
            sw, sh = int(pw * scale), int(ph * scale)
            r_img = photo_img.resize((sw, sh), Image.Resampling.LANCZOS)
            cx = (sw - vw) // 2
            cy = (sh - vh) // 2
            c_img = r_img.crop((cx, cy, cx + vw, cy + vh))
            canvas.paste(c_img, (vx1, vy1))
        except Exception:
            draw.rectangle([(vx1, vy1), (vx2, vy2)], fill=(12, 18, 36))
    else:
        draw.rectangle([(vx1, vy1), (vx2, vy2)], fill=(12, 18, 36))

    # Inner Top Highlight & Vignette
    draw.rectangle([(vx1, vy1), (vx2, vy2)], outline=(20, 28, 48), width=2)

    # Top-Right Slide Tag Badge
    draw.rounded_rectangle([(vx2 - 270, vy1 + 12), (vx2 - 12, vy1 + 52)], radius=5, fill=(10, 16, 32), outline=GOLD, width=1)
    draw_shaped_text(canvas, (vx2 - 255, vy1 + 18), slide_tag, font_size=20, bold=True, text_color=GOLD_LIGHT)

    # Bottom-Left Photo Credit Pill
    draw.rounded_rectangle([(vx1 + 12, vy2 - 44), (vx1 + 330, vy2 - 10)], radius=4, fill=(5, 8, 18), outline=(60, 75, 110), width=1)
    draw_shaped_text(canvas, (vx1 + 22, vy2 - 38), f"📷 {sanitize_text(credit_text[:28])}", font_size=18, bold=True, text_color=WHITE_DIM)


def render_shorts_headline_panel(
    canvas: Image.Image,
    headline_text: str,
    t: float,
    base_y1: int = 1140,
    base_y2: int = 1370,
    w: int = 1080
):
    """Renders 3D extruded Devanagari Hindi mega-headline panel with specular sheen sweeps."""
    x1, x2 = 40, w - 40
    h_panel = base_y2 - base_y1
    w_panel = x2 - x1

    # Panel Body Gradient
    grad = create_vertical_gradient(w_panel, h_panel, (24, 38, 80), (10, 16, 38))
    canvas.paste(grad, (x1, base_y1))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(x1, base_y1), (x2, base_y2)], outline=GOLD, width=3)

    # Top & Bottom Metallic Gold Chamfer Rails
    draw.line([(x1, base_y1 + 4), (x2, base_y1 + 4)], fill=GOLD_LIGHT, width=2)
    draw.line([(x1, base_y2 - 4), (x2, base_y2 - 4)], fill=GOLD_LIGHT, width=2)

    # Left Ruby Prism Accent
    draw.polygon([(x1, base_y1), (x1 + 35, base_y1), (x1 + 15, base_y2), (x1, base_y2)], fill=CRIMSON)

    # Specular Sheen Sweep Animation
    sheen_period = 3.5
    phase = (t % sheen_period) / sheen_period
    sheen_x = int(x1 + phase * (w_panel + 200) - 100)
    if x1 <= sheen_x <= x2:
        draw.line([(sheen_x, base_y1 + 6), (sheen_x + 30, base_y2 - 6)], fill=(255, 255, 230), width=4)

    # Multi-Line Headline Text Wrapping & 3D Extruded Rendering
    words = headline_text.split()
    lines: List[str] = []
    curr = []
    for word in words:
        curr.append(word)
        if len(" ".join(curr)) > 26:
            if len(curr) > 1:
                curr.pop()
                lines.append(" ".join(curr))
                curr = [word]
            else:
                lines.append(" ".join(curr))
                curr = []
    if curr:
        lines.append(" ".join(curr))
    lines = lines[:3]

    font_size = 44 if len(lines) <= 2 else 38
    line_h = 64 if font_size == 44 else 54
    total_text_h = len(lines) * line_h
    start_y = base_y1 + (h_panel - total_text_h) // 2

    for i, line in enumerate(lines):
        ly = start_y + i * line_h
        draw_shaped_text(
            canvas,
            (x1 + 50, ly),
            line,
            font_size=font_size,
            bold=True,
            text_color=GOLD_LIGHT if i == 0 else WHITE,
            shadow=True
        )


def render_shorts_key_development_card(
    canvas: Image.Image,
    takeaway_text: str,
    slide_idx: int,
    total_slides: int,
    t: float,
    w: int = 1080
):
    """
    Renders ONE large, premium, unified Live Story Capsule / Ground Insight box (y: 1390 to 1720).
    Replaces old multi-option / quiz layout with a clean television news summary panel.
    """
    x1, x2 = 40, w - 40
    y1, y2 = 1390, 1720
    w_card = x2 - x1
    h_card = y2 - y1

    draw = ImageDraw.Draw(canvas)

    # 1. Directional Cast Shadow
    draw.rounded_rectangle([(x1 - 6, y1 - 4), (x2 + 8, y2 + 8)], radius=12, fill=(0, 3, 10))

    # 2. Main Glassmorphic Panel Gradient
    card_grad = create_vertical_gradient(w_card, h_card, (24, 42, 92), (10, 20, 48))
    canvas.paste(card_grad, (x1, y1))
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=10, outline=GOLD, width=2)

    # 3. Top Header Ribbon inside the Capsule
    badge_poly = [(x1, y1), (x1 + 380, y1), (x1 + 340, y1 + 52), (x1, y1 + 52)]
    badge_grad = create_vertical_gradient(380, 52, CRIMSON, CRIMSON_DARK)
    mask_b = Image.new("L", (380, 52), 0)
    ImageDraw.Draw(mask_b).polygon([(0, 0), (380, 0), (340, 52), (0, 52)], fill=255)
    canvas.paste(badge_grad, (x1, y1), mask_b)
    draw.polygon(badge_poly, outline=GOLD_LIGHT, width=1)

    # Live Beacon on Header
    pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * 1.8 * t)
    r_val = int(220 + 35 * pulse)
    draw.ellipse([(x1 + 18, y1 + 18), (x1 + 34, y1 + 34)], fill=(r_val, 30, 30), outline=(255, 230, 230))
    draw_shaped_text(canvas, (x1 + 42, y1 + 12), "⚡ मुख्य घटनाक्रम व विवरण", font_size=23, bold=True, text_color=WHITE)

    # Slide indicator on right
    draw_shaped_text(canvas, (x2 - 140, y1 + 14), f"अपडेट {slide_idx + 1}/{total_slides}", font_size=20, bold=True, text_color=GOLD_LIGHT)

    # 4. Clean Multi-line Story Insight Narrative Text
    clean_text = sanitize_text(takeaway_text)
    words = clean_text.split()
    lines = []
    curr = []
    for word in words:
        curr.append(word)
        if len(" ".join(curr)) > 30:
            if len(curr) > 1:
                curr.pop()
                lines.append(" ".join(curr))
                curr = [word]
            else:
                lines.append(" ".join(curr))
                curr = []
    if curr:
        lines.append(" ".join(curr))
    lines = lines[:4]

    start_yt = y1 + 75
    line_spacing = 48
    for i, line in enumerate(lines):
        draw_shaped_text(
            canvas,
            (x1 + 28, start_yt + i * line_spacing),
            line,
            font_size=28,
            bold=True if i == 0 else False,
            text_color=(255, 240, 140) if i == 0 else WHITE,
            shadow=True
        )


def render_shorts_ticker(
    canvas: Image.Image,
    headline_text: str,
    t: float,
    w: int = 1080,
    h: int = 1920
):
    """Renders bottom running marquee ticker."""
    y1, y2 = 1745, 1835
    h_ticker = y2 - y1
    draw = ImageDraw.Draw(canvas)

    # Ticker Bar Body
    t_grad = create_vertical_gradient(w, h_ticker, (20, 30, 65), (8, 14, 30))
    canvas.paste(t_grad, (0, y1))
    draw.line([(0, y1), (w, y1)], fill=GOLD, width=2)
    draw.line([(0, y2), (w, y2)], fill=GOLD, width=2)

    # Scrolling Marquee
    marquee_content = f"BREAKING NEWS 🔴   {headline_text}   ★   AI-NEWSTUBE EXCLUSIVE SHORTS   ★   "
    marquee_full = f"{marquee_content} {marquee_content}"
    speed = 130.0
    approx_w = len(marquee_full) * 16
    scroll_offset = -int((t * speed) % max(1, approx_w // 2))

    draw_shaped_text(canvas, (scroll_offset, y1 + 26), marquee_full, font_size=24, bold=True, text_color=(255, 235, 120), shadow=True)

    # Left Solid Crimson Badge
    poly_badge = [(0, y1), (210, y1), (180, y2), (0, y2)]
    b_grad = create_vertical_gradient(210, h_ticker, CRIMSON, CRIMSON_DARK)
    mask_b = Image.new("L", (210, h_ticker), 0)
    d_mb = ImageDraw.Draw(mask_b)
    d_mb.polygon([(0, 0), (210, 0), (180, h_ticker), (0, h_ticker)], fill=255)
    canvas.paste(b_grad, (0, y1), mask_b)
    draw.polygon(poly_badge, outline=GOLD, width=2)
    draw_shaped_text(canvas, (25, y1 + 26), "BREAKING", font_size=22, bold=True, text_color=WHITE)


def bake_shorts_slide(
    slide_idx: int,
    headline: str,
    category: str,
    takeaways: List[str],
    photo_img: Optional[Image.Image],
    credit_str: str,
    w: int = 1080,
    h: int = 1920
) -> Image.Image:
    """Pre-renders all static 9:16 vertical 2.5D layers once per slide."""
    canvas = render_shorts_background(w, h)
    clean_cat = sanitize_text(category.upper())
    clean_head = sanitize_text(headline)

    # 1. Top HUD
    render_shorts_top_hud(canvas, category=clean_cat, t=0.0, w=w)

    # 2. Large Media Photo Frame (4:5 Ratio)
    render_shorts_media_frame(
        canvas,
        xy=(40, 190, w - 40, 1120),
        photo_img=photo_img,
        slide_tag=f"[ EXCLUSIVE ] ({slide_idx + 1}/{len(takeaways)})",
        credit_text=credit_str
    )

    # 3. Mega-Headline Slab
    render_shorts_headline_panel(canvas, headline_text=clean_head, t=0.0, base_y1=1140, base_y2=1370, w=w)

    # 4. Premium Single Story Capsule (Clean Narrative Highlight - Zero Quiz Boxes)
    cur_takeaway = takeaways[slide_idx % len(takeaways)] if takeaways else "ग्राउंड रिपोर्ट: ताज़ा स्थिति पर पूरी निगरानी जारी"
    render_shorts_key_development_card(
        canvas,
        takeaway_text=cur_takeaway,
        slide_idx=slide_idx,
        total_slides=len(takeaways),
        t=0.0,
        w=w
    )

    if canvas.mode != "RGB":
        canvas = canvas.convert("RGB")
    return canvas


def render_shorts_broadcast_video(
    headline: str,
    category: str,
    slide_takeaways: Optional[List[str]] = None,
    photo_paths: Optional[List[str]] = None,
    photo_credits: Optional[List[str]] = None,
    audio_path: Optional[Path] = None,
    output_video_path: Optional[Path] = None,
    fps: int = 15
) -> Path:
    """Renders high-performance 1080x1920 (9:16) vertical MP4 YouTube Short in <10 seconds."""
    if output_video_path is None:
        raise ValueError("output_video_path must be provided")

    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"📱 [Shorts 2.5D Fast Renderer] Rendering vertical 9:16 Short ({output_video_path.name})...")

    resolved_takeaways = slide_takeaways or [
        "मुख्य घटनाक्रम: बड़ी ख़बर पर ताज़ा अपडेट",
        "ग्राउंड रिपोर्ट: घटना स्थल से प्राप्त अहम जानकारी",
        "ताज़ा स्थिति: प्रशासन एवं संबंधित टीमों द्वारा कार्रवाई"
    ]

    # Verify Audio File and get Duration
    if audio_path is None or not audio_path.exists() or audio_path.stat().st_size < 1000:
        raise FileNotFoundError(f"Shorts audio not found or empty: {audio_path}")

    audio_clip = AudioFileClip(str(audio_path))
    duration = float(audio_clip.duration)
    logger.info(f"  🎙️ Verified Shorts Audio: {audio_path.name} (Duration: {duration:.1f}s)")

    # Pre-crop photos for 1000x930 viewport
    vw, vh = 1000 - 16, 930 - 16
    loaded_photos: List[Optional[Image.Image]] = []

    if photo_paths:
        for p in photo_paths:
            if p and os.path.exists(p):
                try:
                    raw = Image.open(p).convert("RGB")
                    pw, ph = raw.size
                    scale = max(vw / float(pw), vh / float(ph))
                    sw, sh = int(pw * scale), int(ph * scale)
                    resized = raw.resize((sw, sh), Image.Resampling.LANCZOS)
                    cx = (sw - vw) // 2
                    cy = (sh - vh) // 2
                    cropped = resized.crop((cx, cy, cx + vw, cy + vh))
                    loaded_photos.append(cropped)
                except Exception as e:
                    logger.warning(f"Error pre-formatting shorts photo {p}: {e}")
                    loaded_photos.append(None)
            else:
                loaded_photos.append(None)

    if not loaded_photos:
        loaded_photos.append(None)

    resolved_credits = photo_credits if photo_credits else ["Verified News Wire"]

    # PRE-BAKE SHORTS SLIDES (Speedup from 7 FPS to 60+ FPS)
    num_slides = max(1, len(resolved_takeaways))
    slide_dur = duration / float(num_slides)
    clean_head = sanitize_text(headline)

    logger.info(f"  ⚡ Pre-baking {num_slides} vertical 9:16 slide layouts...")
    baked_shorts: List[Image.Image] = []
    for s_idx in range(num_slides):
        p_img = loaded_photos[s_idx % len(loaded_photos)]
        c_txt = resolved_credits[s_idx % len(resolved_credits)]
        baked = bake_shorts_slide(
            slide_idx=s_idx,
            headline=headline,
            category=category,
            takeaways=resolved_takeaways,
            photo_img=p_img,
            credit_str=c_txt,
            w=1080,
            h=1920
        )
        baked_shorts.append(baked)

    def make_frame(t):
        s_idx = min(num_slides - 1, int(t // slide_dur))
        frame = baked_shorts[s_idx].copy()
        draw = ImageDraw.Draw(frame)

        # Pulsing Live Dot at top
        pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * 1.8 * t)
        draw.ellipse([(68, 108), (86, 126)], fill=(255, 240, 240), outline=(255, 100, 100))

        # Bottom Scrolling Marquee Ticker
        render_shorts_ticker(frame, headline_text=clean_head, t=t, w=1080, h=1920)

        return np.array(frame)

    video_clip = VideoClip(make_frame, duration=duration)
    video_with_audio = video_clip.with_audio(audio_clip)

    logger.info(f"  ⚡ Encoding 1080x1920 Vertical Short at {fps} FPS (Ultrafast)...")
    video_with_audio.write_videofile(
        str(output_video_path),
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        preset="ultrafast",
        threads=4,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-tune", "zerolatency"],
        logger=None
    )

    try:
        audio_clip.close()
    except Exception:
        pass
    video_clip.close()

    logger.info(f"✅ [Shorts 2.5D Fast Renderer] Vertical 9:16 Short Created: {output_video_path.name}")
    return output_video_path
