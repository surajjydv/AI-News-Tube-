import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('98.84.135.236', username='ubuntu', key_filename=r'C:\Users\suraj\Downloads\NewsTube.pem', timeout=15)

script = """
import subprocess
from pathlib import Path
import sys
sys.path.insert(0, '/app/AI-NewsTube')
from services.youtube_upload_service import upload_video_to_youtube

# 1. Convert video to standard YouTube yuv420p
src_vid = '/app/AI-NewsTube/videos/breaking_1787431248_c6804474.mp4'
dst_vid = '/app/AI-NewsTube/videos/clean_yuv420p.mp4'
thumb_file = '/app/AI-NewsTube/thumbnails/thumb_1787431248_c6804474.jpg'

cmd = ['ffmpeg', '-y', '-i', src_vid, '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-c:a', 'copy', dst_vid]
subprocess.run(cmd, check=True)
print('✅ Successfully transcoded to standard yuv420p MP4!')

# 2. Upload to YouTube
vid = upload_video_to_youtube(
    video_path=dst_vid,
    title='🔴 BREAKING: Canada PM Suspends US Trade Talks | NewsTube Alert',
    description='Special Investigative Broadcast Report: Canada suspends bilateral trade talks with the US.\\n\\n#BreakingNews #Canada #WorldNews #NewsTube',
    category_id='25',
    privacy_status='public',
    thumbnail_path=thumb_file,
    tags=['Canada', 'US Trade', 'Breaking News', 'World News', 'NewsTube']
)
print('NEW YOUTUBE VIDEO ID:', vid)
"""

stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{script}\"")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

ssh.close()
