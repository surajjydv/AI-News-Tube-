import os
import sys
import time
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.broadcast_25d_engine import (
    render_25d_top_header,
    render_25d_floating_media_frame,
    render_25d_headline_panel,
    render_25d_dual_tickers,
    draw_25d_beveled_panel,
    draw_soft_drop_shadow_rect,
    draw_pulsing_live_beacon,
    create_vertical_gradient,
    GOLD, GOLD_LIGHT, GOLD_DARK, WHITE, CYAN_HIGHLIGHT, CRIMSON, CRIMSON_GLOW
)
from utils.font_utils import draw_shaped_text, sanitize_text, load_font

def render_test_25d_frame(out_path: Path):
    w, h = 1920, 1080
    t = 2.5

    # 1. Base Canvas with Deep Broadcast Gradient & Ambient Vignette
    img = create_vertical_gradient(w, h, (10, 15, 35), (4, 7, 18), mid_color=(12, 18, 42), mid_pos=0.35)
    draw = ImageDraw.Draw(img)

    # Subtle broadcast grid texture (refined low opacity)
    for gy in range(0, h, 60):
        draw.line([(0, gy), (w, gy)], fill=(18, 28, 58), width=1)
    for gx in range(0, w, 90):
        draw.line([(gx, 0), (gx, h)], fill=(18, 28, 58), width=1)

    # 2. TOP HEADER
    render_25d_top_header(img, category="NATIONAL NEWS", t=t, w=w)

    # 3. LEFT 3 NEWS CARDS
    headline = "सुप्रीम कोर्ट का ऐतिहासिक फैसला: केंद्र सरकार को दिए कड़े निर्देश"
    takeaways = [
        "मुख्य घटनाक्रम: संविधान पीठ ने सर्वसम्मति से पारित किया आदेश",
        "ग्राउंड रिपोर्ट: सभी संबंधित पक्षों को नोटिस जारी कर मांगा हलफनामा",
        "आगामी सुनवाई: अगली तारीख पर विस्तृत समीक्षा एवं जांच रिपोर्ट पेश होगी"
    ]

    card_items = [
        ("▶ मुख्य घटनाक्रम", takeaways[0], 0),
        ("▶ ग्राउंड फैक्ट्स व विवरण", takeaways[1], 1),
        ("▶ ताज़ा स्थिति व प्रभाव", takeaways[2], 2)
    ]
    card_positions = [
        (100, 280),
        (295, 475),
        (490, 670)
    ]

    for (c_label, c_desc, c_idx), (cy1, cy2) in zip(card_items, card_positions):
        is_active = (c_idx == 1)
        c_xy = (50, cy1, 760, cy2)

        # Draw 2.5D Beveled Glass Panel
        draw_25d_beveled_panel(
            img, c_xy, radius=12,
            top_color=(26, 46, 96) if is_active else (14, 22, 46),
            bot_color=(14, 24, 56) if is_active else (8, 14, 30),
            border_color=GOLD if is_active else (50, 85, 145),
            border_width=3 if is_active else 1,
            top_highlight=CYAN_HIGHLIGHT if is_active else (40, 65, 110),
            drop_shadow=True,
            is_active=is_active
        )

        d = ImageDraw.Draw(img)

        # Left 3D Accent Indicator Beacon
        if is_active:
            beacon_w = int(14 + 5 * math.sin(t * 5.0))
            d.rounded_rectangle([(50, cy1), (50 + beacon_w, cy2)], radius=4, fill=GOLD)
            d.rounded_rectangle([(50, cy1), (56, cy2)], radius=2, fill=GOLD_LIGHT)
            d.line([(50 + beacon_w, cy1), (50 + beacon_w, cy2)], fill=GOLD_DARK, width=1)
        else:
            d.rounded_rectangle([(50, cy1), (62, cy2)], radius=4, fill=(45, 75, 125))

        # 3D Category Pill Header
        pill_xy = (78, cy1 + 12, 360, cy1 + 48)
        draw_25d_beveled_panel(
            img, pill_xy, radius=6,
            top_color=(215, 20, 28) if is_active else (24, 42, 85),
            bot_color=(125, 8, 14) if is_active else (14, 24, 52),
            border_color=GOLD if is_active else (40, 70, 130),
            border_width=1,
            top_highlight=CRIMSON_GLOW if is_active else CYAN_HIGHLIGHT,
            drop_shadow=True,
            is_active=False
        )
        draw_shaped_text(img, (92, cy1 + 15), c_label, font_size=21, bold=True, text_color=WHITE)

        # Content Text (HarfBuzz Shaped Hindi)
        words = c_desc.split()
        lines = []
        if len(c_desc) > 28:
            mid = len(words) // 2
            lines.append(" ".join(words[:mid + 1]))
            lines.append(" ".join(words[mid + 1:]))
        else:
            lines.append(c_desc)

        yt = cy1 + 60
        for line in lines[:2]:
            text_col = (255, 255, 255) if is_active else (210, 225, 245)
            draw_shaped_text(img, (82, yt), line, font_size=23, bold=is_active, text_color=text_col, shadow=is_active)
            yt += 36

    # 4. RIGHT SECTION: 2.5D FLOATING MEDIA VIEWPORT
    photo_file = BASE_DIR / "assets" / "real_event_photo_1.jpg"
    photo_img = Image.open(photo_file) if photo_file.exists() else None

    render_25d_floating_media_frame(
        img,
        xy=(785, 100, 1870, 670),
        photo_img=photo_img,
        rel_t=0.5,
        slide_tag="[ SPECIAL REPORT ] (2/3)",
        credit_text="Verified Press Wire / Supreme Court Bureau"
    )

    # 5. LOWER-THIRD MEGA HEADLINE PANEL
    render_25d_headline_panel(
        img,
        headline_text=headline,
        t=t,
        base_y1=695,
        base_y2=910
    )

    # 6. BOTTOM DUAL-ROW TICKERS
    render_25d_dual_tickers(
        img,
        headline_text=headline,
        takeaways=takeaways,
        category="NATIONAL",
        t=t,
        w=w,
        h=h
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    print(f"✅ Rendered Test 2.5D Frame: {out_path}")

if __name__ == "__main__":
    import math
    from PIL import ImageDraw
    render_test_25d_frame(BASE_DIR / "assets" / "test_25d_proof.png")
