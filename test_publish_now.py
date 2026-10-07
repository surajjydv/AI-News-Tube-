import sys
import paramiko
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key_path = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.RSAKey.from_private_key_file(str(key_path))
ssh.connect("98.84.135.236", username="ubuntu", pkey=pkey, timeout=20)

script = """
import sys, glob, os
sys.path.insert(0, '/app/AI-NewsTube')
from services.youtube_upload_service import upload_video_to_youtube

video_files = sorted(glob.glob('/app/AI-NewsTube/videos/breaking_*.mp4'), key=os.path.getmtime, reverse=True)
if not video_files:
    print('No breaking video found!')
    sys.exit(1)

latest_video = video_files[0]
vid_basename = os.path.basename(latest_video).replace('breaking_', 'thumb_').replace('.mp4', '.jpg')
thumb_file = os.path.join('/app/AI-NewsTube/thumbnails', vid_basename)

print(f'🚀 Direct Uploading Latest Video to YouTube: {latest_video}')
vid = upload_video_to_youtube(
    video_path=latest_video,
    title='SpaceX Launches 27 Starlink Satellites | 100th Falcon Mission 🔴 बड़ी ख़बर',
    description='🔴 SpaceX Launches 27 Starlink Satellites on 100th Falcon Mission of 2026\\n\\n📌 ग्राउंड रिपोर्ट एवं मुख्य बिंदु:\\n• SpaceX ने फ्लोरिडा से 27 नए स्टारलिंक उपग्रहों को सफलतापूर्वक कक्षा में स्थापित किया\\n• इस वर्ष का 100वां सफल फाल्कन-9 मिशन पूरा\\n• वैश्विक ब्रॉडबैंड इंटरनेट नेटवर्क में नया विस्तार\\n\\n#SpaceX #Starlink #Falcon9 #BreakingNews #HindiNews #NewsTube',
    category_id='25',
    privacy_status='public',
    thumbnail_path=thumb_file if os.path.exists(thumb_file) else None,
    tags=['SpaceX', 'Starlink', 'Falcon 9', 'Elon Musk', 'Breaking News', 'Science News', 'NewsTube']
)
print('YOUTUBE VIDEO ID:', vid)
"""

stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{script}\"")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

ssh.close()

