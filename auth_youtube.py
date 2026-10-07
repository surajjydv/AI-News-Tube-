"""
auth_youtube.py
===============
One-time YouTube OAuth Authorization & Immediate Video Uploader.
Runs a local server to capture authorization, saves data/token.json,
and immediately uploads the generated 2-minute video to YouTube.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.youtube_upload_service import get_authenticated_service, upload_video_to_youtube

def main():
    print("=" * 65)
    print("🔑 ONE-TIME YOUTUBE OAUTH AUTHENTICATION SETUP")
    print("=" * 65)
    print("A browser window will open now. Please select your Google account")
    print("and click 'Allow' / 'Continue' to grant YouTube upload permission.")
    print("=" * 65)

    try:
        service = get_authenticated_service(interactive=True)
        print("\n✅ AUTHENTICATION SUCCESSFUL! data/token.json has been created!")

        # Verify Channel Info
        channels_response = service.channels().list(mine=True, part="snippet").execute()
        items = channels_response.get("items", [])
        if items:
            ch_title = items[0]["snippet"]["title"]
            print(f"📺 Connected YouTube Channel: {ch_title}")
        
        # Check if 2-minute video exists and upload it immediately!
        v_file = BASE_DIR / "videos" / "story_2m_video.mp4"
        thumb_file = BASE_DIR / "thumbnails" / "story_2m_thumbnail.jpg"

        if v_file.exists():
            print("\n🚀 UPLOADING 2-MINUTE VIDEO TO YOUTUBE NOW...")
            video_id = upload_video_to_youtube(
                video_path=str(v_file),
                title="Supreme Court Big Ruling 🔴 2-Min Special News Bulletin | NewsTube",
                description="2-Minute Special News Bulletin on Supreme Court Latest Ruling.\n\n#NewsUpdate #HindiNews #SupremeCourt #BreakingNews #NewsTube",
                category_id="25",
                tags=["Supreme Court", "Breaking News", "Hindi News", "NewsTube", "Today News"],
                thumbnail_path=str(thumb_file) if thumb_file.exists() else None,
                privacy_status="public"
            )
            print("\n" + "=" * 65)
            print("🎉 VIDEO SUCCESSFULLY PUBLISHED AS PUBLIC ON YOUTUBE!")
            print(f"🔗 YOUR YOUTUBE VIDEO LINK: https://youtu.be/{video_id}")
            print("=" * 65)
    except Exception as e:
        print(f"\n❌ Error during authorization or upload: {e}")

if __name__ == "__main__":
    main()
