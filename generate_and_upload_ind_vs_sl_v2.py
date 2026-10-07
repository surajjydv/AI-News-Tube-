"""
generate_and_upload_ind_vs_sl_v2.py
====================================
Generates a broadcast-grade 3-scene Cricket News Bulletin for IND vs SL Today's Match:
1. Scene 1: Match Overview & Live Scorecard (IND 298/6 vs SL 245/10) with BCCI & SLC logos + Team photos.
2. Scene 2: Top Performers & Key Player Stats (Rohit Sharma 92, Virat Kohli 64, Kuldeep Yadav 4/38).
3. Scene 3: Match Summary & Highlights (Toss, Venue, Boundary stats).
Includes clean Devanagari text rendering (Mukta-Bold.ttf - NO tofu boxes) and custom YouTube Thumbnail.
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from utils.font_utils import load_font, sanitize_text
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# File Paths
CRICKET_DIR = BASE_DIR / "assets" / "cricket"
CRICKET_DIR.mkdir(parents=True, exist_ok=True)

IND_PHOTO_PATH = CRICKET_DIR / "ind_team.jpg"
SL_PHOTO_PATH  = CRICKET_DIR / "sl_team.jpg"

AUDIO_FILE     = BASE_DIR / "assets" / "ind_vs_sl_v2_audio.mp3"
FRAME1_FILE    = BASE_DIR / "assets" / "ind_vs_sl_scene1.jpg"
FRAME2_FILE    = BASE_DIR / "assets" / "ind_vs_sl_scene2.jpg"
FRAME3_FILE    = BASE_DIR / "assets" / "ind_vs_sl_scene3.jpg"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "ind_vs_sl_v2_thumbnail.jpg"
VIDEO_FILE     = BASE_DIR / "videos" / "ind_vs_sl_v2_match_update.mp4"

# Colors
DARK_BG   = (10, 18, 35)
BLUE_IND  = (20, 80, 180)
BLUE_SL   = (15, 60, 120)
GOLD      = (255, 200, 0)
RED       = (220, 35, 35)
WHITE     = (255, 255, 255)
DARK_BAR  = (15, 23, 42)
LIGHT_BLUE= (220, 240, 255)

# High Quality Font Loaders
def font_bold(size: int):
    return load_font(size, bold=True, lang="hi")

def font_reg(size: int):
    return load_font(size, bold=False, lang="hi")

# News Script
SCRIPT_TEXT = (
    "नमस्कार! AI-NewsTube की क्रिकेट स्पेशल बुलेटिन में आपका स्वागत है। "
    "आज भारत और श्रीलंका के बीच खेले गए रोमांचक वनडे मुकाबले में भारत ने श्रीलंका को 53 रनों से करारी शिकस्त दी। "
    "भारत ने पहले बल्लेबाजी करते हुए 50 ओवर में 6 विकेट पर 298 रनों का विशाल स्कोर खड़ा किया। "
    "कप्तान रोहित शर्मा ने धमाकेदार 92 रन बनाए, जबकि विराट कोहली ने 64 रनों की शानदार पारी खेली। "
    "जवाब में श्रीलंका की पूरी टीम 46.3 ओवर में 245 रनों पर ढेर हो गई। "
    "कुलदीप यादव ने बेहतरीन गेंदबाजी करते हुए 4 विकेट चटकाए। "
    "भारतीय टीम की इस शानदार जीत पर फैंस में भारी उत्साह है। ताज़ा स्पोर्ट्स अपडेट्स के लिए सब्सक्राइब करें AI-NewsTube!"
)

# -------------------------------------------------------------
# LOGO GENERATORS (BCCI & SLC LOGO BADGES)
# -------------------------------------------------------------
def draw_bcci_logo(size=140) -> Image.Image:
    """Generates a sharp 3D BCCI Logo Emblem."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    r = size // 2 - 5

    # Gold outer star ring
    draw.ellipse([5, 5, size - 5, size - 5], fill=(255, 193, 7), outline=(218, 165, 32), width=3)
    # Blue inner circle
    draw.ellipse([15, 15, size - 15, size - 15], fill=(0, 51, 153), outline=(255, 255, 255), width=2)

    # BCCI Text
    f_bcci = font_bold(int(size * 0.28))
    draw.text((center - int(size * 0.28), center - int(size * 0.22)), "BCCI", fill=(255, 255, 255), font=f_bcci)
    draw.text((center - int(size * 0.32), center + int(size * 0.08)), "INDIA", fill=GOLD, font=font_bold(int(size * 0.16)))
    return img

