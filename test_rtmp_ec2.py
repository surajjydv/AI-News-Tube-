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

test_cmd = (
    "python3 -c \""
    "import os, subprocess; "
    "from dotenv import load_dotenv; "
    "load_dotenv('/app/AI-NewsTube/.env'); "
    "k = os.getenv('YOUTUBE_STREAM_KEY'); "
    "cmd = ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=640x360:rate=15', "
    "'-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', "
    "'-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-strict', '-2', '-t', '3', "
    "'-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{k}']; "
    "res = subprocess.run(cmd, capture_output=True, text=True); "
    "print('RETURNCODE:', res.returncode); "
    "print('STDERR:', res.stderr); "
    "\""
)

_, stdout, stderr = client.exec_command(test_cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))
client.close()
