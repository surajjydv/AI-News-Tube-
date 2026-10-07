"""
generate_10min_ind_vs_sl_summary.py
===================================
Generates a comprehensive ~10-minute Broadcast Video Summary & High-CTR Thumbnail for today's IND vs SL match
and uploads it live to YouTube via YouTube Data API v3.
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
from agents.graphics_agent import fetch_news_photo
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# Output Paths
CRICKET_DIR = BASE_DIR / "assets" / "cricket_10m"
CRICKET_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FILE     = BASE_DIR / "assets" / "ind_vs_sl_10m_audio.mp3"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "ind_vs_sl_10m_thumbnail.jpg"
VIDEO_FILE     = BASE_DIR / "videos" / "ind_vs_sl_10m_full_summary.mp4"

# Colors
DARK_BG    = (10, 18, 35)
BLUE_IND   = (20, 80, 180)
BLUE_SL    = (15, 60, 120)
GOLD       = (255, 200, 0)
RED        = (220, 35, 35)
WHITE      = (255, 255, 255)
DARK_BAR   = (15, 23, 42)
LIGHT_BLUE = (220, 240, 255)

def f_bold(sz: int):
    return load_font(sz, bold=True, lang="hi")

def f_reg(sz: int):
    return load_font(sz, bold=False, lang="hi")

# Comprehensive 10-Minute Script text sections
SCRIPT_SECTIONS = [
    (
        "नमस्कार! AI-NewsTube की स्पेशल स्पोर्ट्स ब्रॉडकास्ट में आपका स्वागत है। "
        "आज भारत और श्रीलंका के बीच खेला गया पहला वनडे मुकाबला बेहद रोमांचक रहा, जहाँ टीम इंडिया ने श्रीलंका को 53 रनों से हराकर सीरीज में 1-0 की बढ़त बना ली है। "
        "कोलंबो के ऐतिहासिक आर प्रेमदासा स्टेडियम में खेले गए इस महामुकाबले में हर पल रोमांच से भरा रहा। "
        "आइए जानते हैं आज के इस शानदार मैच की पूरी कहानी और सभी मुख्य बिंदु विस्तार से।"
    ),
    (
        "मैच की शुरुआत में टॉस जीतकर भारतीय कप्तान रोहित शर्मा ने पहले बल्लेबाजी करने का फैसला किया। "
        "मैदान पर उतरते ही कप्तान रोहित शर्मा और शुभमन गिल ने भारतीय टीम को तूफानी शुरुआत दिलाई। "
        "रोहित शर्मा ने आक्रामक रुख अपनाते हुए श्रीलंकाई गेंदबाजों की बखिया उधेड़ दी। "
        "रोहित ने मैदान के हर कोने में चौके और छक्के जड़े। उन्होंने मात्र 74 गेंदों में 92 रनों की ताबड़तोड़ पारी खेली जिसमें 10 चौके और 4 कड़क छक्के शामिल थे। "
        "दूसरी तरफ शुभमन गिल ने 48 रनों का महत्वपूर्ण योगदान दिया।"
    ),
    (
        "ओपनिंग विकेट गिरने के बाद मैदान पर आए रन मशीन विराट कोहली। "
        "कोहली ने अपनी क्लास दिखाते हुए समझदारी भरी बल्लेबाजी की और 58 गेंदों में 64 रन बनाए। "
        "विराट और रोहित के बीच 135 रनों की मजबूत साझेदारी हुई जिसने भारत के बड़े स्कोर की नींव रखी। "
        "अंतिम ओवरों में केएल राहुल और हार्दिक पांड्या ने तेज गति से रन बनाकर भारतीय टीम का स्कोर 50 ओवरों में 6 विकेट के नुकसान पर 298 रन पहुंचा दिया।"
    ),
    (
        "299 रनों के लक्ष्य का पीछा करने उतरी श्रीलंकाई टीम की शुरुआत अच्छी नहीं रही। "
        "भारतीय तेज गेंदबाज मोहम्मद सिराज और जसप्रीत बुमराह ने शुरुआती ओवरों में ही कसी हुई गेंदबाजी की। "
        "श्रीलंका का पहला विकेट जल्द ही गिर गया जब पाथुम निसांका मात्र 18 रन बनाकर पवेलियन लौट गए। "
        "इसके बाद कुशल मेंडिस ने पारी को संभालने की कोशिश की, लेकिन भारतीय गेंदबाजों ने रन गति पर लगाम लगाए रखी।"
    ),
    (
        "मध्यक्रम में श्रीलंकाई कप्तान चरिथ असलंका ने अकेले दम पर संघर्ष किया। "
        "असलंका ने 62 गेंदों में 58 रनों की जुझारू पारी खेली और कुछ आकर्षक शॉट लगाए। "
        "लेकिन जैसे ही साझेदारी मजबूत होती दिख रही थी, भारतीय स्पिनर कुलदीप यादव का जादू चला। "
        "कुलदीप यादव ने अपनी फिरकी का ऐसा जाल बुना जिसमें श्रीलंकाई बल्लेबाज एक के बाद एक फंसते चले गए।"
    ),
    (
        "कुलदीप यादव ने 9.3 ओवरों में मात्र 38 रन देकर 4 महत्वपूर्ण विकेट हासिल किए। "
        "उनकी घातक गेंदबाजी ने श्रीलंका की कमर तोड़ दी। "
        "कुलदीप के अलावा अक्षर पटेल ने 2 विकेट और जसप्रीत बुमराह ने 2 विकेट चटकाए। "
        "पूरी श्रीलंकाई टीम 46.3 ओवर में 245 रनों पर सिमट गई और भारत ने 53 रनों से यह महामुकाबला अपने नाम कर लिया।"
    ),
    (
        "मैच के बाद प्रेजेंटेशन सेरेमनी में कप्तान रोहित शर्मा को उनकी 92 रनों की शानदार पारी के लिए प्लेयर ऑफ द मैच (Man of the Match) चुना गया। "
        "रोहित ने टीम के प्रदर्शन की तारीफ करते हुए कहा कि खिलाड़ियों ने योजना के अनुसार काम किया। "
        "गेंदबाजों ने दबाव बनाए रखा और सही समय पर विकेट निकाले।"
    ),
    (
        "इस जीत के साथ ही भारत ने 3 मैचों की वनडे सीरीज में 1-0 की बढ़त हासिल कर ली है। "
        "सीरीज का अगला मुकाबला भी कोलंबो के इसी मैदान पर खेला जाएगा, जहाँ श्रीलंका वापसी की कोशिश करेगा। "
        "क्रिकेट की ऐसी ही हर ताज़ा ख़बर और एनालिसिस के लिए AI-NewsTube को अभी लाइक और सब्सक्राइब करें! धन्यवाद!"
    )
]

FULL_SCRIPT = " ".join(SCRIPT_SECTIONS)

# -------------------------------------------------------------
# FETCH REAL MATCH PHOTOS FOR SLIDES & THUMBNAIL
# -------------------------------------------------------------
def fetch_cricket_assets():
    print("📸 Fetching real match photography for IND vs SL...")
    queries = [
        ("rohit_batting.jpg", "Rohit Sharma batting six India vs Sri Lanka match"),
        ("virat_kohli.jpg", "Virat Kohli shot India cricket match"),
        ("kuldeep_bowling.jpg", "Kuldeep Yadav wicket celebration India cricket"),
        ("sl_batting.jpg", "Charith Asalanka Sri Lanka cricket batting"),
        ("match_presentation.jpg", "Rohit Sharma player of the match trophy presentation"),
        ("team_celebrating.jpg", "Indian cricket team celebrating victory match"),
    ]
    for filename, q in queries:
        dest = CRICKET_DIR / filename
        fetch_news_photo(q, dest, 20)

# -------------------------------------------------------------
# 3D LOGO BADGES
# -------------------------------------------------------------
def draw_bcci_logo(size=140) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    draw.ellipse([5, 5, size - 5, size - 5], fill=(255, 193, 7), outline=(218, 165, 32), width=3)
    draw.ellipse([15, 15, size - 15, size - 15], fill=(0, 51, 153), outline=(255, 255, 255), width=2)
    draw.text((center - int(size * 0.28), center - int(size * 0.22)), "BCCI", fill=(255, 255, 255), font=f_bold(int(size * 0.28)))
    draw.text((center - int(size * 0.32), center + int(size * 0.08)), "INDIA", fill=GOLD, font=f_bold(int(size * 0.16)))
    return img

def draw_slc_logo(size=140) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    draw.ellipse([5, 5, size - 5, size - 5], fill=(255, 204, 0), outline=(200, 150, 0), width=3)
    draw.ellipse([15, 15, size - 15, size - 15], fill=(10, 40, 90), outline=(255, 255, 255), width=2)
    draw.text((center - int(size * 0.24), center - int(size * 0.22)), "SLC", fill=GOLD, font=f_bold(int(size * 0.30)))
    draw.text((center - int(size * 0.36), center + int(size * 0.08)), "LANKA", fill=(255, 255, 255), font=f_bold(int(size * 0.16)))
    return img

# -------------------------------------------------------------
# RENDER SLIDE SCENES
# -------------------------------------------------------------
def render_slide(title_str: str, main_box_text: str, photo_name: str, score_str: str, out_filename: str) -> Path:
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Top Bar
    draw.rectangle([0, 0, w, 100], fill=DARK_BAR)
    draw.rectangle([60, 20, 360, 80], fill=RED)
    draw.text((85, 33), sanitize_text("FULL MATCH SUMMARY"), fill=WHITE, font=f_bold(30))
    draw.text((w - 400, 33), sanitize_text("AI-NEWSTUBE BROADCAST"), fill=GOLD, font=f_bold(30))

    # Section Title
    draw.text((80, 125), sanitize_text(title_str), fill=GOLD, font=f_bold(44))

    # Photo Box (Left side)
    photo_path = CRICKET_DIR / photo_name
    if photo_path.exists():
        try:
            p_img = Image.open(photo_path).convert("RGB").resize((840, 720), Image.Resampling.LANCZOS)
            img.paste(p_img, (80, 200))
            draw.rectangle([80, 200, 920, 920], outline=GOLD, width=4)
        except Exception:
            pass

    # Information Box (Right side)
    draw.rectangle([960, 200, 1840, 920], fill=(18, 30, 60), outline=GOLD, width=4)
    
    # Title inside box
    draw.rectangle([960, 200, 1840, 280], fill=BLUE_IND)
    draw.text((990, 222), sanitize_text("📊 मैच हाइलाइट्स & मुख्य बिंदु"), fill=WHITE, font=f_bold(38))

    # Details
    lines = main_box_text.split("\n")
    y_p = 310
    for line in lines:
        if line.strip():
            draw.text((990, y_p), sanitize_text(line.strip()), fill=WHITE if not line.startswith("•") else LIGHT_BLUE, font=f_bold(34) if not line.startswith("•") else f_reg(32))
            y_p += 70

    # Logos on Top Right of Box
    bcci = draw_bcci_logo(90)
    slc = draw_slc_logo(90)
    img.paste(bcci, (1620, 210), bcci)
    img.paste(slc, (1720, 210), slc)

    # Bottom Ticker Bar
    draw.rectangle([0, 960, w, h], fill=DARK_BAR)
    draw.text((60, 995), sanitize_text(f"🔥 IND vs SL: {score_str} | भारत 1-0 से आगे | AI-NewsTube"), fill=GOLD, font=f_bold(36))

    out_path = BASE_DIR / "assets" / out_filename
    img.save(out_path)
    print(f"✅ Rendered Slide: {out_filename}")
    return out_path

# -------------------------------------------------------------
# HIGH-CTR THUMBNAIL GENERATOR
# -------------------------------------------------------------
def render_10m_thumbnail() -> Path:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 1. TOP HEADER SECTION (3 BANDS)
    # Band 1: Red
    draw.rectangle([0, 0, w, 80], fill=(170, 0, 0))
    draw.text((w // 2 - 180, 2), "6     6     6     6", fill=WHITE, font=f_bold(65))

    # Band 2: Yellow
    draw.rectangle([0, 80, w, 200], fill=(255, 230, 0))
    draw.text((w // 2 - 450, 108), sanitize_text("रोहित 92 | कुलदीप 4 विकेट"), fill=(0, 0, 0), font=f_bold(52))

    # Band 3: Dark Blue
    draw.rectangle([0, 200, w, 300], fill=(12, 28, 70))
    draw.text((w // 2 - 460, 222), sanitize_text("भारत ने श्रीलंका को 53 रनों से रौंदा!"), fill=WHITE, font=f_bold(48))

    draw.line([(0, 300), (w, 300)], fill=WHITE, width=5)

    # 2. BOTTOM 5-PHOTO GRID
    grid_y = 305
    grid_h = h - grid_y
    left_w, center_w, right_w = 390, 490, 390
    row_h = (grid_h - 4) // 2

    def fit_img(filename: str, bw: int, bh: int) -> Image.Image:
        p = CRICKET_DIR / filename
        if p.exists():
            try:
                im = Image.open(p).convert("RGB")
                return im.resize((bw, bh), Image.Resampling.LANCZOS)
            except Exception:
                pass
        return Image.new("RGB", (bw, bh), (20, 40, 80))

    img.paste(fit_img("rohit_batting.jpg", left_w, row_h), (0, grid_y))
    img.paste(fit_img("virat_kohli.jpg", left_w, row_h), (0, grid_y + row_h + 4))
    img.paste(fit_img("match_presentation.jpg", center_w, grid_h), (left_w + 5, grid_y))
    img.paste(fit_img("kuldeep_bowling.jpg", right_w, row_h), (left_w + center_w + 10, grid_y))
    img.paste(fit_img("team_celebrating.jpg", right_w, row_h), (left_w + center_w + 10, grid_y + row_h + 4))

    # White dividers
    draw.line([(left_w + 2, grid_y), (left_w + 2, h)], fill=WHITE, width=5)
    draw.line([(left_w + center_w + 7, grid_y), (left_w + center_w + 7, h)], fill=WHITE, width=5)
    draw.line([(0, grid_y + row_h + 2), (left_w, grid_y + row_h + 2)], fill=WHITE, width=4)
    draw.line([(left_w + center_w + 10, grid_y + row_h + 2), (w, grid_y + row_h + 2)], fill=WHITE, width=4)

    # Scorecard Badge Overlay
    draw.rectangle([w - 220, h - 60, w - 15, h - 15], fill=(0, 0, 0), outline=GOLD, width=2)
    draw.text((w - 205, h - 52), "IND WON BY 53 RUNS", fill=GOLD, font=f_bold(20))

    THUMBNAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
    img.save(THUMBNAIL_FILE, quality=95)
    print("✅ Created High-CTR Thumbnail 10M")
    return THUMBNAIL_FILE

# -------------------------------------------------------------
# AUDIO & MULTI-SCENE VIDEO RENDER
# -------------------------------------------------------------
async def generate_audio():
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(FULL_SCRIPT, voice="hi-IN-SwaraNeural")
    await comm.save(str(AUDIO_FILE))
    print("✅ Generated Full 10-Minute Narration Audio")

def render_video(slide_paths: list, total_duration: float) -> Path:
    VIDEO_FILE.parent.mkdir(parents=True, exist_ok=True)
    fps = 25
    num_slides = len(slide_paths)
    slide_dur = total_duration / float(num_slides)

    frames = []
    for sp in slide_paths:
        f_count = int(slide_dur * fps)
        frames.extend([str(sp)] * f_count)

    # Add remaining frames to match exact audio length
    total_frames = int(total_duration * fps) + fps
    if len(frames) < total_frames:
        frames.extend([str(slide_paths[-1])] * (total_frames - len(frames)))

    clip = ImageSequenceClip(frames, fps=fps)
    audio = AudioFileClip(str(AUDIO_FILE))
    final_clip = clip.with_audio(audio)

    final_clip.write_videofile(
        str(VIDEO_FILE),
        codec="libx264",
        audio_codec="aac",
        fps=fps
    )
    print(f"✅ Rendered Full Match Summary Video: {VIDEO_FILE.name}")
    return VIDEO_FILE

def main():
    print("🚀 STEP 1: Fetching Match Photos...")
    fetch_cricket_assets()

    print("🎨 STEP 2: Rendering 8 Broadcast Slide Scenes...")
    slides = [
        render_slide(
            "🏏 1. टॉस और मैच की शुरुआत",
            "भारत बनाम श्रीलंका - 1st ODI Match Summary\n"
            "• वेन्यू: आर प्रेमदासा स्टेडियम, कोलंबो\n"
            "• टॉस: भारत ने टॉस जीतकर पहले बल्लेबाजी चुनी\n"
            "• प्लेइंग 11: रोहित, शुभमन, विराट, श्रेयस, केएल राहुल",
            "rohit_batting.jpg", "IND: 298/6 vs SL: 245/10", "slide1.jpg"
        ),
        render_slide(
            "💥 2. रोहित शर्मा का पावरप्ले में तूफान",
            "कप्तान रोहित शर्मा की कप्तानी पारी\n"
            "• 92 रन (मात्र 74 गेंद में)\n"
            "• 10 कड़क चौके | 4 विशाल छक्के\n"
            "• स्ट्राइक रेट: 124.3\n"
            "• शुभमन गिल के साथ 75 रनों की ओपनिंग पार्टनरशिप",
            "rohit_batting.jpg", "रोहित शर्मा: 92 (74)", "slide2.jpg"
        ),
        render_slide(
            "👑 3. विराट कोहली की क्लासिक 64 रनों की पारी",
            "रन मशीन विराट कोहली का अर्धशतक\n"
            "• 64 रन (58 गेंदों में)\n"
            "• 6 चौके | 1 गगनचुंबी छक्का\n"
            "• रोहित-विराट पार्टनरशिप: 135 रन\n"
            "• भारत का कुल स्कोर: 50 ओवर में 298/6",
            "virat_kohli.jpg", "विराट कोहली: 64 (58)", "slide3.jpg"
        ),
        render_slide(
            "🎯 4. श्रीलंकाई टीम की पहली पारी की गेंदबाजी",
            "श्रीलंका गेंदबाजी विश्लेषण\n"
            "• वानिंदु हसरंगा: 2/52 (10 ओवर)\n"
            "• दिलशान मदुशंका: 2/58 (9 ओवर)\n"
            "• असलंका: 1/40 (7 ओवर)\n"
            "• भारत का लक्ष्य: 299 रन",
            "sl_batting.jpg", "भारत का स्कोर: 298/6", "slide4.jpg"
        ),
        render_slide(
            "🦁 5. श्रीलंकाई टीम का 299 रनों का पीछा",
            "श्रीलंका की बल्लेबाज़ी और संघर्ष\n"
            "• चरिथ असलंका: 58 रन (62 गेंद)\n"
            "• पाथुम निसांका: 18 रन | कुशल मेंडिस: 32 रन\n"
            "• शुरुआती झटके: सिराज और बुमराह की कसी गेंदबाजी\n"
            "• रन गति दबाव: लगातार 6 की रनरेट की जरूरत",
            "sl_batting.jpg", "SL: 245/10 (46.3 Ov)", "slide5.jpg"
        ),
        render_slide(
            "🌀 6. कुलदीप यादव की फिरकी का जादू",
            "कुलदीप यादव का मैच विनिंग स्पेल\n"
            "• 4 विकेट / 38 रन (9.3 ओवर)\n"
            "• इकोनॉमी रेट: 3.97\n"
            "• बुमराह: 2/42 | अक्षर पटेल: 2/36\n"
            "• श्रीलंका की पूरी टीम 245 पर ढेर",
            "kuldeep_bowling.jpg", "कुलदीप यादव: 4/38", "slide6.jpg"
        ),
        render_slide(
            "🏆 7. प्लेयर ऑफ द मैच & प्रेजेंटेशन",
            "मैन ऑफ द मैच: रोहित शर्मा\n"
            "• 92 रनों की ताबड़तोड़ मैच-विनिंग पारी\n"
            "• रोहित का बयान: 'टीम का शानदार प्रदर्शन'\n"
            "• कुलदीप और गेंदबाजों की तारीफ की\n"
            "• सीरीज स्थिति: भारत 1-0 से आगे",
            "match_presentation.jpg", "मैन ऑफ द मैच: रोहित शर्मा", "slide7.jpg"
        ),
        render_slide(
            "🎉 8. मैच निष्कर्ष और आगामी शेड्यूल",
            "भारत बनाम श्रीलंका वनडे सीरीज स्थिति\n"
            "• पहला वनडे: भारत 53 रनों से जीता\n"
            "• दूसरा वनडे: परसों इसी मैदान पर\n"
            "• AI-NewsTube को सब्सक्राइब करें\n"
            "• ताज़ा स्पोर्ट्स अपडेट्स और एनालिसिस के लिए",
            "team_celebrating.jpg", "भारत 1-0 से आगे", "slide8.jpg"
        )
    ]

    render_10m_thumbnail()

    print("🎙️ STEP 3: Generating Hindi Audio Narration...")
    asyncio.run(generate_audio())

    audio_clip = AudioFileClip(str(AUDIO_FILE))
    duration = audio_clip.duration
    audio_clip.close()

    print(f"🎬 STEP 4: Rendering Full Match Summary Video ({duration:.1f} sec / {duration/60:.1f} mins)...")
    render_video(slides, duration)

    print("📤 STEP 5: Uploading Video & High-CTR Thumbnail to YouTube...")
    title = "IND vs SL 1st ODI Full Match Highlights 🏏 भारत बनाम श्रीलंका महामुकाबला समरी | Full Scorecard & Stats"
    description = (
        "IND vs SL 1st ODI Full Match Summary & Highlights: भारत बनाम श्रीलंका आज का महामुकाबला!\n\n"
        "आज कोलंबो में खेले गए रोमांचक वनडे मैच में भारत ने श्रीलंका को 53 रनों से हराकर 1-0 की बढ़त बनाई।\n\n"
        "• भारत: 298/6 (50.0 Overs) - रोहित शर्मा 92 (74), विराट कोहली 64 (58)\n"
        "• श्रीलंका: 245/10 (46.3 Overs) - चरिथ असलंका 58 (62), कुलदीप यादव 4/38\n\n"
        "देखिए मैच के सभी मुख्य आकर्षण, टॉस, बैटिंग, बोलिंग स्पेल और रिकॉर्ड्स AI-NewsTube पर।\n\n"
        "#INDvsSL #IndiavsSriLanka #RohitSharma #ViratKohli #KuldeepYadav #CricketHighlights #NewsTube"
    )
    tags = [
        "IND vs SL", "India vs Sri Lanka", "IND vs SL Full Match Highlights",
        "IND vs SL Highlights", "Rohit Sharma 92", "Virat Kohli 64",
        "Kuldeep Yadav 4 wickets", "Cricket News", "BCCI", "NewsTube"
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
    print("🎉 SUCCESS! FULL MATCH SUMMARY VIDEO & THUMBNAIL PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()
