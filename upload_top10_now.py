"""
upload_top10_now.py
===================
Uploads the pre-rendered Top 10 News Bulletin video & high-CTR thumbnail to YouTube.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.youtube_upload_service import upload_video_to_youtube

VIDEO_FILE = BASE_DIR / "videos" / "top10_today_bulletin.mp4"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "top10_today_thumbnail.jpg"

def main():
    print("📤 Uploading Today's Top 10 News Bulletin & Real Thumbnail to YouTube...")
    title = "आज की 10 बड़ी मुख्य खबरें 📰 Today Top 10 Headlines News | 10 Big Stories Update"
    description = (
        "Today's Top 10 Headlines News Bulletin - आज की 10 बड़ी मुख्य ख़बरें!\n\n"
        "देखिए देश, दुनिया, खेल, राजनीति और टेक्नोलॉजी की आज की 10 सबसे बड़ी ख़बरें एक साथ AI-NewsTube पर।\n\n"
        "#Top10News #TodayNews #HindiNews #BreakingNews #IndiaNews #NewsTube"
    )
    tags = [
        "Today Top 10 News", "Top 10 Headlines", "Aaj Ki Badi Khabrein",
        "Hindi News", "Breaking News India", "Latest News Today", "AI NewsTube"
    ]

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=title,
        description=description,
        category_id="25",
        tags=tags,
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! TODAY'S TOP 10 NEWS BULLETIN & THUMBNAIL PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()
