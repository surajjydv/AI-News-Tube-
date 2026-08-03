import sys
import shutil
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "videos"


def get_ffmpeg_binary() -> str:
    """Find ffmpeg binary either from PATH or imageio_ffmpeg."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    return "ffmpeg"


def get_best_video() -> Path:
    """Find the best valid MP4 file to stream."""
    candidates = [
        "broadcast_tv_production_1080p.mp4",
        "full_5min_news_bulletin_1080p.mp4",
        "todays_top_stories_25d_bulletin.mp4",
        "test_broadcast_30sec.mp4"
    ]
    for name in candidates:
        p = VIDEOS_DIR / name
        if p.exists() and p.stat().st_size > 100000:
            return p

    mp4_files = [f for f in VIDEOS_DIR.glob("*.mp4") if f.name != ".gitkeep" and f.stat().st_size > 100000]
    if mp4_files:
        return mp4_files[0]

    raise FileNotFoundError("No valid MP4 video found in videos/ directory.")


def start_stream(input_key_or_url: str):
    video_path = get_best_video()

    raw = input_key_or_url.strip()
    if raw.startswith("rtmp://") or raw.startswith("rtmps://"):
        if raw.endswith("/live2") or raw.endswith("/live2/"):
            print("\n[WARNING] You pasted Stream URL instead of Stream Key.")
            print("[INFO] Please copy Stream Key (e.g. abcd-1234-efgh-5678) from YouTube Studio.\n")
            return
        rtmp_url = raw
    else:
        rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{raw}"

    ffmpeg_bin = get_ffmpeg_binary()
    print("\n==================================================")
    print(" [LIVE STREAM] YouTube Live Broadcast Starting...")
    print(f" [VIDEO SOURCE] {video_path.name}")
    print(f" [FFMPEG BINARY] {ffmpeg_bin}")
    print(" [STATUS] Streaming live to YouTube! Press Ctrl+C to stop.")
    print("==================================================\n")

    cmd = [
        ffmpeg_bin,
        "-re",
        "-stream_loop", "-1",
        "-i", str(video_path),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "3500k",
        "-maxrate", "4000k",
        "-bufsize", "8000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-f", "flv",
        rtmp_url
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[STOPPED] Stream ended by user.")
    except Exception as e:
        print(f"\n[ERROR] Streaming failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        key = sys.argv[1]
    else:
        key = input("Enter YouTube Stream Key (e.g. abcd-1234-efgh-5678): ").strip()

    if key:
        start_stream(key)
    else:
        print("[ERROR] Stream key is required!")
