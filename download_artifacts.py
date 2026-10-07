import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import paramiko

KEY = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("98.84.135.236", username="ubuntu", pkey=paramiko.RSAKey.from_private_key_file(str(KEY)), timeout=25)

# Extract frames from the final completed 107MB video
script = """
FF=/home/ubuntu/.local/lib/python3.14/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
$FF -y -ss 00:00:10 -i /app/AI-NewsTube/output/test_cinematic_1788728317.mp4 -frames:v 1 /app/AI-NewsTube/output/sample_frame_10s.jpg
$FF -y -ss 00:00:45 -i /app/AI-NewsTube/output/test_cinematic_1788728317.mp4 -frames:v 1 /app/AI-NewsTube/output/sample_frame_45s.jpg
$FF -y -ss 00:01:20 -i /app/AI-NewsTube/output/test_cinematic_1788728317.mp4 -frames:v 1 /app/AI-NewsTube/output/sample_frame_80s.jpg
ls -lh /app/AI-NewsTube/output/sample_frame*.jpg
"""
s, o, e = c.exec_command(script)
print("EXTRACT OUTPUT:")
print(o.read().decode("utf-8", errors="replace"))

sftp = c.open_sftp()
local_dir = Path(r"C:\Users\suraj\.gemini\antigravity-ide\brain\2dd3bff8-6b59-4389-82bc-da16357d38ce")

to_download = [
    ("test_cinematic_1788728317.jpg", "thumbnail.jpg"),
    ("sample_frame_10s.jpg", "frame_10s.jpg"),
    ("sample_frame_45s.jpg", "frame_45s.jpg"),
    ("sample_frame_80s.jpg", "frame_80s.jpg")
]

for remote_name, local_name in to_download:
    remote_p = f"/app/AI-NewsTube/output/{remote_name}"
    local_p = local_dir / local_name
    try:
        sftp.get(remote_p, str(local_p))
        print(f"Downloaded: {local_name} ({local_p.stat().st_size // 1024} KB)")
    except Exception as ex:
        print(f"Failed to download {remote_name}: {ex}")

sftp.close()
c.close()
print("All artifacts downloaded successfully!")
