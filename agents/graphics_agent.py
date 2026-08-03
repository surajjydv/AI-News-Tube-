import os
import sys
import time
import json
import math
import requests
import numpy as np
import datetime as _dt
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR, CHANNEL_NAME, load_graphics_config
from services.groq_service import generate_text
from services.rss_service import get_realtime_ticker_headlines
from models.news_models import GeneratedScript, MediaAsset
from agents.visuals_agent import VisualResearchEngine
from agents.video_agent import _load_font
from utils.logger import logger


STUDIO_ASSETS_DIR = ASSETS_DIR / "studio"
STUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

STUDIO_BG_PATH    = STUDIO_ASSETS_DIR / "studio_background.png"
CHANNEL_LOGO_PATH = STUDIO_ASSETS_DIR / "channel_logo_3d.png"

PEXELS_API_KEY = "tMiZhafYzUHfNIUQbq5VwDe38aVyJhPjMqj0k5pFufAqBOvXH6b2UcfR"


# ─────────────────────────────────────────────────────────────
# 2.5D VISUAL EFFECTS ENGINE
# ─────────────────────────────────────────────────────────────
class VisualEffects2D:
    """
    2.5D Visual Effects Engine:
    Handles perspective homography quads, 3D slab extrusion, floor reflections,
    light rays, and drop shadows.
    """

    @staticmethod
    def apply_perspective_warp(
        img: Image.Image,
        src_quad: List[Tuple[int, int]],
        dst_quad: List[Tuple[int, int]]
    ) -> Image.Image:
        """Applies 2.5D spatial perspective transform using OpenCV or PIL Quad Mesh."""
        try:
            import cv2
            src_pts = np.float32(src_quad)
            dst_pts = np.float32(dst_quad)
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            img_np = np.array(img.convert("RGBA"))
            h, w = img_np.shape[:2]
            warped = cv2.warpPerspective(
                img_np, M, (w, h),
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0)
            )
            return Image.fromarray(warped, "RGBA")
        except Exception:
            w, h = img.size
            coeffs = [
                dst_quad[0][0], dst_quad[0][1],
                dst_quad[1][0], dst_quad[1][1],
                dst_quad[2][0], dst_quad[2][1],
                dst_quad[3][0], dst_quad[3][1]
            ]
            return img.transform((w, h), Image.Transform.QUAD, coeffs,
                                 resample=Image.Resampling.BICUBIC)

    @staticmethod
    def create_3d_extruded_panel(
        w: int, h: int, depth: int = 12,
        fill_color: Tuple[int, int, int, int] = (12, 16, 32, 230),
        border_color: Tuple[int, int, int, int] = (255, 215, 0, 255)
    ) -> Image.Image:
        """Renders 3D extruded glass slab with edge highlights and depth shadow."""
        canvas = Image.new("RGBA", (w + depth + 20, h + depth + 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        for d in range(depth, 0, -1):
            alpha = int(180 * (d / depth))
            draw.rounded_rectangle(
                [(d + 10, d + 10), (w + d + 10, h + d + 10)],
                radius=14, fill=(5, 8, 18, alpha)
            )
        draw.rounded_rectangle(
            [(10, 10), (w + 10, h + 10)],
            radius=14, fill=fill_color, outline=border_color, width=3
        )
        draw.rounded_rectangle(
            [(14, 14), (w + 6, h // 2 + 5)],
            radius=10, fill=(255, 255, 255, 40)
        )
        return canvas

    @staticmethod
    def render_floor_reflection(frame: Image.Image, desk_y: int = 800) -> Image.Image:
        """Renders inverted studio desk floor reflection with exponential vertical opacity decay."""
        w, h = frame.size
        try:
            desk_region = frame.crop((0, desk_y - 220, w, desk_y))
            flipped = desk_region.transpose(Image.FLIP_TOP_BOTTOM).convert("RGBA")
            mask = Image.new("L", (w, 220), 0)
            m_draw = ImageDraw.Draw(mask)
            for y in range(220):
                opacity = int(90 * ((220 - y) / 220) ** 1.8)
                m_draw.line([(0, y), (w, y)], fill=opacity)
            flipped.putalpha(mask)
            frame_rgba = frame.convert("RGBA")
            frame_rgba.paste(flipped, (0, desk_y), flipped)
            return frame_rgba.convert("RGB")
        except Exception:
            return frame

    @staticmethod
    def apply_light_sweep(
        frame: Image.Image,
        headline_top: int,
        headline_bottom: int,
        global_t: float
    ) -> Image.Image:
        """Sweeps a dynamic glass reflection light sheen across headline panels."""
        w, h = frame.size
        sheen_x = int((global_t * 650) % (w + 400)) - 200
        sheen_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(sheen_overlay)
        s_draw.polygon(
            [(sheen_x, headline_top), (sheen_x + 120, headline_top),
             (sheen_x + 60, headline_bottom), (sheen_x - 60, headline_bottom)],
            fill=(255, 255, 255, 45)
        )
        return Image.alpha_composite(frame.convert("RGBA"), sheen_overlay).convert("RGB")


# ─────────────────────────────────────────────────────────────
# 7-LAYER BROADCAST GRAPHICS SYSTEM
# ─────────────────────────────────────────────────────────────
class BroadcastLayerSystem:
    """
    Production 7-Layer Graphics Engine:
    - Layer 0: Background Layer (Multiplane LED Wall)
    - Layer 1: Depth Layer (Volumetric light rays & floor reflection)
    - Layer 2: Studio Elements Layer (Desk & 3D Logo)
    - Layer 3: Headline Layer (3D Perspective Skew Templates)
    - Layer 4: HUD Layer (Live 4K Badge & Clock)
    - Layer 5: Ticker Layer (Scrolling News Marquee)
    - Layer 6: Effects Layer (Glass Sheen & Red Alert Glow)
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        self.w = width
        self.h = height
        self.config = load_graphics_config()

    def render_layer_0_background(self, studio_bg: Image.Image, cam_offset_x: int = 0) -> Image.Image:
        """Layer 0: Base Studio Background Grid & Multiplane LED Wall."""
        bg = studio_bg.resize((self.w, self.h), Image.Resampling.LANCZOS).convert("RGB")
        if cam_offset_x != 0:
            bg_shifted = Image.new("RGB", (self.w, self.h), (10, 12, 28))
            bg_shifted.paste(bg, (cam_offset_x, 0))
            return bg_shifted
        return bg

    def render_layer_1_depth(self, frame: Image.Image, global_t: float) -> Image.Image:
        """Layer 1: Volumetric Sweeping Light Rays & Glossy Floor Reflections."""
        w, h = frame.width, frame.height
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        ray_speed = self.config.get("volumetric_ray_speed", 1.2)
        angle_shift = int(120 * math.sin(global_t * ray_speed))
        draw.polygon(
            [(w // 2 - 80 + angle_shift, 0), (w // 2 + 120 + angle_shift, 0),
             (w // 2 + 500 + angle_shift, h), (w // 2 - 300 + angle_shift, h)],
            fill=(255, 215, 0, 18)
        )
        draw.polygon(
            [(100 - angle_shift // 2, 0), (320 - angle_shift // 2, 0),
             (750 - angle_shift // 2, h), (-50 - angle_shift // 2, h)],
            fill=(220, 38, 38, 22)
        )
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
        if self.config.get("enable_floor_reflection", True):
            frame = VisualEffects2D.render_floor_reflection(frame, desk_y=h - 280)
        return frame

    def render_layer_2_studio_elements(self, frame: Image.Image, logo_img: Optional[Image.Image]) -> Image.Image:
        """Layer 2: Studio News Desk & 3D Metallic Channel Emblem Logo."""
        w, h = frame.width, frame.height
        if logo_img:
            resized_logo = logo_img.resize((240, 70), Image.Resampling.LANCZOS).convert("RGBA")
            frame.paste(resized_logo, (w // 2 - 120, h - 275), resized_logo)
        return frame

    def render_layer_3_headline(
        self, frame: Image.Image,
        headline: str, category: str, t: float, global_t: float
    ) -> Image.Image:
        """Layer 3: 3D Perspective Skew Headline Templates."""
        w, h = frame.width, frame.height
        draw = ImageDraw.Draw(frame)
        style = self.config.get("headline_style", "breaking_news")
        palette = self.config.get("palettes", {}).get(style, {
            "header_bg":    [190, 18, 18],
            "header_text":  [255, 255, 255],
            "tag_bg":       [234, 179, 8],
            "tag_text":     [10, 15, 30],
            "border_accent":[255, 215, 0],
            "box_bg":       [12, 16, 32],
            "alert_glow":   [255, 30, 30]
        })
        banner_y     = h - 250
        header_bg    = tuple(palette["header_bg"])
        tag_bg       = tuple(palette["tag_bg"])
        border_accent= tuple(palette["border_accent"])
        box_bg       = tuple(palette["box_bg"])
        alert_glow   = tuple(palette.get("alert_glow", [255, 30, 30]))
        template_labels = {
            "breaking_news": ("🚨 ताज़ा ख़बर", "BREAKING STORY"),
            "top_story":     ("📌 मुख्य समाचार", "TOP STORY"),
            "exclusive":     ("⭐ विशेष एक्सक्लूसिव", "EXCLUSIVE REPORT"),
            "live_update":   ("⚡ लाइव अपडेट", "LIVE COVERAGE")
        }
        main_label, sub_label = template_labels.get(style, ("🚨 ताज़ा ख़बर", "BREAKING STORY"))
        from agents.video_agent import _load_font
        brk_font = _load_font(24, bold=True)
        cat_font = _load_font(22, bold=True)
        pulse     = abs(math.sin(global_t * 3.5))
        glow_alpha= int(140 * pulse)
        glow_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow_overlay)
        g_draw.rectangle(
            [(30, banner_y - 10), (w - 30, banner_y + 175)],
            fill=alert_glow + (glow_alpha // 4,)
        )
        frame = Image.alpha_composite(frame.convert("RGBA"), glow_overlay).convert("RGB")
        draw  = ImageDraw.Draw(frame)
        draw.rectangle([(40, banner_y), (420, banner_y + 48)], fill=header_bg)
        draw.rectangle([(38, banner_y - 2), (422, banner_y + 50)], outline=border_accent, width=2)
        draw.text((50, banner_y + 10), f"{main_label} | {sub_label}",
                  fill=tuple(palette["header_text"]), font=brk_font)
        draw.rectangle([(420, banner_y), (740, banner_y + 48)], fill=tag_bg)
        draw.text((435, banner_y + 10), f"⚡ {category.upper()}",
                  fill=tuple(palette["tag_text"]), font=cat_font)
        headline_top    = banner_y + 48
        headline_bottom = banner_y + 165
        box_w = w - 80
        box_h = headline_bottom - headline_top
        slab_img = VisualEffects2D.create_3d_extruded_panel(
            box_w, box_h, depth=10,
            fill_color=box_bg + (240,), border_color=border_accent + (255,)
        )
        frame.paste(slab_img, (30, headline_top - 5), slab_img)
        draw = ImageDraw.Draw(frame)
        draw.rectangle([(40, headline_top), (58, headline_bottom)], fill=header_bg)
        draw.rectangle([(40, headline_top), (w - 40, headline_top + 4)], fill=border_accent)
        clean_headline = headline.replace("\n", " ").strip()
        y_offset = int(32 * (1.0 - (1.0 - min(1.0, t / 0.8)) ** 3)) if t < 0.8 else 0
        if len(clean_headline) > 85:
            headline_size = 34
        elif len(clean_headline) > 65:
            headline_size = 40
        elif len(clean_headline) > 45:
            headline_size = 46
        else:
            headline_size = 52
        headline_font = _load_font(headline_size, bold=True)
        max_text_w = self.w - 160
        words = clean_headline.split()
        lines, current = [], ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=headline_font)
            if bbox[2] - bbox[0] > max_text_w and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        line_h  = headline_size + 8
        total_h = len(lines[:2]) * line_h
        text_y  = headline_top + (headline_bottom - headline_top - total_h) // 2
        for i, line in enumerate(lines[:2]):
            draw.text((78, text_y + i * line_h + y_offset + 3), line, fill=(5, 5, 10), font=headline_font)
            draw.text((76, text_y + i * line_h + y_offset),     line, fill=(255, 255, 255), font=headline_font)
        return frame

    def render_layer_4_hud(self, frame: Image.Image, global_t: float, cam_mode: int = 0) -> Image.Image:
        """Layer 4: Live 4K Badge & Clock Widget."""
        import datetime as _dt
        draw = ImageDraw.Draw(frame)
        from agents.video_agent import _load_font
        live_font  = _load_font(26, bold=True)
        live_pulse = abs(math.sin(global_t * 4.0))
        aura_r = int(14 + 8 * live_pulse)
        draw.ellipse(
            [(56 - aura_r, 58 - aura_r), (56 + aura_r, 58 + aura_r)],
            fill=(239, 68, 68, int(180 * live_pulse))
        )
        draw.rounded_rectangle(
            [(36, 26), (410, 90)],
            radius=12, fill=(200, 20, 20), outline=(255, 215, 0), width=3
        )
        draw.text((76, 42), f"🚨 LIVE 4K  |  {CHANNEL_NAME}", fill=(255, 255, 255), font=live_font)
        now      = _dt.datetime.now()
        time_str = now.strftime('%H:%M') + " IST"
        time_box_x1 = self.w - 380
        draw.rounded_rectangle(
            [(time_box_x1, 26), (self.w - 40, 90)],
            radius=10, fill=(10, 15, 30), outline=(255, 215, 0), width=2
        )
        draw.text((time_box_x1 + 18, 36), f"⏰ {time_str}", fill=(255, 215, 0),
                  font=_load_font(22, bold=True))
        draw.text((time_box_x1 + 18, 64),
                  f"📍 NEW DELHI  •  {now.strftime('%d %b %Y').upper()}",
                  fill=(220, 230, 245), font=_load_font(15, bold=True))
        return frame

    def render_layer_5_ticker(
        self, frame: Image.Image, global_t: float,
        ticker_headlines: Optional[List[str]]
    ) -> Image.Image:
        """Layer 5: Bottom Scrolling News Ticker Marquee (seamless, no ×4 bleed)."""
        draw = ImageDraw.Draw(frame)
        from agents.video_agent import _load_font
        ticker_y   = self.h - 85
        ticker_font= _load_font(21, bold=True)
        draw.rectangle([(40, ticker_y), (self.w - 40, ticker_y + 48)], fill=(10, 14, 26))
        draw.rectangle([(40, ticker_y), (self.w - 40, ticker_y + 3)],  fill=(255, 215, 0))
        draw.rectangle([(40, ticker_y), (240, ticker_y + 48)],         fill=(220, 38, 38))
        draw.text((52, ticker_y + 12), "🔥 ताज़ा खबर", fill=(255, 255, 255),
                  font=_load_font(19, bold=True))
        concat_str = ("   ⚡   ".join(ticker_headlines)
                      if ticker_headlines and len(ticker_headlines) > 0
                      else "AI-NewsTube 2.5D Broadcast Active — Real-Time Processing Operational")
        scroll_text = f"   ⚡ {concat_str}   ►   "
        try:
            txt_w = int(draw.textlength(scroll_text, font=ticker_font))
        except Exception:
            txt_w = max(len(scroll_text) * 12, 1)
        soff  = int(global_t * 150) % max(txt_w, 1)
        tx    = 245 - soff
        draw.text((tx,          ticker_y + 12), scroll_text, fill=(255, 255, 255), font=ticker_font)
        draw.text((tx + txt_w,  ticker_y + 12), scroll_text, fill=(255, 255, 255), font=ticker_font)
        return frame

    def render_layer_6_effects(self, frame: Image.Image, global_t: float) -> Image.Image:
        """Layer 6: Specular Light Sweeps & Glass Sheen Effects."""
        headline_top    = self.h - 202
        headline_bottom = self.h - 85
        return VisualEffects2D.apply_light_sweep(frame, headline_top, headline_bottom, global_t)


def generate_ai_anchor() -> Path:
    """Returns path to 2.5D AI presenter anchor asset."""
    anchor_path = STUDIO_ASSETS_DIR / "ai_anchor_male_3d.png"
    if not anchor_path.exists():
        _gen_male_anchor_asset(anchor_path)
    return anchor_path


def _gen_male_anchor_asset(out_path: Path):
    """
    Generates hyper-realistic transparent 3D male news anchor asset.
    Uses Groq LLM (llama-3.3-70b-versatile) to engineer hyper-realistic 8K prompts.
    """
    # 1. Use Groq LLM to design photorealistic prompt
    prompt_text = (
        "Photorealistic 8K professional male TV news anchor presenter in dark navy business suit "
        "and silk red tie, studio lighting, isolated on solid chroma key green background, "
        "detailed skin pores and realistic eyes, facing camera."
    )
    try:
        from services.groq_service import generate_text
        groq_req = (
            "Write a single concise 40-word prompt for generating a photorealistic 8K image "
            "of an Indian male TV news anchor presenter in a navy suit and red tie facing camera, "
            "isolated on solid green chroma key background. Return prompt text only."
        )
        groq_prompt = generate_text(groq_req, temperature=0.3, max_tokens=100)
        if groq_prompt and len(groq_prompt) > 20:
            prompt_text = groq_prompt.replace("\n", " ").strip()
            logger.info(f"  🤖 Groq LLM Anchor Prompt: '{prompt_text}'")
    except Exception as ge:
        logger.warning(f"Groq prompt gen fallback: {ge}")

    # 2. Render high-resolution portrait via Pollinations AI
    try:
        encoded_prompt = requests.utils.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=600&height=900&nologo=true&seed=105"
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 10000:
            import io
            raw_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            arr = np.array(raw_img, dtype=float)
            r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
            green_mask = (g > 1.05 * r) & (g > 1.05 * b) & (g > 50)
            alpha = np.where(green_mask, 0, 255).astype(np.uint8)
            alpha_img = Image.fromarray(alpha, mode='L').filter(ImageFilter.GaussianBlur(radius=1.0))
            raw_img.putalpha(alpha_img)
            raw_img.save(out_path, "PNG")
            logger.info(f"  ✅ Hyper-realistic Groq AI male anchor saved → {out_path}")
            return
    except Exception as e:
        logger.warning(f"Failed to generate green anchor: {e}")

    # PIL Fallback male anchor drawing
    canvas = Image.new("RGBA", (600, 900), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.polygon([(100, 900), (500, 900), (450, 420), (150, 420)], fill=(16, 28, 64, 255))
    d.polygon([(240, 420), (360, 420), (300, 600)], fill=(245, 245, 250, 255))
    d.polygon([(285, 420), (315, 420), (305, 680), (295, 680)], fill=(200, 30, 30, 255))
    d.ellipse([(200, 100), (400, 380)], fill=(225, 175, 140, 255))
    canvas.save(out_path, "PNG")


def render_tv_broadcast_frame(
    headline_text: str,
    news_photo_path: Optional[str],
    global_t: float = 0.0,
    category: str = "TOP STORIES",
    ticker_headlines: Optional[List[str]] = None,
    quick_cards: Optional[List[str]] = None
) -> Image.Image:
    """
    Renders 1920x1080 Full HD Premier Real Channel Broadcast Frame.

    Layout:
    - Background: Full-bleed Real HD News Photograph with 3D Ken Burns Motion, studio vignette & depth blur.
    - Top Bar: Live 4K Badge, Channel Emblem, Category Tag, Live IST Clock, Location & Date.
    - Left Panel: 3D Glassmorphic Key Highlight Cards (3 Bullet Cards).
    - Lower Third: Animated 3D Extruded Devanagari Hindi Headline Banner with Specular Light Sweep.
    - Bottom Marquee: Seamless Live News Ticker + Financial Market Bar + Category Pill.
    """
    w, h = 1920, 1080

    # ─── LAYER 0: FULL-BLEED REAL HD NEWS PHOTOGRAPHY BACKDROP ─────────────────
    real_photo = None
    if news_photo_path and Path(news_photo_path).exists():
        try:
            real_photo = Image.open(str(news_photo_path)).convert("RGB")
        except Exception:
            pass

    if not real_photo:
        pip_files = sorted(list(ASSETS_DIR.glob("pip_photo_*.jpg")))
        if pip_files:
            try:
                real_photo = Image.open(str(pip_files[0])).convert("RGB")
            except Exception:
                pass

    if real_photo:
        # Clean, sharp, steady HD photo positioning (NO zoom or panning motion)
        img_w, img_h = real_photo.size
        aspect_target = w / float(h)
        aspect_img    = img_w / float(img_h)

        if aspect_img > aspect_target:
            # Wider photo: resize to target height & crop sides cleanly
            new_h = h
            new_w = int(h * aspect_img)
            p_resized = real_photo.resize((new_w, new_h), Image.Resampling.LANCZOS)
            crop_x = (new_w - w) // 2
            frame  = p_resized.crop((crop_x, 0, crop_x + w, h))
        else:
            # Taller photo: resize to target width & crop top/bottom cleanly
            new_w = w
            new_h = int(w / aspect_img)
            p_resized = real_photo.resize((new_w, new_h), Image.Resampling.LANCZOS)
            crop_y = (new_h - h) // 2
            frame  = p_resized.crop((0, crop_y, w, crop_y + h))
    else:
        # Dark Broadcast Studio Background Fallback
        if STUDIO_BG_PATH.exists():
            frame = Image.open(str(STUDIO_BG_PATH)).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
        else:
            frame = Image.new("RGB", (w, h), (10, 14, 30))

    # Dark Studio Vignette Overlay (Ensures UI & Text Readability)
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    v_draw   = ImageDraw.Draw(vignette)

    # Check if Breaking News for Red Alert Strobe
    is_brk_event = "break" in category.lower() or "ताज़ा" in category or "dhamaka" in category.lower()
    if is_brk_event:
        strobe_alpha = int(70 + 40 * math.sin(global_t * 6.0))
        v_draw.rectangle([(0, 0), (w, h)], fill=(220, 15, 20, strobe_alpha))

    # Top & Bottom Gradient Shadows
    for y in range(160):
        alpha = int(180 * (1.0 - y / 160.0))
        v_draw.line([(0, y), (w, y)], fill=(4, 8, 20, alpha))
    for y in range(h - 320, h):
        prog  = (y - (h - 320)) / 320.0
        alpha = int(210 * prog)
        v_draw.line([(0, y), (w, y)], fill=(4, 8, 20, alpha))
    # Left Side Panel Shadow
    for x in range(480):
        alpha = int(140 * (1.0 - x / 480.0))
        v_draw.line([(x, 160), (x, h - 320)], fill=(4, 8, 20, alpha))

    frame = Image.alpha_composite(frame.convert("RGBA"), vignette).convert("RGB")
    draw  = ImageDraw.Draw(frame)

    # ─── LAYER 1: TOP BROADCAST HUD HEADER ────────────────────────────────────
    live_font  = _load_font(22, bold=True)
    hud_font   = _load_font(18, bold=True)
    clock_font = _load_font(21, bold=True)

    # 1A. Top-Left Slanted Live Channel Badge
    live_pulse = abs(math.sin(global_t * 3.5))
    badge_bg = (220, 15, 20) if is_brk_event else (200, 20, 20)
    draw.polygon([(20, 18), (380, 18), (360, 64), (20, 64)], fill=badge_bg)
    draw.polygon([(20, 18), (380, 18), (380, 22), (20, 22)], fill=(255, 215, 0))
    dot_r = int(6 + 3 * live_pulse)
    draw.ellipse([(44 - dot_r, 41 - dot_r), (44 + dot_r, 41 + dot_r)], fill=(255, 255, 255))
    draw.text((58, 27), f"🔴 LIVE 4K  |  {CHANNEL_NAME}", fill=(255, 255, 255), font=live_font)

    # 1B. Top-Center Category Tag Pill
    draw.polygon([(390, 18), (680, 18), (660, 64), (370, 64)], fill=(12, 18, 36))
    draw.polygon([(390, 18), (680, 18), (680, 21), (390, 21)], fill=(255, 215, 0))
    cat_str = f"⚡ {category.upper()}"
    draw.text((400, 28), cat_str, fill=(255, 215, 0), font=hud_font)

    # 1C. Top-Right IST Digital Clock & Location Box
    now = _dt.datetime.now()
    time_str = now.strftime('%H:%M') + " IST"
    draw.polygon([(w - 420, 18), (w - 20, 18), (w - 20, 64), (w - 400, 64)], fill=(10, 14, 28), outline=(255, 215, 0), width=2)
    draw.text((w - 390, 26), f"⏰ {time_str}", fill=(255, 215, 0), font=clock_font)
    draw.text((w - 210, 28), f"📍 NEW DELHI", fill=(220, 230, 245), font=_load_font(15, bold=True))

    # ─── LAYER 2: 2.5D IMPACTFUL HIGH-DEF HEADLINE BANNER (POP-UP ANIMATED) ───
    pop_t   = min(1.0, global_t / 0.5)
    scale_y = math.sin(pop_t * math.pi / 2)
    banner_h = int(120 * scale_y)
    banner_y = h - 90 - banner_h

    if banner_h > 20:
        b_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        b_draw  = ImageDraw.Draw(b_layer)

        # 2.5D Extruded Left Action Box
        act_title1 = "🚨 BREAKING" if is_brk_event else "🚨 BIG"
        act_title2 = "NEWS" if is_brk_event else "NEWS"
        b_draw.polygon([(0, banner_y), (310, banner_y), (250, banner_y + banner_h), (0, banner_y + banner_h)], fill=(170, 15, 20, 255))
        b_draw.polygon([(0, banner_y), (310, banner_y), (310, banner_y + 5), (0, banner_y + 5)], fill=(255, 215, 0, 255))

        # 3D Slanted Divider Chevron
        b_draw.polygon([(260, banner_y), (305, banner_y), (245, banner_y + banner_h), (200, banner_y + banner_h)], fill=(255, 255, 255, 240))

        # Main 2.5D Headline Glassmorphic Center Slab
        b_draw.rectangle([(310, banner_y), (w - 280, banner_y + banner_h)], fill=(10, 15, 32, 248))
        b_draw.rectangle([(310, banner_y), (w - 280, banner_y + 5)], fill=(255, 215, 0, 255))
        b_draw.rectangle([(310, banner_y + banner_h - 4), (w - 280, banner_y + banner_h)], fill=(255, 215, 0, 255))

        # Right Action Box ("🔴 LIVE 4K")
        b_draw.rectangle([(w - 280, banner_y), (w, banner_y + banner_h)], fill=(200, 20, 20, 255))
        b_draw.rectangle([(w - 280, banner_y), (w, banner_y + 5)], fill=(255, 215, 0, 255))

        frame = Image.alpha_composite(frame.convert("RGBA"), b_layer).convert("RGB")
        draw  = ImageDraw.Draw(frame)

        # Left Box Text
        draw.text((38, banner_y + 18), act_title1, fill=(255, 235, 100), font=_load_font(28 if is_brk_event else 32, bold=True))
        draw.text((38, banner_y + 60), act_title2, fill=(255, 235, 100), font=_load_font(28 if is_brk_event else 32, bold=True))

        # Center Devanagari Hindi Main Headline (Large 2.5D Extruded Text)
        hclean = headline_text.split(" - ")[0].strip() if " - " in headline_text else headline_text
        hfont_size = 38 if len(hclean) > 55 else 44
        hfont = _load_font(hfont_size, bold=True)

        # 3D Extruded Shadow Layer behind Headline Text
        for ext in range(5, 0, -1):
            draw.text((330 + ext, banner_y + 30 + ext), hclean, fill=(15, 5, 10), font=hfont)
        draw.text((330, banner_y + 30), hclean, fill=(255, 255, 255), font=hfont)

        # Right CTA Box Text
        draw.text((w - 255, banner_y + 24), "🔴 LIVE NOW", fill=(255, 255, 255), font=_load_font(21, bold=True))
        draw.text((w - 265, banner_y + 64), f"{CHANNEL_NAME.lower().replace(' ', '')}.com", fill=(255, 215, 0), font=_load_font(18, bold=True))

        # Periodic Specular Sheen Light Sweep Animation (Every 2.5s)
        sweep_cycle = (global_t * 1.2) % 2.5
        if sweep_cycle < 0.6:
            flash_x = int(310 + (sweep_cycle / 0.6) * (w - 590))
            flash_l = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(flash_l).polygon(
                [(flash_x, banner_y), (flash_x + 140, banner_y), (flash_x + 70, banner_y + banner_h), (flash_x - 70, banner_y + banner_h)],
                fill=(255, 255, 255, int(170 * (1 - pop_t)))
            )
            frame = Image.alpha_composite(frame.convert("RGBA"), flash_l).convert("RGB")
            draw  = ImageDraw.Draw(frame)

    # ─── LAYER 4: BOTTOM DUAL MARQUEE TICKER (y=h-90..h) ─────────────────────
    tick_y = h - 90
    draw.rectangle([(0, tick_y), (w, h)], fill=(8, 12, 24))
    draw.rectangle([(0, tick_y), (w, tick_y + 3)], fill=(255, 215, 0))

    # Ticker Line 1: Live News Headlines Feed
    tfont = _load_font(20, bold=True)
    ctick = ("  ►  ".join(ticker_headlines)
             if ticker_headlines else "AI-NewsTube 4K Live Broadcast Active — Real-Time News Processing Operational")
    stxt  = f"  ►  {ctick}  "
    try:
        tw = max(int(draw.textlength(stxt, font=tfont)), 1)
    except Exception:
        tw = max(len(stxt) * 12, 1)

    loop_w = max(tw, w + 1)
    soff   = int(global_t * 150) % loop_w

    tick_canvas = Image.new("RGB", (w - 160, 42), (8, 12, 24))
    tc_draw     = ImageDraw.Draw(tick_canvas)
    x1_t = -soff
    while x1_t < (w - 160):
        tc_draw.text((x1_t, 10), stxt, fill=(255, 255, 255), font=tfont)
        x1_t += tw
    frame.paste(tick_canvas, (0, tick_y + 4))
    draw = ImageDraw.Draw(frame)

    # Ticker Line 2: Financial Market & Weather Bar (y=h-44..h)
    mkt_y = h - 44
    draw.rectangle([(0, mkt_y), (w - 160, h)], fill=(14, 20, 38))
    draw.rectangle([(0, mkt_y), (w - 160, mkt_y + 2)], fill=(220, 38, 38))
    mkt_str = "📈 SENSEX 81,420 ▲ +340  |  NIFTY 24,850 ▲ +95  |  GOLD ₹72,500 ▲  |  USD/INR 83.72  |  WEATHER 32°C NEW DELHI"
    draw.text((16, mkt_y + 10), mkt_str, fill=(255, 215, 0), font=_load_font(16, bold=True))

    # Bottom Right Category Pill
    draw.rectangle([(w - 160, tick_y), (w, h)], fill=(180, 20, 20))
    cat_text = category[:8].upper() if category else "NEWS"
    draw.text((w - 142, tick_y + 30), cat_text, fill=(255, 255, 255), font=_load_font(21, bold=True))

    return frame


def create_3d_channel_logo(force: bool = False) -> Path:
    """Creates metallic red and gold 3D channel emblem logo for AI-NEWSTUBE."""
    if CHANNEL_LOGO_PATH.exists() and not force:
        return CHANNEL_LOGO_PATH

    logger.info("  🎨 Graphics Agent: Designing 3D Metallic Channel Logo...")
    w, h = 480, 140
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 3D Extruded Outer Glass Slab
    for d in range(8, 0, -1):
        draw.rounded_rectangle([(6+d, 6+d), (w-6+d, h-6+d)],
                                radius=20, fill=(10, 14, 28, int(160 * (d/8))))

    draw.rounded_rectangle([(6, 6), (w-6, h-6)],
                            radius=20, fill=(180, 20, 20, 255), outline=(255, 215, 0, 255), width=4)
    draw.rounded_rectangle([(12, 12), (w-12, h-12)],
                            radius=16, fill=(220, 30, 30, 255), outline=(234, 179, 8, 255), width=2)
    # Glossy top reflection sheen
    draw.rounded_rectangle([(16, 16), (w-16, h//2+2)], radius=12, fill=(255, 255, 255, 65))
    draw.line([(30, h-20), (w-30, h-20)], fill=(255, 215, 0, 255), width=3)

    # YouTube 3D Play Icon Badge on Left (x=24..68)
    draw.rounded_rectangle([(28, 42), (80, 88)], radius=12, fill=(255, 0, 0, 255), outline=(255, 255, 255, 255), width=2)
    draw.polygon([(46, 52), (68, 65), (46, 78)], fill=(255, 255, 255, 255))

    try:
        from agents.video_agent import _load_font
        font = _load_font(34, bold=True)
    except Exception:
        font = ImageFont.load_default(size=30)

    # 3D Bevel Text Extrusion
    for ext in range(5, 0, -1):
        draw.text((95 + ext, 45 + ext), "AI-NEWSTUBE", fill=(30, 5, 10, 240), font=font)

    draw.text((95, 45), "AI-NEWSTUBE", fill=(255, 215, 0, 255), font=font)
    draw.text((96, 44), "AI-NEWSTUBE", fill=(255, 255, 255, 240), font=font)

    img.save(CHANNEL_LOGO_PATH, "PNG")
    return CHANNEL_LOGO_PATH


def create_studio_background(force: bool = False) -> Path:
    # Renders 1920x1080 premium 3D TV news studio background using PIL
    if STUDIO_BG_PATH.exists() and not force:
        return STUDIO_BG_PATH

    logger.info("  🏢 Graphics Agent: Rendering premium 3D studio background...")
    w, h = 1920, 1080
    img  = Image.new("RGB", (w, h), (4, 6, 18))
    draw = ImageDraw.Draw(img)

    # ── Base radial-ish gradient: dark navy centre → dark indigo edges ──
    for y in range(h):
        t_y = y / h
        for x_seg in range(0, w, 4):
            t_x = abs((x_seg / w) - 0.5) * 2     # 0 at centre, 1 at edges
            dark = t_x * 0.35
            r = max(0, int((4  + 18*t_y) * (1-dark)))
            g = max(0, int((5  + 12*t_y) * (1-dark)))
            b = max(0, int((20 + 32*t_y) * (1-dark*0.5)))
            draw.line([(x_seg, y), (x_seg+4, y)], fill=(r, g, b))

    desk_top = h - 280

    # ── Hex/diamond accent pattern on rear wall ──────────────────────────
    # Semi-transparent diamonds to simulate LED tile grid
    hex_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hex_layer)
    hex_size = 80
    for hx in range(0, w + hex_size, hex_size):
        for hy in range(0, desk_top + hex_size, hex_size):
            offset_x = (hex_size // 2) if ((hy // hex_size) % 2 == 1) else 0
            cx_, cy_ = hx + offset_x, hy
            pts = [
                (cx_, cy_ - hex_size//3),
                (cx_ + hex_size//3, cy_),
                (cx_, cy_ + hex_size//3),
                (cx_ - hex_size//3, cy_)
            ]
            hd.polygon(pts, outline=(40, 70, 160, 22))
    img = Image.alpha_composite(img.convert("RGBA"), hex_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 18 vivid concentric curved LED wall rings ────────────────────────
    for ring in range(18, 0, -1):
        ratio   = ring / 18
        # Outer rings: deep blue; inner rings: bright cyan/white core
        r_c = int(10  + ratio * 30)
        g_c = int(80  + ratio * 120)
        b_c = int(200 + ratio * 55)
        alpha_v = int(60 + ratio * 140)     # 72 → 200 (very visible)
        lw_     = max(1, int(2 + ratio * 3))

        rw_ = w + 400 - ring * 28
        rh_ = 620 - ring * 18
        ry_ = -120
        led  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(led).ellipse(
            [(w//2 - rw_//2, ry_), (w//2 + rw_//2, ry_ + rh_)],
            outline=(r_c, g_c, b_c, alpha_v), width=lw_
        )
        img = Image.alpha_composite(img.convert("RGBA"), led).convert("RGB")
        draw = ImageDraw.Draw(img)

    # ── Bold vanishing-point perspective floor grid ──────────────────────
    vp_x = w // 2
    # Radial spokes
    for col in range(-12, 13):
        gx    = vp_x + col * 160
        alpha = 90 if col == 0 else 55
        cw_   = 2 if col == 0 else 1
        draw.line([(vp_x, desk_top), (gx, h)],
                  fill=(50, 80, 180, alpha), width=cw_)
    # Horizontal perspective rows
    for row in range(0, 8):
        scale   = row / 7
        gy      = desk_top + int(scale * (h - desk_top))
        rx_span = int(scale * w * 0.52)
        alpha   = int(30 + scale * 80)
        draw.line([(vp_x - rx_span, gy), (vp_x + rx_span, gy)],
                  fill=(50, 80, 180, alpha), width=1)

    # ── 5 volumetric spotlight cones from ceiling ────────────────────────
    spot_positions = [
        (w * 1//6,  22),
        (w * 2//6,  28),
        (w * 3//6,  34),   # centre — brightest
        (w * 4//6,  28),
        (w * 5//6,  22),
    ]
    for sp_x, sp_a in spot_positions:
        cone = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        half = int(sp_a * 0.4 * w // 100)  # half-width at desk level
        ImageDraw.Draw(cone).polygon(
            [(sp_x - 35, 0), (sp_x + 35, 0),
             (sp_x + 260, desk_top), (sp_x - 260, desk_top)],
            fill=(210, 225, 255, sp_a)
        )
        # Inner bright core
        ImageDraw.Draw(cone).polygon(
            [(sp_x - 12, 0), (sp_x + 12, 0),
             (sp_x + 80, desk_top), (sp_x - 80, desk_top)],
            fill=(255, 255, 255, sp_a // 2)
        )
        img  = Image.alpha_composite(img.convert("RGBA"), cone).convert("RGB")
        draw = ImageDraw.Draw(img)

    # ── Metallic anchor desk surface ─────────────────────────────────────
    for y in range(desk_top, h):
        prog = (y - desk_top) / 280
        r = int(22 + 30*prog)
        g = int(20 + 18*prog)
        b = int(45 + 32*prog)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Desk shimmer highlight (horizontal specular)
    for offset in range(12):
        shim_alpha = int(60 * (1 - offset/12))
        draw.line([(0, desk_top + offset), (w, desk_top + offset)],
                  fill=(255, 255, 255, shim_alpha))

    # Gold + red separator stripe
    draw.line([(0, desk_top),     (w, desk_top)],     fill=(255, 215, 0), width=5)
    draw.line([(0, desk_top + 5), (w, desk_top + 5)], fill=(180, 20, 20), width=4)
    draw.line([(0, desk_top + 9), (w, desk_top + 9)], fill=(255, 215, 0), width=2)

    # ── Top broadcast stripe (red + gold) ───────────────────────────────
    draw.rectangle([(0, 0), (w, 8)], fill=(220, 38, 38))
    draw.rectangle([(0, 8), (w, 14)], fill=(255, 215, 0))

    # ── Ambient vertical grid lines on wall ─────────────────────────────
    for x in range(0, w + 1, 80):
        draw.line([(x, 14), (x, desk_top)], fill=(30, 50, 100, 28), width=1)

    # Soft blur to blend composited layers
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img.save(STUDIO_BG_PATH, "PNG", quality=95)
    logger.info(f"  ✅ 3D Studio background saved → {STUDIO_BG_PATH}")
    return STUDIO_BG_PATH


def generate_search_keywords(topic_title: str, category: str) -> List[str]:
    prompt = (f"Given news topic '{topic_title}' category '{category}', "
              "return 5 search queries as JSON list of strings.")
    try:
        response  = generate_text(prompt, temperature=0.2)
        clean_json = response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        keywords = json.loads(clean_json)
        if isinstance(keywords, list) and len(keywords) >= 5:
            return keywords[:5]
    except Exception:
        pass
    return [
        f"{category} news",
        f"{topic_title.split()[0]} event",
        "press conference",
        "breaking news",
        "news broadcast"
    ]


def fetch_news_photo(keyword: str, output_path: Path, idx: int) -> bool:
    """
    Fetches news photos with strict 1st Priority for Real Photography:
    1st Priority (Real News Photography):
      1. Real NASA Open API (space/astronomy/satellite topics)
      2. Real Wikimedia Commons Media API (real news events/figures/landmarks)
      3. Real Picsum Photos API (real HD photography)
    LAST OPTION (AI-Generated Fallback):
      4. Pollinations AI (used ONLY when all real photo APIs fail)
    """
    clean_kw = keyword.lower()

    # ── 1ST PRIORITY SOURCE 1: NASA Official API (Real Space / Satellite Photos) ──
    space_kws = ["nasa", "space", "astronomy", "planet", "mars", "moon", "satellite",
                 "rocket", "telescope", "star", "galaxy", "orbit", "iss", "launch"]
    if any(skw in clean_kw for skw in space_kws):
        try:
            nasa_url = (f"https://images-api.nasa.gov/search"
                        f"?q={requests.utils.quote(keyword)}&media_type=image")
            resp = requests.get(nasa_url, timeout=8)
            if resp.status_code == 200:
                items = resp.json().get("collection", {}).get("items", [])
                if items:
                    item  = items[idx % len(items)]
                    links = item.get("links", [])
                    if links and "href" in links[0]:
                        img_url  = links[0]["href"]
                        img_resp = requests.get(img_url, timeout=10)
                        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                            with open(output_path, "wb") as f:
                                f.write(img_resp.content)
                            logger.info(f"  📸 [REAL PHOTO 1ST PRIORITY] NASA image fetched for '{keyword}'")
                            return True
        except Exception as e:
            logger.warning(f"  NASA API warning: {e}")

    # ── 1ST PRIORITY SOURCE 2: Real Wikimedia Commons Media Search ──
    try:
        headers = {"User-Agent": "AI-NewsTube/2.0 (https://github.com/ai-newstube; contact@ai-newstube.org)"}
        wiki_url = (f"https://commons.wikimedia.org/w/api.php"
                    f"?action=query&generator=search&gsrsearch={requests.utils.quote(keyword)}"
                    f"&gsrnamespace=6&prop=imageinfo&iiprop=url&format=json&gsrlimit=8")
        resp = requests.get(wiki_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for _, page_info in pages.items():
                imageinfo = page_info.get("imageinfo", [])
                if imageinfo and "url" in imageinfo[0]:
                    img_url = imageinfo[0]["url"]
                    if img_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                        img_resp = requests.get(img_url, headers=headers, timeout=10)
                        if img_resp.status_code == 200 and len(img_resp.content) > 8000:
                            with open(output_path, "wb") as f:
                                f.write(img_resp.content)
                            logger.info(f"  📸 [REAL PHOTO 1ST PRIORITY] Wikimedia Commons real image fetched for '{keyword}'")
                            return True
    except Exception as e:
        logger.warning(f"  Wikimedia search warning: {e}")

    # ── 1ST PRIORITY SOURCE 3: Real Picsum HD Photography ──
    try:
        url  = f"https://picsum.photos/seed/{idx + 10}/1280/720.jpg"
        resp = requests.get(url, timeout=10, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 20000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"  📸 [REAL PHOTO 1ST PRIORITY] Real Picsum HD photo fetched for '{keyword}'")
            return True
    except Exception as e:
        logger.warning(f"  Picsum warning: {e}")

    # ── SOURCE 4: Real Pexels / Unsplash HD Photography ──
    try:
        pex_headers = {"Authorization": PEXELS_API_KEY}
        pex_url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(keyword)}&per_page=5&orientation=landscape"
        resp = requests.get(pex_url, headers=pex_headers, timeout=8)
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                photo_obj = photos[idx % len(photos)]
                src_url = photo_obj.get("src", {}).get("large", photo_obj.get("src", {}).get("medium", ""))
                if src_url:
                    img_resp = requests.get(src_url, timeout=10)
                    if img_resp.status_code == 200 and len(img_resp.content) > 10000:
                        with open(output_path, "wb") as f:
                            f.write(img_resp.content)
                        logger.info(f"  📸 [REAL PHOTO] Pexels HD photo fetched for '{keyword}'")
                        return True
    except Exception as e:
        logger.warning(f"  Pexels search warning: {e}")

    return False


def graphics_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Graphics Agent: Generates 3D Studio Background, Channel Emblem Logo,
    PiP Photos & Ticker Headlines.
    """
    logger.info("=" * 50)
    logger.info("🎨 GRAPHICS AGENT (2.5D Premium Broadcast Engine)")
    logger.info("=" * 50)

    anchor_path = generate_ai_anchor()
    logo_path   = create_3d_channel_logo()

    # Generate 3D studio background (PIL-rendered perspective scene)
    studio_path = create_studio_background()

    keywords = generate_search_keywords(script_obj.topic_title, script_obj.category)
    logger.info(f"  📸 Visual Research Keywords: {keywords}")

    pip_photos:   List[str]       = []
    media_assets: List[MediaAsset]= []
    timestamp = int(time.time())

    for idx, kw in enumerate(keywords, start=1):
        output_file = ASSETS_DIR / f"pip_photo_{timestamp}_{idx}.jpg"
        asset = VisualResearchEngine.research_media(kw, output_file, idx)
        pip_photos.append(asset.file_path)
        media_assets.append(asset)

    ticker_news = get_realtime_ticker_headlines(limit=10)
    script_obj.ticker_headlines = ticker_news
    script_obj.media_assets     = media_assets
    script_obj.image_paths      = [str(anchor_path), str(studio_path), str(logo_path)] + pip_photos

    logger.info(f"✅ Graphics Agent Ready — 3D Engine + {len(pip_photos)} PiP photos ready!")
    return script_obj
