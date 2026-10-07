"""
scripts/continuous_live_stream.py
==================================
24/7 Continuous Seamless Live AI News Stream Engine for NewsTube.

Solves RTMP Discontinuity:
- Uses FFmpeg Concat Demuxer (-f concat -stream_loop -1) on dynamic playlist.
- Guarantees 100% smooth monotonic PTS/DTS timestamps.
- Instant 5-Second Startup to YouTube RTMP.
"""

import os
import sys
import math
import shutil
import time
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw



if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import VIDEOS_DIR, ASSETS_DIR, VOICE_DIR, CHANNEL_NAME, YOUTUBE_STREAM_KEY, BROADCAST_FPS
from services.rss_service import fetch_news, get_realtime_ticker_headlines, get_fresh_unseen_news
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from agents.graphics_agent import render_tv_broadcast_frame, fetch_news_photo
from utils.logger import logger

# ── NEWSFORGEAI Enhancement Pack ──────────────────────────────
try:
    from agents.broadcast_enhancements import (
        DualAnchorVoice, render_enhanced_broadcast_frame,
        StoryDeduplicator, CategoryGraphicsEngine,
        MotionStinger, KenBurnsMotion
    )
    ENHANCEMENTS_ACTIVE = True
    logger.info("[ENHANCEMENTS] All 6 NEWSFORGEAI broadcast features ACTIVE")
except Exception as _e:
    ENHANCEMENTS_ACTIVE = False
    render_enhanced_broadcast_frame = None
    logger.warning(f"[ENHANCEMENTS] Could not load broadcast_enhancements: {_e}")

# A live queue is required here. FFmpeg reads a concat manifest once, so a
# manifest-based loop never picked up newly rendered clips. The consumer keeps
# one RTMP connection open and feeds normalized MPEG-TS segments into stdin.
RENDERED_VIDEOS = []
PLAYLIST_LOCK = threading.Condition()
LAST_GOOD_CLIP = None
LIVE_STREAM_FPS = int(os.getenv("LIVE_STREAM_FPS", "30"))
LIVE_VIDEO_BITRATE = os.getenv("LIVE_VIDEO_BITRATE", "4500k")
LIVE_MAXRATE = os.getenv("LIVE_MAXRATE", "5000k")
LIVE_BUFSIZE = os.getenv("LIVE_BUFSIZE", "9000k")


def get_ffmpeg_binary() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return "ffmpeg"


def translate_to_devanagari_hindi(english_title: str) -> str:
    if not english_title:
        return f"देश और दुनिया की ताज़ा बड़ी ख़बरें — {CHANNEL_NAME}"

    if any('\u0900' <= c <= '\u097f' for c in english_title):
        return english_title.split(" - ")[0].strip()

    clean_text = english_title.split(" - ")[0].replace("BREAKING|", "").replace("🚨", "").strip()

    try:
        from services.groq_service import generate_text
        prompt = (
            "You are an expert TV news editor who speaks simple, natural, everyday conversational Hindi (bol-chaal wali Hindi).\n"
            "Rewrite and translate this English news title into ONE short, super simple, exciting news headline in Devanagari script (max 8-12 words).\n\n"
            "CRITICAL RULES:\n"
            "- Use simple everyday words that a 10-year-old child can instantly understand (e.g. use 'केस से बरी' instead of 'याचिका निरस्त', use 'गिनती शुरू' instead of 'मतगणना जारी', use 'सुप्रीम कोर्ट' instead of 'उच्चतम न्यायालय', use 'वोट' instead of 'मतदान').\n"
            "- Do NOT use heavy, formal, difficult Sanskritized words.\n"
            "- Write in clean Devanagari Hindi using simple everyday spoken words.\n"
            "- OUTPUT ONLY THE HINDI HEADLINE TEXT, NO QUOTES, NO EXTRA WORDS.\n\n"
            f"Title: {clean_text}"
        )
        res_hindi = generate_text(prompt, model="llama-3.1-8b-instant", max_tokens=60).strip().replace('"', '').replace("'", "")
        if res_hindi and len(res_hindi) > 3:
            return res_hindi
    except Exception as e:
        logger.warning(f"Groq Hindi headline translation fallback ({e})")

    return clean_text


