"""
services/live_feed_renderer.py
==============================
Live TV Newsfeed Video Renderer (Zero 3D Anchors / Zero Avatars):
Renders a full-screen Live Newsfeed broadcast video featuring:
1. Real Event Photos with cinematic Ken Burns pan-and-zoom motion effect.
2. Top-left 'LIVE' pulsing red badge + Category badge.
3. Sleek TV News Channel Lower-Third (Yellow Headline + Sub-headline box).
4. Bottom Scrolling Ticker Bar.
5. 100% Devanagari Hindi support via Mukta-Bold font with zero tofu boxes.
"""

import os
import sys
import math
import numpy as np
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.font_utils import load_font, sanitize_text, draw_cairo_text
from utils.logger import logger
from moviepy import VideoClip, AudioFileClip

# Color Palette for TV Live Feed
DARK_BG   = (10, 18, 35)
GOLD      = (255, 200, 0)
RED       = (220, 35, 35)
WHITE     = (255, 255, 255)
BLUE_BOX  = (15, 32, 68)
DARK_BAR  = (15, 23, 42)

def f_bold(sz: int, lang: str = "hi"):
    return load_font(sz, bold=True, lang=lang)

def f_reg(sz: int, lang: str = "hi"):
    return load_font(sz, bold=False, lang=lang)

