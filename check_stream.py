import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

KEY        = r'C:\Users\suraj\Downloads\NewsTube.pem'
IP         = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(KEY)
c.connect(IP, username='ubuntu', pkey=pkey, timeout=20)

def run(cmd):
    _, o, e = c.exec_command(cmd, timeout=60)
    o.channel.recv_exit_status()
    return o.read().decode(errors='replace') + e.read().decode(errors='replace')

print('=== tmux/process status ===')
print(run('tmux list-sessions 2>&1'))
print(run('pgrep -a python3 2>&1'))
print(run('pgrep -a ffmpeg 2>&1 | head -5'))

print('\n=== .env on server ===')
print(run('cat ' + REMOTE_APP + '/.env'))

print('\n=== RTMP errors in log ===')
print(run('grep -i "rtmp\\|error\\|fail\\|connect\\|flv\\|stream_key\\|smk0" ' + REMOTE_APP + '/logs/stream.log 2>/dev/null | tail -40'))

print('\n=== last 50 log lines ===')
print(run('tail -50 ' + REMOTE_APP + '/logs/stream.log 2>/dev/null'))

c.close()
