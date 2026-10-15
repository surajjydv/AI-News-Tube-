"""
services/broadcast_25d_engine.py
================================
True 2.5D Physical Television Broadcast Graphics Engine.
Renders multi-layered broadcast television graphics using procedural extrusion blocks,
directional cast shadows, metallic chamfers, recessed monitor housings,
and physically elevated 2.5D glass panels without relying on flat 2D overlays.

Layer Stack:
1. Technical Broadcast Background (radial spotlight + perspective grid + dark vignette)
2. Top Header Ribbon (layered depth ribbon + titanium chassis + glowing live pill)
3. Left Story Cards (physical 2.5D extruded glass blocks + active card elevation)
4. Floating Media Display Chassis (rear cast shadow + 8px titanium extrusion + recessed screen)
5. Lower-Third Mega-Headline Slab (trapezoid chassis + faceted ruby chevron + 3D typography)
6. Dual-Row Tickers (extruded ruby breaking marquee + metallic market ribbon)
7. Directional Key Lighting & Specular Sheens
"""

import math
import time
from pathlib import Path
from typing import List, Tuple, Optional, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
from utils.font_utils import load_font, sanitize_text, draw_shaped_text

# ── BROADCAST COLOR PALETTE (PREMIUM TV BROADCAST) ────────────
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

NAVY_BG_TOP      = (12, 18, 42)
NAVY_BG_BOT      = (4, 7, 18)
NAVY_GRID        = (20, 30, 62)

SAPPHIRE_TOP     = (26, 52, 120)
SAPPHIRE_BOT     = (12, 24, 60)
SAPPHIRE_EXTRUDE = (6, 12, 32)

GLASS_ACTIVE_TOP = (28, 48, 108)
GLASS_ACTIVE_BOT = (14, 26, 62)
GLASS_ACTIVE_EXT = (8, 14, 36)

GLASS_IDLE_TOP   = (16, 24, 52)
GLASS_IDLE_BOT   = (8, 14, 32)
GLASS_IDLE_EXT   = (4, 7, 18)

CYAN_HIGHLIGHT   = (90, 165, 255)
CYAN_GLOW        = (35, 95, 180)


# ── PROCEDURAL GRADIENTS & RADIAL_GRADIENT_CACHE = {}
_GRADIENT_CACHE = {}
_BG_CACHE = {}

def create_vertical_gradient(
    w: int, h: int,
    top_color: Tuple[int, int, int],
    bot_color: Tuple[int, int, int],
    mid_color: Optional[Tuple[int, int, int]] = None,
    mid_pos: float = 0.5
) -> Image.Image:
    """Generates vertical linear gradient with fast in-memory caching."""
    w = max(1, int(w))
    h = max(1, int(h))
    cache_key = (w, h, top_color, bot_color, mid_color, mid_pos)
    if cache_key in _GRADIENT_CACHE:
        return _GRADIENT_CACHE[cache_key].copy()

    if mid_color is None:
        r = np.linspace(top_color[0], bot_color[0], h, dtype=np.float32)
        g = np.linspace(top_color[1], bot_color[1], h, dtype=np.float32)
        b = np.linspace(top_color[2], bot_color[2], h, dtype=np.float32)
    else:
        h1 = max(1, int(h * mid_pos))
        h2 = max(1, h - h1)
        r = np.concatenate([np.linspace(top_color[0], mid_color[0], h1, dtype=np.float32),
                            np.linspace(mid_color[0], bot_color[0], h2, dtype=np.float32)])
        g = np.concatenate([np.linspace(top_color[1], mid_color[1], h1, dtype=np.float32),
                            np.linspace(mid_color[1], bot_color[1], h2, dtype=np.float32)])
        b = np.concatenate([np.linspace(top_color[2], mid_color[2], h1, dtype=np.float32),
                            np.linspace(mid_color[2], bot_color[2], h2, dtype=np.float32)])

    col = np.stack([r, g, b], axis=1).astype(np.uint8)
    grid = np.repeat(col[:, np.newaxis, :], w, axis=1)
    res = Image.fromarray(grid, "RGB")
    if len(_GRADIENT_CACHE) < 200:
        _GRADIENT_CACHE[cache_key] = res
    return res.copy()


