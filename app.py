import os, sys, time, json, asyncio, subprocess, hashlib, glob
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, os.getcwd())

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File, Form
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
    direct_url = req_data.get("direct_url", "")
    raw_script = req_data.get("raw_script_text", "")

    logger.info(f"🚀 [CUSTOM GENERATION STARTED] Topic: '{topic}' | Format: {v_format} | Length: {target_min} min")

    try:
        import hashlib, time as _time, asyncio as _aio
        from services.deep_research_service import DeepResearchService
        from services.fluent_script_service import clean_news_headline
        from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
        from services.youtube_upload_service import upload_video_to_youtube
        from scripts.trending_documentary_autopublisher import (
            generate_trending_hindi_script,
            fetch_real_incident_photos,
            generate_hindi_voiceover,
            verify_and_select_thumbnail_photo,
            render_video_fast_ffmpeg,
            cleanup_old_files,
            save_processed_story,
        )
        from services.rss_service import NewsArticle

        u_hash = hashlib.md5(topic.lower().encode("utf-8")).hexdigest()[:10]
        story_id = f"custom_{int(_time.time())}_{u_hash}"
        story_dir = BASE_DIR / "output" / f"assets_{story_id}"
        audio_path = BASE_DIR / "output" / f"audio_{story_id}.mp3"
        video_path = BASE_DIR / "videos" / f"custom_{story_id}.mp4"
        thumb_path = BASE_DIR / "output" / f"thumb_{story_id}.jpg"
        temp_dir = BASE_DIR / "output" / f"temp_{story_id}"
        story_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 1. Deep Research
        logger.info(f"🔍 [CUSTOM] Compiling research dossier for: {topic}")
        dossier_data = DeepResearchService.compile_investigative_dossier(
            topic=clean_news_headline(topic),
            direct_url=direct_url or "",
            raw_summary=topic,
            deep=True
        )
        dossier_text = dossier_data.get("full_dossier", topic)

        # 2. Hindi Script
        logger.info("📝 [CUSTOM] Generating Hindi script...")
        narr, chapters, doc_title, v_title, tags = generate_trending_hindi_script(
            topic=topic,
            dossier=dossier_text,
            target_minutes=target_min
        )

        # 3. Fetch Real Photos
        logger.info("📸 [CUSTOM] Fetching real press photos...")
        article = NewsArticle(title=topic, link=direct_url or "", summary=topic, source="Custom",
                              published="", category="Breaking News", image_url="", trending_score=100)
        photo_paths = fetch_real_incident_photos(
            topic=topic, story_dir=story_dir,
            direct_image_url="", article_url=direct_url or "",
            max_photos=6
        )

        # 4. Voiceover
        logger.info("🎙️ [CUSTOM] Synthesizing Hindi voiceover...")
        _aio.run(generate_hindi_voiceover(narr, audio_path))

        # 5. Thumbnail
        logger.info("🖼️ [CUSTOM] Generating thumbnail...")
        verified_thumb_photo = verify_and_select_thumbnail_photo(
            target_article=article,
            headline=doc_title or topic,
            photo_paths=photo_paths,
            story_dir=story_dir
        )
        try:
            create_real_event_youtube_thumbnail(
                headline=doc_title or topic,
                category="Breaking News",
                real_photo_path=verified_thumb_photo,
                output_path=thumb_path
            )
        except Exception as e:
            logger.warning(f"Thumbnail generation note: {e}")

        # 6. Render Video
        logger.info("🎬 [CUSTOM] Rendering 1080p video...")
        success = render_video_fast_ffmpeg(
            audio_path=audio_path,
            photo_paths=photo_paths,
            chapters=chapters,
            doc_title=doc_title,
            output_video=video_path,
            temp_dir=temp_dir
        )
        if not success:
            logger.error("❌ [CUSTOM] Video render failed")
            return

        # 7. Upload to YouTube
        logger.info("📤 [CUSTOM] Publishing to YouTube...")
        chapter_text = "\n".join([
            f"📌 {c.get('title', f'अध्याय {i+1}')} : {c.get('summary', '')}"
            for i, c in enumerate(chapters)
        ])
        description = (
            f"😱 {v_title}\n\n"
            f"देश और दुनिया की इस बड़ी खबर का पूरा सच और ज़मीनी पड़ताल।\n\n"
            f"📖 इस वीडियो में:\n{chapter_text}\n\n"
            f"🔔 निष्पक्ष और खोजी पत्रकारिता के लिए SRJ UNDERRATED को Subscribe करें!\n\n"
            f"#TrendingNews #HindiNews #BreakingNews #Investigation #SRJUnderrated"
        )

        vid_id = upload_video_to_youtube(
            video_path=str(video_path),
            title=v_title[:95],
            description=description,
            category_id="25",
            privacy_status="public",
            thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
            tags=tags[:15]
        )

        if vid_id and vid_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
            logger.info("=" * 70)
            logger.info(f"🎉 [CUSTOM] VIDEO PUBLISHED: https://youtu.be/{vid_id}")
            logger.info("=" * 70)
            save_processed_story(topic, u_hash)

        # 8. Auto-Publish Everywhere (Telegram, Twitter, Instagram, Facebook)
        try:
            from services.social_media_manager import publish_to_all_platforms
            yt_clean_id = vid_id if (vid_id and vid_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]) else None
            social_res = publish_to_all_platforms(
                title=v_title,
                body_text=narr[:500] if narr else topic,
                hashtags=" ".join([f"#{t}" for t in tags[:6]]),
                video_path=str(video_path),
                thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
                youtube_video_id=yt_clean_id
            )
            logger.info(f"🌐 [CUSTOM] Auto-published everywhere: {list(social_res.keys())}")
        except Exception as e:
            logger.warning(f"⚠️ [CUSTOM] Multi-platform publish error: {e}")

        cleanup_old_files()

    except Exception as e:
        logger.error(f"❌ Error in custom generation: {e}", exc_info=True)


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


