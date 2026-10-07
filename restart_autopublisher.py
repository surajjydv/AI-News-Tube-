"""
restart_autopublisher.py
Force-restarts the breaking news autopublisher daemon on EC2.
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
print('Connected to EC2!', flush=True)

# Step 1: Kill old stale process
kill_cmd = "pkill -9 -f run_realtime_news_autopublisher; tmux kill-session -t autopublisher; sleep 2"
_, out, err = client.exec_command(kill_cmd)
out.channel.recv_exit_status()
time.sleep(3)
print('Old session killed.', flush=True)

# Step 2: Start fresh tmux session
start_cmd = (
    f"tmux new-session -d -s autopublisher "
    f"'cd {REMOTE_APP} && python3 -u run_realtime_news_autopublisher.py "
    f">> {REMOTE_APP}/logs/autopublisher.log 2>&1'"
)
_, out, err = client.exec_command(start_cmd)
out.channel.recv_exit_status()
time.sleep(4)
print('Fresh autopublisher started!', flush=True)

# Step 3: Verify
_, out, _ = client.exec_command('pgrep -la python3')
print('\n=== Running Python processes ===')
print(out.read().decode('utf-8', errors='replace'))

_, out, _ = client.exec_command('tmux list-sessions')
print('\n=== Tmux sessions ===')
print(out.read().decode('utf-8', errors='replace'))

time.sleep(6)
_, out, _ = client.exec_command(f'tail -n 20 {REMOTE_APP}/logs/autopublisher.log')
print('\n=== Latest autopublisher log ===')
print(out.read().decode('utf-8', errors='replace'))

client.close()
print('\nDone.')
