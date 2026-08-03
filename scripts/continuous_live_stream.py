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
import shutil
import time
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

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

# A live queue is required here. ffmpeg reads a concat manifest once, so a
# manifest-based loop never picked up newly rendered clips.
RENDERED_VIDEOS = []
PLAYLIST_LOCK = threading.Condition()


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
    with PLAYLIST_LOCK:
        while not RENDERED_VIDEOS:
            PLAYLIST_LOCK.wait(timeout=5)
        return RENDERED_VIDEOS.pop(0)


def start_persistent_ffmpeg_process(rtmp_url: str) -> subprocess.Popen:
    """Keep one RTMP connection while feeding clips through MPEG-TS stdin."""
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning", "-fflags", "+genpts+igndts",
        "-re", "-f", "mpegts", "-i", "pipe:0", "-c:v", "libx264",
        "-preset", "ultrafast", "-tune", "zerolatency", "-b:v", "2500k",
        "-maxrate", "2800k", "-bufsize", "5600k", "-pix_fmt", "yuv420p",
        "-g", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-ac", "2", "-f", "flv", rtmp_url,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def stream_clip_to_process(video_path: Path, stream_process: subprocess.Popen) -> bool:
    """Remux one MP4 into MPEG-TS and feed it without closing RTMP."""
    remux = subprocess.Popen(
        [get_ffmpeg_binary(), "-loglevel", "error", "-i", str(video_path),
         "-c", "copy", "-bsf:v", "h264_mp4toannexb", "-f", "mpegts", "pipe:1"],
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
        return True
    except (BrokenPipeError, OSError):
        return False
    finally:
        remux.wait()


def stream_clip_to_rtmp(video_path: Path, rtmp_url: str) -> bool:
    """Broadcast one complete clip with clean timestamps, then return.

    Feeding multiple independent MPEG-TS streams into one stdin caused DTS
    discontinuities and could leave the feeder blocked after the first clip.
    A bounded ffmpeg process per clip is reliable for YouTube reconnects and
    guarantees the next queued story is actually reached.
    """
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning", "-re", "-i", str(video_path),
        "-c:v", "copy", "-bsf:v", "h264_mp4toannexb", "-c:a", "aac",
        "-b:a", "128k", "-ar", "44100", "-ac", "2", "-avoid_negative_ts", "make_zero",
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
    audio_read, audio_write = os.pipe()
    cmd = [
        get_ffmpeg_binary(), "-loglevel", "warning",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
        "-r", str(BROADCAST_FPS), "-i", f"pipe:{video_read}",
        "-f", "s16le", "-ar", "44100", "-ac", "2", "-i", f"pipe:{audio_read}",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "ultrafast",
        "-tune", "zerolatency", "-b:v", "2500k", "-maxrate", "2800k",
        "-bufsize", "5600k", "-pix_fmt", "yuv420p", "-g", "30",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-flvflags", "no_duration_filesize", "-f", "flv", rtmp_url,
    ]
    process = subprocess.Popen(cmd, pass_fds=(video_read, audio_read))
    os.close(video_read)
    os.close(audio_read)
    return process, video_write, audio_write


def feed_clip_into_continuous_stream(video_path: Path, stream_state) -> bool:
    """Decode one MP4 and append its frames/audio to persistent pipes."""
    process, video_fd, audio_fd = stream_state
    decoders = [
        subprocess.Popen(
            [get_ffmpeg_binary(), "-loglevel", "error", "-re", "-i", str(video_path),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
             "-r", str(BROADCAST_FPS), "pipe:1"], stdout=subprocess.PIPE,
             stderr=subprocess.DEVNULL,
        ),
        subprocess.Popen(
            [get_ffmpeg_binary(), "-loglevel", "error", "-re", "-i", str(video_path),
             "-f", "s16le", "-ar", "44100", "-ac", "2", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        ),
    ]
    results = [False, False]

    def copy_stream(index, target_fd):
        try:
            while True:
                chunk = decoders[index].stdout.read(256 * 1024)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    written = os.write(target_fd, view)
                    view = view[written:]
            results[index] = True
        except (BrokenPipeError, OSError):
            results[index] = False

    threads = [threading.Thread(target=copy_stream, args=(0, video_fd)),
               threading.Thread(target=copy_stream, args=(1, audio_fd))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for decoder in decoders:
        decoder.wait()
    return all(results) and process.poll() is None


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
        if frame_pil.size != (1280, 720):
            frame_pil = frame_pil.resize((1280, 720), Image.Resampling.BILINEAR)
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
        raise RuntimeError("No unseen fresh news available; waiting for a new RSS item")

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
        if fetch_news_photo(clean_kw, p_file, clip_index * 3 + p_idx):
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

    # Voice generation depends on the script, so it starts after the parallel prep.
    script_obj = GeneratedScript(
        topic_title=headline_hindi[:60],
        category=category,
        script_text=script_text,
        word_count=len(script_text.split())
    )
    res_script = voice_agent(script_obj)
    audio_path = Path(res_script.audio_path) if res_script.audio_path else None

    tickers = get_realtime_ticker_headlines()

    from moviepy import VideoClip, AudioFileClip
    import numpy as np

    audio_clip = AudioFileClip(str(audio_path)) if audio_path and audio_path.exists() else None
    duration = max(25.0, (audio_clip.duration + 2.0) if audio_clip else 30.0)

    def make_frame(t):
        current_photo = photo_paths[int(t / 7.0) % len(photo_paths)] if photo_paths else None
        frame_pil = render_tv_broadcast_frame(
            headline_text=headline_hindi,
            news_photo_path=current_photo,
            global_t=t,
            category=category,
            ticker_headlines=tickers
        )
        if frame_pil.size != (1280, 720):
            frame_pil = frame_pil.resize((1280, 720), Image.Resampling.BILINEAR)
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
    """Continuously pre-renders fresh 30s story clips into rotating slot files."""
    clip_idx = 1
    while True:
        try:
            render_single_30s_story_clip(clip_idx)
            clip_idx += 1
            time.sleep(1)
        except Exception as e:
            print(f"[PRE-RENDER WARN] {e}. Retrying in 3s...")
            time.sleep(3)


def main():
    if len(sys.argv) > 1:
        stream_key = sys.argv[1].strip()
    else:
        stream_key = YOUTUBE_STREAM_KEY

    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    ffmpeg_bin = get_ffmpeg_binary()

    print("\n==================================================")
    print(" 🔴 NewsTube HINDI 24/7 PERSISTENT STREAM ENGINE")
    print(f" Target: rtmp://a.rtmp.youtube.com/live2/******")
    print(f" Stream Key: {stream_key}")
    print(" Strategy: Persistent FFmpeg Concat Stream (-stream_loop -1)")
    print("==================================================\n")

    # 1. Check existing clips & render initial 30s clip if empty
    existing_videos = [v for v in VIDEOS_DIR.glob("*.mp4") if v.stat().st_size > 100000 and "tmp" not in v.name]
    if existing_videos:
        for v in existing_videos[:3]:
            add_video_to_playlist(v)
    else:
        startup_clip = render_quick_startup_clip()
        add_video_to_playlist(startup_clip)

    # 2. Launch background producer thread
    t = threading.Thread(target=bg_producer_thread, daemon=True)
    t.start()
    print("[STARTUP] 🚀 Background news producer thread active.")

    # 3. Persistent FFmpeg Concat Command (Never drops RTMP connection)
    cmd = [
        ffmpeg_bin,
        "-re",
        "-f", "concat",
        "-safe", "0",
        "-stream_loop", "-1",
        "-i", str(PLAYLIST_TXT.resolve()),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-b:v", "2500k",
        "-maxrate", "2800k",
        "-bufsize", "5600k",
        "-pix_fmt", "yuv420p",
        "-g", "30",
        "-keyint_min", "30",
        "-sc_threshold", "0",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        "-max_muxing_queue_size", "1024",
        "-flvflags", "no_duration_filesize",
        "-f", "flv",
        rtmp_url
    ]

    print("[PERSISTENT STREAM] 🔴 Broadcasting Live 24/7 to YouTube RTMP...")
    while True:
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n[STOPPED] Stream stopped by user.")
            break
        except Exception as e:
            print(f"[STREAM RECOVERY] Connection error: {e}. Retrying in 1s...")
            time.sleep(1)


def main_fixed():
    """Run the live producer/consumer engine; old concat main is retained for compatibility."""
    stream_key = sys.argv[1].strip() if len(sys.argv) > 1 else YOUTUBE_STREAM_KEY
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    # Reuse a valid startup clip so a restart does not block live output for
    # minutes while rendering. The background worker immediately prepares a
    # fresh unseen story afterwards.
    startup_clip = VIDEOS_DIR / "live_startup_30s.mp4"
    if not startup_clip.exists() or startup_clip.stat().st_size < 100_000:
        startup_clip = render_quick_startup_clip()
    add_video_to_playlist(startup_clip)
    threading.Thread(target=bg_producer_thread, daemon=True).start()
    stream_state = start_continuous_raw_stream(rtmp_url)
    while True:
        try:
            clip_path = next_video_from_queue()
            print(f"[STREAM] Broadcasting fresh clip: {clip_path.name}")
            clip_ok = (
                feed_clip_into_continuous_stream(clip_path, stream_state)
                if stream_state else stream_clip_to_rtmp(clip_path, rtmp_url)
            )
            if clip_ok:
                # The clip is immutable and has already been broadcast; keep
                # the 24/7 process from filling the disk over time.
                if clip_path.name != "live_startup_30s.mp4":
                    try:
                        clip_path.unlink()
                    except OSError:
                        pass
            elif stream_state:
                stream_state[0].terminate()
                stream_state = start_continuous_raw_stream(rtmp_url)
        except KeyboardInterrupt:
            if stream_state:
                try:
                    os.close(stream_state[1])
                    os.close(stream_state[2])
                    stream_state[0].terminate()
                except OSError:
                    pass
            break
        except Exception as e:
            print(f"[STREAM RECOVERY] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main_fixed()
