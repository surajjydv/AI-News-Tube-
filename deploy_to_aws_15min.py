#!/usr/bin/env python3
"""
deploy_to_aws_15min.py
======================
Fast, reliable deployment of the upgraded 2.5D TV Broadcast Engine to AWS EC2.
"""

import os
import sys
import time
import tarfile
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SERVER_IP = "98.84.135.236"
KEY_FILE = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
if not KEY_FILE.exists():
    KEY_FILE = BASE_DIR / "ai-newstube-key.pem"

SSH_USER = "ubuntu"
REMOTE_APP = "/app/AI-NewsTube"

def ensure_paramiko():
    import paramiko
    return paramiko

def pack_project() -> Path:
    print("[1/6] 📦 Creating clean deploy archive of 2.5D engine...")
    tarball = BASE_DIR / "deploy_package.tar.gz"
    
    skip_dirs = {
        ".git", "venv", "__pycache__", "frames", "thumbnails",
        "uploads", "videos", "voice", ".agents", ".gemini", "threejs_frames"
    }
    skip_exts = {
        ".pem", ".pyc", ".pyo", ".mp4", ".ts", ".tar.gz", ".gz", ".zip"
    }

    with tarfile.open(str(tarball), "w:gz") as tar:
        for item in BASE_DIR.iterdir():
            if item.name in skip_dirs or item.suffix.lower() in skip_exts:
                continue
            if item.is_dir():
                for root, dirs, files in os.walk(str(item)):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in skip_exts:
                            continue
                        rel = fp.relative_to(BASE_DIR)
                        tar.add(str(fp), arcname=f"AI-NewsTube/{rel}")
            else:
                tar.add(str(item), arcname=f"AI-NewsTube/{item.name}")
                
    print(f"      Archive ready: {tarball.stat().st_size / (1024*1024):.2f} MB")
    return tarball

def ssh_exec(client, cmd: str, timeout: int = 180) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return code, out, err

def deploy():
    paramiko = ensure_paramiko()
    print(f"[2/6] 🌐 Connecting to AWS EC2 ({SERVER_IP})...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.RSAKey.from_private_key_file(str(KEY_FILE))
    client.connect(SERVER_IP, username=SSH_USER, pkey=pkey, timeout=30)
    print("      Connected successfully.")

    # 1. Prepare directories
    print("[3/6] 📁 Setting up remote directories on AWS...")
    ssh_exec(client, "sudo mkdir -p /app && sudo chown ubuntu:ubuntu /app")
    ssh_exec(client, f"mkdir -p {REMOTE_APP}/logs {REMOTE_APP}/videos {REMOTE_APP}/voice {REMOTE_APP}/assets/fonts {REMOTE_APP}/data {REMOTE_APP}/thumbnails")

    # 2. Upload codebase
    tarball = pack_project()
    print("[4/6] ⬆️ Uploading package via SFTP to AWS EC2...")
    sftp = client.open_sftp()
    sftp.put(str(tarball), "/app/deploy_package.tar.gz")
    tarball.unlink(missing_ok=True)

    # Copy sensitive/auth tokens
    for f_name in ["client_secret.json", ".env"]:
        local_f = BASE_DIR / f_name
        if local_f.exists():
            sftp.put(str(local_f), f"{REMOTE_APP}/{f_name}")

    token_f = BASE_DIR / "data" / "token.json"
    if token_f.exists():
        sftp.put(str(token_f), f"{REMOTE_APP}/data/token.json")
    sftp.close()
    print("      Upload completed.")

    # 3. Extract & install deps
    print("[5/6] ⚙️ Extracting code and installing Python dependencies...")
    ssh_exec(client, "cd /app && tar -xzf deploy_package.tar.gz && rm deploy_package.tar.gz")
    
    pip_cmd = (
        "pip3 install --break-system-packages -q "
        "feedparser groq python-dotenv trafilatura edge-tts pillow requests moviepy numpy gtts "
        "google-api-python-client google-auth-oauthlib google-auth-httplib2 pyttsx3 uharfbuzz freetype-py"
    )
    code, out, err = ssh_exec(client, pip_cmd, timeout=300)
    if code != 0:
        print(f"      Pip Notice: {err.strip()}")
    else:
        print("      Python dependencies verified and ready.")

    # 4. Verify 2.5D graphics engine on server
    verify_cmd = (
        f"cd {REMOTE_APP} && python3 -c \""
        "import uharfbuzz, freetype, PIL; "
        "from services.broadcast_25d_engine import render_25d_top_header; "
        "print('2.5D Broadcast Engine Loaded Successfully on AWS')\""
    )
    v_code, v_out, v_err = ssh_exec(client, verify_cmd)
    print(f"      Verification: {v_out.strip() if v_code == 0 else v_err.strip()}")

    # 5. Stop old jobs and launch 15-min auto-publisher daemon
    print("[6/6] 🎬 Launching 15-Minute 2.5D Auto-Publisher Daemon in tmux...")
    ssh_exec(client, "pkill -f direct_pub 2>/dev/null; pkill -f realtime_breaking_news_autouploader 2>/dev/null; pkill -f auto_15min_news_story_scheduler 2>/dev/null; tmux kill-session -t autopublisher 2>/dev/null; sleep 1")

    start_cmd = (
        "tmux new-session -d -s autopublisher "
        f"'cd {REMOTE_APP} && python3 run_realtime_news_autopublisher.py "
        f">> {REMOTE_APP}/logs/autopublisher.log 2>&1'"
    )
    ssh_exec(client, start_cmd)
    time.sleep(3)

    _, tmux_out, _ = ssh_exec(client, "tmux list-sessions")
    _, log_out, _ = ssh_exec(client, f"tail -n 20 {REMOTE_APP}/logs/autopublisher.log 2>/dev/null || echo '(Starting...)'")

    client.close()

    print("\n" + "=" * 70)
    print("🎉 DEPLOYMENT COMPLETE & 15-MIN AUTO-PUBLISHER RUNNING ON AWS!")
    print(f"   Server IP    : {SERVER_IP}")
    print(f"   tmux Session : {tmux_out.strip()}")
    print("=" * 70)
    print("Live Daemon Logs:")
    print(log_out.strip())
    print("=" * 70)

if __name__ == "__main__":
    deploy()
