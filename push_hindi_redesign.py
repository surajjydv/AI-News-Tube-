"""push_hindi_redesign.py — Push all Hindi + thumbnail changes to EC2"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko
from pathlib import Path

KEY_PATH = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
SERVER_IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'
LOCAL_APP  = Path(r'C:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_PATH))
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)
sftp = client.open_sftp()
print('Connected!\n', flush=True)

files = [
    'config/settings.py',
    '.env',
    'services/fluent_script_service.py',
    'services/ai_thumbnail_service.py',
]

print('📤 Pushing Hindi + thumbnail redesign...')
for f in files:
    sftp.put(str(LOCAL_APP / f), f'{REMOTE_APP}/{f}')
    print(f'  ✅ {f}')

sftp.close()
client.close()
print('\n✅ All changes live on EC2.')
print('Run restart_autopublisher.py when you are ready to start posting.')
