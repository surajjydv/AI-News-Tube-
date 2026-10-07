#!/usr/bin/env python3
"""
deploy_existing.py - Deploy AI-NewsTube to an EXISTING EC2 instance
====================================================================
Uses your existing server: 98.84.135.236
Key file: C:\\Users\\suraj\\Downloads\\NewsTube.pem

Steps:
  1. Packs the project (skips venv, media, .git)
  2. Uploads via SCP (paramiko)
  3. Installs ffmpeg + Python deps on server
  4. Starts continuous_live_stream.py in tmux (survives SSH disconnect)
"""

import os, sys, time, tarfile
from pathlib import Path
from dotenv import load_dotenv

# Force UTF-8 output on Windows to avoid emoji/Hindi encoding crashes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).parent / ".env")

SERVER_IP   = "98.84.135.236"
KEY_FILE    = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
SSH_USER    = "ubuntu"
PROJECT_DIR = Path(__file__).parent.resolve()
REMOTE_APP  = "/app/AI-NewsTube"

YOUTUBE_STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
CHANNEL_NAME       = os.getenv("CHANNEL_NAME", "NewsTube")
DEFAULT_TTS_VOICE  = os.getenv("DEFAULT_TTS_VOICE", "hi-IN-SwaraNeural")


def banner(msg):  print(f"\n{'='*60}\n  {msg}\n{'='*60}")
def step(msg):    print(f"\n[-&gt;] {msg}")
def ok(msg):      print(f"[OK] {msg}")


