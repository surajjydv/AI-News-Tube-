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

def run(cmd, timeout=60):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return (o.read().decode(errors='replace') + e.read().decode(errors='replace')).strip()

# Check which packages are missing
print('=== Checking key imports ===')
checks = [
    'moviepy',
    'PIL',
    'feedparser',
    'groq',
    'edge_tts',
    'gtts',
    'trafilatura',
    'numpy',
    'requests',
]
for pkg in checks:
    result = run(f'python3 -c "import {pkg}; print(\\"{pkg} OK\\")" 2>&1')
    print(result)

print()
print('=== Install missing packages ===')
r = run(
    'pip3 install --quiet --break-system-packages moviepy numpy pillow 2>&1 | tail -5',
    timeout=120
)
print(r)

print()
print('=== Test graphics_agent import ===')
print(run('cd ' + REMOTE_APP + ' && python3 -c "from agents.graphics_agent import render_tv_broadcast_frame; print(\'graphics_agent OK\')" 2>&1'))

print()
print('=== Test broadcast_enhancements import ===')
print(run('cd ' + REMOTE_APP + ' && python3 -c "from agents.broadcast_enhancements import DualAnchorVoice; print(\'enhancements OK\')" 2>&1'))

c.close()
