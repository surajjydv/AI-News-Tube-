"""
push_hotfix.py
Hot-push only the 2 fixed files to EC2 without restarting daemons.
Running daemons pick up changes on their NEXT cycle automatically.
"""
import sys
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
print('Connected!\n', flush=True)

hotfix_files = [
    ('services/investigative_explainer_engine.py', 'services/investigative_explainer_engine.py'),
    ('scripts/realtime_breaking_news_autouploader.py', 'scripts/realtime_breaking_news_autouploader.py'),
]

print('📤 Pushing hotfix files...')
for local_rel, remote_rel in hotfix_files:
    local_path = LOCAL_APP / local_rel
    remote_path = f'{REMOTE_APP}/{remote_rel}'
    sftp.put(str(local_path), remote_path)
    print(f'  ✅ {local_rel}')

sftp.close()
print('\n✅ Hotfix pushed. Running daemons will pick up changes on next cycle.')

# Show current process status
_, out, _ = client.exec_command('pgrep -la python3')
print('\nActive processes:', out.read().decode('utf-8', errors='replace').strip())

client.close()
