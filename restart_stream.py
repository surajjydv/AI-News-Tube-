import sys
import os
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko, time

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

KEY            = os.getenv("SSH_PEM_KEY_PATH", r'C:\Users\suraj\Downloads\NewsTube.pem')
IP             = os.getenv("EC2_HOST", '98.84.135.236')
NEW_STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
REMOTE_APP     = '/app/AI-NewsTube'

if not GROQ_API_KEY or not NEW_STREAM_KEY:
    print("❌ ERROR: GROQ_API_KEY and YOUTUBE_STREAM_KEY must be set in .env before running restart_stream.py!")
    sys.exit(1)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(KEY)
c.connect(IP, username='ubuntu', pkey=pkey, timeout=20)

def run(cmd, show=True):
    _, o, e = c.exec_command(cmd, timeout=60)
    o.channel.recv_exit_status()
    out = o.read().decode(errors='replace') + e.read().decode(errors='replace')
    if show and out.strip():
        print(out.strip())
    return out

# 1. Write new .env
print('Step 1: Writing new .env with updated stream key...')
env_lines = [
    'CHANNEL_NAME=NewsTube',
    'GROQ_API_KEY=' + GROQ_API_KEY,
    'YOUTUBE_STREAM_KEY=' + NEW_STREAM_KEY,
    'DEFAULT_TTS_VOICE=hi-IN-SwaraNeural',
    'GROQ_ORPHEUS_ENABLED=false',
    'LIVE_STREAM_FPS=30',
    'LIVE_VIDEO_BITRATE=4500k',
]
sftp = c.open_sftp()
with sftp.open(REMOTE_APP + '/.env', 'w') as f:
    f.write('\n'.join(env_lines) + '\n')
sftp.close()
print('[OK] .env updated on server')

# 2. Stop old stream
print('Step 2: Stopping old stream...')
run('pkill -f continuous_live_stream 2>/dev/null; tmux kill-session -t livestream 2>/dev/null; sleep 3')

# 3. Reset seen-news cache
print('Step 3: Resetting seen-news cache...')
sftp = c.open_sftp()
with sftp.open(REMOTE_APP + '/data/seen_news.json', 'w') as f:
    f.write('{"titles":[],"hashes":[]}')
sftp.close()
print('[OK] Cache reset')

# 4. Start fresh stream in tmux
print('Step 4: Starting fresh stream with new YouTube key...')
start_cmd = (
    'tmux new-session -d -s livestream '
    '"cd ' + REMOTE_APP + ' '
    '&& python3 scripts/continuous_live_stream.py '
    '> ' + REMOTE_APP + '/logs/stream.log 2>&1"'
)
run(start_cmd, show=False)
time.sleep(10)

# 5. Verify
print()
print('=== tmux sessions ===')
run('tmux list-sessions 2>&1')
print('=== python processes ===')
run('pgrep -a python3 2>&1')
print('=== last 20 log lines ===')
run('tail -20 ' + REMOTE_APP + '/logs/stream.log 2>/dev/null')

c.close()
print()
print('[DONE] Stream restarted cleanly.')

