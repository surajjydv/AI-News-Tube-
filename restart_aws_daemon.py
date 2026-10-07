import os, sys, time
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

# Copy updated files to EC2
sftp = client.open_sftp()
sftp.put(str(BASE_DIR / ".env"), f"{REMOTE_APP}/.env")
sftp.put(str(BASE_DIR / "config" / "settings.py"), f"{REMOTE_APP}/config/settings.py")
sftp.put(str(BASE_DIR / "services" / "broadcast_25d_engine.py"), f"{REMOTE_APP}/services/broadcast_25d_engine.py")
sftp.put(str(BASE_DIR / "services" / "dynamic_broadcast_renderer.py"), f"{REMOTE_APP}/services/dynamic_broadcast_renderer.py")
sftp.put(str(BASE_DIR / "services" / "shorts_25d_renderer.py"), f"{REMOTE_APP}/services/shorts_25d_renderer.py")
sftp.put(str(BASE_DIR / "services" / "fluent_script_service.py"), f"{REMOTE_APP}/services/fluent_script_service.py")
sftp.put(str(BASE_DIR / "services" / "groq_service.py"), f"{REMOTE_APP}/services/groq_service.py")
sftp.put(str(BASE_DIR / "services" / "visual_asset_manager.py"), f"{REMOTE_APP}/services/visual_asset_manager.py")
sftp.put(str(BASE_DIR / "services" / "audio_manager.py"), f"{REMOTE_APP}/services/audio_manager.py")
sftp.put(str(BASE_DIR / "services" / "ai_thumbnail_service.py"), f"{REMOTE_APP}/services/ai_thumbnail_service.py")
sftp.put(str(BASE_DIR / "scripts" / "realtime_breaking_news_autouploader.py"), f"{REMOTE_APP}/scripts/realtime_breaking_news_autouploader.py")
sftp.put(str(BASE_DIR / "generate_and_publish_2min_video.py"), f"{REMOTE_APP}/generate_and_publish_2min_video.py")
sftp.put(str(BASE_DIR / "generate_and_upload_5min_story.py"), f"{REMOTE_APP}/generate_and_upload_5min_story.py")
sftp.put(str(BASE_DIR / "utils" / "json_utils.py"), f"{REMOTE_APP}/utils/json_utils.py")
sftp.put(str(BASE_DIR / "services" / "cinematic_story_renderer.py"), f"{REMOTE_APP}/services/cinematic_story_renderer.py")
sftp.put(str(BASE_DIR / "services" / "youtube_upload_service.py"), f"{REMOTE_APP}/services/youtube_upload_service.py")
if (BASE_DIR / "data" / "token.json").exists():
    sftp.put(str(BASE_DIR / "data" / "token.json"), f"{REMOTE_APP}/data/token.json")
sftp.close()

print("Uploaded latest 2.5D graphics engine and services to EC2!", flush=True)

# Stop old processes, reclaim RAM, and reset cache
client.exec_command(f"rm -f {REMOTE_APP}/data/llm_cache.json; pkill -9 -f run_realtime_news_autopublisher; pkill -9 -f realtime_breaking_news; pkill -9 -f us_investigative_autopublisher; tmux kill-session -t autopublisher 2>/dev/null; tmux kill-session -t explainer_daemon 2>/dev/null; tmux kill-session -t trending_publisher 2>/dev/null; sleep 2")
time.sleep(3)

print("Starting updated 15-minute 2.5D auto-publisher on AWS EC2 in tmux...", flush=True)
client.exec_command(f"tmux new-session -d -s autopublisher 'cd {REMOTE_APP} && python3 -u run_realtime_news_autopublisher.py >> {REMOTE_APP}/logs/autopublisher.log 2>&1'")
time.sleep(3)


_, stdout, _ = client.exec_command("tmux list-sessions")
print("Active Tmux Sessions:\n", stdout.read().decode('utf-8', errors='replace').strip(), flush=True)

_, stdout, _ = client.exec_command(f"tail -n 25 {REMOTE_APP}/logs/autopublisher.log 2>/dev/null || echo '(Starting...)'")
print("\n=== Live Autopublisher Logs from AWS ===\n", stdout.read().decode('utf-8', errors='replace'), flush=True)

client.close()
print("🎉 UPGRADED ENGINE IS LIVE ON AWS!", flush=True)
