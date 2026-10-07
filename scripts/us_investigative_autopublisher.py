"""
scripts/us_investigative_autopublisher.py
=========================================
24/7 Autonomous Investigative Video Essay & Documentary Publisher (Nitish Rajput / Dhruv Rathee Style).
Publishes 4 to 5 deeply researched, multi-chapter case study videos per day (every ~4.8 hours).
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import edge_tts
from utils.logger import logger
from services.rss_service import fetch_news, NewsArticle
from services.deep_research_service import DeepResearchService
from services.investigative_explainer_engine import InvestigativeExplainerEngine
from services.documentary_explainer_renderer import DocumentaryRenderer
from services.visual_asset_manager import VisualAssetManager
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
from services.youtube_upload_service import upload_video_to_youtube

OUTPUT_DIR = BASE_DIR / "output"
VIDEOS_DIR = BASE_DIR / "videos"
PROCESSED_FILE = BASE_DIR / "data" / "processed_explainer_stories.txt"
TOKEN_CHANNEL2 = BASE_DIR / "data" / "token_channel2.json"

POLL_INTERVAL_SECONDS = 17280  # 4.8 Hours (5 videos per 24-hour day)


def load_processed_topics() -> List[str]:
    if PROCESSED_FILE.exists():
        return [l.strip().lower() for l in PROCESSED_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return []


def mark_topic_processed(topic: str):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{topic}\n")


async def generate_documentary_narration(text: str, output_path: Path, voice: str = "en-US-AndrewNeural") -> Path:
    """Synthesizes high-clarity cinematic documentary voiceover."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+3%", volume="+0%")
    await communicate.save(str(output_path))
    logger.info(f"✅ Generated Documentary Voiceover: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path


def process_and_publish_case_study(article: NewsArticle) -> bool:
    """Executes end-to-end deep research, script writing, video rendering, and YouTube publishing."""
    start_t = time.time()
    story_id = f"{int(time.time())}_{hash(article.title) & 0xffffffff:08x}"
    story_dir = OUTPUT_DIR / f"explainer_assets_{story_id}"
    audio_path = OUTPUT_DIR / f"explainer_audio_{story_id}.mp3"
    video_path = VIDEOS_DIR / f"case_study_{story_id}.mp4"
    thumb_path = OUTPUT_DIR / f"explainer_thumb_{story_id}.jpg"

    logger.info("=" * 70)
    logger.info(f"🎬 [INVESTIGATIVE CASE STUDY] Processing: '{article.title}'")
    logger.info("=" * 70)

    # 1. Multi-Source Deep Web & Document Research
    dossier = DeepResearchService.compile_investigative_dossier(
        topic=article.title,
        direct_url=article.link,
        raw_summary=article.summary
    )

    # 2. Generate 4-Chapter Video Essay Narrative (Nitish Rajput / Dhruv Rathee style)
    narr, chapters, doc_title, v_title, tags = InvestigativeExplainerEngine.generate_case_study_script(
        topic=article.title,
        category=article.category,
        research_dossier=dossier["full_dossier"],
        target_minutes=5.5
    )

    # 3. Retrieve Authentic Real Photos for All Chapters
    assets = VisualAssetManager.get_multi_visual_assets(
        headline=article.title,
        category=article.category,
        output_dir=story_dir,
        article_url=article.link,
        direct_image_url=article.image_url,
        max_photos=max(4, len(chapters))
    )
    photo_paths = [a.file_path for a in assets]

    # 4. Synthesize Deep Voiceover
    asyncio.run(generate_documentary_narration(narr, audio_path))
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        logger.error(f"❌ Voice synthesis failed for case study: {audio_path}")
        return False

    # 5. Create Cinematic Thumbnail
    create_real_event_youtube_thumbnail(
        headline=doc_title,
        category="Investigation",
        real_photo_path=photo_paths[0] if photo_paths else "",
        output_path=thumb_path
    )

    # 6. Render 1080p Video Essay
    DocumentaryRenderer.render_documentary_video(
        doc_title=doc_title,
        chapters=chapters,
        photo_paths=photo_paths,
        audio_path=audio_path,
        output_video_path=video_path,
        fps=15
    )

    # 7. Upload to YouTube (Channel 2)
    chapter_text = "\n".join([f"📌 Chapter {c.get('chapter_num')}: {c.get('title')} - {c.get('summary')}" for c in chapters])
    description = (
        f"🔍 {v_title}\n\n"
        f"In this deep-dive investigative case study, we break down the full timeline, evidence, and hidden facts behind {doc_title}.\n\n"
        f"📖 CHAPTER BREAKDOWN:\n{chapter_text}\n\n"
        f"📄 Full Investigation Narrative:\n{narr}\n\n"
        f"🔔 Subscribe for full-length investigative case studies and documentary breakdowns.\n\n"
        f"#Documentary #Investigation #CaseStudy #Explained #DeepDive #RealStory"
    )

    token_to_use = str(TOKEN_CHANNEL2) if TOKEN_CHANNEL2.exists() else None

    vid_id = upload_video_to_youtube(
        video_path=str(video_path),
        title=v_title[:95],
        description=description,
        category_id="27",  # Education / Case Studies
        privacy_status="public",
        thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
        tags=tags[:15]
    )

    if vid_id and vid_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
        logger.info("=" * 70)
        logger.info(f"SUCCESS! Investigative Case Study Published: https://youtu.be/{vid_id}")
        logger.info("=" * 70)

        # ── Auto-broadcast to Telegram ─────────────────────────────────
        try:
            from services.platform_config_service import PlatformConfigService
            tg_cfg = PlatformConfigService.load().get("telegram", {})
            if tg_cfg.get("enabled") and tg_cfg.get("bot_token") and tg_cfg.get("channel_id"):
                from services.telegram_publisher import send_telegram_photo, send_telegram_message
                tg_caption = (
                    f"<b>{v_title}</b>\n\n"
                    f"Deep-dive investigative case study now live on YouTube!\n\n"
                    f"Watch: https://youtu.be/{vid_id}\n\n"
                    f"#Documentary #Investigation #CaseStudy #DeepDive"
                )
                if thumb_path.exists():
                    tg_result = send_telegram_photo(
                        image_path=str(thumb_path),
                        caption=tg_caption[:1024],
                        bot_token=tg_cfg["bot_token"],
                        channel_id=str(tg_cfg["channel_id"])
                    )
                else:
                    tg_result = send_telegram_message(
                        text=tg_caption[:4096],
                        bot_token=tg_cfg["bot_token"],
                        channel_id=str(tg_cfg["channel_id"])
                    )
                if tg_result.get("success"):
                    logger.info(f"Telegram broadcast sent! msg_id={tg_result.get('message_id')}")
                else:
                    logger.warning(f"Telegram broadcast failed: {tg_result.get('error')}")
        except Exception as tg_err:
            logger.warning(f"Telegram integration error (non-fatal): {tg_err}")

    mark_topic_processed(article.title)
    return True



def run_explainer_daemon():
    """Continuous 24/7 daemon publishing 4 to 5 deep-dive videos per day."""
    logger.info("=" * 70)
    logger.info("🚀 INVESTIGATIVE CASE STUDY AUTO-PUBLISHER ACTIVE (CHANNEL 2)")
    logger.info(f"   - Target Cadence : 4-5 Videos Per Day (Every {POLL_INTERVAL_SECONDS // 3600} Hours)")
    logger.info("   - Style          : Nitish Rajput / Dhruv Rathee Documentary Video Essays")
    logger.info("=" * 70)

    while True:
        try:
            articles = fetch_news()
            processed = load_processed_topics()
            unseen = [a for a in articles if a.title.strip().lower() not in processed]

            if unseen:
                # Pick top trending US / global controversy
                unseen.sort(key=lambda x: (getattr(x, "trending_score", 0.0), getattr(x, "published_at", "") or ""), reverse=True)
                target_article = unseen[0]
                process_and_publish_case_study(target_article)
            else:
                logger.info("⚡ No unseen major controversy found. Waiting for next trend cycle...")

        except Exception as e:
            logger.error(f"❌ Explainer daemon exception: {e}", exc_info=True)

        logger.info(f"⏳ Sleeping for {POLL_INTERVAL_SECONDS}s before next daily documentary cycle...")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_explainer_daemon()
