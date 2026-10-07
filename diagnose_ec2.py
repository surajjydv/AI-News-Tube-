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

def run(cmd, timeout=60):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return (o.read().decode(errors='replace') + e.read().decode(errors='replace')).strip()

# 1. Check what ffmpeg version is on the server
print('=== ffmpeg version ===')
print(run('ffmpeg -version 2>&1 | head -3'))

# 2. Check if Panda3D is installed (it's required for rendering)
print('\n=== panda3d installed? ===')
print(run('python3 -c "import panda3d; print(panda3d.__version__)" 2>&1'))

# 3. Test RTMP connection directly (reads key from server .env)
print('\n=== Test RTMP connect to YouTube (5 sec test) ===')
rtmp_test = run(
    'STREAM_KEY=$(grep YOUTUBE_STREAM_KEY ' + REMOTE_APP + '/.env | cut -d= -f2) && '
    'timeout 12 ffmpeg -loglevel warning -f lavfi -i testsrc=size=1280x720:rate=30 '
    '-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 '
    '-c:v libx264 -preset ultrafast -pix_fmt yuv420p '
    '-c:a aac -strict -2 -t 5 '
    '-f flv rtmp://a.rtmp.youtube.com/live2/"$STREAM_KEY" 2>&1 | tail -10',
    timeout=30
)
print(rtmp_test)

# 4. Run stream directly (not in tmux) and capture full crash output
print('\n=== Running stream directly to catch full crash ===')
print(run(
    'cd ' + REMOTE_APP + ' && timeout 30 python3 scripts/continuous_live_stream.py 2>&1 | tail -50',
    timeout=45
))

c.close()