def create_radial_spotlight(
    w: int, h: int,
    center: Tuple[int, int],
    radius: int,
    inner_color: Tuple[int, int, int, int],
    outer_color: Tuple[int, int, int, int]
) -> Image.Image:
    """Creates a smooth radial spotlight overlay."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cx, cy = center
    y_coords, x_coords = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    normalized_dist = np.clip(dist_from_center / float(radius), 0.0, 1.0)

    smooth = normalized_dist * normalized_dist * (3 - 2 * normalized_dist)

    r = (inner_color[0] * (1 - smooth) + outer_color[0] * smooth).astype(np.uint8)
    g = (inner_color[1] * (1 - smooth) + outer_color[1] * smooth).astype(np.uint8)
    b = (inner_color[2] * (1 - smooth) + outer_color[2] * smooth).astype(np.uint8)
    a = (inner_color[3] * (1 - smooth) + outer_color[3] * smooth).astype(np.uint8)

    rgba = np.stack([r, g, b, a], axis=2)
    return Image.fromarray(rgba, "RGBA")


# ── REUSABLE 2.5D SHADOW & EXTRUSION ENGINE ───────────────────

def draw_25d_directional_shadow(
    canvas: Image.Image,
    poly: List[Tuple[int, int]],
    offset: Tuple[int, int] = (6, 12),
    blur_radius: int = 14,
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    opacity: int = 180
):
    """
    Renders an authentic directional cast shadow behind any 2.5D object polygon.
    Optimized with localized bounding box rendering for ultra-fast frame compositing.
    """
    w, h = canvas.size
    shifted_poly = [(x + offset[0], y + offset[1]) for (x, y) in poly]
    if not shifted_poly:
        return

    xs = [p[0] for p in shifted_poly]
    ys = [p[1] for p in shifted_poly]
    pad = blur_radius * 2 + 4

    min_x = max(0, min(xs) - pad)
    min_y = max(0, min(ys) - pad)
    max_x = min(w, max(xs) + pad)
    max_y = min(h, max(ys) + pad)

    box_w = max_x - min_x
    box_h = max_y - min_y
    if box_w <= 0 or box_h <= 0:
        return

    local_poly = [(x - min_x, y - min_y) for (x, y) in shifted_poly]
    shadow_layer = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow_layer)
    d.polygon(local_poly, fill=(shadow_color[0], shadow_color[1], shadow_color[2], opacity))

    if blur_radius > 0:
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    canvas.paste(shadow_layer, (min_x, min_y), shadow_layer)


def draw_25d_extruded_panel(
    canvas: Image.Image,
    xy: Tuple[int, int, int, int],
    radius: int = 8,
    extrude_offset: Tuple[int, int] = (6, 8),
    top_color: Tuple[int, int, int] = GLASS_ACTIVE_TOP,
    bot_color: Tuple[int, int, int] = GLASS_ACTIVE_BOT,
    extrude_color: Tuple[int, int, int] = GLASS_ACTIVE_EXT,
    border_color: Tuple[int, int, int] = GOLD,
    border_width: int = 2,
    top_highlight: Tuple[int, int, int] = CYAN_HIGHLIGHT,
    is_active: bool = False,
    cast_shadow: bool = True
):
    """
    Renders a true physical 2.5D extruded glass/metal block:
    1. Soft Directional Cast Shadow on Background (+6px X, +12px Y)
    2. Physical 3D Extrusion Block (Dark depth walls on Bottom & Right faces)
    3. Beveled Metallic Chamfer on Extrusion Edges
    4. Main Front Face (Tinted Glass / Metal vertical gradient)
    5. Inner Dark Bezel Inset
    6. Crisp Top-Left Specular Key Light Rail
    """
    x1, y1, x2, y2 = xy
    pw = x2 - x1
    ph = y2 - y1
    ex, ey = extrude_offset

    # 1. Directional Cast Shadow
    if cast_shadow:
        poly_full = [
            (x1, y1), (x2, y1), (x2 + ex, y1 + ey),
            (x2 + ex, y2 + ey), (x1 + ex, y2 + ey), (x1, y2)
        ]
        s_blur = 16 if is_active else 10
        s_op = 200 if is_active else 150
        s_off = (ex + 3, ey + 6) if is_active else (ex + 1, ey + 4)
        draw_25d_directional_shadow(canvas, poly_full, offset=s_off, blur_radius=s_blur, opacity=s_op)

    draw = ImageDraw.Draw(canvas)

    # 2. Physical 3D Extrusion Walls (Right & Bottom depth faces)
    poly_right = [(x2, y1), (x2 + ex, y1 + ey), (x2 + ex, y2 + ey), (x2, y2)]
    poly_bottom = [(x1, y2), (x1 + ex, y2 + ey), (x2 + ex, y2 + ey), (x2, y2)]

    draw.polygon(poly_bottom, fill=extrude_color)
    rf_col = (
        min(255, extrude_color[0] + 12),
        min(255, extrude_color[1] + 16),
        min(255, extrude_color[2] + 24)
    )
    draw.polygon(poly_right, fill=rf_col)

    # Outer Depth Edge Lines
    draw.line([(x2 + ex, y1 + ey), (x2 + ex, y2 + ey)], fill=(30, 45, 80), width=1)
    draw.line([(x1 + ex, y2 + ey), (x2 + ex, y2 + ey)], fill=(20, 30, 60), width=1)
    draw.line([(x2, y2), (x2 + ex, y2 + ey)], fill=(40, 60, 110), width=1)

    # 3. Main Front Face
    face_grad = create_vertical_gradient(pw, ph, top_color, bot_color)
    mask = Image.new("L", (pw, ph), 0)
    d_mask = ImageDraw.Draw(mask)
    d_mask.rounded_rectangle([(0, 0), (pw, ph)], radius=radius, fill=255)
    canvas.paste(face_grad, (x1, y1), mask)

    # 4. Front Face Physical Border
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, outline=border_color, width=border_width)

    # 5. Top-Left Specular Key Light Rail
    draw.line([(x1 + radius, y1 + 1), (x2 - radius, y1 + 1)], fill=top_highlight, width=1)
    draw.line([(x1 + 1, y1 + radius), (x1 + 1, y2 - radius)], fill=top_highlight, width=1)

    # 6. Bottom-Right Inner Recess Shadow
    draw.line([(x1 + radius, y2 - 1), (x2 - radius, y2 - 1)], fill=(10, 15, 30), width=1)
    draw.line([(x2 - 1, y1 + radius), (x2 - 1, y2 - radius)], fill=(10, 15, 30), width=1)


def draw_inner_shadow_rect(
    canvas: Image.Image,
    xy: Tuple[int, int, int, int],
    depth: int = 8,
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    max_alpha: int = 150
):
    """Renders physical inner recess shadow creating a sunken/recessed screen."""
    x1, y1, x2, y2 = xy
    w = x2 - x1
    h = y2 - y1
    if w <= 0 or h <= 0:
        return

    inner_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(inner_layer)

    for i in range(depth):
        alpha = int(max_alpha * (1.0 - (i / float(depth))) ** 1.5)
        col = (shadow_color[0], shadow_color[1], shadow_color[2], alpha)
        d.rectangle([(i, i), (w - 1 - i, h - 1 - i)], outline=col, width=1)

    canvas.paste(inner_layer, (x1, y1), inner_layer)


# ── 1. LAYER 0: TECHNICAL BROADCAST BACKGROUND ───────────────
_BG_CACHE = {}


def render_25d_background(w: int = 1920, h: int = 1080) -> Image.Image:
    """
    Renders Layer 0: Technical Broadcast Studio Background:
    - Deep matte navy vertical gradient
    - Perspective grid lines
    - Radial studio key spotlight in upper center
    Cached in memory for zero-latency frame compositing.
    """
    key = (w, h)
    if key in _BG_CACHE:
        return _BG_CACHE[key].copy()

    bg = create_vertical_gradient(w, h, NAVY_BG_TOP, NAVY_BG_BOT, mid_color=(8, 12, 28), mid_pos=0.4)

    # Radial Studio Spotlight (Upper center key light)
    spot = create_radial_spotlight(w, h, center=(960, 180), radius=950, inner_color=(35, 75, 155, 80), outer_color=(0, 0, 0, 0))
    bg.paste(spot, (0, 0), spot)

    draw = ImageDraw.Draw(bg)

    # Clean borders without grid line artifacts
    draw.rectangle([(0, 0), (w, 3)], fill=(8, 14, 30))
    draw.rectangle([(0, h - 3), (w, h)], fill=(2, 4, 10))

    _BG_CACHE[key] = bg
    return bg.copy()


# ── 2. LAYER 1: TOP HEADER 2.5D RIBBON ─────────────────────────

def render_25d_top_header(
    canvas: Image.Image,
    category: str = "SPECIAL REPORT",
    t: float = 0.0,
    w: int = 1920
):
    """
    Renders Layer 1: Top 2.5D Layered Titanium Broadcast Ribbon:
    - Angled trapezoid titanium chassis with visible physical thickness
    - Pulsing ruby LIVE 24x7 indicator with glowing LED beacon
    - Sapphire category pill with gold edge highlight
    - Digital IST clock
    """
    draw = ImageDraw.Draw(canvas)
    h_bar = 64
    ex, ey = 3, 5

    # 1. Rear Cast Shadow
    poly_bar = [(0, 0), (w, 0), (w, h_bar), (0, h_bar)]
    draw_25d_directional_shadow(canvas, poly_bar, offset=(0, 6), blur_radius=10, opacity=170)

    # 2. Extrusion Wall beneath Top Bar
    draw.rectangle([(0, h_bar), (w, h_bar + ey)], fill=(8, 14, 30))
    draw.line([(0, h_bar + ey), (w, h_bar + ey)], fill=(20, 32, 65), width=1)

    # 3. Main Titanium Ribbon Face
    bar_grad = create_vertical_gradient(w, h_bar, (24, 40, 88), (12, 20, 48))
    canvas.paste(bar_grad, (0, 0))

    # Top & Bottom Rails
    draw.line([(0, 0), (w, 0)], fill=GOLD, width=2)
    draw.line([(0, 1), (w, 1)], fill=GOLD_LIGHT, width=1)
    draw.line([(0, h_bar), (w, h_bar)], fill=GOLD, width=2)
    draw.line([(0, h_bar - 1), (w, h_bar - 1)], fill=GOLD_DARK, width=1)

    # 4. Left 3D Ruby LIVE Module (x: 0..360)
    poly_live = [(0, 0), (360, 0), (320, h_bar), (0, h_bar)]
    draw.polygon([(360, 0), (360 + ex, ey), (320 + ex, h_bar + ey), (320, h_bar)], fill=CRIMSON_EXTRUDE)
    draw.polygon([(0, h_bar), (ex, h_bar + ey), (320 + ex, h_bar + ey), (320, h_bar)], fill=CRIMSON_EXTRUDE)

    live_grad = create_vertical_gradient(360, h_bar, CRIMSON, CRIMSON_DARK)
    mask_live = Image.new("L", (360, h_bar), 0)
    d_ml = ImageDraw.Draw(mask_live)
    d_ml.polygon([(0, 0), (360, 0), (320, h_bar), (0, h_bar)], fill=255)
    canvas.paste(live_grad, (0, 0), mask_live)

    # 3D Gold Faceted Divider
    draw.polygon([(360, 0), (364, 0), (324, h_bar), (320, h_bar)], fill=GOLD)
    draw.line([(360, 0), (320, h_bar)], fill=GOLD_LIGHT, width=2)

    # Glowing Pulsing LIVE LED Dot
    led_radius = int(8 + 2 * math.sin(t * 6.0))
    draw.ellipse([(45 - led_radius, 32 - led_radius), (45 + led_radius, 32 + led_radius)], fill=(255, 255, 255))
    draw.ellipse([(45 - 5, 32 - 5), (45 + 5, 32 + 5)], fill=(255, 230, 230))

    draw_shaped_text(canvas, (75, 16), "LIVE 24x7 | BREAKING", font_size=24, bold=True, text_color=WHITE, shadow=True)

    # 5. Center Sapphire Category Capsule (x: 400..1280)
    draw_25d_extruded_panel(
        canvas, xy=(400, 8, 1260, h_bar - 8), radius=6, extrude_offset=(2, 3),
        top_color=SAPPHIRE_TOP, bot_color=SAPPHIRE_BOT, extrude_color=SAPPHIRE_EXTRUDE,
        border_color=GOLD, border_width=1, top_highlight=CYAN_HIGHLIGHT, is_active=False, cast_shadow=False
    )
    cat_text = f"SPECIAL REPORT • {category.upper()}"
    draw_shaped_text(canvas, (430, 16), cat_text, font_size=22, bold=True, text_color=GOLD_LIGHT, shadow=True)

    # 6. Right Digital Clock Ribbon (x: 1300..1900)
    draw_25d_extruded_panel(
        canvas, xy=(1300, 8, 1900, h_bar - 8), radius=6, extrude_offset=(2, 3),
        top_color=(18, 30, 68), bot_color=(10, 18, 42), extrude_color=(6, 10, 26),
        border_color=(45, 80, 150), border_width=1, top_highlight=CYAN_HIGHLIGHT, is_active=False, cast_shadow=False
    )
    ist_time = time.strftime("%I:%M:%S %p IST | %d %b %Y")
    draw_shaped_text(canvas, (1325, 17), f"🕒 {ist_time}", font_size=20, bold=True, text_color=WHITE, shadow=True)


# ── 3. LAYER 2: LEFT STORY CARDS (2.5D EXTRUDED BLOCKS) ────────

def render_25d_story_cards(
    canvas: Image.Image,
    takeaways: List[str],
    active_idx: int = 1,
    t: float = 0.0
):
    """
    Renders Layer 2: 3 Physical 2.5D Extruded Glass Story Cards (x: 50..760, y: 95..675):
    - Physical dark extrusion walls on right & bottom faces
    - Selected active card visibly raised higher in Z-space (+10px extrusion, elevated +16px shadow)
    - Clean Hindi typography with 2-line word wrapping and 24px text
    """
    t1 = takeaways[0] if len(takeaways) > 0 else "मुख्य घटनाक्रम: बड़ी खबर पर विस्तृत रिपोर्ट"
    t2 = takeaways[active_idx % len(takeaways)] if takeaways else "ग्राउंड फैक्ट्स: घटना स्थल से प्राप्त अहम जानकारी"
    t3 = takeaways[(active_idx + 1) % len(takeaways)] if len(takeaways) > 1 else "ताज़ा स्थिति: प्रशासन एवं जांच टीमों द्वारा निरंतर निगरानी"

    card_items = [
        ("▶ मुख्य घटनाक्रम", t1, 0),
        ("▶ ग्राउंड फैक्ट्स व विवरण", t2, 1),
        ("▶ ताज़ा स्थिति व प्रभाव", t3, 2)
    ]
    card_positions = [
        (95, 275),
        (295, 475),
        (495, 675)
    ]

    for (c_label, c_desc, c_idx), (cy1, cy2) in zip(card_items, card_positions):
        is_active = (c_idx == 1)

        # Physical Z-space parameters
        if is_active:
            c_xy = (46, cy1 - 3, 764, cy2 - 3)
            ext_offset = (8, 11)
            t_col, b_col = GLASS_ACTIVE_TOP, GLASS_ACTIVE_BOT
            ext_col = GLASS_ACTIVE_EXT
            b_col_border = GOLD
            b_width = 3
            t_high = GOLD_LIGHT
        else:
            c_xy = (50, cy1, 760, cy2)
            ext_offset = (5, 7)
            t_col, b_col = GLASS_IDLE_TOP, GLASS_IDLE_BOT
            ext_col = GLASS_IDLE_EXT
            b_col_border = (45, 75, 140)
            b_width = 1
            t_high = CYAN_HIGHLIGHT

        # Render 2.5D Extruded Panel
        draw_25d_extruded_panel(
            canvas, xy=c_xy, radius=10, extrude_offset=ext_offset,
            top_color=t_col, bot_color=b_col, extrude_color=ext_col,
            border_color=b_col_border, border_width=b_width,
            top_highlight=t_high, is_active=is_active, cast_shadow=True
        )

        d = ImageDraw.Draw(canvas)
        x1_c, y1_c, x2_c, y2_c = c_xy

        # Left Physical Accent Beacon
        if is_active:
            beacon_w = 14
            d.rounded_rectangle([(x1_c, y1_c), (x1_c + beacon_w, y2_c)], radius=4, fill=GOLD)
            d.rounded_rectangle([(x1_c, y1_c), (x1_c + 5, y2_c)], radius=2, fill=GOLD_SPECULAR)
            d.line([(x1_c + beacon_w, y1_c), (x1_c + beacon_w, y2_c)], fill=GOLD_DARK, width=1)
        else:
            d.rounded_rectangle([(x1_c, y1_c), (x1_c + 8, y2_c)], radius=4, fill=(35, 60, 115))

        # 3D Category Pill Header
        pill_xy = (x1_c + 24, y1_c + 12, x1_c + 320, y1_c + 46)
        draw_25d_extruded_panel(
            canvas, xy=pill_xy, radius=5, extrude_offset=(2, 3),
            top_color=CRIMSON if is_active else (24, 40, 85),
            bot_color=CRIMSON_DARK if is_active else (14, 24, 55),
            extrude_color=CRIMSON_EXTRUDE if is_active else (8, 14, 32),
            border_color=GOLD if is_active else (40, 70, 130),
            border_width=1, top_highlight=CRIMSON_GLOW if is_active else CYAN_HIGHLIGHT,
            is_active=False, cast_shadow=False
        )
        draw_shaped_text(canvas, (x1_c + 38, y1_c + 14), c_label, font_size=20, bold=True, text_color=WHITE)

        # Clean 2-Line Hindi Story Text
        clean_desc = sanitize_text(c_desc)
        words = clean_desc.split()
        lines = []
        if len(clean_desc) > 28:
            mid = len(words) // 2
            lines.append(" ".join(words[:mid + 1]))
            lines.append(" ".join(words[mid + 1:]))
        else:
            lines.append(clean_desc)

        yt = y1_c + 60
        for line in lines[:2]:
            t_col = WHITE if is_active else (210, 225, 245)
            draw_shaped_text(canvas, (x1_c + 26, yt), line, font_size=24, bold=is_active, text_color=t_col, shadow=is_active)
            yt += 36


# ── 4. LAYER 3: 16:9 2.5D FLOATING MEDIA DISPLAY ───────────────

def render_25d_floating_media_frame(
    canvas: Image.Image,
    xy: Tuple[int, int, int, int] = (785, 95, 1870, 675),
    photo_img: Optional[Image.Image] = None,
    slide_tag: str = "[ SPECIAL REPORT ]",
    credit_text: str = "Verified News Wire",
    rel_t: float = 0.0,
    **kwargs
):
    """
    Renders Layer 3: 16:9 Floating Television Display with True Physical Depth:
    1. Broad 24px Directional Cast Shadow beneath monitor chassis
    2. 8px Thick Titanium Extrusion Block (Right & Bottom depth casing walls)
    3. Brushed Metallic Outer Frame with top-left specular rail
    4. Inner Recessed Screen Housing (6px inset shadow)
    5. 100% Pixel-Locked News Photograph (Zero zooming/warping)
    6. Subtle Specular Glass Wash
    7. 3D Beveled Gold HUD Corner Brackets ┌ ┐ └ ┘
    8. LIVE ON-GROUND & Slide Tag Floating Pills
    """
    mx1, my1, mx2, my2 = xy
    mw = mx2 - mx1
    mh = my2 - my1
    ex, ey = 8, 11

    # 1. Directional Cast Shadow
    poly_monitor = [
        (mx1, my1), (mx2, my1), (mx2 + ex, my1 + ey),
        (mx2 + ex, my2 + ey), (mx1 + ex, my2 + ey), (mx1, my2)
    ]
    draw_25d_directional_shadow(canvas, poly_monitor, offset=(ex + 4, ey + 8), blur_radius=22, opacity=210)

    draw = ImageDraw.Draw(canvas)

    # 2. Physical 3D Extrusion Casing Walls
    poly_right = [(mx2, my1), (mx2 + ex, my1 + ey), (mx2 + ex, my2 + ey), (mx2, my2)]
    poly_bottom = [(mx1, my2), (mx1 + ex, my2 + ey), (mx2 + ex, my2 + ey), (mx2, my2)]

    draw.polygon(poly_bottom, fill=(8, 14, 30))
    draw.polygon(poly_right, fill=(16, 26, 52))

    # Casing Chamfer Edges
    draw.line([(mx2 + ex, my1 + ey), (mx2 + ex, my2 + ey)], fill=(30, 48, 92), width=2)
    draw.line([(mx1 + ex, my2 + ey), (mx2 + ex, my2 + ey)], fill=(20, 34, 68), width=2)
    draw.line([(mx2, my2), (mx2 + ex, my2 + ey)], fill=(45, 75, 140), width=2)

    # 3. Outer Metallic Frame
    frame_grad = create_vertical_gradient(mw, mh, (22, 36, 78), (10, 18, 42))
    mask_f = Image.new("L", (mw, mh), 0)
    d_mf = ImageDraw.Draw(mask_f)
    d_mf.rounded_rectangle([(0, 0), (mw, mh)], radius=10, fill=255)
    canvas.paste(frame_grad, (mx1, my1), mask_f)

    # Frame Outer Border & Specular Highlight
    draw.rounded_rectangle([(mx1, my1), (mx2, my2)], radius=10, outline=GOLD, width=2)
    draw.line([(mx1 + 10, my1 + 1), (mx2 - 10, my1 + 1)], fill=GOLD_SPECULAR, width=1)
    draw.line([(mx1 + 1, my1 + 10), (mx1 + 1, my2 - 10)], fill=GOLD_LIGHT, width=1)

    # 4. Inner Recessed Screen Viewport
    bezel = 4
    vx1, vy1 = mx1 + bezel, my1 + bezel
    vx2, vy2 = mx2 - bezel, my2 - bezel
    vw, vh = vx2 - vx1, vy2 - vy1

    draw.rectangle([(vx1, vy1), (vx2, vy2)], fill=(4, 6, 14))

    # 5. 100% Pixel-Locked News Photograph
    if photo_img is not None:
        try:
            pw, ph = photo_img.size
            if (pw, ph) != (vw, vh):
                scale = max(vw / float(pw), vh / float(ph))
                sw, sh = int(pw * scale), int(ph * scale)
                r_img = photo_img.resize((sw, sh), Image.Resampling.LANCZOS)
                cx = (sw - vw) // 2
                cy = (sh - vh) // 2
                c_img = r_img.crop((cx, cy, cx + vw, cy + vh))
            else:
                c_img = photo_img
            canvas.paste(c_img, (vx1, vy1))
        except Exception:
            f_grad = create_vertical_gradient(vw, vh, (18, 30, 60), (8, 14, 28))
            canvas.paste(f_grad, (vx1, vy1))
    else:
        f_grad = create_vertical_gradient(vw, vh, (18, 30, 60), (8, 14, 28))
        canvas.paste(f_grad, (vx1, vy1))

    # 6. Inner Recess Shadow
    draw_inner_shadow_rect(canvas, (vx1, vy1, vx2, vy2), depth=8, max_alpha=150)

    # 7. Specular Glass Wash
    glass_layer = Image.new("RGBA", (vw, vh), (0, 0, 0, 0))
    d_glass = ImageDraw.Draw(glass_layer)
    g_poly = [(0, 0), (int(vw * 0.40), 0), (int(vw * 0.12), vh), (0, vh)]
    d_glass.polygon(g_poly, fill=(255, 255, 255, 12))
    canvas.paste(glass_layer, (vx1, vy1), glass_layer)

    # 8. 3D Metallic HUD Corner Brackets ┌ ┐ └ ┘
    b_len, b_th = 48, 4
    draw.line([(mx1, my1), (mx1 + b_len, my1)], fill=GOLD_SPECULAR, width=b_th)
    draw.line([(mx1, my1), (mx1, my1 + b_len)], fill=GOLD_SPECULAR, width=b_th)
    draw.line([(mx2, my1), (mx2 - b_len, my1)], fill=GOLD_SPECULAR, width=b_th)
    draw.line([(mx2, my1), (mx2, my1 + b_len)], fill=GOLD_SPECULAR, width=b_th)
    draw.line([(mx1, my2), (mx1 + b_len, my2)], fill=GOLD, width=b_th)
    draw.line([(mx1, my2), (mx1, my2 - b_len)], fill=GOLD, width=b_th)
    draw.line([(mx2, my2), (mx2 - b_len, my2)], fill=GOLD, width=b_th)
    draw.line([(mx2, my2), (mx2, my2 - b_len)], fill=GOLD, width=b_th)

    # 9. Floating Top-Left LIVE ON-GROUND VISUALS Bug
    bug_xy = (mx1 + 14, my1 + 14, mx1 + 340, my1 + 52)
    draw_25d_extruded_panel(
        canvas, xy=bug_xy, radius=5, extrude_offset=(2, 3),
        top_color=CRIMSON, bot_color=CRIMSON_DARK, extrude_color=CRIMSON_EXTRUDE,
        border_color=GOLD, border_width=1, top_highlight=CRIMSON_GLOW, is_active=False, cast_shadow=True
    )
    draw_shaped_text(canvas, (mx1 + 28, my1 + 18), "LIVE ON-GROUND VISUALS", font_size=20, bold=True, text_color=WHITE)

    # 10. Floating Top-Right Slide Tag
    tag_xy = (mx2 - 320, my1 + 14, mx2 - 14, my1 + 52)
    draw_25d_extruded_panel(
        canvas, xy=tag_xy, radius=5, extrude_offset=(2, 3),
        top_color=(18, 30, 68), bot_color=(10, 18, 42), extrude_color=(6, 10, 26),
        border_color=GOLD, border_width=1, top_highlight=GOLD_LIGHT, is_active=False, cast_shadow=True
    )
    draw.text((mx2 - 305, my1 + 20), slide_tag, fill=GOLD, font=load_font(18, bold=True))

    # 11. Bottom Smoked Glass Source Bar
    bar_h = 38
    bar_y = my2 - bar_h
    src_grad = create_vertical_gradient(vw, bar_h, (12, 18, 36), (4, 6, 14))
    canvas.paste(src_grad, (vx1, bar_y))
    draw.line([(vx1, bar_y), (vx2, bar_y)], fill=GOLD, width=2)
    draw.text((vx1 + 18, bar_y + 8), sanitize_text(f"Source: {credit_text}"), fill=WHITE_DIM, font=load_font(18))


# ── 5. LAYER 4: 2.5D LOWER-THIRD MEGA-HEADLINE CHASSIS ─────────

def render_25d_headline_panel(
    canvas: Image.Image,
    headline_text: str,
    t: float = 0.0,
    base_y1: int = 695,
    base_y2: int = 910
):
    """
    Renders Layer 4: Physical 2.5D Mega-Headline Slab projecting forward from background:
    1. Deep Directional Cast Shadow (+8px X, +14px Y) onto lower tickers
    2. Physical 3D Extrusion Wall beneath chassis (8px thick)
    3. Left 3D Ruby Prism Chevron Block with illuminated 'बड़ी ख़बर'
    4. Center Curved Sapphire Metallic Chassis
    5. Top & Bottom 3D Triple-Stripe Metallic Gold Chamfer Rails
    6. Gaussian Specular Sheen Beam sweeping smoothly across slab
    7. 3D Extruded HarfBuzz Devanagari Headline (Yellow Line 1 + White Line 2)
    """
    draw = ImageDraw.Draw(canvas)
    c_h = base_y2 - base_y1
    ex, ey = 8, 12

    poly_chassis = [(340, base_y1), (1870, base_y1), (1870, base_y2), (290, base_y2)]
    poly_chevron = [(50, base_y1), (340, base_y1), (290, base_y2), (50, base_y2)]
    poly_full = [(50, base_y1), (1870, base_y1), (1870, base_y2), (50, base_y2)]

    # 1. Deep Directional Cast Shadow
    draw_25d_directional_shadow(canvas, poly_full, offset=(6, 14), blur_radius=20, opacity=220)

    # 2. Physical 3D Extrusion Walls
    draw.polygon([(50, base_y2), (50 + ex, base_y2 + ey), (1870 + ex, base_y2 + ey), (1870, base_y2)], fill=(8, 14, 30))
    draw.polygon([(1870, base_y1), (1870 + ex, base_y1 + ey), (1870 + ex, base_y2 + ey), (1870, base_y2)], fill=(16, 26, 52))

    # 3. Left 3D Ruby Prism Chevron Block
    poly_chev_ex = [(50 + ex, base_y2 + ey), (290 + ex, base_y2 + ey), (290, base_y2), (50, base_y2)]
    draw.polygon(poly_chev_ex, fill=CRIMSON_EXTRUDE)

    chev_grad = create_vertical_gradient(300, c_h, CRIMSON, CRIMSON_DARK)
    mask_ch = Image.new("L", (300, c_h), 0)
    d_mch = ImageDraw.Draw(mask_ch)
    d_mch.polygon([(0, 0), (290, 0), (240, c_h), (0, c_h)], fill=255)
    canvas.paste(chev_grad, (50, base_y1), mask_ch)

    draw.polygon(poly_chevron, outline=GOLD, width=2)
    # 3D Gold Faceted Separator Divider
    draw.polygon([(340, base_y1), (348, base_y1), (298, base_y2), (290, base_y2)], fill=GOLD)
    draw.line([(340, base_y1), (290, base_y2)], fill=GOLD_SPECULAR, width=2)
    draw.line([(348, base_y1), (298, base_y2)], fill=GOLD_DARK, width=2)

    # Chevron Text
    draw_shaped_text(canvas, (85, base_y1 + 45), "बड़ी ख़बर", font_size=38, bold=True, text_color=WHITE, shadow=True)
    draw.text((95, base_y1 + 120), "TOP HEADLINE", fill=GOLD, font=load_font(24, bold=True))

    # 4. Center Metallic 3D Headline Chassis
    c_w = 1870 - 290
    chassis_grad = create_vertical_gradient(c_w, c_h, (24, 40, 88), (10, 18, 42), mid_color=(14, 24, 58), mid_pos=0.45)
    mask_c = Image.new("L", (c_w, c_h), 0)
    d_mc = ImageDraw.Draw(mask_c)
    d_mc.polygon([(340 - 290, 0), (1870 - 290, 0), (1870 - 290, c_h), (0, c_h)], fill=255)
    canvas.paste(chassis_grad, (290, base_y1), mask_c)

    # 5. Soft Specular Sheen Beam
    sheen_span = 1460
    sheen_speed = 340.0
    sheen_x = 340 + int((t * sheen_speed) % sheen_span)
    sheen_layer = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
    d_sheen = ImageDraw.Draw(sheen_layer)
    bw = 100
    for i in range(bw):
        prog = i / float(bw)
        alpha = int(90 * math.sin(prog * math.pi))
        sx = (sheen_x - 290) - bw // 2 + i
        d_sheen.line([(sx + 35, 0), (sx, c_h)], fill=(120, 180, 255, alpha), width=1)
    
    sheen_layer.putalpha(Image.fromarray(
        (np.array(sheen_layer.getchannel("A")) * (np.array(mask_c) / 255.0)).astype(np.uint8)
    ))
    canvas.paste(sheen_layer, (290, base_y1), sheen_layer)

    # 6. Top & Bottom 3D Triple-Stripe Metallic Gold Chamfer Rails
    draw.polygon(poly_chassis, outline=GOLD, width=2)
    draw.line([(340, base_y1), (1870, base_y1)], fill=GOLD_SPECULAR, width=2)
    draw.line([(340, base_y1 + 2), (1870, base_y1 + 2)], fill=GOLD, width=2)
    draw.line([(340, base_y1 + 4), (1870, base_y1 + 4)], fill=GOLD_DARK, width=1)
    draw.line([(290, base_y2), (1870, base_y2)], fill=GOLD, width=2)
    draw.line([(290, base_y2 - 2), (1870, base_y2 - 2)], fill=GOLD_DARK, width=2)

    # 7. 3D Extruded Devanagari Headline
    clean_h = sanitize_text(headline_text)
    h_words = clean_h.split()
    h_lines = []
    if len(clean_h) > 34:
        h_mid = len(h_words) // 2
        h_lines.append(" ".join(h_words[:h_mid + 1]))
        h_lines.append(" ".join(h_words[h_mid + 1:]))
    else:
        h_lines.append(clean_h)

    yh = base_y1 + 34
    font_sz = 40 if len(clean_h) > 50 else 44
    for idx_l, hl in enumerate(h_lines[:2]):
        l_color = (255, 235, 30) if idx_l == 0 else WHITE
        for sd in range(4, 0, -1):
            draw_shaped_text(canvas, (380 + sd, yh + sd), hl, font_size=font_sz, bold=True, text_color=(0, 0, 0))
        draw_shaped_text(canvas, (380, yh), hl, font_size=font_sz, bold=True, text_color=l_color, shadow=False)
        yh += 65


# ── 6. LAYER 5: DUAL-ROW TICKERS (EXTRUDED 2.5D RIBBONS) ───────

def render_25d_dual_tickers(
    canvas: Image.Image,
    headline_text: str,
    takeaways: List[str],
    category: str = "National",
    t: float = 0.0,
    w: int = 1920,
    h: int = 1080
):
    """
    Renders Layer 5: Dual-Row Elevated Tickers:
    - Row 1 (y: 915..995): 2.5D Ruby Breaking Marquee with continuous running ticker (clipped to badge)
    - Row 2 (y: 1000..1080): 3D Metallic Market Index Ribbon with physical gold badge
    """
    draw = ImageDraw.Draw(canvas)

    # ── ROW 1: RUBY BREAKING NEWS MARQUEE (y: 915..995) ───────
    y1_row1, y2_row1 = 915, 995
    h_row1 = y2_row1 - y1_row1
    ex, ey = 3, 4

    # Directional Cast Shadow for Row 1
    poly_row1 = [(0, y1_row1), (w, y1_row1), (w, y2_row1), (0, y2_row1)]
    draw_25d_directional_shadow(canvas, poly_row1, offset=(0, 5), blur_radius=10, opacity=180)

    # Extrusion Wall beneath Row 1
    draw.rectangle([(0, y2_row1), (w, y2_row1 + ey)], fill=CRIMSON_EXTRUDE)

    # Row 1 Background Face
    r1_grad = create_vertical_gradient(w, h_row1, (200, 16, 24), (110, 8, 12))
    canvas.paste(r1_grad, (0, y1_row1))

    # Top & Bottom Rails
    draw.line([(0, y1_row1), (w, y1_row1)], fill=GOLD, width=2)
    draw.line([(0, y2_row1), (w, y2_row1)], fill=CRIMSON_DEEP, width=2)

    # Running Marquee Text rendered in isolated clipped sub-canvas (x: 340..1920)
    raw_takeaways = "   ★★★   ".join(takeaways[:4]) if takeaways else sanitize_text(headline_text)
    marquee_raw = f"{sanitize_text(headline_text)}   ★★★   {raw_takeaways}   ★★★   "
    marquee_text = f"{marquee_raw}   ★★★   {marquee_raw}   ★★★   {marquee_raw}"

    px_speed = 130.0
    text_width_approx = len(marquee_text) * 14
    scroll_x_offset = -int((t * px_speed) % max(1, text_width_approx // 3))

    marquee_sub_w = w - 340
    marquee_sub = create_vertical_gradient(marquee_sub_w, h_row1, (200, 16, 24), (110, 8, 12))
    draw_shaped_text(marquee_sub, (scroll_x_offset, 25), marquee_text, font_size=23, bold=True, text_color=WHITE, shadow=True)
    canvas.paste(marquee_sub, (340, y1_row1))

    # Static Left BREAKING NEWS Badge sitting physically ON TOP of marquee (x: 0..330)
    poly_badge1 = [(0, y1_row1), (330, y1_row1), (290, y2_row1), (0, y2_row1)]
    b1_grad = create_vertical_gradient(330, h_row1, (240, 22, 32), (140, 10, 16))
    mask_b1 = Image.new("L", (330, h_row1), 0)
    d_mb1 = ImageDraw.Draw(mask_b1)
    d_mb1.polygon([(0, 0), (330, 0), (290, h_row1), (0, h_row1)], fill=255)
    canvas.paste(b1_grad, (0, y1_row1), mask_b1)

    draw.polygon(poly_badge1, outline=GOLD, width=2)
    draw_shaped_text(canvas, (35, y1_row1 + 24), "BREAKING NEWS", font_size=25, bold=True, text_color=WHITE, shadow=True)

    # ── ROW 2: 3D METALLIC MARKET INDEX RIBBON (y: 1000..1080) ─
    y1_row2, y2_row2 = 1000, 1080
    h_row2 = y2_row2 - y1_row2

    # Row 2 Background Face
    r2_grad = create_vertical_gradient(w, h_row2, (18, 30, 68), (8, 14, 34))
    canvas.paste(r2_grad, (0, y1_row2))
    draw.line([(0, y1_row2), (w, y1_row2)], fill=GOLD, width=2)

    # Financial Market Index Ribbon rendered in isolated clipped sub-canvas (x: 260..1700)
    market_items = (
        "SENSEX 81,420 (▲ +0.4%)   |   NIFTY 24,850 (▲ +0.3%)   |   GOLD ₹72,400 (▼ -0.1%)   |   "
        "USD/INR ₹83.95 (▼ -0.05)   |   CRUDE $78.40 (▲ +0.8%)   |   NEW DELHI 32°C (☀)   |   MUMBAI 29°C (🌧)"
    )
    market_full = f"{market_items}   |   {market_items}"
    m_speed = 90.0
    m_width_approx = len(market_full) * 12
    m_scroll_offset = -int((t * m_speed) % max(1, m_width_approx // 2))

    market_sub_w = 1700 - 260
    market_sub = create_vertical_gradient(market_sub_w, h_row2, (18, 30, 68), (8, 14, 34))
    draw_shaped_text(market_sub, (m_scroll_offset, 26), market_full, font_size=21, bold=True, text_color=(255, 220, 80), shadow=True)
    canvas.paste(market_sub, (260, y1_row2))

    # Left Solid Gold MARKET LIVE Badge (x: 0..260)
    poly_badge2 = [(0, y1_row2), (260, y1_row2), (225, y2_row2), (0, y2_row2)]
    b2_grad = create_vertical_gradient(260, h_row2, GOLD_LIGHT, GOLD_DARK)
    mask_b2 = Image.new("L", (260, h_row2), 0)
    d_mb2 = ImageDraw.Draw(mask_b2)
    d_mb2.polygon([(0, 0), (260, 0), (225, h_row2), (0, h_row2)], fill=255)
    canvas.paste(b2_grad, (0, y1_row2), mask_b2)

    draw.polygon(poly_badge2, outline=(50, 35, 0), width=2)
    draw.text((28, y1_row2 + 25), "MARKET LIVE", fill=(10, 10, 10), font=load_font(23, bold=True))

    # Right Category Anchor Badge (x: 1720..1920)
    draw_25d_extruded_panel(
        canvas, xy=(1720, y1_row2 + 6, 1910, y2_row2 - 6), radius=5, extrude_offset=(2, 2),
        top_color=CRIMSON, bot_color=CRIMSON_DARK, extrude_color=CRIMSON_EXTRUDE,
        border_color=GOLD, border_width=1, top_highlight=CRIMSON_GLOW, is_active=False, cast_shadow=False
    )
    draw_shaped_text(canvas, (1740, y1_row2 + 24), sanitize_text(category.upper()[:12]), font_size=20, bold=True, text_color=WHITE)


# ── FULL 2.5D COMPOSITOR PIPELINE ─────────────────────────────

def render_broadcast_frame_25d(
    t: float,
    total_duration: float,
    headline: str,
    category: str,
    slide_takeaways: List[str],
    photo_images: List[Optional[Image.Image]],
    photo_credits: List[str],
    w: int = 1920,
    h: int = 1080
) -> Image.Image:
    """
    Master 2.5D Broadcast Compositing Pipeline:
    Layer 0: Technical Broadcast Background
    Layer 1: Top 2.5D Titanium Header Ribbon
    Layer 2: Left 2.5D Extruded Story Glass Cards
    Layer 3: 16:9 Floating 2.5D Television Display (Stationary Photo)
    Layer 4: Lower-Third 2.5D Mega-Headline Slab
    Layer 5: Dual-Row Elevated Tickers
    """
    takeaways = slide_takeaways if slide_takeaways else [
        "मुख्य घटनाक्रम: बड़ी खबर पर विस्तृत रिपोर्ट",
        "ग्राउंड रिपोर्ट: घटना स्थल से प्राप्त अहम जानकारी एवं समीक्षा",
        "आधिकारिक बयान: सभी पक्षों के बयान एवं प्राथमिक रिपोर्ट दर्ज",
        "ताजा स्थिति: प्रशासन एवं जांच टीमों द्वारा निरंतर निगरानी"
    ]
    num_slides = max(1, len(takeaways))
    slide_dur = total_duration / float(num_slides)
    active_idx = min(num_slides - 1, int(t // slide_dur))
    time_in_slide = t - active_idx * slide_dur

    clean_head = sanitize_text(headline)
    clean_cat = sanitize_text(category.upper())

    # 1. LAYER 0: TECHNICAL BROADCAST STUDIO BACKGROUND
    canvas = render_25d_background(w, h)

    # 2. LAYER 1: TOP 2.5D TITANIUM HEADER RIBBON
    render_25d_top_header(canvas, category=clean_cat, t=t, w=w)

    # 3. LAYER 2: LEFT 2.5D EXTRUDED STORY GLASS CARDS
    render_25d_story_cards(canvas, takeaways=takeaways, active_idx=active_idx, t=t)

    # 4. LAYER 3: 16:9 FLOATING 2.5D MEDIA DISPLAY (Stationary Photo with smooth crossfade)
    num_p = len(photo_images)
    cur_p = photo_images[active_idx % num_p] if num_p > 0 else None
    prev_p = photo_images[(active_idx - 1) % num_p] if num_p > 0 else None

    active_photo = cur_p
    if active_idx > 0 and time_in_slide < 0.5 and cur_p is not None and prev_p is not None:
        try:
            fade_alpha = time_in_slide / 0.5
            active_photo = Image.blend(prev_p, cur_p, fade_alpha)
        except Exception:
            active_photo = cur_p

    credit_txt = photo_credits[active_idx % len(photo_credits)] if photo_credits else "Verified News Wire"

    render_25d_floating_media_frame(
        canvas,
        xy=(785, 95, 1870, 675),
        photo_img=active_photo,
        slide_tag=f"[ SPECIAL REPORT ] ({active_idx + 1}/{num_slides})",
        credit_text=credit_txt
    )

    # 5. LAYER 4: LOWER-THIRD 2.5D MEGA-HEADLINE SLAB
    render_25d_headline_panel(
        canvas,
        headline_text=clean_head,
        t=t,
        base_y1=695,
        base_y2=910
    )

    # 6. LAYER 5: DUAL-ROW ELEVATED TICKERS
    render_25d_dual_tickers(
        canvas,
        headline_text=clean_head,
        takeaways=takeaways,
        category=clean_cat,
        t=t,
        w=w,
        h=h
    )

    return canvas