class LiveFeedRenderer:
    """
    Live TV Newsfeed Video Renderer:
    Renders pure TV broadcast live feed with real photos, cinematic motion, and sleek TV graphics overlays.
    NO 3D anchors or cartoon presenter avatars.
    """

    @classmethod
    def render_live_feed_frame(
        cls,
        w: int,
        h: int,
        t: float,
        duration: float,
        headline: str,
        category: str,
        photos: List[Image.Image],
        photo_credits: List[str],
        ticker_text: str,
        sub_text: str = ""
    ) -> Image.Image:
        canvas = Image.new("RGB", (w, h), DARK_BG)

        # 1. Select active real photo & apply Ken Burns pan-and-zoom + smooth dynamic slide push transition
        PHOTO_DURATION = 4.5   # seconds each photo is shown
        FADE_DURATION  = 0.9   # transition duration

        def _render_photo(photo: Image.Image, seg_t: float, idx: int) -> Optional[Image.Image]:
            """Return smooth Ken-Burns rendered photo with dynamic pan direction per photo."""
            try:
                zoom_scale = 1.0 + 0.14 * seg_t
                pw, ph = photo.size
                target_ratio = w / h
                photo_ratio  = pw / ph
                if photo_ratio > target_ratio:
                    crop_h = ph
                    crop_w = int(ph * target_ratio)
                else:
                    crop_w = pw
                    crop_h = int(pw / target_ratio)
                
                # Pan direction changes based on photo index (left-to-right, right-to-left, top-to-bottom)
                pan_x = (seg_t - 0.5) * 40 if idx % 2 == 0 else (0.5 - seg_t) * 40
                left = (pw - crop_w) // 2 + int(pan_x)
                top  = (ph - crop_h) // 2
                left = max(0, min(pw - crop_w, left))
                cropped = photo.crop((left, top, left + crop_w, top + crop_h))
                zw = int(w * zoom_scale)
                zh = int(h * zoom_scale)
                resized = cropped.resize((zw, zh), Image.Resampling.LANCZOS)
                z_left = (zw - w) // 2
                z_top  = (zh - h) // 2
                return resized.crop((z_left, z_top, z_left + w, z_top + h))
            except Exception:
                return None

        n_photos   = len(photos)
        cur_idx    = int(t // PHOTO_DURATION) % n_photos
        next_idx   = (cur_idx + 1) % n_photos
        segment_t  = (t % PHOTO_DURATION) / PHOTO_DURATION
        fade_start = (PHOTO_DURATION - FADE_DURATION) / PHOTO_DURATION

        active_credit = photo_credits[cur_idx] if cur_idx < len(photo_credits) else "Source: Press News Photo"

        cur_frame = _render_photo(photos[cur_idx], segment_t, cur_idx)
        if cur_frame:
            if segment_t >= fade_start and n_photos > 1:
                # Smooth push + cross-fade blend
                progress = (segment_t - fade_start) / (1.0 - fade_start)
                # Smooth ease-in-out curve
                smooth_p = 0.5 - 0.5 * math.cos(progress * math.pi)
                nxt_frame = _render_photo(photos[next_idx], (progress * FADE_DURATION) / PHOTO_DURATION, next_idx)
                if nxt_frame:
                    cur_frame = Image.blend(cur_frame, nxt_frame, alpha=smooth_p)
            canvas.paste(cur_frame, (0, 0))

        draw = ImageDraw.Draw(canvas)

        # 2. TOP TV OVERLAY BARS
        # Top-Left Live Badge & Category
        draw.rectangle([40, 30, 170, 80], fill=RED)
        # Pulsing Red Dot
        dot_r = 6 + int(3 * math.sin(t * 6.0))
        draw.ellipse([55 - dot_r, 55 - dot_r, 55 + dot_r, 55 + dot_r], fill=WHITE)
        draw.text((70, 38), "LIVE", fill=WHITE, font=f_bold(32))

        # Category Pill
        clean_cat = sanitize_text(category or "BREAKING NEWS").upper()
        draw.rectangle([180, 30, 480, 80], fill=(20, 45, 95), outline=GOLD, width=2)
        draw.text((200, 40), f"NEWS • {clean_cat}", fill=WHITE, font=f_bold(28))

        # Top-Right Breaking Flash Bar (x: 800 to 1880, y: 30)
        draw.rectangle([780, 30, w - 40, 80], fill=(180, 0, 0), outline=GOLD, width=2)
        draw_cairo_text(canvas, (800, 40), "FLASH: रांची में धारा 144 लागू | पुलिस सतर्क", font_size=26, font_name="Hind", text_color=WHITE, is_bold=True)

        # 2.5 RIGHT-SIDE KEY HEADLINES PANEL (x: 1340 to 1880, y: 100 to 710)
        draw.rectangle([1340, 100, w - 40, 710], fill=(10, 22, 45, 230), outline=GOLD, width=2)
        # Header Badge
        draw.rectangle([1340, 100, w - 40, 155], fill=(220, 0, 0))
        draw_cairo_text(canvas, (1355, 112), "⚡ बड़ी बातें (HIGHLIGHTS)", font_size=26, font_name="Hind", text_color=WHITE, is_bold=True)

        # Key Bullet Headlines
        key_points = [
            "• छात्रों का विधानसभा मार्च",
            "• परीक्षा धांधली पर CBI मांग",
            "• मौके पर भारी पुलिस तैनात",
            "• धारा 144 लागू की गई",
            "• लाइव अपडेट्स AI-NewsTube"
        ]
        y_kp = 175
        for kp in key_points:
            color = GOLD if ("CBI" in kp or "144" in kp) else WHITE
            draw_cairo_text(canvas, (1355, y_kp), kp, font_size=24, font_name="Hind", text_color=color, is_bold=True)
            draw.line([(1355, y_kp + 42), (w - 60, y_kp + 42)], fill=(40, 70, 120), width=1)
            y_kp += 54

        # 3. TV LOWER-THIRD GRAPHICS BANNER (y: 750 to 960)
        # Main Headline Box (Yellow Accent)
        draw.rectangle([40, 750, w - 40, 860], fill=(255, 230, 0), outline=(0, 0, 0), width=2)
        
        clean_h = sanitize_text(headline)
        words = clean_h.split()
        h_lines = []
        curr = []
        for word in words:
            curr.append(word)
            if len(" ".join(curr)) > 36:
                h_lines.append(" ".join(curr[:-1]))
                curr = [word]
        if curr:
            h_lines.append(" ".join(curr))

        y_h = 760
        for hl in h_lines[:2]:
            draw_cairo_text(canvas, (65, y_h), hl, font_size=40, font_name="Hind", text_color=(0, 0, 0), is_bold=True)
            y_h += 48

        # Sub-headline / Summary Box (Navy Blue)
        draw.rectangle([40, 860, w - 40, 960], fill=BLUE_BOX, outline=GOLD, width=2)
        clean_sub = sanitize_text(sub_text or clean_h)
        draw_cairo_text(canvas, (65, 885), clean_sub[:95], font_size=30, font_name="Hind", text_color=WHITE, is_bold=True)

        # Photo Credit (Small Tag on Bottom-Left of Photo)
        draw.rectangle([40, 715, 460, 745], fill=(0, 0, 0, 180))
        draw_cairo_text(canvas, (50, 720), active_credit, font_size=20, font_name="Hind", text_color=WHITE, is_bold=False)

        # 4. BOTTOM SCROLLING TICKER BAR (y: 970 to 1080)
        draw.rectangle([0, 970, w, h], fill=DARK_BAR)

        # Multi-Headline Scrolling Ticker Animation (moves right-to-left)
        clean_ticker = sanitize_text(ticker_text or "ताज़ा समाचार: देश और दुनिया की आज की बड़ी ख़बरें | AI-NewsTube")
        # Extend ticker with additional breaking headlines
        full_ticker_str = f" {clean_ticker}   •   झारखंड छात्र आंदोलन: विधानसभा घेराव और बड़ी कार्रवाई   •   देश-दुनिया की तमाम बड़ी ख़बरें लाइव   •   "
        
        # Calculate ticker scrolling position starting from x=240
        ticker_len_px = len(full_ticker_str) * 22
        scroll_offset = int((t * 160) % (ticker_len_px + w))
        ticker_x = w - scroll_offset

        # Draw ticker text behind the red badge label
        draw_cairo_text(canvas, (ticker_x, 1005), full_ticker_str, font_size=34, font_name="Hind", text_color=GOLD, is_bold=True)

        # Red Ticker Label Box (drawn OVER the text to act as a solid mask overlay)
        draw.rectangle([0, 970, 240, h], fill=RED)
        draw_cairo_text(canvas, (25, 1005), "ताज़ा समाचार", font_size=34, font_name="Hind", text_color=WHITE, is_bold=True)

        return canvas

    @classmethod
    def render_live_feed_video(
        cls,
        headline: str,
        category: str,
        photo_paths: List[str],
        photo_credits: List[str],
        audio_path: str,
        output_path: Path,
        sub_text: str = "",
        ticker_text: str = ""
    ) -> Path:
        """Renders 1080p Full HD Live TV Feed Video using MoviePy (NO 3D anchors)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = 1920, 1080
        fps = 25

        # Load real photo images
        photos = []
        for p in photo_paths:
            if p and os.path.exists(p):
                try:
                    photos.append(Image.open(p).convert("RGB"))
                except Exception:
                    pass
        if not photos:
            # Fallback canvas if no photo
            blank = Image.new("RGB", (w, h), DARK_BG)
            photos = [blank]

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        def make_frame(t):
            frame_img = cls.render_live_feed_frame(
                w=w, h=h, t=t, duration=duration,
                headline=headline, category=category,
                photos=photos, photo_credits=photo_credits,
                ticker_text=ticker_text, sub_text=sub_text
            )
            return np.array(frame_img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.with_audio(audio_clip)

        logger.info(f"🎬 [LIVE FEED RENDERER] Exporting {duration:.1f}s Live TV Feed Video to {output_path.name}...")
        clip.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac"
        )
        audio_clip.close()
        logger.info(f"✅ [LIVE FEED RENDERER] Video Rendered Successfully: {output_path.name}")
        return output_path