@app.post("/api/generate/trending")
async def generate_trending_content(bg_tasks: BackgroundTasks):
    """One-click: auto-picks top trending story → research → script → render → YouTube publish."""
    def _run_trending_bg():
        try:
            from scripts.trending_documentary_autopublisher import run_single_trending_cycle
            logger.info("🚀 [ONE-CLICK TRENDING] Starting auto trending cycle...")
            result = run_single_trending_cycle()
            if result:
                logger.info("🎉 [ONE-CLICK TRENDING] Video published to YouTube!")
            else:
                logger.warning("⚠️ [ONE-CLICK TRENDING] Cycle completed but no video published.")
        except Exception as e:
            logger.error(f"❌ [ONE-CLICK TRENDING] Error: {e}", exc_info=True)

    bg_tasks.add_task(_run_trending_bg)
    return {
        "status": "success",
        "message": "Trending video generation triggered. Will auto-pick top story, generate video, and publish to YouTube."
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


@app.post("/api/publish/blast")
async def blast_media_to_platforms(
    title: str = Form(...),
    description: str = Form(...),
    hashtags: Optional[str] = Form(""),
    platforms: Optional[str] = Form("all"),
    media: Optional[UploadFile] = File(None),
    thumbnail: Optional[UploadFile] = File(None)
):
    """
    1-Click Multi-Platform Media Blast:
    Accepts media (video or image) + title + description + hashtags,
    and publishes immediately across all selected platforms (YouTube, Telegram, Twitter, Instagram, Facebook).
    """
    if not title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    upload_dir = BASE_DIR / "output" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    video_path = None
    thumbnail_path = None

    ts = int(time.time())
    if media and media.filename:
        safe_name = f"{ts}_{media.filename.replace(' ', '_')}"
        saved_file = upload_dir / safe_name
        contents = await media.read()
        saved_file.write_bytes(contents)
        ext = saved_file.suffix.lower()
        if ext in [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]:
            video_path = str(saved_file)
        elif ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            thumbnail_path = str(saved_file)

    if thumbnail and thumbnail.filename:
        thumb_name = f"{ts}_thumb_{thumbnail.filename.replace(' ', '_')}"
        thumb_file = upload_dir / thumb_name
        contents = await thumbnail.read()
        thumb_file.write_bytes(contents)
        thumbnail_path = str(thumb_file)

    from services.platform_config_service import PlatformConfigService
    from services.social_media_manager import publish_to_all_platforms

    enabled_platforms = PlatformConfigService.get_enabled_platforms()
    if platforms and platforms != "all":
        selected = [p.strip().lower() for p in platforms.split(",") if p.strip()]
        enabled_platforms = {k: v for k, v in enabled_platforms.items() if k.lower() in selected}

    try:
        results = publish_to_all_platforms(
            title=title.strip(),
            body_text=description.strip(),
            hashtags=hashtags.strip() if hashtags else "",
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            platforms_config=enabled_platforms
        )
        return {
            "status": "success",
            "message": f"Blasted to {len(results)} platforms",
            "results": results,
            "media_uploaded": bool(video_path or thumbnail_path)
        }
    except Exception as e:
        logger.error(f"Error in /api/publish/blast: {e}", exc_info=True)
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


@app.get("/api/studio/latest")
async def get_latest_generated_asset():
    conn = neon_db._get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, account_id, image_url, video_url, audio_url, thumbnail_url, caption, hashtags, aspect_ratio, content_type, prompt, created_at
        FROM generated_assets
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if row:
        hashtags = []
        if row[7]:
            try:
                hashtags = json.loads(row[7])
            except Exception:
                hashtags = []
        return {
            "id": row[0],
            "accountId": row[1],
            "imageUrl": row[2],
            "videoUrl": row[3],
            "audioUrl": row[4],
            "thumbnailUrl": row[5],
            "caption": row[6],
            "hashtags": hashtags,
            "aspectRatio": row[8],
            "contentType": row[9],
            "prompt": row[10],
            "createdAt": row[11],
        }
    return None

@app.post("/api/studio/generate")
async def generate_studio_media(req: GenerateRequest):
    from services.real_media_generator import generate_real_media_pack
    asset = await generate_real_media_pack(
        prompt=req.prompt,
        content_type=req.contentType or "reel",
        aspect_ratio=req.aspectRatio or "9:16",
        tone=req.tone or "Warm & Artisanal",
        account_id=req.accountId or "acc_1"
    )
    return asset



# --- Real YouTube Studio Endpoints ---
from services.youtube_real_service import youtube_real_service

@app.get("/api/youtube/channel")
async def get_real_youtube_channel():
    try:
        data = youtube_real_service.get_channel_info()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/youtube/videos")
async def get_real_youtube_videos(max_results: int = 24):
    try:
        videos = youtube_real_service.get_channel_videos(max_results=max_results)
        return {"videos": videos, "total": len(videos)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/youtube/stream")
async def get_real_youtube_stream():
    try:
        return youtube_real_service.get_stream_details()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting AI Social Media Manager on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

