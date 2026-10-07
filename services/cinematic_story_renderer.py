"""
services/cinematic_story_renderer.py
======================================
Cinematic Story-Type Video Renderer (1080p @ 15 FPS)
Produces documentary/investigative style videos with:

  • Full-screen photo with Ken Burns zoom+pan per slide
  • Deep cinematic vignette (dark edges + heavy bottom gradient)
  • 4 story-arc slide types: HOOK → BACKGROUND → DATA → IMPACT
  • Animated lower-third text fly-in (slides from left)
  • Prominent data facts box (numbers, dates highlighted)
  • Animated 🔴 LIVE badge with pulsing beacon
  • Scrolling Hindi news ticker at bottom
  • Smooth cross-fade between slides (0.4s blend)
  • No TV studio chrome — pure cinematic look
"""

import os
import sys
import math
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from moviepy import VideoClip, AudioFileClip

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.logger import logger
from utils.font_utils import sanitize_text, draw_shaped_text

# ─── Palette ──────────────────────────────────────────────────────────────────
GOLD      = (255, 210, 50)
WHITE     = (255, 255, 255)
RED_LIVE  = (210, 18, 35)
TEAL_GLOW = (0, 180, 220)
DARK_BG   = (5, 8, 18)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _cinematic_grade(img: Image.Image) -> Image.Image:
    """Apply dark cinematic colour grade: high contrast, slight desaturate, darken."""
    img = ImageEnhance.Contrast(img).enhance(1.30)
    img = ImageEnhance.Color(img).enhance(0.85)
    img = ImageEnhance.Brightness(img).enhance(0.78)
    img = ImageEnhance.Sharpness(img).enhance(1.35)
    return img


def _build_vignette(w: int, h: int) -> Image.Image:
    """Creates a strong cinematic vignette layer (pre-built once)."""
    v = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    # Heavy bottom gradient (text area)
    for y in range(h):
        f = max(0.0, (y - h * 0.28) / (h * 0.72))
        a = int(255 * min(1.0, f ** 1.4))
        d.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    # Subtle top dark
    for y in range(int(h * 0.30)):
        f = 1.0 - y / (h * 0.30)
        a = int(140 * f ** 2.0)
        d.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    # Left edge
    for x in range(int(w * 0.30)):
        f = 1.0 - x / (w * 0.30)
        a = int(130 * f ** 2.0)
        d.line([(x, 0), (x, h)], fill=(0, 0, 0, a))
    # Right edge
    for x in range(int(w * 0.20)):
        f = 1.0 - x / (w * 0.20)
        a = int(100 * f ** 2.0)
        d.line([(w - x, 0), (w - x, h)], fill=(0, 0, 0, a))
    return v


def _ken_burns(photo: Image.Image, w: int, h: int, progress: float,
               zoom_start: float = 1.0, zoom_end: float = 1.06,
               pan_dx: float = 0.0, pan_dy: float = 0.0) -> Image.Image:
    """
    Apply Ken Burns effect: smooth crop + resize.
    Crops directly from the oversized source photo then resizes to (w, h).
    """
    orig_w, orig_h = photo.size
    zoom = zoom_start + (zoom_end - zoom_start) * progress
    # Sub-window size inversely proportional to zoom
    crop_w = max(100, min(orig_w, int(orig_w / zoom)))
    crop_h = max(100, min(orig_h, int(orig_h / zoom)))

    # Pan offset
    max_pan_x = orig_w - crop_w
    max_pan_y = orig_h - crop_h
    cx = int(max_pan_x / 2.0 + pan_dx * progress * 25)
    cy = int(max_pan_y / 2.0 + pan_dy * progress * 15)
    cx = max(0, min(cx, max_pan_x))
    cy = max(0, min(cy, max_pan_y))

    cropped = photo.crop((cx, cy, cx + crop_w, cy + crop_h))
    return cropped.resize((w, h), Image.Resampling.BILINEAR)


def _draw_live_badge(canvas: Image.Image, t: float, x: int = 40, y: int = 36):
    """Animated SRJ UNDERRATED badge with pulsing beacon."""
    d = ImageDraw.Draw(canvas)
    bw, bh = 220, 44
    # Shadow
    d.rounded_rectangle([(x+3, y+3), (x+bw+3, y+bh+3)], radius=8, fill=(0, 0, 0, 160))
    # Fill
    d.rounded_rectangle([(x, y), (x+bw, y+bh)], radius=8,
                         fill=RED_LIVE, outline=(255, 80, 80, 220), width=2)
    draw_shaped_text(canvas, (x+14, y+9), "SRJ UNDERRATED", font_size=22, bold=True,
                     text_color=WHITE)
    # Pulsing dot overlay
    pulse = 0.5 + 0.5 * math.sin(t * 6.0)
    r = int(5 + 3 * pulse)
    d.ellipse([(x+14-r, y+22-r), (x+14+r, y+22+r)],
              fill=(255, int(60 + 60*pulse), int(60 + 60*pulse)))


