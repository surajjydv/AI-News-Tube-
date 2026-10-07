"""
reauth_youtube.py
Deletes old token.json on EC2, then runs the OAuth flow on your LOCAL machine
to generate a fresh token for the NEW YouTube channel.
After generating, it uploads the new token.json to EC2.
"""
import sys, webbrowser, json
sys.stdout.reconfigure(encoding='utf-8')
import paramiko
from pathlib import Path

KEY_PATH = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
SERVER_IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'
LOCAL_APP = Path(r'C:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube')

# ─── Step 1: Delete old token on EC2 ────────────────────────────────────────
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_PATH))
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)

_, out, _ = client.exec_command(f'rm -f {REMOTE_APP}/data/token.json && echo DELETED')
result = out.read().decode().strip()
print(f'EC2 old token: {result}', flush=True)
client.close()

# ─── Step 2: Generate fresh token LOCALLY ────────────────────────────────────
print('\n🔑 Generating fresh OAuth token for NEW YouTube channel...')
print('A browser window will open. Sign in with the NEW YouTube account.\n')

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

client_secret = LOCAL_APP / 'client_secret.json'
token_path    = LOCAL_APP / 'data' / 'token.json'
token_path.parent.mkdir(parents=True, exist_ok=True)

flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
creds = flow.run_local_server(port=0, prompt='consent', open_browser=True)

with open(token_path, 'w') as f:
    f.write(creds.to_json())
print(f'\n✅ New token saved locally: {token_path}')

# ─── Step 3: Upload new token to EC2 ─────────────────────────────────────────
print('\n📤 Uploading new token.json to EC2...')
client2 = paramiko.SSHClient()
client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client2.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)
sftp = client2.open_sftp()
sftp.put(str(token_path), f'{REMOTE_APP}/data/token.json')
sftp.close()
print('✅ New token.json uploaded to EC2!')

# ─── Step 4: Verify by calling YouTube API ────────────────────────────────────
print('\n🔍 Verifying new channel access...')
_, out, _ = client2.exec_command(
    f"cd {REMOTE_APP} && python3 -c \""
    f"from services.youtube_upload_service import get_authenticated_service; "
    f"svc = get_authenticated_service(); "
    f"res = svc.channels().list(part='snippet', mine=True).execute(); "
    f"ch = res['items'][0]['snippet']; "
    f"print('Channel:', ch['title'])"
    f"\" 2>&1"
)
out.channel.settimeout(20)
verify = out.read().decode('utf-8', errors='replace')
print(verify)

client2.close()
print('\n🎉 Done! Publishing will now go to the new channel.')
print('Run: python restart_autopublisher.py  to bring daemons back up.')
