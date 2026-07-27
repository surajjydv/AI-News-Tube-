import sys
from pathlib import Path

# Fix sys.path so 'config', 'agents', 'services', 'utils' are always resolvable
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.ceo_agent import ceo_agent
from utils.logger import logger


def main():
    logger.info("🚀 Starting AI-NewsTube Pipeline...")
    result = ceo_agent()
    if result:
        logger.info("✅ AI-NewsTube Pipeline Finished Successfully.")
    else:
        logger.warning("⚠️ AI-NewsTube Pipeline finished with warnings or errors.")


if __name__ == "__main__":
    main()
