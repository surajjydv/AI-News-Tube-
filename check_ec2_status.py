import paramiko
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key_path = Path(r'C:\Users\suraj\Downloads\NewsTube.pem')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(key_path))
client.connect('98.84.135.236', username='ubuntu', pkey=pkey, timeout=10)

stdin, stdout, stderr = client.exec_command('ps aux | grep python3')
print("=== Python Processes on EC2 ===")
print(stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command('tmux list-sessions')
print("=== Tmux Sessions ===")
print(stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command('tail -n 30 /app/AI-NewsTube/logs/autopublisher.log 2>/dev/null || echo "(No log yet)"')
print("=== Autopublisher Logs ===")
print(stdout.read().decode('utf-8', errors='replace'))

client.close()
