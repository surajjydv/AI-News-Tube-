"""
services/youtube_upload_service.py
===================================
Automated YouTube Video & Shorts Publisher Service using YouTube Data API v3.
Handles Console URL authentication, OAuth2 token caching, video uploads, and thumbnails.
"""

import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv()

from utils.logger import logger


CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_PICKLE_FILE  = BASE_DIR / "data" / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


def get_authenticated_service(interactive: bool = False):
    """Authenticates and returns YouTube API client service instance."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    TOKEN_PICKLE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if TOKEN_PICKLE_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PICKLE_FILE), SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token file: {e}")
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired YouTube OAuth access token...")
            creds.refresh(Request())
            with open(TOKEN_PICKLE_FILE, "w") as token:
                token.write(creds.to_json())
            logger.info("✅ Refreshed and updated data/token.json successfully!")
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            creds = None

    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError("OAuth token (data/token.json) not generated yet. Use interactive setup or RTMP live stream.")

        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(f"Missing {CLIENT_SECRET_FILE.name}! Add Google OAuth credentials file.")
        
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
        try:
            creds = flow.run_local_server(port=0, prompt="consent", open_browser=True)
            with open(TOKEN_PICKLE_FILE, "w") as token:
                token.write(creds.to_json())
            logger.info("✅ Generated and saved data/token.json successfully!")
        except Exception as e:
            logger.error(f"OAuth server error: {e}")
            raise e

    return build("youtube", "v3", credentials=creds)


def stream_video_to_youtube_rtmp(video_path: str) -> bool:
    """Streams a video file directly to YouTube Live RTMP using YOUTUBE_STREAM_KEY from .env."""
    import subprocess
    stream_key = os.getenv("YOUTUBE_STREAM_KEY")
    if not stream_key:
        logger.warning("⚠️ YOUTUBE_STREAM_KEY not found in .env. Skipping RTMP stream.")
        return False

    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    print(f"[YOUTUBE RTMP] 🚀 Streaming '{Path(video_path).name}' to YouTube Live RTMP...")

    rtmp_cmd = [
        "ffmpeg", "-re", "-y",
        "-i", str(video_path),
        "-c:v", "copy",
        "-c:a", "copy",
        "-f", "flv",
        "-strict", "-2",
        rtmp_url
    ]
    res = subprocess.run(rtmp_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0:
        print("[YOUTUBE RTMP] ✅ Video Successfully Broadcasted to YouTube Live!")
        return True
    return False


def upload_video_to_youtube(
    video_path: str,
    title: str,
    description: str,
    category_id: str = "25",
    tags: list = None,
    thumbnail_path: str = None,
    is_short: bool = False,
    privacy_status: str = "public"
) -> str:
    from googleapiclient.http import MediaFileUpload

    v_path = Path(video_path)
    if not v_path.exists():
        raise FileNotFoundError(f"Video file not found at {video_path}")

    # 1. Try YouTube Data API v3 OAuth Upload if token exists
    try:
        youtube = get_authenticated_service(interactive=False)
        if tags is None:
            tags = ["NewsTube", "BreakingNews", "HindiNews", "LatestNews", "IndiaNews"]

        if is_short and "#Shorts" not in title:
            title = f"{title[:90]} #Shorts"
            description = f"{description}\n\n#Shorts #NewsTube #HindiNews"

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        print(f"[YOUTUBE UPLOADER] 🚀 Uploading '{v_path.name}' to YouTube ({privacy_status.upper()})...")
        media = MediaFileUpload(str(v_path), chunksize=1024*1024*2, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        max_retries = 5
        retry_count = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    print(f"[YOUTUBE UPLOADER] ⏳ Upload progress: {int(status.progress() * 100)}%")
                retry_count = 0
            except Exception as ex:
                retry_count += 1
                if retry_count > max_retries:
                    raise ex
                time.sleep(2 * retry_count)
                print(f"[YOUTUBE UPLOADER] ⚠️ Temporary network hiccup, retrying chunk ({retry_count}/{max_retries})...")

        video_id = response.get("id")
        print(f"[YOUTUBE UPLOADER] ✅ Video Published Successfully! URL: https://youtu.be/{video_id}")

        if thumbnail_path and Path(thumbnail_path).exists():
            try:
                print(f"[YOUTUBE UPLOADER] 🖼️ Setting Custom Thumbnail: {Path(thumbnail_path).name}")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path))
                ).execute()
                print("[YOUTUBE UPLOADER] ✅ Custom Thumbnail Set Successfully!")
            except Exception as e:
                print(f"[YOUTUBE UPLOADER WARN] Thumbnail update failed: {e}")

        return video_id

    except Exception as e:
        logger.info(f"ℹ️ OAuth VOD upload unavailable ({e}). Falling back to YouTube Live RTMP broadcast...")
        streamed = stream_video_to_youtube_rtmp(str(v_path))
        if streamed:
            return "RTMP_LIVE_STREAM_BROADCASTED"
        return "LOCAL_SAVED"


if __name__ == "__main__":
    print("[TEST] Authenticating YouTube API Service...")
    srv = get_authenticated_service()
    print("✅ YouTube API Authenticated Successfully!")
