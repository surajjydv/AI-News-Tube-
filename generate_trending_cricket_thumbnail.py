"""
generate_trending_cricket_thumbnail.py
======================================
Generates a viral High-CTR YouTube Cricket News Thumbnail matching the exact 3-Band Header + 5-Photo Grid layout requested by the user.
Bands:
1. Top Red Band: White bold numbers "6  6  6  6"
2. Yellow Band: Bold Black Hindi headline "रोहित ने 1 ओवर में लगाए 4 छक्के"
3. Blue Band: Bold White Hindi reaction headline "गंभीर ने सीट से उछल कर पीटी ताली"
Grid:
- Center Big Photo: Gambhir & Rohit celebrating
- Left Column: 2 Action Shots
- Right Column: 2 Action Shots
- White Grid Dividers
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.font_utils import load_font, sanitize_text
from services.youtube_upload_service import get_authenticated_service
from googleapiclient.http import MediaFileUpload

CRICKET_DIR = BASE_DIR / "assets" / "cricket"
THUMBNAIL_OUTPUT = BASE_DIR / "thumbnails" / "trending_cricket_thumbnail.jpg"

REACTION_PHOTO = CRICKET_DIR / "reaction.jpg"
ACTION1_PHOTO  = CRICKET_DIR / "action1.jpg"
ACTION2_PHOTO  = CRICKET_DIR / "action2.jpg"
ACTION3_PHOTO  = CRICKET_DIR / "action3.jpg"
ACTION4_PHOTO  = CRICKET_DIR / "action4.jpg"

# Font Helper
def f_bold(size: int):
    return load_font(size, bold=True, lang="hi")

def create_trending_thumbnail(w=1280, h=720) -> Path:
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # -------------------------------------------------------------
    # 1. TOP HEADER SECTION (3 COLOR BANDS) - Total Height = 310px
    # -------------------------------------------------------------
    # Band 1: RED BAND (y: 0 to 80)
    draw.rectangle([0, 0, w, 80], fill=(160, 0, 0))
    f_num = f_bold(65)
    # Centered white bold numbers "6   6   6   6"
    num_text = "6     6     6     6"
    draw.text((w // 2 - 180, 2), num_text, fill=(255, 255, 255), font=f_num)

    # Band 2: YELLOW BAND (y: 80 to 200)
    draw.rectangle([0, 80, w, 200], fill=(255, 230, 0))
    f_yellow = f_bold(52)
    t_yellow = sanitize_text("रोहित ने 1 ओवर में लगाए 4 छक्के")
    # Draw dark shadow and black text
    draw.text((w // 2 - 448, 108), t_yellow, fill=(0, 0, 0), font=f_yellow)

    # Band 3: DARK BLUE BAND (y: 200 to 300)
    draw.rectangle([0, 200, w, 300], fill=(12, 28, 70))
    f_blue = f_bold(48)
    t_blue = sanitize_text("गंभीर ने सीट से उछल कर पीटी ताली")
    draw.text((w // 2 - 438, 222), t_blue, fill=(255, 255, 255), font=f_blue)

    # White Border line below blue header
    draw.line([(0, 300), (w, 300)], fill=(255, 255, 255), width=5)

    # -------------------------------------------------------------
    # 2. BOTTOM COMPOSITE PHOTO GRID (y: 305 to 720)
    # Grid Layout:
    # Left Col (w: 0 to 390) -> 2 Action photos
    # Center Col (w: 395 to 885) -> Big Reaction Photo (Gambhir & Rohit)
    # Right Col (w: 890 to 1280) -> 2 Action photos
    # -------------------------------------------------------------
    grid_y = 305
    grid_h = h - grid_y # 415px

    # Helper function to crop/resize image to box
    def fit_image(path: Path, box_w: int, box_h: int) -> Image.Image:
        if path.exists():
            try:
                im = Image.open(path).convert("RGB")
                # Center crop
                im_aspect = im.width / im.height
                box_aspect = box_w / box_h
                if im_aspect > box_aspect:
                    new_w = int(im.height * box_aspect)
                    offset = (im.width - new_w) // 2
                    im = im.crop((offset, 0, offset + new_w, im.height))
                else:
                    new_h = int(im.width / box_aspect)
                    offset = (im.height - new_h) // 2
                    im = im.crop((0, offset, im.width, offset + new_h))
                return im.resize((box_w, box_h), Image.Resampling.LANCZOS)
            except Exception:
                pass
        # Fallback solid color image
        fb = Image.new("RGB", (box_w, box_h), (20, 40, 80))
        d = ImageDraw.Draw(fb)
        d.text((20, 20), "CRICKET ACTION", fill=(255, 200, 0), font=f_bold(24))
        return fb

    # Widths
    left_w = 390
    center_w = 490
    right_w = w - (left_w + center_w + 10) # 390px
    row_h = (grid_h - 4) // 2 # ~205px

    # 1. Left Top (Action 1)
    im_a1 = fit_image(ACTION1_PHOTO, left_w, row_h)
    img.paste(im_a1, (0, grid_y))

    # 2. Left Bottom (Action 2)
    im_a2 = fit_image(ACTION2_PHOTO, left_w, row_h)
    img.paste(im_a2, (0, grid_y + row_h + 4))

    # 3. Center Big Box (Reaction Shot)
    im_react = fit_image(REACTION_PHOTO, center_w, grid_h)
    img.paste(im_react, (left_w + 5, grid_y))

    # 4. Right Top (Action 3)
    im_a3 = fit_image(ACTION3_PHOTO, right_w, row_h)
    img.paste(im_a3, (left_w + center_w + 10, grid_y))

    # 5. Right Bottom (Action 4)
    im_a4 = fit_image(ACTION4_PHOTO, right_w, row_h)
    img.paste(im_a4, (left_w + center_w + 10, grid_y + row_h + 4))

    # White Vertical & Horizontal Grid Border Lines
    draw.line([(left_w + 2, grid_y), (left_w + 2, h)], fill=(255, 255, 255), width=5)
    draw.line([(left_w + center_w + 7, grid_y), (left_w + center_w + 7, h)], fill=(255, 255, 255), width=5)
    draw.line([(0, grid_y + row_h + 2), (left_w, grid_y + row_h + 2)], fill=(255, 255, 255), width=4)
    draw.line([(left_w + center_w + 10, grid_y + row_h + 2), (w, grid_y + row_h + 2)], fill=(255, 255, 255), width=4)

    # -------------------------------------------------------------
    # 3. SCORECARD BADGE OVERLAY AT BOTTOM RIGHT
    # -------------------------------------------------------------
    draw.rectangle([w - 180, h - 55, w - 15, h - 15], fill=(0, 0, 0), outline=(255, 255, 255), width=2)
    draw.text((w - 165, h - 48), "IND vs SL", fill=(255, 200, 0), font=f_bold(24))

    THUMBNAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_OUTPUT, quality=95)
    print(f"✅ Generated High-CTR Trending Thumbnail: {THUMBNAIL_OUTPUT.name}")
    return THUMBNAIL_OUTPUT

def update_youtube_thumbnail(video_id="WTvQBbm_Pag", thumb_path=THUMBNAIL_OUTPUT):
    """Updates the thumbnail for the specified YouTube Video ID via YouTube Data API."""
    print(f"🚀 Updating YouTube Video Thumbnail for Video ID: {video_id}...")
    try:
        youtube = get_authenticated_service()
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumb_path))
        ).execute()
        print("✅ YouTube Video Thumbnail Updated Successfully!")
        return True
    except Exception as e:
        print(f"❌ YouTube Thumbnail Update Error: {e}")
        return False

def main():
    print("🎨 STEP 1: Creating Trending High-CTR Thumbnail...")
    thumb_path = create_trending_thumbnail()

    print("📤 STEP 2: Updating YouTube Video Thumbnail...")
    update_youtube_thumbnail("WTvQBbm_Pag", thumb_path)

if __name__ == "__main__":
    main()