def _draw_category_tag(canvas: Image.Image, category: str, x: int = 40, y: int = 90):
    """Small category tag below LIVE badge."""
    d = ImageDraw.Draw(canvas)
    cat = category.upper()[:18]
    d.rounded_rectangle([(x, y), (x+180, y+30)], radius=5,
                         fill=(20, 30, 60, 200), outline=GOLD, width=1)
    draw_shaped_text(canvas, (x+10, y+6), cat, font_size=16, bold=True, text_color=GOLD)


def _draw_slide_label(canvas: Image.Image, label: str, slide_num: int, total: int,
                      w: int, y: int = 36):
    """Top-right slide type label + progress dots."""
    d = ImageDraw.Draw(canvas)
    rx = w - 40
    # Label text (right-aligned)
    draw_shaped_text(canvas, (rx - 220, y + 8), label, font_size=18, bold=True,
                     text_color=(200, 200, 200))
    # Progress dots
    dot_y = y + 30
    for i in range(total):
        cx_dot = rx - (total - i - 1) * 18 - 10
        color = GOLD if i == slide_num else (80, 80, 80)
        d.ellipse([(cx_dot-5, dot_y-5), (cx_dot+5, dot_y+5)], fill=color)


def _draw_lower_third_headline(canvas: Image.Image, line1: str, line2: str,
                                w: int, h: int, anim_progress: float):
    """
    Sleek broadcast lower-third plate:
    - High-contrast glassmorphic card with metallic gold and crimson rails.
    - Clean Hind typography without distorted multi-stroke outlines.
    - Zero left-edge clipping (x_base locked at safe margin).
    """
    ease = min(1.0, anim_progress * 3.0)
    if ease <= 0:
        return

    y_shift = int((1.0 - ease) * 15)
    card_x = 50
    card_y = (h - 280) + y_shift
    card_w = min(1500, w - 100)
    card_h = 175

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)

    card_alpha = int(230 * ease)
    cd.rounded_rectangle([(0, 0), (card_w, card_h)], radius=12,
                         fill=(8, 14, 28, card_alpha),
                         outline=(50, 70, 110, int(180 * ease)), width=1)
    # Glowing top accent stripe
    cd.rounded_rectangle([(0, 0), (card_w, 4)], radius=2,
                         fill=(255, 204, 0, int(255 * ease)))
    # Left crimson accent rail
    cd.rounded_rectangle([(0, 0), (8, card_h)], radius=2,
                         fill=(220, 20, 35, int(255 * ease)))

    # Live Report Pill Badge
    cd.rounded_rectangle([(25, 14), (185, 40)], radius=5,
                         fill=(220, 20, 35, int(240 * ease)))
    draw_shaped_text(card, (36, 18), "⚡ LIVE REPORT", font_size=15, bold=True,
                     text_color=WHITE)

    f1_size = 46 if len(line1) <= 35 else (40 if len(line1) <= 50 else 34)
    f2_size = 32 if len(line2) <= 50 else (28 if len(line2) <= 70 else 24)

    # Line 1: Main hook headline in Electric Gold
    draw_shaped_text(card, (25, 48), line1[:60], font_size=f1_size, bold=True,
                     text_color=GOLD, shadow=True)

    # Line 2: Context subtitle in Clean White
    draw_shaped_text(card, (25, 108), line2[:80], font_size=f2_size, bold=False,
                     text_color=(245, 248, 255), shadow=True)

    canvas.paste(card, (card_x, card_y), card)


def _draw_fact_bullets(canvas: Image.Image, bullets: List[str], w: int, h: int,
                        anim_progress: float):
    """Clean bullet cards with zero clipping and high contrast."""
    x_base = 55
    y_start = int(h * 0.54)
    line_h = 58

    for i, bullet in enumerate(bullets[:4]):
        local_p = max(0.0, (anim_progress - i * 0.12) * 2.5)
        ease = min(1.0, local_p)
        if ease <= 0:
            continue

        y = y_start + i * line_h
        y_shift = int((1.0 - ease) * 10)
        clean = sanitize_text(str(bullet))[:80]

        # Dark glass backing strip for readability
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([(x_base - 5, y + y_shift - 6), (min(w - 60, x_base + 1100), y + y_shift + 42)],
                            radius=8, fill=(8, 14, 28, int(190 * ease)))

        # Bullet marker
        draw_shaped_text(canvas, (x_base + 10, y + y_shift), "▶",
                         font_size=22, bold=True, text_color=GOLD)
        # Bullet text
        draw_shaped_text(canvas, (x_base + 44, y + y_shift + 2), clean,
                         font_size=28, bold=False, text_color=WHITE, shadow=True)


