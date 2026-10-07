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

print('Step 1: Creating 2GB Swap space on EC2 to prevent OOM kills...')
swap_cmds = (
    "sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 && "
    "sudo chmod 600 /swapfile && "
    "sudo mkswap /swapfile && "
    "sudo swapon /swapfile 2>/dev/null || true"
)
print(run(swap_cmds))

print('Step 2: Uploading updated continuous_live_stream.py...')
sftp = c.open_sftp()
sftp.put(r'c:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube\scripts\continuous_live_stream.py',
         f'{REMOTE_APP}/scripts/continuous_live_stream.py')
sftp.close()
print('[OK] Code uploaded')

print('Step 3: Stopping old processes...')
run('pkill -f continuous_live_stream 2>/dev/null; tmux kill-session -t livestream 2>/dev/null; sleep 3')

print('Step 4: Starting fresh live stream in tmux...')
start_cmd = (
    'tmux new-session -d -s livestream '
    '"cd ' + REMOTE_APP + ' '
    '&& python3 scripts/continuous_live_stream.py '
    '> ' + REMOTE_APP + '/logs/stream.log 2>&1"'
)
run(start_cmd)
time.sleep(6)

print()
print('=== Memory & Swap status ===')
print(run('free -m'))

print()
print('=== tmux sessions ===')
print(run('tmux list-sessions 2>&1'))

print()
print('=== Python processes ===')
print(run('pgrep -a python3 2>&1'))

print()
print('=== Stream log (first 15 lines) ===')
print(run(f'tail -15 {REMOTE_APP}/logs/stream.log 2>/dev/null'))

c.close()
print('\n[SUCCESS] EC2 Swap setup done & 24/7 stream restarted!')
