"""
start_system_services.py
========================
MASTER SUPERVISOR DAEMON FOR 24/7 CRICKET STREAM & HOURLY AUTOMATED UPLOADS.

Features:
- Ensures generate_and_upload_cricket_live.py runs 24/7 with auto-restart on network/pipe drop.
- Runs auto_hourly_cricket_summary_scheduler.py in background for automatic hourly video uploads.
"""

import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

CRICKET_SCRIPT   = BASE_DIR / "generate_and_upload_cricket_live.py"
HOURLY_SCHEDULER = BASE_DIR / "auto_hourly_cricket_summary_scheduler.py"

def run_supervisor():
    print("🚀 Master Supervisor Active — Monitoring 24/7 Live Stream & Hourly Scheduler...")

    # Launch Hourly Scheduler in background
    scheduler_proc = subprocess.Popen([sys.executable, str(HOURLY_SCHEDULER)])

    while True:
        print("🔴 Launching 24/7 Live Stream Engine...")
        stream_proc = subprocess.Popen([sys.executable, str(CRICKET_SCRIPT)])
        
        # Wait for stream process to terminate/crash, then auto-restart after 5s
        stream_proc.wait()
        print("⚠️ Stream process disconnected or ended. Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    run_supervisor()
