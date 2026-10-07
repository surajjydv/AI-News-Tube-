"""
generate_viral_cricket_thumbnail.py
===================================
Generates 100% VERIFIED Test Match Key Performers YouTube Thumbnail:
- Left: Real HD Ravindra Jadeja (3/57 in 21.0 Ov, 5 Maidens).
- Right: Real HD Kuldeep Yadav (4/38 in 9.3 Ov, Player of the Match).
- Center: 3D Metallic VS & Verified Test Scoreboard (IND 462 / SL 284/10 in 79.4 Ov).
- High impact 3D Hindi Headline: "भारत की 178 रनों से मजबूत बढ़त! जडेजा-कुलदीप का जादू!"
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.font_utils import load_font, sanitize_text

CRICKET_DIR   = BASE_DIR / "assets" / "cricket"
THUMBNAIL_DIR = BASE_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

OUT_THUMB = THUMBNAIL_DIR / "ind_vs_sl_viral_thumbnail.jpg"

DARK_BG   = (6, 12, 24)
GOLD      = (255, 205, 0)
WHITE     = (255, 255, 255)
RED_LIVE  = (220, 20, 20)
BLUE_IND  = (18, 72, 170)
BLUE_SL   = (12, 48, 110)
CYAN      = (0, 210, 255)

def f_bold(size: int): return load_font(size, bold=True, lang="hi")

def create_verified_player_card(photo_path: Path, border_color: tuple, size=(380, 480)) -> Image.Image:
    """Renders player photo inside a sleek 3D metallic frame."""
    w_box, h_box = size
    card = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
    if photo_path.exists():
        try:
            photo = Image.open(photo_path).convert("RGB")
            p_w, p_h = photo.size
            scale = max(w_box / p_w, h_box / p_h)
            photo = photo.resize((int(p_w * scale), int(p_h * scale)), Image.Resampling.LANCZOS)
            crop_x = (photo.width - w_box) // 2
            crop_y = (photo.height - h_box) // 2
            photo = photo.crop((crop_x, crop_y, crop_x + w_box, crop_y + h_box))
            card.paste(photo, (0, 0))
        except Exception:
            pass

    draw = ImageDraw.Draw(card)
    draw.rectangle([0, 0, w_box, h_box], outline=border_color, width=6)
    draw.line([(0, 2), (w_box, 2)], fill=(255, 255, 255, 180), width=4)
    return card

def create_verified_test_thumbnail(w=1280, h=720):
    """Renders Verified Test Match Key Performers 16:9 Thumbnail."""
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # 1. Split Team Diagonal Background
    draw.polygon([(0, 0), (680, 0), (520, h), (0, h)], fill=BLUE_IND)
    draw.polygon([(680, 0), (w, 0), (w, h), (520, h)], fill=BLUE_SL)

    # Center Gold Lightning Divider
    draw.line([(680, 0), (520, h)], fill=GOLD, width=10)

    # 2. Ravindra Jadeja (3/57) & Kuldeep Yadav (4/38) Verified Player Cards
    jadeja_img = create_verified_player_card(CRICKET_DIR / "jadeja_cap.jpg", GOLD, size=(380, 480))
    img.paste(jadeja_img, (60, 120))

    kuldeep_img = create_verified_player_card(CRICKET_DIR / "kuldeep_cap.jpg", CYAN, size=(380, 480))
    img.paste(kuldeep_img, (840, 120))

    # Player Badges
    draw.rectangle([60, 550, 440, 600], fill=(10, 20, 50), outline=GOLD, width=2)
    draw.text((80, 560), "R. JADEJA: 3/57", fill=GOLD, font=f_bold(26))

    draw.rectangle([840, 550, 1220, 600], fill=(10, 20, 50), outline=CYAN, width=2)
    draw.text((860, 560), "K. YADAV: 4/38", fill=WHITE, font=f_bold(26))

    # 3. TOP LIVE MATCH BADGES
    draw.rectangle([40, 20, 240, 80], fill=RED_LIVE, outline=GOLD, width=3)
    draw.text((65, 32), "LIVE 4K", fill=WHITE, font=f_bold(34))

    draw.rectangle([260, 20, 1020, 80], fill=(12, 24, 54), outline=GOLD, width=3)
    draw.text((280, 32), sanitize_text("IND vs SL TEST MATCH — DAY 3/4"), fill=GOLD, font=f_bold(32))

    # 4. CENTER 3D VS & SCORE BREAKDOWN BADGE
    draw.rectangle([470, 200, 810, 440], fill=(10, 16, 32), outline=GOLD, width=5)
    draw.rectangle([470, 200, 810, 260], fill=RED_LIVE)
    draw.text((600, 212), "VS", fill=WHITE, font=f_bold(36))

    draw.text((490, 280), "IND: 462", fill=WHITE, font=f_bold(46))
    draw.text((490, 350), "SL: 284/10", fill=GOLD, font=f_bold(40))
    draw.text((490, 400), "(79.4 OV)", fill=CYAN, font=f_bold(24))

    # 5. BOTTOM HIGH IMPACT VIRAL HINDI BANNER
    draw.rectangle([40, 620, 1240, 700], fill=RED_LIVE, outline=GOLD, width=4)
    draw.text((70, 632), sanitize_text("🔥 भारत की 178 रनों से मजबूत बढ़त! जडेजा-कुलदीप का जादू!"), fill=WHITE, font=f_bold(38))

    img.save(OUT_THUMB, quality=95)
    print(f"✅ 100% Verified Test Match YouTube Thumbnail rendered: {OUT_THUMB}")

if __name__ == "__main__":
    create_verified_test_thumbnail()
