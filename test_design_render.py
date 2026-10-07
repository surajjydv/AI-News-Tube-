import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from utils.font_utils import draw_shaped_text, sanitize_text, load_font, FONT_DIR

def render_sample():
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (15, 20, 32, 255))
    
    # Try using an existing photo if available
    photo_path = Path("output/doc_thumb_1787774197_046570d6.jpg")
    if photo_path.exists():
        bg = Image.open(photo_path).convert("RGBA").resize((W, H))
        canvas.paste(bg, (0, 0))
    
    # Add subtle lower third gradient vignette
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for y in range(H - 450, H):
        alpha = int(200 * ((y - (H - 450)) / 450) ** 1.3)
        vd.line([(0, y), (W, y)], fill=(5, 8, 16, alpha))
    canvas = Image.alpha_composite(canvas, vignette)
    
    # Draw top badges
    d = ImageDraw.Draw(canvas)
    # LIVE badge
    d.rounded_rectangle([(40, 36), (230, 76)], radius=6, fill=(220, 20, 35), outline=(255, 90, 90, 220), width=2)
    draw_shaped_text(canvas, (54, 45), "SRJ UNDERRATED", font_size=22, bold=True, text_color=(255, 255, 255))
    d.ellipse([(46, 52), (54, 60)], fill=(255, 255, 255))
    
    # Category tag
    d.rounded_rectangle([(40, 88), (210, 118)], radius=5, fill=(15, 25, 50, 220), outline=(255, 200, 0), width=1)
    draw_shaped_text(canvas, (50, 94), "TOP STORIES", font_size=16, bold=True, text_color=(255, 200, 0))
    
    # Slide label
    draw_shaped_text(canvas, (W - 220, 44), "◆ OPENING", font_size=18, bold=True, text_color=(210, 210, 210))
    for i in range(4):
        cx_dot = W - 40 - (4 - i - 1) * 18 - 10
        col = (255, 200, 0) if i == 0 else (90, 90, 90)
        d.ellipse([(cx_dot-5, 76), (cx_dot+5, 86)], fill=col)

    # -------------------------------------------------------------
    # NEW LOWER-THIRD HEADLINE (Clean, Modern Broadcast Card)
    # -------------------------------------------------------------
    headline_line1 = "Delhi Police Detains Opposition Leaders"
    headline_line2 = "High Drama in Capital Over CEC Resignation Demand"
    
    card_x = 50
    card_y = H - 280
    card_w = 1450
    card_h = 175
    
    # Glassmorphic card overlay
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    
    # Dark glass base with subtle border
    cd.rounded_rectangle([(0, 0), (card_w, card_h)], radius=12, fill=(8, 14, 28, 230), outline=(50, 70, 110, 180), width=1)
    # Glowing top accent stripe
    cd.rounded_rectangle([(0, 0), (card_w, 4)], radius=2, fill=(255, 204, 0, 255))
    # Left red accent bar
    cd.rounded_rectangle([(0, 0), (8, card_h)], radius=2, fill=(220, 20, 35, 255))
    
    # Pill badge
    cd.rounded_rectangle([(25, 16), (185, 42)], radius=5, fill=(220, 20, 35, 240))
    draw_shaped_text(card, (36, 21), "⚡ LIVE REPORT", font_size=15, bold=True, text_color=(255, 255, 255))
    
    # Line 1: Primary Headline (Electric Gold / Pure White, Hind-Bold)
    draw_shaped_text(card, (25, 52), headline_line1, font_size=46, bold=True, text_color=(255, 215, 0), shadow=True)
    
    # Line 2: Context / Subhead (Crisp White, Hind-Medium)
    draw_shaped_text(card, (25, 112), headline_line2, font_size=34, bold=False, text_color=(245, 248, 255), shadow=True)
    
    canvas.paste(card, (card_x, card_y), card)
    
    # -------------------------------------------------------------
    # NEW BIGGER & BOLDER BOTTOM TICKER
    # -------------------------------------------------------------
    ty1, ty2 = H - 85, H
    # Ticker bar background
    d_canvas = ImageDraw.Draw(canvas)
    d_canvas.rectangle([(0, ty1), (W, ty2)], fill=(6, 10, 22, 255))
    # Vibrant top border line
    d_canvas.line([(0, ty1), (W, ty1)], fill=(220, 20, 35, 255), width=3)
    
    # Scrolling ticker text (Rendered first, size 30px!)
    ticker_text = "Delhi Police Detains Opposition Leaders   •   Supreme Court review scheduled tomorrow   •   Protests erupt across Jantar Mantar   •   "
    draw_shaped_text(canvas, (320, ty1 + 24), ticker_text, font_size=30, bold=True, text_color=(255, 255, 255))
    
    # Red Breaking News badge (Drawn on top to matte the left edge!)
    badge_w = 280
    badge_img = Image.new("RGBA", (badge_w, ty2 - ty1), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge_img)
    # Angled polygon badge
    bd.polygon([(0, 0), (badge_w, 0), (badge_w - 24, ty2 - ty1), (0, ty2 - ty1)], fill=(220, 20, 35, 255))
    draw_shaped_text(badge_img, (20, 24), "🔴 BREAKING NEWS", font_size=24, bold=True, text_color=(255, 255, 255))
    canvas.paste(badge_img, (0, ty1), badge_img)
    
    canvas.convert("RGB").save("output/test_new_design.png")
    print("Saved output/test_new_design.png successfully!")

if __name__ == "__main__":
    render_sample()
