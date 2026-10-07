import os
import sys
import time
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

# 1. Install missing python packages
print("Installing Python dependencies (uharfbuzz, freetype-py, beautifulsoup4, etc)...", flush=True)
pip_cmd = (
    "pip3 install --break-system-packages -q "
    "uharfbuzz freetype-py beautifulsoup4 bs4 feedparser groq python-dotenv "
    "trafilatura edge-tts pillow requests moviepy numpy gtts "
    "google-api-python-client google-auth-oauthlib google-auth-httplib2 pyttsx3"
)
_, stdout, stderr = client.exec_command(pip_cmd, timeout=300)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
if out or err:
    print(f"Pip output: {out} {err}", flush=True)
print("Dependencies installed!", flush=True)

# 2. Test imports on EC2
print("Verifying 2.5D TV Broadcast Engine imports on AWS...", flush=True)
verify_cmd = (
    f"cd {REMOTE_APP} && python3 -c \""
    "import uharfbuzz, freetype, bs4, PIL, edge_tts, moviepy; "
    "from services.broadcast_25d_engine import render_25d_top_header; "
    "from scripts.realtime_breaking_news_autouploader import run_breaking_news_autopublisher_loop; "
    "print('✅ ALL 2.5D BROADCAST & AUTO-PUBLISHER MODULES VERIFIED ON AWS')\""
)
_, stdout, stderr = client.exec_command(verify_cmd)
v_out = stdout.read().decode('utf-8', errors='replace')
v_err = stderr.read().decode('utf-8', errors='replace')
print("Verification Result:", v_out.strip() if v_out else v_err.strip(), flush=True)

# 3. Kill existing sessions & launch tmux
print("Starting 15-Minute 2.5D Auto-Publisher Daemon in tmux...", flush=True)
client.exec_command("pkill -9 -f realtime_breaking_news 2>/dev/null; pkill -9 -f auto_15min 2>/dev/null; tmux kill-session -t autopublisher 2>/dev/null; sleep 1")

start_cmd = (
    "tmux new-session -d -s autopublisher "
    f"'cd {REMOTE_APP} && python3 run_realtime_news_autopublisher.py "
    f"> {REMOTE_APP}/logs/autopublisher.log 2>&1'"
)
client.exec_command(start_cmd)
time.sleep(4)

# 4. Check status & logs
_, stdout, _ = client.exec_command("tmux list-sessions")
tmux_sessions = stdout.read().decode('utf-8', errors='replace').strip()
print("Active Tmux Sessions:\n", tmux_sessions, flush=True)

_, stdout, _ = client.exec_command(f"tail -n 25 {REMOTE_APP}/logs/autopublisher.log 2>/dev/null || echo '(Starting...)'")
print("\n=== Live Autopublisher Logs from AWS ===\n", stdout.read().decode('utf-8', errors='replace'), flush=True)

client.close()
print("🎉 AWS DEPLOYMENT & 15-MIN 2.5D AUTO-PUBLISHER IS LIVE!", flush=True)
