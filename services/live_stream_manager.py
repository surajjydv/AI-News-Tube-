import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import psutil
from utils.logger import logger
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PID_FILE = BASE_DIR / "data" / "live_stream.pid"
LOG_FILE = BASE_DIR / "data" / "live_stream.log"


class LiveStreamManager:
    def __init__(self):
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._start_time: Optional[float] = None

    def _read_pid(self) -> Optional[int]:
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                return pid
            except Exception:
                return None
        return None

    def _write_pid(self, pid: int, start_time: float):
        PID_FILE.write_text(f"{pid}:{int(start_time)}")

    def _clear_pid(self):
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
            except Exception:
                pass

    def is_running(self) -> tuple[bool, Optional[int], int]:
        """Returns (is_active, pid, uptime_seconds)."""
        pid_data = None
        if PID_FILE.exists():
            try:
                content = PID_FILE.read_text().strip()
                if ":" in content:
                    parts = content.split(":")
                    pid = int(parts[0])
                    st = float(parts[1])
                else:
                    pid = int(content)
                    st = time.time()
                pid_data = (pid, st)
            except Exception:
                pass

        # Check by pid first
        if pid_data:
            pid, st = pid_data
            try:
                p = psutil.Process(pid)
                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                    cmdline = " ".join(p.cmdline()).lower()
                    if "continuous_live_stream.py" in cmdline or "python" in p.name().lower():
                        uptime = int(time.time() - st)
                        return True, pid, max(0, uptime)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Fallback search in psutil process list
        try:
            for p in psutil.process_iter(['pid', 'cmdline', 'create_time']):
                try:
                    cmdline = " ".join(p.info.get('cmdline') or []).lower()
                    if "continuous_live_stream.py" in cmdline:
                        pid = p.info['pid']
                        ctime = p.info.get('create_time', time.time())
                        uptime = int(time.time() - ctime)
                        self._write_pid(pid, ctime)
                        return True, pid, max(0, uptime)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        self._clear_pid()
        return False, None, 0

    def start_stream(self) -> Dict[str, Any]:
        """Starts continuous 24/7 video rotation live stream to YouTube RTMP."""
        running, pid, uptime = self.is_running()
        if running:
            return {
                "success": True,
                "message": f"Continuous Live Stream is already running (PID: {pid})",
                "pid": pid,
                "isLive": True,
                "uptimeSeconds": uptime
            }

        stream_key = os.getenv("YOUTUBE_STREAM_KEY", "").strip()
        if not stream_key:
            return {
                "success": False,
                "message": "YOUTUBE_STREAM_KEY not configured in .env",
                "isLive": False,
            }

        script_path = BASE_DIR / "scripts" / "continuous_live_stream.py"
        if not script_path.exists():
            return {
                "success": False,
                "message": f"Script not found: {script_path}",
                "isLive": False,
            }

        log_out = open(LOG_FILE, "a", encoding="utf-8")
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

            proc = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(BASE_DIR),
                stdout=log_out,
                stderr=subprocess.STDOUT,
                creationflags=creationflags
            )

            now = time.time()
            self._write_pid(proc.pid, now)
            logger.info(f"[LiveStreamManager] Started continuous live stream process PID={proc.pid}")

            return {
                "success": True,
                "message": "Continuous 24/7 Live Stream started successfully with video rotation queue.",
                "pid": proc.pid,
                "isLive": True,
                "uptimeSeconds": 0
            }
        except Exception as e:
            logger.error(f"[LiveStreamManager] Failed to start live stream: {e}")
            return {
                "success": False,
                "message": f"Failed to start live stream: {str(e)}",
                "isLive": False,
            }

    def stop_stream(self) -> Dict[str, Any]:
        """Stops the continuous live stream process and associated FFmpeg subprocesses."""
        running, pid, _ = self.is_running()
        if not running and not pid:
            self._clear_pid()
            return {"success": True, "message": "Live stream is not running.", "isLive": False}

        terminated = False
        if pid:
            try:
                parent = psutil.Process(pid)
                # Kill children first (e.g. ffmpeg)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
                terminated = True
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"[LiveStreamManager] Process {pid} could not be killed directly: {e}")

        # Scan for any orphaned continuous_live_stream.py
        try:
            for p in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = " ".join(p.info.get('cmdline') or []).lower()
                    if "continuous_live_stream.py" in cmdline:
                        for child in p.children(recursive=True):
                            try:
                                child.kill()
                            except Exception:
                                pass
                        p.kill()
                        terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

        self._clear_pid()
        return {
            "success": True,
            "message": "Continuous Live Stream stopped successfully.",
            "isLive": False
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of continuous live streaming."""
        running, pid, uptime = self.is_running()
        stream_key = os.getenv("YOUTUBE_STREAM_KEY", "")
        masked_key = stream_key[:4] + "-****-****-" + stream_key[-4:] if len(stream_key) > 8 else "****"

        # Check latest log line
        last_log = ""
        if LOG_FILE.exists():
            try:
                lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").strip().splitlines()
                if lines:
                    last_log = lines[-1]
            except Exception:
                pass

        return {
            "isLive": running,
            "pid": pid,
            "uptimeSeconds": uptime,
            "rtmpUrl": "rtmp://a.rtmp.youtube.com/live2",
            "streamKeyMasked": masked_key,
            "hasKey": bool(stream_key),
            "mode": "24/7 Continuous Video Rotation",
            "lastLog": last_log,
            "targetChannel": "@SRJUNDERRATED"
        }


live_stream_manager = LiveStreamManager()
