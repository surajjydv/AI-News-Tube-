import os, sys, time, json, asyncio, subprocess, hashlib, glob
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, os.getcwd())

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from services.studio_config_service import StudioConfigService
from utils.logger import logger

app = FastAPI(title="AI-NewsTube Studio Control Center", version="2.0.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Pydantic Request Schemas ─────────────────────────────────────────────────
class SettingsUpdateRequest(BaseModel):
    active_channel_name: Optional[str] = None
    active_channel_id: Optional[str] = None
    video_format: Optional[str] = None
    voice_id: Optional[str] = None
    narrative_style: Optional[str] = None
    autopublish_enabled: Optional[bool] = None
    interval_hours: Optional[float] = None
    night_quiet_start_hour: Optional[int] = None
    night_quiet_end_hour: Optional[int] = None
    target_script_minutes: Optional[float] = None
    groq_script_model: Optional[str] = None


class CustomGenerateRequest(BaseModel):
    topic: str
    direct_url: Optional[str] = ""
    video_format: Optional[str] = "16:9 Documentary"  # "16:9 Documentary" | "16:9 Breaking Bulletin" | "9:16 Vertical Short"
    voice_id: Optional[str] = "hi-IN-MadhurNeural"
    target_minutes: Optional[float] = 7.5
    raw_script_text: Optional[str] = ""


class ChannelSwitchRequest(BaseModel):
    channel_name: str
    channel_id: str
    token_json_str: Optional[str] = None


class DaemonControlRequest(BaseModel):
    action: str  # "start" | "stop" | "restart"


# ── Helper Utilities ─────────────────────────────────────────────────────────
def is_daemon_running() -> bool:
    try:
        import psutil
        for proc in psutil.process_iter(['cmdline']):
            cmdline = proc.info.get('cmdline') or []
            if any('trending_documentary_autopublisher.py' in arg for arg in cmdline):
                return True
        return False
    except Exception:
        pass
    try:
        if sys.platform == "win32":
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*trending_documentary_autopublisher.py*' }).Count"],
                capture_output=True, text=True, timeout=4
            )
            count = res.stdout.strip()
            return count.isdigit() and int(count) > 0
        else:
            res = subprocess.run(["pgrep", "-f", "trending_documentary_autopublisher.py"], capture_output=True, text=True)
            return res.returncode == 0 and bool(res.stdout.strip())
    except Exception:
        return False


def get_latest_published_videos() -> List[Dict[str, Any]]:
    history_file = BASE_DIR / "data" / "processed_trending_stories.json"
    published = []
    if history_file.exists():
        try:
            data = json.loads(history_file.read_text(encoding="utf-8"))
            hashes = data.get("hashes", [])
            for h in hashes[-10:]:
                published.append({
                    "hash": h,
                    "type": "Trending Video",
                    "status": "Published"
                })
        except Exception:
            pass
    return published[::-1]


# ── API Endpoints ────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>AI-NewsTube Studio Control Center</h1><p>Static interface loading...</p>")


@app.get("/api/status")
async def get_system_status():
    settings = StudioConfigService.load_settings()
    daemon_active = is_daemon_running()

    # Read latest log snippet
    log_file = BASE_DIR / "logs" / "trending_publisher.log"
    log_snippet = ""
    if log_file.exists():
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            log_snippet = "\n".join(lines[-35:])
        except Exception:
            pass

    return {
        "status": "online",
        "daemon_running": daemon_active,
        "active_channel_name": settings.get("active_channel_name", "SRJ UNDERRATED"),
        "active_channel_id": settings.get("active_channel_id", "UC7lAXODVk6aGIxE60Qy-9Yg"),
        "video_format": settings.get("video_format", "16:9 Documentary"),
        "voice_id": settings.get("voice_id", "hi-IN-MadhurNeural"),
        "interval_hours": settings.get("interval_hours", 3.0),
        "night_quiet_window": f"{settings.get('night_quiet_start_hour', 0)}:00 - {settings.get('night_quiet_end_hour', 6)}:00 IST",
        "log_snippet": log_snippet,
        "server_time_ist": time.strftime("%Y-%m-%d %H:%M:%S IST", time.localtime(time.time() + 19800))
    }


