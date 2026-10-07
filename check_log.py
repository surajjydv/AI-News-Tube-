import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import paramiko

KEY = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("98.84.135.236", username="ubuntu", pkey=paramiko.RSAKey.from_private_key_file(str(KEY)), timeout=15)

s, o, e = c.exec_command("tail -n 25 /tmp/video_gen.log")
log_content = o.read().decode("utf-8", errors="replace")
print("=== LOG TAIL ===")
print(log_content.strip())

s, o, e = c.exec_command("ps -eo pid,%cpu,%mem,time,cmd | grep ffmpeg | grep -v grep")
ff_proc = o.read().decode("utf-8", errors="replace").strip()
print("\n=== FFMPEG ===")
print(ff_proc if ff_proc else "FFmpeg idle/not running")

s, o, e = c.exec_command("ls -lh /app/AI-NewsTube/output/test_cinematic* 2>/dev/null")
files = o.read().decode("utf-8", errors="replace").strip()
print("\n=== OUTPUT FILES ===")
print(files if files else "No test output files yet")

c.close()
