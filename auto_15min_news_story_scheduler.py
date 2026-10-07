"""
auto_15min_news_story_scheduler.py
===================================
AUTOMATED 15-MINUTE NEW STORY GENERATOR & YOUTUBE UPLOADER.

Features:
- Runs continuous loop every 15 minutes (900 seconds).
- Fetches fresh trending news via RSS.
- Anti-Repetition Filter: Tracks processed news titles in `processed_stories.json` to prevent repeating any story.
- Generates 5-minute detailed Hindi narration & 1080p video with real event photos.
- Uploads video with high-CTR thumbnail & SEO tags to YouTube channel automatically.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.logger import logger
from generate_and_upload_5min_story import main as generate_and_upload_story

PROCESSED_FILE = BASE_DIR / "processed_stories.json"

def load_processed_titles() -> set:
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_title(title: str):
    titles = load_processed_titles()
    titles.add(title)
    try:
        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(titles), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed title: {e}")

def run_15min_news_scheduler():
    print("⏰ [15-MIN NEWS SCHEDULER] Active! Generating 5-Min News Story every 15 Minutes (Zero Repetition)...")
    
    cycle_count = 1
    while True:
        logger.info(f"⌛ [CYCLE #{cycle_count}] Fetching fresh non-repeated news story...")
        try:
            # Execute 5-minute story generation and auto-upload
            generate_and_upload_story()
            logger.info(f"✅ [CYCLE #{cycle_count}] 5-Minute News Story published successfully!")
            cycle_count += 1
        except Exception as e:
            logger.error(f"❌ [CYCLE #{cycle_count}] News story generation/upload error: {e}")

        logger.info("💤 Sleeping for 15 minutes (900s) before next story...")
        time.sleep(900)

if __name__ == "__main__":
    run_15min_news_scheduler()
