"""
services/pro_tv_engine.py
=========================
Professional TV News Broadcast Engine (Zero Blending, 100% Sharp High-Contrast Graphics):
Renders a 1080p Full HD TV Broadcast video featuring:
1. Authentic Real Event Photos (Full 16:9 Stage).
2. Solid, High-Contrast TV News Lower-Third (Bright Yellow Gold Headline Banner + Dark Navy Sub-banner).
3. NO Alpha Blending / NO Muddy Text / NO 3D Avatars.
4. Top TV News Station Badges ('🔴 LIVE | SPECIAL REPORT') and Bottom News Ticker.
"""

import os
import sys
import math
import numpy as np
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.font_utils import load_font, sanitize_text
from utils.logger import logger
from moviepy import VideoClip, AudioFileClip

# Color Palette: TV Station High-Contrast Colors
SOLID_DARK_BG = (12, 18, 32)
BRIGHT_YELLOW = (255, 220, 0)
SOLID_RED     = (210, 20, 20)
SOLID_NAVY    = (10, 24, 55)
PURE_WHITE    = (255, 255, 255)
PURE_BLACK    = (0, 0, 0)

def f_bold(sz: int):
    return load_font(sz, bold=True, lang="hi")

def f_reg(sz: int):
    return load_font(sz, bold=False, lang="hi")

class ProTVEngine:
    """
    Professional TV News Broadcast Engine:
    Renders sharp, crisp, high-contrast TV News Broadcast frames with real photos and solid graphics.
    """

    @classmethod
    def render_tv_frame(
        cls,
        w: int,
        h: int,
        t: float,
        headline: str,
        category: str,
        photos: List[Image.Image],
        photo_credits: List[str],
        ticker_text: str,
        sub_text: str = ""
    ) -> Image.Image:
        # Create solid background canvas
        canvas = Image.new("RGB", (w, h), SOLID_DARK_BG)

        # 1. Real Event Photo Presentation (16:9 Fit/Fill)
        photo_idx = int(t // 5.0) % len(photos) if photos else 0
        active_photo = photos[photo_idx] if photo_idx < len(photos) and photos[photo_idx] else None
        active_credit = photo_credits[photo_idx] if photo_idx < len(photo_credits) else "Photo: Press News Coverage"

        if active_photo:
            try:
                pw, ph = active_photo.size
                target_ratio = w / h
                photo_ratio = pw / ph

                if photo_ratio > target_ratio:
                    crop_h = ph
                    crop_w = int(ph * target_ratio)
                else:
                    crop_w = pw
                    crop_h = int(pw / target_ratio)

                left = (pw - crop_w) // 2
                top = (ph - crop_h) // 2

                cropped = active_photo.crop((left, top, left + crop_w, top + crop_h))
                resized = cropped.resize((w, h), Image.Resampling.LANCZOS)
                canvas.paste(resized, (0, 0))
            except Exception:
                pass

        draw = ImageDraw.Draw(canvas)

        # 2. TOP TV BADGES (Solid, Sharp, High-Contrast)
        # Live Red Badge
        draw.rectangle([50, 40, 200, 95], fill=SOLID_RED, outline=PURE_WHITE, width=2)
        draw.text((75, 48), "🔴 LIVE", fill=PURE_WHITE, font=f_bold(34))

        # Category Pill
        clean_cat = sanitize_text(category or "BREAKING NEWS").upper()
        draw.rectangle([210, 40, 520, 95], fill=SOLID_NAVY, outline=BRIGHT_YELLOW, width=2)
        draw.text((230, 52), f"📌 {clean_cat}", fill=PURE_WHITE, font=f_bold(28))

        # Channel Branding Top-Right
        draw.rectangle([w - 420, 40, w - 50, 95], fill=SOLID_NAVY, outline=(60, 90, 160), width=2)
        draw.text((w - 395, 52), "AI-NEWSTUBE EXCLUSIVE", fill=BRIGHT_YELLOW, font=f_bold(26))

        # Photo Credit Badge (Above Lower-Third)
        draw.rectangle([50, 635, 480, 670], fill=PURE_BLACK)
        draw.text((60, 640), sanitize_text(active_credit[:45]), fill=PURE_WHITE, font=f_reg(20))

        # 3. TV LOWER-THIRD HEADLINE BANNER (Solid Gold/Yellow & Dark Navy - 100% HINDI DEVANAGARI)
        clean_h = sanitize_text(headline)
        clean_sub = sanitize_text(sub_text or clean_h)

        # Yellow Headline Container (Solid 100% Opaque)
        draw.rectangle([50, 675, w - 50, 795], fill=BRIGHT_YELLOW, outline=PURE_BLACK, width=3)

        words = clean_h.split()
        h_lines = []
        curr = []
        for word in words:
            curr.append(word)
            if len(" ".join(curr)) > 34:
                h_lines.append(" ".join(curr[:-1]))
                curr = [word]
        if curr:
            h_lines.append(" ".join(curr))

        y_h = 688
        for hl in h_lines[:2]:
            draw.text((75, y_h), hl, fill=PURE_BLACK, font=f_bold(44))
            y_h += 50

        # Navy Sub-headline Container (Solid 100% Opaque)
        draw.rectangle([50, 795, w - 50, 915], fill=SOLID_NAVY, outline=BRIGHT_YELLOW, width=2)
        draw.text((75, 830), clean_sub[:90], fill=PURE_WHITE, font=f_bold(34))

        # 4. BOTTOM TICKER BAR (Solid Dark Navy + Red Header - NO OVERLAP)
        draw.rectangle([0, 930, w, h], fill=(10, 16, 30))
        draw.rectangle([0, 930, 260, h], fill=SOLID_RED)
        draw.text((30, 975), "ताज़ा समाचार", fill=PURE_WHITE, font=f_bold(34))

        # Animated Hindi News Ticker
        clean_ticker = sanitize_text(ticker_text or "🔥 ताज़ा समाचार: देश और दुनिया की बड़ी ख़बरें | AI-NewsTube")
        ticker_x = int(w - (t * 190) % (w + len(clean_ticker) * 26))
        draw.text((ticker_x + 270, 975), f"🔥 {clean_ticker}", fill=BRIGHT_YELLOW, font=f_bold(34))

        return canvas

    @classmethod
    def render_pro_tv_video(
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
        """Renders 1080p Professional TV Broadcast Video using MoviePy (Zero Blending, 100% Solid TV Graphics)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = 1920, 1080
        fps = 25

        photos = []
        for p in photo_paths:
            if p and os.path.exists(p):
                try:
                    photos.append(Image.open(p).convert("RGB"))
                except Exception:
                    pass
        if not photos:
            blank = Image.new("RGB", (w, h), SOLID_DARK_BG)
            photos = [blank]

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        def make_frame(t):
            frame_img = cls.render_tv_frame(
                w=w, h=h, t=t,
                headline=headline, category=category,
                photos=photos, photo_credits=photo_credits,
                ticker_text=ticker_text, sub_text=sub_text
            )
            return np.array(frame_img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.with_audio(audio_clip)

        logger.info(f"🎬 [PRO TV ENGINE] Exporting Professional TV Broadcast Video to {output_path.name}...")
        clip.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac"
        )
        audio_clip.close()
        logger.info(f"✅ [PRO TV ENGINE] Video Rendered Successfully: {output_path.name}")
        return output_path
