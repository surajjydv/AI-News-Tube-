import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import paramiko

KEY = Path(r"C:\Users\suraj\Downloads\NewsTube.pem")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("98.84.135.236", username="ubuntu", pkey=paramiko.RSAKey.from_private_key_file(str(KEY)), timeout=25)

cmd = 'cd /app/AI-NewsTube && python3 -c "from services.ai_thumbnail_service import create_real_event_youtube_thumbnail; create_real_event_youtube_thumbnail(headline=\'Modi Youth Remarks Ignite Controversy\', category=\'India\', real_photo_path=\'/tmp/test_photos/story_photo_1.jpg\', output_path=\'/app/AI-NewsTube/output/test_clean_thumb.jpg\'); print(\'THUMB_SUCCESS\')"'
s, o, e = c.exec_command(cmd)
out = o.read().decode("utf-8", errors="replace")
err = e.read().decode("utf-8", errors="replace")
print("OUT:", out.strip())
if err.strip():
    print("ERR:\n", err.strip())

sftp = c.open_sftp()
local_path = Path(r"C:\Users\suraj\.gemini\antigravity-ide\brain\2dd3bff8-6b59-4389-82bc-da16357d38ce\thumbnail_clean.jpg")
try:
    sftp.get("/app/AI-NewsTube/output/test_clean_thumb.jpg", str(local_path))
    print(f"Downloaded clean thumbnail to {local_path} ({local_path.stat().st_size} bytes)")
except Exception as ex:
    print("Download failed:", ex)
sftp.close()
c.close()
