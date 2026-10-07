import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko
from pathlib import Path

KEY = r'C:\Users\suraj\Downloads\NewsTube.pem'
IP = '98.84.135.236'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(KEY)
client.connect(IP, username='ubuntu', pkey=pkey, timeout=20)

def run(cmd):
    print(f"\n>>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

run("ps -ef | grep ffmpeg")
run("ls -lh /app/AI-NewsTube/videos/")
run("tail -n 25 /app/AI-NewsTube/logs/autopublisher.log")

client.close()
