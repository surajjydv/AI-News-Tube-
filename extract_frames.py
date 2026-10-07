import sys, os
from pathlib import Path
import paramiko

KEY = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("98.84.135.236", username="ubuntu", pkey=paramiko.RSAKey.from_private_key_file(str(KEY)), timeout=30)

s, o, e = c.exec_command("python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'")
ffmpeg_bin = o.read().decode("utf-8").strip()
print(f"FFmpeg binary: {ffmpeg_bin}")

commands = [
    f"{ffmpeg_bin} -y -ss 00:00:10 -i /app/AI-NewsTube/output/test_cinematic_1788727337.mp4 -frames:v 1 /app/AI-NewsTube/output/frame_10s.jpg",
    f"{ffmpeg_bin} -y -ss 00:00:45 -i /app/AI-NewsTube/output/test_cinematic_1788727337.mp4 -frames:v 1 /app/AI-NewsTube/output/frame_45s.jpg",
    f"{ffmpeg_bin} -y -ss 00:01:30 -i /app/AI-NewsTube/output/test_cinematic_1788727337.mp4 -frames:v 1 /app/AI-NewsTube/output/frame_90s.jpg",
    "ls -lh /app/AI-NewsTube/output/frame*.jpg"
]

for cmd in commands:
    s, o, e = c.exec_command(cmd)
    res = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    if res.strip():
        print("STDOUT:", res.strip())
    if err.strip():
        print("STDERR TAIL:", err.strip()[-300:])

sftp = c.open_sftp()
local_dir = Path(r"C:\Users\suraj\.gemini\antigravity-ide\brain\2dd3bff8-6b59-4389-82bc-da16357d38ce")
for frame_name in ["frame_10s.jpg", "frame_45s.jpg", "frame_90s.jpg"]:
    remote_path = f"/app/AI-NewsTube/output/{frame_name}"
    local_path = local_dir / frame_name
    try:
        sftp.get(remote_path, str(local_path))
        print(f"Downloaded {frame_name} ({local_path.stat().st_size} bytes)")
    except Exception as ex:
        print(f"Failed to get {frame_name}: {ex}")

sftp.close()
c.close()
print("All frames downloaded successfully!")
