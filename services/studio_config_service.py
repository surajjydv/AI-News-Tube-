import json, os
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "data" / "studio_settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "active_channel_name": "SRJ UNDERRATED",
    "active_channel_id": "UC7lAXODVk6aGIxE60Qy-9Yg",
    "video_format": "16:9 Documentary",  # "16:9 Documentary" | "16:9 Breaking Bulletin" | "9:16 Vertical Short"
    "voice_id": "hi-IN-MadhurNeural",     # "hi-IN-MadhurNeural" | "hi-IN-SwaraNeural"
    "narrative_style": "Deep Investigative (Nitish Rajput)", # "Deep Investigative" | "AajTak Breaking" | "Shorts Explainer"
    "autopublish_enabled": True,
    "interval_hours": 3.0,
    "night_quiet_start_hour": 0,          # 12:00 AM IST
    "night_quiet_end_hour": 6,            # 06:00 AM IST
    "target_script_minutes": 7.5,
    "groq_script_model": "openai/gpt-oss-120b"
}


class StudioConfigService:
    @staticmethod
    def load_settings() -> Dict[str, Any]:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                merged = DEFAULT_SETTINGS.copy()
                merged.update(data)
                return merged
            except Exception:
                pass
        return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(new_settings: Dict[str, Any]) -> Dict[str, Any]:
        current = StudioConfigService.load_settings()
        current.update(new_settings)
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        return current
