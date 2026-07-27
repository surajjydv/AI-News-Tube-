import os
import sys
import time
import math
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import VideoClip, AudioFileClip, VideoFileClip, concatenate_videoclips
from config.settings import VIDEOS_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from utils.logger import logger
from utils.exceptions import VideoGenerationError


# ─────────────────────────────────────────────────────────────
# Font Helper
# ─────────────────────────────────────────────────────────────
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load font with fallback chain."""
    candidates = []
    if bold:
        candidates.append(FONT_DIR / "Roboto-Bold.ttf")
    candidates.append(FONT_DIR / "Roboto-Regular.ttf")
    candidates.append(Path("C:/Windows/Fonts/arialbd.ttf"))
    candidates.append(Path("C:/Windows/Fonts/arial.ttf"))
    candidates.append(Path("C:/Windows/Fonts/segoeui.ttf"))

    for fp in candidates:
        try:
            if fp.exists():
                return ImageFont.truetype(str(fp), size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


# ─────────────────────────────────────────────────────────────
# Audio RMS Helper (For Lip Sync & Visualizer)
# ─────────────────────────────────────────────────────────────
def _get_audio_rms(audio_clip: Optional[AudioFileClip], t: float) -> float:
    """Extract audio RMS volume level at timestamp t."""
    if audio_clip is None:
        return 0.0
    try:
        if t < 0 or t > audio_clip.duration:
            return 0.0
        frame_data = audio_clip.get_frame(t)
        if frame_data is not None and len(frame_data) > 0:
            arr = np.array(frame_data, dtype=np.float32)
            rms = float(np.sqrt(np.mean(np.square(arr))))
            return rms
    except Exception:
        pass
    return 0.0


# ─────────────────────────────────────────────────────────────
# Dynamic Image Mouth Overlay Fallback
# ─────────────────────────────────────────────────────────────
def _render_talking_anchor(
    anchor_img: Image.Image,
    target_w: int,
    target_h: int,
    audio_volume: float,
    global_t: float,
) -> Image.Image:
    """Fallback talking mouth frame generator for static anchor PNG."""
    resized = anchor_img.resize((target_w, target_h), Image.Resampling.LANCZOS).convert("RGBA")
    speech_level = min(1.0, max(0.0, (audio_volume - 0.015) / 0.12))

    mouth_cx = int(target_w * 0.485)
    mouth_cy = int(target_h * 0.235)
    mouth_base_w = int(target_w * 0.075)

    if speech_level > 0.04:
        aperture_h = int(6 + 22 * speech_level + 3 * math.sin(global_t * 25.0))
        aperture_w = int(mouth_base_w + 6 * math.sin(global_t * 18.0))

        mouth_img = Image.new("RGBA", (aperture_w + 10, aperture_h + 10), (0, 0, 0, 0))
        m_draw = ImageDraw.Draw(mouth_img)

        m_draw.ellipse([(2, 2), (aperture_w + 8, aperture_h + 8)], fill=(180, 115, 95, 180))
        m_draw.ellipse([(4, 4), (aperture_w + 6, aperture_h + 6)], fill=(45, 12, 18, 255))
        if aperture_h > 12:
            m_draw.rectangle([(6, 4), (aperture_w + 4, 4 + int(aperture_h * 0.3))], fill=(240, 240, 245, 230))
        m_draw.arc([(4, 4), (aperture_w + 6, aperture_h + 6)], start=0, end=180, fill=(170, 75, 80, 220), width=2)

        paste_x = mouth_cx - (aperture_w // 2) - 5
        paste_y = mouth_cy - (aperture_h // 2) - 5
        resized.paste(mouth_img, (paste_x, paste_y), mouth_img)

    return resized


# ─────────────────────────────────────────────────────────────
# Desk Audio Spectrum VU Meter Visualizer
# ─────────────────────────────────────────────────────────────
def _draw_audio_spectrum(
    draw: ImageDraw.Draw,
    speech_level: float,
    global_t: float,
    start_x: int = 160,
    start_y: int = 800,
    num_bars: int = 24,
):
    """Draws 24 animated audio spectrum EQ visualizer bars on the news desk."""
    bar_width = 8
    gap = 4
    max_h = 45

    for i in range(num_bars):
        band_factor = math.sin(global_t * 12.0 + i * 0.45) * 0.4 + 0.6
        if speech_level > 0.05:
            bar_h = int(8 + (max_h - 8) * speech_level * band_factor)
        else:
            bar_h = int(4 + 4 * math.sin(global_t * 4.0 + i))

        x = start_x + i * (bar_width + gap)
        y1 = start_y - bar_h
        y2 = start_y

        if bar_h > 32:
            fill_color = (239, 68, 68)  # Red
        elif bar_h > 18:
            fill_color = (234, 179, 8)  # Gold/Yellow
        else:
            fill_color = (6, 182, 212)  # Cyan/Blue

        draw.rectangle([(x, y1), (x + bar_width, y2)], fill=fill_color)


# ─────────────────────────────────────────────────────────────
# STAGE 1: Render Studio Camera Layer (Background + Anchor + PiP)
# ─────────────────────────────────────────────────────────────
def render_studio_camera_layer(
    studio_bg: Image.Image,
    anchor_img: Image.Image,
    pip_photo: Optional[Image.Image],
    global_t: float,
    audio_rms: float,
    cam_mode: int,
    t_in_scene: float,
    scene_duration: float,
    talking_anchor_clip: Optional[VideoFileClip] = None,
) -> Image.Image:
    """
    Renders 1920x1080 raw studio camera layer and applies camera transforms (Wide, Anchor Close-Up, Media Focus, Push-In).
    Uses talking_anchor.mp4 clip if available, or falls back to ai_anchor_3d.png overlay.
    """
    base_frame = studio_bg.copy()
    draw = ImageDraw.Draw(base_frame)
    w, h = base_frame.size  # 1920 x 1080

    # 1. PiP News Photo (Left Side)
    pip_x, pip_y = 80, 120
    pip_w, pip_h = 580, 380

    if pip_photo:
        resized_pip = pip_photo.resize((pip_w, pip_h), Image.Resampling.LANCZOS)
        base_frame.paste(resized_pip, (pip_x, pip_y))

        # Animated border
        pulse = 0.6 + 0.4 * abs(math.sin(global_t * 2.5))
        border_r = int(220 * pulse)
        for thickness in range(4):
            draw.rectangle(
                [(pip_x - thickness, pip_y - thickness),
                 (pip_x + pip_w + thickness, pip_y + pip_h + thickness)],
                outline=(border_r, 40, 40),
            )
        pip_font = _load_font(18, bold=True)
        draw.rectangle([(pip_x, pip_y), (pip_x + 120, pip_y + 30)], fill=(220, 38, 38))
        draw.text((pip_x + 10, pip_y + 5), "🔴 LIVE MEDIA", fill=(255, 255, 255), font=pip_font)
    else:
        draw.rectangle([(pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h)], fill=(15, 23, 42))

    # 2. Talking AI Anchor (Right Side)
    anchor_h = h - 280
    anchor_aspect = anchor_img.width / anchor_img.height
    anchor_w = int(anchor_h * anchor_aspect)

    sway_x = int(math.sin(global_t * 1.5) * 3)
    sway_y = int(math.sin(global_t * 3.0) * 2)

    base_anchor_x = w - anchor_w - 90
    base_anchor_y = 10
    anchor_x = base_anchor_x + sway_x
    anchor_y = base_anchor_y + sway_y

    talking_anchor = None
    if talking_anchor_clip is not None:
        try:
            t_sample = global_t % max(0.1, talking_anchor_clip.duration)
            anchor_frame_np = talking_anchor_clip.get_frame(t_sample)
            talking_anchor = Image.fromarray(anchor_frame_np).convert("RGBA")
            if talking_anchor.width != anchor_w or talking_anchor.height != anchor_h:
                talking_anchor = talking_anchor.resize((anchor_w, anchor_h), Image.Resampling.LANCZOS)
        except Exception:
            talking_anchor = None

    if talking_anchor is None:
        talking_anchor = _render_talking_anchor(anchor_img, anchor_w, anchor_h, audio_rms, global_t)

    if talking_anchor.mode == "RGBA":
        base_frame.paste(talking_anchor, (anchor_x, anchor_y), talking_anchor)
    else:
        base_frame.paste(talking_anchor, (anchor_x, anchor_y))

    # 3. Apply Camera Cut Transformation
    if cam_mode == 0:
        return base_frame
    elif cam_mode == 1:
        crop_box = (720, 0, 1920, 1080)
        cropped = base_frame.crop(crop_box)
        return cropped.resize((w, h), Image.Resampling.LANCZOS)
    elif cam_mode == 2:
        crop_box = (0, 0, 1320, 1080)
        cropped = base_frame.crop(crop_box)
        return cropped.resize((w, h), Image.Resampling.LANCZOS)
    else:
        progress = t_in_scene / max(0.1, scene_duration)
        zoom_factor = 1.0 + 0.12 * progress
        crop_w = int(w / zoom_factor)
        crop_h = int(h / zoom_factor)
        crop_x = (w - crop_w) // 2
        crop_y = (h - crop_h) // 2
        cropped = base_frame.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        return cropped.resize((w, h), Image.Resampling.LANCZOS)


# ─────────────────────────────────────────────────────────────
# STAGE 2: Render Fixed HUD Overlays (Clock, Lower Third, Ticker)
# ─────────────────────────────────────────────────────────────
def render_hud_overlay_layer(
    frame: Image.Image,
    logo_img: Optional[Image.Image],
    headline: str,
    category: str,
    t: float,
    duration: float,
    scene_idx: int,
    global_t: float,
    speech_level: float,
    ticker_headlines: Optional[List[str]],
    cam_mode: int,
) -> Image.Image:
    """
    Renders ALL fixed broadcast UI elements on top of the transformed camera layer.
    """
    draw = ImageDraw.Draw(frame)
    w, h = frame.size  # 1920 x 1080

    # 1. 3D CHANNEL LOGO ON DESK
    if logo_img:
        resized_logo = logo_img.resize((220, 64), Image.Resampling.LANCZOS).convert("RGBA")
        frame.paste(resized_logo, (w // 2 - 110, h - 275), resized_logo)

    # 2. TOP-LEFT: PULSING LIVE BROADCAST 4K BADGE
    live_font = _load_font(26, bold=True)
    live_pulse = abs(math.sin(global_t * 3.5))

    aura_r = int(12 + 6 * live_pulse)
    draw.ellipse(
        [(58 - aura_r, 60 - aura_r), (58 + aura_r, 60 + aura_r)],
        fill=(239, 68, 68, int(150 * live_pulse))
    )

    draw.rectangle([(40, 30), (380, 90)], fill=(220, 38, 38))
    draw.rectangle([(38, 28), (382, 92)], outline=(234, 179, 8), width=2)
    draw.ellipse([(52, 54), (66, 68)], fill=(255, 255, 255))
    draw.text((76, 44), f"LIVE 4K  |  {CHANNEL_NAME}", fill=(255, 255, 255), font=live_font)

    # 3. TOP-RIGHT: DIGITAL CLOCK & LOCATION
    now = datetime.now()
    seconds_tick = int(global_t) % 60
    time_str = f"{now.strftime('%H:%M')}:{seconds_tick:02d} IST"
    date_str = now.strftime("%d %b %Y").upper()

    time_box_x1 = w - 340
    time_box_x2 = w - 40
    draw.rectangle([(time_box_x1, 30), (time_box_x2, 90)], fill=(15, 23, 42))
    draw.rectangle([(time_box_x1 - 2, 28), (time_box_x2 + 2, 92)], outline=(51, 65, 85), width=2)

    clock_font = _load_font(22, bold=True)
    sub_font = _load_font(15, bold=False)

    draw.text((time_box_x1 + 18, 38), f"⏰ {time_str}", fill=(234, 179, 8), font=clock_font)
    draw.text((time_box_x1 + 18, 66), f"📍 NEW DELHI  •  {date_str}", fill=(148, 163, 184), font=sub_font)

    # 4. CAMERA CUT BADGE (Top Center)
    cam_names = ["🎥 CAM 1: WIDE STUDIO", "🎥 CAM 2: ANCHOR CLOSE-UP", "🎥 CAM 3: MEDIA FOCUS", "🎥 CAM 4: PUSH-IN ZOOM"]
    cam_colors = [(220, 38, 38), (6, 182, 212), (16, 185, 129), (168, 85, 247)]
    
    cam_font = _load_font(16, bold=True)
    draw.rectangle([(w // 2 - 130, 30), (w // 2 + 130, 68)], fill=cam_colors[cam_mode])
    draw.text((w // 2 - 115, 38), cam_names[cam_mode], fill=(255, 255, 255), font=cam_font)

    # 5. DESK AUDIO SPECTRUM VISUALIZER
    _draw_audio_spectrum(draw, speech_level, global_t, start_x=160, start_y=800, num_bars=24)

    # 6. REDESIGNED LOWER-THIRD HEADLINE CARD
    banner_y = h - 250

    brk_font = _load_font(26, bold=True)
    draw.rectangle([(40, banner_y), (380, banner_y + 48)], fill=(220, 38, 38))
    draw.text((55, banner_y + 10), "🚨 ताज़ा ख़बर", fill=(255, 255, 255), font=brk_font)

    cat_font = _load_font(22, bold=True)
    draw.rectangle([(380, banner_y), (680, banner_y + 48)], fill=(30, 41, 59))
    draw.text((395, banner_y + 12), f"⚡ {category.upper()}", fill=(234, 179, 8), font=cat_font)

    headline_top = banner_y + 48
    headline_bottom = banner_y + 165
    draw.rectangle([(40, headline_top), (w - 40, headline_bottom)], fill=(15, 23, 42))
    draw.rectangle([(40, headline_top), (58, headline_bottom)], fill=(239, 68, 68))
    draw.rectangle([(40, headline_top), (w - 40, headline_top + 3)], fill=(234, 179, 8))

    clean_headline = headline.replace("\n", " ").strip()

    anim_duration = 0.8
    if t < anim_duration:
        progress = t / anim_duration
        ease = 1.0 - (1.0 - progress) ** 3
        y_offset = int(30 * (1.0 - ease))
    else:
        y_offset = 0

    if len(clean_headline) > 85:
        headline_size = 34
    elif len(clean_headline) > 65:
        headline_size = 40
    elif len(clean_headline) > 45:
        headline_size = 46
    else:
        headline_size = 52

    headline_font = _load_font(headline_size, bold=True)

    max_text_w = w - 160
    words = clean_headline.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=headline_font)
        if bbox[2] - bbox[0] > max_text_w and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    line_h = headline_size + 8
    total_h = len(lines[:2]) * line_h
    text_y = headline_top + (headline_bottom - headline_top - total_h) // 2

    for i, line in enumerate(lines[:2]):
        draw.text((78, text_y + i * line_h + y_offset + 2), line, fill=(10, 10, 15), font=headline_font)
        draw.text((76, text_y + i * line_h + y_offset), line, fill=(255, 255, 255), font=headline_font)

    # 7. BOTTOM SLIDE REAL-TIME NEWS TICKER
    ticker_y = headline_bottom
    ticker_font = _load_font(20, bold=True)
    draw.rectangle([(40, ticker_y), (w - 40, ticker_y + 42)], fill=(234, 179, 8))
    draw.rectangle([(40, ticker_y), (220, ticker_y + 42)], fill=(220, 38, 38))
    draw.text((50, ticker_y + 10), "⚡ LIVE NEWS", fill=(255, 255, 255), font=_load_font(18, bold=True))

    if ticker_headlines and len(ticker_headlines) > 0:
        headlines_concat = "   •   ".join(ticker_headlines)
    else:
        headlines_concat = (
            f"[INDIA] AI-NewsTube automated broadcasting network active   •   "
            f"[{category.upper()}] {clean_headline}   •   "
            f"[WORLD] Real-time AI news processing system operational"
        )

    ticker_full_text = f"   {headlines_concat}   •   "
    scroll_speed = 140
    ticker_x = (w - 40) - int(global_t * scroll_speed) % 3500
    draw.text((ticker_x, ticker_y + 10), ticker_full_text * 4, fill=(15, 23, 42), font=ticker_font)

    # Watermark
    scene_font = _load_font(16, bold=True)
    draw.rectangle([(w - 180, ticker_y + 42), (w - 40, ticker_y + 72)], fill=(30, 41, 59))
    draw.text((w - 168, ticker_y + 47), f"SCENE {scene_idx}  |  3D HD", fill=(148, 163, 184), font=scene_font)

    return frame


# ─────────────────────────────────────────────────────────────
# Master Frame Compositor (Camera Cut Layer + Fixed HUD Overlays)
# ─────────────────────────────────────────────────────────────
def compose_studio_frame(
    studio_bg: Image.Image,
    anchor_img: Image.Image,
    pip_photo: Optional[Image.Image],
    logo_img: Optional[Image.Image],
    headline: str,
    category: str,
    t: float,
    duration: float,
    scene_idx: int,
    global_t: float,
    audio_clip: Optional[AudioFileClip] = None,
    ticker_headlines: Optional[List[str]] = None,
    talking_anchor_clip: Optional[VideoFileClip] = None,
) -> Image.Image:
    """
    Renders 1080p frame in two decoupled stages:
    1. Render Raw Studio Camera Layer using talking_anchor.mp4 (or PNG fallback) & apply camera cut transform.
    2. Render Fixed HUD UI Overlays on top.
    """
    audio_rms = _get_audio_rms(audio_clip, global_t)
    speech_level = min(1.0, max(0.0, (audio_rms - 0.015) / 0.12))
    cam_mode = int(global_t // 3.5) % 4

    camera_frame = render_studio_camera_layer(
        studio_bg, anchor_img, pip_photo,
        global_t, audio_rms, cam_mode,
        t_in_scene=t, scene_duration=duration,
        talking_anchor_clip=talking_anchor_clip
    )

    final_frame = render_hud_overlay_layer(
        camera_frame, logo_img, headline, category,
        t, duration, scene_idx, global_t, speech_level,
        ticker_headlines, cam_mode
    )

    return final_frame


# ─────────────────────────────────────────────────────────────
# Create Scene Clip
# ─────────────────────────────────────────────────────────────
def create_studio_scene_clip(
    studio_bg: Image.Image,
    anchor_img: Image.Image,
    pip_photo: Optional[Image.Image],
    logo_img: Optional[Image.Image],
    headline: str,
    category: str,
    duration: float,
    scene_idx: int,
    start_time: float,
    audio_clip: Optional[AudioFileClip] = None,
    ticker_headlines: Optional[List[str]] = None,
    talking_anchor_clip: Optional[VideoFileClip] = None,
) -> VideoClip:
    """Creates a VideoClip for one news scene with talking anchor video / PNG fallback & camera cuts."""

    def make_frame(t):
        global_t = start_time + t
        frame = compose_studio_frame(
            studio_bg, anchor_img, pip_photo, logo_img,
            headline, category, t, duration, scene_idx,
            global_t=global_t,
            audio_clip=audio_clip,
            ticker_headlines=ticker_headlines,
            talking_anchor_clip=talking_anchor_clip
        )
        return np.array(frame)

    return VideoClip(make_frame, duration=duration)


# ─────────────────────────────────────────────────────────────
# Main Video Agent
# ─────────────────────────────────────────────────────────────
def video_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Broadcast Video Editor Agent — Final Compositor:
    - Integrates anchor_talking.mp4 video (with dynamic PNG fallback)
    - 3D Metallic Channel Logo Emblem Overlays
    - Fast Multi-Camera Angle Video Cuts (Switches every 3.5s)
    - Decoupled HUD UI Layer (Clean lower thirds, clock, and live ticker)
    - 1080p MP4 Broadcast Export
    """
    logger.info("=" * 50)
    logger.info("🎬 VIDEO AGENT (Talking Anchor Video Compositor & TV Broadcast Editor)")
    logger.info("=" * 50)

    if not script_obj.audio_path or not Path(script_obj.audio_path).exists():
        raise VideoGenerationError("Audio voiceover file missing for video generation.")

    if not script_obj.image_paths or len(script_obj.image_paths) < 2:
        raise VideoGenerationError(
            "Studio assets missing. Expected: [anchor_path, studio_bg_path, logo_path, pip_photos...]"
        )

    try:
        anchor_path = script_obj.image_paths[0]
        studio_bg_path = script_obj.image_paths[1]
        
        if len(script_obj.image_paths) >= 3 and "logo" in script_obj.image_paths[2]:
            logo_path = script_obj.image_paths[2]
            pip_photo_paths = script_obj.image_paths[3:]
        else:
            logo_path = None
            pip_photo_paths = script_obj.image_paths[2:]

        logger.info(f"  📌 3D Anchor   : {Path(anchor_path).name}")
        logger.info(f"  📌 Studio BG   : {Path(studio_bg_path).name}")
        if logo_path:
            logger.info(f"  📌 3D Logo     : {Path(logo_path).name}")
        logger.info(f"  📌 PiP Photos  : {len(pip_photo_paths)}")

        # Load talking anchor MP4 clip if available
        talking_anchor_clip = None
        if script_obj.talking_anchor_path and Path(script_obj.talking_anchor_path).exists():
            try:
                talking_anchor_clip = VideoFileClip(script_obj.talking_anchor_path)
                logger.info(f"  🎬 Talking Anchor Video Loaded: {Path(script_obj.talking_anchor_path).name}")
            except Exception as e:
                logger.warning(f"  ⚠️ Could not load talking anchor MP4 clip ({e}). Using PNG fallback.")
                talking_anchor_clip = None
        else:
            logger.info("  ℹ️ Using 3D Anchor Image fallback for compositing.")

        # Load base assets
        studio_bg = Image.open(studio_bg_path).convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
        anchor_img = Image.open(anchor_path).convert("RGBA")

        logo_img = None
        if logo_path and Path(logo_path).exists():
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
            except Exception:
                logo_img = None

        # Load PiP photos
        pip_photos: List[Optional[Image.Image]] = []
        for pp in pip_photo_paths:
            try:
                pip_photos.append(Image.open(pp).convert("RGB"))
            except Exception:
                pip_photos.append(None)

        if not pip_photos:
            pip_photos = [None]

        # Audio
        audio_clip = AudioFileClip(script_obj.audio_path)
        total_duration = audio_clip.duration

        num_scenes = len(pip_photos)
        scene_duration = total_duration / num_scenes

        logger.info(
            f"  🎥 Rendering 1080p Broadcast Video — {total_duration:.1f}s total, "
            f"{num_scenes} scenes × {scene_duration:.1f}s each"
        )

        scene_clips = []
        current_start_time = 0.0

        for idx, pip_photo in enumerate(pip_photos, start=1):
            logger.info(f"  🖼️ Scene {idx}/{num_scenes}: Compositing broadcast clip with dynamic camera cuts...")
            clip = create_studio_scene_clip(
                studio_bg, anchor_img, pip_photo, logo_img,
                script_obj.topic_title, script_obj.category,
                scene_duration, idx,
                start_time=current_start_time,
                audio_clip=audio_clip,
                ticker_headlines=script_obj.ticker_headlines,
                talking_anchor_clip=talking_anchor_clip
            )
            scene_clips.append(clip)
            current_start_time += scene_duration

        video_sequence = concatenate_videoclips(scene_clips, method="compose")
        final_video = video_sequence.with_audio(audio_clip)

        timestamp = int(time.time())
        output_path = VIDEOS_DIR / f"studio_broadcast_{timestamp}.mp4"

        logger.info(f"  ⏳ Encoding 1080p Broadcast Video → {output_path.name}...")
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger="bar",
        )

        audio_clip.close()
        final_video.close()
        if talking_anchor_clip is not None:
            talking_anchor_clip.close()

        if output_path.exists() and output_path.stat().st_size > 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"  ✅ Broadcast Video rendered successfully: {output_path.name} ({size_mb:.1f} MB)")
            script_obj.video_path = str(output_path)
            return script_obj
        else:
            raise VideoGenerationError("Exported video file is missing or empty.")

    except VideoGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error in Video Agent: {e}")
        raise VideoGenerationError(f"Failed to render studio video: {e}") from e
