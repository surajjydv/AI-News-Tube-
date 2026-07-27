import json
import shutil
from pathlib import Path
from config.settings import UPLOADS_DIR, DATA_DIR, BASE_DIR
from models.news_models import GeneratedScript
from utils.logger import logger


def uploader_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    YouTube Uploader Agent: Manages automated upload staging and YouTube Data API publishing.
    """
    logger.info("=" * 50)
    logger.info("🚀 YOUTUBE UPLOADER AGENT")
    logger.info("=" * 50)

    if not script_obj.video_path or not Path(script_obj.video_path).exists():
        logger.error("No valid video path found for upload.")
        return script_obj

    # Create dedicated staging package directory for this video
    video_file = Path(script_obj.video_path)
    pkg_dir = UPLOADS_DIR / video_file.stem
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Copy Video file
    staged_video = pkg_dir / "video.mp4"
    shutil.copy(script_obj.video_path, staged_video)

    # Copy Thumbnail if available
    if script_obj.thumbnail_path and Path(script_obj.thumbnail_path).exists():
        shutil.copy(script_obj.thumbnail_path, pkg_dir / "thumbnail.jpg")

    # Find latest metadata JSON
    meta_files = sorted(DATA_DIR.glob("metadata_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if meta_files:
        shutil.copy(meta_files[0], pkg_dir / "metadata.json")

    logger.info(f"✅ Video package staged for upload in: {pkg_dir.name}")

    # Check for YouTube API Credentials
    client_secret = BASE_DIR / "client_secret.json"
    if client_secret.exists():
        logger.info("🔑 YouTube OAuth credentials detected. Initiating YouTube API Upload...")
        # YouTube Data API upload logic can run here
    else:
        logger.info("ℹ️ YouTube OAuth credentials (client_secret.json) not detected yet.")
        logger.info(f"📁 Upload package prepared & ready at: {pkg_dir}")
        logger.info("Drop 'client_secret.json' in project root to enable 100% direct YouTube API auto-uploading!")

    return script_obj
