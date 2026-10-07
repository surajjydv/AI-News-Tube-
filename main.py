import sys
import argparse
from pathlib import Path
from typing import Optional

# Fix sys.path so 'config', 'agents', 'services', 'utils' are always resolvable
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.ceo_agent import ceo_agent
from utils.logger import logger
from app import app  # Expose FastAPI ASGI application for uvicorn main:app


def main():
    parser = argparse.ArgumentParser(description="AI-NewsTube Automated News Video Production Pipeline")
    parser.add_argument("topic", nargs="?", type=str, default=None, help="Optional news topic (e.g. 'today's IND vs SL match')")
    parser.add_argument("--topic", "-t", type=str, dest="opt_topic", default=None, help="Optional news topic flag")

    args = parser.parse_args()
    topic: Optional[str] = args.topic or args.opt_topic

    logger.info("🚀 Starting AI-NewsTube Pipeline...")
    if topic:
        logger.info(f"📌 User Specified Topic: '{topic}'")

    result = ceo_agent(topic=topic)
    if result:
        logger.info("✅ AI-NewsTube Pipeline Finished Successfully.")
    else:
        logger.warning("⚠️ AI-NewsTube Pipeline finished with warnings or errors.")


if __name__ == "__main__":
    main()
