import sys, os
import paramiko
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEY_FILE = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(KEY_FILE))
client.connect("98.84.135.236", username="ubuntu", pkey=pkey, timeout=15)

print("=== Python Processes on EC2 ===")
_, stdout, _ = client.exec_command("ps aux | grep python3")
print(stdout.read().decode("utf-8", errors="replace"))

print("=== Tmux Sessions ===")
_, stdout, _ = client.exec_command("tmux list-sessions")
print(stdout.read().decode("utf-8", errors="replace"))

print("=== Last 80 Lines of Autopublisher Log ===")
_, stdout, _ = client.exec_command("tail -n 80 /app/AI-NewsTube/logs/autopublisher.log")
print(stdout.read().decode("utf-8", errors="replace"))

client.close()
