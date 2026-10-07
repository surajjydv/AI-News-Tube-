"""
check_youtube_api.py
===================
Script to check YouTube Stream Key & YouTube Data API OAuth status.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv()

def check_youtube():
    print("=" * 55)
    print("      YOUTUBE API & STREAM KEY CONNECTION CHECK      ")
    print("=" * 55)
    
    # 1. Stream Key Check
    stream_key = os.getenv("YOUTUBE_STREAM_KEY")
    if stream_key:
        masked = stream_key[:4] + "****" + stream_key[-4:]
        print(f"[LIVE STREAM KEY] Status : CONFIGURED (Key: {masked})")
        print(f"[LIVE STREAM KEY] RTMP   : rtmp://a.rtmp.youtube.com/live2/{stream_key}")
    else:
        print("[LIVE STREAM KEY] Status : NOT FOUND in .env")

    print("-" * 55)

    # 2. OAuth API Check
    client_secret_file = BASE_DIR / "client_secret.json"
    token_file = BASE_DIR / "data" / "token.json"

    print(f"[OAUTH CONFIG] client_secret.json : {'FOUND' if client_secret_file.exists() else 'MISSING'}")
    print(f"[OAUTH CONFIG] data/token.json    : {'FOUND' if token_file.exists() else 'NOT GENERATED YET'}")

    if token_file.exists():
        try:
            from services.youtube_upload_service import get_authenticated_service
            srv = get_authenticated_service()
            res = srv.channels().list(mine=True, part="snippet,statistics").execute()
            if "items" in res and res["items"]:
                ch = res["items"][0]
                print(f"[OAUTH API STATUS] Connected Successfully!")
                print(f"[CHANNEL] Name: {ch['snippet']['title']}")
                print(f"[CHANNEL] ID: {ch['id']}")
                print(f"[CHANNEL] Subscribers: {ch['statistics'].get('subscriberCount', 'Hidden')}")
                print(f"[CHANNEL] Videos: {ch['statistics'].get('videoCount', '0')}")
            else:
                print("[OAUTH API STATUS] Authenticated, but no channel found for this Google account.")
        except Exception as e:
            print(f"[OAUTH API STATUS] Error: {e}")
    else:
        print("\n[ACTION REQUIRED FOR VIDEO UPLOAD API]:")
        print("Run 'python services/youtube_upload_service.py' once to log in via browser and save token.json.")

if __name__ == "__main__":
    check_youtube()
