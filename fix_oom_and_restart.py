"""
fix_oom_and_restart.py
Kills stale OOM-causing process, expands swap, then restarts both daemons cleanly.
"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
import paramiko
from pathlib import Path

KEY_PATH = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
SERVER_IP = '98.84.135.236'
REMOTE_APP = '/app/AI-NewsTube'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_PATH))
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=30)
print('Connected!\n', flush=True)

def run(cmd, label=''):
    _, out, err = client.exec_command(cmd)
    out.channel.recv_exit_status()
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    if label:
        print(f'[{label}] {o or e or "done"}', flush=True)
    return o

# Step 1: Kill ALL python3 processes (including stale PID 481343)
print('🛑 Step 1: Kill all stale Python + tmux sessions...')
run('pkill -9 python3; sleep 2', 'kill python3')
run('tmux kill-server 2>/dev/null; sleep 1', 'kill tmux')

# Step 2: Free memory - clear caches
print('\n🧹 Step 2: Free system memory...')
run('sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true', 'drop caches')

# Step 3: Expand swap to 4GB if less than 3GB
print('\n💾 Step 3: Check and expand swap...')
swap_info = run("free -m | grep Swap | awk '{print $2}'")
swap_mb = int(swap_info.strip()) if swap_info.strip().isdigit() else 0
print(f'Current swap: {swap_mb}MB', flush=True)

if swap_mb < 3000:
    print('Expanding swap to 4GB...', flush=True)
    swap_cmds = [
        'swapoff -a',
        'dd if=/dev/zero of=/swapfile bs=1M count=4096 2>/dev/null',
        'chmod 600 /swapfile',
        'mkswap /swapfile',
        'swapon /swapfile',
    ]
    for cmd in swap_cmds:
        run(cmd, cmd[:30])
    print('Swap expanded to 4GB!', flush=True)
else:
    print(f'Swap OK ({swap_mb}MB), skipping expansion.', flush=True)

# Step 4: Clear old output files to free disk
print('\n🗑️  Step 4: Purge old output files...')
run(f"find {REMOTE_APP}/output -name '*.mp4' -mtime +5 -delete 2>/dev/null; echo done", 'purge mp4')
run(f"find {REMOTE_APP}/output -name '*.mp3' -mtime +5 -delete 2>/dev/null; echo done", 'purge mp3')
run(f"find {REMOTE_APP}/output -type d -empty -delete 2>/dev/null; echo done", 'purge empty dirs')

# Show memory after cleanup
mem = run("free -h | grep -E 'Mem|Swap'")
print(f'\nMemory after cleanup:\n{mem}')

time.sleep(3)

# Step 5: Start Breaking News Autopublisher
print('\n🚀 Step 5: Start Breaking News Autopublisher...')
run(
    f"tmux new-session -d -s autopublisher "
    f"'cd {REMOTE_APP} && python3 -u run_realtime_news_autopublisher.py >> {REMOTE_APP}/logs/autopublisher.log 2>&1'",
    'start autopublisher'
)
time.sleep(6)

# Step 6: Start Documentary Engine  
print('🚀 Step 6: Start Documentary Engine...')
run(
    f"tmux new-session -d -s doc_autopublisher "
    f"'cd {REMOTE_APP} && python3 -u scripts/explainer_documentary_engine.py >> {REMOTE_APP}/logs/doc_autopublisher.log 2>&1'",
    'start doc engine'
)
time.sleep(8)

# Step 7: Verify
print('\n=== VERIFICATION ===')
procs = run('pgrep -la python3')
print(f'Python processes:\n{procs if procs else "NONE - checking tmux..."}')

sessions = run('tmux list-sessions')
print(f'\nTmux sessions:\n{sessions}')

mem_final = run("free -h")
print(f'\nFinal memory state:\n{mem_final}')

# Show fresh log lines
time.sleep(10)
print('\n=== AUTOPUBLISHER LOG (last 15 lines) ===')
log = run(f'tail -15 {REMOTE_APP}/logs/autopublisher.log')
print(log)

print('\n=== DOC LOG (last 10 lines) ===')
dlog = run(f'tail -10 {REMOTE_APP}/logs/doc_autopublisher.log')
print(dlog)

client.close()
print('\n✅ Done.')
