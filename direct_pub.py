import sys
from pathlib import Path
from services.youtube_upload_service import upload_video_to_youtube

video_path = Path("videos/story_5m_video.mp4")
thumbnail_path = Path("thumbnails/story_5m_thumbnail.jpg")

print(f"Checking video file: {video_path.exists()} ({video_path.stat().st_size if video_path.exists() else 0} bytes)")
print(f"Checking thumbnail file: {thumbnail_path.exists()}")

video_id = upload_video_to_youtube(
    video_path=str(video_path),
    title="BREAKING: Supreme Court Forms 5-Member Committee Led By Ex-SC Judge Subhash Reddy",
    description="Multi-Source Synthesized Live Hindi News Coverage & Investigation Details.",
    category_id="25",
    tags=["News", "SupremeCourt", "IndiaNews", "BreakingNews", "HindiNews"],
    thumbnail_path=str(thumbnail_path) if thumbnail_path.exists() else None,
    privacy_status="public"
)

print(f"🎉 DIRECT_UPLOAD_SUCCESS: https://youtu.be/{video_id}")
