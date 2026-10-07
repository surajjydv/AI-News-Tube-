"""
debug_autopublisher_crash.py
Checks the exact crash reason by running autopublisher in foreground briefly.
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

# Run the script for 15 seconds and capture all output
test_cmd = (
    f"cd {REMOTE_APP} && timeout 15 python3 -u run_realtime_news_autopublisher.py 2>&1 | head -60"
)
_, out, _ = client.exec_command(test_cmd)
out.channel.settimeout(20)
result = out.read().decode('utf-8', errors='replace')
print('=== STARTUP OUTPUT (first 60 lines) ===')
print(result)

# Also check stderr from last crash attempt in the log
_, out, _ = client.exec_command(f'wc -l {REMOTE_APP}/logs/autopublisher.log')
print('\nAutopublisher log line count:', out.read().decode().strip())

# Check disk space
_, out, _ = client.exec_command('df -h /app')
print('\nDisk space:', out.read().decode('utf-8', errors='replace'))

client.close()
print('Done.')
