"""
scripts/continuous_live_stream.py
==================================
24/7 Continuous Seamless Live AI News Stream Engine for NewsTube.

Optimizations:
1. 0 News Repetition: Uses get_fresh_unseen_news() to guarantee 100% unique news topics across cycles.
2. Parallel Processing Engine: Multi-threaded Groq translations, parallel Edge-TTS voice generation, and parallel photo fetching.
3. 24/7 Persistent Pipe Engine: Single persistent FFmpeg process connected to YouTube RTMP with +genpts timestamp continuity.
"""

import os
import sys
import shutil
import time
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import VIDEOS_DIR, ASSETS_DIR, CHANNEL_NAME, YOUTUBE_STREAM_KEY
from services.rss_service import fetch_news, get_realtime_ticker_headlines, get_fresh_unseen_news
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from agents.graphics_agent import render_tv_broadcast_frame, fetch_news_photo
from utils.logger import logger

RENDERED_VIDEOS_LIST = []
RENDER_LOCK = threading.Lock()


def get_ffmpeg_binary() -> str:
    """Find ffmpeg binary from PATH or imageio_ffmpeg."""
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
    """Translates/rewrites RSS headline into catchy Devanagari Hindi using Groq AI."""
    if not english_title:
        return f"देश और दुनिया की ताज़ा बड़ी ख़बरें — {CHANNEL_NAME}"

    if any('\u0900' <= c <= '\u097f' for c in english_title):
        return english_title.split(" - ")[0].strip()

    clean_text = english_title.split(" - ")[0].replace("BREAKING|", "").replace("🚨", "").strip()

    try:
        from groq import Groq
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            client = Groq(api_key=groq_key)
            prompt = (
                "You are a top Hindi news TV editor. "
                "Translate and rewrite the following English news title into a single short, catchy, professional Devanagari Hindi broadcast news headline (max 10-12 words). "
                "OUTPUT ONLY THE DEVANAGARI HINDI TEXT, NOTHING ELSE:\n\n"
                f"{clean_text}"
            )
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60,
                temperature=0.2,
            )
            res_hindi = response.choices[0].message.content.strip().replace('"', '').replace("'", "")
            if res_hindi and len(res_hindi) > 3:
                return res_hindi
    except Exception as e:
        logger.warning(f"Groq Hindi headline translation fallback ({e})")

    return clean_text


def add_rendered_video_to_loop(video_path: Path):
    """Appends a newly rendered video into the active stream loop playlist."""
    with RENDER_LOCK:
        if video_path not in RENDERED_VIDEOS_LIST:
            RENDERED_VIDEOS_LIST.append(video_path)
            # Keep max 5 recent bulletin videos in active loop
            if len(RENDERED_VIDEOS_LIST) > 5:
                RENDERED_VIDEOS_LIST.pop(0)
            print(f"[LOOP ENGINE] 🔄 Appended '{video_path.name}' to live loop! Total active clips: {len(RENDERED_VIDEOS_LIST)}")


