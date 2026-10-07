import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko
from pathlib import Path

KEY = r'C:\Users\suraj\Downloads\NewsTube.pem'
IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(KEY)
client.connect(IP, username='ubuntu', pkey=pkey, timeout=20)

def run(cmd, timeout=60):
    print(f"\n>>> CMD: {cmd}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out.strip())
    if err:
        print("ERR: " + err.strip())

run("tmux list-sessions")
run("ps aux | grep python3")
run("cat /app/AI-NewsTube/.env | grep -E 'CHANNEL|GROQ|STREAM'")
run("python3 -c \"import sys; sys.path.append('/app/AI-NewsTube'); from services.groq_service import generate_text; print('Groq test:', generate_text('hello')[:50])\"")
run("python3 -c \"import sys; sys.path.append('/app/AI-NewsTube'); from services.youtube_upload_service import get_authenticated_service; print('YT Auth test:', get_authenticated_service())\"")
run("python3 -c \"import sys; sys.path.append('/app/AI-NewsTube'); from services.rss_service import fetch_news; items = fetch_news(); print(f'Fetched {len(items)} news items')\"")

client.close()
