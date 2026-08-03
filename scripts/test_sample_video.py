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
    from moviepy import VideoClip, AudioFileClip

    logger.info("  Video: Compositing 10-second Aaj Tak style sample broadcast video...")

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

    anchor_img = Image.open(str(anchor_path)).convert("RGBA")

    def make_frame(t: float):
        from agents.graphics_agent import BroadcastLayerSystem
        layer_sys = BroadcastLayerSystem(width=W, height=H)

        if bg_path.exists():
            bg = Image.open(str(bg_path)).convert("RGB").resize((W, H), Image.LANCZOS)
        else:
            bg = Image.new("RGB", (W, H), (10, 12, 28))

        # Layer 0 & Layer 1: Base & Volumetric Depth
        frame = layer_sys.render_layer_0_background(bg)
        frame = layer_sys.render_layer_1_depth(frame, t)

        # 2. Presenter (Right side anchor position)
        aw = 340
        ah = int(anchor_img.height * aw / anchor_img.width)
        anch_resized = anchor_img.resize((aw, ah), Image.LANCZOS)

        sway_x = int(3 * np.sin(t * 1.5))
        breathe = int(3 * np.sin(t * 2.8))
        ax, ay = W - aw - 20 + sway_x, H - ah - 30 + breathe
        if anch_resized.mode == "RGBA":
            frame.paste(anch_resized, (ax, ay), anch_resized.split()[3])
        else:
            frame.paste(anch_resized, (ax, ay))

        # 3. Render Broadcast Overlays
        frame = layer_sys.render_layer_3_headline(frame, "AI-NEWSTUBE 2.5D BROADCAST ENGINE ACTIVE", "AI EXCLUSIVE", t, t)
        frame = layer_sys.render_layer_4_hud(frame, t, cam_mode=int(t // 3.5) % 3)
        frame = layer_sys.render_layer_5_ticker(frame, t, ticker_headlines=[
            "2.5D Broadcast Engine Active", "Aaj Tak Red & Gold Metallic Aesthetics Applied", "3D Extruded Lower Third Cards Rendered", "Specular Glass Light Sweeps Active"
        ])
        frame = layer_sys.render_layer_6_effects(frame, t)

        # Timestamp
        frame_draw = ImageDraw.Draw(frame)
        ts = f"{t:.1f}s / {DURATION:.0f}s"
        font_ts = _load_font(14)
        frame_draw.text((W - 90, 8), ts, font=font_ts, fill=(180, 180, 180))
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