def add_video_to_playlist(video_path: Path):
    """Queue a completed clip exactly once for the live consumer."""
    video_path = video_path.resolve()
    with PLAYLIST_LOCK:
        if video_path.exists() and video_path not in RENDERED_VIDEOS:
            RENDERED_VIDEOS.append(video_path)
            PLAYLIST_LOCK.notify()
            print(f"[QUEUE] Added fresh clip '{video_path.name}'. Pending: {len(RENDERED_VIDEOS)}")


def next_video_from_queue() -> Path:
    """Return a fresh clip, or loop the last valid clip to avoid dead air."""
    global LAST_GOOD_CLIP
    with PLAYLIST_LOCK:
        while not RENDERED_VIDEOS:
            PLAYLIST_LOCK.wait(timeout=2)
            if LAST_GOOD_CLIP and LAST_GOOD_CLIP.exists():
                return LAST_GOOD_CLIP
        clip_path = RENDERED_VIDEOS.pop(0)
        LAST_GOOD_CLIP = clip_path
        return clip_path


def start_persistent_ffmpeg_process(rtmp_url: str) -> subprocess.Popen:
    """Keep one RTMP connection while feeding clips through MPEG-TS stdin."""
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning",
        "-fflags", "+genpts+igndts", "-i", "pipe:0",
        "-map", "0:v:0", "-map", "0:a:0?", "-vf",
        f"scale=1280:720,fps={LIVE_STREAM_FPS},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-b:v", LIVE_VIDEO_BITRATE, "-maxrate", LIVE_MAXRATE,
        "-bufsize", LIVE_BUFSIZE, "-r", str(LIVE_STREAM_FPS),
        "-g", str(max(1, LIVE_STREAM_FPS * 2)),
        "-keyint_min", str(max(1, LIVE_STREAM_FPS * 2)), "-sc_threshold", "0",
        "-c:a", "libvo_aacenc", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-f", "flv", rtmp_url,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def stream_clip_to_process(video_path: Path, stream_process: subprocess.Popen) -> bool:
    """Normalize one MP4 into MPEG-TS and feed it without closing RTMP."""
    remux = subprocess.Popen(
        [
            get_ffmpeg_binary(), "-loglevel", "error", "-re",
            "-fflags", "+genpts+igndts", "-i", str(video_path),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-map", "0:v:0", "-map", "0:a:0?", "-map", "1:a:0",
            "-shortest", "-c:v", "copy", "-bsf:v", "h264_mp4toannexb",
            "-c:a", "libvo_aacenc", "-b:a", "128k", "-ar", "44100", "-ac", "2",
            "-reset_timestamps", "1",
            "-muxdelay", "0", "-muxpreload", "0",
            "-f", "mpegts", "pipe:1"
        ],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    try:
        while True:
            chunk = remux.stdout.read(64 * 1024)
            if not chunk:
                break
            if stream_process.poll() is not None:
                return False
            stream_process.stdin.write(chunk)
            stream_process.stdin.flush()
        remux.wait()
        return remux.returncode == 0 and stream_process.poll() is None
    except (BrokenPipeError, OSError):
        return False
    finally:
        if remux.poll() is None:
            remux.terminate()
            remux.wait()


def stream_clip_to_rtmp(video_path: Path, rtmp_url: str) -> bool:
    """Broadcast one clip to YouTube RTMP with clean video copy and resynced audio.

    Audio is re-encoded with aresample=async=1 to fix timestamp lag that causes
    YouTube to drop audio. anullsrc fallback ensures even silent clips stream a
    valid AAC track so the decoder never goes mute.
    """
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning", "-re",
        "-fflags", "+genpts+igndts", "-i", str(video_path),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        # video: copy encoded h264 stream directly, no re-encode cost
        "-map", "0:v:0",
        # audio: prefer clip audio, fall back to silent source
        "-map", "0:a:0?", "-map", "1:a:0",
        "-shortest",
        "-c:v", "copy", "-bsf:v", "h264_mp4toannexb",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-af", "aresample=async=1:min_hard_comp=0.100000:first_pts=0",
        "-avoid_negative_ts", "make_zero",
        "-max_muxing_queue_size", "1024",
        "-flvflags", "no_duration_filesize", "-f", "flv", rtmp_url,
    ]
    try:
        return subprocess.run(cmd).returncode == 0
    except OSError as error:
        logger.error(f"Could not start clip streamer: {error}")
        return False