def draw_slc_logo(size=140) -> Image.Image:
    """Generates a sharp SLC (Sri Lanka Cricket) Emblem."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2

    # Shield Badge
    draw.ellipse([5, 5, size - 5, size - 5], fill=(255, 204, 0), outline=(200, 150, 0), width=3)
    draw.ellipse([15, 15, size - 15, size - 15], fill=(10, 40, 90), outline=(255, 255, 255), width=2)

    f_slc = font_bold(int(size * 0.30))
    draw.text((center - int(size * 0.24), center - int(size * 0.22)), "SLC", fill=GOLD, font=f_slc)
    draw.text((center - int(size * 0.36), center + int(size * 0.08)), "LANKA", fill=(255, 255, 255), font=font_bold(int(size * 0.16)))
    return img

# -------------------------------------------------------------
# SCENE 1: MATCH OVERVIEW & LIVE SCORECARD
# -------------------------------------------------------------
def render_scene_1(w=1920, h=1080) -> Path:
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Top Broadcast Header Bar
    draw.rectangle([0, 0, w, 100], fill=DARK_BAR)
    draw.rectangle([60, 20, 280, 80], fill=RED)
    draw.text((85, 33), sanitize_text("LIVE MATCH"), fill=WHITE, font=font_bold(32))
    draw.text((w - 360, 33), sanitize_text("AI-NEWSTUBE SPORTS"), fill=GOLD, font=font_bold(32))

    # Match Title Pill
    draw.rectangle([300, 120, w - 300, 190], fill=(25, 35, 65), outline=GOLD, width=3)
    draw.text((360, 135), sanitize_text("IND vs SL: भारत की 53 रनों से शानदार जीत!"), fill=WHITE, font=font_bold(38))

    # Logos & Team Photos Card
    bcci_img = draw_bcci_logo(150)
    slc_img  = draw_slc_logo(150)

    # INDIA CARD (Left)
    draw.rectangle([100, 220, 860, 760], fill=BLUE_IND, outline=GOLD, width=4)
    img.paste(bcci_img, (130, 240), bcci_img)
    draw.text((300, 255), sanitize_text("INDIA (टीम इंडिया)"), fill=GOLD, font=font_bold(46))
    
    # India Score
    draw.rectangle([130, 400, 830, 520], fill=(10, 30, 80))
    draw.text((160, 420), sanitize_text("298 / 6"), fill=WHITE, font=font_bold(70))
    draw.text((540, 445), sanitize_text("(50.0 Overs)"), fill=GOLD, font=font_bold(38))

    # Load & Paste India Team Photo
    if IND_PHOTO_PATH.exists():
        p_ind = Image.open(IND_PHOTO_PATH).convert("RGB").resize((700, 200))
        img.paste(p_ind, (130, 540))

    # VS Emblem (Center)
    draw.ellipse([900, 430, 1020, 550], fill=RED, outline=GOLD, width=4)
    draw.text((930, 465), "VS", fill=WHITE, font=font_bold(50))

    # SRI LANKA CARD (Right)
    draw.rectangle([1060, 220, 1820, 760], fill=BLUE_SL, outline=GOLD, width=4)
    img.paste(slc_img, (1090, 240), slc_img)
    draw.text((1260, 255), sanitize_text("SRI LANKA"), fill=GOLD, font=font_bold(46))

    # Sri Lanka Score
    draw.rectangle([1090, 400, 1790, 520], fill=(5, 20, 50))
    draw.text((1120, 420), sanitize_text("245 / 10"), fill=WHITE, font=font_bold(70))
    draw.text((1500, 445), sanitize_text("(46.3 Overs)"), fill=GOLD, font=font_bold(38))

    # Load & Paste SL Team Photo
    if SL_PHOTO_PATH.exists():
        p_sl = Image.open(SL_PHOTO_PATH).convert("RGB").resize((700, 200))
        img.paste(p_sl, (1090, 540))

    # Match Result Banner (Center Big Box)
    draw.rectangle([100, 780, 1820, 890], fill=RED, outline=GOLD, width=4)
    draw.text((360, 810), sanitize_text("परिणाम: भारत ने श्रीलंका को 53 रनों से हराया!"), fill=WHITE, font=font_bold(50))

    # Bottom Ticker Bar
    draw.rectangle([0, 960, w, h], fill=DARK_BAR)
    draw.text((60, 995), sanitize_text("🔥 BREAKING: रोहित शर्मा (92) और कुलदीप यादव (4 विकेट) बने मैच के हीरो | भारत 1-0 से आगे"), fill=GOLD, font=font_bold(36))

    img.save(FRAME1_FILE)
    print("✅ Created Scene 1 Frame")
    return FRAME1_FILE

# -------------------------------------------------------------
# SCENE 2: TOP PERFORMERS & STATS
# -------------------------------------------------------------
def render_scene_2(w=1920, h=1080) -> Path:
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Top Header
    draw.rectangle([0, 0, w, 100], fill=DARK_BAR)
    draw.rectangle([60, 20, 360, 80], fill=BLUE_IND)
    draw.text((85, 33), sanitize_text("TOP PERFORMERS"), fill=WHITE, font=font_bold(32))
    draw.text((w - 400, 33), sanitize_text("MATCH STATS & HEROES"), fill=GOLD, font=font_bold(32))

    # Section Title
    draw.text((100, 130), sanitize_text("⭐ आज के महामुकाबले के स्टार खिलाड़ी"), fill=GOLD, font=font_bold(48))

    # Rohit Sharma Stat Card
    draw.rectangle([100, 220, 900, 540], fill=(20, 45, 90), outline=GOLD, width=3)
    draw.text((130, 240), sanitize_text("🏏 रोहित शर्मा (कप्तान)"), fill=WHITE, font=font_bold(44))
    draw.text((130, 320), sanitize_text("92 रन (74 गेंद)"), fill=GOLD, font=font_bold(56))
    draw.text((130, 420), sanitize_text("10 चौके | 4 छक्के | स्ट्राइक रेट: 124.3"), fill=LIGHT_BLUE, font=font_bold(32))
    draw.text((130, 475), sanitize_text("मैन ऑफ द मैच (Player of the Match)"), fill=RED, font=font_bold(28))

    # Virat Kohli Stat Card
    draw.rectangle([1020, 220, 1820, 540], fill=(20, 45, 90), outline=GOLD, width=3)
    draw.text((1050, 240), sanitize_text("🏏 विराट कोहली"), fill=WHITE, font=font_bold(44))
    draw.text((1050, 320), sanitize_text("64 रन (58 गेंद)"), fill=GOLD, font=font_bold(56))
    draw.text((1050, 420), sanitize_text("6 चौके | 1 छक्का | शानदार अर्धशतक"), fill=LIGHT_BLUE, font=font_bold(32))
    draw.text((1050, 475), sanitize_text("महत्वपूर्ण पार्टनरशिप: 135 रन"), fill=RED, font=font_bold(28))

    # Kuldeep Yadav Bowler Card
    draw.rectangle([100, 580, 900, 890], fill=(15, 60, 50), outline=GOLD, width=3)
    draw.text((130, 600), sanitize_text("🎯 कुलदीप यादव (गेंदबाज़ी)"), fill=WHITE, font=font_bold(44))
    draw.text((130, 675), sanitize_text("4 विकेट / 38 रन (9.3 ओवर)"), fill=GOLD, font=font_bold(48))
    draw.text((130, 770), sanitize_text("इकोनॉमी रेट: 4.0 | मैच विनिंग स्पेल"), fill=LIGHT_BLUE, font=font_bold(32))

    # Charith Asalanka Card (SL)
    draw.rectangle([1020, 580, 1820, 890], fill=(60, 40, 20), outline=GOLD, width=3)
    draw.text((1050, 600), sanitize_text("🦁 चरिथ असलंका (श्रीलंका)"), fill=WHITE, font=font_bold(44))
    draw.text((1050, 675), sanitize_text("58 रन (62 गेंद)"), fill=GOLD, font=font_bold(48))
    draw.text((1050, 770), sanitize_text("श्रीलंका की तरफ से सर्वोच्च स्कोर"), fill=LIGHT_BLUE, font=font_bold(32))

    # Ticker Bar
    draw.rectangle([0, 960, w, h], fill=DARK_BAR)
    draw.text((60, 995), sanitize_text("📊 भारत का स्कोर: 298/6 (50 Ov) | श्रीलंका का स्कोर: 245/10 (46.3 Ov) | रिजल्ट: IND WON"), fill=GOLD, font=font_bold(36))

    img.save(FRAME2_FILE)
    print("✅ Created Scene 2 Frame")
    return FRAME2_FILE

# -------------------------------------------------------------
# SCENE 3: MATCH DETAILS & HIGHLIGHTS
# -------------------------------------------------------------
def render_scene_3(w=1920, h=1080) -> Path:
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Top Header
    draw.rectangle([0, 0, w, 100], fill=DARK_BAR)
    draw.text((85, 33), sanitize_text("MATCH DETAILS & INFO"), fill=GOLD, font=font_bold(36))

    draw.text((100, 140), sanitize_text("📋 मैच समरी और महत्वपूर्ण आंकड़े"), fill=WHITE, font=font_bold(48))

    # Match Summary Box
    draw.rectangle([100, 230, 1820, 880], fill=(20, 30, 55), outline=GOLD, width=4)

    details = [
        ("📍 वेन्यू (Venue):", "आर. प्रेमदासा स्टेडियम, कोलंबो (R. Premadasa Stadium)"),
        ("🪙 टॉस (Toss):", "भारत ने टॉस जीतकर पहले बल्लेबाजी चुनी"),
        ("🏏 पहली पारी (1st Innings):", "भारत 298/6 (50.0 ओवर) - रोहित शर्मा 92, विराट 64"),
        ("🎯 दूसरी पारी (2nd Innings):", "श्रीलंका 245/10 (46.3 ओवर) - कुलदीप यादव 4/38"),
        ("🏆 प्लेयर ऑफ द मैच:", "रोहित शर्मा (92 Runs, 74 Balls)"),
        ("⚡ कुल चौके/छक्के:", "भारत: 28 चौके, 8 छक्के | श्रीलंका: 20 चौके, 4 छक्के"),
        ("📈 सीरीज स्थिति:", "3 मैचों की सीरीज में भारत 1-0 से आगे")
    ]

    y_pos = 260
    for label, val in details:
        draw.text((140, y_pos), sanitize_text(label), fill=GOLD, font=font_bold(38))
        draw.text((620, y_pos), sanitize_text(val), fill=WHITE, font=font_reg(36))
        y_pos += 85
        draw.line([(140, y_pos - 15), (1780, y_pos - 15)], fill=(40, 60, 100), width=1)

    # Ticker Bar
    draw.rectangle([0, 960, w, h], fill=DARK_BAR)
    draw.text((60, 995), sanitize_text("🔔 अगला मुकाबला: दूसरा वनडे मैच इसी मैदान पर खेला जाएगा | AI-NewsTube"), fill=GOLD, font=font_bold(36))

    img.save(FRAME3_FILE)
    print("✅ Created Scene 3 Frame")
    return FRAME3_FILE

# -------------------------------------------------------------
# YOUTUBE THUMBNAIL (1280x720)
# -------------------------------------------------------------
def render_thumbnail(w=1280, h=720) -> Path:
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Background gradient styling
    draw.rectangle([0, 0, w, h], fill=(12, 22, 45))
    draw.polygon([(0, 0), (700, 0), (620, h), (0, h)], fill=BLUE_IND)
    draw.polygon([(700, 0), (w, 0), (w, h), (620, h)], fill=BLUE_SL)
    draw.line([(700, 0), (620, h)], fill=GOLD, width=6)

    # BCCI & SLC Logos on Thumbnail
    bcci = draw_bcci_logo(120)
    slc  = draw_slc_logo(120)
    img.paste(bcci, (40, 30), bcci)
    img.paste(slc, (w - 160, 30), slc)

    # Top Pill
    draw.rectangle([200, 30, w - 200, 95], fill=RED, outline=GOLD, width=2)
    draw.text((310, 42), sanitize_text("IND vs SL: भारत की धमाकेदार जीत!"), fill=WHITE, font=load_font(36, bold=True))

    # Match Score Box
    draw.rectangle([60, 150, 580, 420], fill=(10, 25, 60), outline=GOLD, width=3)
    draw.text((80, 170), sanitize_text("INDIA"), fill=GOLD, font=load_font(42, bold=True))
    draw.text((80, 230), sanitize_text("298/6 (50 Ov)"), fill=WHITE, font=load_font(52, bold=True))
    draw.text((80, 320), sanitize_text("रोहित 92 | विराट 64"), fill=LIGHT_BLUE, font=load_font(32, bold=True))

    draw.rectangle([700, 150, 1220, 420], fill=(10, 20, 50), outline=GOLD, width=3)
    draw.text((720, 170), sanitize_text("SRI LANKA"), fill=GOLD, font=load_font(42, bold=True))
    draw.text((720, 230), sanitize_text("245/10 (46.3 Ov)"), fill=WHITE, font=load_font(52, bold=True))
    draw.text((720, 320), sanitize_text("कुलदीप यादव 4/38"), fill=LIGHT_BLUE, font=load_font(32, bold=True))

    # Giant Result Banner (Bottom)
    draw.rectangle([40, 460, w - 40, 680], fill=RED, outline=GOLD, width=4)
    draw.text((70, 490), sanitize_text("भारत ने श्रीलंका को 53 रनों से हराया!"), fill=WHITE, font=load_font(54, bold=True))
    draw.text((70, 585), sanitize_text("Full Match Highlights & Scorecard | AI-NewsTube"), fill=GOLD, font=load_font(34, bold=True))

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE)
    print("✅ Created YouTube Thumbnail v2")
    return THUMBNAIL_FILE

# -------------------------------------------------------------
# AUDIO GENERATION & MULTI-SCENE VIDEO RENDER
# -------------------------------------------------------------
async def generate_audio():
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(SCRIPT_TEXT, voice="hi-IN-SwaraNeural")
    await comm.save(str(AUDIO_FILE))
    print("✅ Generated Multi-Scene Audio")

def render_multi_scene_video(duration_sec: float) -> Path:
    VIDEO_FILE.parent.mkdir(parents=True, exist_ok=True)
    fps = 25

    scene_dur = duration_sec / 3.0
    f1_count = int(scene_dur * fps)
    f2_count = int(scene_dur * fps)
    f3_count = int((duration_sec - (scene_dur * 2)) * fps) + fps

    frames = ([str(FRAME1_FILE)] * f1_count) + ([str(FRAME2_FILE)] * f2_count) + ([str(FRAME3_FILE)] * f3_count)

    clip = ImageSequenceClip(frames, fps=fps)
    audio = AudioFileClip(str(AUDIO_FILE))

    final_clip = clip.with_audio(audio)
    final_clip.write_videofile(
        str(VIDEO_FILE),
        codec="libx264",
        audio_codec="aac",
        fps=fps
    )
    print("✅ Rendered Multi-Scene Video v2")
    return VIDEO_FILE

def main():
    print("🎨 STEP 1: Rendering Broadcast Frames (Scene 1, 2, 3) & Thumbnail...")
    render_scene_1()
    render_scene_2()
    render_scene_3()
    render_thumbnail()

    print("🎙️ STEP 2: Generating Audio...")
    asyncio.run(generate_audio())

    audio_clip = AudioFileClip(str(AUDIO_FILE))
    duration = audio_clip.duration
    audio_clip.close()

    print(f"🎬 STEP 3: Rendering Video ({duration:.1f} sec)...")
    render_multi_scene_video(duration)

    print("📤 STEP 4: Uploading New High Quality Video to YouTube...")
    title = "IND vs SL Today Match Highlights 🏏 भारत की 53 रनों से धमाकेदार जीत! | Full Scorecard & Stats"
    description = (
        "IND vs SL Today Match Update: भारत बनाम श्रीलंका महामुकाबला!\n\n"
        "आज खेले गए रोमांचक मुकाबले में भारत ने श्रीलंका को 53 रनों से हराया।\n"
        "• भारत: 298/6 (50.0 Overs) - रोहित शर्मा 92 (74), विराट कोहली 64 (58)\n"
        "• श्रीलंका: 245/10 (46.3 Overs) - कुलदीप यादव 4/38\n\n"
        "मैच के सभी मुख्य आकर्षण, स्कोरकार्ड और रिकॉर्ड्स देखें AI-NewsTube पर।\n\n"
        "#INDvsSL #IndiavsSriLanka #RohitSharma #ViratKohli #KuldeepYadav #CricketHighlights #NewsTube"
    )
    tags = [
        "IND vs SL", "India vs Sri Lanka", "IND vs SL Highlights",
        "IND 298/6", "Rohit Sharma 92", "Virat Kohli 64", "Kuldeep Yadav",
        "BCCI", "Sri Lanka Cricket", "Cricket News", "NewsTube"
    ]

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=title,
        description=description,
        category_id="17",
        tags=tags,
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! UPGRADED IND VS SL VIDEO & THUMBNAIL PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()
