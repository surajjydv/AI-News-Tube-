"""
audit_errors.py
Full error audit - pulls all ERROR/WARNING lines from EC2 logs + checks key pipeline health.
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

checks = {
    "AUTOPUBLISHER - All ERRORs": f"grep -i 'error\\|ERROR\\|exception\\|traceback\\|failed\\|FAILED' {REMOTE_APP}/logs/autopublisher.log | tail -80",
    "DOC AUTOPUBLISHER - All ERRORs": f"grep -i 'error\\|ERROR\\|exception\\|traceback\\|failed\\|FAILED' {REMOTE_APP}/logs/doc_autopublisher.log | tail -80",
    "AUTOPUBLISHER - Last 100 lines": f"tail -100 {REMOTE_APP}/logs/autopublisher.log",
    "DOC AUTOPUBLISHER - Last 50 lines": f"tail -50 {REMOTE_APP}/logs/doc_autopublisher.log",
    "DISK SPACE": "df -h /app",
    "MEMORY": "free -h",
    "ENV FILE": f"cat {REMOTE_APP}/.env | grep -v 'KEY\\|SECRET\\|TOKEN'",
}

for label, cmd in checks.items():
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    _, out, _ = client.exec_command(cmd + " 2>/dev/null || echo '(no output)'")
    print(out.read().decode('utf-8', errors='replace'))

client.close()
print('\nAudit complete.')
