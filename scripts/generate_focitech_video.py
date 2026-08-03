"""
scripts/generate_focitech_video.py
===================================
Generates a professional 90-second promotional HD video for the Foci Tech Internship Program.
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

from config.settings import VIDEOS_DIR, ASSETS_DIR

OUTPUT_VIDEO = VIDEOS_DIR / "focitech_internship_program.mp4"
AUDIO_PATH = VIDEOS_DIR / "focitech_voiceover.mp3"

PROMO_SCRIPT = (
    "Welcome to the Foki Tech Internship Program — where we bridge the gap between academic learning and real-world industry requirements. "
    "Unlike traditional college internships that focus only on theory, Foki Tech emphasizes practical skills, live assignments, and direct mentorship from industry professionals. "
    "Through our association with MaidX India, an on-demand services platform, interns gain firsthand exposure to real software development, business workflows, and hands-on problem solving. "
    "Upon successful completion, you receive a professionally verified Foki Tech Internship Certificate to boost your resume, strengthen your portfolio, and accelerate your job placements. "
    "Plus, with our unique Refund and Assessment Policy, eligible candidates can earn a program refund after passing the final assessment! "
    "Don't just study technology — build your professional career with Foki Tech. Apply today at focitech.in!"
)


async def generate_voiceover():
    import edge_tts
    print("[VOICE] Generating professional voiceover using Edge-TTS...")
    communicator = edge_tts.Communicate(PROMO_SCRIPT, voice="en-IN-NeerjaNeural")
    await communicator.save(str(AUDIO_PATH))
    print(f"[VOICE] ✅ Voiceover saved to {AUDIO_PATH}")


def draw_header(draw, title_text, category_text="FOKI TECH INTERNSHIP PROGRAM"):
    # Background gradient fill
    draw.rectangle([0, 0, 1280, 720], fill=(15, 23, 42))  # Deep Slate Navy
    
    # Top banner background
    draw.rectangle([0, 0, 1280, 100], fill=(30, 41, 59))
    draw.rectangle([0, 96, 1280, 100], fill=(14, 165, 233))  # Cyan Accent line
    
    # Logo / Brand Pill
    draw.rounded_rectangle([40, 25, 320, 75], radius=10, fill=(14, 165, 233))
    
    try:
        font_brand = ImageFont.truetype("arial.ttf", 24)
        font_cat = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_brand = ImageFont.load_default()
        font_cat = ImageFont.load_default()
        
    draw.text((60, 37), "FOKI TECH", fill=(255, 255, 255), font=font_brand)
    draw.text((350, 36), category_text, fill=(226, 232, 240), font=font_cat)
    
    # Bottom ticker / URL bar
    draw.rectangle([0, 660, 1280, 720], fill=(2, 132, 199))
    try:
        font_url = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_url = ImageFont.load_default()
    draw.text((40, 673), "🌐 VISIT OFFICIAL WEBSITE: https://focitech.in/   |   BUILD JOB-READY SKILLS TODAY", fill=(255, 255, 255), font=font_url)


def render_slide_frame(t, duration):
    # Determine slide index based on time
    # Total duration ~ 36-40s
    slide_progress = t / duration
    
    img = Image.new("RGB", (1280, 720), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 44)
        font_sub = ImageFont.truetype("arial.ttf", 28)
        font_bullet = ImageFont.truetype("arialbd.ttf", 26)
        font_desc = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_bullet = ImageFont.load_default()
        font_desc = ImageFont.load_default()

    if slide_progress < 0.20:
        # Slide 1: Welcome & Overview
        draw_header(draw, "PROGRAM OVERVIEW")
        
        # Main Hero Card (2.5D Glassmorphic Card)
        draw.rounded_rectangle([80, 150, 1200, 620], radius=20, fill=(30, 41, 59), outline=(56, 189, 248), width=3)
        
        draw.text((120, 190), "Foci Tech Internship Program", fill=(56, 189, 248), font=font_title)
        draw.text((120, 260), "Bridging Academic Learning with Real Industry Requirements", fill=(226, 232, 240), font=font_sub)
        
        # Bullets
        bullets = [
            "⚡ Practical Implementation Over Theory",
            "🚀 Live Assignments & Real-World Projects",
            "👨‍💻 Professional Mentorship & Skill Development",
            "🎓 Stand Out in Placement & Career Opportunities"
        ]
        
        y = 330
        for b in bullets:
            draw.rounded_rectangle([120, y, 1160, y + 55], radius=10, fill=(15, 23, 42))
            draw.text((140, y + 12), b, fill=(241, 245, 249), font=font_bullet)
            y += 70

    elif slide_progress < 0.40:
        # Slide 2: Why Choose Foci Tech?
        draw_header(draw, "WHY CHOOSE FOCI TECH?")
        
        # Left Card
        draw.rounded_rectangle([80, 150, 610, 620], radius=20, fill=(30, 41, 59), outline=(239, 68, 68), width=2)
        draw.text((110, 180), "TRADITIONAL INTERNSHIPS", fill=(248, 113, 113), font=font_title)
        draw.text((110, 250), "❌ Mostly Theoretical Sessions", fill=(203, 213, 225), font=font_sub)
        draw.text((110, 320), "❌ Generic Participation Certificates", fill=(203, 213, 225), font=font_sub)
        draw.text((110, 390), "❌ Limited Real-World Exposure", fill=(203, 213, 225), font=font_sub)
        draw.text((110, 460), "❌ Minimal Project Work", fill=(203, 213, 225), font=font_sub)
        
        # Right Card
        draw.rounded_rectangle([670, 150, 1200, 620], radius=20, fill=(30, 41, 59), outline=(34, 197, 94), width=3)
        draw.text((700, 180), "FOCI TECH ADVANTAGE", fill=(74, 222, 128), font=font_title)
        draw.text((700, 250), "✅ 100% Practical Project Implementation", fill=(241, 245, 249), font=font_sub)
        draw.text((700, 320), "✅ Verified Industry Certificate", fill=(241, 245, 249), font=font_sub)
        draw.text((700, 390), "✅ Live Mentorship & Coding Practices", fill=(241, 245, 249), font=font_sub)
        draw.text((700, 460), "✅ In-Demand Technologies & Tools", fill=(241, 245, 249), font=font_sub)

    elif slide_progress < 0.60:
        # Slide 3: Real Industry Experience via MaidX India
        draw_header(draw, "REAL INDUSTRY ECOSYSTEM")
        
        draw.rounded_rectangle([80, 150, 1200, 620], radius=20, fill=(30, 41, 59), outline=(251, 191, 36), width=3)
        draw.text((120, 180), "Real Industry Experience via MaidX India", fill=(251, 191, 36), font=font_title)
        draw.text((120, 250), "Foci Tech is associated with MaidX India (Customized On-Demand Services Platform)", fill=(226, 232, 240), font=font_sub)
        
        features = [
            ("🏢 Real Business Workflows", "Understand how technology powers live commercial service applications."),
            ("💻 Software Development Practices", "Learn professional coding standards, version control, and architecture."),
            ("🎯 Problem-Solving Skills", "Work on real client challenges and real-world system debugging."),
            ("📈 Workplace Readiness", "Gain the exact technical and operational mindset expected by top recruiters.")
        ]
        
        y = 320
        for title, desc in features:
            draw.rounded_rectangle([120, y, 1160, y + 60], radius=10, fill=(15, 23, 42))
            draw.text((140, y + 8), title, fill=(56, 189, 248), font=font_bullet)
            draw.text((140, y + 33), desc, fill=(203, 213, 225), font=font_desc)
            y += 72

    elif slide_progress < 0.80:
        # Slide 4: Certificate & Career Benefits
        draw_header(draw, "CERTIFICATE & CAREER BENEFITS")
        
        draw.rounded_rectangle([80, 150, 1200, 620], radius=20, fill=(30, 41, 59), outline=(168, 85, 247), width=3)
        draw.text((120, 180), "Verified Certificate & Career Perks", fill=(192, 132, 252), font=font_title)
        
        perks = [
            "🏆 Professionally Verified Foci Tech Internship Certificate",
            "💼 Project Experience to Build a Competitive Resume",
            "🎯 Interview & Placement Preparation Guidance",
            "💰 Eligible Candidate Refund Policy After Assessment Pass",
            "🚀 Skill-Based Learning Aligned with Industry Standards"
        ]
        
        y = 260
        for p in perks:
            draw.rounded_rectangle([120, y, 1160, y + 58], radius=12, fill=(15, 23, 42), outline=(168, 85, 247), width=1)
            draw.text((140, y + 14), p, fill=(241, 245, 249), font=font_bullet)
            y += 70

    else:
        # Slide 5: Call to Action / Apply Now
        draw_header(draw, "APPLY NOW — FOCI TECH")
        
        draw.rounded_rectangle([80, 150, 1200, 620], radius=20, fill=(30, 41, 59), outline=(14, 165, 233), width=4)
        draw.text((220, 200), "Ready to Launch Your Tech Career?", fill=(56, 189, 248), font=font_title)
        draw.text((220, 270), "Join the Foci Tech Internship Program Today!", fill=(226, 232, 240), font=font_sub)
        
        # Big CTA Box
        draw.rounded_rectangle([250, 360, 1030, 480], radius=15, fill=(14, 165, 233))
        draw.text((290, 395), "🌐 APPLY ONLINE: https://focitech.in/", fill=(255, 255, 255), font=font_title)
        
        draw.text((310, 520), "Practical Knowledge  |  Real Exposure  |  Job-Ready Skills", fill=(203, 213, 225), font=font_sub)

    return np.array(img)


def main():
    asyncio.run(generate_voiceover())
    
    from moviepy import VideoClip, AudioFileClip
    audio = AudioFileClip(str(AUDIO_PATH))
    duration = audio.duration
    
    print(f"[VIDEO] Voiceover duration: {duration:.2f} seconds.")
    
    def make_frame(t):
        return render_slide_frame(t, duration)
        
    video = VideoClip(make_frame, duration=duration)
    video = video.with_audio(audio)
    
    print(f"[VIDEO] Rendering HD MP4 video to {OUTPUT_VIDEO}...")
    video.write_videofile(
        str(OUTPUT_VIDEO),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4
    )
    print(f"[VIDEO] ✅ Successfully generated {OUTPUT_VIDEO}!")


if __name__ == "__main__":
    main()
