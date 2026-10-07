"""
get_auth_url.py
Prints the Google OAuth URL — copy and open it manually in your browser.
After authorizing, paste the redirect URL back here.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

LOCAL_APP = Path(r'C:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube')
client_secret = LOCAL_APP / 'client_secret.json'

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

flow = InstalledAppFlow.from_client_secrets_file(
    str(client_secret),
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # No localhost needed - shows code in browser
)

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

print("=" * 70)
print("STEP 1: Open this URL in your browser (sign in with NEW YouTube account):")
print("=" * 70)
print(auth_url)
print("=" * 70)
print("\nSTEP 2: After signing in and clicking Allow,")
print("copy the authorization CODE shown in the browser")
print("and paste it below when prompted.\n")

code = input("Paste the authorization code here: ").strip()

flow.fetch_token(code=code)
creds = flow.credentials

token_path = LOCAL_APP / 'data' / 'token.json'
token_path.parent.mkdir(parents=True, exist_ok=True)
with open(token_path, 'w') as f:
    f.write(creds.to_json())
print(f'\n✅ token.json saved locally: {token_path}')

# Upload to EC2
print('\n📤 Uploading new token.json to EC2...')
import paramiko
KEY_PATH = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
SERVER_IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_PATH))
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)
sftp = client.open_sftp()
sftp.put(str(token_path), f'{REMOTE_APP}/data/token.json')
sftp.close()

# Verify
print('Verifying new channel on EC2...')
_, out, _ = client.exec_command(
    f"cd {REMOTE_APP} && python3 -c \""
    "from services.youtube_upload_service import get_authenticated_service; "
    "svc = get_authenticated_service(); "
    "res = svc.channels().list(part='snippet', mine=True).execute(); "
    "ch = res['items'][0]['snippet']; "
    "print('NEW CHANNEL:', ch['title'])"
    "\" 2>&1"
)
out.channel.settimeout(20)
print(out.read().decode('utf-8', errors='replace'))
client.close()

print('\n🎉 Done! All videos will now publish to the new channel.')
