import json
from pathlib import Path
from typing import Dict
from config.settings import DATA_DIR
from models.news_models import GeneratedScript
from utils.logger import logger

ANALYTICS_FILE = DATA_DIR / "analytics_history.json"


def load_analytics() -> Dict:
    if ANALYTICS_FILE.exists():
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_videos_created": 0,
        "categories_covered": {},
        "video_history": []
    }


def save_analytics(data: Dict):
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def analytics_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Analytics Agent: Tracks video output metrics and informs CEO Agent on top performing categories.
    """
    logger.info("=" * 50)
    logger.info("📊 ANALYTICS & FEEDBACK AGENT")
    logger.info("=" * 50)

    data = load_analytics()

    data["total_videos_created"] += 1
    cat = script_obj.category
    data["categories_covered"][cat] = data["categories_covered"].get(cat, 0) + 1

    entry = {
        "title": script_obj.topic_title,
        "category": script_obj.category,
        "word_count": script_obj.word_count,
        "video_file": Path(script_obj.video_path).name if script_obj.video_path else None,
        "created_at": script_obj.created_at
    }
    data["video_history"].append(entry)

    save_analytics(data)

    logger.info(f"📈 Total Channel Videos Produced: {data['total_videos_created']}")
    logger.info(f"📊 Category Breakdown: {data['categories_covered']}")
    logger.info("✅ Analytics & CEO Feedback Loop Updated Successfully!")

    return script_obj