def _draw_data_box(canvas: Image.Image, facts: List[str], w: int, h: int,
                    anim_progress: float):
    """Floating glass card showing key facts in top-right."""
    ease = min(1.0, anim_progress * 2.2)
    if ease <= 0:
        return

    bx, by = w - 480, int(h * 0.38)
    bw, bh = 420, min(280, 55 + len(facts[:4]) * 58)

    card = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([(0, 0), (bw, bh)], radius=14,
                         fill=(8, 14, 35, int(210 * ease)),
                         outline=GOLD + (int(180 * ease),), width=2)

    cd.rounded_rectangle([(0, 0), (bw, 40)], radius=14,
                         fill=(185, 140, 30, int(200 * ease)))
    draw_shaped_text(card, (14, 8), "📊 KEY FACTS", font_size=20, bold=True,
                     text_color=(15, 15, 15))

    for i, fact in enumerate(facts[:4]):
        fy = 50 + i * 55
        f_text = sanitize_text(str(fact))[:55]
        draw_shaped_text(card, (14, fy), "•", font_size=24, bold=True, text_color=GOLD)
        draw_shaped_text(card, (34, fy + 2), f_text, font_size=21, bold=False,
                         text_color=WHITE)

    offset_y = int((1 - ease) * 30)
    canvas.paste(card, (bx, by + offset_y), card)