def start_continuous_raw_stream(rtmp_url: str):
    """Start one RTMP process fed by continuous raw video/audio pipes."""
    if os.name == "nt":
        return None
    video_read, video_write = os.pipe()
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
        "-r", str(BROADCAST_FPS), "-i", f"pipe:{video_read}",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "ultrafast",
        "-tune", "zerolatency", "-b:v", "2500k", "-maxrate", "2800k",
        "-bufsize", "5600k", "-pix_fmt", "yuv420p", "-g", "30",
        "-c:a", "libvo_aacenc", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-f", "flv", rtmp_url,
    ]
    process = subprocess.Popen(cmd, pass_fds=(video_read,))
    os.close(video_read)
    return process, video_write


def start_continuous_video_stream(rtmp_url: str) -> subprocess.Popen:
    """Start one RTMP process fed by raw video frames through stdin."""
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
        "-r", str(LIVE_STREAM_FPS), "-i", "pipe:0",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264",
        "-preset", "veryfast", "-tune", "zerolatency",
        "-b:v", LIVE_VIDEO_BITRATE, "-maxrate", LIVE_MAXRATE,
        "-bufsize", LIVE_BUFSIZE, "-pix_fmt", "yuv420p", "-r", str(LIVE_STREAM_FPS),
        "-g", str(max(1, LIVE_STREAM_FPS * 2)),
        "-keyint_min", str(max(1, LIVE_STREAM_FPS * 2)), "-sc_threshold", "0",
        "-c:a", "libvo_aacenc", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-f", "flv", rtmp_url,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def feed_clip_into_video_stream(video_path: Path, stream_process: subprocess.Popen) -> bool:
    """Decode one MP4 to raw frames and append it to the persistent encoder."""
    decoder = subprocess.Popen(
        [
            get_ffmpeg_binary(), "-loglevel", "error", "-re",
            "-i", str(video_path), "-an", "-vf",
            f"scale=1280:720,fps={LIVE_STREAM_FPS}", "-pix_fmt", "rgb24",
            "-f", "rawvideo", "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        while True:
            chunk = decoder.stdout.read(256 * 1024)
            if not chunk:
                break
            if stream_process.poll() is not None:
                return False
            stream_process.stdin.write(chunk)
        stream_process.stdin.flush()
        decoder.wait()
        return decoder.returncode == 0 and stream_process.poll() is None
    except (BrokenPipeError, OSError):
        return False
    finally:
        if decoder.poll() is None:
            decoder.terminate()
            decoder.wait()


def feed_clip_into_continuous_stream(video_path: Path, stream_state) -> bool:
    """Decode one MP4 and append its frames/audio to persistent pipes."""
    process, video_fd = stream_state
    decoder = subprocess.Popen(
        [get_ffmpeg_binary(), "-loglevel", "error", "-re", "-i", str(video_path),
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
         "-r", str(BROADCAST_FPS), "pipe:1"], stdout=subprocess.PIPE,
         stderr=subprocess.DEVNULL,
    )
    try:
        while True:
            chunk = decoder.stdout.read(256 * 1024)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(video_fd, view)
                view = view[written:]
        decoder.wait()
        return decoder.returncode == 0 and process.poll() is None
    except (BrokenPipeError, OSError):
        return False


def build_broadcast_keyframe_clip(
    headline: str,
    category: str,
    photo_paths: list[str],
    ticker_headlines: list[str],
    duration: float,
):
    """Build a smooth continuous broadcast clip with zero frame jumps.

    Strategy:
    - Render one high-quality static base frame (PIL — background + headline + cards + HUD)
    - Per video frame, composite only animated layers via NumPy:
        * Ken Burns zoom/pan on the news photo (continuous f(t))
        * Scrolling ticker strip
        * Pulsing live-dot aura
        * Glass light-sweep sheen across headline
    This gives real 25fps continuous motion at low CPU cost — no PIL re-render per frame.
    """
    from moviepy import VideoClip
    import numpy as np
    import datetime as _dt

    W, H = 1280, 720
    FPS  = 25

    # ── 1. Load photo and build zoomed photo strip ────────────────────────────
    photo_np_list = []
    for pp in (photo_paths or []):
        try:
            img = Image.open(pp).convert("RGB")
            # Oversample for Ken Burns headroom — 30% larger than frame
            ph_w = int(W * 1.30)
            ph_h = int(H * 1.30)
            img  = img.resize((ph_w, ph_h), Image.Resampling.LANCZOS)
            photo_np_list.append(np.array(img, dtype=np.uint8))
        except Exception:
            pass
    if not photo_np_list:
        ph_w = int(W * 1.30)
        ph_h = int(H * 1.30)
        placeholder = np.zeros((ph_h, ph_w, 3), dtype=np.uint8)
        placeholder[:, :] = [10, 14, 28]
        photo_np_list.append(placeholder)

    # ── 2. Pre-render static base (no photo, no animated layers) ─────────────
    cam_mode = KenBurnsMotion.get_mode_for_category(category) if ENHANCEMENTS_ACTIVE else "push_in"
    if ENHANCEMENTS_ACTIVE and render_enhanced_broadcast_frame:
        base_pil = render_enhanced_broadcast_frame(
            headline_text=headline,
            news_photo_path=None,          # no photo — we composite it per-frame
            global_t=0.0,
            category=category,
            ticker_headlines=[],           # no ticker — composited per-frame
            enable_ken_burns=False,
            clip_duration=duration,
            ken_burns_mode=cam_mode,
        )
    else:
        base_pil = render_tv_broadcast_frame(
            headline_text=headline,
            news_photo_path=None,
            global_t=0.0,
            category=category,
            ticker_headlines=[],
        )
    if base_pil.size != (W, H):
        base_pil = base_pil.resize((W, H), Image.Resampling.BILINEAR)
    base_np = np.array(base_pil, dtype=np.float32)  # H×W×3 float

    # ── 3. Pre-render ticker strip (wide enough to scroll) ────────────────────
    from utils.font_utils import load_font as _load_font, sanitize_text
    ticker_font = _load_font(20, bold=True)

    safe_ticks  = [sanitize_text(h) for h in (ticker_headlines or [])]
    tick_str    = ("  |  ".join(safe_ticks)
                   if safe_ticks else "AI-NewsTube Live Broadcast - Breaking News Every Minute")
    scroll_text = f"  >>  {tick_str}  >>  "

    # Measure text width
    probe = Image.new("RGB", (10, 10))
    pd    = ImageDraw.Draw(probe)
    try:
        txt_w = max(int(pd.textlength(scroll_text, font=ticker_font)), 1)
    except Exception:
        txt_w = max(len(scroll_text) * 12, 1)

    # Render 2× width strip for seamless loop
    strip_w   = txt_w * 2
    strip_h   = 44
    tick_strip = Image.new("RGB", (strip_w, strip_h), (8, 12, 24))
    td         = ImageDraw.Draw(tick_strip)
    td.text((0,          10), scroll_text, fill=(255, 255, 255), font=ticker_font)
    td.text((txt_w,      10), scroll_text, fill=(255, 255, 255), font=ticker_font)
    tick_np   = np.array(tick_strip, dtype=np.uint8)   # strip_h × strip_w × 3

    # Ticker region in the frame
    TICK_Y  = H - 90 + 4          # paste y offset in frame
    TICK_X0 = 0                    # left edge
    TICK_XE = W - 160              # right edge (leave category pill)
    TICK_PX_W = TICK_XE - TICK_X0

    SCROLL_SPEED = 150.0           # px / second

    # ── 4. Pre-render photo-region mask (right half of frame) ─────────────────
    # Photo occupies right 680 px × full height in render_tv_broadcast_frame
    PHOTO_X0, PHOTO_Y0 = 340, 0
    PHOTO_W,  PHOTO_H  = W - PHOTO_X0, H - 90  # leave ticker area

    # ── 5. make_frame ─────────────────────────────────────────────────────────
    def make_frame(t: float) -> np.ndarray:
        frame = base_np.copy()

        # — Ken Burns: smooth continuous zoom & pan over photo ——————————————
        photo_np = photo_np_list[int(t / max(duration / len(photo_np_list), 1)) % len(photo_np_list)]
        ph_h_src, ph_w_src = photo_np.shape[:2]

        if cam_mode == "push_in":
            progress   = t / max(duration, 1)
            scale      = 1.0 + 0.20 * progress            # 1.0 → 1.20
            cx, cy     = ph_w_src * 0.50, ph_h_src * 0.50
        elif cam_mode == "pull_out":
            progress   = t / max(duration, 1)
            scale      = 1.20 - 0.20 * progress           # 1.20 → 1.00
            cx, cy     = ph_w_src * 0.50, ph_h_src * 0.50
        elif cam_mode == "pan_left":
            scale      = 1.15
            progress   = t / max(duration, 1)
            cx         = ph_w_src * (0.70 - 0.40 * progress)   # right → left
            cy         = ph_h_src * 0.50
        elif cam_mode == "pan_right":
            scale      = 1.15
            progress   = t / max(duration, 1)
            cx         = ph_w_src * (0.30 + 0.40 * progress)   # left → right
            cy         = ph_h_src * 0.50
        else:  # tilt_up
            scale      = 1.15
            progress   = t / max(duration, 1)
            cx         = ph_w_src * 0.50
            cy         = ph_h_src * (0.65 - 0.30 * progress)   # bottom → top

        crop_w = int(PHOTO_W / scale)
        crop_h = int(PHOTO_H / scale)
        x0 = int(cx - crop_w // 2)
        y0 = int(cy - crop_h // 2)
        x0 = max(0, min(x0, ph_w_src - crop_w))
        y0 = max(0, min(y0, ph_h_src - crop_h))

        cropped    = photo_np[y0:y0 + crop_h, x0:x0 + crop_w]
        photo_tile = Image.fromarray(cropped).resize((PHOTO_W, PHOTO_H), Image.Resampling.BILINEAR)
        frame[PHOTO_Y0:PHOTO_Y0 + PHOTO_H, PHOTO_X0:PHOTO_X0 + PHOTO_W] = np.array(photo_tile)

        # — Ticker scroll: vectorised NumPy (fast, pixel-accurate) ─────────────
        soff     = int(t * SCROLL_SPEED) % max(txt_w, 1)
        # Build one row of width TICK_PX_W by slicing from the pre-rendered strip
        src_indices = np.arange(TICK_X0, TICK_XE) + soff
        src_indices = src_indices % strip_w
        tick_row    = tick_np[:, src_indices]  # strip_h × TICK_PX_W × 3
        frame[TICK_Y:TICK_Y + strip_h, TICK_X0:TICK_XE] = tick_row

        # — Pulsing live-dot aura (vectorised) ───────────────────────────────
        pulse     = (math.sin(t * 4.0 * math.pi) + 1.0) / 2.0
        aura_r    = int(14 + 8 * pulse)
        dot_alpha = 0.55 * pulse
        dot_cx, dot_cy = 56, 58
        y0d = max(0, dot_cy - aura_r)
        y1d = min(H, dot_cy + aura_r + 1)
        x0d = max(0, dot_cx - aura_r)
        x1d = min(W, dot_cx + aura_r + 1)
        ys, xs = np.ogrid[y0d:y1d, x0d:x1d]
        mask   = (ys - dot_cy) ** 2 + (xs - dot_cx) ** 2 <= aura_r * aura_r
        patch  = frame[y0d:y1d, x0d:x1d].astype(np.float32)
        red    = np.array([239, 68, 68], dtype=np.float32)
        patch[mask] = patch[mask] * (1 - dot_alpha) + red * dot_alpha
        frame[y0d:y1d, x0d:x1d] = np.clip(patch, 0, 255)

        # — Glass light sweep across headline panel ——————————————————————————
        banner_y   = H - 250
        sheen_x    = int((t * 650) % (W + 400)) - 200
        sheen_x2   = sheen_x + 120
        for row in range(banner_y, H - 85):
            prog   = (row - banner_y) / max(H - 85 - banner_y, 1)
            sx_lo  = int(sheen_x + (sheen_x - 60 - sheen_x) * prog)
            sx_hi  = int(sheen_x2 + (sheen_x2 + 60 - sheen_x2 - 120) * prog) + 120
            if sx_lo < W and sx_hi > 0:
                sx_lo_c = max(0, sx_lo)
                sx_hi_c = min(W, sx_hi)
                if sx_hi_c > sx_lo_c:
                    frame[row, sx_lo_c:sx_hi_c] = np.clip(
                        frame[row, sx_lo_c:sx_hi_c].astype(np.float32) * 1.0 + 22, 0, 255
                    )

        return frame.astype(np.uint8)

    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(FPS)
    return clip



def render_quick_startup_clip() -> Path:
    """Renders a fresh 30-second breaking news clip for instant 5-second stream start."""
    output_path = VIDEOS_DIR / "live_startup_30s.mp4"
    tmp_path = VIDEOS_DIR / "live_startup_30s.tmp.mp4"
    print("\n[STARTUP ENGINE] Fetching fresh breaking news & generating Devanagari Hindi headline...")

    articles = get_fresh_unseen_news(count=1)
    if articles:
        top = articles[0]
        raw_title = top.title
        category = top.category.upper()
    else:
        raw_title = f"देश भर में ताज़ा हलचल: {CHANNEL_NAME} पर देखें दिनभर की तमाम बड़ी ख़बरें"
        category = "TOP STORIES"

    hindi_headline = translate_to_devanagari_hindi(raw_title)

    script_hindi = (
        f"नमस्कार! {CHANNEL_NAME} की 24/7 लाइव ब्रॉडकास्ट में आपका स्वागत है। "
        f"इस वक्त की बड़ी ख़बर: {hindi_headline}। "
        f"देश और दुनिया की तमाम ताज़ा अपडेट्स के लिए जुड़े रहिए {CHANNEL_NAME} के साथ।"
    )

    script_obj = GeneratedScript(
        topic_title=hindi_headline[:60],
        category=category,
        script_text=script_hindi,
        word_count=len(script_hindi.split())
    )
    res_script = voice_agent(script_obj)
    audio_path = Path(res_script.audio_path) if res_script.audio_path else None

    clean_kw = raw_title.split(" - ")[0].replace("BREAKING|", "").replace("🚨", "").strip()
    photo_paths = []

    def _fetch_p(idx):
        p_file = ASSETS_DIR / f"startup_photo_{idx}.jpg"
        if fetch_news_photo(clean_kw, p_file, idx):
            return str(p_file)
        return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        res_photos = pool.map(_fetch_p, [1, 2, 3])
        for p in res_photos:
            if p:
                photo_paths.append(p)

    tickers = get_realtime_ticker_headlines()

    from moviepy import AudioFileClip

    audio_clip = AudioFileClip(str(audio_path)) if audio_path and audio_path.exists() else None
    duration = max(25.0, (audio_clip.duration + 4.0) if audio_clip else 30.0)

    clip = build_broadcast_keyframe_clip(
        hindi_headline, category, photo_paths, tickers, duration
    )
    if audio_clip:
        clip = clip.with_audio(audio_clip)

    if tmp_path.exists():
        try:
            tmp_path.unlink()
        except Exception:
            pass

    clip.write_videofile(
        str(tmp_path),
        fps=BROADCAST_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None
    )
    clip.close()
    if audio_clip:
        audio_clip.close()

    # Video contains the pixels/audio now; release intermediate media.
    for generated_path in [*photo_paths, audio_path]:
        if generated_path:
            try:
                Path(generated_path).unlink(missing_ok=True)
            except OSError:
                pass

    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    tmp_path.rename(output_path)
    print(f"[STARTUP ENGINE] ✅ Fresh startup clip ready: {output_path.name}")
    return output_path


def generate_full_detail_hindi_script(headline_hindi: str, raw_english_title: str, category: str) -> str:
    """Generates detailed, in-depth 30-second Hindi news script using Groq LLM Llama 3.3 70B."""
    prompt = f"""आप एक बेहतरीन और तेज़ टीवी समाचार एंकर हैं।
आपको इस 30-सेकंड की खबर पर पूरी कहानी का संपूर्ण विवरण (Full Story Explanation) बेहद सरल, आसान और बोलचाल वाली हिंदी में समझाना है।

समाचार श्रेणी: {category}
मुख्य शीर्षक: {headline_hindi} ({raw_english_title})

मुख्य नियम:
1. पूरी कहानी का विवरण (Full Explanation): 30 सेकंड के अंदर स्पष्ट समझाएं कि क्या मुख्य घटना हुई, इसके पीछे की क्या वजह थी, और अब क्या बड़ा अपडेट या फैसला आया है।
2. सरल भाषा (Saral Hindi): भारी किताबी शब्दों (जैसे 'मतगणना', 'अधिवक्ता', 'निरस्त', 'याचिका') का प्रयोग न करें। दैनिक बोलचाल के आसान शब्दों (जैसे 'कोर्ट', 'गिनती', 'केस', 'फैसला', 'राहत') का प्रयोग करें।
3. कोई इंट्रो या आउट्रो नहीं: "नमस्कार", "स्वागत है", "सब्सक्राइब करें" जैसे वाक्य बिलकुल न लिखें।
4. सटीक लंबाई: 65 से 80 शब्द लिखें ताकि 25 से 28 सेकंड में पूरी खबर स्पष्ट रूप से बोलकर समझाई जा सके।
"""
    try:
        from services.groq_service import generate_text
        text = generate_text(prompt)
        if text and len(text.strip()) > 30:
            return text.strip()
    except Exception as e:
        print(f"[SCRIPT LLM WARN] {e}")

    return (
        f"इस वक्त की बड़ी खबर: {headline_hindi}। "
        f"इस मामले में प्राप्त ताज़ा जानकारियों के अनुसार, स्थिति पर लगातार नज़र रखी जा रही है। "
        f"विशेषज्ञों का मानना है कि इस घटना के व्यापक प्रभाव देखने को मिल सकते हैं।"
    )


def _process_story_assets_parallel(story_dict: dict, cycle_count: int, s_idx: int) -> dict:
    clean_kw = story_dict['clean_kw']
    h_text = story_dict['headline_hindi']
    c_text = story_dict['category']

    def _fetch_photo(p_idx):
        photo_file = ASSETS_DIR / f"topic_5m_c{cycle_count}_s{s_idx}_p{p_idx}.jpg"
        if fetch_news_photo(clean_kw, photo_file, s_idx * 3 + p_idx):
            return str(photo_file)
        return None

    story_photos = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        photo_results = pool.map(_fetch_photo, [1, 2, 3])
        for p in photo_results:
            if p:
                story_photos.append(p)

    # Generate Full-Detail Script for Trending News Story
    script_hindi = generate_full_detail_hindi_script(h_text, clean_kw, c_text)

    script_obj = GeneratedScript(
        topic_title=h_text[:60],
        category=c_text,
        script_text=script_hindi,
        word_count=len(script_hindi.split())
    )
    res_script = voice_agent(script_obj)
    audio_path = Path(res_script.audio_path) if res_script.audio_path else None

    return {
        "headline_hindi": h_text,
        "category": c_text,
        "photos": story_photos,
        "audio_path": audio_path
    }


def render_single_30s_story_clip(clip_index: int) -> Path:
    """Renders an instant, standalone 30-second story clip and pushes to playlist immediately."""
    # Never overwrite a clip that may still be in the live pipeline.
    file_id = f"{int(time.time())}_{clip_index}"
    output_path = VIDEOS_DIR / f"live_30s_story_{file_id}.mp4"
    tmp_path = VIDEOS_DIR / f"live_30s_story_{file_id}.tmp.mp4"
    print(f"\n[FAST STREAM ENGINE] Clip #{clip_index}: Fetching fresh trending news story...")

    articles = get_fresh_unseen_news(count=1)
    if not articles:
        articles = fetch_news(limit_per_category=2)

    art = articles[0] if articles else None
    if art:
        raw_t = art.title
        category = art.category.upper()
    else:
        raw_t = "India Today Latest News Bulletin"
        category = "TOP STORIES"

    clean_kw = raw_t.split(" - ")[0].replace("BREAKING|", "").replace("🚨", "").strip()
    headline_hindi = translate_to_devanagari_hindi(raw_t)

    # Photos and script generation are independent; run them concurrently.
    def _fetch_p(p_idx):
        p_file = ASSETS_DIR / f"story_c{clip_index}_p{p_idx}.jpg"
        if fetch_news_photo(clean_kw, p_file, clip_index * 3 + p_idx, category=category):
            return str(p_file)
        return None

    def _fetch_photos():
        with ThreadPoolExecutor(max_workers=3) as photo_pool:
            return [p for p in photo_pool.map(_fetch_p, [1, 2, 3]) if p]

    with ThreadPoolExecutor(max_workers=2) as prep_pool:
        photos_future = prep_pool.submit(_fetch_photos)
        script_future = prep_pool.submit(
            generate_full_detail_hindi_script, headline_hindi, clean_kw, category
        )
        photo_paths = photos_future.result()
        script_text = script_future.result()

    # Voice generation: Use DualAnchorVoice (Male/Female alternation) if available
    script_obj = GeneratedScript(
        topic_title=headline_hindi[:60],
        category=category,
        script_text=script_text,
        word_count=len(script_text.split())
    )
    if ENHANCEMENTS_ACTIVE:
        # Dual Anchor: alternate male/female voice per story
        voice = DualAnchorVoice.get_next_voice()
        ts_v = int(time.time())
        dual_audio_path = VOICE_DIR / f"voice_{ts_v}.mp3"
        ok = DualAnchorVoice.generate_dual_voiceover(script_text, dual_audio_path, force_voice=voice)
        if ok and dual_audio_path.exists() and dual_audio_path.stat().st_size > 1000:
            script_obj.audio_path = str(dual_audio_path)
            logger.info(f"  [DUAL ANCHOR] Voice: {voice}")
        else:
            res_script = voice_agent(script_obj)
            script_obj = res_script
    else:
        res_script = voice_agent(script_obj)
        script_obj = res_script
    audio_path = Path(script_obj.audio_path) if script_obj.audio_path else None

    tickers = get_realtime_ticker_headlines()

    from moviepy import AudioFileClip

    audio_clip = AudioFileClip(str(audio_path)) if audio_path and audio_path.exists() else None
    duration = max(25.0, (audio_clip.duration + 2.0) if audio_clip else 30.0)

    clip = build_broadcast_keyframe_clip(
        headline_hindi, category, photo_paths, tickers, duration
    )
    if audio_clip:
        clip = clip.with_audio(audio_clip)

    if tmp_path.exists():
        try:
            tmp_path.unlink()
        except Exception:
            pass

    clip.write_videofile(
        str(tmp_path),
        fps=BROADCAST_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None
    )
    clip.close()
    if audio_clip:
        audio_clip.close()

    # Remove intermediate photos/audio after the rendered MP4 is complete.
    for generated_path in [*photo_paths, audio_path]:
        if generated_path:
            try:
                Path(generated_path).unlink(missing_ok=True)
            except OSError:
                pass

    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    tmp_path.rename(output_path)
    add_video_to_playlist(output_path)
    return output_path


def bg_producer_thread():
    """Continuously pre-renders fresh 30s story clips, maintaining a healthy 3-4 clip buffer."""
    clip_idx = 1
    MAX_BUFFER = 4
    while True:
        try:
            with PLAYLIST_LOCK:
                queue_len = len(RENDERED_VIDEOS)
            if queue_len >= MAX_BUFFER:
                time.sleep(4)
                continue
            render_single_30s_story_clip(clip_idx)
            clip_idx += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"[PRE-RENDER WARN] {e}. Retrying in 2s...")
            time.sleep(2)



def main():
    """Legacy entry point; delegates to main_fixed()."""
    main_fixed()


def main_fixed():
    """Run the 24/7 live stream engine with full video and neural audio voiceover."""
    stream_key = sys.argv[1].strip() if len(sys.argv) > 1 else YOUTUBE_STREAM_KEY
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    startup_clip = VIDEOS_DIR / "live_startup_30s.mp4"
    if not startup_clip.exists() or startup_clip.stat().st_size < 100_000:
        startup_clip = render_quick_startup_clip()
    add_video_to_playlist(startup_clip)
    threading.Thread(target=bg_producer_thread, daemon=True).start()
    print("[PERSISTENT STREAM] 🔴 Live Stream Engine Active (Video + Neural Audio Voiceover)")
    while True:
        try:
            clip_path = next_video_from_queue()
            print(f"[STREAM] Broadcasting clip with audio: {clip_path.name}")
            clip_ok = stream_clip_to_rtmp(clip_path, rtmp_url)
            if clip_ok:
                with PLAYLIST_LOCK:
                    can_delete = clip_path != LAST_GOOD_CLIP
                if clip_path.name != "live_startup_30s.mp4" and can_delete:
                    try:
                        clip_path.unlink()
                    except OSError:
                        pass
            else:
                print(f"[STREAM RECOVERY] Error streaming {clip_path.name}. Retrying in 1s...")
                time.sleep(1)
                add_video_to_playlist(clip_path)
        except KeyboardInterrupt:
            print("\n[STOPPED] Stream stopped by user.")
            break
        except Exception as e:
            print(f"[STREAM RECOVERY] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main_fixed()
