import sys, time
from pathlib import Path
import paramiko

KEY = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("98.84.135.236", username="ubuntu", pkey=paramiko.RSAKey.from_private_key_file(str(KEY)), timeout=30)

sftp = c.open_sftp()
local_script = Path(r"C:\Users\suraj\Downloads\AI-NewsTube-upgraded (1)\AI-NewsTube\test_generate_one_video.py")
sftp.put(str(local_script), "/app/AI-NewsTube/test_generate_one_video.py")
sftp.close()
print("Uploaded test_generate_one_video.py")

# Launch detached in background
cmd = "cd /app/AI-NewsTube && nohup python3 -u test_generate_one_video.py > /tmp/video_gen.log 2>&1 &"
c.exec_command(cmd)
time.sleep(2)
print("Started detached video generation in background. Monitoring /tmp/video_gen.log...")

c.close()
