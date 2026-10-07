"""
diagnose_crash.py
Check exactly what error kills the autopublisher on startup.
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
client.connect(SERVER_IP, username='ubuntu', pkey=pkey, timeout=25)
print('Connected!\n', flush=True)

# 1. Check tmux pane output for autopublisher session
print('=== TMUX AUTOPUBLISHER PANE (last 50 lines) ===')
_, out, _ = client.exec_command(
    "tmux capture-pane -pt autopublisher -S -50 2>/dev/null || echo 'no output'"
)
print(out.read().decode('utf-8', errors='replace'))

print('\n=== TMUX DOC_AUTOPUBLISHER PANE (last 30 lines) ===')
_, out, _ = client.exec_command(
    "tmux capture-pane -pt doc_autopublisher -S -30 2>/dev/null || echo 'no output'"
)
print(out.read().decode('utf-8', errors='replace'))

# 2. Run autopublisher directly to see the actual crash
print('\n=== DIRECT CRASH TEST (run 10s, capture full stderr) ===')
_, out, err = client.exec_command(
    f"cd {REMOTE_APP} && timeout 10 python3 -u run_realtime_news_autopublisher.py 2>&1 | head -80"
)
out.channel.settimeout(15)
result = out.read().decode('utf-8', errors='replace')
print(result if result else '(no output - crashed before printing anything)')

# 3. Check for import errors
print('\n=== IMPORT CHECK ===')
_, out, _ = client.exec_command(
    f"cd {REMOTE_APP} && python3 -c 'from scripts.realtime_breaking_news_autouploader import run_breaking_news_autopublisher_loop; print(\"IMPORT OK\")' 2>&1"
)
print(out.read().decode('utf-8', errors='replace'))

# 4. Check disk space & available RAM
print('\n=== SYSTEM RESOURCES ===')
_, out, _ = client.exec_command("df -h /app && echo '---' && free -h")
print(out.read().decode('utf-8', errors='replace'))

client.close()
print('Done.')
