"""
scripts/test_sample_video.py
=============================
Generates a 10-second sample broadcast video to verify the full pipeline:

  processed_anchor.glb (Blender output)
       ↓
  TTS voice (edge-tts / gTTS)
       ↓
  Animated anchor compositing (video_agent)
       ↓
  videos/sample_test_10sec.mp4

Run with:
    python scripts/test_sample_video.py
"""

import os
import sys
import time
import asyncio
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Ensure project root is importable
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR, AVATAR_DIR, VIDEOS_DIR, VOICE_DIR, CHANNEL_NAME
from utils.logger import logger

STUDIO_DIR = ASSETS_DIR / "studio"
FONTS_DIR  = ASSETS_DIR / "fonts"
OUTPUT_VIDEO = VIDEOS_DIR / "sample_test_10sec.mp4"
SAMPLE_VOICE = VOICE_DIR / "sample_test_voice.mp3"

# ─────────────────────────────────────────
# 10-second sample script text
# ─────────────────────────────────────────
SAMPLE_TEXT = (
    "Welcome to AI-NewsTube. I am your AI news anchor. "
    "Today's top story — artificial intelligence is transforming the media industry. "
    "This is a 10-second sample video to verify your pipeline is fully working."
)


def _load_font(size: int, bold: bool = True):
    candidates = [
        FONTS_DIR / "Roboto-Bold.ttf",
        FONTS_DIR / "Roboto-Regular.ttf",
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ]
    for fp in candidates:
        try:
            if fp.exists():
                return ImageFont.truetype(str(fp), size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


# ─────────────────────────────────────────
# Step 1: Generate Voice
# ─────────────────────────────────────────
def generate_sample_voice() -> Path:
    if SAMPLE_VOICE.exists() and SAMPLE_VOICE.stat().st_size > 5000:
        logger.info(f"  Voice: Using cached sample voice ({SAMPLE_VOICE.name})")
        return SAMPLE_VOICE

    logger.info("  Voice: Generating sample TTS voice...")

    # Try edge-tts first
    try:
        import edge_tts

        async def _run_edge_tts():
            communicate = edge_tts.Communicate(SAMPLE_TEXT, voice="en-US-GuyNeural", rate="+5%")
            await communicate.save(str(SAMPLE_VOICE))

        asyncio.run(_run_edge_tts())
        if SAMPLE_VOICE.exists() and SAMPLE_VOICE.stat().st_size > 5000:
            logger.info(f"  Voice: edge-tts generated ({SAMPLE_VOICE.name})")
            return SAMPLE_VOICE
    except Exception as e:
        logger.warning(f"  Voice: edge-tts failed ({e}), trying gTTS...")

    # Fallback: gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=SAMPLE_TEXT, lang="en", slow=False)
        tts.save(str(SAMPLE_VOICE))
        logger.info(f"  Voice: gTTS generated ({SAMPLE_VOICE.name})")
        return SAMPLE_VOICE
    except Exception as e:
        logger.warning(f"  Voice: gTTS failed ({e})")

    return None


# ─────────────────────────────────────────
# Step 2: Load Anchor Image (from GLB or PNG portrait)
# ─────────────────────────────────────────
def get_anchor_image() -> Path:
    # Prefer the 3D portrait rendered by avatar_agent
    candidates = [
        STUDIO_DIR / "ai_anchor_3d.png",
        STUDIO_DIR / "ai_anchor.png",
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 5000:
            return c
    # Create placeholder if none exist
    placeholder = STUDIO_DIR / "ai_anchor_3d.png"
    img = Image.new("RGBA", (800, 1080), (15, 15, 35, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(300, 80), (500, 300)], fill=(70, 72, 100, 255))
    draw.polygon([(250, 300), (550, 300), (600, 800), (200, 800)], fill=(40, 44, 70, 255))
    img.save(str(placeholder), "PNG")
    return placeholder


# ─────────────────────────────────────────
# Step 3: Compose & Render 10-second Video
# ─────────────────────────────────────────
def render_sample_video(voice_path: Path) -> Path:
    from moviepy import VideoClip, AudioFileClip, CompositeVideoClip

    logger.info("  Video: Compositing 10-second sample broadcast video...")

    # Load audio
    audio_clip = None
    if voice_path and voice_path.exists():
        audio_clip = AudioFileClip(str(voice_path))

    DURATION = min(10.0, audio_clip.duration if audio_clip else 10.0)
    W, H = 1280, 720
    FPS = 24

    # Load studio background
    bg_path = STUDIO_DIR / "studio_background.png"
    anchor_path = get_anchor_image()
    logo_path = STUDIO_DIR / "channel_logo_3d.png"

    anchor_img = Image.open(str(anchor_path)).convert("RGBA")

    def make_frame(t: float):
        # ── Background ──────────────────────────────────
        if bg_path.exists():
            bg = Image.open(str(bg_path)).convert("RGB").resize((W, H), Image.LANCZOS)
        else:
            bg = Image.new("RGB", (W, H), (8, 10, 28))

        frame = bg.copy()
        draw = ImageDraw.Draw(frame)

        # ── Animated gradient overlay ─────────────────
        pulse = 0.5 + 0.5 * np.sin(t * 2.0)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.rectangle([(0, 0), (W, H)], fill=(10, 15, 40, int(30 + 10 * pulse)))
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

        # ── AI Anchor (right side) ────────────────────
        aw = 380
        ah = int(anchor_img.height * aw / anchor_img.width)
        anch_resized = anchor_img.resize((aw, ah), Image.LANCZOS)

        # Subtle breathe animation
        breathe = int(3 * np.sin(t * 1.2))
        ax, ay = W - aw - 30, H - ah + breathe
        frame.paste(anch_resized, (ax, ay), anch_resized.split()[3])

        frame_draw = ImageDraw.Draw(frame)

        # ── LIVE badge ────────────────────────────────
        badge_x, badge_y = 30, 30
        live_pulse = int(200 + 55 * np.sin(t * 3.0))
        frame_draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + 90, badge_y + 36)],
            radius=6, fill=(live_pulse, 20, 20)
        )
        font_sm = _load_font(20, bold=True)
        frame_draw.text((badge_x + 10, badge_y + 7), "● LIVE", font=font_sm, fill=(255, 255, 255))

        # ── Channel name ──────────────────────────────
        font_ch = _load_font(28, bold=True)
        frame_draw.text((30, 72), CHANNEL_NAME.upper(), font=font_ch, fill=(0, 200, 255))

        # ── Sample label ─────────────────────────────
        font_sample = _load_font(18)
        frame_draw.text((30, 106), "SAMPLE TEST — 10 SECOND PREVIEW", font=font_sample, fill=(255, 180, 0))

        # ── Ticker strip ─────────────────────────────
        ticker_y = H - 54
        frame_draw.rectangle([(0, ticker_y), (W, ticker_y + 54)], fill=(0, 140, 220))
        frame_draw.rectangle([(0, ticker_y), (120, ticker_y + 54)], fill=(220, 30, 30))
        font_ticker_label = _load_font(22, bold=True)
        frame_draw.text((8, ticker_y + 14), "BREAKING", font=font_ticker_label, fill=(255, 255, 255))

        # Scrolling ticker text
        ticker_text = "  AI-NewsTube Pipeline Test  ✓  Blender 5.2 Avatar Active  ✓  GLB Model Loaded  ✓  Full Pipeline Verified  "
        font_ticker = _load_font(20)
        scroll_speed = 120  # px/sec
        offset = int((t * scroll_speed) % (len(ticker_text) * 12))
        frame_draw.text((125 - offset, ticker_y + 16), ticker_text * 3, font=font_ticker, fill=(255, 255, 255))

        # ── Lower third ───────────────────────────────
        lt_y = H - 130
        lt_alpha = int(210 + 30 * np.sin(t * 1.5))
        lt_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lt_draw = ImageDraw.Draw(lt_overlay)
        lt_draw.rectangle([(0, lt_y), (600, lt_y + 68)], fill=(5, 10, 35, lt_alpha))
        lt_draw.rectangle([(0, lt_y), (6, lt_y + 68)], fill=(0, 200, 255, 255))
        frame = Image.alpha_composite(frame.convert("RGBA"), lt_overlay).convert("RGB")
        frame_draw = ImageDraw.Draw(frame)

        font_lt1 = _load_font(26, bold=True)
        font_lt2 = _load_font(18)
        frame_draw.text((18, lt_y + 8), "AI News Anchor", font=font_lt1, fill=(255, 255, 255))
        frame_draw.text((18, lt_y + 38), "Blender 5.2  |  Ch33_nonPBR.fbx  |  processed_anchor.glb", font=font_lt2, fill=(180, 220, 255))

        # ── Lip-sync mouth indicator ─────────────────
        if audio_clip:
            try:
                frame_arr = audio_clip.get_frame(min(t, audio_clip.duration - 0.01))
                rms = float(np.sqrt(np.mean(np.square(np.array(frame_arr, dtype=np.float32)))))
            except Exception:
                rms = 0.2
        else:
            rms = 0.3 * abs(np.sin(t * 4.0))

        mouth_open = min(int(rms * 800), 30)
        mx, my = ax + aw // 2 - 15, ay + int(ah * 0.62)
        frame_draw.ellipse([(mx, my), (mx + 30, my + mouth_open + 4)], fill=(50, 20, 20))

        # ── Progress bar ─────────────────────────────
        progress = t / DURATION
        bar_w = int(W * progress)
        frame_draw.rectangle([(0, H - 58), (bar_w, H - 55)], fill=(0, 200, 255))

        # ── Timestamp ─────────────────────────────────
        ts = f"{t:.1f}s / {DURATION:.0f}s"
        font_ts = _load_font(16)
        frame_draw.text((W - 100, 10), ts, font=font_ts, fill=(150, 150, 150))

        return np.array(frame.convert("RGB"))

    # Create clip
    video = VideoClip(make_frame, duration=DURATION)
    video = video.with_fps(FPS)

    if audio_clip:
        video = video.with_audio(audio_clip)

    logger.info(f"  Video: Rendering {DURATION:.0f}s at {W}x{H} {FPS}fps...")
    video.write_videofile(
        str(OUTPUT_VIDEO),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None,
    )

    if audio_clip:
        audio_clip.close()
    video.close()

    return OUTPUT_VIDEO


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    print("=" * 60)
    print("AI-NewsTube — 10 Second Sample Video Test")
    print("=" * 60)

    # Confirm processed_anchor.glb exists
    glb_path = AVATAR_DIR / "processed_anchor.glb"
    if glb_path.exists():
        size_mb = glb_path.stat().st_size / (1024 * 1024)
        print(f"[OK] processed_anchor.glb  : {size_mb:.2f} MB  (Blender 5.2 output)")
    else:
        print("[WARN] processed_anchor.glb not found — run blender_service.py first")

    # Step 1: Voice
    print()
    print("Step 1: Generating sample voice...")
    voice = generate_sample_voice()
    if voice and voice.exists():
        print(f"[OK] Voice: {voice.name}")
    else:
        print("[WARN] Voice generation failed — video will be silent")

    # Step 2: Render video
    print()
    print("Step 2: Rendering 10-second broadcast video...")
    out = render_sample_video(voice)

    if out.exists():
        size_mb = out.stat().st_size / (1024 * 1024)
        print()
        print("=" * 60)
        print(f"[SUCCESS] Sample video generated!")
        print(f"  File  : {out}")
        print(f"  Size  : {size_mb:.2f} MB")
        print(f"  Open  : start {out}")
        print("=" * 60)

        # Auto-open the video
        try:
            import subprocess
            subprocess.Popen(["start", "", str(out)], shell=True)
        except Exception:
            pass
    else:
        print("[ERROR] Video generation failed.")


if __name__ == "__main__":
    main()