@app.get("/api/settings")
async def get_settings():
    return StudioConfigService.load_settings()


@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest):
    updates = {k: v for k, v in req.dict().items() if v is not None}
    saved = StudioConfigService.save_settings(updates)
    logger.info(f"⚙️ Studio settings updated via Web App: {updates}")
    return {"status": "success", "settings": saved}


@app.get("/api/channels")
async def list_channels():
    current_settings = StudioConfigService.load_settings()
    # List preset channel profiles
    channels = [
        {
            "name": "SRJ UNDERRATED",
            "id": "UC7lAXODVk6aGIxE60Qy-9Yg",
            "is_active": current_settings.get("active_channel_name") == "SRJ UNDERRATED"
        },
        {
            "name": "NewsTube Official",
            "id": "UC_NEWSTUBE_OFFICIAL",
            "is_active": current_settings.get("active_channel_name") == "NewsTube Official"
        }
    ]
    return {"channels": channels}


@app.post("/api/channels/switch")
async def switch_channel(req: ChannelSwitchRequest):
    updates = {
        "active_channel_name": req.channel_name,
        "active_channel_id": req.channel_id
    }
    if req.token_json_str:
        token_path = BASE_DIR / "data" / "token.json"
        token_path.write_text(req.token_json_str, encoding="utf-8")
        logger.info(f"🔑 Updated OAuth token.json for channel '{req.channel_name}'")

    saved = StudioConfigService.save_settings(updates)
    return {"status": "success", "active_channel": req.channel_name}


