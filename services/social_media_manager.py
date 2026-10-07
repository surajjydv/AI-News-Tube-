"""
Social Media Manager — Unified Multi-Platform Orchestrator
Dispatches a single content payload to all enabled/connected platforms.
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = BASE_DIR / "data" / "social_history.json"
logger = logging.getLogger("social_media_manager")


def _save_history(entry: dict):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []
    history.append(entry)
    # Keep last 200 entries
    history = history[-200:]
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def publish_to_all_platforms(
    title: str,
    body_text: str,
    hashtags: str,
    video_path: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
    shorts_path: Optional[str] = None,
    youtube_video_id: Optional[str] = None,
    platforms_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Publish content to all enabled + connected platforms.
    Returns a dict of results per platform.
    """
    if not platforms_config:
        from services.platform_config_service import PlatformConfigService
        platforms_config = PlatformConfigService.get_enabled_platforms()

    caption = f"{title}\n\n{body_text[:300]}...\n\n{hashtags}"
    results = {}
    timestamp = datetime.now().isoformat()

    # ── YouTube: already published via trending_documentary_autopublisher
    if "youtube" in platforms_config and youtube_video_id:
        results["youtube"] = {
            "success": True,
            "url": f"https://youtu.be/{youtube_video_id}",
            "platform": "youtube"
        }

    # ── Telegram ──────────────────────────────────────────────────────────
    tg_cfg = platforms_config.get("telegram", {})
    if tg_cfg.get("enabled") and tg_cfg.get("connected"):
        try:
            from services.telegram_publisher import send_telegram_video, send_telegram_photo, send_telegram_message
            yt_link = f"\n\n▶ YouTube: https://youtu.be/{youtube_video_id}" if youtube_video_id else ""
            msg_text = f"<b>{title}</b>\n\n{body_text[:500]}{yt_link}\n\n{hashtags}"

            if video_path and os.path.exists(video_path):
                result = send_telegram_video(
                    video_path=video_path,
                    caption=msg_text[:1024],
                    bot_token=tg_cfg.get("bot_token", ""),
                    channel_id=tg_cfg.get("channel_id", ""),
                    thumbnail_path=thumbnail_path
                )
            elif thumbnail_path and os.path.exists(thumbnail_path):
                result = send_telegram_photo(
                    image_path=thumbnail_path,
                    caption=msg_text[:1024],
                    bot_token=tg_cfg.get("bot_token", ""),
                    channel_id=tg_cfg.get("channel_id", "")
                )
            else:
                result = send_telegram_message(
                    text=msg_text[:4096],
                    bot_token=tg_cfg.get("bot_token", ""),
                    channel_id=tg_cfg.get("channel_id", "")
                )
            results["telegram"] = result
        except Exception as e:
            results["telegram"] = {"success": False, "error": str(e)}

    # ── Twitter / X ───────────────────────────────────────────────────────
    tw_cfg = platforms_config.get("twitter", {})
    if tw_cfg.get("enabled") and tw_cfg.get("connected"):
        try:
            from services.twitter_publisher import post_tweet
            yt_link = f" https://youtu.be/{youtube_video_id}" if youtube_video_id else ""
            tweet_text = f"{title}{yt_link} {hashtags}"[:280]
            result = post_tweet(
                text=tweet_text,
                api_key=tw_cfg.get("api_key", ""),
                api_secret=tw_cfg.get("api_secret", ""),
                access_token=tw_cfg.get("access_token", ""),
                access_token_secret=tw_cfg.get("access_token_secret", ""),
                media_path=thumbnail_path
            )
            results["twitter"] = result
        except Exception as e:
            results["twitter"] = {"success": False, "error": str(e)}

    # ── Facebook ──────────────────────────────────────────────────────────
    fb_cfg = platforms_config.get("facebook", {})
    if fb_cfg.get("enabled") and fb_cfg.get("connected"):
        try:
            from services.facebook_publisher import post_facebook_text
            yt_link = f"https://youtu.be/{youtube_video_id}" if youtube_video_id else ""
            result = post_facebook_text(
                message=f"{title}\n\n{body_text[:600]}\n\n{hashtags}",
                page_id=fb_cfg.get("page_id", ""),
                page_access_token=fb_cfg.get("token", ""),
                link=yt_link or None
            )
            results["facebook"] = result
        except Exception as e:
            results["facebook"] = {"success": False, "error": str(e)}

    # ── Instagram ─────────────────────────────────────────────────────────
    ig_cfg = platforms_config.get("instagram", {})
    if ig_cfg.get("enabled") and ig_cfg.get("connected"):
        try:
            from services.instagram_publisher import post_instagram_photo
            result = post_instagram_photo(
                image_path=thumbnail_path or "",
                caption=caption[:2200],
                access_token=ig_cfg.get("token", ""),
                instagram_business_id=ig_cfg.get("page_id", "")
            )
            results["instagram"] = result
        except Exception as e:
            results["instagram"] = {"success": False, "error": str(e)}

    # Save history
    _save_history({
        "timestamp": timestamp,
        "title": title,
        "platforms": results,
        "youtube_url": f"https://youtu.be/{youtube_video_id}" if youtube_video_id else None
    })

    logger.info(f"[SMM] Published to {len(results)} platforms: {list(results.keys())}")
    return results


def get_publish_history(limit: int = 50) -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return list(reversed(history[-limit:]))
    except Exception:
        return []


def generate_hashtags(title: str, platform: str = "general") -> str:
    """Generate platform-appropriate hashtags from a title."""
    tags = ["#BreakingNews", "#LatestNews", "#NewsUpdate", "#HindiNews", "#IndiaNews"]
    words = [w.strip("!?,.:") for w in title.split() if len(w) > 4]
    tags += [f"#{w.title()}" for w in words[:3]]
    if platform == "instagram":
        tags += ["#Instagram", "#Reels", "#Viral"]
    elif platform == "twitter":
        return " ".join(tags[:5])
    return " ".join(tags[:8])


def generate_caption(title: str, script_text: str, platform: str = "general") -> str:
    """Generate a platform-optimized caption from title + script."""
    if platform == "instagram":
        # Punchy, emoji-rich
        return f"🔴 {title}\n\n{script_text[:200]}...\n\nSwipe ➡️ for full story!\n\n{generate_hashtags(title, 'instagram')}"
    elif platform == "twitter":
        return f"🔴 {title[:200]}\n\n{generate_hashtags(title, 'twitter')}"
    elif platform == "telegram":
        return f"<b>🔴 {title}</b>\n\n{script_text[:500]}..."
    elif platform == "facebook":
        return f"🔴 {title}\n\n{script_text[:500]}...\n\n{generate_hashtags(title)}"
    return f"{title}\n\n{script_text[:300]}..."
