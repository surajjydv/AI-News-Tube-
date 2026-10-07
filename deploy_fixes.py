"""
deploy_fixes.py
Push all local fixes to EC2 and restart both daemons fresh.
"""
import sys, time, os
sys.stdout.reconfigure(encoding='utf-8')
import paramiko
from pathlib import Path

KEY_PATH = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
SERVER_IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'
LOCAL_APP = Path(r'C:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_PATH))
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)
sftp = client.open_sftp()
print('Connected to EC2!', flush=True)

# Files to push
files_to_push = [
    ('scripts/realtime_breaking_news_autouploader.py',  'scripts/realtime_breaking_news_autouploader.py'),
    ('scripts/explainer_documentary_engine.py',         'scripts/explainer_documentary_engine.py'),
    ('services/fluent_script_service.py',               'services/fluent_script_service.py'),
    ('services/youtube_upload_service.py',              'services/youtube_upload_service.py'),
    ('services/investigative_explainer_engine.py',      'services/investigative_explainer_engine.py'),
    ('config/settings.py',                              'config/settings.py'),
    ('.env',                                            '.env'),
]

print('\n📤 Pushing updated files to EC2...')
for local_rel, remote_rel in files_to_push:
    local_path = LOCAL_APP / local_rel
    remote_path = f'{REMOTE_APP}/{remote_rel}'
    if local_path.exists():
        sftp.put(str(local_path), remote_path)
        print(f'  ✅ {local_rel}')
    else:
        print(f'  ⚠️  SKIP (not found locally): {local_rel}')

sftp.close()
print('\n📤 All files pushed.\n')

# Kill all old daemons
print('🛑 Killing old daemons...')
kill_cmd = (
    'pkill -9 -f run_realtime_news_autopublisher; '
    'pkill -9 -f explainer_documentary_engine; '
    'tmux kill-session -t autopublisher 2>/dev/null; '
    'tmux kill-session -t doc_autopublisher 2>/dev/null; '
    'sleep 2'
)
_, out, _ = client.exec_command(kill_cmd)
out.channel.recv_exit_status()
time.sleep(3)
print('Old daemons killed.', flush=True)

# Clear old output to free disk + avoid stale cache
print('🧹 Clearing old output files (>7 days)...')
_, out, _ = client.exec_command(f"find {REMOTE_APP}/output -name '*.mp4' -mtime +7 -delete 2>/dev/null; "
                                 f"find {REMOTE_APP}/output -name '*.mp3' -mtime +7 -delete 2>/dev/null; "
                                 f"echo done")
print(out.read().decode('utf-8', errors='replace').strip())

# Start fresh breaking news autopublisher
print('\n🚀 Starting Breaking News Autopublisher...')
start_news = (
    f"tmux new-session -d -s autopublisher "
    f"'cd {REMOTE_APP} && python3 -u run_realtime_news_autopublisher.py >> {REMOTE_APP}/logs/autopublisher.log 2>&1'"
)
_, out, _ = client.exec_command(start_news)
out.channel.recv_exit_status()
time.sleep(3)
print('Breaking news autopublisher started!', flush=True)

# Start fresh documentary engine
print('🚀 Starting Documentary Engine...')
start_doc = (
    f"tmux new-session -d -s doc_autopublisher "
    f"'cd {REMOTE_APP} && python3 -u scripts/explainer_documentary_engine.py >> {REMOTE_APP}/logs/doc_autopublisher.log 2>&1'"
)
_, out, _ = client.exec_command(start_doc)
out.channel.recv_exit_status()
time.sleep(5)
print('Documentary engine started!', flush=True)

# Verify
print('\n=== VERIFICATION ===')
_, out, _ = client.exec_command('tmux list-sessions')
print('Tmux sessions:')
print(out.read().decode('utf-8', errors='replace').strip())

_, out, _ = client.exec_command('pgrep -la python3')
print('\nRunning Python processes:')
print(out.read().decode('utf-8', errors='replace').strip())

time.sleep(10)
_, out, _ = client.exec_command(f'tail -20 {REMOTE_APP}/logs/autopublisher.log')
print('\nAutopublisher log tail (last 20):')
print(out.read().decode('utf-8', errors='replace'))

_, out, _ = client.exec_command(f'tail -10 {REMOTE_APP}/logs/doc_autopublisher.log')
print('\nDoc autopublisher log tail (last 10):')
print(out.read().decode('utf-8', errors='replace'))

client.close()
print('\n✅ Deployment complete. Both daemons running with fixes applied.')
