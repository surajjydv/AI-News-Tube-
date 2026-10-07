"""
Telegram Publisher — Bot API
Supports: Text messages, photos, videos, documents to channels
"""
import requests
from pathlib import Path
from typing import Optional


BASE_TG_URL = "https://api.telegram.org/bot{token}"


def send_telegram_message(
    text: str,
    bot_token: str,
    channel_id: str,
    parse_mode: str = "HTML",
    disable_preview: bool = False
) -> dict:
    """Send a text message to a Telegram channel."""
    if not bot_token or not channel_id:
        return {"success": False, "error": "Telegram credentials not configured"}

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text[:4096],
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_preview
    }
    resp = requests.post(url, json=payload, timeout=30).json()
    if resp.get("ok"):
        return {"success": True, "message_id": resp["result"]["message_id"], "platform": "telegram"}
    return {"success": False, "error": resp.get("description", "Message failed")}


def send_telegram_photo(
    image_path: str,
    caption: str,
    bot_token: str,
    channel_id: str
) -> dict:
    """Send a photo with caption to Telegram channel."""
    if not bot_token or not channel_id:
        return {"success": False, "error": "Telegram credentials not configured"}

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(image_path, "rb") as f:
        resp = requests.post(url, data={
            "chat_id": channel_id,
            "caption": caption[:1024],
            "parse_mode": "HTML"
        }, files={"photo": f}, timeout=60).json()

    if resp.get("ok"):
        return {"success": True, "message_id": resp["result"]["message_id"], "platform": "telegram"}
    return {"success": False, "error": resp.get("description", "Photo send failed")}


def send_telegram_video(
    video_path: str,
    caption: str,
    bot_token: str,
    channel_id: str,
    thumbnail_path: Optional[str] = None
) -> dict:
    """Send a video to Telegram channel."""
    if not bot_token or not channel_id:
        return {"success": False, "error": "Telegram credentials not configured"}

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    files = {}
    with open(video_path, "rb") as vf:
        files["video"] = vf
        if thumbnail_path and Path(thumbnail_path).exists():
            with open(thumbnail_path, "rb") as tf:
                files["thumbnail"] = tf

        resp = requests.post(url, data={
            "chat_id": channel_id,
            "caption": caption[:1024],
            "parse_mode": "HTML",
            "supports_streaming": True
        }, files=files, timeout=300).json()

    if resp.get("ok"):
        return {"success": True, "message_id": resp["result"]["message_id"], "platform": "telegram"}
    return {"success": False, "error": resp.get("description", "Video send failed")}


def verify_telegram_bot(bot_token: str, channel_id: str) -> dict:
    """Verify bot token by calling getMe and sendMessage with a test ping."""
    if not bot_token:
        return {"connected": False, "error": "No token provided"}
    try:
        r = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5).json()
        if r.get("ok"):
            bot_name = r["result"].get("username", "Unknown Bot")
            return {"connected": True, "bot_name": bot_name}
        return {"connected": False, "error": r.get("description", "Invalid token")}
    except Exception as e:
        return {"connected": False, "error": str(e)}