def ensure_deps():
    for pkg in ["paramiko"]:
        try:
            __import__(pkg)
        except ImportError:
            print(f"Installing {pkg}...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])


def pack_project():
    step("Packing project (code only, no venv/media)...")
    skip_dirs = {".git", "venv", "__pycache__", "frames", "thumbnails",
                 "uploads", "videos", "voice", ".agents", ".gemini"}
    skip_exts = {".pem", ".pyc", ".pyo", ".mp4", ".ts", ".mp3",
                 ".jpg", ".png", ".tar.gz", ".gz", ".zip"}
    tarball = PROJECT_DIR / "deploy_package.tar.gz"
    with tarfile.open(str(tarball), "w:gz") as tar:
        for item in PROJECT_DIR.iterdir():
            if item.name in skip_dirs or item.suffix.lower() in skip_exts:
                continue
            if item.is_dir():
                for root, dirs, files in os.walk(str(item)):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in skip_exts:
                            continue
                        rel = fp.relative_to(PROJECT_DIR)
                        tar.add(str(fp), arcname=f"AI-NewsTube/{rel}")
            else:
                tar.add(str(item), arcname=f"AI-NewsTube/{item.name}")
    size_mb = tarball.stat().st_size / 1024 / 1024
    ok(f"Package ready: {size_mb:.1f} MB")
    return str(tarball)


def ssh_run(client, cmd, show=False, timeout=600):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out  = stdout.read().decode(errors="replace")
    err_ = stderr.read().decode(errors="replace")
    if show and (out or err_):
        print((out + err_)[-800:])
    return code, out, err_


def wait_ssh(max_wait=120):
    import paramiko
    step(f"Waiting for SSH on {SERVER_IP}...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            pkey = paramiko.RSAKey.from_private_key_file(str(KEY_FILE))
            c.connect(SERVER_IP, username=SSH_USER, pkey=pkey, timeout=10)
            c.close()
            ok("SSH is ready!")
            return True
        except Exception as e:
            print(f"  Waiting... ({e})")
            time.sleep(10)
    return False


def connect():
    import paramiko
    step(f"Connecting to {SSH_USER}@{SERVER_IP}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.RSAKey.from_private_key_file(str(KEY_FILE))
    client.connect(SERVER_IP, username=SSH_USER, pkey=pkey, timeout=30)
    ok("Connected!")
    return client


def deploy():
    banner("AI-NewsTube - Deploying to Existing EC2")

    if not KEY_FILE.exists():
        print(f"ERROR: PEM file not found: {KEY_FILE}")
        sys.exit(1)

    ensure_deps()
    wait_ssh()
    client = connect()

    # 1. Prepare remote directories
    step("Preparing remote directories...")
    ssh_run(client, "sudo mkdir -p /app && sudo chown ubuntu:ubuntu /app")
    ssh_run(client, f"mkdir -p {REMOTE_APP}/logs {REMOTE_APP}/videos "
                    f"{REMOTE_APP}/voice {REMOTE_APP}/assets {REMOTE_APP}/data")
    ok("Directories ready")

    # 2. Install system packages
    step("Installing system packages (ffmpeg, fonts, tmux)...")
    sys_pkgs = (
        "sudo apt-get update -qq 2>&1 | tail -3 && "
        "sudo apt-get install -y -qq ffmpeg tmux python3 python3-pip espeak-ng "
        "fonts-noto-core fonts-noto-extra fonts-indic libgl1 libglib2.0-0 2>&1 | tail -5"
    )
    ssh_run(client, sys_pkgs, show=True, timeout=300)
    ok("System packages installed")

    # 3. Pack and upload project
    tarball = pack_project()
    step("Uploading project (2-3 min)...")
    sftp = client.open_sftp()
    last = [0]
    def progress(sent, total):
        pct = int(sent / total * 100)
        if pct - last[0] >= 10:
            print(f"  {pct}%...", flush=True)
            last[0] = pct
    sftp.put(tarball, "/app/deploy_package.tar.gz", callback=progress)
    sftp.close()
    ok("Upload complete!")
    Path(tarball).unlink(missing_ok=True)

    # 4. Extract
    step("Extracting on server...")
    ssh_run(client, "cd /app && tar -xzf deploy_package.tar.gz && rm deploy_package.tar.gz")
    ok("Extracted!")

    # 5. Write .env
    step("Writing .env with API keys...")
    env_content = (
        f"CHANNEL_NAME={CHANNEL_NAME}\n"
        f"GROQ_API_KEY={GROQ_API_KEY}\n"
        f"YOUTUBE_STREAM_KEY={YOUTUBE_STREAM_KEY}\n"
        f"DEFAULT_TTS_VOICE={DEFAULT_TTS_VOICE}\n"
        "GROQ_ORPHEUS_ENABLED=false\n"
        "LIVE_STREAM_FPS=30\n"
        "LIVE_VIDEO_BITRATE=4500k\n"
    )
    sftp = client.open_sftp()
    with sftp.open(f"{REMOTE_APP}/.env", "w") as f:
        f.write(env_content)
    sftp.close()
    ok(".env written!")

    # 6. Install Python deps
    step("Installing Python deps (3-5 min)...")
    pip_cmd = (
        f"pip3 install --quiet --break-system-packages "
        f"-r {REMOTE_APP}/requirements.txt 2>&1 | tail -10"
    )
    ssh_run(client, pip_cmd, show=True, timeout=600)
    ssh_run(client,
            "pip3 install --quiet --break-system-packages pyttsx3 2>&1 | tail -3",
            show=True, timeout=120)
    ok("Python deps installed!")

    # 7. Reset seen-news cache
    ssh_run(client,
            f'echo \'{{"titles":[],"hashes":[]}}\' > {REMOTE_APP}/data/seen_news.json')
    ok("Seen-news cache reset")

    # 8. Kill old stream + start in tmux
    step("Stopping any existing stream...")
    ssh_run(client,
            "pkill -f continuous_live_stream 2>/dev/null; "
            "tmux kill-session -t livestream 2>/dev/null; sleep 2")

    step("Starting 24/7 live stream in tmux...")
    start_cmd = (
        "tmux new-session -d -s livestream "
        f"'cd {REMOTE_APP} && python3 scripts/continuous_live_stream.py "
        f"> {REMOTE_APP}/logs/stream.log 2>&1'"
    )
    ssh_run(client, start_cmd)
    time.sleep(8)

    # 9. Show status
    _, tmux_out, _ = ssh_run(client, "tmux list-sessions 2>&1")
    _, log_out,  _ = ssh_run(client,
                              f"tail -25 {REMOTE_APP}/logs/stream.log 2>/dev/null || echo '(starting...)'")
    client.close()

    banner("DEPLOYMENT COMPLETE!")
    print(f"""
  Server IP:   {SERVER_IP}
  tmux:        {tmux_out.strip()}
  YouTube Key: {YOUTUBE_STREAM_KEY[:8]}...

  Recent logs:
{log_out.strip()}

  ---- SSH Commands -----------------------------------------------
  Watch logs:
    ssh -i "C:\\Users\\suraj\\Downloads\\NewsTube.pem" ubuntu@{SERVER_IP} 'tail -f /app/AI-NewsTube/logs/stream.log'

  Attach stream session:
    ssh -i "C:\\Users\\suraj\\Downloads\\NewsTube.pem" ubuntu@{SERVER_IP} 'tmux attach -t livestream'

  [LIVE] Stream chal raha hai 24/7 - laptop band kar sakte hain!
""")


if __name__ == "__main__":
    deploy()