def render_quick_startup_clip() -> Path:
    """Renders a fresh 30-second breaking news clip for instant 5-second stream startup."""
    output_path = VIDEOS_DIR / "live_startup_30s.mp4"
    tmp_path = VIDEOS_DIR / "live_startup_30s.tmp.mp4"
    print("\n[STARTUP ENGINE] Fetching fresh breaking news & generating Devanagari Hindi headline...")

    articles = fetch_news()
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

    # Fetch 3 real photos in parallel
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

    from moviepy import VideoClip, AudioFileClip
    import numpy as np

    audio_clip = AudioFileClip(str(audio_path)) if audio_path and audio_path.exists() else None
    duration = max(25.0, (audio_clip.duration + 4.0) if audio_clip else 30.0)

    def make_frame(t):
        current_photo = photo_paths[int(t / 7.0) % len(photo_paths)] if photo_paths else None
        frame_pil = render_tv_broadcast_frame(
            headline_text=hindi_headline,
            news_photo_path=current_photo,
            global_t=t,
            category=category,
            ticker_headlines=tickers
        )
        return np.array(frame_pil)

    clip = VideoClip(make_frame, duration=duration)
    if audio_clip:
        clip = clip.with_audio(audio_clip)

    if tmp_path.exists():
        try:
            tmp_path.unlink()
        except Exception:
            pass

    clip.write_videofile(
        str(tmp_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        logger=None
    )
    clip.close()
    if audio_clip:
        audio_clip.close()

    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    tmp_path.rename(output_path)
    print(f"[STARTUP ENGINE] ✅ Fresh Hindi startup clip ready: {output_path.name}")
    return output_path


def _process_story_assets_parallel(story_dict: dict, cycle_count: int, s_idx: int) -> dict:
    """Helper worker: Parallelizes photo downloads and TTS voice generation for a single story."""
    clean_kw = story_dict['clean_kw']
    h_text = story_dict['headline_hindi']
    c_text = story_dict['category']

    # 1. Fetch 3 real photos concurrently
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

    # 2. Generate Neural Voiceover
    script_hindi = (
        f"नमस्कार! {CHANNEL_NAME} की 5-मिनट की ताज़ा बुलेटिन में आपका स्वागत है। "
        f"इस वक्त की बड़ी ख़बर: {h_text}। "
        f"देश और दुनिया की तमाम अपडेट्स के लिए जुड़े रहिए {CHANNEL_NAME} के साथ।"
    )

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


def render_5min_live_bulletin(cycle_count: int) -> Path:
    """Renders a 5-minute news bulletin with 5 stories, Hindi headlines, and 3-photo slideshows."""
    output_path = VIDEOS_DIR / f"live_5min_bulletin_slot_{cycle_count % 3}.mp4"
    tmp_path = VIDEOS_DIR / f"live_5min_bulletin_slot_{cycle_count % 3}.tmp.mp4"
    print(f"\n[BACKGROUND ENGINE] Cycle #{cycle_count}: Fetching 5 fresh 100% unique news stories...")

    # Fetch 100% unseen, unique news articles
    articles = get_fresh_unseen_news(count=5)

    # Translate all 5 headlines into Hindi in parallel!
    def _translate_worker(art):
        raw_t = art.title
        clean_title = raw_t.split(" - ")[0].replace("BREAKING|", "").replace("🚨", "").strip()
        hindi_t = translate_to_devanagari_hindi(raw_t)
        return {
            "category": art.category.upper(),
            "headline_hindi": hindi_t,
            "clean_kw": clean_title,
        }

    with ThreadPoolExecutor(max_workers=5) as pool:
        selected_stories = list(pool.map(_translate_worker, articles))

    # Fetch photos and generate TTS for all 5 stories IN PARALLEL!
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [
            pool.submit(_process_story_assets_parallel, story, cycle_count, idx + 1)
            for idx, story in enumerate(selected_stories)
        ]
        processed_stories = [f.result() for f in futures]

    story_clips = []
    from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
    import numpy as np

    tickers = get_realtime_ticker_headlines()

    for story_data in processed_stories:
        audio_path = story_data["audio_path"]
        audio_clip = AudioFileClip(str(audio_path)) if audio_path and audio_path.exists() else None
        story_duration = max(50.0, (audio_clip.duration + 4.0) if audio_clip else 60.0)

        h_text = story_data['headline_hindi']
        c_text = story_data['category']
        story_photos = story_data['photos']

        def make_frame_closure(h_val, c_val, photo_list):
            def make_frame(t):
                curr_photo = photo_list[int(t / 7.0) % len(photo_list)] if photo_list else None
                frame_pil = render_tv_broadcast_frame(
                    headline_text=h_val,
                    news_photo_path=curr_photo,
                    global_t=t,
                    category=c_val,
                    ticker_headlines=tickers
                )
                return np.array(frame_pil)
            return make_frame

        frame_fn = make_frame_closure(h_text, c_text, story_photos)
        clip = VideoClip(frame_fn, duration=story_duration)
        if audio_clip:
            clip = clip.with_audio(audio_clip)

        story_clips.append(clip)

    final_5min_clip = concatenate_videoclips(story_clips, method="compose")

    if tmp_path.exists():
        try:
            tmp_path.unlink()
        except Exception:
            pass

    final_5min_clip.write_videofile(
        str(tmp_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        logger=None
    )

    for c in story_clips:
        c.close()
    final_5min_clip.close()

    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    tmp_path.rename(output_path)
    print(f"[BACKGROUND ENGINE] ✅ 5-Min Bulletin Render Finished: {output_path.name}")

    add_rendered_video_to_loop(output_path)
    return output_path


def bg_producer_thread():
    """Background worker thread: Continuously pre-renders 5-minute news bulletins."""
    cycle = 1
    while True:
        try:
            render_5min_live_bulletin(cycle)
            cycle += 1
        except Exception as e:
            print(f"[BACKGROUND THREAD] Warning: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def start_persistent_ffmpeg_process(rtmp_url: str) -> subprocess.Popen:
    """
    Launches a single persistent FFmpeg process connected to YouTube RTMP.
    Reads MPEG-TS stream continuously from stdin (pipe:0) with auto-generated timestamps.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin,
        "-loglevel", "warning",
        "-fflags", "+genpts+igndts",
        "-re",
        "-f", "mpegts",
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-b:v", "2500k",
        "-maxrate", "2800k",
        "-bufsize", "5600k",
        "-pix_fmt", "yuv420p",
        "-g", "48",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-f", "flv",
        rtmp_url
    ]
    print("[PERSISTENT ENGINE] 🚀 Launching long-running persistent YouTube RTMP process...")
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def stream_clip_to_pipe(video_path: Path, persistent_proc: subprocess.Popen) -> bool:
    """
    Demuxes/remuxes an MP4 file into MPEG-TS format and pipes raw bytes into
    the persistent FFmpeg process's stdin.
    """
    if not video_path.exists():
        return True

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin,
        "-loglevel", "error",
        "-i", str(video_path.resolve()),
        "-c:v", "copy",
        "-c:a", "copy",
        "-bsf:v", "h264_mp4toannexb",
        "-f", "mpegts",
        "pipe:1"
    ]

    print(f"[STREAM FEEDER] 📺 Now broadcasting live clip: '{video_path.name}'")
    feeder_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    chunk_size = 64 * 1024  # 64 KB
    try:
        while True:
            if persistent_proc.poll() is not None:
                print("[STREAM FEEDER] ⚠️ Persistent RTMP process exited unexpectedly!")
                feeder_proc.kill()
                return False

            data = feeder_proc.stdout.read(chunk_size)
            if not data:
                break

            persistent_proc.stdin.write(data)
            persistent_proc.stdin.flush()
    except (BrokenPipeError, OSError) as e:
        print(f"[STREAM FEEDER] ⚠️ Pipe write error during stream: {e}")
        try:
            feeder_proc.kill()
        except Exception:
            pass
        return False
    finally:
        feeder_proc.wait()

    return True


def main():
    if len(sys.argv) > 1:
        stream_key = sys.argv[1].strip()
    else:
        stream_key = YOUTUBE_STREAM_KEY

    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    print("\n==================================================")
    print(" 🔴 NewsTube HINDI 24/7 PERSISTENT LIVE ENGINE")
    print(f" Target: rtmp://a.rtmp.youtube.com/live2/******")
    print(f" Stream Key: {stream_key}")
    print(" Architecture: 0-Disconnect Persistent MPEG-TS Stdin Pipe Engine")
    print(" Features: 0-Repetition Unseen News | Parallel TTS & Photo Engine | Devanagari Hindi")
    print("==================================================\n")

    # 1. Render instant 30-second startup clip (< 5 seconds)
    startup_clip = render_quick_startup_clip()

    # 2. Add startup clip to initial loop playlist
    add_rendered_video_to_loop(startup_clip)

    # 3. Start background pre-rendering thread for 5-minute bulletins
    t = threading.Thread(target=bg_producer_thread, daemon=True)
    t.start()

    # 4. Seamless 24/7 Streaming Feeder Loop
    play_index = 0
    persistent_proc = None

    print("[PERSISTENT STREAM] 🔴 Live Stream Engine Started! Broadcasting 24/7 Non-Stop to YouTube RTMP...\n")

    while True:
        try:
            if persistent_proc is None or persistent_proc.poll() is not None:
                persistent_proc = start_persistent_ffmpeg_process(rtmp_url)

            with RENDER_LOCK:
                if RENDERED_VIDEOS_LIST:
                    clip_to_play = RENDERED_VIDEOS_LIST[play_index % len(RENDERED_VIDEOS_LIST)]
                else:
                    clip_to_play = startup_clip

            success = stream_clip_to_pipe(clip_to_play, persistent_proc)
            if success:
                play_index += 1
            else:
                print("[STREAM RECOVERY] ⚠️ RTMP Pipe disconnected. Re-initializing persistent process...")
                time.sleep(2)
                persistent_proc = None
        except KeyboardInterrupt:
            print("\n[STOPPED] Live stream stopped by user.")
            if persistent_proc:
                try:
                    persistent_proc.stdin.close()
                    persistent_proc.terminate()
                except Exception:
                    pass
            break
        except Exception as e:
            print(f"[STREAM RECOVERY] ⚠️ Unexpected stream loop error: {e}. Retrying in 2s...")
            time.sleep(2)
            persistent_proc = None


if __name__ == "__main__":
    main()
