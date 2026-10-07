"""
scripts/realtime_breaking_news_autouploader.py
=============================================
Autonomous 24/7 Dual-Track Real-Time Breaking News Publisher for YouTube.
Alternates between 16:9 Full-Length Investigative Broadcasts and 9:16 Vertical YouTube Shorts
on distinct topics at separate 15-minute intervals.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import (
    CHANNEL_NAME,
    VOICE_DIR,
    VIDEOS_DIR,
    THUMBNAILS_DIR,
    DATA_DIR,
    DEFAULT_TTS_VOICE,
    DEFAULT_GROQ_MODEL
)
POLL_INTERVAL_SECONDS = 900
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
from utils.logger import logger
from utils.json_utils import extract_json_from_llm
from models.news_models import NewsArticle, MediaAsset
from services.rss_service import fetch_news
from services.visual_asset_manager import VisualAssetManager
from services.fluent_script_service import generate_fluent_news_script, generate_shorts_news_script
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
from services.cinematic_story_renderer import render_dynamic_broadcast_video
from services.shorts_25d_renderer import render_shorts_broadcast_video
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts


# Anti-Repetition Cache Management
SEEN_FILE = BASE_DIR / "data" / "processed_breaking_stories.json"
PUBLISH_STATE_FILE = BASE_DIR / "data" / "publish_cadence_state.json"


def load_processed_story_hashes() -> List[str]:
    if SEEN_FILE.exists():
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def mark_story_processed(story_title: str):
    hashes = load_processed_story_hashes()
    clean = story_title.strip().lower()
    if clean not in hashes:
        hashes.append(clean)
        # Keep last 500 stories
        if len(hashes) > 500:
            hashes = hashes[-500:]
        SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(SEEN_FILE, "w", encoding="utf-8") as f:
                json.dump(hashes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Error saving seen stories: {e}")


def cleanup_storage_and_temp_files(max_keep_videos: int = 6):
    """
    Automated Rolling Garbage Collector:
    - Prunes historical rendered MP4s in VIDEOS_DIR, keeping only the latest N videos.
    - Cleans temporary audio, thumbnail, and intermediate assets in OUTPUT_DIR older than 1 hour.
    - Guarantees 24/7 non-stop operation without disk space exhaustion.
    """
    try:
        # 1. Prune Videos
        if VIDEOS_DIR.exists():
            vids = sorted(VIDEOS_DIR.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)
            for v in vids[max_keep_videos:]:
                try:
                    v.unlink()
                except Exception:
                    pass

        # 2. Clean temporary files in OUTPUT_DIR older than 1 hour
        if OUTPUT_DIR.exists():
            cutoff = time.time() - 3600
            for item in OUTPUT_DIR.iterdir():
                try:
                    if item.is_file() and item.stat().st_mtime < cutoff:
                        item.unlink()
                    elif item.is_dir() and item.stat().st_mtime < cutoff:
                        import shutil
                        shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Storage cleanup note: {e}")


def get_next_publish_mode() -> str:
    """Returns 'full' or 'short', alternating between iterations."""
    state = {"mode": "full", "last_published": None}
    if PUBLISH_STATE_FILE.exists():
        try:
            with open(PUBLISH_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
    return state.get("mode", "full")



def set_next_publish_mode(current_mode: str, last_title: str):
    """Saves state and flips mode for next cycle."""
    next_m = "short" if current_mode == "full" else "full"
    state = {
        "mode": next_m,
        "last_mode": current_mode,
        "last_title": last_title,
        "last_time": datetime.now(timezone.utc).isoformat()
    }
    PUBLISH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(PUBLISH_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error saving publish state: {e}")


def fetch_latest_fresh_breaking_news(max_age_hours: float = 3.0) -> Optional[NewsArticle]:
    """Fetches high-impact news articles and returns the freshest unposted story."""
    articles = fetch_news()
    if not articles:
        return None

    seen_titles = load_processed_story_hashes()
    unseen_articles = []

    for a in articles:
        clean_t = a.title.strip().lower()
        already_seen = any(clean_t in s or s in clean_t for s in seen_titles)
        if not already_seen:
            unseen_articles.append(a)

    if not unseen_articles:
        logger.info("⚡ All fresh stories broadcasted. Selecting top trending unseen wire candidate...")
        unseen_articles = [a for a in articles if a.title.strip().lower() not in seen_titles]

    if not unseen_articles:
        return None

    # Sort primarily by trending score (importance) and recency
    unseen_articles.sort(key=lambda x: (getattr(x, "trending_score", 0.0), getattr(x, "published_at", "") or ""), reverse=True)
    return unseen_articles[0]



async def generate_realtime_narration(text: str, output_path: Path, voice: str = DEFAULT_TTS_VOICE) -> Path:
    """Synthesizes high-clarity broadcast English narration with energetic news tempo."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+10%", volume="+0%")
    await communicate.save(str(output_path))
    logger.info(f"✅ Generated Fresh Neural Narration: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path


def process_and_publish_full_video(article: NewsArticle) -> bool:
    """Renders and uploads a 16:9 full-length 1080p broadcast story with 4K thumbnail."""
    start_time = time.time()
    story_id = f"{int(time.time())}_{hash(article.title) & 0xffffffff:08x}"
    
    clean_title = article.title.split(" - ")[0].strip()
    clean_summary = article.summary.replace("<p>", "").replace("</p>", "").strip() if article.summary else ""
    
    logger.info("=" * 65)
    logger.info(f"🚨 [FULL VIDEO 16:9] PUBLISHING STORY: [{article.category.upper()}] '{article.title}'")
    logger.info("=" * 65)

    story_audio = OUTPUT_DIR / f"narration_{story_id}.mp3"
    story_thumb = OUTPUT_DIR / f"thumb_{story_id}.jpg"
    story_video = VIDEOS_DIR / f"breaking_{story_id}.mp4"

    # Step 1: Resolve 4 Authentic Real Event Press Photos
    logger.info("📸 Step 1: Retrieving 4 Distinct Authentic On-Ground Press Photographs...")
    story_dir = OUTPUT_DIR / f"story_assets_{story_id}"
    assets = VisualAssetManager.get_multi_visual_assets(
        headline=article.title,
        category=article.category,
        output_dir=story_dir,
        article_url=article.link,
        direct_image_url=article.image_url,
        max_photos=4
    )

    # Step 2: Write Deep Investigative Narrative
    logger.info("📝 Step 2: Writing Deep Investigative Story (Zero Welcome, Pure Detailed Facts)...")
    full_narr_text, slide_takeaways, broadcast_headline, viral_title, yt_tags = generate_fluent_news_script(
        title=article.title,
        category=article.category,
        context=f"{clean_title}. {clean_summary}",
        article_url=article.link,
        target_minutes=2.5
    )

    # Step 3: Synthesize English Neural Voiceover
    logger.info("🎙️ Step 3: Synthesizing Neural English Voiceover (Andrew Neural)...")
    asyncio.run(generate_realtime_narration(full_narr_text, story_audio))
    if not story_audio.exists() or story_audio.stat().st_size < 1000:
        logger.error(f"❌ Failed to generate valid audio file: {story_audio}")
        return False

    # Step 4: Create Real Event Photo YouTube Thumbnail
    logger.info("🖼️ Step 4: Creating High-CTR Real Event Photo Thumbnail...")
    create_real_event_youtube_thumbnail(
        headline=broadcast_headline,
        category=article.category,
        real_photo_path=assets[0].file_path if assets else None,
        output_path=story_thumb
    )

    # Step 5: Render 1080p 2.5D Broadcast Video
    logger.info("🎬 Step 5: Rendering 1080p 2.5D Animated Broadcast Video...")
    photo_paths = [a.file_path for a in assets]
    photo_credits = [a.on_screen_credit for a in assets]

    render_dynamic_broadcast_video(
        headline=broadcast_headline,
        category=article.category,
        takeaway_points=slide_takeaways,
        photo_paths=photo_paths,
        photo_credits=photo_credits,
        audio_path=story_audio,
        output_video_path=story_video,
        fps=15
    )


    # Step 6: Post Publicly to YouTube

    logger.info("📤 Step 6: Uploading to YouTube as Public VOD...")
    video_title = viral_title if viral_title else f"{broadcast_headline} 🔴 Breaking News & Live Report"
    if len(video_title) > 98:
        video_title = video_title[:95] + "..."
    
    credit_str = ", ".join(list(set([a.on_screen_credit for a in assets if a])))
    takeaway_lines = "\n".join([f"• {t}" for t in slide_takeaways])
    description = (
        f"🚨 {video_title}\n\n"
        f"📌 KEY HIGHLIGHTS & DEVELOPMENTS:\n"
        f"{takeaway_lines}\n\n"
        f"📖 INVESTIGATIVE REPORT:\n{full_narr_text}\n\n"
        f"🔔 Subscribe to {CHANNEL_NAME} for 24/7 unvarnished global breaking news, deep investigations, and live crisis analysis.\n\n"
        f"Category: {article.category.upper()}\n"
        f"Credits: {credit_str}\n\n"
        f"#BreakingNews #WorldNews #Trending #ViralNews #Investigation #LiveNews #{CHANNEL_NAME}"
    )

    combined_tags = list(dict.fromkeys(yt_tags + ["Breaking News", "World News", "Trending News", "Live Updates", "Investigation", CHANNEL_NAME, article.category]))

    video_id = upload_video_to_youtube(
        video_path=str(story_video),
        title=video_title,
        description=description,
        category_id="25",
        privacy_status="public",
        thumbnail_path=str(story_thumb) if story_thumb.exists() else None,
        tags=combined_tags[:15]
    )

    if video_id and video_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
        logger.info("=" * 65)
        logger.info(f"🎉 SUCCESS! Full Video Published: https://youtu.be/{video_id}")
        logger.info("=" * 65)

    mark_story_processed(article.title)
    set_next_publish_mode("full", article.title)
    cleanup_storage_and_temp_files(max_keep_videos=6)
    return True


def process_and_publish_short_video(article: NewsArticle) -> bool:
    """Renders and uploads a 9:16 vertical mobile YouTube Short with unified story capsule."""
    start_time = time.time()
    story_id = f"{int(time.time())}_{hash(article.title) & 0xffffffff:08x}"

    clean_title = article.title.split(" - ")[0].strip()
    clean_summary = article.summary.replace("<p>", "").replace("</p>", "").strip() if article.summary else ""

    logger.info("=" * 65)
    logger.info(f"📱 [YOUTUBE SHORT 9:16] PUBLISHING STORY: [{article.category.upper()}] '{article.title}'")
    logger.info("=" * 65)

    shorts_audio_path = OUTPUT_DIR / f"shorts_audio_{story_id}.mp3"
    shorts_video_path = VIDEOS_DIR / f"shorts_{story_id}.mp4"

    # Step 1: Resolve Authentic Real Event Press Photos
    logger.info("📸 Step 1: Retrieving Authentic Press Photographs for Short...")
    story_dir = OUTPUT_DIR / f"shorts_assets_{story_id}"
    assets = VisualAssetManager.get_multi_visual_assets(
        headline=article.title,
        category=article.category,
        output_dir=story_dir,
        article_url=article.link,
        direct_image_url=article.image_url,
        max_photos=3
    )

    # Step 2: Write Fast-Paced Short Script (70-95 words in English)
    logger.info("📝 Step 2: Generating Fast-Paced Viral Shorts Script...")
    s_narr, s_takeaways, s_head, s_title, s_tags = generate_shorts_news_script(
        title=article.title,
        category=article.category,
        context=f"{clean_title}. {clean_summary}",
        article_url=article.link
    )

    # Step 3: Synthesize Short Voiceover
    logger.info("🎙️ Step 3: Synthesizing Neural English Voiceover for Short...")
    asyncio.run(generate_realtime_narration(s_narr, shorts_audio_path))
    if not shorts_audio_path.exists() or shorts_audio_path.stat().st_size < 1000:
        logger.error(f"❌ Failed to generate audio for Short: {shorts_audio_path}")
        return False

    # Step 4: Render 9:16 Vertical Short Video (Unified Story Capsule Layout)
    logger.info("🎬 Step 4: Rendering 9:16 Vertical Short Video (Fast 2.5D Capsule)...")
    photo_paths = [a.file_path for a in assets]
    photo_credits = [a.on_screen_credit for a in assets]

    render_shorts_broadcast_video(
        headline=s_head,
        category=article.category,
        slide_takeaways=s_takeaways,
        photo_paths=photo_paths,
        photo_credits=photo_credits,
        audio_path=shorts_audio_path,
        output_video_path=shorts_video_path,
        fps=15
    )

    # Step 5: Upload to YouTube Shorts
    logger.info("📤 Step 5: Uploading to YouTube as Public Short (#Shorts)...")
    shorts_desc = f"🚨 {s_title}\n\n📌 {s_narr}\n\n🔔 Subscribe for 24/7 breaking news updates.\n\n#Shorts #YouTubeShorts #BreakingNews #Trending #ViralNews #WorldNews #{CHANNEL_NAME}"
    shorts_tags = list(dict.fromkeys(s_tags + ["Shorts", "YouTubeShorts", "ViralShorts", "Trending", "BreakingNews", "WorldNews", CHANNEL_NAME]))
    
    shorts_vid_id = upload_video_to_youtube(
        video_path=str(shorts_video_path),
        title=s_title,
        description=shorts_desc,
        category_id="25",
        privacy_status="public",
        thumbnail_path=None,
        tags=shorts_tags[:15],
        is_short=True
    )


    if shorts_vid_id and shorts_vid_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
        logger.info("=" * 65)
        logger.info(f"🎉 SUCCESS! YouTube Short Published: https://youtube.com/shorts/{shorts_vid_id}")
        logger.info("=" * 65)

    mark_story_processed(article.title)
    set_next_publish_mode("short", article.title)
    cleanup_storage_and_temp_files(max_keep_videos=6)
    return True



def run_breaking_news_autopublisher_loop(single_run: bool = False):
    """
    Continuous 24/7 Interleaved Publishing Loop:
    Every 15 minutes:
    - Slot 1: Full 16:9 Video on Story A
    - Slot 2 (15m later): 9:16 Vertical Short on Story B (Different Topic!)
    - Slot 3 (15m later): Full 16:9 Video on Story C
    - Slot 4 (15m later): 9:16 Vertical Short on Story D
    """
    logger.info("=" * 70)
    logger.info("🚀 AI-NEWSTUBE 24/7 DUAL-TRACK INTERLEAVED AUTO-PUBLISHER ACTIVE")
    logger.info(f"   - Polling Interval : Every {POLL_INTERVAL_SECONDS} seconds (15 Minutes)")
    logger.info("   - Publishing Mode  : Alternating (Full Video 16:9 ↔ YouTube Short 9:16)")
    logger.info("   - Topic Rule       : 100% Unique Independent Stories Per Upload")
    logger.info("   - Graphics Layout  : 2.5D Physical TV Studio & Unified Live News Capsule")
    logger.info("=" * 70)

    while True:
        try:
            current_mode = get_next_publish_mode()
            mode_label = "FULL VIDEO (16:9)" if current_mode == "full" else "YOUTUBE SHORT (9:16)"
            logger.info(f"📡 Scanning live news wire for next breaking story [Target Format: {mode_label}]...")
            
            fresh_story = fetch_latest_fresh_breaking_news(max_age_hours=3.0)

            if fresh_story:
                logger.info(f"⚡ Selected Fresh Story: [{fresh_story.category}] '{fresh_story.title}'")
                if current_mode == "full":
                    process_and_publish_full_video(fresh_story)
                else:
                    process_and_publish_short_video(fresh_story)
            else:
                logger.info("ℹ️ All current feed stories already published or pending fresh updates.")

            if single_run:
                break

            logger.info(f"⏳ Sleeping for {POLL_INTERVAL_SECONDS}s before next alternating cycle...")
            time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("🛑 Breaking news auto-publisher stopped by user.")
            break
        except Exception as e:
            logger.error(f"❌ Error in breaking news publisher loop: {e}", exc_info=True)
            if single_run:
                break
            time.sleep(60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI-NewsTube 24/7 Realtime Breaking News Publisher")
    parser.add_argument("--once", action="store_true", help="Run single news publication cycle and exit")
    args = parser.parse_args()

    run_breaking_news_autopublisher_loop(single_run=args.once)