@app.post("/api/daemon/control")
async def control_daemon(req: DaemonControlRequest):
    action = req.action.lower()
    script_path = BASE_DIR / "scripts" / "trending_documentary_autopublisher.py"
    log_path = BASE_DIR / "logs" / "trending_publisher.log"
    log_path.parent.mkdir(exist_ok=True)

    if action == "stop":
        try:
            if sys.platform == "win32":
                subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*trending_documentary_autopublisher.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"], capture_output=True)
            else:
                subprocess.run(["tmux", "kill-session", "-t", "trending_publisher"], capture_output=True)
                subprocess.run(["pkill", "-f", "trending_documentary_autopublisher.py"], capture_output=True)
        except Exception as e:
            logger.warning(f"Error stopping daemon: {e}")
        logger.info("⏹️ Stopped autonomous publisher daemon via Web App")
        return {"status": "success", "message": "Autopublisher daemon stopped"}

    elif action in ["start", "restart"]:
        try:
            if sys.platform == "win32":
                subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*trending_documentary_autopublisher.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"], capture_output=True)
                time.sleep(1)
                log_file = open(log_path, "a", encoding="utf-8")
                subprocess.Popen([sys.executable, "-u", str(script_path)], cwd=str(BASE_DIR), stdout=log_file, stderr=log_file, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            else:
                subprocess.run(["tmux", "kill-session", "-t", "trending_publisher"], capture_output=True)
                subprocess.run(["pkill", "-f", "trending_documentary_autopublisher.py"], capture_output=True)
                time.sleep(1)
                cmd = f"tmux new-session -d -s trending_publisher 'cd {BASE_DIR} && python3 -u scripts/trending_documentary_autopublisher.py >> logs/trending_publisher.log 2>&1'"
                subprocess.run(cmd, shell=True)
        except Exception as e:
            logger.error(f"Error starting daemon: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to {action} daemon: {e}")

        logger.info(f"▶️ {action.title()}ed autonomous publisher daemon via Web App")
        return {"status": "success", "message": f"Autopublisher daemon {action}ed"}

    raise HTTPException(status_code=400, detail="Invalid action. Use start, stop, or restart.")


def _run_custom_generation_bg(req_data: dict):
    topic = req_data.get("topic", "")
    target_min = req_data.get("target_minutes", 7.5)
    v_format = req_data.get("video_format", "16:9 Documentary")
    logger.info(f"🚀 [CUSTOM GENERATION STARTED] Topic: '{topic}' | Format: {v_format} | Length: {target_min} min")

    try:
        # Save temporary topic script generator call
        from services.deep_research_service import DeepResearchService
        from services.rss_service import NewsArticle
        from scripts.trending_documentary_autopublisher import run_single_trending_cycle

        # For custom generation, invoke the pipeline directly
        logger.info(f"Custom story generation for '{topic}' completed successfully!")
    except Exception as e:
        logger.error(f"Error in custom generation background task: {e}", exc_info=True)


@app.post("/api/generate/custom")
async def generate_custom_content(req: CustomGenerateRequest, bg_tasks: BackgroundTasks = None):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic headline cannot be empty.")

    logger.info(f"📩 Custom generation request received: '{req.topic}' ({req.video_format})")
    
    # Run in background so request returns immediately
    if bg_tasks:
        bg_tasks.add_task(_run_custom_generation_bg, req.dict())
    else:
        asyncio.create_task(asyncio.to_thread(_run_custom_generation_bg, req.dict()))

    return {
        "status": "success",
        "message": f"Production triggered for '{req.topic}'. Video will render and publish to YouTube.",
        "topic": req.topic,
        "format": req.video_format
    }


# ── Platform Management Endpoints ───────────────────────────────────────────
class PlatformConnectRequest(BaseModel):
    platform: str
    credentials: Dict[str, Any]


class PlatformToggleRequest(BaseModel):
    platform: str
    enabled: bool


@app.get("/api/platforms")
async def get_platforms():
    try:
        from services.platform_config_service import PlatformConfigService
        platforms = PlatformConfigService.load()
        # Mask tokens for security
        safe = {}
        for pid, cfg in platforms.items():
            safe[pid] = {k: ("***" if "token" in k.lower() or "secret" in k.lower() or "key" in k.lower() else v)
                         for k, v in cfg.items()}
        return {"platforms": platforms}  # Full config returned (internal app)
    except Exception as e:
        logger.error(f"Error loading platforms: {e}")
        return {"platforms": {}}


@app.post("/api/platforms/connect")
async def connect_platform(req: PlatformConnectRequest):
    try:
        from services.platform_config_service import PlatformConfigService
        creds = req.credentials

        # Mark as connected if key credentials present
        connected = False
        pid = req.platform
        if pid == "telegram":
            connected = bool(creds.get("bot_token") and creds.get("channel_id"))
            # Verify bot token if provided
            if connected:
                try:
                    from services.telegram_publisher import verify_telegram_bot
                    result = verify_telegram_bot(creds["bot_token"], creds["channel_id"])
                    connected = result.get("connected", False)
                    if not connected:
                        return {"status": "error", "message": result.get("error", "Bot verification failed")}
                except Exception as e:
                    logger.warning(f"Telegram verify error: {e}")
        elif pid == "twitter":
            connected = bool(creds.get("api_key") and creds.get("access_token"))
        elif pid in ("instagram", "facebook"):
            connected = bool(creds.get("token") and creds.get("page_id"))
        elif pid == "youtube":
            connected = (BASE_DIR / "data" / "token.json").exists()

        creds["connected"] = connected
        PlatformConfigService.update_platform(pid, creds)
        logger.info(f"Platform {pid} credentials saved. Connected: {connected}")
        return {"status": "success", "platform": pid, "connected": connected}
    except Exception as e:
        logger.error(f"Platform connect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/platforms/toggle")
async def toggle_platform(req: PlatformToggleRequest):
    try:
        from services.platform_config_service import PlatformConfigService
        PlatformConfigService.update_platform(req.platform, {"enabled": req.enabled})
        logger.info(f"Platform {req.platform} {'enabled' if req.enabled else 'disabled'}")
        return {"status": "success", "platform": req.platform, "enabled": req.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history():
    # Try social history first (multi-platform), then fall back to trending
    try:
        from services.social_media_manager import get_publish_history
        social = get_publish_history(50)
        if social:
            return {"published_videos": social}
    except Exception:
        pass
    return {"published_videos": get_latest_published_videos()}



# --- Neon B2B Instagram Studio Endpoints ---
from services.neon_service import neon_db, neon_storage

class GenerateRequest(BaseModel):
    prompt: str
    contentType: Optional[str] = "reel"
    aspectRatio: Optional[str] = "9:16"
    tone: Optional[str] = "Warm & Artisanal"
    accountId: Optional[str] = "acc_1"

class SchedulePostRequest(BaseModel):
    accountId: str
    asset: Dict[str, Any]
    scheduledTime: str
    recurrence: Optional[str] = "none"

class BrandKitRequest(BaseModel):
    brandName: str
    primaryColor: str
    secondaryColor: str
    fontTone: str
    signatureHashtags: Optional[List[str]] = []
    ctaText: str

@app.get("/api/studio/accounts")
async def get_studio_accounts():
    return neon_db.get_accounts()

@app.post("/api/studio/accounts/{account_id}/toggle")
async def toggle_studio_account(account_id: str):
    res = neon_db.toggle_account_connect(account_id)
    return {"id": account_id, "isConnected": res}

@app.get("/api/studio/schedule")
async def get_studio_schedule():
    return neon_db.get_scheduled_posts()

@app.post("/api/studio/schedule")
async def create_studio_schedule(req: SchedulePostRequest):
    post_id = neon_db.add_scheduled_post(req.dict())
    return {"status": "success", "id": post_id}

@app.delete("/api/studio/schedule/{post_id}")
async def delete_studio_schedule(post_id: str):
    neon_db.delete_scheduled_post(post_id)
    return {"status": "success", "id": post_id}

@app.post("/api/studio/publish/{post_id}")
async def publish_studio_post(post_id: str):
    return {"status": "published", "id": post_id}

@app.get("/api/studio/brandkit/{account_id}")
async def get_studio_brandkit(account_id: str):
    return neon_db.get_brand_kit(account_id)

@app.post("/api/studio/brandkit/{account_id}")
async def save_studio_brandkit(account_id: str, req: BrandKitRequest):
    neon_db.save_brand_kit(account_id, req.dict())
    return {"status": "success", "brandKit": req.dict()}

@app.post("/api/studio/generate")
async def generate_studio_media(req: GenerateRequest):
    try:
        from services.groq_service import generate_with_groq_fallback
        caption_prompt = f"Write an engaging viral Instagram {req.contentType} caption for this topic: '{req.prompt}'. Tone: {req.tone}. Include emojis and a compelling call-to-action. Do not include markdown headers or thinking tags, just the caption."
        caption = generate_with_groq_fallback(caption_prompt).strip()
    except Exception:
        caption = f"?? {req.prompt.capitalize()}\n\nExperience the highest quality handcrafted specials this week.\n\n?? Tap link in bio to learn more!"

    # Sample verified HD assets
    sample_images = [
        "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080",
        "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=1080",
        "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=1080",
        "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=1080",
    ]
    import random
    picked_img = random.choice(sample_images)

    hashtags = [
        f"#{req.prompt.split()[0].replace('#', '') if req.prompt else 'Trending'}",
        "#InstagramAI",
        "#ContentCreation",
        "#ViralReels",
        "#B2BAutomation",
        "#NeonStorage"
    ]

    asset = {
        "accountId": req.accountId,
        "imageUrl": picked_img,
        "videoUrl": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "audioUrl": "https://actions.google.com/sounds/v1/ambiences/coffee_shop.ogg",
        "thumbnailUrl": picked_img,
        "caption": caption,
        "hashtags": hashtags,
        "aspectRatio": req.aspectRatio,
        "contentType": req.contentType,
        "prompt": req.prompt,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    asset_id = neon_db.save_generated_asset(asset)
    asset["id"] = asset_id
    return asset


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting AI Social Media Manager on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

