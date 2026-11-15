"""
Platform Config Service
Manages platform API credentials and toggle states in data/platforms.json
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
PLATFORMS_FILE = BASE_DIR / "data" / "platforms.json"

DEFAULT_PLATFORMS = {
    "groq": {
        "name": "Groq AI Brain",
        "icon": "⚡",
        "color": "#F59E0B",
        "enabled": True,
        "connected": bool(os.getenv("GROQ_API_KEY")),
        "content_types": ["script_generation", "fact_checking"],
        "api_key": os.getenv("GROQ_API_KEY", "")
    },
    "youtube": {
        "name": "YouTube",
        "icon": "▶",
        "color": "#FF0000",
        "enabled": True,
        "connected": True,
        "content_types": ["video_169", "shorts_916"],
        "interval_hours": 3.0,
        "stream_key": os.getenv("YOUTUBE_STREAM_KEY", ""),
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
            PlatformConfigService.save(DEFAULT_PLATFORMS)
            return dict(DEFAULT_PLATFORMS)
        try:
            stored = json.loads(PLATFORMS_FILE.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_PLATFORMS)
            for k, v in stored.items():
                if k in merged:
                    merged[k].update(v)
                else:
                    merged[k] = v
            # Hydrate env fallbacks
            if os.getenv("GROQ_API_KEY") and not merged.get("groq", {}).get("api_key"):
                merged["groq"]["api_key"] = os.getenv("GROQ_API_KEY", "")
                merged["groq"]["connected"] = True
            if os.getenv("YOUTUBE_STREAM_KEY") and not merged.get("youtube", {}).get("stream_key"):
                merged["youtube"]["stream_key"] = os.getenv("YOUTUBE_STREAM_KEY", "")
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
        if platform_id not in data:
            data[platform_id] = {}
        data[platform_id].update(updates)
        PlatformConfigService.save(data)
        return data

    @staticmethod
    def get_enabled_platforms() -> Dict[str, Any]:
        data = PlatformConfigService.load()
        return {k: v for k, v in data.items() if v.get("enabled") and v.get("connected")}
