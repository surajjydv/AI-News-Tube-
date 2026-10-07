"""
Platform Config Service
Manages platform API credentials and toggle states in data/platforms.json
"""
import json
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
PLATFORMS_FILE = BASE_DIR / "data" / "platforms.json"

DEFAULT_PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "icon": "▶",
        "color": "#FF0000",
        "enabled": True,
        "connected": True,  # already via OAuth token.json
        "content_types": ["video_169", "shorts_916"],
        "interval_hours": 3.0,
        "token": ""
    },
    "instagram": {
        "name": "Instagram",
        "icon": "📸",
        "color": "#E1306C",
        "enabled": False,
        "connected": False,
        "content_types": ["reels_916", "photo_11", "story"],
        "interval_hours": 8.0,
        "token": "",
        "page_id": ""
    },
    "twitter": {
        "name": "Twitter / X",
        "icon": "🐦",
        "color": "#1DA1F2",
        "enabled": False,
        "connected": False,
        "content_types": ["tweet", "thread", "media_tweet"],
        "interval_hours": 1.5,
        "api_key": "",
        "api_secret": "",
        "access_token": "",
        "access_token_secret": "",
        "bearer_token": ""
    },
    "facebook": {
        "name": "Facebook",
        "icon": "📘",
        "color": "#1877F2",
        "enabled": False,
        "connected": False,
        "content_types": ["post", "video", "reel"],
        "interval_hours": 6.0,
        "token": "",
        "page_id": ""
    },
    "telegram": {
        "name": "Telegram",
        "icon": "✈",
        "color": "#26A5E4",
        "enabled": False,
        "connected": False,
        "content_types": ["text", "photo", "video", "document"],
        "interval_hours": 2.0,
        "bot_token": "",
        "channel_id": ""
    }
}


class PlatformConfigService:

    @staticmethod
    def load() -> Dict[str, Any]:
        PLATFORMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not PLATFORMS_FILE.exists():
            PLATFORMS_FILE.write_text(json.dumps(DEFAULT_PLATFORMS, indent=2), encoding="utf-8")
            return dict(DEFAULT_PLATFORMS)
        try:
            stored = json.loads(PLATFORMS_FILE.read_text(encoding="utf-8"))
            # Merge with defaults to add any new platforms
            merged = dict(DEFAULT_PLATFORMS)
            for k, v in stored.items():
                if k in merged:
                    merged[k].update(v)
            return merged
        except Exception:
            return dict(DEFAULT_PLATFORMS)

    @staticmethod
    def save(data: Dict[str, Any]) -> Dict[str, Any]:
        PLATFORMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PLATFORMS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data

    @staticmethod
    def update_platform(platform_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        data = PlatformConfigService.load()
        if platform_id in data:
            data[platform_id].update(updates)
        PlatformConfigService.save(data)
        return data

    @staticmethod
    def get_enabled_platforms() -> Dict[str, Any]:
        data = PlatformConfigService.load()
        return {k: v for k, v in data.items() if v.get("enabled") and v.get("connected")}
