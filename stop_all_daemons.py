"""
stop_all_daemons.py
Kills all publishing daemons on EC2. Run this before making changes.
"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
import paramiko
from pathlib import Path

KEY_PATH = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
SERVER_IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_PATH))
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)
print('Connected!', flush=True)

stop_cmd = (
    "pkill -9 -f run_realtime_news_autopublisher; "
    "pkill -9 -f explainer_documentary_engine; "
    "pkill -9 -f us_investigative_autopublisher; "
    "tmux kill-session -t autopublisher; "
    "tmux kill-session -t doc_autopublisher; "
    "echo STOPPED"
)
_, out, _ = client.exec_command(stop_cmd)
out.channel.recv_exit_status()
time.sleep(2)
print('All daemons killed.', flush=True)

_, out, _ = client.exec_command('tmux list-sessions 2>/dev/null || echo "No tmux sessions running"')
print('Tmux sessions:', out.read().decode('utf-8', errors='replace').strip())

_, out, _ = client.exec_command('pgrep -la python3 2>/dev/null || echo "No python3 processes"')
print('Python processes:', out.read().decode('utf-8', errors='replace').strip())

client.close()
print('\nAll publishing stopped. Safe to make changes.')