def _draw_ticker(canvas: Image.Image, ticker_text: str, t: float, w: int, h: int):
    """
    Enlarged broadcast news ticker at bottom:
    - 82px high strip with vibrant red boundary.
    - Large 30px bold headline typography.
    - Angled red Breaking News badge overlay for clean edge masking.
    """
    ty1, ty2 = h - 82, h
    d = ImageDraw.Draw(canvas)

    # Base dark container
    d.rectangle([(0, ty1), (w, ty2)], fill=(6, 10, 22))
    d.line([(0, ty1), (w, ty1)], fill=(225, 25, 45), width=3)

    # Scrolling headline text (30px bold)
    speed = 105
    clean_ticker = sanitize_text(ticker_text)
    est_item_w = max(w, len(clean_ticker) * 19)
    offset = int((t * speed) % est_item_w)

    text_y = ty1 + 22
    start_x = 300 - offset
    draw_shaped_text(canvas, (start_x, text_y), clean_ticker,
                     font_size=30, bold=True, text_color=WHITE)
    draw_shaped_text(canvas, (start_x + est_item_w, text_y), clean_ticker,
                     font_size=30, bold=True, text_color=WHITE)

    # Red Breaking News badge (drawn over top to matte the left scroll)
    badge_w = 280
    badge = Image.new("RGBA", (badge_w, ty2 - ty1), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.polygon([(0, 0), (badge_w, 0), (badge_w - 24, ty2 - ty1), (0, ty2 - ty1)],
               fill=(220, 20, 35, 255))
    draw_shaped_text(badge, (20, 22), "🔴 BREAKING NEWS", font_size=24,
                     bold=True, text_color=WHITE)
    canvas.paste(badge, (0, ty1), badge)


def _draw_source_tag(canvas: Image.Image, credit: str, w: int, h: int):
    """Small photo credit tag bottom-right."""
    if not credit:
        return
    d = ImageDraw.Draw(canvas)
    tag_y = h - 70
    tag_text = f"📷 {credit[:40]}"
    d.rectangle([(w - 360, tag_y), (w - 10, tag_y + 24)],
                 fill=(0, 0, 0, 140))
    draw_shaped_text(canvas, (w - 355, tag_y + 4),
                      tag_text, font_size=16, bold=False, text_color=(180, 180, 180))


# ─── Slide type definitions ────────────────────────────────────────────────────

SLIDE_TYPES = {
    0: {"label": "◆ OPENING",    "zoom_s": 1.00, "zoom_e": 1.07, "pan_dx":  0.3, "pan_dy": 0.2},
    1: {"label": "◆ BACKGROUND", "zoom_s": 1.04, "zoom_e": 1.00, "pan_dx": -0.4, "pan_dy": 0.0},
    2: {"label": "◆ EVIDENCE",   "zoom_s": 1.02, "zoom_e": 1.08, "pan_dx":  0.2, "pan_dy":-0.3},
    3: {"label": "◆ IMPACT",     "zoom_s": 1.06, "zoom_e": 1.00, "pan_dx": -0.2, "pan_dy": 0.2},
}


# ─── Master Renderer ──────────────────────────────────────────────────────────

def render_cinematic_story_video(
    headline: str,
    category: str,
    slide_takeaways: Optional[List[str]] = None,
    takeaway_points: Optional[List[str]] = None,
    photo_paths: Optional[List[str]] = None,
    photo_credits: Optional[List[str]] = None,
    audio_path: Optional[Path] = None,
    output_video_path: Optional[Path] = None,
    fps: int = 15,
    **kwargs
) -> Path:
    """
    Cinematic Story Video Renderer — full-screen Ken Burns photos,
    animated text, story arc slides, data box, scrolling ticker.
    Drop-in replacement for render_dynamic_broadcast_video().
    """
    if output_video_path is None:
        raise ValueError("output_video_path must be provided")

    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"🎬 [Cinematic Story Renderer] Starting: {output_video_path.name}")

    W, H = 1920, 1080

    # Resolve takeaways
    resolved_takeaways = slide_takeaways or takeaway_points or [
        "Breaking Development: Investigation teams actively deployed on ground",
        "Historical Background: Key decisions and timeline traced back to origin",
        "Official Action: Government agencies confirm findings and next steps",
        "Wide Impact: Citizens and institutions brace for long-term consequences"
    ]
    num_slides = max(2, min(len(resolved_takeaways), 5))
    resolved_credits = photo_credits or ["Verified News Wire"]

    # ── Audio ──────────────────────────────────────────────────────────────────
    if not audio_path or not audio_path.exists() or audio_path.stat().st_size < 1000:
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    audio_clip = AudioFileClip(str(audio_path))
    duration   = float(audio_clip.duration)
    logger.info(f"  🎙️ Audio: {duration:.1f}s")

    slide_dur    = duration / num_slides
    fade_dur     = min(0.40, slide_dur * 0.12)   # cross-fade length

    # ── Load + grade photos ────────────────────────────────────────────────────
    logger.info("  📸 Loading and grading photos...")
    graded_photos: List[Optional[Image.Image]] = []
    if photo_paths:
        for p in photo_paths:
            if p and os.path.exists(p):
                try:
                    raw = Image.open(p).convert("RGB")
                    # Scale to fill 1920×1080
                    scale = max(W / raw.width, H / raw.height) * 1.10  # 10% extra for KB
                    nw, nh = int(raw.width * scale), int(raw.height * scale)
                    scaled = raw.resize((nw, nh), Image.Resampling.LANCZOS)
                    graded = _cinematic_grade(scaled)
                    graded_photos.append(graded)
                except Exception as e:
                    logger.warning(f"Photo load failed {p}: {e}")
                    graded_photos.append(None)
            else:
                graded_photos.append(None)
    if not graded_photos:
        graded_photos.append(None)

    # ── Pre-build vignette (expensive — do once) ───────────────────────────────
    logger.info("  🎨 Pre-building cinematic vignette...")
    vignette = _build_vignette(W, H)

    # ── Ticker text ────────────────────────────────────────────────────────────
    clean_hl = sanitize_text(headline)
    ticker = (f"{clean_hl}   •   "
              + "   •   ".join(sanitize_text(t)[:60] for t in resolved_takeaways)
              + "   •   ")

    # ── Headline split (Line1 = hook, Line2 = context) ─────────────────────────
    words = clean_hl.split()
    if len(words) <= 4:
        line1 = clean_hl
        line2 = f"LIVE REPORT • {category.upper()}"
    else:
        total_len = sum(len(w) for w in words)
        mid_target = total_len // 2
        running = 0
        split_idx = len(words) // 2
        for i, w in enumerate(words):
            running += len(w) + 1
            if running >= mid_target:
                split_idx = max(2, min(i + 1, len(words) - 1))
                break
        line1 = " ".join(words[:split_idx])
        line2 = " ".join(words[split_idx:])

    # ── Frame compositor ───────────────────────────────────────────────────────
    def make_frame(t: float) -> np.ndarray:
        slide_idx  = min(num_slides - 1, int(t / slide_dur))
        t_in_slide = t - slide_idx * slide_dur
        progress   = min(1.0, t_in_slide / slide_dur)  # 0→1 within slide

        # Animation progress within slide (0→1 for first 40%)
        anim_p = min(1.0, t_in_slide / (slide_dur * 0.40))

        # Ken Burns for current slide
        s_cfg  = SLIDE_TYPES.get(slide_idx % 4, SLIDE_TYPES[0])
        photo  = graded_photos[slide_idx % len(graded_photos)]

        if photo is not None:
            frame_photo = _ken_burns(
                photo, W, H, progress,
                zoom_start=s_cfg["zoom_s"],
                zoom_end=s_cfg["zoom_e"],
                pan_dx=s_cfg["pan_dx"],
                pan_dy=s_cfg["pan_dy"]
            )
        else:
            frame_photo = Image.new("RGB", (W, H), DARK_BG)

        canvas = frame_photo.convert("RGBA")

        # Vignette
        canvas = Image.alpha_composite(canvas, vignette)

        # Cross-fade: if we're in transition window with next slide
        if t_in_slide < fade_dur and slide_idx > 0:
            prev_idx   = slide_idx - 1
            p_cfg      = SLIDE_TYPES.get(prev_idx % 4, SLIDE_TYPES[0])
            prev_photo = graded_photos[prev_idx % len(graded_photos)]
            if prev_photo is not None:
                prev_frame = _ken_burns(prev_photo, W, H, 1.0,
                                         zoom_start=p_cfg["zoom_s"],
                                         zoom_end=p_cfg["zoom_e"])
            else:
                prev_frame = Image.new("RGB", (W, H), DARK_BG)
            prev_canvas = Image.alpha_composite(prev_frame.convert("RGBA"), vignette)
            alpha_t     = t_in_slide / fade_dur  # 0→1 (fade new in)
            canvas      = Image.blend(prev_canvas, canvas, alpha_t)

        # Convert to RGB for drawing
        canvas = canvas.convert("RGB")

        # ── LIVE badge (always visible) ────────────────────────────────────────
        _draw_live_badge(canvas, t)
        _draw_category_tag(canvas, category)

        # ── Slide type label + progress dots ─────────────────────────────────
        label = s_cfg["label"]
        _draw_slide_label(canvas, label, slide_idx, num_slides, W)

        # ── Story content by slide type ───────────────────────────────────────
        if slide_idx == 0:
            # HOOK: big headline lower third
            _draw_lower_third_headline(canvas, line1, line2, W, H, anim_p)

        elif slide_idx == num_slides - 1:
            # IMPACT: headline + conclusion bullets
            _draw_lower_third_headline(canvas, line1, line2, W, H, anim_p)
            _draw_fact_bullets(canvas,
                                [f"Conclusion: {t}" for t in resolved_takeaways[-2:]],
                                W, H, max(0, anim_p - 0.3))

        else:
            # MIDDLE slides: bullets + optional data box
            idx_bullets = (slide_idx - 1) * 2
            bullets = resolved_takeaways[idx_bullets: idx_bullets + 2]
            _draw_fact_bullets(canvas, bullets, W, H, anim_p)

            # Data box on even middle slides
            if slide_idx % 2 == 0 and len(resolved_takeaways) > 2:
                data_facts = resolved_takeaways[:4]
                _draw_data_box(canvas, data_facts, W, H, max(0, anim_p - 0.2))

            # Subtle headline at very bottom for context
            draw_shaped_text(canvas, (55, int(H * 0.90)),
                              f"◆ {clean_hl[:75]}",
                              font_size=24, bold=False, text_color=(200, 200, 200))

        # ── Photo credit ──────────────────────────────────────────────────────
        credit = resolved_credits[slide_idx % len(resolved_credits)]
        _draw_source_tag(canvas, credit, W, H)

        # ── Scrolling ticker ──────────────────────────────────────────────────
        _draw_ticker(canvas, ticker, t, W, H)

        return np.array(canvas)

    # ── Encode ────────────────────────────────────────────────────────────────
    logger.info(f"  ⚡ Encoding {duration:.0f}s cinematic video @ {fps} FPS...")
    video_clip       = VideoClip(make_frame, duration=duration)
    video_with_audio = video_clip.with_audio(audio_clip)
    video_with_audio.write_videofile(
        str(output_video_path),
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        preset="ultrafast",
        threads=4,
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",
            "-crf", "20",
            "-tune", "zerolatency",
            "-movflags", "+faststart",
        ],
        logger=None
    )
    try:
        audio_clip.close()
    except Exception:
        pass
    video_clip.close()
    logger.info(f"✅ [Cinematic Story] Done: {output_video_path.name}")
    return output_video_path


# ─── Drop-in alias for existing callers ───────────────────────────────────────
render_dynamic_broadcast_video = render_cinematic_story_video
