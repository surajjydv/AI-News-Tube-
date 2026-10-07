import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko, time

KEY        = r'C:\Users\suraj\Downloads\NewsTube.pem'
IP         = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(KEY)
c.connect(IP, username='ubuntu', pkey=pkey, timeout=20)

def run(cmd, timeout=120):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return (o.read().decode(errors='replace') + e.read().decode(errors='replace')).strip()

# --- 1. Server resources
print('=== Server RAM / CPU ===')
print(run('free -m && nproc'))

# --- 2. Upload a test script to EC2
test_script = r"""
import sys, os, subprocess, shutil, time
sys.path.insert(0, '/app/AI-NewsTube')
os.chdir('/app/AI-NewsTube')
from dotenv import load_dotenv
load_dotenv('/app/AI-NewsTube/.env')

from services.rss_service import get_fresh_unseen_news, get_realtime_ticker_headlines
from agents.graphics_agent import render_tv_broadcast_frame
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from pathlib import Path

print('[TEST] Getting news article...')
arts = get_fresh_unseen_news(count=1)
art = arts[0] if arts else None
headline = art.title[:80] if art else 'Breaking News India Today'
category = art.category.upper() if art else 'TOP STORIES'
print(f'[TEST] headline: {headline[:60]}')

print('[TEST] Generating voice...')
sobj = GeneratedScript(topic_title=headline[:60], category=category, script_text=headline, word_count=10)
res = voice_agent(sobj)
audio = Path(res.audio_path) if res.audio_path else None
print(f'[TEST] audio: {audio}')

print('[TEST] Rendering 30 frames...')
tickers = get_realtime_ticker_headlines()
t0 = time.time()
ok = 0
for i in range(30):
    try:
        img = render_tv_broadcast_frame(headline_text=headline, news_photo_path=None, global_t=i/30.0, category=category, ticker_headlines=tickers, photo_paths=[])
        ok += 1
    except Exception as ex:
        print(f'[FRAME ERR] {i}: {ex}')
        break
elapsed = time.time() - t0
print(f'[TEST] {ok}/30 frames in {elapsed:.1f}s ({ok/elapsed:.1f} fps)')

print('[TEST] Building 10s test clip...')
dest = Path('/tmp/test_clip.mp4')
ffmpeg = shutil.which('ffmpeg') or 'ffmpeg'
cmd = [ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-vcodec', 'rawvideo',
       '-s', '1280x720', '-pix_fmt', 'rgb24', '-r', '30', '-i', '-']
if audio and audio.exists():
    cmd += ['-i', str(audio), '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac', '-b:a', '128k', '-shortest']
cmd += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-pix_fmt', 'yuv420p', str(dest)]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    for i in range(300):
        img = render_tv_broadcast_frame(headline_text=headline, news_photo_path=None, global_t=i/30.0, category=category, ticker_headlines=tickers, photo_paths=[])
        proc.stdin.write(img.convert('RGB').tobytes())
    proc.stdin.close()
    proc.wait()
    sz = dest.stat().st_size if dest.exists() else 0
    print(f'[TEST] clip done rc={proc.returncode} size={sz}')
except Exception as ex:
    proc.kill()
    print(f'[CLIP ERR] {ex}')
"""

sftp = c.open_sftp()
with sftp.open('/tmp/ec2_render_test.py', 'w') as f:
    f.write(test_script)
sftp.close()
print('\n=== Running render test on EC2 (may take 1-2 min) ===')
print(run('python3 /tmp/ec2_render_test.py 2>&1', timeout=180))

c.close()
