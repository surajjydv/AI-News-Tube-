import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('98.84.135.236', username='ubuntu', key_filename=r'C:\Users\suraj\Downloads\NewsTube.pem', timeout=15)

script = """
import sys
sys.path.insert(0, '/app/AI-NewsTube')
from services.youtube_upload_service import upload_video_to_youtube, get_authenticated_service

try:
    print('Testing YouTube Auth on EC2...')
    srv = get_authenticated_service()
    if srv:
        print('YouTube Auth: SUCCESS!')
    else:
        print('YouTube Auth: RETURNED NONE')
except Exception as e:
    print('YouTube Auth Error:', e)
"""

stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{script}\"")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

ssh.close()
