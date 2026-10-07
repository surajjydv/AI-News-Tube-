import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('98.84.135.236', username='ubuntu', key_filename=r'C:\Users\suraj\Downloads\NewsTube.pem', timeout=15)

script = """
import sys
sys.path.insert(0, '/app/AI-NewsTube')
from services.youtube_upload_service import upload_video_to_youtube

video_file = '/app/AI-NewsTube/videos/breaking_1787430683_7ce26bfb.mp4'
thumb_file = '/app/AI-NewsTube/thumbnails/thumb_1787430683_7ce26bfb.jpg'

print('Uploading video to YouTube...')
vid = upload_video_to_youtube(
    video_path=video_file,
    title='🔴 LIVE: H1N1 Virus Alert In Delhi - Health Ministry Releases Strict Advisory',
    description='Full investigative ground report on rising H1N1 cases in Delhi and government advisories.\\n\\n#BreakingNews #HindiNews #HealthAlert',
    category_id='25',
    privacy_status='public',
    thumbnail_path=thumb_file,
    tags=['Breaking News', 'H1N1', 'Health News', 'Hindi News', 'NewsTube']
)
print('UPLOAD RESULT VIDEO ID:', vid)
"""

stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{script}\"")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

ssh.close()
