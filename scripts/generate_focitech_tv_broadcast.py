"""
scripts/generate_focitech_tv_broadcast.py
=========================================
Generates a full TV Broadcast News Bulletin video for the Foci Tech Internship Program.
- Spoken Audio: Pronounced as "Foki Tech"
- Written Visual Text: Displayed as "Foci Tech"
- Full News Broadcast UI: 2.5D Glassmorphic Cards, 48px Devanagari/Hindi TV Headline Banner, Ticker & IST Weather Clock.
"""

import os
import sys
import asyncio
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from config.settings import VIDEOS_DIR, ASSETS_DIR, CHANNEL_NAME
from agents.graphics_agent import render_tv_broadcast_frame, fetch_news_photo

OUTPUT_VIDEO = VIDEOS_DIR / "focitech_tv_broadcast_bulletin.mp4"
AUDIO_PATH = VIDEOS_DIR / "focitech_tv_voice.mp3"

# Written text uses exact spelling 'Foci Tech'
# Voiceover script uses phonetic spelling 'Foki Tech' so Edge-TTS pronounces it as 'Foki Tech'!
SPOKEN_SCRIPT = (
    "Welcome to NewsTube Special Career Broadcast! Today we highlight the Foki Tech Internship Program — designed to bridge the gap between academic learning and real-world industry requirements. "
    "Unlike traditional college internships that focus mostly on theory, Foki Tech emphasizes practical skills, live assignments, and direct mentorship from industry professionals. "
    "Through its association with MaidX India, an on-demand services platform, interns gain firsthand exposure to real software development, business workflows, and hands-on problem solving. "
    "Upon successful completion, students receive a professionally verified Foki Tech Internship Certificate to strengthen their portfolio and placement opportunities. "
    "Plus, eligible candidates can earn a program refund after passing the final assessment! "
    "Prepare for your professional tech career with Foki Tech. Apply online today at focitech.in!"
)

HEADLINE_TEXT = "Foci Tech Internship Program: Learn Real-World Industry Skills & Practical Tech"
CATEGORY_TEXT = "EXCLUSIVE CAREER"

TICKERS = [
    "FOCI TECH INTERNSHIP: Apply online at focitech.in for real-world tech exposure",
    "PRACTICAL TRAINING: Learn software development, business workflows & live problem solving",
    "CERTIFICATE & CAREER: Recognized internship certificate for placements & higher education",
    "MAIDX INDIA PARTNERSHIP: Hands-on experience with customized on-demand service platform"
]


async def generate_voiceover():
    import edge_tts
    print("[VOICE] Generating TV anchor voiceover with 'Foki Tech' pronunciation...")
    communicator = edge_tts.Communicate(SPOKEN_SCRIPT, voice="en-IN-NeerjaNeural")
    await communicator.save(str(AUDIO_PATH))
    print(f"[VOICE] ✅ Voiceover saved to {AUDIO_PATH}")


def fetch_focitech_photos():
    photos = []
    # 3 High-Impact Technical Photos:
    # 1. College students working on laptops (coding & teamwork, NO BOOKS)
    # 2. Software developer / engineer coding on laptop
    # 3. Modern high-tech corporate office / Google style tech company workplace
    technical_photo_urls = [
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1280&h=720&fit=crop", # College students on laptops
        "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=1280&h=720&fit=crop", # Software developer coding
        "https://images.unsplash.com/photo-1573164713988-8665fc963095?w=1280&h=720&fit=crop"  # Modern tech company office
    ]
    
    import requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-NewsTube/2.0"}
    
    for idx, url in enumerate(technical_photo_urls):
        p_file = ASSETS_DIR / f"focitech_technical_photo_{idx + 1}.jpg"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(p_file, "wb") as f:
                    f.write(r.content)
                photos.append(str(p_file))
                print(f"[PHOTO] ✅ Saved technical photo {idx + 1} to {p_file.name}")
        except Exception as e:
            print(f"[PHOTO WARN] Could not fetch photo {idx + 1}: {e}")
            
    # Fallback if network issue
    if not photos:
        queries = ["college students laptop coding", "software developer laptop", "google office tech company"]
        for idx, q in enumerate(queries):
            p_file = ASSETS_DIR / f"focitech_photo_{idx + 1}.jpg"
            if fetch_news_photo(q, p_file, idx):
                photos.append(str(p_file))
                
    return photos


def main():
    asyncio.run(generate_voiceover())
    
    photo_paths = fetch_focitech_photos()
    
    from moviepy import VideoClip, AudioFileClip
    audio = AudioFileClip(str(AUDIO_PATH))
    duration = audio.duration
    
    print(f"[TV BROADCAST] Voiceover duration: {duration:.2f} seconds.")
    
    def make_frame(t):
        current_photo = photo_paths[int(t / 7.0) % len(photo_paths)] if photo_paths else None
        frame_pil = render_tv_broadcast_frame(
            headline_text=HEADLINE_TEXT,
            news_photo_path=current_photo,
            global_t=t,
            category=CATEGORY_TEXT,
            ticker_headlines=TICKERS
        )
        
        # Overlay 2.5D Glassmorphic Card on RIGHT SIDE with Matching Gold Theme
        draw = ImageDraw.Draw(frame_pil)
        
        card_x, card_y, card_w, card_h = 820, 140, 420, 390
        
        # Card Shadow & Base (Matching Gold & Dark Slate)
        draw.rounded_rectangle([card_x + 4, card_y + 4, card_x + card_w + 4, card_y + card_h + 4], radius=16, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=16, fill=(15, 23, 42), outline=(245, 158, 11), width=3)
        
        # Header Badge (Matching Gold Accent)
        draw.rounded_rectangle([card_x + 15, card_y + 15, card_x + card_w - 15, card_y + 60], radius=10, fill=(245, 158, 11))
        
        try:
            font_hdr = ImageFont.truetype("arialbd.ttf", 20)
            font_bp = ImageFont.truetype("arialbd.ttf", 16)
        except Exception:
            font_hdr = ImageFont.load_default()
            font_bp = ImageFont.load_default()
            
        draw.text((card_x + 65, card_y + 26), "FOCI TECH HIGHLIGHTS", fill=(15, 23, 42), font=font_hdr)
        
        # Bullet List Items (Clean Gold Dots, No Emoji Rectangle Boxes)
        items = [
            "Practical Skills Over Theory",
            "MaidX India Ecosystem Exposure",
            "Verified Internship Certificate",
            "Eligible Assessment Refund Scheme",
            "Placements & Interview Prep"
        ]
        
        y_pos = card_y + 80
        for item in items:
            draw.rounded_rectangle([card_x + 15, y_pos, card_x + card_w - 15, y_pos + 46], radius=8, fill=(30, 41, 59), outline=(56, 189, 248), width=1)
            # Draw solid gold bullet dot
            draw.ellipse([card_x + 30, y_pos + 17, card_x + 42, y_pos + 29], fill=(245, 158, 11))
            draw.text((card_x + 52, y_pos + 13), item, fill=(241, 245, 249), font=font_bp)
            y_pos += 56
            
        return np.array(frame_pil)
        
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_audio(audio)
    
    print(f"[TV BROADCAST] Rendering 720p HD TV Broadcast MP4 to {OUTPUT_VIDEO}...")
    clip.write_videofile(
        str(OUTPUT_VIDEO),
        fps=15,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )
    print(f"[TV BROADCAST] ✅ Successfully rendered {OUTPUT_VIDEO}!")


if __name__ == "__main__":
    main()
