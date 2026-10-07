import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.realtime_breaking_news_autouploader import run_breaking_news_autopublisher_loop

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='24/7 Realtime Breaking News Auto-Publisher')
    parser.add_argument('--once', action='store_true', help='Execute single breaking news cycle')
    args = parser.parse_args()

    run_breaking_news_autopublisher_loop(single_run=args.once)
