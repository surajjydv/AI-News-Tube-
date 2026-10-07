import os
import sys
import time
import tarfile
from pathlib import Path
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
SERVER_IP = "98.84.135.236"
KEY_FILE = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
if not KEY_FILE.exists():
    KEY_FILE = BASE_DIR / "ai-newstube-key.pem"

REMOTE_APP = "/app/AI-NewsTube"

print(f"Connecting to {SERVER_IP}...", flush=True)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_FILE))
client.connect(SERVER_IP, username="ubuntu", pkey=pkey, timeout=30)
print("Connected!", flush=True)

# Create small lean tarball
tarball = BASE_DIR / "lean_deploy.tar.gz"
skip_dirs = {".git", "venv", "__pycache__", "frames", "thumbnails", "uploads", "videos", "voice", ".agents", ".gemini", "threejs_frames", "assets/audio", "assets/video"}
skip_exts = {".pem", ".pyc", ".pyo", ".mp4", ".ts", ".tar.gz", ".gz", ".zip", ".jpg", ".png", ".mp3"}

print("Packaging files...", flush=True)
with tarfile.open(str(tarball), "w:gz") as tar:
    for item in BASE_DIR.iterdir():
        if item.name in skip_dirs or item.suffix.lower() in skip_exts:
            continue
        if item.is_dir():
            for root, dirs, files in os.walk(str(item)):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for f in files:
                    fp = Path(root) / f
                    # Include font files, exclude media
                    if fp.suffix.lower() in skip_exts and fp.suffix.lower() not in {".ttf", ".ttc", ".otf"}:
                        continue
                    rel = fp.relative_to(BASE_DIR)
                    tar.add(str(fp), arcname=f"AI-NewsTube/{rel}")
        else:
            tar.add(str(item), arcname=f"AI-NewsTube/{item.name}")

size_kb = tarball.stat().st_size / 1024
print(f"Lean package ready: {size_kb:.1f} KB", flush=True)

sftp = client.open_sftp()
print("Uploading lean package to /app/...", flush=True)
sftp.put(str(tarball), "/app/lean_deploy.tar.gz")
tarball.unlink(missing_ok=True)

for fname in ["client_secret.json", ".env"]:
    if (BASE_DIR / fname).exists():
        sftp.put(str(BASE_DIR / fname), f"{REMOTE_APP}/{fname}")
if (BASE_DIR / "data" / "token.json").exists():
    sftp.put(str(BASE_DIR / "data" / "token.json"), f"{REMOTE_APP}/data/token.json")
sftp.close()
print("Uploaded!", flush=True)

print("Extracting code on server...", flush=True)
_, stdout, _ = client.exec_command(f"cd /app && tar -xzf lean_deploy.tar.gz && rm lean_deploy.tar.gz && ls -la {REMOTE_APP}/services")
print(stdout.read().decode('utf-8', errors='replace'), flush=True)

print("Verifying 2.5D Engine & dependencies on EC2...", flush=True)
_, stdout, stderr = client.exec_command(f"cd {REMOTE_APP} && python3 -c \"import uharfbuzz, freetype, PIL; from services.broadcast_25d_engine import render_25d_top_header; print('2.5D TV BROADCAST ENGINE VERIFIED ON AWS')\"")
v_out = stdout.read().decode('utf-8', errors='replace')
v_err = stderr.read().decode('utf-8', errors='replace')
print("Output:", v_out, "Error:", v_err, flush=True)

print("Stopping old processes...", flush=True)
client.exec_command("pkill -9 -f direct_pub 2>/dev/null; pkill -9 -f realtime_breaking_news 2>/dev/null; pkill -9 -f auto_15min 2>/dev/null; tmux kill-session -t autopublisher 2>/dev/null")
time.sleep(2)

print("Starting 15-minute 2.5D auto-publisher in tmux...", flush=True)
client.exec_command(f"tmux new-session -d -s autopublisher 'cd {REMOTE_APP} && python3 run_realtime_news_autopublisher.py >> {REMOTE_APP}/logs/autopublisher.log 2>&1'")
time.sleep(3)

print("Checking tmux and logs...", flush=True)
_, stdout, _ = client.exec_command("tmux list-sessions")
print("Tmux:", stdout.read().decode('utf-8', errors='replace'), flush=True)

_, stdout, _ = client.exec_command(f"tail -n 25 {REMOTE_APP}/logs/autopublisher.log 2>/dev/null || echo '(Starting...)'")
print("Logs:\n", stdout.read().decode('utf-8', errors='replace'), flush=True)

client.close()
print("ALL DONE!", flush=True)
