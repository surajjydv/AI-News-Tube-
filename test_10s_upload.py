"""
test_10s_upload.py
Creates a 10-second news bulletin test video and attempts uploading to YouTube.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from moviepy import ImageSequenceClip
from services.youtube_upload_service import upload_video_to_youtube
from utils.font_utils import load_font

def create_10s_test_video() -> str:
    output_dir = BASE_DIR / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "test_10s_bulletin.mp4"

    w, h = 1920, 1080
    font = load_font(40, bold=True, lang="en")

    frames = []
    temp_dir = BASE_DIR / "assets" / "test_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Render 10 frames (1 frame per sec, 10s duration)
    for i in range(10):
        img = Image.new("RGB", (w, h), (10, 20, 45))
        draw = ImageDraw.Draw(img)

        # Header Bar
        draw.rectangle([0, 0, w, 120], fill=(200, 30, 30))
        draw.text((60, 35), "NEWS 24x7 HD • TEST BROADCAST", fill=(255, 255, 255), font=font)

        # Main Box
        draw.rectangle([100, 200, 1820, 850], fill=(20, 45, 90), outline=(255, 200, 0), width=4)
        draw.text((150, 300), f"TEST STORY BULLETIN — FRAME {i+1}/10", fill=(255, 200, 0), font=font)
        draw.text((150, 420), "10-Second YouTube Integration Test", fill=(255, 255, 255), font=font)

        # Ticker Bar
        draw.rectangle([0, 960, w, h], fill=(15, 23, 42))
        draw.text((60, 995), "MARKET LIVE: SENSEX ▲ 81,420 | NIFTY ▲ 24,850 | AI-NEWSTUBE 10S TEST", fill=(255, 200, 0), font=font)

    # Encode with direct FFmpeg for high performance and zero pipe deadlocks
    import subprocess
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", "1",
        "-i", str(temp_dir / "frame_%02d.jpg"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-t", "10",
        "-c:a", "aac",
        "-strict", "-2",
        "-b:a", "128k",
        "-shortest",
        str(video_path)
    ]
    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(video_path)

def main():
    print("🎬 Generating 10-Second Test News Bulletin Video...")
    v_path = create_10s_test_video()
    print(f"✅ Video created: {v_path}")

    print("📤 Attempting YouTube Upload...")
    res = upload_video_to_youtube(
        video_path=v_path,
        title="AI-NewsTube 10-Second Test Bulletin",
        description="Automated 10-second test video upload from AI-NewsTube engine.",
        tags=["NewsTube", "TestUpload", "Shorts"],
        is_short=True,
        privacy_status="unlisted"
    )
    print(f"RESULT: {res}")

if __name__ == "__main__":
    main()
